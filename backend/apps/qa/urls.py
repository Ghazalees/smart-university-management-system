from django.urls import path

from .views import (
    AnalyzeRequestView,
    MyQuestionsView,
    QuestionAnswerView,
    QuestionCreateView,
    QuestionDetailView,
    QuestionHistoryView,
)

urlpatterns = [
    path("questions", QuestionCreateView.as_view(), name="question-create"),
    path("questions/my", MyQuestionsView.as_view(), name="my-questions"),
    path("questions/<int:pk>", QuestionDetailView.as_view(), name="question-detail"),
    path(
        "questions/<int:pk>/answer",
        QuestionAnswerView.as_view(),
        name="question-answer",
    ),
    path(
        "questions/<int:pk>/history",
        QuestionHistoryView.as_view(),
        name="question-history",
    ),
    path("ai/analyze-request", AnalyzeRequestView.as_view(), name="analyze-request"),
]
