"""Analyzes incoming questions and classifies intent for grounded response generation."""


class RequestAnalyzer:
    RULES = {
        "registration": ("enroll", "registration", "course add", "course drop"),
        "finance": ("tuition", "payment", "fee", "scholarship", "refund"),
        "academic": ("grade", "exam", "class", "course"),
        "technical_support": ("login", "password", "portal", "error"),
        "administrative": ("transcript", "certificate", "letter", "request"),
    }

    def analyze(self, text):
        normalized = text.lower()
        scores = {
            name: sum(term in normalized for term in terms)
            for name, terms in self.RULES.items()
        }
        category, score = max(scores.items(), key=lambda item: item[1])
        if score == 0:
            category = "general"
        priority = (
            "Urgent"
            if any(x in normalized for x in ("urgent", "deadline today"))
            else "High"
            if "deadline" in normalized
            else "Medium"
        )
        workflow = {
            "registration": "registrar-review",
            "finance": "finance-office-review",
            "academic": "academic-department-review",
            "technical_support": "it-support-review",
            "administrative": "administrative-staff-review",
            "general": "general-support-review",
        }[category]
        return {
            "category": category,
            "priority": priority,
            "confidence": min(0.95, 0.45 + score * 0.18) if score else 0.35,
            "suggested_workflow": workflow,
            "source": "rule-analysis",
        }
