from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import BearerTokenAuthentication
from apps.core.responses import api_success
from apps.qa.permissions import CanAnswerQuestions, CanSubmitQuestions
from apps.qa.serializers import (
    QuestionAnswerSerializer,
    QuestionCreateSerializer,
    QuestionHistorySerializer,
    QuestionReadSerializer,
    QuestionResponseReadSerializer,
)
from apps.qa.services import QuestionAccessService, QuestionService


class QuestionCreateView(APIView):
    """Handle question submission for authenticated university users."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated, CanSubmitQuestions]

    def post(self, request):
        """Create a pending question for the current authenticated user."""
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = QuestionService.submit_question(request.user, serializer.validated_data)
        return api_success(
            message="Question submitted successfully.",
            data=QuestionReadSerializer(question).data,
            status_code=status.HTTP_201_CREATED,
        )


class MyQuestionsView(APIView):
    """Handle retrieval of questions submitted by the current user."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return only the current user's submitted questions."""
        questions = QuestionService.list_my_questions(request.user)
        return api_success(
            message="My questions retrieved successfully.",
            data=QuestionReadSerializer(questions, many=True).data,
            meta={"count": questions.count()},
        )


class QuestionDetailView(APIView):
    """Handle authorized retrieval of one question and its latest answer."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        """Return question details when the current user has access."""
        question = QuestionAccessService.get_question_or_403(question_id, request.user)
        return api_success(
            message="Question retrieved successfully.",
            data=QuestionReadSerializer(question).data,
        )


class QuestionAnswerView(APIView):
    """Handle answer creation and status updates for selected questions."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated, CanAnswerQuestions]

    def post(self, request, question_id):
        """Create an answer and update the selected question status."""
        question = QuestionAccessService.get_question_or_403(question_id, request.user)
        serializer = QuestionAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = QuestionService.answer_question(question, request.user, serializer.validated_data)
        question.refresh_from_db()
        return api_success(
            message="Question answer stored successfully.",
            data={
                "question": QuestionReadSerializer(question).data,
                "answer": QuestionResponseReadSerializer(response).data,
            },
        )


class QuestionHistoryView(APIView):
    """Handle retrieval of the processing history for a selected question."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        """Return ordered history events when the current user has access."""
        question = QuestionAccessService.get_question_or_403(question_id, request.user)
        history = QuestionService.question_history(question)
        return api_success(
            message="Question history retrieved successfully.",
            data=QuestionHistorySerializer(history, many=True).data,
            meta={"count": history.count()},
        )
