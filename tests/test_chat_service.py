from app.schemas.chat import ChatRequest
from app.services.chat_service import (
    build_chat_response,
    get_answer_for_intent,
    get_missing_information,
    get_response_confidence,
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


def test_build_chat_response_handles_dataset_product_match_case() -> None:
    request = ChatRequest(
        message="What door frame should I use for a masonry opening?",
        building={"building_type": "warehouse", "application": "masonry opening frame"},
        location={"state": "TX", "zip_code": "77002"},
    )

    response = build_chat_response(request)

    product_names = [product.name for product in response.recommended_products]
    product_reasons = [product.reason for product in response.recommended_products]
    assert response.intent == "product_match"
    assert "KD Masonry Frame" in product_names
    assert any("Matches the requested product category" in reason for reason in product_reasons)
    assert response.missing_information == []


def test_build_chat_response_handles_automatic_operator_case() -> None:
    request = ChatRequest(
        message="Do I need an automatic operator on a hospital entrance door?",
        building={"building_type": "hospital", "application": "hospital entrance"},
        location={"state": "TX"},
    )

    response = build_chat_response(request)

    assert response.intent == "automatic_operator_recommendation"
    assert "Automatic Door Operator" in [
        product.name for product in response.recommended_products
    ]
    assert "zip_code" in response.missing_information


def test_build_chat_response_includes_knowledge_references() -> None:
    request = ChatRequest(
        message="Can I use a maglock on this egress door?",
        building={"application": "egress door"},
    )

    response = build_chat_response(request)

    titles = [reference.title for reference in response.knowledge_references]
    assert "Maglock Seed Case" in titles


def test_get_response_confidence_is_low_when_information_is_missing() -> None:
    confidence = get_response_confidence(
        missing_information=["zip_code"],
        recommended_products=[],
        code_references=[],
        knowledge_references=[],
    )

    assert confidence == "low"


def test_build_chat_response_uses_medium_confidence_for_complete_context() -> None:
    request = ChatRequest(
        message="What door frame should I use for a masonry opening?",
        building={"building_type": "warehouse", "application": "masonry opening frame"},
        location={"state": "TX", "zip_code": "77002"},
    )

    response = build_chat_response(request)

    assert response.confidence == "medium"
    assert response.human_review_recommended is False
