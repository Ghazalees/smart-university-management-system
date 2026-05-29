import logging

from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

from apps.accounts.models import Role
from apps.documents.models import Document

logger = logging.getLogger(__name__)


ROLE_ACCESS_LEVELS = {
    Role.STUDENT: Document.AccessLevel.STUDENT,
    Role.PROFESSOR: Document.AccessLevel.PROFESSOR,
    Role.ADMINISTRATIVE_STAFF: Document.AccessLevel.STAFF,
    Role.UNIVERSITY_PRESIDENT: Document.AccessLevel.PRESIDENT,
}

DOCUMENT_MANAGER_ROLES = {Role.ADMINISTRATIVE_STAFF, Role.UNIVERSITY_PRESIDENT}


class DocumentService:
    """Business logic for document creation, retrieval, search, and visibility."""

    @staticmethod
    def visible_queryset_for_user(user, filters=None):
        """Return active documents visible to the authenticated user's role."""
        queryset = Document.objects.select_related("created_by").filter(is_active=True)

        if not user.has_role(DOCUMENT_MANAGER_ROLES):
            access_level = ROLE_ACCESS_LEVELS.get(user.primary_role())
            if not access_level:
                queryset = queryset.filter(access_level=Document.AccessLevel.PUBLIC)
            else:
                queryset = queryset.filter(
                    Q(access_level=Document.AccessLevel.PUBLIC) | Q(access_level=access_level)
                )

        return DocumentService.apply_filters(queryset, filters or {})

    @staticmethod
    def apply_filters(queryset, filters):
        """Apply validated document search/filter parameters."""
        keyword = filters.get("keyword")
        if keyword:
            queryset = queryset.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))

        document_type = filters.get("document_type")
        if document_type:
            queryset = queryset.filter(document_type=document_type)

        access_level = filters.get("access_level")
        if access_level:
            queryset = queryset.filter(access_level=access_level)

        return queryset

    @classmethod
    def create_document(cls, *, data, user):
        """Create a document and attach the authenticated creator."""
        document = Document.objects.create(created_by=user, **data)
        logger.info(
            "Document created",
            extra={"document_id": document.id, "created_by": user.id},
        )
        return document

    @classmethod
    def update_document(cls, *, document, data, user):
        """Update a document and log the content-management action."""
        for field, value in data.items():
            setattr(document, field, value)
        document.save()
        logger.info(
            "Document updated",
            extra={"document_id": document.id, "updated_by": user.id},
        )
        return document

    @classmethod
    def archive_document(cls, *, document, user):
        """Archive a document instead of hard-deleting it."""
        document.is_active = False
        document.save(update_fields=["is_active", "updated_at"])
        logger.info(
            "Document archived",
            extra={"document_id": document.id, "archived_by": user.id},
        )
        return document

    @classmethod
    def get_visible_document_or_403(cls, *, document_id, user):
        """Return a visible document or raise a permission error."""
        try:
            document = Document.objects.select_related("created_by").get(id=document_id, is_active=True)
        except Document.DoesNotExist as exc:
            raise PermissionDenied("Document was not found or is not accessible.") from exc

        if user.has_role(DOCUMENT_MANAGER_ROLES):
            return document

        access_level = ROLE_ACCESS_LEVELS.get(user.primary_role())
        allowed_levels = {Document.AccessLevel.PUBLIC}
        if access_level:
            allowed_levels.add(access_level)

        if document.access_level not in allowed_levels:
            raise PermissionDenied("You do not have access to this document.")

        return document
