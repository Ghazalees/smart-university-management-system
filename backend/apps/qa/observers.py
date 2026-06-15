from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from apps.core.services import AuditEvent, AuditService
from .models import QuestionHistory

@dataclass(frozen=True)
class QuestionEvent:
    question: object
    event: str
    actor: object = None
    from_status: str = ""
    to_status: str = ""
    metadata: dict = field(default_factory=dict)

class QuestionObserver(ABC):
    @abstractmethod
    def update(self, event: QuestionEvent): ...

class QuestionHistoryObserver(QuestionObserver):
    def update(self, event):
        QuestionHistory.objects.create(
            question=event.question,
            event=event.event,
            actor=event.actor if getattr(event.actor, "is_authenticated", False) else None,
            from_status=event.from_status,
            to_status=event.to_status,
            metadata=event.metadata,
        )

class QuestionAuditObserver(QuestionObserver):
    def update(self, event):
        AuditService.record(AuditEvent(
            action=f"question.{event.event}", entity_type="Question",
            entity_id=event.question.pk, metadata=event.metadata,
        ), actor=event.actor)

class QuestionEventPublisher:
    """Observer subject; synchronous to keep DB state deterministic."""
    _observers = (QuestionHistoryObserver(), QuestionAuditObserver())

    @classmethod
    def publish(cls, event: QuestionEvent):
        for observer in cls._observers:
            observer.update(event)
