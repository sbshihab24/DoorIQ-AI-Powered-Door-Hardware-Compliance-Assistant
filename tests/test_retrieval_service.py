from app.services.retrieval_service import (
    KnowledgeSnippet,
    _with_applicable_code_pins,
    find_relevant_knowledge,
)


def test_find_relevant_knowledge_for_masonry_frame() -> None:
    snippets = find_relevant_knowledge(
        "What door frame should I use for a masonry opening?",
        "product_match",
    )

    titles = [snippet.title for snippet in snippets]
    assert "Masonry Frame Seed Case" in titles


def test_find_relevant_knowledge_for_local_code_lookup() -> None:
    snippets = find_relevant_knowledge(
        "What code applies in my ZIP?",
        "applicable_code_lookup",
    )

    titles = [snippet.title for snippet in snippets]
    assert "ZIP-Based Local Code Resolution" in titles


def test_find_relevant_knowledge_for_door_recommendation_pins_conditions() -> None:
    snippets = find_relevant_knowledge(
        "I need a door for my office door_type_recommendation",
        "door_type_recommendation",
    )

    titles = [snippet.title for snippet in snippets]
    assert titles[0] == "Product Recommendation Conditions"


def test_find_relevant_knowledge_filters_mismatched_seed_context() -> None:
    snippets = find_relevant_knowledge(
        "I need a door for my office door_type_recommendation",
        "door_type_recommendation",
    )

    titles = [snippet.title for snippet in snippets]
    assert "Seed QA: What doors and hardware are required for a hospital main entrance" not in titles
    assert "Hospital Main Entrance Seed Case" not in titles
    assert "Seed QA: Can I use a magnetic lock on this type of door" not in titles


def test_find_relevant_knowledge_filters_mismatched_named_seed_case() -> None:
    snippets = find_relevant_knowledge(
        "i need a door for my kitchen door_type_recommendation",
        "door_type_recommendation",
    )

    titles = [snippet.title for snippet in snippets]
    assert titles == ["Product Recommendation Conditions"]


def test_db_knowledge_pin_filter_uses_query_context() -> None:
    snippets = [
        KnowledgeSnippet(
            title="Seed QA: What doors and hardware are required for a hospital main entrance",
            source="united_doors_ai_training_dataset.pdf",
            content="Hospital entrance seed case.",
            tags=["door_type_recommendation", "hospital", "main entrance"],
        )
    ]

    filtered = _with_applicable_code_pins(
        snippets,
        limit=3,
        intent="door_type_recommendation",
        query_tokens={"need", "door", "kitchen"},
    )

    titles = [snippet.title for snippet in filtered]
    assert titles == ["Product Recommendation Conditions"]
