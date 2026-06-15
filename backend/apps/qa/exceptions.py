from rest_framework.exceptions import APIException


class AIServiceUnavailable(APIException):
    status_code = 503
    default_detail = "AI service is currently unavailable."
    default_code = "ai_service_unavailable"
