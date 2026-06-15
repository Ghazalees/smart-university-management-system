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
        OTHER = "other", "Other"
    class AccessLevel(models.TextChoices):
        PUBLIC = "public", "Public"
        AUTHENTICATED = "authenticated", "Authenticated"
        ROLE = "role", "Role restricted"
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255, db_index=True)
    document_type = models.CharField(max_length=30, choices=Type.choices, default=Type.OTHER, db_index=True)
    content = models.TextField()
    access_level = models.CharField(max_length=30, choices=AccessLevel.choices, default=AccessLevel.AUTHENTICATED, db_index=True)
    allowed_roles = models.ManyToManyField(Role, blank=True, related_name="documents")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_documents")
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["status", "document_type"])]

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=["status", "archived_at", "updated_at"])
