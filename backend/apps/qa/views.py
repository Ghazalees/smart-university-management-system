from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import success

from .adapters import AIProviderFactory
from .analysis import KeywordRequestAnalysisStrategy
from .models import Question
from .permissions import CanAnswerQuestion, CanCreateQuestion
from .serializers import (
    AnalyzeRequestSerializer,
    QuestionCreateSerializer,
    QuestionHistorySerializer,
    QuestionResponseSerializer,
    QuestionSerializer,
)
from .services import QuestionService
from .workflows import GenerateAnswerCommand


def accessible_questions(user):
    qs = Question.objects.select_related("user", "response").prefetch_related(
        "response__sources", "history"
    )
    if user.has_system_permission("questions.view_all"):
        return qs
    return qs.filter(user=user)


class QuestionCreateView(APIView):
    permission_classes = [CanCreateQuestion]

    def post(self, request):
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = QuestionService.create(
            user=request.user, text=serializer.validated_data["text"]
        )
        return success(
            QuestionSerializer(question).data,
            "Question submitted",
            status.HTTP_201_CREATED,
        )


class MyQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success(
            QuestionSerializer(
                Question.objects.filter(user=request.user)
                .select_related("response")
                .prefetch_related("response__sources"),
                many=True,
            ).data
        )


class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(accessible_questions(request.user), pk=pk)
        return success(QuestionSerializer(question).data)


class QuestionAnswerView(APIView):
    permission_classes = [CanAnswerQuestion]

    def post(self, request, pk):
        question = get_object_or_404(accessible_questions(request.user), pk=pk)
        response = GenerateAnswerCommand(question, request.user).execute()
        return success(
            {
                "question": QuestionSerializer(question).data,
                "answer": QuestionResponseSerializer(response).data,
            },
            "Answer generated",
        )


class QuestionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(accessible_questions(request.user), pk=pk)
        return success(
            QuestionHistorySerializer(question.history.all(), many=True).data
        )


class AnalyzeRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data["text"]
        try:
            data = AIProviderFactory.create().analyze(text)
        except Exception as exc:
            from .exceptions import AIServiceUnavailable

            if not isinstance(exc, AIServiceUnavailable):
                raise
            fallback = KeywordRequestAnalysisStrategy().analyze(text)
            data = {
                "category": fallback.category,
                "priority": fallback.priority,
                "confidence": fallback.confidence,
                "suggested_workflow": fallback.suggested_workflow,
                "source": "local-fallback",
            }
        return success(data)
