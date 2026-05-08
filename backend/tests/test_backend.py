from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import Department, Role, UserRole


class SprintOneTests(TestCase):

    def setUp(self):
        """Create roles, a department, and demo users for API tests."""
        self.client = APIClient()
        self.department = Department.objects.create(name="Computer Engineering", code="CE")
        self.student = self._create_user("student@university.local", "student", "Student123!", Role.STUDENT)
        self.professor = self._create_user("professor@university.local", "professor", "Professor123!", Role.PROFESSOR)
        self.staff = self._create_user("staff@university.local", "staff", "Staff123!", Role.ADMINISTRATIVE_STAFF)
        self.president = self._create_user("president@university.local", "president", "President123!", Role.UNIVERSITY_PRESIDENT)

    def _create_user(self, email, username, password, role_name):
        """Create a test user and assign the requested role."""
        User = get_user_model()
        role, _ = Role.objects.get_or_create(name=role_name)
        user = User.objects.create_user(email=email, username=username, password=password)
        UserRole.objects.create(user=user, role=role)
        return user

    def test_login_returns_token_and_role(self):
        """Verify that valid credentials return a token and role."""
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": "student@university.local", "password": "Student123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertIn("token", response.data["data"])
        self.assertEqual(response.data["data"]["role"], Role.STUDENT)

    def test_login_rejects_invalid_password(self):
        """Verify that invalid credentials are rejected."""
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": "student@university.local", "password": "WrongPassword"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data["success"])

    def test_auth_me_requires_token(self):
        """Verify that the current-user endpoint is protected."""
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 403)

    def test_auth_me_returns_student_dashboard(self):
        """Verify that Strategy Pattern returns the student dashboard."""
        token = self._login_and_get_token("student@university.local", "Student123!")
        response = self.client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["role"], Role.STUDENT)
        self.assertEqual(response.data["data"]["dashboard"]["title"], "Student Dashboard")

    def test_auth_me_returns_president_dashboard(self):
        """Verify that Strategy Pattern returns the president dashboard."""
        token = self._login_and_get_token("president@university.local", "President123!")
        response = self.client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["role"], Role.UNIVERSITY_PRESIDENT)
        self.assertEqual(response.data["data"]["dashboard"]["title"], "University President Dashboard")

    def _login_and_get_token(self, email, password):
        """Log in through the public API and return the generated token."""
        response = self.client.post("/api/v1/auth/login", {"email": email, "password": password}, format="json")
        return response.data["data"]["token"]
