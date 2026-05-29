from django.db import connection
from rest_framework.views import APIView

from apps.core.responses import api_success


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """Handle GET /api/v1/health."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return api_success(
            message="Backend health check passed.",
            data={
                "backend": "ok",
                "database": "ok",
                "service": "smart-university-backend",
            },
            meta={"request_id": getattr(request, "request_id", None)},
        )
