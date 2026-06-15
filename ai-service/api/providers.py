from abc import ABC, abstractmethod
import os
import re
import httpx
from .prompting import ResponseBuilder

class LLMProvider(ABC):
    @abstractmethod
    def answer(self, request): ...

class LocalGroundedProvider(LLMProvider):
    """Deterministic provider used for offline development and tests."""
    def answer(self, request):
        if not request.documents:
            return ResponseBuilder().add_escalation().build(), 0.2, "local-grounded", "local-v1"
        terms = {t for t in re.findall(r"[a-zA-Z0-9]+", request.question.lower()) if len(t) > 2}
        ranked = []
        for doc in request.documents:
            text = f"{doc.title} {doc.content}".lower()
            score = sum(term in text for term in terms)
            ranked.append((score, doc))
        ranked.sort(key=lambda x: x[0], reverse=True)
        best = [doc for score, doc in ranked if score > 0][:3] or [request.documents[0]]
        snippets = []
        for doc in best:
            clean = " ".join(doc.content.split())
            snippets.append(f"According to {doc.title}: {clean[:500]}")
        confidence = min(0.92, 0.52 + 0.08 * max(1, ranked[0][0]))
        answer = ResponseBuilder().add_summary("\n".join(snippets)).add_sources(best).build()
        return answer, confidence, "local-grounded", "local-v1"

class RemoteLLMProvider(LLMProvider):
    def __init__(self):
        self.url = os.environ["LLM_API_URL"]
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.model = os.environ.get("LLM_MODEL", "default")
    def answer(self, request):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = httpx.post(self.url, headers=headers, json={"model": self.model, "prompt": request.prompt}, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data["answer"], float(data.get("confidence", 0.7)), "remote-llm", self.model

class LLMProviderFactory:
    @staticmethod
    def create():
        return RemoteLLMProvider() if os.getenv("AI_PROVIDER", "local") == "remote" else LocalGroundedProvider()
