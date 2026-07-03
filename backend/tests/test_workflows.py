"""Verifies workflows behavior, authorization rules, validation, and regression scenarios."""

import pytest

from apps.accounts.models import Permission, Profile, Role, User, UserRole
from apps.notifications.models import Notification
from apps.workflows.models import WorkflowRequest, WorkflowType


@pytest.fixture
def workflow_permissions(roles):
    values = {
        code: Permission.objects.create(code=code, name=code)
        for code in [
            "workflows.create",
            "workflows.view_own",
            "workflows.view_all",
            "workflows.review",
            "workflows.configure",
        ]
    }
    roles[Role.STUDENT].permissions.add(
        values["workflows.create"], values["workflows.view_own"]
    )
    roles[Role.ADMIN_STAFF].permissions.add(*values.values())
    return values


@pytest.fixture
def workflow_type(roles, workflow_permissions):
    value = WorkflowType.objects.create(
        code="leave", name="Leave request", schema={"reason": {"required": True}}
    )
    value.allowed_roles.add(roles[Role.STUDENT])
    return value


@pytest.fixture
def other_student(db, roles):
    user = User.objects.create_user(
        username="other-student",
        email="other-student@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(user=user)
    UserRole.objects.create(user=user, role=roles[Role.STUDENT])
    return user


@pytest.mark.django_db
def test_workflow_happy_path_creates_history_and_notification(
    api_client, student, admin_user, workflow_type, workflow_permissions
):
    api_client.force_authenticate(student)
    created = api_client.post(
        "/api/v1/workflow-requests",
        {
            "request_type": workflow_type.pk,
            "title": "Medical leave",
            "description": "Requesting one week of leave",
            "payload": {"reason": "medical"},
        },
        format="json",
    )
    assert created.status_code == 201
    request_id = created.data["data"]["id"]
    assert created.data["data"]["status"] == WorkflowRequest.Status.DRAFT
    assert created.data["data"]["history"][0]["event"] == "created"

    submitted = api_client.post(
        f"/api/v1/workflow-requests/{request_id}/transition",
        {"action": "submit", "expected_version": 1},
        format="json",
    )
    assert submitted.status_code == 200
    assert submitted.data["data"]["status"] == WorkflowRequest.Status.PENDING

    api_client.force_authenticate(admin_user)
    started = api_client.post(
        f"/api/v1/workflow-requests/{request_id}/transition",
        {"action": "start_review", "expected_version": 2},
        format="json",
    )
    assert started.status_code == 200
    approved = api_client.post(
        f"/api/v1/workflow-requests/{request_id}/transition",
        {"action": "approve", "expected_version": 3, "note": "Requirements met"},
        format="json",
    )
    assert approved.status_code == 200
    assert approved.data["data"]["status"] == WorkflowRequest.Status.APPROVED
    obj = WorkflowRequest.objects.get(pk=request_id)
    assert obj.history.filter(event="approve").count() == 1
    assert Notification.objects.filter(
        recipient=student, metadata__request_id=request_id
    ).exists()


@pytest.mark.django_db
def test_stale_workflow_version_is_rejected(
    api_client, student, admin_user, workflow_type, workflow_permissions
):
    obj = WorkflowRequest.objects.create(
        request_type=workflow_type,
        requester=student,
        title="Certificate",
        description="Need a certificate",
        status=WorkflowRequest.Status.PENDING,
        current_step=WorkflowRequest.Status.PENDING,
        version=4,
    )
    api_client.force_authenticate(admin_user)
    response = api_client.post(
        f"/api/v1/workflow-requests/{obj.pk}/assign",
        {"assigned_to": admin_user.pk, "expected_version": 3},
        format="json",
    )
    assert response.status_code == 400
    obj.refresh_from_db()
    assert obj.assigned_to is None
    assert obj.version == 4


@pytest.mark.django_db
def test_other_student_cannot_view_private_workflow(
    api_client, student, other_student, workflow_type, workflow_permissions
):
    obj = WorkflowRequest.objects.create(
        request_type=workflow_type,
        requester=student,
        title="Private",
        description="Private request",
    )
    api_client.force_authenticate(other_student)
    assert api_client.get(f"/api/v1/workflow-requests/{obj.pk}").status_code == 403


@pytest.mark.django_db
def test_reject_and_revision_require_reason(
    api_client, student, admin_user, workflow_type, workflow_permissions
):
    obj = WorkflowRequest.objects.create(
        request_type=workflow_type,
        requester=student,
        title="Request",
        description="Description",
        status=WorkflowRequest.Status.UNDER_REVIEW,
        current_step=WorkflowRequest.Status.UNDER_REVIEW,
    )
    api_client.force_authenticate(admin_user)
    response = api_client.post(
        f"/api/v1/workflow-requests/{obj.pk}/transition",
        {"action": "reject", "expected_version": 1, "note": ""},
        format="json",
    )
    assert response.status_code == 400
    obj.refresh_from_db()
    assert obj.status == WorkflowRequest.Status.UNDER_REVIEW


@pytest.mark.django_db
def test_invalid_state_transition_is_rejected(
    api_client, student, admin_user, workflow_type, workflow_permissions
):
    obj = WorkflowRequest.objects.create(
        request_type=workflow_type,
        requester=student,
        title="Request",
        description="Description",
        status=WorkflowRequest.Status.DRAFT,
    )
    api_client.force_authenticate(admin_user)
    response = api_client.post(
        f"/api/v1/workflow-requests/{obj.pk}/transition",
        {"action": "approve", "expected_version": 1, "note": "No"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_workflow_payload_must_include_schema_required_fields(
    api_client, student, workflow_type, workflow_permissions
):
    api_client.force_authenticate(student)
    response = api_client.post(
        "/api/v1/workflow-requests",
        {
            "request_type": workflow_type.id,
            "title": "Leave request",
            "description": "I need an academic leave.",
            "payload": {},
        },
        format="json",
    )
    assert response.status_code == 400
    assert "payload" in response.data["errors"]


@pytest.mark.django_db
def test_workflow_cannot_be_assigned_to_non_reviewer(
    api_client, admin_user, student, workflow_type, workflow_permissions
):
    obj = WorkflowRequest.objects.create(
        request_type=workflow_type,
        requester=student,
        title="Private",
        description="Private request",
        status=WorkflowRequest.Status.PENDING,
        current_step=WorkflowRequest.Status.PENDING,
    )
    api_client.force_authenticate(admin_user)
    response = api_client.post(
        f"/api/v1/workflow-requests/{obj.id}/assign",
        {"assigned_to": student.id, "expected_version": obj.version},
        format="json",
    )
    assert response.status_code == 400
