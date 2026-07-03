"""Verifies experience advanced behavior, authorization rules, validation, and regression scenarios."""

from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Department, Permission, Profile, Role, User, UserRole
from apps.academics.models import (
    AcademicClass,
    Course,
    CoursePrerequisite,
    Enrollment,
    ProgramRequirement,
)
from apps.core.models import AuditLog
from apps.documents.models import Document, DocumentVersion
from apps.documents.repositories import DocumentRepositoryFactory
from apps.documents.services import DocumentService
from apps.notifications.models import Notification
from apps.qa.models import Question, QuestionResponse


def grant(role, *codes):
    for code in codes:
        permission, _ = Permission.objects.get_or_create(
            code=code, defaults={"name": code}
        )
        role.permissions.add(permission)


@pytest.fixture
def experience_admin(admin_user, roles):
    grant(
        roles[Role.ADMIN_STAFF],
        "feedback.manage",
        "documents.manage",
        "users.view",
        "academics.manage",
        "reports.view_all",
        "questions.view_all",
        "questions.answer",
    )
    return admin_user


@pytest.fixture
def professor_user(db, roles):
    grant(roles[Role.PROFESSOR], "classes.create")
    user = User.objects.create_user(
        username="advanced-professor",
        email="advanced-professor@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(user=user)
    UserRole.objects.create(user=user, role=roles[Role.PROFESSOR])
    return user


@pytest.mark.django_db
def test_experience_preferences_are_persisted_and_validated(api_client, student):
    api_client.force_authenticate(student)
    response = api_client.patch(
        "/api/v1/experience/preferences",
        {"accent_color": "coral", "density": "compact", "reduced_motion": True},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["data"]["accent_color"] == "coral"
    assert response.data["data"]["reduced_motion"] is True

    invalid = api_client.patch(
        "/api/v1/experience/preferences", {"accent_color": "unsafe-css"}, format="json"
    )
    assert invalid.status_code == 400


@pytest.mark.django_db
def test_feedback_is_private_but_manageable_by_authorized_staff(
    api_client, student, experience_admin
):
    api_client.force_authenticate(student)
    created = api_client.post(
        "/api/v1/feedback",
        {
            "feedback_type": "idea",
            "title": "Better calendar",
            "message": "Add agenda focus",
            "rating": 5,
        },
        format="json",
    )
    assert created.status_code == 201
    feedback_id = created.data["data"]["id"]

    api_client.force_authenticate(experience_admin)
    listing = api_client.get("/api/v1/feedback")
    assert listing.status_code == 200
    assert any(item["id"] == feedback_id for item in listing.data["data"])
    managed = api_client.patch(
        f"/api/v1/feedback/{feedback_id}",
        {"status": "in_progress", "admin_note": "Added to roadmap"},
        format="json",
    )
    assert managed.status_code == 200
    assert managed.data["data"]["status"] == "in_progress"


@pytest.mark.django_db
def test_global_search_never_leaks_role_restricted_documents(
    api_client, student, experience_admin, roles
):
    public = DocumentService.create(
        actor=experience_admin,
        title="Student enrollment roadmap",
        content="Enrollment guidance",
        access_level=Document.AccessLevel.AUTHENTICATED,
        status=Document.Status.PUBLISHED,
    )
    restricted = DocumentService.create(
        actor=experience_admin,
        title="Enrollment finance secret",
        content="Restricted enrollment budget",
        access_level=Document.AccessLevel.ROLE,
        status=Document.Status.PUBLISHED,
        allowed_roles=[roles[Role.ADMIN_STAFF]],
    )
    api_client.force_authenticate(student)
    response = api_client.get("/api/v1/search?q=enrollment")
    assert response.status_code == 200
    document_ids = {
        item["identifier"]
        for item in response.data["data"]["results"]
        if item["result_type"] == "document"
    }
    assert public.pk in document_ids
    assert restricted.pk not in document_ids
    assert api_client.get("/api/v1/search?q=x&limit=bad").status_code == 400


@pytest.mark.django_db
def test_calendar_is_role_scoped_and_rejects_excessive_ranges(
    api_client, student, professor_user
):
    course = Course.objects.create(code="CAL101", title="Calendar Design")
    own = AcademicClass.objects.create(
        course=course,
        professor=professor_user,
        term="2026-Fall",
        section="01",
        weekday=timezone.localdate().isoweekday(),
        start_time=time(9),
        end_time=time(10),
        location="Room 1",
    )
    Enrollment.objects.create(academic_class=own, student=student)
    other_course = Course.objects.create(code="CAL999", title="Hidden Seminar")
    AcademicClass.objects.create(
        course=other_course,
        professor=professor_user,
        term="2026-Fall",
        section="01",
        weekday=timezone.localdate().isoweekday(),
        start_time=time(13),
        end_time=time(14),
        location="Room 2",
    )
    api_client.force_authenticate(student)
    start = (timezone.now() - timedelta(days=1)).isoformat()
    end = (timezone.now() + timedelta(days=2)).isoformat()
    response = api_client.get("/api/v1/calendar", {"start": start, "end": end})
    assert response.status_code == 200
    titles = [item["title"] for item in response.data["data"]["events"]]
    assert any("CAL101" in title for title in titles)
    assert not any("CAL999" in title for title in titles)

    excessive_end = (timezone.now() + timedelta(days=181)).isoformat()
    assert (
        api_client.get(
            "/api/v1/calendar", {"start": start, "end": excessive_end}
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_degree_progress_and_recommendations_use_requirements_and_prerequisites(
    api_client, student
):
    department = Department.objects.create(code="ADV", name="Advanced Studies")
    student.department = department
    student.save(update_fields=["department"])
    intro = Course.objects.create(
        code="ADV101", title="Foundation", credits=3, department=department
    )
    next_course = Course.objects.create(
        code="ADV201", title="Advanced Topic", credits=3, department=department
    )
    ProgramRequirement.objects.create(
        department=department, course=intro, recommended_term=1
    )
    ProgramRequirement.objects.create(
        department=department, course=next_course, recommended_term=2
    )
    CoursePrerequisite.objects.create(course=next_course, prerequisite=intro)

    api_client.force_authenticate(student)
    progress = api_client.get("/api/v1/academics/degree-progress")
    assert progress.status_code == 200
    assert progress.data["data"]["total_credits"] == 6
    recommendations = api_client.get("/api/v1/academics/recommendations")
    assert recommendations.status_code == 200
    assert any(
        item["code"].startswith("requirement-")
        for item in recommendations.data["data"]["recommendations"]
    )


@pytest.mark.django_db
def test_smart_scheduler_returns_ranked_conflict_free_slots(api_client, professor_user):
    api_client.force_authenticate(professor_user)
    response = api_client.post(
        "/api/v1/academics/schedule-suggestions",
        {
            "professor": professor_user.pk,
            "term": "2026-Fall",
            "duration_minutes": 90,
            "weekdays": [1, 2],
            "location": "R-100",
        },
        format="json",
    )
    assert response.status_code == 200
    suggestions = response.data["data"]["suggestions"]
    assert suggestions
    assert suggestions == sorted(
        suggestions, key=lambda row: (-row["score"], row["weekday"], row["start_time"])
    )


@pytest.mark.django_db
def test_document_versioning_restore_and_import_validation(
    api_client, experience_admin
):
    api_client.force_authenticate(experience_admin)
    created = api_client.post(
        "/api/v1/documents",
        {
            "title": "Versioned policy",
            "document_type": "policy",
            "content": "Version one",
            "status": "draft",
            "access_level": "authenticated",
            "knowledge_enabled": True,
        },
        format="json",
    )
    assert created.status_code == 201
    document_id = created.data["data"]["id"]
    updated = api_client.patch(
        f"/api/v1/documents/{document_id}",
        {"content": "Version two", "change_summary": "Clarified policy"},
        format="json",
    )
    assert updated.status_code == 200
    assert DocumentVersion.objects.filter(document_id=document_id).count() == 2
    restored = api_client.post(f"/api/v1/documents/{document_id}/versions/1/restore")
    assert restored.status_code == 200
    assert restored.data["data"]["content"] == "Version one"

    malformed = api_client.post(
        "/api/v1/documents/import",
        {"format": "json", "content": "{broken"},
        format="json",
    )
    assert malformed.status_code == 400


@pytest.mark.django_db
def test_expired_or_future_documents_are_excluded_from_rag(student, experience_admin):
    expired = DocumentService.create(
        actor=experience_admin,
        title="Expired AI rule",
        content="expired-token",
        access_level=Document.AccessLevel.AUTHENTICATED,
        status=Document.Status.PUBLISHED,
        knowledge_enabled=True,
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    future = DocumentService.create(
        actor=experience_admin,
        title="Future AI rule",
        content="future-token",
        access_level=Document.AccessLevel.AUTHENTICATED,
        status=Document.Status.PUBLISHED,
        knowledge_enabled=True,
        effective_from=timezone.now() + timedelta(days=1),
    )
    current = DocumentService.create(
        actor=experience_admin,
        title="Current AI rule",
        content="current-token",
        access_level=Document.AccessLevel.AUTHENTICATED,
        status=Document.Status.PUBLISHED,
        knowledge_enabled=True,
    )
    ids = set(
        DocumentRepositoryFactory.create()
        .accessible_to(student, knowledge_only=True)
        .values_list("id", flat=True)
    )
    assert current.pk in ids
    assert expired.pk not in ids
    assert future.pk not in ids


@pytest.mark.django_db
def test_notification_center_actions_and_digest(api_client, student):
    notification = Notification.objects.create(
        recipient=student,
        title="Urgent registration",
        message="Complete registration today",
        category=Notification.Category.ACADEMIC,
        priority="urgent",
    )
    api_client.force_authenticate(student)
    pinned = api_client.post(
        f"/api/v1/notifications/{notification.pk}/action",
        {"action": "pin"},
        format="json",
    )
    assert pinned.status_code == 200
    assert pinned.data["data"]["is_pinned"] is True
    digest = api_client.get("/api/v1/notifications/digest?period=daily")
    assert digest.status_code == 200
    assert digest.data["data"]["urgent"] == 1


@pytest.mark.django_db
def test_ai_answer_feedback_can_only_be_submitted_by_question_owner(
    api_client, student, experience_admin
):
    question = Question.objects.create(user=student, text="Explain enrollment")
    QuestionResponse.objects.create(
        question=question,
        answer="Grounded answer",
        confidence=0.9,
        provider="test",
        is_documented=True,
    )
    api_client.force_authenticate(experience_admin)
    assert (
        api_client.post(
            f"/api/v1/questions/{question.pk}/feedback", {"rating": 1}, format="json"
        ).status_code
        == 404
    )
    api_client.force_authenticate(student)
    own = api_client.post(
        f"/api/v1/questions/{question.pk}/feedback",
        {"rating": 1, "comment": "Useful"},
        format="json",
    )
    assert own.status_code == 200


@pytest.mark.django_db
def test_activity_feed_is_private_for_non_management_users(
    api_client, student, admin_user
):
    AuditLog.objects.create(
        actor=student,
        action="student.action",
        entity_type="User",
        entity_id=str(student.pk),
    )
    AuditLog.objects.create(
        actor=admin_user,
        action="admin.secret",
        entity_type="User",
        entity_id=str(admin_user.pk),
    )
    api_client.force_authenticate(student)
    response = api_client.get("/api/v1/activity-feed")
    assert response.status_code == 200
    actions = {item["action"] for item in response.data["data"]["items"]}
    assert "student.action" in actions
    assert "admin.secret" not in actions
