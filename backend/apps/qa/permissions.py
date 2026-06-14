from rest_framework.permissions import BasePermission

from apps.accounts.models import Role


class CanAnswerQuestions(BasePermission):
    """Allow question answering to professors, administrative staff, and the university president."""

    message = "Only professors, administrative staff, or the university president can answer questions."
    allowed_roles = {Role.PROFESSOR, Role.ADMINISTRATIVE_STAFF, Role.UNIVERSITY_PRESIDENT}

    def has_permission(self, request, view):
        """Return whether the authenticated user can answer questions."""
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.has_role(self.allowed_roles))


class CanSubmitQuestions(BasePermission):
    """Allow question submission to authenticated core university roles."""

    message = "The authenticated user cannot submit questions."
    allowed_roles = {Role.STUDENT, Role.PROFESSOR, Role.ADMINISTRATIVE_STAFF, Role.UNIVERSITY_PRESIDENT}

    def has_permission(self, request, view):
        """Return whether the authenticated user can submit questions."""
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.has_role(self.allowed_roles))
