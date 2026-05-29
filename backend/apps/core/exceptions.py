import logging

from rest_framework import status
from rest_framework.views import exception_handler

from apps.core.responses import api_error

logger = logging.getLogger(__name__)


def _extract_message(original_data):
    """Extract a readable message from DRF exception payloads."""
    if isinstance(original_data, dict):
        detail = original_data.get("detail")
        if detail:
            return str(detail)
        if original_data:
            first_key = next(iter(original_data))
            first_value = original_data[first_key]
            if isinstance(first_value, list) and first_value:
                return f"{first_key}: {first_value[0]}"
            return f"{first_key}: {first_value}"
    if isinstance(original_data, list) and original_data:
        return str(original_data[0])
    return "Request failed."


def custom_exception_handler(exc, context):
    """Return consistent API error responses and log backend exceptions."""
    response = exception_handler(exc, context)
    view = context.get("view")
    request = context.get("request")
    request_id = getattr(request, "request_id", None)

    logger.warning(
        "API exception handled",
        extra={
            "request_id": request_id,
            "view": view.__class__.__name__ if view else None,
            "path": getattr(request, "path", None),
            "method": getattr(request, "method", None),
            "exception": exc.__class__.__name__,
        },
    )

    if response is None:
        logger.exception("Unhandled API exception", exc_info=exc)
        return api_error(
            message="Internal server error.",
            errors={"detail": "An unexpected server error occurred."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            meta={"request_id": request_id} if request_id else None,
        )

    original_data = response.data
    response.data = {
        "success": False,
        "message": _extract_message(original_data),
        "errors": original_data,
    }
    if request_id:
        response.data["meta"] = {"request_id": request_id}
    return response
