from __future__ import annotations

import re
from functools import lru_cache
from app.schemas.code import CodeDocument
from app.services.data_loader import load_processed_json


INTENT_ALIASES = {
    "access_control": "maglock_analysis",
    "accessibility": "accessibility_analysis",
    "code": "applicable_code_lookup",
    "egress": "egress_analysis",
    "fire_rating": "fire_rating_analysis",
    "hardware": "hardware_allowance",
}


INTENT_CODE_TERMS = {
    "applicable_code_lookup": {"adoption", "amendments", "jurisdiction", "state", "city", "county", "local"},
    "code_section_navigation": {"code", "section", "adopted", "edition", "amendments"},
    "egress_analysis": {"egress", "exit", "panic", "locking", "swing", "life safety"},
    "fire_rating_analysis": {"fire", "rated", "label", "closing", "latching", "nfpa 80"},
    "accessibility_analysis": {"accessible", "accessibility", "ada", "clear", "operator", "maneuvering"},
    "automatic_operator_recommendation": {"automatic", "operator", "accessible", "ada", "entrances"},
    "maglock_analysis": {"locking", "egress", "fire", "life safety", "panic"},
    "hardware_allowance": {"hardware", "grade", "operation", "egress", "fire", "locking"},
    "sliding_door_analysis": {"egress", "accessible", "swing", "entrances"},
    "delayed_egress_analysis": {"egress", "locking", "life safety", "healthcare"},
    "door_type_recommendation": {"egress", "fire", "accessible", "amendments"},
    "product_match": {"hardware", "grade", "fire", "accessible"},
}


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2
    }


@lru_cache
def get_code_reference_catalog() -> list[CodeDocument]:
    references = []
    for index, item in enumerate(load_processed_json("code_framework.json"), start=1):
        title = str(item.get("source_or_code_family", f"Code source {index}"))
        covers = str(item.get("covers", "")).strip()
        typical_questions = [
            str(question)
            for question in item.get("typical_questions", [])
            if str(question).strip()
        ]
        source_type = str(item.get("type", "")).strip()
        tags = sorted(
            _tokenize(" ".join([title, covers, source_type, *typical_questions]))
        )
        references.append(
            CodeDocument(
                id=f"code-framework-{index:03d}",
                title=title,
                content=covers,
                section=source_type or None,
                url=item.get("source_url"),
                tags=tags,
            )
        )

    return references


def find_code_references(intent: str, state: str | None = None) -> list[CodeDocument]:
    intent = INTENT_ALIASES.get(intent, intent)
    intent_terms = INTENT_CODE_TERMS.get(intent, set()) | _tokenize(intent)
    scored_matches: list[tuple[int, CodeDocument]] = []

    for code_reference in get_code_reference_catalog():
        searchable_tokens = set(code_reference.tags) | _tokenize(
            " ".join(
                [
                    code_reference.title,
                    code_reference.content,
                    code_reference.section or "",
                ]
            )
        )
        score = len(searchable_tokens & intent_terms)
        if score:
            scored_matches.append((score, code_reference))

    scored_matches.sort(key=lambda item: (-item[0], item[1].title))
    matches = [reference for _, reference in scored_matches[:3]]

    if state:
        matches.insert(
            0,
            CodeDocument(
                id=f"state-{state.lower()}-review",
                title=f"{state.upper()} Local Code Review",
                content="Use the dataset code-framework jurisdiction sources to verify state adoption and city or county amendments for this opening.",
                state=state.upper(),
                section="local review",
                url="https://codes.iccsafe.org/codes/united-states",
                tags=["local", "code", "jurisdiction"],
            ),
        )

    return matches
