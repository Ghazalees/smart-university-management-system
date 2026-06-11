from rest_framework.response import Response


def api_success(message="Success.", data=None, meta=None, status_code=200):
    """
    Return a consistent successful API response.

    Shape:
    {
        "success": true,
        "message": "...",
        "data": {...},
        "meta": {...}
    }
    """
    payload = {
        "success": True,
        "message": message,
        "data": data,
    }

    if meta is not None:
        payload["meta"] = meta

    return Response(payload, status=status_code)


def api_error(message="Request failed.", errors=None, status_code=400):
    """
    Return a consistent error API response.

    Shape:
    {
        "success": false,
        "message": "...",
        "errors": {...}
    }
    """
    payload = {
        "success": False,
        "message": message,
        "errors": errors,
    }

    return Response(payload, status=status_code)
