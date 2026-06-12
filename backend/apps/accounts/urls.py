from django.urls import path
from apps.accounts.views import (
    AuditLogListView,
    CurrentUserView,
    LoginView,
    LogoutView,
    PermissionListView,
    RoleListView,
    UserDetailView,
    UserListCreateView,
    UserRoleUpdateView,
)

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/me", CurrentUserView.as_view(), name="auth-me"),
    path("users", UserListCreateView.as_view(), name="users-list-create"),
    path("users/<int:user_id>", UserDetailView.as_view(), name="users-detail"),
    path("users/<int:user_id>/role", UserRoleUpdateView.as_view(), name="users-role-update"),
    path("roles", RoleListView.as_view(), name="roles-list"),
    path("permissions", PermissionListView.as_view(), name="permissions-list"),
    path("audit-logs", AuditLogListView.as_view(), name="audit-logs-list"),
]
