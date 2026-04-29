from app.schemas.chat import ChatRequest
from app.services.chat_service import (
    build_chat_response,
    get_answer_for_intent,
    get_missing_information,
)


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
    assert response.code_references[0].section == "access control"
    assert response.requirements
    assert response.allowed_options
    assert response.risky_or_not_allowed


def test_get_answer_for_egress_intent() -> None:
    answer = get_answer_for_intent("egress")

    assert "Egress door hardware" in answer


def test_get_answer_for_unknown_intent_uses_default() -> None:
    answer = get_answer_for_intent("general")

    assert "door and hardware recommendation" in answer


def test_build_chat_response_includes_local_review_when_state_is_known() -> None:
    request = ChatRequest(
        message="I need help choosing a door.",
        location={"state": "TX"},
    )

    response = build_chat_response(request)

    assert response.code_references[0].title == "TX Local Code Review"


def test_build_chat_response_flags_lead_capture_for_quote_request() -> None:
    request = ChatRequest(message="Can I get pricing for this egress hardware?")

    response = build_chat_response(request)

    assert response.should_capture_lead is True
