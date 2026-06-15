from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    PermissionListView,
    RoleListView,
    UserDetailView,
    UserListCreateView,
    UserRoleView,
)

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("auth/me", MeView.as_view(), name="me"),
    path("users", UserListCreateView.as_view(), name="users"),
    path("users/<int:pk>", UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/role", UserRoleView.as_view(), name="user-role"),
    path("roles", RoleListView.as_view(), name="roles"),
    path("permissions", PermissionListView.as_view(), name="permissions"),
]
