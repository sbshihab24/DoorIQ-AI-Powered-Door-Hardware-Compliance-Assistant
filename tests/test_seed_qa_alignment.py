from app.schemas.chat import ChatRequest
from app.services.chat_service import build_chat_response
from app.services.conversation_context_service import infer_request_context
from app.services.data_loader import load_processed_json
from app.services.intent_service import normalize_intent


def _expected_intents(primary_intent: str) -> list[str]:
    return [
        normalize_intent(intent.strip())
        for intent in primary_intent.split(";")
        if intent.strip()
    ]


def test_seed_qa_questions_use_expected_intent_lead_and_escalation_flags() -> None:
    for seed_qa in load_processed_json("seed_qa.json"):
        request = infer_request_context(seed_qa["user_question"])
        response = build_chat_response(request)

        assert normalize_intent(response.intent or "") in _expected_intents(
            seed_qa["primary_intent"]
        ), seed_qa["id"]
        assert response.should_capture_lead is seed_qa["need_email_phone"], seed_qa["id"]
        assert response.human_review_recommended is seed_qa["escalate_to_human"], seed_qa["id"]


def test_seed_qa_flags_apply_to_plain_chat_request() -> None:
    response = build_chat_response(
        ChatRequest(message="What code applies to a school entrance in my state?")
    )

    assert normalize_intent(response.intent or "") == "applicable_code_lookup"
    assert response.should_capture_lead is True
    assert response.human_review_recommended is False
