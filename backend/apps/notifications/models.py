"""Defines persistent data models for notification delivery and notification-center state."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    class Category(models.TextChoices):
        SYSTEM = "system", "System"
        WORKFLOW = "workflow", "Workflow"
        DOCUMENT = "document", "Document"
        ACADEMIC = "academic", "Academic"
        MANAGEMENT = "management", "Management"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=180)
    message = models.TextField()
    category = models.CharField(
        max_length=30, choices=Category.choices, default=Category.SYSTEM, db_index=True
    )
    link = models.CharField(max_length=300, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    priority = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        default="normal",
        db_index=True,
    )
    pinned_at = models.DateTimeField(null=True, blank=True, db_index=True)
    snoozed_until = models.DateTimeField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_notifications",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "read_at", "-created_at"])]


class NotificationPreference(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    enabled_categories = models.JSONField(default=list, blank=True)
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    muted_until = models.DateTimeField(null=True, blank=True)
