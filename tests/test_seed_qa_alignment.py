from app.schemas.chat import ChatRequest
from app.services.chat_service import build_chat_response


def test_seed_qa_examples_are_retrieval_context_not_exact_control_flags() -> None:
    response = build_chat_response(
        ChatRequest(message="What code applies to a school entrance in my state?")
    )

    assert response.intent == "code"
    assert response.should_capture_lead is False
    assert response.human_review_recommended is True
    assert "Dataset guidance:" in response.answer


def test_related_reworded_question_uses_dataset_without_exact_seed_match() -> None:
    response = build_chat_response(
        ChatRequest(message="Which rules should I check for a school main entry door?")
    )

    assert response.intent != "out_of_scope"
    assert response.knowledge_references
    assert "Dataset guidance:" in response.answer
