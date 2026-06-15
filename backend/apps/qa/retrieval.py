import re
from abc import ABC, abstractmethod
from django.db.models import Case, IntegerField, Q, Value, When
from apps.documents.repositories import DocumentRepositoryFactory

class KnowledgeRetrievalStrategy(ABC):
    @abstractmethod
    def retrieve(self, user, question, limit=5): ...

class KeywordKnowledgeRetrievalStrategy(KnowledgeRetrievalStrategy):
    STOP_WORDS = {"the", "and", "for", "with", "that", "this", "what", "how", "can", "are", "is", "to", "of", "a", "an"}

    def retrieve(self, user, question, limit=5):
        tokens = [t for t in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(t) > 2 and t not in self.STOP_WORDS][:10]
        qs = DocumentRepositoryFactory.create().accessible_to(user)
        if not tokens:
            return list(qs[:limit])
        query = Q()
        for token in tokens:
            query |= Q(title__icontains=token) | Q(content__icontains=token)
        return list(qs.filter(query).distinct()[:limit])
