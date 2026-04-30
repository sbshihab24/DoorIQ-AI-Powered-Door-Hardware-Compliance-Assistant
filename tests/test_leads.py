from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import ChatSession, Lead
from app.main import app


client = TestClient(app)


def test_lead_capture_persists_record(db_session: Session) -> None:
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
    assert data["id"] == 1
    assert data["session_id"] == "session-123"
    assert data["email"] == "brian@example.com"
    assert data["phone"] == "555-0100"

    lead = db_session.get(Lead, data["id"])
    chat_session = db_session.get(ChatSession, "session-123")

    assert lead is not None
    assert lead.email == "brian@example.com"
    assert lead.phone == "555-0100"
    assert chat_session is not None
    assert chat_session.email == "brian@example.com"
    assert chat_session.phone == "555-0100"
