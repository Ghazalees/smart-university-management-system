from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, UserRole
from apps.documents.models import Document, DocumentAuditLog


class DocumentApiTests(TestCase):
    """Sprint 2 tests for Backend Developer 2 document APIs."""

    def setUp(self):
        self.client = APIClient()
        self.student = self._create_user(
            "student@university.local",
            "student",
            "Student123!",
            Role.STUDENT,
        )
        self.professor = self._create_user(
            "professor@university.local",
            "professor",
            "Professor123!",
            Role.PROFESSOR,
        )
        self.staff = self._create_user(
            "staff@university.local",
            "staff",
            "Staff123!",
            Role.ADMINISTRATIVE_STAFF,
        )
        self.president = self._create_user(
            "president@university.local",
            "president",
            "President123!",
            Role.UNIVERSITY_PRESIDENT,
        )

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

    def _auth(self, email="staff@university.local", password="Staff123!"):
        return {"HTTP_AUTHORIZATION": f"Bearer {self._login_and_get_token(email, password)}"}

    def test_staff_can_create_document_with_kb_metadata_and_audit_log(self):
        response = self.client.post(
            "/api/v1/documents",
            {
                "title": "Academic Calendar",
                "document_type": Document.DocumentType.GUIDE,
                "access_level": Document.AccessLevel.PUBLIC,
                "content": "Semester dates and deadlines.",
                "summary": "Calendar and deadline knowledge-base entry.",
                "keywords": "calendar, deadline, semester, calendar",
            },
            format="json",
            **self._auth(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Document created successfully.")
        self.assertEqual(response.data["data"]["title"], "Academic Calendar")
        self.assertEqual(response.data["data"]["keywords"], "calendar, deadline, semester")
        self.assertEqual(response.data["data"]["version"], 1)
        self.assertIsNotNone(response.data["data"]["last_updated_at"])
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(DocumentAuditLog.objects.count(), 1)
        self.assertEqual(DocumentAuditLog.objects.first().action, DocumentAuditLog.Action.CREATED)

    def test_student_cannot_create_document(self):
        response = self.client.post(
            "/api/v1/documents",
            {
                "title": "Unauthorized Document",
                "document_type": Document.DocumentType.OTHER,
                "access_level": Document.AccessLevel.PUBLIC,
            },
            format="json",
            **self._auth("student@university.local", "Student123!"),
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["success"])
        self.assertIn("errors", response.data)
        self.assertEqual(Document.objects.count(), 0)
        self.assertEqual(DocumentAuditLog.objects.count(), 0)

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

        response = self.client.get(
            "/api/v1/documents",
            **self._auth("student@university.local", "Student123!"),
        )

        self.assertEqual(response.status_code, 200)
        titles = {item["title"] for item in response.data["data"]}
        self.assertEqual(titles, {"Public FAQ", "Student Guide"})
        self.assertEqual(response.data["meta"]["count"], 2)

    def test_document_detail_route_returns_accessible_document(self):
        document = Document.objects.create(
            title="Public FAQ",
            document_type=Document.DocumentType.FAQ,
            access_level=Document.AccessLevel.PUBLIC,
            content="Visible to everyone.",
            created_by=self.staff,
        )

        response = self.client.get(
            f"/api/v1/documents/{document.id}",
            **self._auth("student@university.local", "Student123!"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], document.id)
        self.assertEqual(response.data["data"]["title"], "Public FAQ")

    def test_document_detail_rejects_restricted_document(self):
        document = Document.objects.create(
            title="Staff Procedure",
            document_type=Document.DocumentType.POLICY,
            access_level=Document.AccessLevel.STAFF,
            content="Visible to staff only.",
            created_by=self.staff,
        )

        response = self.client.get(
            f"/api/v1/documents/{document.id}",
            **self._auth("student@university.local", "Student123!"),
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["success"])

    def test_document_search_by_keyword_title_and_type(self):
        Document.objects.create(
            title="Scholarship FAQ",
            document_type=Document.DocumentType.FAQ,
            access_level=Document.AccessLevel.PUBLIC,
            content="Financial aid details.",
            summary="Scholarship and funding information.",
            keywords="scholarship, aid, funding",
            created_by=self.staff,
        )
        Document.objects.create(
            title="Library Rules",
            document_type=Document.DocumentType.POLICY,
            access_level=Document.AccessLevel.PUBLIC,
            content="Borrowing and study room details.",
            keywords="library, borrowing",
            created_by=self.staff,
        )

        keyword_response = self.client.get(
            "/api/v1/documents/search?keyword=funding",
            **self._auth("student@university.local", "Student123!"),
        )
        title_response = self.client.get(
            "/api/v1/documents/search?title=library",
            **self._auth("student@university.local", "Student123!"),
        )
        type_response = self.client.get(
            f"/api/v1/documents/search?document_type={Document.DocumentType.FAQ}",
            **self._auth("student@university.local", "Student123!"),
        )

        self.assertEqual(keyword_response.status_code, 200)
        self.assertEqual([item["title"] for item in keyword_response.data["data"]], ["Scholarship FAQ"])
        self.assertEqual([item["title"] for item in title_response.data["data"]], ["Library Rules"])
        self.assertEqual([item["title"] for item in type_response.data["data"]], ["Scholarship FAQ"])

    def test_knowledge_base_only_filter_returns_kb_enabled_documents(self):
        Document.objects.create(
            title="KB Enabled",
            document_type=Document.DocumentType.GUIDE,
            access_level=Document.AccessLevel.PUBLIC,
            is_knowledge_base_enabled=True,
            created_by=self.staff,
        )
        Document.objects.create(
            title="KB Disabled",
            document_type=Document.DocumentType.GUIDE,
            access_level=Document.AccessLevel.PUBLIC,
            is_knowledge_base_enabled=False,
            created_by=self.staff,
        )

        response = self.client.get(
            "/api/v1/documents/search?knowledge_base_only=true",
            **self._auth("student@university.local", "Student123!"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["title"] for item in response.data["data"]], ["KB Enabled"])

    def test_invalid_document_title_returns_standard_validation_error(self):
        response = self.client.post(
            "/api/v1/documents",
            {
                "title": " ",
                "document_type": Document.DocumentType.GUIDE,
                "access_level": Document.AccessLevel.PUBLIC,
            },
            format="json",
            **self._auth(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("title", response.data["errors"])

    def test_staff_can_update_and_archive_document_with_audit_logs(self):
        document = Document.objects.create(
            title="Old Policy",
            document_type=Document.DocumentType.POLICY,
            access_level=Document.AccessLevel.PUBLIC,
            created_by=self.staff,
            last_updated_by=self.staff,
        )

        update_response = self.client.patch(
            f"/api/v1/documents/{document.id}",
            {"title": "Updated Policy", "summary": "Updated summary."},
            format="json",
            **self._auth(),
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.data["data"]["title"], "Updated Policy")
        self.assertEqual(update_response.data["data"]["version"], 2)
        self.assertEqual(DocumentAuditLog.objects.count(), 1)
        self.assertEqual(DocumentAuditLog.objects.first().action, DocumentAuditLog.Action.UPDATED)

        archive_response = self.client.delete(
            f"/api/v1/documents/{document.id}",
            **self._auth(),
        )

        self.assertEqual(archive_response.status_code, 200)
        document.refresh_from_db()
        self.assertFalse(document.is_active)
        self.assertIsNotNone(document.archived_at)
        self.assertEqual(document.version, 3)
        self.assertEqual(DocumentAuditLog.objects.count(), 2)
        self.assertTrue(
            DocumentAuditLog.objects.filter(action=DocumentAuditLog.Action.ARCHIVED).exists()
        )

    def test_archived_documents_are_not_returned_in_list(self):
        Document.objects.create(
            title="Active Document",
            document_type=Document.DocumentType.GUIDE,
            access_level=Document.AccessLevel.PUBLIC,
            created_by=self.staff,
        )
        Document.objects.create(
            title="Archived Document",
            document_type=Document.DocumentType.GUIDE,
            access_level=Document.AccessLevel.PUBLIC,
            is_active=False,
            created_by=self.staff,
        )

        response = self.client.get(
            "/api/v1/documents",
            **self._auth("student@university.local", "Student123!"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["title"] for item in response.data["data"]], ["Active Document"])
