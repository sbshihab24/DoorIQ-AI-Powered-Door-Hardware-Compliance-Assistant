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
    assert response.code_references
    assert response.code_references[0].summary
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


def test_build_chat_response_includes_zip_code_verification_packet() -> None:
    request = ChatRequest(
        message="Can I use a maglock on this egress door?",
        building={"application": "egress door", "is_egress_path": True},
        location={"state": "TX", "zip_code": "77002"},
    )

    response = build_chat_response(request)

    assert response.code_references[0].title == "TX / 77002 Code Verification Packet"
    assert response.code_references[0].url == "https://codes.iccsafe.org/"
    assert "not as final legal text" in response.code_references[0].summary
    assert "last_verified_utc" in response.code_references[0].summary


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
    masonry_frame = next(
        product
        for product in response.recommended_products
        if product.name == "KD Masonry Frame"
    )
    assert masonry_frame.starting_price_usd == 160
    assert masonry_frame.fire_rating == "Up to 3 hours"
    assert any("Matches the requested product category" in reason for reason in product_reasons)
    assert response.missing_information == [
        "hardware_type",
        "finish",
        "rating",
        "brand_preference",
    ]


def test_build_chat_response_handles_office_door_request_as_door_recommendation() -> None:
    response = build_chat_response(
        ChatRequest(
            message="I need a door for my office",
            building={"building_type": "office", "application": "office"},
        )
    )

    assert response.intent == "door_type_recommendation"
    assert "Dataset-grounded starting point for an office" in response.answer
    assert "Product Recommendation Conditions" in [
        reference.title for reference in response.knowledge_references
    ]
    assert "Seed QA: What doors and hardware are required for a hospital main entrance" not in [
        reference.title for reference in response.knowledge_references
    ]
    assert "Hospital Main Entrance Seed Case" not in [
        reference.title for reference in response.knowledge_references
    ]
    assert "Seed QA: Can I use a magnetic lock on this type of door" not in [
        reference.title for reference in response.knowledge_references
    ]
    assert "Commercial Wood Door with Glass" in [
        product.name for product in response.recommended_products
    ]


def test_build_chat_response_does_not_recommend_products_for_generic_kitchen_door() -> None:
    response = build_chat_response(ChatRequest(message="i need a door for my kitchen"))

    assert response.intent == "door_type_recommendation"
    assert response.recommended_products == []
    assert "Product Recommendation Conditions" in [
        reference.title for reference in response.knowledge_references
    ]


def test_build_chat_response_handles_automatic_operator_case() -> None:
    request = ChatRequest(
        message="Do I need an automatic operator on a hospital entrance door?",
        building={"building_type": "hospital", "application": "hospital entrance"},
        location={"state": "TX"},
    )

    response = build_chat_response(request)

    assert response.intent == "automatic_operator_recommendation"
    assert any(
        "low-energy" in option and "full-power" in option
        for option in response.allowed_options
    )
    assert "Automatic Door Operator" not in [
        product.name for product in response.recommended_products
    ]
    assert response.missing_information == [
        "accessible_route",
        "user_population",
        "power_access",
    ]


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

    assert response.confidence == "low"
    assert response.human_review_recommended is True


def test_build_chat_response_handles_greeting_without_door_pipeline() -> None:
    response = build_chat_response(ChatRequest(message="Hi"))

    assert response.intent == "greeting"
    assert response.answer == "Hi, how can I help you?"
    assert response.missing_information == []
    assert response.recommended_products == []
    assert response.should_capture_lead is False
    assert response.human_review_recommended is False


def test_build_chat_response_redirects_unrelated_questions() -> None:
    response = build_chat_response(ChatRequest(message="What is the capital of France?"))

    assert response.intent == "out_of_scope"
    assert "commercial doors" in response.answer
    assert response.missing_information == []
    assert response.recommended_products == []
    assert response.should_capture_lead is False
