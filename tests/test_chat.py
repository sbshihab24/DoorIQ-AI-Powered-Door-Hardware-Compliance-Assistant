from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_returns_placeholder_response() -> None:
    response = client.post("/chat", json={"message": "Do I need panic hardware?"})

    assert response.status_code == 200

    data = response.json()
    assert data["session_id"]
    assert data["answer"]
    assert data["confidence"] == "low"
    assert data["human_review_recommended"] is True
    assert data["missing_information"] == [
        "building_type",
        "application",
        "state",
        "zip_code",
    ]
