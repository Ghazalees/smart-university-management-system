from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True)
class AnalysisResult:
    category: str
    priority: str
    confidence: float
    suggested_workflow: str

class RequestAnalysisStrategy(ABC):
    @abstractmethod
    def analyze(self, text: str) -> AnalysisResult: ...

class KeywordRequestAnalysisStrategy(RequestAnalysisStrategy):
    CATEGORY_RULES = {
        "registration": ("enroll", "registration", "course add", "course drop"),
        "finance": ("tuition", "payment", "fee", "scholarship", "refund"),
        "academic": ("grade", "exam", "professor", "class", "course"),
        "technical_support": ("login", "password", "portal", "error", "website"),
        "administrative": ("certificate", "transcript", "letter", "request"),
    }
    URGENT_TERMS = ("urgent", "deadline today", "immediately", "blocked")
    HIGH_TERMS = ("deadline", "cannot access", "exam tomorrow", "payment failed")

    def analyze(self, text):
        normalized = text.lower()
        scored = {category: sum(term in normalized for term in terms) for category, terms in self.CATEGORY_RULES.items()}
        category, score = max(scored.items(), key=lambda item: item[1])
        if score == 0:
            category = "general"
        if any(term in normalized for term in self.URGENT_TERMS):
            priority = "Urgent"
        elif any(term in normalized for term in self.HIGH_TERMS):
            priority = "High"
        else:
            priority = "Medium"
        confidence = min(0.95, 0.45 + score * 0.18) if score else 0.35
        workflow = {
            "registration": "registrar-review",
            "finance": "finance-office-review",
            "academic": "academic-department-review",
            "technical_support": "it-support-review",
            "administrative": "administrative-staff-review",
            "general": "general-support-review",
        }[category]
        return AnalysisResult(category, priority, confidence, workflow)
