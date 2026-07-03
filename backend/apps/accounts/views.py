"""Implements authenticated API endpoints for user accounts, roles, permissions, and authentication."""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.pagination import PaginationMixin
from apps.core.responses import success
from apps.core.services import AuditEvent, AuditService

from .commands import (
    ChangePasswordCommand,
    LoginCommand,
    LogoutCommand,
    RefreshSessionCommand,
)
from .models import Department, Permission, Role, User, UserRole
from .permissions import HasSystemPermission
from .serializers import (
    ChangePasswordSerializer,
    CurrentUserSerializer,
    DepartmentSerializer,
    LoginSerializer,
    PermissionSerializer,
    RoleAssignmentSerializer,
    RoleSerializer,
    RoleUpdateSerializer,
    TokenSerializer,
    UserCreateSerializer,
    UserListSerializer,
    UserUpdateSerializer,
)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, tokens = LoginCommand(
            **serializer.validated_data, request=request
        ).execute()
        return success(
            {"tokens": tokens, "user": CurrentUserSerializer(user).data},
            "Login successful",
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token"

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = RefreshSessionCommand(serializer.validated_data["refresh"]).execute()
        return success({"tokens": tokens}, "Session refreshed")


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        LogoutCommand(
            serializer.validated_data["refresh"], actor=request.user, request=request
        ).execute()
        return success(message="Logout successful")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password"

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ChangePasswordCommand(
            request.user, request=request, **serializer.validated_data
        ).execute()
        return success(message="Password changed. Please sign in again.")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success(CurrentUserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        # A user cannot self-activate/deactivate through profile editing.
        if "is_active" in request.data:
            raise ValidationError({"is_active": "This field cannot be changed here."})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            AuditEvent("profile.updated", "User", request.user.pk),
            actor=request.user,
            request=request,
        )
        return success(CurrentUserSerializer(request.user).data, "Profile updated")


class UserListCreateView(PaginationMixin, APIView):
    permission_classes = [HasSystemPermission]

    def get_permissions(self):
        self.required_permission = (
            "users.manage" if self.request.method == "POST" else "users.view"
        )
        return super().get_permissions()

    def get(self, request):
        users = User.objects.select_related("department", "profile").prefetch_related(
            "roles", "roles__permissions"
        )
        query = request.query_params.get("search", "").strip()
        role = request.query_params.get("role", "").strip()
        active = request.query_params.get("is_active")
        if query:
            users = users.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(profile__student_number__icontains=query)
                | Q(profile__employee_number__icontains=query)
            )
        if role:
            users = users.filter(roles__name=role)
        if active in {"true", "false"}:
            users = users.filter(is_active=active == "true")
        ordering = request.query_params.get("ordering", "id")
        allowed_ordering = {"id", "username", "email", "date_joined", "-date_joined"}
        users = users.distinct().order_by(
            ordering if ordering in allowed_ordering else "id"
        )
        return self.paginate(request, users, UserListSerializer)

    def post(self, request):
        serializer = UserCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success(
            UserListSerializer(user).data, "User created", status.HTTP_201_CREATED
        )


class UserDetailView(APIView):
    permission_classes = [HasSystemPermission]

    def get_permissions(self):
        self.required_permission = (
            "users.view" if self.request.method == "GET" else "users.manage"
        )
        return super().get_permissions()

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(
            User.objects.select_related("department", "profile").prefetch_related(
                "roles", "roles__permissions"
            ),
            pk=pk,
        )

    def get(self, request, pk):
        return success(UserListSerializer(self.get_object(pk)).data)

    @transaction.atomic
    def patch(self, request, pk):
        user = User.objects.select_for_update().get(pk=self.get_object(pk).pk)
        if user.pk == request.user.pk and request.data.get("is_active") is False:
            raise ValidationError("You cannot deactivate your own account.")
        if (
            not request.data.get("is_active", True)
            and user.has_role(Role.PRESIDENT)
            and User.objects.filter(is_active=True, roles__name=Role.PRESIDENT)
            .distinct()
            .count()
            <= 1
        ):
            raise ValidationError(
                "The final active university president cannot be deactivated."
            )
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            AuditEvent("user.updated", "User", user.pk, {"fields": list(request.data)}),
            actor=request.user,
            request=request,
        )
        return success(UserListSerializer(user).data, "User updated")

    @transaction.atomic
    def delete(self, request, pk):
        user = User.objects.select_for_update().get(pk=self.get_object(pk).pk)
        if user.pk == request.user.pk:
            raise ValidationError("You cannot deactivate your own account.")
        if (
            user.has_role(Role.PRESIDENT)
            and User.objects.filter(is_active=True, roles__name=Role.PRESIDENT)
            .distinct()
            .count()
            <= 1
        ):
            raise ValidationError(
                "The final active university president cannot be deactivated."
            )
        user.is_active = False
        user.deactivated_at = timezone.now()
        user.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        AuditService.record(
            AuditEvent("user.deactivated", "User", user.pk),
            actor=request.user,
            request=request,
        )
        return success(message="User deactivated")


class UserReactivateView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "users.manage"

    @transaction.atomic
    def post(self, request, pk):
        from django.shortcuts import get_object_or_404

        user = get_object_or_404(User.objects.select_for_update(), pk=pk)
        user.is_active = True
        user.deactivated_at = None
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(
            update_fields=[
                "is_active",
                "deactivated_at",
                "failed_login_attempts",
                "locked_until",
                "updated_at",
            ]
        )
        AuditService.record(
            AuditEvent("user.reactivated", "User", user.pk),
            actor=request.user,
            request=request,
        )
        return success(UserListSerializer(user).data, "User reactivated")


class UserRoleView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "users.assign_role"

    @transaction.atomic
    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404

        user = get_object_or_404(User.objects.select_for_update(), pk=pk)
        if user.pk == request.user.pk:
            raise ValidationError("You cannot change your own roles.")
        serializer = RoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roles = list(serializer.validated_data["role_ids"])
        old_role_names = set(user.roles.values_list("name", flat=True))
        new_role_names = {role.name for role in roles}
        if (
            Role.PRESIDENT in old_role_names
            and Role.PRESIDENT not in new_role_names
            and User.objects.filter(is_active=True, roles__name=Role.PRESIDENT)
            .distinct()
            .count()
            <= 1
        ):
            raise ValidationError(
                "The final active university president must retain that role."
            )
        role_ids = [role.id for role in roles]
        UserRole.objects.filter(user=user).exclude(role_id__in=role_ids).delete()
        existing = set(
            UserRole.objects.filter(user=user).values_list("role_id", flat=True)
        )
        UserRole.objects.bulk_create(
            [
                UserRole(user=user, role_id=role_id, assigned_by=request.user)
                for role_id in role_ids
                if role_id not in existing
            ]
        )
        AuditService.record(
            AuditEvent(
                "user.roles_updated",
                "User",
                user.pk,
                {"before": sorted(old_role_names), "after": sorted(new_role_names)},
            ),
            actor=request.user,
            request=request,
        )
        return success(CurrentUserSerializer(user).data, "Roles updated")


class RoleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = Role.objects.prefetch_related("permissions").order_by("id")
        return success(RoleSerializer(roles, many=True).data)


class RoleDetailView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "roles.manage"

    @transaction.atomic
    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404

        role = get_object_or_404(Role.objects.select_for_update(), pk=pk)
        serializer = RoleUpdateSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        AuditService.record(
            AuditEvent("role.updated", "Role", role.pk),
            actor=request.user,
            request=request,
        )
        return success(RoleSerializer(role).data, "Role updated")


class PermissionListView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "users.view"

    def get(self, request):
        return success(
            PermissionSerializer(
                Permission.objects.all().order_by("code"), many=True
            ).data
        )


class DepartmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success(
            DepartmentSerializer(
                Department.objects.filter(is_active=True), many=True
            ).data
        )
