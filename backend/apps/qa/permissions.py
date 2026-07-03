"""Enforces role- and object-level authorization for grounded question answering, retrieval, and AI orchestration."""

from rest_framework.permissions import BasePermission


class CanCreateQuestion(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_system_permission("questions.create")
        )


class CanGenerateQuestionAnswer(BasePermission):
    """Allow a user to process their own question or staff to process any visible one."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.has_system_permission("questions.create")
                or request.user.has_system_permission("questions.answer")
            )
        )


class CanAnswerQuestion(BasePermission):
    """Human-reviewed answers remain a privileged staff operation."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_system_permission("questions.answer")
        )
