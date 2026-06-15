class ResponseBuilder:
    """Builder pattern for readable source-grounded responses."""

    def __init__(self):
        self._parts = []

    def add_summary(self, text):
        self._parts.append(text.strip())
        return self

    def add_sources(self, documents):
        if documents:
            self._parts.append(
                "Sources: " + "; ".join(f"[{d.id}] {d.title}" for d in documents)
            )
        return self

    def add_escalation(self):
        self._parts.append(
            "The available documents are not sufficient for a reliable answer. Please escalate this request to university staff."
        )
        return self

    def build(self):
        return "\n\n".join(self._parts)
