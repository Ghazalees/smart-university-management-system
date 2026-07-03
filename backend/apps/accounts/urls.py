"""Declares API routes for user accounts, roles, permissions, and authentication."""

from django.urls import path

from .views import (
    ChangePasswordView,
    DepartmentListView,
    LoginView,
    LogoutView,
    MeView,
    PermissionListView,
    RefreshView,
    RoleDetailView,
    RoleListView,
    UserDetailView,
    UserListCreateView,
    UserReactivateView,
    UserRoleView,
)

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/refresh", RefreshView.as_view(), name="refresh"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("auth/change-password", ChangePasswordView.as_view(), name="change-password"),
    path("auth/me", MeView.as_view(), name="me"),
    path("users", UserListCreateView.as_view(), name="users"),
    path("users/<int:pk>", UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/roles", UserRoleView.as_view(), name="user-role"),
    path(
        "users/<int:pk>/reactivate",
        UserReactivateView.as_view(),
        name="user-reactivate",
    ),
    path("roles", RoleListView.as_view(), name="roles"),
    path("roles/<int:pk>", RoleDetailView.as_view(), name="role-detail"),
    path("permissions", PermissionListView.as_view(), name="permissions"),
    path("departments", DepartmentListView.as_view(), name="departments"),
]
