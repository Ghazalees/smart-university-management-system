"""Declares API routes for grounded question answering, retrieval, and AI orchestration."""

from django.urls import path

from .views import (
    AnalyzeRequestView,
    MyQuestionsView,
    QuestionAnswerView,
    QuestionDetailView,
    QuestionHistoryView,
    QuestionHumanAnswerView,
    QuestionListCreateView,
    QuestionResponseFeedbackView,
)

urlpatterns = [
    path("questions", QuestionListCreateView.as_view(), name="questions"),
    path("questions/my", MyQuestionsView.as_view(), name="my-questions"),
    path("questions/<int:pk>", QuestionDetailView.as_view(), name="question-detail"),
    path(
        "questions/<int:pk>/answer",
        QuestionAnswerView.as_view(),
        name="question-answer",
    ),
    path(
        "questions/<int:pk>/human-answer",
        QuestionHumanAnswerView.as_view(),
        name="question-human-answer",
    ),
    path(
        "questions/<int:pk>/history",
        QuestionHistoryView.as_view(),
        name="question-history",
    ),
    path(
        "questions/<int:pk>/feedback",
        QuestionResponseFeedbackView.as_view(),
        name="question-feedback",
    ),
    path("ai/analyze-request", AnalyzeRequestView.as_view(), name="analyze-request"),
]
