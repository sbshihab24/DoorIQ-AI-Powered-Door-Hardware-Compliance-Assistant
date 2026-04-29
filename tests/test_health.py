from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_returns_app_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "DoorIQ Chatbot API",
        "app_env": "development",
    }
