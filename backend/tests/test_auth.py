import pytest
from rest_framework_simplejwt.tokens import RefreshToken

@pytest.mark.django_db
def test_valid_login_returns_tokens_and_role(api_client, student):
    response = api_client.post("/api/v1/auth/login", {"username": "student", "password": "StrongPass123!"}, format="json")
    assert response.status_code == 200
    assert response.data["data"]["tokens"]["access"]
    assert "Student" in response.data["data"]["user"]["roles"]

@pytest.mark.django_db
def test_invalid_login_is_401(api_client, student):
    response = api_client.post("/api/v1/auth/login", {"username": "student", "password": "wrong"}, format="json")
    assert response.status_code == 401

@pytest.mark.django_db
def test_logout_blacklists_refresh(api_client, student):
    refresh = RefreshToken.for_user(student)
    api_client.force_authenticate(student)
    response = api_client.post("/api/v1/auth/logout", {"refresh": str(refresh)}, format="json")
    assert response.status_code == 200
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
    assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()

@pytest.mark.django_db
def test_me_requires_authentication(api_client):
    assert api_client.get("/api/v1/auth/me").status_code == 401

@pytest.mark.django_db
def test_health_is_public(api_client):
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.data["data"]["database"] == "ok"
