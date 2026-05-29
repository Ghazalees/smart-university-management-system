import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Return consistent API error responses and log backend exceptions."""
    response = exception_handler(exc, context)
    view = context.get("view")
    request = context.get("request")

    logger.warning(
        "API exception handled",
        extra={
            "view": view.__class__.__name__ if view else None,
            "path": getattr(request, "path", None),
            "method": getattr(request, "method", None),
            "exception": exc.__class__.__name__,
        },
    )

    if response is None:
        logger.exception("Unhandled API exception", exc_info=exc)
        return response

    original_data = response.data
    message = "Request failed."

    if isinstance(original_data, dict):
        detail = original_data.get("detail")
        if detail:
            message = str(detail)
    elif isinstance(original_data, list) and original_data:
        message = str(original_data[0])

    response.data = {
        "success": False,
        "message": message,
        "errors": original_data,
    }
    return response
