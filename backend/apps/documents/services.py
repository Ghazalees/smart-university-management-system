"""Contains reusable business logic for knowledge documents, versions, extraction, and governance."""

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .decorators import audited
from .models import Document, DocumentVersion
from .observers import DocumentEvent, DocumentEventPublisher


class DocumentVersionService:
    SNAPSHOT_FIELDS = (
        "title",
        "document_type",
        "content",
        "access_level",
        "status",
        "knowledge_enabled",
        "effective_from",
        "expires_at",
        "review_due_at",
        "tags",
    )

    @classmethod
    def snapshot(cls, document, actor, summary=""):
        next_number = (
            document.versions.aggregate(value=Max("version_number"))["value"] or 0
        ) + 1
        payload = {}
        for field in cls.SNAPSHOT_FIELDS:
            value = getattr(document, field)
            payload[field] = (
                value.isoformat()
                if hasattr(value, "isoformat") and value is not None
                else value
            )
        payload["allowed_role_ids"] = list(
            document.allowed_roles.values_list("id", flat=True)
        )
        return DocumentVersion.objects.create(
            document=document,
            version_number=next_number,
            snapshot=payload,
            content_checksum=document.calculate_checksum(),
            change_summary=(summary or "Document updated")[:300],
            created_by=actor,
        )

    @classmethod
    @transaction.atomic
    def restore(cls, version, actor):
        document = Document.objects.select_for_update().get(pk=version.document_id)
        data = dict(version.snapshot)
        role_ids = data.pop("allowed_role_ids", [])
        for field in cls.SNAPSHOT_FIELDS:
            if field not in data:
                continue
            value = data[field]
            if field in {"effective_from", "expires_at", "review_due_at"} and value:
                from django.utils.dateparse import parse_datetime

                value = parse_datetime(value)
            setattr(document, field, value)
        document.last_updated_by = actor
        document.save()
        document.allowed_roles.set(role_ids)
        cls.snapshot(document, actor, f"Restored from version {version.version_number}")
        return document


class DocumentService:
    @staticmethod
    @transaction.atomic
    @audited("document.created")
    def create(
        *,
        actor,
        request=None,
        allowed_roles=None,
        change_summary="Initial version",
        **data,
    ):
        document = Document.objects.create(
            created_by=actor, last_updated_by=actor, **data
        )
        if allowed_roles is not None:
            document.allowed_roles.set(allowed_roles)
        DocumentVersionService.snapshot(document, actor, change_summary)
        DocumentEventPublisher.publish(DocumentEvent(document, "created", actor))
        return document

    @staticmethod
    @transaction.atomic
    @audited("document.updated")
    def update(
        document, *, actor, request=None, allowed_roles=None, change_summary="", **data
    ):
        for field, value in data.items():
            setattr(document, field, value)
        document.last_updated_by = actor
        document.save()
        if allowed_roles is not None:
            document.allowed_roles.set(allowed_roles)
        DocumentVersionService.snapshot(
            document, actor, change_summary or "Document updated"
        )
        DocumentEventPublisher.publish(DocumentEvent(document, "updated", actor))
        return document

    @staticmethod
    @transaction.atomic
    @audited("document.published")
    def publish(document, *, actor, request=None):
        document.status = Document.Status.PUBLISHED
        document.published_at = timezone.now()
        document.archived_at = None
        document.last_updated_by = actor
        document.save()
        DocumentVersionService.snapshot(document, actor, "Published")
        DocumentEventPublisher.publish(DocumentEvent(document, "published", actor))
        return document

    @staticmethod
    @transaction.atomic
    @audited("document.archived")
    def archive(document, *, actor, request=None):
        document.archive()
        DocumentVersionService.snapshot(document, actor, "Archived")
        return document

    @staticmethod
    @transaction.atomic
    @audited("document.restored")
    def restore(document, *, actor, request=None):
        document.status = Document.Status.DRAFT
        document.archived_at = None
        document.last_updated_by = actor
        document.save(
            update_fields=["status", "archived_at", "last_updated_by", "updated_at"]
        )
        DocumentVersionService.snapshot(document, actor, "Restored as draft")
        return document
