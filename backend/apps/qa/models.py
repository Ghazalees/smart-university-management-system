from django.conf import settings
from django.db import models


class Question(models.Model):
    """Store a submitted university question and its processing status."""

    STATUS_PENDING = "Pending"
    STATUS_ANSWERED = "Answered"
    STATUS_ESCALATED = "Escalated"
    STATUS_FAILED = "Failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ANSWERED, "Answered"),
        (STATUS_ESCALATED, "Escalated"),
        (STATUS_FAILED, "Failed"),
    ]

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    title = models.CharField(max_length=180)
    body = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"
        ordering = ["-created_at"]

    def __str__(self):
        """Return a readable question label."""
        return self.title


class QuestionResponse(models.Model):
    """Store one response generated or recorded for a submitted question."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="responses")
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_responses",
    )
    body = models.TextField()
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    source_documents = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "question_responses"
        ordering = ["-created_at"]

    def __str__(self):
        """Return a readable question response label."""
        return f"Response for question {self.question_id}"


class QuestionHistory(models.Model):
    """Store timeline events for question submission, answer, and status changes."""

    EVENT_SUBMITTED = "SUBMITTED"
    EVENT_ANSWERED = "ANSWERED"
    EVENT_STATUS_CHANGED = "STATUS_CHANGED"

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="history")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_history_events",
    )
    event = models.CharField(max_length=80)
    status_from = models.CharField(max_length=20, blank=True)
    status_to = models.CharField(max_length=20, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "question_history"
        ordering = ["created_at"]

    def __str__(self):
        """Return a readable history event label."""
        return f"{self.event} for question {self.question_id}"
