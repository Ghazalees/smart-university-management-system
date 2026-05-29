from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ServiceResult:
    """Reusable service-layer return object for future modules."""

    success: bool
    data: Optional[Any] = None
    message: str = ""
    errors: Optional[Any] = None

    @classmethod
    def ok(cls, data=None, message="Operation completed successfully."):
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, message="Operation failed.", errors=None):
        return cls(success=False, message=message, errors=errors)
