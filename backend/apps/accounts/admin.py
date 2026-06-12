from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import AuditLog, Department, Permission, Profile, Role, User, UserRole


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Display the custom user model in Django admin."""

    list_display = ("id", "email", "username", "is_active", "is_staff", "created_at")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("id",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Display system roles and their permissions."""

    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    filter_horizontal = ("permissions",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Display fine-grained RBAC permissions."""

    list_display = ("id", "code", "name")
    search_fields = ("code", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Display user-to-role assignments."""

    list_display = ("id", "user", "role", "assigned_at")
    list_filter = ("role",)
    search_fields = ("user__email", "role__name")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Display user profile data."""

    list_display = ("id", "full_name", "user", "department", "student_number", "employee_number")
    search_fields = ("full_name", "user__email", "student_number", "employee_number")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Display university departments."""

    list_display = ("id", "name", "code", "is_active", "created_at")
    search_fields = ("name", "code")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Display audit events for sensitive account operations."""

    list_display = ("id", "action", "actor", "target_user", "created_at")
    list_filter = ("action",)
    search_fields = ("action", "actor__email", "target_user__email")
    readonly_fields = ("actor", "target_user", "action", "metadata", "created_at")
