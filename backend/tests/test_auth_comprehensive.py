"""Verifies auth comprehensive behavior, authorization rules, validation, and regression scenarios."""

from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.commands import LoginCommand
from apps.accounts.models import Permission, Profile, Role, User, UserRole


@pytest.mark.django_db
def test_login_accepts_email_case_insensitively(api_client, student):
    response = api_client.post(
        "/api/v1/auth/login",
        {"email": "STUDENT@EXAMPLE.COM", "password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["data"]["user"]["username"] == "student"


@pytest.mark.django_db
def test_missing_identifier_is_validation_error(api_client):
    response = api_client.post(
        "/api/v1/auth/login", {"password": "StrongPass123!"}, format="json"
    )
    assert response.status_code == 400
    assert response.data["success"] is False


@pytest.mark.django_db
def test_unknown_and_wrong_password_have_same_public_message(api_client, student):
    wrong = api_client.post(
        "/api/v1/auth/login",
        {"identifier": "student", "password": "not-the-password"},
        format="json",
    )
    missing = api_client.post(
        "/api/v1/auth/login",
        {"identifier": "does-not-exist", "password": "not-the-password"},
        format="json",
    )
    assert wrong.status_code == missing.status_code == 401
    assert wrong.data["message"] == missing.data["message"]


@pytest.mark.django_db
def test_inactive_user_receives_generic_login_failure(api_client, student):
    student.is_active = False
    student.deactivated_at = timezone.now()
    student.save(update_fields=["is_active", "deactivated_at", "updated_at"])
    response = api_client.post(
        "/api/v1/auth/login",
        {"identifier": "student", "password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 401
    assert "inactive" not in response.data["message"].lower()


@pytest.mark.django_db
@override_settings(LOGIN_MAX_ATTEMPTS=5, ACCOUNT_LOCK_MINUTES=15)
def test_account_lockout_boundary_and_expiry(student):
    for expected in range(1, 5):
        with pytest.raises(Exception):
            LoginCommand("student", "wrong").execute()
        student.refresh_from_db()
        assert student.failed_login_attempts == expected
        assert student.locked_until is None

    with pytest.raises(Exception):
        LoginCommand("student", "wrong").execute()
    student.refresh_from_db()
    assert student.failed_login_attempts == 5
    assert student.is_locked()

    student.locked_until = timezone.now() - timedelta(seconds=1)
    student.save(update_fields=["locked_until", "updated_at"])
    user, _ = LoginCommand("student", "StrongPass123!").execute()
    user.refresh_from_db()
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


@pytest.mark.django_db
def test_refresh_rotates_and_replay_is_rejected(api_client, student):
    old_refresh = str(RefreshToken.for_user(student))
    first = api_client.post(
        "/api/v1/auth/refresh", {"refresh": old_refresh}, format="json"
    )
    assert first.status_code == 200
    new_refresh = first.data["data"]["tokens"]["refresh"]
    assert new_refresh != old_refresh
    assert (
        api_client.post(
            "/api/v1/auth/refresh", {"refresh": old_refresh}, format="json"
        ).status_code
        == 401
    )
    assert (
        api_client.post(
            "/api/v1/auth/refresh", {"refresh": new_refresh}, format="json"
        ).status_code
        == 200
    )


@pytest.mark.django_db
def test_invalid_refresh_is_rejected(api_client):
    response = api_client.post(
        "/api/v1/auth/refresh", {"refresh": "tampered.token.value"}, format="json"
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_change_password_rejects_wrong_current_password(api_client, student):
    api_client.force_authenticate(student)
    response = api_client.post(
        "/api/v1/auth/change-password",
        {"current_password": "wrong", "new_password": "DifferentPass456!"},
        format="json",
    )
    assert response.status_code == 400
    student.refresh_from_db()
    assert student.check_password("StrongPass123!")


@pytest.mark.django_db
def test_change_password_blacklists_outstanding_refresh_tokens(api_client, student):
    refresh = RefreshToken.for_user(student)
    api_client.force_authenticate(student)
    response = api_client.post(
        "/api/v1/auth/change-password",
        {
            "current_password": "StrongPass123!",
            "new_password": "DifferentPass456!",
        },
        format="json",
    )
    assert response.status_code == 200
    student.refresh_from_db()
    assert student.check_password("DifferentPass456!")
    assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()
    api_client.force_authenticate(user=None)
    assert (
        api_client.post(
            "/api/v1/auth/refresh", {"refresh": str(refresh)}, format="json"
        ).status_code
        == 401
    )


@pytest.mark.django_db
def test_change_password_rejects_same_password(api_client, student):
    api_client.force_authenticate(student)
    response = api_client.post(
        "/api/v1/auth/change-password",
        {"current_password": "StrongPass123!", "new_password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_malformed_access_token_cannot_open_protected_resource(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer malformed.jwt.token")
    response = api_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.fixture
def president_with_permissions(db, roles):
    permissions = {
        code: Permission.objects.create(code=code, name=code)
        for code in ["users.view", "users.manage", "users.assign_role"]
    }
    role = roles[Role.PRESIDENT]
    role.permissions.add(*permissions.values())
    president = User.objects.create_user(
        username="president",
        email="president@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(user=president)
    UserRole.objects.create(user=president, role=role)
    return president


@pytest.mark.django_db
def test_final_president_cannot_be_deactivated(api_client, president_with_permissions):
    api_client.force_authenticate(president_with_permissions)
    response = api_client.delete(
        f"/api/v1/users/{president_with_permissions.pk}", format="json"
    )
    assert response.status_code == 400
    president_with_permissions.refresh_from_db()
    assert president_with_permissions.is_active


@pytest.mark.django_db
def test_manager_cannot_change_own_roles(api_client, president_with_permissions, roles):
    api_client.force_authenticate(president_with_permissions)
    response = api_client.patch(
        f"/api/v1/users/{president_with_permissions.pk}/roles",
        {"role_ids": [roles[Role.STUDENT].pk]},
        format="json",
    )
    assert response.status_code == 400
    assert president_with_permissions.roles.filter(name=Role.PRESIDENT).exists()
