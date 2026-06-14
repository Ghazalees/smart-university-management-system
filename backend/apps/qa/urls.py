from django.urls import path

from apps.qa.views import (
    MyQuestionsView,
    QuestionAnswerView,
    QuestionCreateView,
    QuestionDetailView,
    QuestionHistoryView,
)

urlpatterns = [
    path("questions", QuestionCreateView.as_view(), name="questions-create"),
    path("questions/my", MyQuestionsView.as_view(), name="questions-my"),
    path("questions/<int:question_id>", QuestionDetailView.as_view(), name="questions-detail"),
    path("questions/<int:question_id>/answer", QuestionAnswerView.as_view(), name="questions-answer"),
    path("questions/<int:question_id>/history", QuestionHistoryView.as_view(), name="questions-history"),
]
