from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, UserRole
from apps.documents.models import Document


class DocumentApiTests(TestCase):
    """Sprint 1 tests for Backend Developer 2 document APIs."""

    def setUp(self):
        self.client = APIClient()
        self.student = self._create_user("student@university.local", "student", "Student123!", Role.STUDENT)
        self.staff = self._create_user("staff@university.local", "staff", "Staff123!", Role.ADMINISTRATIVE_STAFF)

    def _create_user(self, email, username, password, role_name):
        User = get_user_model()
        role, _ = Role.objects.get_or_create(name=role_name)
        user = User.objects.create_user(email=email, username=username, password=password)
        UserRole.objects.create(user=user, role=role)
        return user

    def _login_and_get_token(self, email, password):
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": email, "password": password},
            format="json",
        )
        return response.data["data"]["token"]

    def test_staff_can_create_document(self):
        token = self._login_and_get_token("staff@university.local", "Staff123!")
        response = self.client.post(
            "/api/v1/documents",
            {
                "title": "Academic Calendar",
                "document_type": Document.DocumentType.GUIDE,
                "access_level": Document.AccessLevel.PUBLIC,
                "content": "Semester dates and deadlines.",
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["title"], "Academic Calendar")
        self.assertEqual(Document.objects.count(), 1)

    def test_student_cannot_create_document(self):
        token = self._login_and_get_token("student@university.local", "Student123!")
        response = self.client.post(
            "/api/v1/documents",
            {
                "title": "Unauthorized Document",
                "document_type": Document.DocumentType.OTHER,
                "access_level": Document.AccessLevel.PUBLIC,
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Document.objects.count(), 0)

    def test_student_sees_public_and_student_documents_only(self):
        Document.objects.create(
            title="Public FAQ",
            document_type=Document.DocumentType.FAQ,
            access_level=Document.AccessLevel.PUBLIC,
            content="Visible to everyone.",
            created_by=self.staff,
        )
        Document.objects.create(
            title="Student Guide",
            document_type=Document.DocumentType.GUIDE,
            access_level=Document.AccessLevel.STUDENT,
            content="Visible to students.",
            created_by=self.staff,
        )
        Document.objects.create(
            title="Staff Procedure",
            document_type=Document.DocumentType.POLICY,
            access_level=Document.AccessLevel.STAFF,
            content="Visible to staff only.",
            created_by=self.staff,
        )

        token = self._login_and_get_token("student@university.local", "Student123!")
        response = self.client.get("/api/v1/documents", HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(response.status_code, 200)
        titles = {item["title"] for item in response.data["data"]}
        self.assertEqual(titles, {"Public FAQ", "Student Guide"})
