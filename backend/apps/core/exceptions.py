from rest_framework.views import exception_handler

from apps.core.responses import api_error


def custom_exception_handler(exc, context):
    """
    Return all DRF exceptions using the project's standard API error format.

    This keeps authentication, permission, validation, and not-found errors
    consistent with the rest of the backend response contract.
    """
    response = exception_handler(exc, context)

    if response is None:
        return None

    detail = response.data.get("detail") if isinstance(response.data, dict) else response.data

    if isinstance(response.data, dict) and "detail" not in response.data:
        errors = response.data
    else:
        errors = None

    message = str(detail) if detail else "Request failed."

    return api_error(
        message=message,
        errors=errors,
        status_code=response.status_code,
    )
