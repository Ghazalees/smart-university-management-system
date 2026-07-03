"""Implements local and external AI provider integrations behind a common interface."""

import os
import re
import unicodedata
from abc import ABC, abstractmethod
from threading import Lock

import httpx

from .prompting import ResponseBuilder

TOKEN_PATTERN = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)
PASSAGE_SPLIT = re.compile(r"\n{2,}|(?<=[.!?؟])\s+")
PERSIAN_TRANSLATION = str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"})
STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "what",
    "how",
    "can",
    "are",
    "is",
    "to",
    "of",
    "a",
    "an",
    "from",
    "about",
    "please",
    "از",
    "به",
    "در",
    "برای",
    "که",
    "این",
    "آن",
    "را",
    "با",
    "یا",
    "چه",
    "چگونه",
    "است",
    "هست",
}


def tokens(text):
    normalized = (
        unicodedata.normalize("NFKC", text or "").translate(PERSIAN_TRANSLATION).lower()
    )
    return {
        token
        for token in TOKEN_PATTERN.findall(normalized)
        if len(token) > 1 and token not in STOP_WORDS
    }


def _best_passages(question_terms, content, limit=3):
    passages = [
        part.strip() for part in PASSAGE_SPLIT.split(content or "") if part.strip()
    ]
    if not passages:
        passages = [content.strip()] if content and content.strip() else []
    ranked = []
    for index, passage in enumerate(passages):
        passage_terms = tokens(passage)
        overlap = len(question_terms & passage_terms)
        if not overlap:
            continue
        coverage = overlap / max(1, len(question_terms))
        density = overlap / max(1, min(len(passage_terms), 50))
        score = coverage * 3 + density
        ranked.append((score, overlap, -index, passage))
    ranked.sort(reverse=True)
    return [(score, overlap, passage) for score, overlap, _, passage in ranked[:limit]]


class LLMProvider(ABC):
    @abstractmethod
    def answer(self, request): ...


class LocalGroundedProvider(LLMProvider):
    """Deterministic offline provider that answers from the retrieved passages only."""

    def answer(self, request):
        if not request.documents:
            return (
                ResponseBuilder().add_escalation().build(),
                0.0,
                "local-grounded",
                "local-v3",
            )

        question_terms = tokens(request.question)
        ranked_documents = []
        for document in request.documents:
            passages = _best_passages(question_terms, document.content)
            if not passages:
                continue
            best_score, best_overlap, _ = passages[0]
            ranked_documents.append((best_score, best_overlap, document, passages))
        ranked_documents.sort(key=lambda row: (row[0], row[1]), reverse=True)

        if not ranked_documents:
            return (
                ResponseBuilder().add_escalation().build(),
                0.0,
                "local-grounded",
                "local-v3",
            )

        answer_parts = []
        source_documents = []
        total_overlap = 0
        for _, overlap, document, passages in ranked_documents[:3]:
            source_documents.append(document)
            total_overlap = max(total_overlap, overlap)
            selected = []
            for _, _, passage in passages:
                clean = " ".join(passage.split())
                if clean:
                    selected.append(clean[:900])
            if selected:
                answer_parts.append(
                    f"[DOC:{document.id}] {document.title}\n" + "\n".join(selected)
                )

        coverage = total_overlap / max(1, len(question_terms))
        confidence = min(0.95, 0.62 + coverage * 0.30)
        answer = (
            ResponseBuilder()
            .add_summary("\n\n".join(answer_parts))
            .add_sources(source_documents)
            .build()
        )
        return answer, confidence, "local-grounded", "local-v3"


class RemoteLLMProvider(LLMProvider):
    def __init__(self):
        self.url = os.environ["LLM_API_URL"]
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.model = os.environ.get("LLM_MODEL", "default")

    def answer(self, request):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = httpx.post(
            self.url,
            headers=headers,
            json={"model": self.model, "prompt": request.prompt},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return (
            data["answer"],
            float(data.get("confidence", 0.7)),
            "remote-llm",
            self.model,
        )


class LLMProviderRegistry:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.providers = {}
        return cls._instance


class LLMProviderFactory:
    @staticmethod
    def create():
        provider_name = os.getenv("AI_PROVIDER", "local")
        registry = LLMProviderRegistry()
        if provider_name not in registry.providers:
            registry.providers[provider_name] = (
                RemoteLLMProvider()
                if provider_name in {"remote", "openai", "llama"}
                else LocalGroundedProvider()
            )
        return registry.providers[provider_name]
