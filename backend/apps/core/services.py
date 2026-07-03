"""Contains reusable business logic for shared platform infrastructure and cross-cutting utilities."""

from dataclasses import dataclass
from ipaddress import ip_address
from threading import Lock
from typing import Any

from .models import AuditLog


class ServiceRegistry:
    """Thread-safe Singleton registry for infrastructure services."""

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

    def clear(self) -> None:
        self._services.clear()


@dataclass(frozen=True)
class AuditEvent:
    action: str
    entity_type: str = ""
    entity_id: str = ""
    metadata: dict | None = None


def _request_ip(request):
    if not request:
        return None
    candidate = request.META.get("REMOTE_ADDR")
    try:
        return str(ip_address(candidate)) if candidate else None
    except ValueError:
        return None


class AuditService:
    @staticmethod
    def record(event: AuditEvent, actor=None, request=None):
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=event.action[:100],
            entity_type=event.entity_type[:100],
            entity_id=str(event.entity_id)[:64],
            metadata=event.metadata or {},
            ip_address=_request_ip(request),
        )
