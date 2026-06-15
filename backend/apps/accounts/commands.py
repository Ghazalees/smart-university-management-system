from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import User


class Command(ABC):
    @abstractmethod
    def execute(self): ...


@dataclass
class LoginCommand(Command):
    username: str
    password: str

    def execute(self):
        try:
            candidate = User.objects.get(username=self.username)
        except User.DoesNotExist:
            candidate = None
        if candidate and candidate.is_locked():
            raise AuthenticationFailed(
                "Account is temporarily locked.", code="account_locked"
            )
        user = authenticate(username=self.username, password=self.password)
        if user is None:
            if candidate:
                candidate.register_failed_login()
            raise AuthenticationFailed("Invalid credentials.")
        if not user.is_active:
            raise AuthenticationFailed("Account is disabled.")
        user.clear_login_failures()
        refresh = RefreshToken.for_user(user)
        return user, {"access": str(refresh.access_token), "refresh": str(refresh)}


@dataclass
class LogoutCommand(Command):
    refresh_token: str

    def execute(self):
        try:
            RefreshToken(self.refresh_token).blacklist()
        except TokenError as exc:
            raise AuthenticationFailed("Invalid or expired refresh token.") from exc
