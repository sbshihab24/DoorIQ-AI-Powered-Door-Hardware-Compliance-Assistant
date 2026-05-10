from dataclasses import dataclass
import re

from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.services.data_loader import load_processed_json
from app.services.embedding_service import cosine_similarity, embed_text


GENERIC_RETRIEVAL_TOKENS = {
    "and",
    "door",
    "doors",
    "for",
    "need",
    "needs",
    "recommendation",
    "type",
    "what",
    "with",
}


@dataclass(frozen=True)
class KnowledgeSnippet:
    title: str
    source: str
    content: str
    tags: list[str]


def get_knowledge_base() -> list[KnowledgeSnippet]:
    return [
        KnowledgeSnippet(**snippet_data)
        for snippet_data in load_processed_json("knowledge_snippets.json")
    ]


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in GENERIC_RETRIEVAL_TOKENS
    }


def find_relevant_knowledge(query: str, intent: str | None = None, limit: int = 3) -> list[KnowledgeSnippet]:
    query_tokens = _tokenize(query)
    intent_tokens = _tokenize(intent or "")
    scored_snippets: list[tuple[int, KnowledgeSnippet]] = []

    for snippet in get_knowledge_base():
        searchable_text = " ".join(
            [snippet.title, snippet.content, " ".join(snippet.tags)]
        )
        snippet_tokens = _tokenize(searchable_text)
        score = len(query_tokens & snippet_tokens) + (2 * len(intent_tokens & snippet_tokens))

        if intent and intent in snippet.tags:
            score += 4

        if score > 0:
            scored_snippets.append((score, snippet))

    scored_snippets.sort(key=lambda item: item[0], reverse=True)
    snippets = [snippet for _, snippet in scored_snippets]
    snippets = _filter_context_mismatched_seed_snippets(snippets, query_tokens, intent)

    if intent == "applicable_code_lookup":
        required_titles = [
            "Dataset Implementation Note",
            "ZIP-Based Local Code Resolution",
        ]
        snippets = _pin_titles(snippets, required_titles)

    if intent == "door_type_recommendation":
        required_titles = [
            "Product Recommendation Conditions",
        ]
        snippets = _pin_titles(snippets, required_titles)

    deduplicated_snippets = []
    seen_titles = set()
    for snippet in snippets:
        if snippet.title in seen_titles:
            continue
        seen_titles.add(snippet.title)
        deduplicated_snippets.append(snippet)

    return deduplicated_snippets[:limit]


def find_relevant_knowledge_from_db(
    db: Session,
    query: str,
    intent: str | None = None,
    limit: int = 3,
) -> list[KnowledgeSnippet]:
    query_tokens = _tokenize(query)
    query_embedding = embed_text(" ".join(part for part in [query, intent or ""] if part))
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.embedding.isnot(None))
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
            .all()
        )
        if chunks:
            snippets = [
                KnowledgeSnippet(
                    title=chunk.title,
                    source=chunk.source,
                    content=chunk.content,
                    tags=list(chunk.tags or []),
                )
                for chunk in chunks
            ]
            return _with_applicable_code_pins(snippets, limit, intent, query_tokens)

    chunks = db.query(DocumentChunk).all()
    scored_chunks: list[tuple[float, DocumentChunk]] = []

    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk.embedding)
        if intent and intent in (chunk.tags or []):
            score += 0.15

        if score > 0:
            scored_chunks.append((score, chunk))

    if not scored_chunks:
        return find_relevant_knowledge(query, intent, limit)

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    snippets = [
        KnowledgeSnippet(
            title=chunk.title,
            source=chunk.source,
            content=chunk.content,
            tags=list(chunk.tags or []),
        )
        for _, chunk in scored_chunks[:limit]
    ]

    return _with_applicable_code_pins(snippets, limit, intent, query_tokens)


def _with_applicable_code_pins(
    snippets: list[KnowledgeSnippet],
    limit: int,
    intent: str | None = None,
    query_tokens: set[str] | None = None,
) -> list[KnowledgeSnippet]:
    snippets = _filter_context_mismatched_seed_snippets(
        snippets,
        query_tokens or set(),
        intent,
    )
    if intent != "applicable_code_lookup":
        if intent == "door_type_recommendation":
            return _pin_titles(snippets, ["Product Recommendation Conditions"])[:limit]

        return snippets[:limit]

    return _pin_titles(
        snippets,
        ["Dataset Implementation Note", "ZIP-Based Local Code Resolution"],
    )[:limit]


def _pin_titles(snippets: list[KnowledgeSnippet], titles: list[str]) -> list[KnowledgeSnippet]:
    knowledge_base = get_knowledge_base()
    pinned_snippets = [
        snippet
        for title in titles
        for snippet in knowledge_base
        if snippet.title == title
    ]
    pinned_titles = {snippet.title for snippet in pinned_snippets}
    remaining_snippets = [
        snippet for snippet in snippets if snippet.title not in pinned_titles
    ]
    return pinned_snippets + remaining_snippets


def _filter_context_mismatched_seed_snippets(
    snippets: list[KnowledgeSnippet],
    query_tokens: set[str],
    intent: str | None,
) -> list[KnowledgeSnippet]:
    if not query_tokens:
        return snippets

    specific_context_tags = {"hospital", "school", "healthcare", "memory care"}
    filtered_snippets = []
    for snippet in snippets:
        snippet_tags = {tag.lower() for tag in snippet.tags}
        snippet_tag_tokens = set()
        for tag in snippet_tags:
            snippet_tag_tokens.update(_tokenize(tag))

        if (
            snippet_tags & specific_context_tags
            and not snippet_tags & query_tokens
            and not snippet_tag_tokens & query_tokens
        ):
            continue

        is_seed_snippet = snippet.title.startswith("Seed QA:") or snippet.title.endswith("Seed Case")
        if not is_seed_snippet:
            filtered_snippets.append(snippet)
            continue

        if intent and intent not in snippet_tags:
            continue

        if "general" in snippet_tags or snippet_tags & query_tokens or snippet_tag_tokens & query_tokens:
            filtered_snippets.append(snippet)

    return filtered_snippets
