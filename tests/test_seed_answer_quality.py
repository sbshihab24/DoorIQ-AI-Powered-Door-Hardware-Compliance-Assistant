from app.schemas.chat import ChatRequest
from app.services.chat_service import build_chat_response


def test_code_seed_answer_mentions_jurisdiction_stack_and_source_urls() -> None:
    response = build_chat_response(
        ChatRequest(message="What code applies to a school entrance in my state?")
    )

    assert "Dataset guidance:" in response.answer
    assert "local-code precision requires resolving ZIP to city, county, and state" in response.answer


def test_code_answer_mentions_resolved_zip_verification_packet() -> None:
    response = build_chat_response(
        ChatRequest(
            message="What code applies to a school entrance in my state?",
            building={"building_type": "school", "application": "main entrance"},
            location={"state": "TX", "zip_code": "77002"},
        )
    )

    assert "TX / 77002 Code Verification Packet" in response.answer
    assert response.code_references[0].url == "https://codes.iccsafe.org/"


def test_operator_seed_answer_compares_operator_paths() -> None:
    response = build_chat_response(
        ChatRequest(message="Do I need an automatic operator on a hospital entrance door?")
    )

    assert "automatic-door preference" in response.answer


def test_delayed_egress_seed_answer_mentions_ahj_review() -> None:
    response = build_chat_response(
        ChatRequest(message="Can I use delayed egress at a memory care unit?")
    )

    assert "AHJ review" in response.answer


def test_product_seed_answer_mentions_matched_product_list() -> None:
    response = build_chat_response(
        ChatRequest(message="What products on your site fit a 90-minute corridor pair?")
    )

    assert "Recommended output: Matched product list" in response.answer
    assert response.recommended_products


def test_meta_seed_answer_lists_exact_answer_inputs() -> None:
    response = build_chat_response(
        ChatRequest(message="What information do you need before giving an exact answer?")
    )

    assert response.intent == "general"
    assert "What I need next:" in response.answer
    assert "What type of building is it?" in response.answer


def test_electrified_rated_opening_seed_answer_mentions_listed_components() -> None:
    response = build_chat_response(
        ChatRequest(message="Can I electrify this fire-rated opening?")
    )

    assert "listed components" in response.answer
    assert "Recommended output: Conditional allow + listed components only" in response.answer
