from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from apps.core.responses import success
from apps.core.services import AuditEvent, AuditService
from .commands import LoginCommand, LogoutCommand
from .models import Permission, Role, User, UserRole
from .permissions import HasSystemPermission
from .serializers import (
    CurrentUserSerializer, LoginSerializer, LogoutSerializer, PermissionSerializer,
    RoleAssignmentSerializer, RoleSerializer, UserCreateSerializer, UserListSerializer,
    UserUpdateSerializer,
)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, tokens = LoginCommand(**serializer.validated_data).execute()
        return success({"tokens": tokens, "user": CurrentUserSerializer(user).data}, "Login successful")

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        LogoutCommand(serializer.validated_data["refresh"]).execute()
        return success(message="Logout successful")

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return success(CurrentUserSerializer(request.user).data)

class UserListCreateView(APIView):
    permission_classes = [HasSystemPermission]
    def get_permissions(self):
        self.required_permission = "users.manage" if self.request.method == "POST" else "users.view"
        return super().get_permissions()

    def get(self, request):
        users = User.objects.select_related("department", "profile").prefetch_related("roles").order_by("id")
        return success(UserListSerializer(users, many=True).data)

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success(UserListSerializer(user).data, "User created", status.HTTP_201_CREATED)

class UserDetailView(APIView):
    permission_classes = [HasSystemPermission]
    def get_permissions(self):
        self.required_permission = "users.view" if self.request.method == "GET" else "users.manage"
        return super().get_permissions()

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(User.objects.select_related("department", "profile").prefetch_related("roles"), pk=pk)

    def get(self, request, pk): return success(UserListSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        user = self.get_object(pk)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(AuditEvent("user.updated", "User", user.pk, {"fields": list(request.data)}), actor=request.user, request=request)
        return success(UserListSerializer(user).data, "User updated")

    def delete(self, request, pk):
        user = self.get_object(pk)
        if user.pk == request.user.pk:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You cannot deactivate your own account.")
        user.is_active = False
        user.deactivated_at = timezone.now()
        user.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        AuditService.record(AuditEvent("user.deactivated", "User", user.pk), actor=request.user, request=request)
        return success(message="User deactivated")

class UserRoleView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "users.assign_role"

    @transaction.atomic
    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404
        user = get_object_or_404(User, pk=pk)
        serializer = RoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role_ids = [role.id for role in serializer.validated_data["role_ids"]]
        UserRole.objects.filter(user=user).exclude(role_id__in=role_ids).delete()
        existing = set(UserRole.objects.filter(user=user).values_list("role_id", flat=True))
        UserRole.objects.bulk_create([UserRole(user=user, role_id=rid, assigned_by=request.user) for rid in role_ids if rid not in existing])
        AuditService.record(AuditEvent("user.roles_updated", "User", user.pk, {"role_ids": role_ids}), actor=request.user, request=request)
        return success(CurrentUserSerializer(user).data, "Roles updated")

class RoleListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return success(RoleSerializer(Role.objects.prefetch_related("permissions"), many=True).data)

class PermissionListView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "users.view"
    def get(self, request): return success(PermissionSerializer(Permission.objects.all(), many=True).data)
