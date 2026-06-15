from rest_framework.permissions import BasePermission

class CanCreateQuestion(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.has_system_permission("questions.create"))

class CanAnswerQuestion(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.has_system_permission("questions.answer"))
