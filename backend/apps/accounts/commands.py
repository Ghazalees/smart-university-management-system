"""Defines explicit command objects for state-changing accounts operations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from apps.core.services import AuditEvent, AuditService

from .models import User

DUMMY_PASSWORD_HASH = make_password("smart-university-dummy-password")
GENERIC_LOGIN_ERROR = "Unable to sign in with the provided credentials."


class Command(ABC):
    @abstractmethod
    def execute(self): ...


@dataclass
class LoginCommand(Command):
    identifier: str
    password: str
    request: object = None

    def execute(self):
        normalized = self.identifier.strip()
        user = None
        tokens = None
        failure = None

        # The row lock makes the read/increment/write sequence safe under concurrent
        # login attempts. Authentication failures are raised only after leaving the
        # atomic block so the failed-attempt counter is not rolled back.
        with transaction.atomic():
            candidate = (
                User.objects.select_for_update()
                .filter(Q(username__iexact=normalized) | Q(email__iexact=normalized))
                .first()
            )
            if candidate is None:
                failure = "missing"
            elif candidate.is_locked() or not candidate.is_active:
                failure = "unavailable"
            else:
                authenticated = authenticate(
                    username=candidate.username, password=self.password
                )
                if authenticated is None:
                    candidate.register_failed_login(save=False)
                    candidate.save(
                        update_fields=[
                            "failed_login_attempts",
                            "locked_until",
                            "updated_at",
                        ]
                    )
                    failure = "invalid"
                else:
                    user = authenticated
                    user.clear_login_failures(save=False)
                    user.last_login = timezone.now()
                    user.save(
                        update_fields=[
                            "failed_login_attempts",
                            "locked_until",
                            "last_login",
                            "updated_at",
                        ]
                    )
                    refresh = RefreshToken.for_user(user)
                    tokens = {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    }

        if failure:
            if failure == "missing":
                # Equalize the expensive password-hash operation to reduce account
                # enumeration through timing differences.
                check_password(self.password, DUMMY_PASSWORD_HASH)
            raise AuthenticationFailed(GENERIC_LOGIN_ERROR)

        AuditService.record(
            AuditEvent("auth.login", "User", user.pk), actor=user, request=self.request
        )
        return user, tokens


@dataclass
class RefreshSessionCommand(Command):
    refresh_token: str

    @transaction.atomic
    def execute(self):
        try:
            old_refresh = RefreshToken(self.refresh_token)
            user = User.objects.get(pk=old_refresh["user_id"], is_active=True)
            old_refresh.blacklist()
            new_refresh = RefreshToken.for_user(user)
            return {
                "access": str(new_refresh.access_token),
                "refresh": str(new_refresh),
            }
        except (TokenError, User.DoesNotExist, KeyError) as exc:
            raise AuthenticationFailed("Invalid or expired refresh token.") from exc


@dataclass
class LogoutCommand(Command):
    refresh_token: str
    actor: object = None
    request: object = None

    def execute(self):
        try:
            RefreshToken(self.refresh_token).blacklist()
        except TokenError as exc:
            raise AuthenticationFailed("Invalid or expired refresh token.") from exc
        AuditService.record(
            AuditEvent("auth.logout", "User", getattr(self.actor, "pk", "")),
            actor=self.actor,
            request=self.request,
        )


@dataclass
class ChangePasswordCommand(Command):
    user: User
    current_password: str
    new_password: str
    request: object = None

    @transaction.atomic
    def execute(self):
        locked_user = User.objects.select_for_update().get(pk=self.user.pk)
        if not locked_user.check_password(self.current_password):
            raise ValidationError(
                {"current_password": "Current password is incorrect."}
            )
        if self.current_password == self.new_password:
            raise ValidationError(
                {"new_password": "The new password must be different."}
            )
        locked_user.set_password(self.new_password)
        locked_user.save(update_fields=["password", "updated_at"])
        for token in OutstandingToken.objects.filter(user=locked_user):
            BlacklistedToken.objects.get_or_create(token=token)
        AuditService.record(
            AuditEvent("auth.password_changed", "User", locked_user.pk),
            actor=locked_user,
            request=self.request,
        )
        return locked_user
