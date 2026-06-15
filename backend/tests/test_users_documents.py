import pytest
from apps.accounts.models import Permission, Role
from apps.documents.models import Document

@pytest.fixture
def admin_with_permissions(admin_user, roles):
    for code in ["users.view", "users.manage", "users.assign_role", "documents.manage"]:
        p = Permission.objects.create(code=code, name=code)
        roles[Role.ADMIN_STAFF].permissions.add(p)
    return admin_user

@pytest.mark.django_db
def test_admin_creates_user(api_client, admin_with_permissions, roles):
    api_client.force_authenticate(admin_with_permissions)
    response = api_client.post("/api/v1/users", {
        "username": "prof1", "email": "prof1@example.com", "password": "StrongPass123!",
        "role_ids": [roles[Role.PROFESSOR].id],
    }, format="json")
    assert response.status_code == 201
    assert response.data["data"]["roles"] == [Role.PROFESSOR]

@pytest.mark.django_db
def test_duplicate_user_is_rejected(api_client, admin_with_permissions, student):
    api_client.force_authenticate(admin_with_permissions)
    response = api_client.post("/api/v1/users", {"username": student.username, "email": "new@example.com", "password": "StrongPass123!"}, format="json")
    assert response.status_code == 400

@pytest.mark.django_db
def test_role_restricted_document_visibility(api_client, student, admin_with_permissions, roles):
    document = Document.objects.create(title="Admin policy", content="secret", access_level=Document.AccessLevel.ROLE, created_by=admin_with_permissions)
    document.allowed_roles.add(roles[Role.ADMIN_STAFF])
    api_client.force_authenticate(student)
    assert api_client.get(f"/api/v1/documents/{document.id}").status_code == 404

@pytest.mark.django_db
def test_document_keyword_search(api_client, student, admin_with_permissions):
    Document.objects.create(title="Enrollment Guide", content="How to enroll", access_level=Document.AccessLevel.AUTHENTICATED, created_by=admin_with_permissions)
    Document.objects.create(title="Parking", content="Permit", access_level=Document.AccessLevel.AUTHENTICATED, created_by=admin_with_permissions)
    api_client.force_authenticate(student)
    response = api_client.get("/api/v1/documents?keyword=enroll")
    assert response.status_code == 200
    assert len(response.data["data"]) == 1
