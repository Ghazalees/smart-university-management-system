from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from apps.accounts.models import Role
from apps.qa.models import Question, QuestionHistory, QuestionResponse


class QuestionAccessService:
    """Centralize authorization rules for question visibility and answering."""

    elevated_roles = {Role.PROFESSOR, Role.ADMINISTRATIVE_STAFF, Role.UNIVERSITY_PRESIDENT}

    @classmethod
    def can_view(cls, user, question):
        """Return whether the user can view the selected question."""
        if question.submitted_by_id == user.id:
            return True
        return user.has_role(cls.elevated_roles)

    @classmethod
    def can_answer(cls, user):
        """Return whether the user can answer or escalate questions."""
        return user.has_role(cls.elevated_roles)

    @classmethod
    def get_question_or_403(cls, question_id, user):
        """Load a question and raise PermissionDenied when the user cannot view it."""
        question = get_object_or_404(
            Question.objects.select_related("submitted_by").prefetch_related("responses", "history"),
            id=question_id,
        )
        if not cls.can_view(user, question):
            raise PermissionDenied("You are not allowed to access this question.")
        return question


class QuestionService:
    """Coordinate question submission, retrieval, answer creation, and history storage."""

    @staticmethod
    def submit_question(user, data):
        """Create a pending question and store the first history event."""
        question = Question.objects.create(
            submitted_by=user,
            title=data["title"],
            body=data["body"],
            category=data.get("category", ""),
            status=Question.STATUS_PENDING,
        )
        QuestionHistory.objects.create(
            question=question,
            actor=user,
            event=QuestionHistory.EVENT_SUBMITTED,
            status_from="",
            status_to=Question.STATUS_PENDING,
            note="Question submitted.",
        )
        return question

    @staticmethod
    def list_my_questions(user):
        """Return questions submitted by the current authenticated user."""
        return Question.objects.filter(submitted_by=user).select_related("submitted_by").prefetch_related("responses")

    @staticmethod
    def answer_question(question, actor, data):
        """Create a question response, update status, and append a history event."""
        if not QuestionAccessService.can_answer(actor):
            raise PermissionDenied("You are not allowed to answer questions.")

        previous_status = question.status
        response = QuestionResponse.objects.create(
            question=question,
            responder=actor,
            body=data["body"],
            confidence=data.get("confidence"),
            source_documents=data.get("source_documents", []),
        )
        question.status = data.get("status", Question.STATUS_ANSWERED)
        question.save(update_fields=["status", "updated_at"])
        QuestionHistory.objects.create(
            question=question,
            actor=actor,
            event=QuestionHistory.EVENT_ANSWERED,
            status_from=previous_status,
            status_to=question.status,
            note=data.get("note", "Question response stored."),
        )
        return response

    @staticmethod
    def question_history(question):
        """Return the ordered history timeline for a question."""
        return question.history.select_related("actor").order_by("created_at")
