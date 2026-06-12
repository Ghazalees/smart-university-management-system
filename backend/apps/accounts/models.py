from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Department(models.Model):
    """Represent an academic or administrative department."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "departments"

    def __str__(self):
        """Return the department display name."""
        return self.name


class Permission(models.Model):
    """Represent a fine-grained permission used by RBAC."""

    code = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "permissions"

    def __str__(self):
        """Return the permission code."""
        return self.code


class Role(models.Model):
    """Represent a university role with assigned permissions."""

    STUDENT = "Student"
    PROFESSOR = "Professor"
    ADMINISTRATIVE_STAFF = "AdministrativeStaff"
    UNIVERSITY_PRESIDENT = "UniversityPresident"

    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"

    def __str__(self):
        """Return the role name."""
        return self.name


class User(AbstractUser):
    """Store an authenticated user account with lockout fields and role helpers."""

    email = models.EmailField(unique=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"

    def is_locked(self):
        """Return whether the account is currently locked."""
        return bool(self.locked_until and self.locked_until > timezone.now())

    def primary_role(self):
        """Return the first assigned role name for dashboard and access decisions."""
        user_role = self.user_roles.select_related("role").first()
        return user_role.role.name if user_role else None

    def has_role(self, role_names):
        """Check whether the user has one of the requested role names."""
        names = role_names if isinstance(role_names, (list, tuple, set)) else [role_names]
        return self.user_roles.filter(role__name__in=names).exists()

    def has_permission_code(self, permission_codes):
        """Check whether any assigned role contains one of the requested permission codes."""
        codes = permission_codes if isinstance(permission_codes, (list, tuple, set)) else [permission_codes]
        return self.user_roles.filter(role__permissions__code__in=codes).exists()


class UserRole(models.Model):
    """Connect users to roles for RBAC enforcement."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_roles"
        unique_together = ("user", "role")

    def __str__(self):
        """Return a readable user-role assignment label."""
        return f"{self.user.email} -> {self.role.name}"


class Profile(models.Model):
    """Store role-neutral profile information for a system user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40, blank=True)
    student_number = models.CharField(max_length=40, blank=True)
    employee_number = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles"

    def __str__(self):
        """Return the profile display name."""
        return self.full_name


class AuditLog(models.Model):
    """Store compact audit events for sensitive account and RBAC operations."""

    ACTION_USER_CREATED = "USER_CREATED"
    ACTION_USER_UPDATED = "USER_UPDATED"
    ACTION_USER_ROLE_UPDATED = "USER_ROLE_UPDATED"
    ACTION_USER_DISABLED = "USER_DISABLED"

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs_created",
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs_received",
    )
    action = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        """Return a readable audit event label."""
        return f"{self.action} at {self.created_at}"
