from django.test import TestCase
from rest_framework.test import APIClient


class CoreInfrastructureTests(TestCase):
    """Sprint 1 tests for response format, middleware, and health routing."""

    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint_uses_standard_response_envelope(self):
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertIn("message", response.data)
        self.assertEqual(response.data["data"]["backend"], "ok")
        self.assertEqual(response.data["data"]["database"], "ok")

    def test_request_id_header_is_added(self):
        response = self.client.get("/api/v1/health", HTTP_X_REQUEST_ID="test-request-id")

        self.assertEqual(response["X-Request-ID"], "test-request-id")
