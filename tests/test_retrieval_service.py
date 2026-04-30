from app.services.retrieval_service import find_relevant_knowledge


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
