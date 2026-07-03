"""Defines persistent data models for user experience preferences, feedback, search, and calendar features."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class UserExperiencePreference(TimeStampedModel):
    class Density(models.TextChoices):
        COMFORTABLE = "comfortable", "Comfortable"
        COMPACT = "compact", "Compact"

    class DigestFrequency(models.TextChoices):
        OFF = "off", "Off"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="experience_preferences",
    )
    accent_color = models.CharField(max_length=20, default="indigo")
    density = models.CharField(
        max_length=20, choices=Density.choices, default=Density.COMFORTABLE
    )
    reduced_motion = models.BooleanField(default=False)
    high_contrast = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default="en")
    dashboard_layout = models.JSONField(default=list, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    digest_frequency = models.CharField(
        max_length=20,
        choices=DigestFrequency.choices,
        default=DigestFrequency.DAILY,
    )


class Feedback(TimeStampedModel):
    class Type(models.TextChoices):
        BUG = "bug", "Bug"
        IDEA = "idea", "Idea"
        UX = "ux", "UX feedback"
        AI = "ai", "AI feedback"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        NEW = "new", "New"
        TRIAGED = "triaged", "Triaged"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedback_items",
    )
    feedback_type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=180)
    message = models.TextField()
    page = models.CharField(max_length=300, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, db_index=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_feedback",
    )
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "feedback_type", "-created_at"],
                name="experience__status_568f3a_idx",
            )
        ]
