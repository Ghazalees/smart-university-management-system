from typing import Any, Optional

from rest_framework.response import Response


def api_success(
    *,
    data: Any = None,
    message: str = "Request completed successfully.",
    status_code: int = 200,
    meta: Optional[dict] = None,
) -> Response:
    """Return the standardized success response envelope used by all APIs."""
    payload = {
        "success": True,
        "message": message,
        "data": data if data is not None else {},
    }
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status_code)


def api_error(
    *,
    message: str = "Request failed.",
    errors: Any = None,
    status_code: int = 400,
    data: Any = None,
    meta: Optional[dict] = None,
) -> Response:
    """Return the standardized error response envelope used by all APIs."""
    payload = {
        "success": False,
        "message": message,
        "errors": errors if errors is not None else {},
    }
    if data is not None:
        payload["data"] = data
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status_code)
