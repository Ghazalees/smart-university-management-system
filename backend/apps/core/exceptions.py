"""Defines domain-specific exceptions for the grounded QA workflow."""

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _message_for_status(status_code):
    if status_code == 400:
        return "Request validation failed"
    if status_code == 401:
        return "Authentication failed"
    if status_code == 403:
        return "You do not have permission to perform this action"
    if status_code == 404:
        return "The requested resource was not found"
    if status_code == 429:
        return "Too many requests. Please try again later"
    return "Request failed"


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API exception", exc_info=exc)
        if settings.DEBUG:
            return None
        return Response(
            {
                "success": False,
                "message": "An unexpected error occurred",
                "errors": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    details = response.data
    response.data = {
        "success": False,
        "message": _message_for_status(response.status_code),
        "errors": details,
    }
    return response
