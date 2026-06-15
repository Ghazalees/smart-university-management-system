from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
import time
import httpx
from django.conf import settings
from .exceptions import AIServiceUnavailable
from apps.core.services import ServiceRegistry

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

    def answer(self, *, question, prompt, documents):
        payload = {
            "question": question,
            "prompt": prompt,
            "documents": [{"id": d.id, "title": d.title, "content": d.content} for d in documents],
        }
        try:
            response = httpx.post(f"{self.base_url}/v1/answer", json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return AIAnswer(data["answer"], float(data["confidence"]), data.get("provider", "ai-service"), data.get("model_name", ""))
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AIServiceUnavailable() from exc

    def analyze(self, text):
        try:
            response = httpx.post(f"{self.base_url}/v1/analyze", json={"text": text}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AIServiceUnavailable() from exc

class ResilientAIProxy(AIProvider):
    """Proxy pattern adding retries and failure isolation to any AI provider."""
    def __init__(self, target, retries=1, backoff_seconds=0.05):
        self.target = target
        self.retries = retries
        self.backoff_seconds = backoff_seconds

    def _call(self, method, *args, **kwargs):
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                return getattr(self.target, method)(*args, **kwargs)
            except AIServiceUnavailable as exc:
                last_error = exc
                logger.warning("AI call failed method=%s attempt=%s", method, attempt + 1)
                if attempt < self.retries:
                    time.sleep(self.backoff_seconds * (attempt + 1))
        raise last_error

    def answer(self, **kwargs): return self._call("answer", **kwargs)
    def analyze(self, text): return self._call("analyze", text)

class AIProviderFactory:
    """Factory Method selecting the infrastructure provider."""
    @staticmethod
    def create():
        registry = ServiceRegistry()
        if not registry.has("ai_provider"):
            registry.register("ai_provider", ResilientAIProxy(FastAPILLMAdapter()))
        return registry.get("ai_provider")
