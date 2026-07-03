"""Provides reusable decorators for knowledge documents, versions, extraction, and governance."""

from functools import wraps

from apps.core.services import AuditEvent, AuditService


def audited(action):
    """Decorator pattern for reusable service-level auditing."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            actor = kwargs.get("actor")
            request = kwargs.get("request")
            AuditService.record(
                AuditEvent(action, "Document", getattr(result, "pk", "")),
                actor=actor,
                request=request,
            )
            return result

        return wrapper

    return decorator
