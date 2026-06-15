import pytest
from django.test import override_settings

from apps.accounts.models import Permission, Role, UserRole
from apps.documents.models import Document
from apps.qa.adapters import AIAnswer
from apps.qa.exceptions import AIServiceUnavailable
from apps.qa.models import Question


class FakeProvider:
    def __init__(self, confidence=0.9):
        self.confidence = confidence

    def answer(self, **kwargs):
        return AIAnswer("Documented answer", self.confidence, "fake", "fake-v1")

    def analyze(self, text):
        return {
            "category": "academic",
            "priority": "Medium",
            "confidence": 0.8,
            "suggested_workflow": "academic-department-review",
        }


class DownProvider(FakeProvider):
    def answer(self, **kwargs):
        raise AIServiceUnavailable()


@pytest.fixture
def question_permissions(roles):
    values = {}
    for code in [
        "questions.create",
        "questions.view_own",
        "questions.view_all",
        "questions.answer",
    ]:
        values[code] = Permission.objects.create(code=code, name=code)
    roles[Role.STUDENT].permissions.add(
        values["questions.create"], values["questions.view_own"]
    )
    roles[Role.ADMIN_STAFF].permissions.add(*values.values())
    return values


@pytest.mark.django_db
def test_submit_and_history(api_client, student, question_permissions):
    api_client.force_authenticate(student)
    response = api_client.post(
        "/api/v1/questions", {"text": "How do I enroll in a course?"}, format="json"
    )
    assert response.status_code == 201
    qid = response.data["data"]["id"]
    history = api_client.get(f"/api/v1/questions/{qid}/history")
    assert history.status_code == 200
    assert history.data["data"][0]["event"] == "submitted"


@pytest.mark.django_db
def test_user_cannot_view_another_users_question(
    api_client, student, roles, question_permissions
):
    other = student.__class__.objects.create_user(
        username="other", email="other@example.com", password="StrongPass123!"
    )
    UserRole.objects.create(user=other, role=roles[Role.STUDENT])
    question = Question.objects.create(user=other, text="Private question")
    api_client.force_authenticate(student)
    assert api_client.get(f"/api/v1/questions/{question.id}").status_code == 404


@pytest.mark.django_db
@override_settings(AI_CONFIDENCE_THRESHOLD=0.55)
def test_documented_answer_changes_status(
    monkeypatch, api_client, student, admin_user, question_permissions
):
    Document.objects.create(
        title="Enrollment", content="Use the portal to enroll", created_by=admin_user
    )
    question = Question.objects.create(user=student, text="How do I enroll?")
    monkeypatch.setattr(
        "apps.qa.workflows.AIProviderFactory.create", lambda: FakeProvider(0.9)
    )
    api_client.force_authenticate(admin_user)
    response = api_client.post(
        f"/api/v1/questions/{question.id}/answer", {}, format="json"
    )
    assert response.status_code == 200
    question.refresh_from_db()
    assert question.status == Question.Status.ANSWERED
    assert question.response.sources.count() == 1


@pytest.mark.django_db
@override_settings(AI_CONFIDENCE_THRESHOLD=0.55)
def test_low_confidence_escalates(
    monkeypatch, api_client, student, admin_user, question_permissions
):
    Document.objects.create(
        title="General", content="General university information", created_by=admin_user
    )
    question = Question.objects.create(user=student, text="General information")
    monkeypatch.setattr(
        "apps.qa.workflows.AIProviderFactory.create", lambda: FakeProvider(0.2)
    )
    api_client.force_authenticate(admin_user)
    assert (
        api_client.post(
            f"/api/v1/questions/{question.id}/answer", {}, format="json"
        ).status_code
        == 200
    )
    question.refresh_from_db()
    assert question.status == Question.Status.ESCALATED


@pytest.mark.django_db
def test_ai_unavailable_marks_failed(
    monkeypatch, api_client, student, admin_user, question_permissions
):
    question = Question.objects.create(user=student, text="How do I enroll?")
    monkeypatch.setattr(
        "apps.qa.workflows.AIProviderFactory.create", lambda: DownProvider()
    )
    api_client.force_authenticate(admin_user)
    response = api_client.post(
        f"/api/v1/questions/{question.id}/answer", {}, format="json"
    )
    assert response.status_code == 503
    question.refresh_from_db()
    assert question.status == Question.Status.FAILED
