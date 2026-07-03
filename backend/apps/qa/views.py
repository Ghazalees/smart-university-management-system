"""Implements authenticated API endpoints for grounded question answering, retrieval, and AI orchestration."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.pagination import PaginationMixin
from apps.core.responses import success

from .adapters import AIProviderFactory
from .analysis import KeywordRequestAnalysisStrategy
from .models import Question
from .permissions import CanAnswerQuestion, CanCreateQuestion, CanGenerateQuestionAnswer
from .serializers import (
    AIResponseFeedbackSerializer,
    AnalyzeRequestSerializer,
    HumanAnswerSerializer,
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


class QuestionListCreateView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

    def get(self, request):
        qs = accessible_questions(request.user)
        status_value = request.query_params.get("status")
        search = request.query_params.get("search", "").strip()
        if status_value:
            qs = qs.filter(status=status_value)
        if search:
            qs = qs.filter(
                Q(text__icontains=search) | Q(response__answer__icontains=search)
            )
        return self.paginate(request, qs, QuestionSerializer)

    def post(self, request):
        if not CanCreateQuestion().has_permission(request, self):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied()
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


class MyQuestionsView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Question.objects.filter(user=request.user)
            .select_related("response")
            .prefetch_related("response__sources")
        )
        return self.paginate(request, qs, QuestionSerializer)


class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(accessible_questions(request.user), pk=pk)
        return success(QuestionSerializer(question).data)


class QuestionAnswerView(APIView):
    permission_classes = [CanGenerateQuestionAnswer]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

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


class QuestionHumanAnswerView(APIView):
    permission_classes = [CanAnswerQuestion]

    def post(self, request, pk):
        question = get_object_or_404(accessible_questions(request.user), pk=pk)
        serializer = HumanAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sources = serializer.validated_data.get("sources", [])
        if sources:
            from apps.documents.repositories import DocumentRepositoryFactory

            visible_ids = set(
                DocumentRepositoryFactory.create()
                .accessible_to(question.user)
                .filter(pk__in=[source.pk for source in sources])
                .values_list("pk", flat=True)
            )
            if visible_ids != {source.pk for source in sources}:
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "source_ids": "Every cited source must be accessible to the question owner."
                    }
                )
        response = QuestionService.human_answer(
            question=question,
            actor=request.user,
            answer=serializer.validated_data["answer"],
            sources=sources,
        )
        return success(QuestionResponseSerializer(response).data, "Human answer saved")


class QuestionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(accessible_questions(request.user), pk=pk)
        return success(
            QuestionHistorySerializer(question.history.all(), many=True).data
        )


class AnalyzeRequestView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

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


class QuestionResponseFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        question = get_object_or_404(
            Question.objects.filter(user=request.user).select_related("response"), pk=pk
        )
        if not hasattr(question, "response"):
            from rest_framework.exceptions import ValidationError

            raise ValidationError("This question does not have an answer yet.")
        serializer = AIResponseFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question.response.user_rating = serializer.validated_data["rating"]
        question.response.user_feedback = serializer.validated_data.get("comment", "")
        question.response.save(
            update_fields=["user_rating", "user_feedback", "updated_at"]
        )
        from apps.core.services import AuditEvent, AuditService

        AuditService.record(
            AuditEvent(
                "ai.response_feedback",
                "QuestionResponse",
                question.response.pk,
                {"rating": question.response.user_rating},
            ),
            actor=request.user,
            request=request,
        )
        return success(
            QuestionResponseSerializer(question.response).data, "Feedback recorded"
        )
