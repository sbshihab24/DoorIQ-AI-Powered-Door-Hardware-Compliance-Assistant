from dataclasses import dataclass
import re

from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.services.data_loader import load_processed_json
from app.services.embedding_service import cosine_similarity, embed_text


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
        if len(token) > 2
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

    if intent == "applicable_code_lookup":
        required_titles = [
            "Dataset Implementation Note",
            "ZIP-Based Local Code Resolution",
        ]
        pinned_snippets = [
            snippet
            for title in required_titles
            for snippet in get_knowledge_base()
            if snippet.title == title and snippet not in snippets[:limit]
        ]
        snippets = pinned_snippets + snippets

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
            return _with_applicable_code_pins(snippets, limit, intent)

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

    return _with_applicable_code_pins(snippets, limit, intent)


def _with_applicable_code_pins(
    snippets: list[KnowledgeSnippet],
    limit: int,
    intent: str | None = None,
) -> list[KnowledgeSnippet]:
    if intent != "applicable_code_lookup":
        return snippets[:limit]

    pinned_titles = {
        "Dataset Implementation Note",
        "ZIP-Based Local Code Resolution",
    }
    existing_titles = {snippet.title for snippet in snippets}
    fallback_pins = [
        snippet
        for snippet in get_knowledge_base()
        if snippet.title in pinned_titles and snippet.title not in existing_titles
    ]
    return (fallback_pins + snippets)[:limit]
