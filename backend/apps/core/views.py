from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .responses import success


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return success({"service": "backend", "status": "ok", "database": "ok"})
