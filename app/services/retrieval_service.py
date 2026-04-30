from dataclasses import dataclass
import re

from app.services.data_loader import load_processed_json


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
    return [snippet for _, snippet in scored_snippets[:limit]]
