from app.schemas.chat import ChatRequest
from app.services.chat_service import build_chat_response


def test_code_seed_answer_mentions_jurisdiction_stack_and_source_urls() -> None:
    response = build_chat_response(
        ChatRequest(message="What code applies to a school entrance in my state?")
    )

    assert "jurisdiction stack" in response.answer
    assert "source URLs" in response.answer


def test_operator_seed_answer_compares_operator_paths() -> None:
    response = build_chat_response(
        ChatRequest(message="Do I need an automatic operator on a hospital entrance door?")
    )

    assert "manual, low-energy, and full-power" in response.answer


def test_delayed_egress_seed_answer_mentions_ahj_review() -> None:
    response = build_chat_response(
        ChatRequest(message="Can I use delayed egress at a memory care unit?")
    )

    assert "AHJ-review" in response.answer


def test_product_seed_answer_mentions_matched_product_list() -> None:
    response = build_chat_response(
        ChatRequest(message="What products on your site fit a 90-minute corridor pair?")
    )

    assert "matched product list" in response.answer
    assert response.recommended_products


def test_meta_seed_answer_lists_exact_answer_inputs() -> None:
    response = build_chat_response(
        ChatRequest(message="What information do you need before giving an exact answer?")
    )

    assert "state/ZIP" in response.answer
    assert "building type" in response.answer
    assert "access-control intent" in response.answer


def test_electrified_rated_opening_seed_answer_mentions_listed_components() -> None:
    response = build_chat_response(
        ChatRequest(message="Can I electrify this fire-rated opening?")
    )

    assert "listed components" in response.answer
    assert "labeled assembly" in response.answer
