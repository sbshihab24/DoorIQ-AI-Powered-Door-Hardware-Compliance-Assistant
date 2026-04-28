from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_lead_capture_returns_placeholder_response() -> None:
    response = client.post(
        "/leads",
        json={
            "session_id": "session-123",
            "email": "brian@example.com",
            "phone": "555-0100",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data == {
        "id": 1,
        "session_id": "session-123",
        "email": "brian@example.com",
        "phone": "555-0100",
    }
