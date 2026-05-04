from sqlalchemy.orm import Session

from app.db.models import ChatSession
from app.schemas.chat import ChatRequest
from app.services.conversation_context_service import (
    infer_request_context,
    merge_conversation_context,
)


def test_infer_request_context_from_plain_text() -> None:
    request = infer_request_context(
        "It is a fire-rated hospital corridor egress door in Texas ZIP 77002."
    )

    assert request.building is not None
    assert request.building.building_type == "hospital"
    assert request.building.application == "hospital corridor"
    assert request.building.is_egress_path is True
    assert request.building.fire_rating_required is True
    assert request.location is not None
    assert request.location.state == "TX"
    assert request.location.zip_code == "77002"


def test_merge_conversation_context_uses_saved_session(db_session: Session) -> None:
    db_session.add(
        ChatSession(
            id="session-ctx",
            building_type="hospital",
            application="egress door",
            state="TX",
            zip_code="77002",
            is_egress_path=True,
        )
    )
    db_session.commit()

    request = ChatRequest(
        session_id="session-ctx",
        message="It is fire-rated.",
    )

    merged_request = merge_conversation_context(db_session, request)

    assert merged_request.building is not None
    assert merged_request.building.building_type == "hospital"
    assert merged_request.building.application == "egress door"
    assert merged_request.building.is_egress_path is True
    assert merged_request.building.fire_rating_required is True
    assert merged_request.location is not None
    assert merged_request.location.state == "TX"
    assert merged_request.location.zip_code == "77002"
