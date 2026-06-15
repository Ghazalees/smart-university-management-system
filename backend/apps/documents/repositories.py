from abc import ABC, abstractmethod
from django.db.models import Q
from .models import Document

class DocumentSearchStrategy(ABC):
    @abstractmethod
    def search(self, queryset, keyword): ...

class SQLiteDocumentSearchStrategy(DocumentSearchStrategy):
    def search(self, queryset, keyword):
        return queryset.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))

class DocumentRepository:
    def __init__(self, search_strategy: DocumentSearchStrategy):
        self.search_strategy = search_strategy

    def accessible_to(self, user, include_archived=False):
        qs = Document.objects.select_related("created_by").prefetch_related("allowed_roles")
        if not include_archived:
            qs = qs.filter(status=Document.Status.ACTIVE)
        if user.is_superuser or user.has_system_permission("documents.manage"):
            return qs
        role_ids = user.roles.values_list("id", flat=True)
        return qs.filter(Q(access_level=Document.AccessLevel.PUBLIC) | Q(access_level=Document.AccessLevel.AUTHENTICATED) | Q(access_level=Document.AccessLevel.ROLE, allowed_roles__id__in=role_ids)).distinct()

    def search(self, user, keyword=None, document_type=None):
        qs = self.accessible_to(user)
        if keyword:
            qs = self.search_strategy.search(qs, keyword.strip())
        if document_type:
            qs = qs.filter(document_type=document_type)
        return qs

class DocumentRepositoryFactory:
    @staticmethod
    def create():
        return DocumentRepository(SQLiteDocumentSearchStrategy())

class DocumentAccessProxy:
    """Proxy that ensures access filtering is never bypassed by detail retrieval."""
    def __init__(self, repository=None):
        self.repository = repository or DocumentRepositoryFactory.create()
    def get(self, user, pk):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(self.repository.accessible_to(user), pk=pk)
