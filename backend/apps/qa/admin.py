from django.contrib import admin

from apps.qa.models import Question, QuestionHistory, QuestionResponse


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Display submitted questions in Django admin."""

    list_display = ("id", "title", "submitted_by", "status", "category", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "body", "submitted_by__email")


@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    """Display stored question responses in Django admin."""

    list_display = ("id", "question", "responder", "confidence", "created_at")
    search_fields = ("body", "question__title", "responder__email")


@admin.register(QuestionHistory)
class QuestionHistoryAdmin(admin.ModelAdmin):
    """Display question history events in Django admin."""

    list_display = ("id", "question", "actor", "event", "status_from", "status_to", "created_at")
    list_filter = ("event", "status_to")
    search_fields = ("question__title", "actor__email", "note")
