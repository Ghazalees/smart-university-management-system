"""Applies cross-cutting request handling and security behavior."""

import logging
import time
import uuid

from .logging import request_id_context

logger = logging.getLogger(__name__)


def _safe_request_id(value):
    if not value or len(value) > 64:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        return str(uuid.uuid4())


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = _safe_request_id(request.headers.get("X-Request-ID"))
        request.request_id = request_id
        token = request_id_context.set(request_id)
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            return response
        finally:
            request_id_context.reset(token)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            actor_id = getattr(getattr(request, "user", None), "pk", None)
            logger.info(
                "%s %s status=%s duration_ms=%s actor_id=%s",
                request.method,
                request.path,
                getattr(response, "status_code", 500),
                elapsed_ms,
                actor_id or "anonymous",
            )
