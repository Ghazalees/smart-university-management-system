"""Defines persistent data models for university requests, assignments, statuses, and revisions."""

import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import Role
from apps.core.models import TimeStampedModel


def generate_request_number():
    return f"REQ-{timezone.now():%Y%m%d}-{secrets.token_hex(3).upper()}"


class WorkflowType(TimeStampedModel):
    code = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    allowed_roles = models.ManyToManyField(
        Role, blank=True, related_name="workflow_types"
    )
    schema = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkflowRequest(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under review"
        NEEDS_REVISION = "needs_revision", "Needs revision"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    request_number = models.CharField(
        max_length=40, unique=True, default=generate_request_number, editable=False
    )
    request_type = models.ForeignKey(
        WorkflowType, on_delete=models.PROTECT, related_name="requests"
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workflow_requests",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    current_step = models.CharField(max_length=100, default="draft")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_workflow_requests",
    )
    decision_reason = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["requester", "status"]),
        ]


class WorkflowHistory(TimeStampedModel):
    request = models.ForeignKey(
        WorkflowRequest, on_delete=models.CASCADE, related_name="history"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="workflow_actions",
    )
    event = models.CharField(max_length=60)
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30, blank=True)
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]
