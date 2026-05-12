from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """Handle GET /api/v1/health."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return Response({"success": True, "data": {"backend": "ok", "database": "ok"}})
