"""Adapts backend question-answering requests to the internal AI service contract."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import Lock

import httpx
from django.conf import settings

from .exceptions import AIServiceUnavailable
from .retrieval import document_context

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIAnswer:
    answer: str
    confidence: float
    provider: str
    model_name: str = ""


class AIProvider(ABC):
    @abstractmethod
    def answer(self, *, question, prompt, documents): ...

    @abstractmethod
    def analyze(self, text): ...


class FastAPILLMAdapter(AIProvider):
    """Adapter from the FastAPI wire contract to the backend domain contract."""

    def __init__(self, base_url=None, timeout=None):
        self.base_url = (base_url or settings.AI_SERVICE_URL).rstrip("/")
        self.timeout = timeout or settings.AI_SERVICE_TIMEOUT_SECONDS
        self.headers = {"X-Internal-API-Key": settings.AI_SERVICE_API_KEY}

    def answer(self, *, question, prompt, documents):
        payload = {
            "question": question,
            "prompt": prompt,
            "documents": [
                {"id": d.id, "title": d.title, "content": document_context(d)[:12000]}
                for d in documents
            ],
        }
        try:
            response = httpx.post(
                f"{self.base_url}/v1/answer",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return AIAnswer(
                data["answer"],
                float(data["confidence"]),
                data.get("provider", "ai-service"),
                data.get("model_name", ""),
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AIServiceUnavailable() from exc

    def analyze(self, text):
        try:
            response = httpx.post(
                f"{self.base_url}/v1/analyze",
                json={"text": text},
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AIServiceUnavailable() from exc


class ResilientAIProxy(AIProvider):
    """Proxy adding retry, timeout isolation and a small circuit breaker."""

    def __init__(
        self,
        target,
        retries=1,
        backoff_seconds=0.05,
        failure_threshold=3,
        reset_seconds=20,
    ):
        self.target = target
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self.failures = 0
        self.opened_at = None
        self._lock = Lock()

    def _call(self, method, *args, **kwargs):
        with self._lock:
            if (
                self.opened_at
                and time.monotonic() - self.opened_at < self.reset_seconds
            ):
                raise AIServiceUnavailable("AI circuit is temporarily open")
            if self.opened_at:
                self.opened_at = None
                self.failures = 0
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                result = getattr(self.target, method)(*args, **kwargs)
                with self._lock:
                    self.failures = 0
                return result
            except AIServiceUnavailable as exc:
                last_error = exc
                logger.warning(
                    "AI call failed method=%s attempt=%s", method, attempt + 1
                )
                if attempt < self.retries:
                    time.sleep(self.backoff_seconds * (attempt + 1))
        with self._lock:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.opened_at = time.monotonic()
        raise last_error

    def answer(self, **kwargs):
        return self._call("answer", **kwargs)

    def analyze(self, text):
        return self._call("analyze", text)


class AIProviderRegistry:
    """Explicit Singleton registry for configured AI providers."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.providers = {}
        return cls._instance

    def get_or_create(self, name, factory):
        if name not in self.providers:
            self.providers[name] = factory()
        return self.providers[name]

    def clear(self):
        self.providers.clear()


class AIProviderFactory:
    """Factory Method selecting the configured infrastructure provider."""

    @staticmethod
    def create():
        return AIProviderRegistry().get_or_create(
            "default", lambda: ResilientAIProxy(FastAPILLMAdapter())
        )
