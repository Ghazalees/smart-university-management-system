"""Coordinates side effects emitted by workflows domain changes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from apps.core.services import AuditEvent, AuditService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService

from .models import WorkflowHistory, WorkflowRequest


@dataclass(frozen=True)
class WorkflowEvent:
    request: WorkflowRequest
    event: str
    actor: object
    from_status: str = ""
    to_status: str = ""
    note: str = ""
    metadata: dict = field(default_factory=dict)
    http_request: object = None


class WorkflowObserver(ABC):
    @abstractmethod
    def update(self, event): ...


class WorkflowHistoryObserver(WorkflowObserver):
    def update(self, event):
        WorkflowHistory.objects.create(
            request=event.request,
            event=event.event,
            actor=event.actor
            if getattr(event.actor, "is_authenticated", False)
            else None,
            from_status=event.from_status,
            to_status=event.to_status,
            note=event.note,
            metadata=event.metadata,
        )


class WorkflowNotificationObserver(WorkflowObserver):
    def update(self, event):
        request = event.request
        recipient = request.requester
        if event.event == "created":
            return
        NotificationService.send(
            recipient=recipient,
            title=f"Request {request.request_number} updated",
            message=f"Your request is now {request.get_status_display()}.",
            category=Notification.Category.WORKFLOW,
            link=f"/workflows/{request.pk}",
            metadata={"request_id": request.pk, "status": request.status},
            actor=event.actor,
        )


class WorkflowAuditObserver(WorkflowObserver):
    def update(self, event):
        AuditService.record(
            AuditEvent(
                f"workflow.{event.event}",
                "WorkflowRequest",
                event.request.pk,
                {
                    "from": event.from_status,
                    "to": event.to_status,
                    **event.metadata,
                },
            ),
            actor=event.actor,
            request=event.http_request,
        )


class WorkflowEventPublisher:
    _observers = (
        WorkflowHistoryObserver(),
        WorkflowNotificationObserver(),
        WorkflowAuditObserver(),
    )

    @classmethod
    def publish(cls, event):
        for observer in cls._observers:
            observer.update(event)
