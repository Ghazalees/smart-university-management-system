"""Verifies reports notifications behavior, authorization rules, validation, and regression scenarios."""

import pytest

from apps.accounts.models import Permission, Profile, Role, User, UserRole
from apps.documents.models import Document
from apps.notifications.models import Notification


@pytest.fixture
def reporting_permissions(roles):
    values = {
        code: Permission.objects.create(code=code, name=code)
        for code in ["reports.view_all", "notifications.broadcast"]
    }
    roles[Role.PRESIDENT].permissions.add(*values.values())
    return values


@pytest.fixture
def president(db, roles, reporting_permissions):
    user = User.objects.create_user(
        username="president-report",
        email="president-report@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(user=user)
    UserRole.objects.create(user=user, role=roles[Role.PRESIDENT])
    return user


@pytest.mark.django_db
def test_student_dashboard_has_student_scope(api_client, student):
    api_client.force_authenticate(student)
    response = api_client.get("/api/v1/reports/dashboard")
    assert response.status_code == 200
    assert response.data["data"]["scope"] == "student"
    assert "my_questions" in response.data["data"]
    assert "grades" in response.data["data"]


@pytest.mark.django_db
def test_president_dashboard_counts_published_documents(
    api_client, president, admin_user
):
    Document.objects.create(
        title="Published policy",
        content="Policy",
        status=Document.Status.PUBLISHED,
        created_by=admin_user,
    )
    api_client.force_authenticate(president)
    response = api_client.get("/api/v1/reports/dashboard")
    assert response.status_code == 200
    assert response.data["data"]["scope"] == "management"
    assert response.data["data"]["documents"] == 1
    assert "users_by_role" in response.data["data"]


@pytest.mark.django_db
def test_role_targeted_notification_broadcast(api_client, president, student, roles):
    api_client.force_authenticate(president)
    response = api_client.post(
        "/api/v1/notifications/broadcast",
        {
            "title": "Student policy update",
            "message": "A new policy is available.",
            "category": "management",
            "role_ids": [roles[Role.STUDENT].pk],
            "link": "/documents",
        },
        format="json",
    )
    assert response.status_code == 201
    assert Notification.objects.filter(recipient=student).count() == 1
    assert not Notification.objects.filter(recipient=president).exists()


@pytest.mark.django_db
def test_user_cannot_read_someone_elses_notification(api_client, student, admin_user):
    notification = Notification.objects.create(
        recipient=admin_user,
        title="Private",
        message="Private message",
        category=Notification.Category.SYSTEM,
    )
    api_client.force_authenticate(student)
    response = api_client.post(f"/api/v1/notifications/{notification.pk}/read")
    assert response.status_code == 404
