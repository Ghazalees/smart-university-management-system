import logging
import time
import uuid

logger = logging.getLogger("apps.core")


class RequestIDMiddleware:
    """Attach a stable request id to each request and response.

    This middleware is intentionally small and dependency-free so it can safely run
    in local development, tests, Docker, and production-like environments.
    """

    HEADER_NAME = "HTTP_X_REQUEST_ID"
    RESPONSE_HEADER_NAME = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.HEADER_NAME) or str(uuid.uuid4())
        request.request_id = request_id

        response = self.get_response(request)
        response[self.RESPONSE_HEADER_NAME] = request_id
        return response


class RequestLoggingMiddleware:
    """Log one compact line per request.

    The middleware avoids logging request bodies or sensitive headers. It only logs
    method, path, status code, duration, and request id.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        request_id = getattr(request, "request_id", "-")
        status_code = getattr(response, "status_code", "-")

        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.get_full_path(),
            status_code,
            duration_ms,
        )

        return response
