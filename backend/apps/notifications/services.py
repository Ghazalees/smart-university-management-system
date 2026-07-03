"""Contains reusable business logic for notification delivery and notification-center state."""

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.core.services import AuditEvent, AuditService

from .models import Notification


class NotificationService:
    @staticmethod
    def send(
        *, recipient, title, message, category, link="", metadata=None, actor=None
    ):
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            category=category,
            link=link,
            metadata=metadata or {},
            created_by=actor if getattr(actor, "is_authenticated", False) else None,
        )

    @classmethod
    @transaction.atomic
    def broadcast(
        cls,
        *,
        title,
        message,
        category,
        recipients=None,
        roles=None,
        link="",
        actor=None,
        request=None,
        metadata=None,
        priority="normal",
    ):
        user_ids = {user.pk for user in recipients or []}
        if roles:
            user_ids.update(
                User.objects.filter(is_active=True, roles__in=roles)
                .values_list("id", flat=True)
                .distinct()
            )
        notifications = Notification.objects.bulk_create(
            [
                Notification(
                    recipient_id=user_id,
                    title=title,
                    message=message,
                    category=category,
                    link=link,
                    created_by=actor
                    if getattr(actor, "is_authenticated", False)
                    else None,
                    metadata=metadata or {},
                    priority=priority,
                )
                for user_id in user_ids
            ]
        )
        AuditService.record(
            AuditEvent(
                "notification.broadcast",
                "Notification",
                metadata={"recipient_count": len(user_ids), "category": category},
            ),
            actor=actor,
            request=request,
        )
        return notifications

    @staticmethod
    def mark_read(notification):
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at", "updated_at"])
        return notification
