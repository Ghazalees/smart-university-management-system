import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone
from apps.accounts.models import Role


class AuthFacade:
    """Provide one simplified interface for login, account lock handling, token generation, and auth response creation."""

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
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "role": role,
            },
        }

    @classmethod
    def logout(cls):
        """Return a stateless logout response for token-based authentication."""
        return {"success": True, "message": "Logout completed successfully."}

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
        """Generate a signed JWT token containing the authenticated user's identity and primary role."""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": role or Role.STUDENT,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=8)).timestamp()),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
