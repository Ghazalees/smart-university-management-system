from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_documented_answer_contains_source():
    response = client.post(
        "/v1/answer",
        json={
            "question": "How can I register for a course?",
            "prompt": "prompt",
            "documents": [
                {
                    "id": 1,
                    "title": "Registration Guide",
                    "content": "Students register using the university portal.",
                }
            ],
        },
    )
    assert response.status_code == 200
    assert "Registration Guide" in response.json()["answer"]
    assert response.json()["confidence"] >= 0.55


def test_no_document_is_low_confidence():
    response = client.post(
        "/v1/answer",
        json={"question": "Unknown policy?", "prompt": "prompt", "documents": []},
    )
    assert response.status_code == 200
    assert response.json()["confidence"] < 0.55


def test_request_analysis():
    response = client.post(
        "/v1/analyze", json={"text": "My tuition payment failed before the deadline"}
    )
    assert response.status_code == 200
    assert response.json()["category"] == "finance"
