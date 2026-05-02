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

    assert "Product matching" in answer
    assert "KD Masonry Frame" in answer
    assert "fire rating" in answer
    assert "Masonry Frame Seed Case" in answer


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

    assert "Exact code guidance needs jurisdiction context" in answer
    assert "starter dataset" in answer
    assert "state, zip code" in answer
