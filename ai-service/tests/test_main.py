from fastapi.testclient import TestClient

from api.main import app


def test_ai_service_health_check():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["status"] == "ok"
