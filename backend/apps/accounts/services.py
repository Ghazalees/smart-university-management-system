from django.db import transaction

from apps.core.services import AuditEvent, AuditService

from .models import Profile, Role, User, UserRole


class UserFactory:
    """Factory Method for role-aware account creation."""

    @classmethod
    @transaction.atomic
    def create(cls, *, actor, request=None, role_names=None, profile=None, **user_data):
        password = user_data.pop("password")
        user = User(**user_data)
        user.set_password(password)
        user.save()
        Profile.objects.create(user=user, **(profile or {}))
        for role in Role.objects.filter(name__in=role_names or []):
            UserRole.objects.create(user=user, role=role, assigned_by=actor)
        AuditService.record(
            AuditEvent("user.created", "User", user.pk, {"roles": role_names or []}),
            actor=actor,
            request=request,
        )
        return user
