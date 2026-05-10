from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_frontend_serves_chat_ui() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "DoorIQ" in response.text
    assert "Project details" in response.text
    assert "details-panel" not in response.text


def test_frontend_static_assets_load() -> None:
    script_response = client.get("/static/app.js")
    style_response = client.get("/static/styles.css")

    assert script_response.status_code == 200
    assert "fetch(\"/chat\"" in script_response.text
    assert "recommended_products" in script_response.text
    assert "appendTextWithLinks" in script_response.text
    assert style_response.status_code == 200
    assert ".chat-card" in style_response.text
    assert ".message a" in style_response.text
