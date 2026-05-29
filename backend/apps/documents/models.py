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
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["document_type"]),
            models.Index(fields=["access_level"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title
