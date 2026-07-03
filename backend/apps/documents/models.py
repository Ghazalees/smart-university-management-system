"""Defines persistent data models for knowledge documents, versions, extraction, and governance."""

import hashlib

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import Role
from apps.core.models import TimeStampedModel


class Document(TimeStampedModel):
    class Type(models.TextChoices):
        POLICY = "policy", "Policy"
        REGULATION = "regulation", "Regulation"
        FAQ = "faq", "FAQ"
        GUIDE = "guide", "Guide"
        ACADEMIC = "academic", "Academic"
        FINANCIAL = "financial", "Financial"
        RESEARCH = "research", "Research"
        ADMINISTRATIVE = "administrative", "Administrative"
        OTHER = "other", "Other"

    class AccessLevel(models.TextChoices):
        PUBLIC = "public", "Public"
        AUTHENTICATED = "authenticated", "Authenticated users"
        ROLE = "role", "Role restricted"
        PRIVATE = "private", "Owner and document managers"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ACTIVE = "active", "Active (legacy)"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255, db_index=True)
    document_type = models.CharField(
        max_length=30, choices=Type.choices, default=Type.OTHER, db_index=True
    )
    content = models.TextField()
    access_level = models.CharField(
        max_length=30,
        choices=AccessLevel.choices,
        default=AccessLevel.AUTHENTICATED,
        db_index=True,
    )
    allowed_roles = models.ManyToManyField(Role, blank=True, related_name="documents")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PUBLISHED,
        db_index=True,
    )
    knowledge_enabled = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_documents",
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_documents",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    indexed_at = models.DateTimeField(null=True, blank=True)
    content_checksum = models.CharField(max_length=64, blank=True)
    index_version = models.PositiveIntegerField(default=0)
    effective_from = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    review_due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    review_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents_to_review",
    )
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "document_type"]),
            models.Index(fields=["knowledge_enabled", "status"]),
        ]

    def calculate_checksum(self):
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def mark_indexed(self):
        self.content_checksum = self.calculate_checksum()
        self.indexed_at = timezone.now()
        self.index_version += 1
        self.save(
            update_fields=[
                "content_checksum",
                "indexed_at",
                "index_version",
                "updated_at",
            ]
        )

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=["status", "archived_at", "updated_at"])


class DocumentVersion(TimeStampedModel):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    snapshot = models.JSONField(default=dict)
    content_checksum = models.CharField(max_length=64)
    change_summary = models.CharField(max_length=300, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="document_versions_created",
    )

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_number"],
                name="unique_document_version_number",
            )
        ]

    def __str__(self):
        return f"{self.document_id} v{self.version_number}"
