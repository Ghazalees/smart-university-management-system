"""Encapsulates database access and query composition for knowledge documents, versions, extraction, and governance."""

from abc import ABC, abstractmethod

from django.db.models import Q
from django.utils import timezone

from .models import Document


class DocumentSearchStrategy(ABC):
    @abstractmethod
    def search(self, queryset, keyword): ...


class SQLiteDocumentSearchStrategy(DocumentSearchStrategy):
    def search(self, queryset, keyword):
        return queryset.filter(
            Q(title__icontains=keyword) | Q(content__icontains=keyword)
        )


class DocumentRepository:
    def __init__(self, search_strategy: DocumentSearchStrategy):
        self.search_strategy = search_strategy

    def accessible_to(self, user, include_archived=False, knowledge_only=False):
        qs = Document.objects.select_related(
            "created_by", "last_updated_by"
        ).prefetch_related("allowed_roles")
        if not include_archived:
            qs = qs.exclude(status=Document.Status.ARCHIVED)
        if knowledge_only:
            now = timezone.now()
            qs = qs.filter(
                knowledge_enabled=True,
                status__in=[Document.Status.PUBLISHED, Document.Status.ACTIVE],
            ).filter(
                Q(effective_from__isnull=True) | Q(effective_from__lte=now),
                Q(expires_at__isnull=True) | Q(expires_at__gt=now),
            )
        if not getattr(user, "is_authenticated", False):
            return qs.filter(
                access_level=Document.AccessLevel.PUBLIC,
                status__in=[Document.Status.PUBLISHED, Document.Status.ACTIVE],
            )
        if user.is_superuser or user.has_system_permission("documents.manage"):
            return qs
        role_ids = user.roles.values_list("id", flat=True)
        return qs.filter(
            Q(access_level=Document.AccessLevel.PUBLIC)
            | Q(access_level=Document.AccessLevel.AUTHENTICATED)
            | Q(access_level=Document.AccessLevel.ROLE, allowed_roles__id__in=role_ids)
            | Q(access_level=Document.AccessLevel.PRIVATE, created_by=user)
        ).distinct()

    def search(
        self,
        user,
        keyword=None,
        document_type=None,
        status=None,
        access_level=None,
        include_archived=False,
    ):
        qs = self.accessible_to(user, include_archived=include_archived)
        if keyword:
            qs = self.search_strategy.search(qs, keyword.strip())
        if document_type:
            qs = qs.filter(document_type=document_type)
        if status:
            qs = qs.filter(status=status)
        if access_level:
            qs = qs.filter(access_level=access_level)
        return qs


class DocumentRepositoryFactory:
    @staticmethod
    def create():
        return DocumentRepository(SQLiteDocumentSearchStrategy())


class DocumentAccessProxy:
    """Proxy that ensures access filtering is never bypassed by detail retrieval."""

    def __init__(self, repository=None):
        self.repository = repository or DocumentRepositoryFactory.create()

    def get(self, user, pk, include_archived=False):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(
            self.repository.accessible_to(user, include_archived=include_archived),
            pk=pk,
        )
