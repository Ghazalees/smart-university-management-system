import logging
import time
import uuid

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """
    Adds a stable request id to every request/response cycle.

    If the client sends X-Request-ID, the same value is reused.
    Otherwise, a new UUID is generated.
    """

    request_header = "HTTP_X_REQUEST_ID"
    response_header = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.request_header) or str(uuid.uuid4())
        request.request_id = request_id

        response = self.get_response(request)
        response[self.response_header] = request_id
        return response


class RequestLoggingMiddleware:
    """
    Logs every request with method, path, status code, duration, and request id.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        logger.info(
            "Request handled",
            extra={
                "request_id": getattr(request, "request_id", None),
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response