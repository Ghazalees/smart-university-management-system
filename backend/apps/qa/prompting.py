class PromptBuilder:
    """Builder pattern for deterministic, documented prompts."""
    def __init__(self):
        self._parts = []

    def with_policy(self):
        self._parts.append(
            "Answer only from the supplied university documents. "
            "If the documents are insufficient, clearly say so and recommend human review."
        )
        return self

    def with_question(self, question):
        self._parts.append(f"QUESTION:\n{question.strip()}")
        return self

    def with_documents(self, documents):
        blocks = []
        for doc in documents:
            blocks.append(f"[DOCUMENT {doc.id}: {doc.title}]\n{doc.content}")
        self._parts.append("CONTEXT:\n" + "\n\n".join(blocks))
        return self

    def build(self):
        return "\n\n".join(self._parts)
