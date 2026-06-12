from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.models import AuditLog, Permission, Role
from apps.accounts.permissions import (
    BearerTokenAuthentication,
    HasUserManagementPermission,
    HasUserReadPermission,
    IsAdministrativeStaffOrPresident,
)
from apps.accounts.serializers import (
    AuditLogSerializer,
    LoginSerializer,
    PermissionSerializer,
    RoleSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserRoleUpdateSerializer,
    UserUpdateSerializer,
)
from apps.accounts.services import AuthFacade, RoleDashboardStrategy, UserManagementService
from apps.core.responses import api_success


class LoginView(APIView):
    """Handle POST /api/v1/auth/login using AuthFacade."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """Validate credentials and return a signed token when authentication succeeds."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AuthFacade.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not result["success"]:
            from apps.core.responses import api_error

            return api_error(
                message=result["message"],
                errors={"detail": result["message"]},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return api_success(message="Login successful.", data=result["data"])


class LogoutView(APIView):
    """Handle POST /api/v1/auth/logout for the token-based authentication flow."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """Return a successful logout response for the current API client."""
        result = AuthFacade.logout()
        return api_success(message=result["message"])


class CurrentUserView(APIView):
    """Handle GET /api/v1/auth/me for authenticated users."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the current user data and role-based dashboard selected by Strategy Pattern."""
        return api_success(
            message="Current user retrieved successfully.",
            data={
                "user": AuthFacade.user_payload(request.user),
                "role": request.user.primary_role(),
                "dashboard": RoleDashboardStrategy.build_dashboard(request.user),
            },
        )


class UserListCreateView(APIView):
    """Handle collection-level user management APIs."""

    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        """Select read or management permission based on the request method."""
        if self.request.method == "GET":
            return [IsAuthenticated(), HasUserReadPermission()]
        return [IsAuthenticated(), HasUserManagementPermission()]

    def get(self, request):
        """Return users visible to authorized staff or management users."""
        users = UserManagementService.list_users()
        serializer = UserReadSerializer(users, many=True)
        return api_success(
            message="Users retrieved successfully.",
            data=serializer.data,
            meta={"count": users.count()},
        )

    def post(self, request):
        """Create a new user account for an authorized account manager."""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserManagementService.create_user(dict(serializer.validated_data), actor=request.user)
        return api_success(
            message="User created successfully.",
            data=UserReadSerializer(user).data,
            status_code=status.HTTP_201_CREATED,
        )


class UserDetailView(APIView):
    """Handle item-level user read, update, and disable APIs."""

    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        """Select read or management permission based on the request method."""
        if self.request.method == "GET":
            return [IsAuthenticated(), HasUserReadPermission()]
        return [IsAuthenticated(), HasUserManagementPermission()]

    def get(self, request, user_id):
        """Return details for one selected user."""
        user = get_object_or_404(UserManagementService.base_queryset(), id=user_id)
        return api_success(
            message="User retrieved successfully.",
            data=UserReadSerializer(user).data,
        )

    def patch(self, request, user_id):
        """Partially update one selected user and profile."""
        user = get_object_or_404(UserManagementService.base_queryset(), id=user_id)
        serializer = UserUpdateSerializer(data=request.data, partial=True, context={"user": user})
        serializer.is_valid(raise_exception=True)
        updated = UserManagementService.update_user(user, dict(serializer.validated_data), actor=request.user)
        return api_success(
            message="User updated successfully.",
            data=UserReadSerializer(updated).data,
        )

    def delete(self, request, user_id):
        """Disable one selected user account without deleting database history."""
        user = get_object_or_404(UserManagementService.base_queryset(), id=user_id)
        disabled = UserManagementService.disable_user(user, actor=request.user)
        return api_success(
            message="User disabled successfully.",
            data=UserReadSerializer(disabled).data,
        )


class UserRoleUpdateView(APIView):
    """Handle role assignment updates for a selected user."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated, HasUserManagementPermission]

    def patch(self, request, user_id):
        """Replace the selected user's role with the requested role."""
        user = get_object_or_404(UserManagementService.base_queryset(), id=user_id)
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = UserManagementService.update_user_role(
            user=user,
            role_name=serializer.validated_data["role"],
            actor=request.user,
        )
        return api_success(
            message="User role updated successfully.",
            data=UserReadSerializer(updated).data,
        )


class RoleListView(APIView):
    """Handle role list retrieval for authorized RBAC users."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdministrativeStaffOrPresident]

    def get(self, request):
        """Return all roles and their assigned permission codes."""
        roles = Role.objects.prefetch_related("permissions").order_by("id")
        return api_success(
            message="Roles retrieved successfully.",
            data=RoleSerializer(roles, many=True).data,
            meta={"count": roles.count()},
        )


class PermissionListView(APIView):
    """Handle permission list retrieval for authorized RBAC users."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdministrativeStaffOrPresident]

    def get(self, request):
        """Return all permission records used by RBAC."""
        permissions = Permission.objects.order_by("code")
        return api_success(
            message="Permissions retrieved successfully.",
            data=PermissionSerializer(permissions, many=True).data,
            meta={"count": permissions.count()},
        )


class AuditLogListView(APIView):
    """Handle audit log retrieval for authorized management users."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdministrativeStaffOrPresident]

    def get(self, request):
        """Return recent audit events for sensitive account operations."""
        logs = AuditLog.objects.select_related("actor", "target_user").order_by("-created_at")[:100]
        return api_success(
            message="Audit logs retrieved successfully.",
            data=AuditLogSerializer(logs, many=True).data,
        )
