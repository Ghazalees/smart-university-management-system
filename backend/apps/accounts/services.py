from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone
from apps.accounts.models import Role


class AuthFacade:
    """Provide one simplified interface for login, logout, token generation, token decoding, and authentication response creation."""

    @classmethod
    def login(cls, email, password):
        """Authenticate a user and return a token-based response payload."""
        user = cls._get_user_by_email(email)
        if user is None:
            return cls._failed_response("Invalid email or password.")
        if not user.is_active:
            return cls._failed_response("This account is inactive.")
        if user.is_locked():
            return cls._failed_response("This account is temporarily locked.")
        if not user.check_password(password):
            cls._register_failed_attempt(user)
            return cls._failed_response("Invalid email or password.")
        cls._reset_failed_attempts(user)
        role = user.primary_role()
        token = cls._generate_token(user, role)
        return {
            "success": True,
            "data": {
                "token": token,
                "token_type": "Bearer",
                "user": cls.user_payload(user),
                "role": role,
            },
        }

    @classmethod
    def logout(cls):
        """Return a stateless logout response for token-based authentication."""
        return {"success": True, "message": "Logout completed successfully."}

    @classmethod
    def decode_token(cls, token):
        """Decode a JWT token and return its payload."""
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

    @classmethod
    def user_payload(cls, user):
        """Build a safe user payload for API responses."""
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    @staticmethod
    def _get_user_by_email(email):
        """Load a user by email and include role data for authentication response generation."""
        User = get_user_model()
        try:
            return User.objects.prefetch_related("user_roles__role").get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def _failed_response(message):
        """Create a consistent authentication failure response."""
        return {"success": False, "message": message}

    @staticmethod
    def _register_failed_attempt(user):
        """Increase failed login attempts and temporarily lock the account when the configured limit is reached."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
            user.locked_until = django_timezone.now() + timedelta(minutes=settings.ACCOUNT_LOCK_MINUTES)
        user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

    @staticmethod
    def _reset_failed_attempts(user):
        """Clear failed login counters after a successful login."""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

    @staticmethod
    def _generate_token(user, role):
        """Create a signed JWT token for the authenticated user."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=8)).timestamp()),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


class StudentDashboardStrategy:
    """Build dashboard behavior for users with the Student role."""

    def build(self, user):
        """Return student dashboard features and basic identity data."""
        return {
            "role": Role.STUDENT,
            "title": "Student Dashboard",
            "features": [
                "Ask educational questions",
                "Track administrative requests",
                "View notifications",
            ],
        }


class ProfessorDashboardStrategy:
    """Build dashboard behavior for users with the Professor role."""

    def build(self, user):
        """Return professor dashboard features and basic identity data."""
        return {
            "role": Role.PROFESSOR,
            "title": "Professor Dashboard",
            "features": [
                "Answer student questions",
                "Manage classes",
                "View academic notifications",
            ],
        }


class AdministrativeStaffDashboardStrategy:
    """Build dashboard behavior for users with the AdministrativeStaff role."""

    def build(self, user):
        """Return administrative staff dashboard features and basic identity data."""
        return {
            "role": Role.ADMINISTRATIVE_STAFF,
            "title": "Administrative Staff Dashboard",
            "features": [
                "Review workflow requests",
                "Manage users",
                "Publish announcements",
            ],
        }


class UniversityPresidentDashboardStrategy:
    """Build dashboard behavior for users with the UniversityPresident role."""

    def build(self, user):
        """Return president dashboard features and basic identity data."""
        return {
            "role": Role.UNIVERSITY_PRESIDENT,
            "title": "University President Dashboard",
            "features": [
                "View management reports",
                "Manage internal policies",
                "Monitor system activity",
            ],
        }


class RoleDashboardStrategy:
    """Select dashboard behavior based on the authenticated user's role."""

    strategies = {
        Role.STUDENT: StudentDashboardStrategy(),
        Role.PROFESSOR: ProfessorDashboardStrategy(),
        Role.ADMINISTRATIVE_STAFF: AdministrativeStaffDashboardStrategy(),
        Role.UNIVERSITY_PRESIDENT: UniversityPresidentDashboardStrategy(),
    }

    @classmethod
    def build_dashboard(cls, user):
        """Return the dashboard response selected for the user's primary role."""
        role = user.primary_role()
        strategy = cls.strategies.get(role, StudentDashboardStrategy())
        dashboard = strategy.build(user)
        dashboard["user"] = AuthFacade.user_payload(user)
        return dashboard


class AuditLogService:
    """Centralize audit log creation for account and RBAC operations."""

    @staticmethod
    def log(actor, action, target_user=None, metadata=None):
        """Create one audit event for a sensitive account operation."""
        from apps.accounts.models import AuditLog

        return AuditLog.objects.create(
            actor=actor,
            target_user=target_user,
            action=action,
            metadata=metadata or {},
        )


class UserManagementService:
    """Coordinate user CRUD, profile updates, role assignment, and audit logging."""

    @staticmethod
    def base_queryset():
        """Return the optimized user queryset used by user management APIs."""
        User = get_user_model()
        return User.objects.prefetch_related("user_roles__role", "user_roles__role__permissions").select_related("profile")

    @classmethod
    def list_users(cls):
        """Return all users ordered by creation time."""
        return cls.base_queryset().order_by("id")

    @classmethod
    def get_user(cls, user_id):
        """Return one user by id or raise the model DoesNotExist exception."""
        return cls.base_queryset().get(id=user_id)

    @classmethod
    def create_user(cls, data, actor):
        """Create a user, assign a role, create a profile, and store an audit event."""
        from apps.accounts.models import AuditLog, Profile, Role, UserRole

        User = get_user_model()
        profile_data = data.pop("profile", {})
        role_name = data.pop("role")
        password = data.pop("password")
        username = data.pop("username", "") or data["email"].split("@")[0]
        user = User(username=username, **data)
        user.set_password(password)
        user.save()

        role = Role.objects.get(name=role_name)
        UserRole.objects.create(user=user, role=role)
        Profile.objects.create(
            user=user,
            full_name=profile_data.get("full_name") or f"{user.first_name} {user.last_name}".strip() or user.email,
            phone=profile_data.get("phone", ""),
            student_number=profile_data.get("student_number", ""),
            employee_number=profile_data.get("employee_number", ""),
            department=profile_data.get("department"),
        )
        AuditLogService.log(
            actor=actor,
            action=AuditLog.ACTION_USER_CREATED,
            target_user=user,
            metadata={"role": role.name, "email": user.email},
        )
        return user

    @classmethod
    def update_user(cls, user, data, actor):
        """Update editable user and profile fields and store an audit event."""
        from apps.accounts.models import AuditLog, Profile

        profile_data = data.pop("profile", None)
        changed_fields = []
        for field in ["email", "username", "first_name", "last_name", "is_active"]:
            if field in data:
                setattr(user, field, data[field])
                changed_fields.append(field)
        if changed_fields:
            user.save(update_fields=changed_fields + ["updated_at"])

        if profile_data is not None:
            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={"full_name": user.email},
            )
            profile_changed_fields = []
            for field in ["full_name", "phone", "student_number", "employee_number", "department"]:
                if field in profile_data:
                    setattr(profile, field, profile_data[field])
                    profile_changed_fields.append(field)
            if profile_changed_fields:
                profile.save(update_fields=profile_changed_fields + ["updated_at"])

        AuditLogService.log(
            actor=actor,
            action=AuditLog.ACTION_USER_UPDATED,
            target_user=user,
            metadata={"changed_fields": changed_fields, "profile_updated": profile_data is not None},
        )
        return cls.get_user(user.id)

    @classmethod
    def update_user_role(cls, user, role_name, actor):
        """Replace the user's current role assignment and store an audit event."""
        from apps.accounts.models import AuditLog, Role, UserRole

        old_role = user.primary_role()
        role = Role.objects.get(name=role_name)
        UserRole.objects.filter(user=user).delete()
        UserRole.objects.create(user=user, role=role)
        AuditLogService.log(
            actor=actor,
            action=AuditLog.ACTION_USER_ROLE_UPDATED,
            target_user=user,
            metadata={"old_role": old_role, "new_role": role.name},
        )
        return cls.get_user(user.id)

    @classmethod
    def disable_user(cls, user, actor):
        """Disable a user account and store an audit event."""
        from apps.accounts.models import AuditLog

        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        AuditLogService.log(
            actor=actor,
            action=AuditLog.ACTION_USER_DISABLED,
            target_user=user,
            metadata={"email": user.email},
        )
        return user
