from app.schemas.chat import (
    ChatRequest,
    CodeReference,
    KnowledgeReference,
    RecommendedProduct,
)
from app.services.answer_service import build_answer


def test_build_answer_uses_structured_context_for_product_match() -> None:
    answer = build_answer(
        request=ChatRequest(message="What door frame should I use for a masonry opening?"),
        intent="product_match",
        requirements=["Confirm wall type, interior or exterior use, and required rating."],
        allowed_options=["KD masonry frame or welded frame depending on wall condition."],
        risky_or_not_allowed=["Do not finalize rating without confirming the wall/barrier requirement."],
        recommended_products=[
            RecommendedProduct(
                name="KD Masonry Frame",
                category="frame",
                reason="Matches the application: masonry opening.",
                starting_price_usd=160,
                fire_rating="Up to 3 hours",
            )
        ],
        code_references=[],
        knowledge_references=[
            KnowledgeReference(
                title="Masonry Frame Seed Case",
                source="united_doors_ai_training_dataset.pdf",
                summary="Compare KD masonry frames and welded frames.",
            )
        ],
        missing_information=["fire_rating"],
    )

    assert "Dataset guidance:" in answer
    assert "KD Masonry Frame" in answer
    assert "from $160" in answer
    assert "rating: Up to 3 hours" in answer
    assert "Fire rating" in answer
    assert "united_doors_ai_training_dataset.pdf / Masonry Frame Seed Case" in answer
    assert "What I need next:" in answer


def test_build_answer_keeps_local_code_caveat() -> None:
    answer = build_answer(
        request=ChatRequest(message="What code applies here?"),
        intent="applicable_code_lookup",
        requirements=["Collect state, ZIP, building type, and whether the work is new or existing."],
        allowed_options=[],
        risky_or_not_allowed=["Treating the starter dataset as the final official jurisdictional code source."],
        recommended_products=[],
        code_references=[
            CodeReference(
                title="ICC Codes by Location",
                section="jurisdiction lookup",
                summary="Resolve adopted code editions and amendments.",
            )
        ],
        knowledge_references=[
            KnowledgeReference(
                title="Dataset Implementation Note",
                source="united_doors_ai_training_dataset.pdf",
                summary="Starter dataset caveat.",
            )
        ],
        missing_information=["state", "zip_code"],
    )

    assert "Dataset guidance:" in answer
    assert "Starter dataset" in answer
    assert "Resolve adopted code editions and amendments" in answer
    assert "What state is the project in?" in answer
    assert "What ZIP code should I use" in answer


def test_build_answer_can_use_llm_writer(monkeypatch) -> None:
    captured_context = {}

    def fake_generate_llm_answer(*, context, fallback_answer):
        captured_context.update(context)
        return f"LLM: {fallback_answer}"

    monkeypatch.setattr(
        "app.services.answer_service.generate_llm_answer",
        fake_generate_llm_answer,
    )

    answer = build_answer(
        request=ChatRequest(message="Can I use a maglock?"),
        intent="maglock_analysis",
        requirements=["Confirm egress role."],
        allowed_options=["Use listed access control hardware where allowed."],
        risky_or_not_allowed=[],
        recommended_products=[],
        code_references=[],
        knowledge_references=[],
        missing_information=["jurisdiction"],
    )

    assert answer.startswith("LLM: Dataset-grounded starting point")
    assert "matching dataset record" in answer
    assert captured_context["intent"] == "maglock_analysis"
    assert captured_context["missing_information"] == ["jurisdiction"]
