from rest_framework.permissions import BasePermission

from .models import Role


class HasSystemPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        permission = getattr(view, "required_permission", self.required_permission)
        return bool(
            request.user
            and request.user.is_authenticated
            and permission
            and request.user.has_system_permission(permission)
        )


class IsManagement(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_role(Role.ADMIN_STAFF, Role.PRESIDENT)
        )
