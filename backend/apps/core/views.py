from django.db import connection
from django.db.utils import OperationalError
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        db_status = "ok"

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError:
            db_status = "error"

        status = "ok" if db_status == "ok" else "degraded"

        return Response({
            "success": db_status == "ok",
            "data": {
                "backend": "ok",
                "database": db_status,
            },
            "status": status
        })
