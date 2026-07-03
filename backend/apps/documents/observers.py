"""Coordinates side effects emitted by documents domain changes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


@dataclass(frozen=True)
class DocumentEvent:
    document: object
    event: str
    actor: object


class DocumentObserver(ABC):
    @abstractmethod
    def update(self, event): ...


class AIIndexObserver(DocumentObserver):
    def update(self, event):
        if (
            event.event in {"created", "updated", "published"}
            and event.document.knowledge_enabled
        ):
            event.document.mark_indexed()


class DocumentNotificationObserver(DocumentObserver):
    def update(self, event):
        if event.event != "published":
            return
        document = event.document
        recipients = User.objects.filter(is_active=True)
        if document.access_level == document.AccessLevel.ROLE:
            recipients = recipients.filter(
                roles__in=document.allowed_roles.all()
            ).distinct()
        elif document.access_level == document.AccessLevel.PRIVATE:
            recipients = recipients.filter(pk=document.created_by_id)
        for recipient in recipients:
            NotificationService.send(
                recipient=recipient,
                title="New university document",
                message=f"{document.title} has been published.",
                category=Notification.Category.DOCUMENT,
                link=f"/documents/{document.pk}",
                actor=event.actor,
            )


class DocumentEventPublisher:
    _observers = (AIIndexObserver(), DocumentNotificationObserver())

    @classmethod
    def publish(cls, event):
        for observer in cls._observers:
            observer.update(event)
