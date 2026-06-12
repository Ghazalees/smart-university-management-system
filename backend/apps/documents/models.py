from django.conf import settings
from django.db import models


class Document(models.Model):
    """Store university document metadata and content for role-based access."""

    class DocumentType(models.TextChoices):
        POLICY = "policy", "Policy"
        FAQ = "faq", "FAQ"
        GUIDE = "guide", "Guide"
        FORM = "form", "Form"
        ANNOUNCEMENT = "announcement", "Announcement"
        OTHER = "other", "Other"

    class AccessLevel(models.TextChoices):
        PUBLIC = "public", "Public"
        STUDENT = "student", "Student"
        PROFESSOR = "professor", "Professor"
        STAFF = "staff", "Administrative Staff"
        PRESIDENT = "president", "University President"

    title = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=40,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )
    access_level = models.CharField(
        max_length=40,
        choices=AccessLevel.choices,
        default=AccessLevel.PUBLIC,
    )
    content = models.TextField(blank=True)

    # Sprint 2 knowledge-base preparation fields for later AI/documented-answer usage.
    summary = models.TextField(blank=True)
    keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords used for document search and AI retrieval.",
    )
    is_knowledge_base_enabled = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_documents",
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_updated_documents",
    )
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archived_documents",
    )
    archived_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["document_type"], name="documents_documen_fc21d0_idx"),
            models.Index(fields=["access_level"], name="documents_access__ab8fbf_idx"),
            models.Index(fields=["is_active"], name="documents_is_acti_a803bb_idx"),
            models.Index(fields=["title"], name="documents_title_3f6c9c_idx"),
            models.Index(fields=["updated_at"], name="documents_updated_5ad4a2_idx"),
            models.Index(fields=["is_knowledge_base_enabled"], name="documents_is_know_31f7bb_idx"),
        ]

    def __str__(self):
        return self.title


class DocumentAuditLog(models.Model):
    """Persist important document-management actions for Sprint 2 audit requirements."""

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        ARCHIVED = "archived", "Archived"

    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_audit_logs",
    )
    action = models.CharField(max_length=40, choices=Action.choices)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action"], name="document_au_action_2701ba_idx"),
            models.Index(fields=["created_at"], name="document_au_created_0787a9_idx"),
            models.Index(fields=["document", "action"], name="document_au_documen_e04a61_idx"),
        ]

    def __str__(self):
        document_id = self.document_id or "deleted"
        return f"Document {document_id} {self.action}"
