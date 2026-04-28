from app.schemas.chat import ChatRequest
from app.services.chat_service import build_chat_response, get_missing_information


def test_get_missing_information_returns_only_missing_fields() -> None:
    request = ChatRequest(
        message="What hardware do I need?",
        building={"application": "egress door"},
        location={"state": "TX"},
    )

    assert get_missing_information(request) == ["building_type", "zip_code"]


def test_build_chat_response_includes_detected_intent() -> None:
    request = ChatRequest(message="Can I use a maglock?")

    response = build_chat_response(request)

    assert response.intent == "access_control"
