from dataclasses import dataclass
from threading import Lock
from typing import Any

from .models import AuditLog


class ServiceRegistry:
    """Singleton registry for infrastructure services."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._services = {}
        return cls._instance

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get(self, name: str) -> Any:
        return self._services[name]

    def has(self, name: str) -> bool:
        return name in self._services


@dataclass(frozen=True)
class AuditEvent:
    action: str
    entity_type: str = ""
    entity_id: str = ""
    metadata: dict | None = None


class AuditService:
    @staticmethod
    def record(event: AuditEvent, actor=None, request=None):
        ip = request.META.get("REMOTE_ADDR") if request else None
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=event.action,
            entity_type=event.entity_type,
            entity_id=str(event.entity_id),
            metadata=event.metadata or {},
            ip_address=ip,
        )
