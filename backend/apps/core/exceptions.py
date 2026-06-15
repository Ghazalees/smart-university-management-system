from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    details = response.data
    response.data = {
        "success": False,
        "message": "Request validation failed" if response.status_code == 400 else "Request failed",
        "errors": details,
    }
    return response
