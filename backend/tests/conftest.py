import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Profile, Role, User, UserRole


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def roles(db):
    return {
        name: Role.objects.create(name=name, is_system=True)
        for name in Role.SYSTEM_ROLES
    }


@pytest.fixture
def student(db, roles):
    user = User.objects.create_user(
        username="student", email="student@example.com", password="StrongPass123!"
    )
    Profile.objects.create(user=user)
    UserRole.objects.create(user=user, role=roles[Role.STUDENT])
    return user


@pytest.fixture
def admin_user(db, roles):
    user = User.objects.create_user(
        username="adminstaff", email="admin@example.com", password="StrongPass123!"
    )
    Profile.objects.create(user=user)
    UserRole.objects.create(user=user, role=roles[Role.ADMIN_STAFF])
    return user


@pytest.fixture
def auth_client(api_client, student):
    api_client.force_authenticate(student)
    return api_client
