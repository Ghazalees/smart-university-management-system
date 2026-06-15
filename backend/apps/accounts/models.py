from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel

class Department(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Permission(TimeStampedModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    def __str__(self): return self.code

class Role(TimeStampedModel):
    STUDENT = "Student"
    PROFESSOR = "Professor"
    ADMIN_STAFF = "AdministrativeStaff"
    PRESIDENT = "UniversityPresident"
    SYSTEM_ROLES = (STUDENT, PROFESSOR, ADMIN_STAFF, PRESIDENT)

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    is_system = models.BooleanField(default=False)
    def __str__(self): return self.name

class User(AbstractUser, TimeStampedModel):
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    roles = models.ManyToManyField(Role, through="UserRole", through_fields=("user", "role"), related_name="users")
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    @property
    def role_names(self):
        return list(self.roles.values_list("name", flat=True))

    def has_role(self, *role_names):
        return self.is_superuser or self.roles.filter(name__in=role_names).exists()

    def has_system_permission(self, permission_code):
        return self.is_superuser or self.roles.filter(permissions__code=permission_code).exists()

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
            self.locked_until = timezone.now() + timedelta(minutes=settings.ACCOUNT_LOCK_MINUTES)
        self.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

    def clear_login_failures(self):
        if self.failed_login_attempts or self.locked_until:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

class UserRole(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="role_assignments")
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "role"], name="unique_user_role")]

class Profile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=30, blank=True)
    student_number = models.CharField(max_length=50, blank=True, db_index=True)
    employee_number = models.CharField(max_length=50, blank=True, db_index=True)
    bio = models.TextField(blank=True)
