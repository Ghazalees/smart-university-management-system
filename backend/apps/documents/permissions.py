from rest_framework.permissions import BasePermission

from apps.accounts.models import Role


class CanManageDocuments(BasePermission):
    """
    Allow document write/archive operations only for administrative staff
    and the university president.
    """

    message = "Only administrative staff or the university president can manage documents."

    manager_roles = {
        Role.ADMINISTRATIVE_STAFF,
        Role.UNIVERSITY_PRESIDENT,
    }

    def has_permission(self, request, view):
        user = getattr(request, "user", None)

        if not user or not getattr(user, "is_authenticated", False):
            return False

        if hasattr(user, "has_role"):
            return user.has_role(self.manager_roles)

        return False
