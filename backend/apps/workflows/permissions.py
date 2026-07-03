"""Enforces role- and object-level authorization for university requests, assignments, statuses, and revisions."""

from rest_framework.permissions import BasePermission


class CanAccessWorkflowRequest(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_superuser
            or obj.requester_id == request.user.id
            or obj.assigned_to_id == request.user.id
            or request.user.has_system_permission("workflows.view_all")
        )
