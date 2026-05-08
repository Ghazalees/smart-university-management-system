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
