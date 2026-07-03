"""Verifies api behavior, authorization rules, validation, and regression scenarios."""

import os

from fastapi.testclient import TestClient

os.environ.setdefault("AI_SERVICE_API_KEY", "test-internal-key")

from api.main import app  # noqa: E402

client = TestClient(app)
HEADERS = {"X-Internal-API-Key": "test-internal-key"}


def test_health_is_public():
    assert client.get("/health").json()["status"] == "ok"


def test_answer_requires_internal_credentials():
    response = client.post(
        "/v1/answer",
        json={"question": "Question", "prompt": "Prompt", "documents": []},
    )
    assert response.status_code == 401


def test_invalid_internal_credentials_are_rejected():
    response = client.post(
        "/v1/analyze",
        headers={"X-Internal-API-Key": "wrong"},
        json={"text": "Analyze this request"},
    )
    assert response.status_code == 401


def test_documented_answer_contains_source():
    response = client.post(
        "/v1/answer",
        headers=HEADERS,
        json={
            "question": "How can I register for a course?",
            "prompt": "Answer only from the supplied university documents.",
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
        headers=HEADERS,
        json={"question": "Unknown policy?", "prompt": "prompt", "documents": []},
    )
    assert response.status_code == 200
    assert response.json()["confidence"] < 0.55


def test_request_size_validation():
    response = client.post(
        "/v1/analyze",
        headers=HEADERS,
        json={"text": "x" * 12001},
    )
    assert response.status_code == 422


def test_request_analysis():
    response = client.post(
        "/v1/analyze",
        headers=HEADERS,
        json={"text": "My tuition payment failed before the deadline"},
    )
    assert response.status_code == 200
    assert response.json()["category"] == "finance"


def test_local_answer_selects_relevant_passage_instead_of_document_opening():
    filler = "General university introduction. " * 120
    target = "Scholarship appeals are submitted in the awards portal within fourteen calendar days."
    response = client.post(
        "/v1/answer",
        headers=HEADERS,
        json={
            "question": "Where are scholarship appeals submitted and what is the deadline?",
            "prompt": "Answer only from the supplied university documents.",
            "documents": [
                {
                    "id": 7,
                    "title": "Student Handbook",
                    "content": f"{filler}\n\n{target}",
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert target in payload["answer"]
    assert "Student Handbook" in payload["answer"]
    assert payload["confidence"] >= 0.55
