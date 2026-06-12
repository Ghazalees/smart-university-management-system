from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Department, Permission, Role, UserRole


class BackendApiTests(TestCase):
    """Verify authentication, user management, RBAC, and audit behavior."""

    def setUp(self):
        """Create roles, permissions, a department, and demo users for API tests."""
        self.client = APIClient()
        self.department = Department.objects.create(name="Computer Engineering", code="CE")
        self._seed_permissions_and_roles()
        self.student = self._create_user("student@university.local", "student", "Student123!", Role.STUDENT)
        self.professor = self._create_user("professor@university.local", "professor", "Professor123!", Role.PROFESSOR)
        self.staff = self._create_user("staff@university.local", "staff", "Staff123!", Role.ADMINISTRATIVE_STAFF)
        self.president = self._create_user("president@university.local", "president", "President123!", Role.UNIVERSITY_PRESIDENT)

    def _seed_permissions_and_roles(self):
        """Create permissions and assign them to the four core roles."""
        permission_defs = [
            ("auth.login", "Login to system"),
            ("dashboard.view", "View dashboard"),
            ("profile.view", "View profile"),
            ("profile.update", "Update profile"),
            ("question.submit", "Submit questions"),
            ("question.read", "Read questions"),
            ("question.answer", "Answer questions"),
            ("user.read", "Read users"),
            ("user.manage", "Manage users"),
            ("role.manage", "Manage roles"),
            ("audit.read", "Read audit logs"),
        ]
        permissions = {}
        for code, name in permission_defs:
            permissions[code] = Permission.objects.create(code=code, name=name)
        role_permissions = {
            Role.STUDENT: ["auth.login", "dashboard.view", "profile.view", "question.submit"],
            Role.PROFESSOR: ["auth.login", "dashboard.view", "profile.view", "question.submit", "question.read", "question.answer"],
            Role.ADMINISTRATIVE_STAFF: ["auth.login", "dashboard.view", "profile.view", "user.read", "user.manage", "audit.read", "question.read", "question.answer"],
            Role.UNIVERSITY_PRESIDENT: list(permissions.keys()),
        }
        for role_name, codes in role_permissions.items():
            role = Role.objects.create(name=role_name)
            role.permissions.set([permissions[code] for code in codes])

    def _create_user(self, email, username, password, role_name):
        """Create a test user and assign the requested role."""
        User = get_user_model()
        role = Role.objects.get(name=role_name)
        user = User.objects.create_user(email=email, username=username, password=password)
        UserRole.objects.create(user=user, role=role)
        return user

    def _login_and_get_token(self, email, password):
        """Log in through the public API and return the generated token."""
        response = self.client.post("/api/v1/auth/login", {"email": email, "password": password}, format="json")
        return response.data["data"]["token"]

    def _auth(self, token):
        """Attach a bearer token to subsequent test requests."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

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
        self._auth(token)
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["role"], Role.STUDENT)
        self.assertEqual(response.data["data"]["dashboard"]["title"], "Student Dashboard")

    def test_staff_can_create_user(self):
        """Verify that administrative staff can create a new user."""
        token = self._login_and_get_token("staff@university.local", "Staff123!")
        self._auth(token)
        response = self.client.post(
            "/api/v1/users",
            {
                "email": "new.student@university.local",
                "username": "newstudent",
                "password": "Student123!",
                "first_name": "New",
                "last_name": "Student",
                "role": Role.STUDENT,
                "profile": {"full_name": "New Student", "student_number": "S-2002"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["role"], Role.STUDENT)

    def test_duplicate_user_is_rejected(self):
        """Verify that duplicate email addresses cannot be created."""
        token = self._login_and_get_token("staff@university.local", "Staff123!")
        self._auth(token)
        response = self.client.post(
            "/api/v1/users",
            {
                "email": "student@university.local",
                "username": "anotherstudent",
                "password": "Student123!",
                "role": Role.STUDENT,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_staff_can_update_user_role(self):
        """Verify that administrative staff can update a user's role."""
        token = self._login_and_get_token("staff@university.local", "Staff123!")
        self._auth(token)
        response = self.client.patch(
            f"/api/v1/users/{self.student.id}/role",
            {"role": Role.PROFESSOR},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["role"], Role.PROFESSOR)

    def test_student_cannot_list_users(self):
        """Verify that students cannot access user management APIs."""
        token = self._login_and_get_token("student@university.local", "Student123!")
        self._auth(token)
        response = self.client.get("/api/v1/users")
        self.assertEqual(response.status_code, 403)

    def test_staff_can_disable_user(self):
        """Verify that administrative staff can disable a user account."""
        token = self._login_and_get_token("staff@university.local", "Staff123!")
        self._auth(token)
        response = self.client.delete(f"/api/v1/users/{self.student.id}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_active"])

    def test_roles_permissions_and_audit_logs_are_available_to_staff(self):
        """Verify that RBAC reference data and audit logs are available to staff."""
        token = self._login_and_get_token("staff@university.local", "Staff123!")
        self._auth(token)
        roles_response = self.client.get("/api/v1/roles")
        permissions_response = self.client.get("/api/v1/permissions")
        logs_response = self.client.get("/api/v1/audit-logs")
        self.assertEqual(roles_response.status_code, 200)
        self.assertEqual(permissions_response.status_code, 200)
        self.assertEqual(logs_response.status_code, 200)
