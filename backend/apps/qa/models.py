"""Defines persistent data models for grounded question answering, retrieval, and AI orchestration."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.documents.models import Document


class Question(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        ANSWERED = "Answered", "Answered"
        ESCALATED = "Escalated", "Escalated"
        FAILED = "Failed", "Failed"

    class Priority(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"
        URGENT = "Urgent", "Urgent"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    category = models.CharField(max_length=80, blank=True, db_index=True)
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM, db_index=True
    )
    analysis_confidence = models.FloatField(null=True, blank=True)
    suggested_workflow = models.CharField(max_length=120, blank=True)
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"])]


class QuestionResponse(TimeStampedModel):
    question = models.OneToOneField(
        Question, on_delete=models.CASCADE, related_name="response"
    )
    answer = models.TextField()
    confidence = models.FloatField()
    provider = models.CharField(max_length=100)
    model_name = models.CharField(max_length=120, blank=True)
    is_documented = models.BooleanField(default=True)
    sources = models.ManyToManyField(
        Document, blank=True, related_name="question_responses"
    )
    citations = models.JSONField(default=list, blank=True)
    retrieval_metadata = models.JSONField(default=dict, blank=True)
    safety_status = models.CharField(max_length=40, default="grounded")
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    user_rating = models.SmallIntegerField(null=True, blank=True)
    user_feedback = models.TextField(blank=True)


class QuestionHistory(TimeStampedModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="history"
    )
    event = models.CharField(max_length=100, db_index=True)
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]
