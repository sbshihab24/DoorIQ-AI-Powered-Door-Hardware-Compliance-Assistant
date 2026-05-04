from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.services.data_loader import load_processed_json


def normalize_seed_question(question: str) -> str:
    normalized = question.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


@lru_cache
def get_seed_qa_by_question() -> dict[str, dict[str, Any]]:
    return {
        normalize_seed_question(item["user_question"]): item
        for item in load_processed_json("seed_qa.json")
        if isinstance(item.get("user_question"), str)
    }


def find_seed_qa_for_question(question: str) -> dict[str, Any] | None:
    return get_seed_qa_by_question().get(normalize_seed_question(question))


def get_primary_seed_intent(seed_qa: dict[str, Any]) -> str:
    primary_intent = str(seed_qa.get("primary_intent", "general"))
    return primary_intent.split(";")[0].strip() or "general"
