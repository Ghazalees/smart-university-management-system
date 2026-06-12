import logging

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.accounts.models import Role
from apps.documents.models import Document, DocumentAuditLog

logger = logging.getLogger(__name__)

ROLE_ACCESS_LEVELS = {
    Role.STUDENT: Document.AccessLevel.STUDENT,
    Role.PROFESSOR: Document.AccessLevel.PROFESSOR,
    Role.ADMINISTRATIVE_STAFF: Document.AccessLevel.STAFF,
    Role.UNIVERSITY_PRESIDENT: Document.AccessLevel.PRESIDENT,
}

DOCUMENT_MANAGER_ROLES = {Role.ADMINISTRATIVE_STAFF, Role.UNIVERSITY_PRESIDENT}
AUDIT_REDACTED_FIELDS = {"content"}


class DocumentService:
    """Business logic for document creation, retrieval, search, and visibility."""

    @staticmethod
    def visible_queryset_for_user(user, filters=None):
        """Return active documents visible to the authenticated user's role."""
        queryset = Document.objects.select_related(
            "created_by",
            "last_updated_by",
            "archived_by",
        ).filter(is_active=True)

        if not user.has_role(DOCUMENT_MANAGER_ROLES):
            access_level = ROLE_ACCESS_LEVELS.get(user.primary_role())
            allowed_levels = {Document.AccessLevel.PUBLIC}
            if access_level:
                allowed_levels.add(access_level)
            queryset = queryset.filter(access_level__in=allowed_levels)

        return DocumentService.apply_filters(queryset, filters or {})

    @staticmethod
    def apply_filters(queryset, filters):
        """Apply validated document search/filter parameters."""
        keyword = filters.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(content__icontains=keyword)
                | Q(summary__icontains=keyword)
                | Q(keywords__icontains=keyword)
            )

        title = filters.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        document_type = filters.get("document_type")
        if document_type:
            queryset = queryset.filter(document_type=document_type)

        access_level = filters.get("access_level")
        if access_level:
            queryset = queryset.filter(access_level=access_level)

        if filters.get("knowledge_base_only"):
            queryset = queryset.filter(is_knowledge_base_enabled=True)

        return queryset

    @classmethod
    @transaction.atomic
    def create_document(cls, *, data, user):
        """Create a document and attach the authenticated creator."""
        document = Document.objects.create(
            created_by=user,
            last_updated_by=user,
            **data,
        )
        cls._write_audit_log(
            document=document,
            actor=user,
            action=DocumentAuditLog.Action.CREATED,
            changes={"created": True},
        )
        logger.info(
            "Document created",
            extra={"document_id": document.id, "created_by": user.id},
        )
        return document

    @classmethod
    @transaction.atomic
    def update_document(cls, *, document, data, user):
        """Update a document, bump version, and persist an audit log."""
        changes = cls._build_change_set(document, data)
        if not changes:
            return document

        for field, value in data.items():
            setattr(document, field, value)

        document.version += 1
        document.last_updated_by = user
        document.save()

        cls._write_audit_log(
            document=document,
            actor=user,
            action=DocumentAuditLog.Action.UPDATED,
            changes=changes,
        )
        logger.info(
            "Document updated",
            extra={"document_id": document.id, "updated_by": user.id},
        )
        return document

    @classmethod
    @transaction.atomic
    def archive_document(cls, *, document, user):
        """Archive a document instead of hard-deleting it."""
        document.is_active = False
        document.archived_by = user
        document.archived_at = timezone.now()
        document.last_updated_by = user
        document.version += 1
        document.save(
            update_fields=[
                "is_active",
                "archived_by",
                "archived_at",
                "last_updated_by",
                "version",
                "updated_at",
            ]
        )
        cls._write_audit_log(
            document=document,
            actor=user,
            action=DocumentAuditLog.Action.ARCHIVED,
            changes={"is_active": {"old": True, "new": False}},
        )
        logger.info(
            "Document archived",
            extra={"document_id": document.id, "archived_by": user.id},
        )
        return document

    @classmethod
    def get_visible_document_or_403(cls, *, document_id, user):
        """Return a visible active document or raise a permission error."""
        try:
            document = Document.objects.select_related(
                "created_by",
                "last_updated_by",
                "archived_by",
            ).get(id=document_id, is_active=True)
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

    @staticmethod
    def _build_change_set(document, data):
        """Build a safe field-level diff for audit logging."""
        changes = {}
        for field, new_value in data.items():
            old_value = getattr(document, field)
            if old_value == new_value:
                continue
            changes[field] = {
                "old": DocumentService._audit_value(field, old_value),
                "new": DocumentService._audit_value(field, new_value),
            }
        return changes

    @staticmethod
    def _audit_value(field, value):
        """Avoid storing full document body content in audit logs."""
        if field in AUDIT_REDACTED_FIELDS:
            return "[content changed]"
        return value

    @staticmethod
    def _write_audit_log(*, document, actor, action, changes):
        """Create a persistent audit log row for an important document action."""
        return DocumentAuditLog.objects.create(
            document=document,
            actor=actor,
            action=action,
            changes=changes,
        )
