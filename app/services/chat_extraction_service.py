from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.schemas.chat import ChatRequest
from app.services.lead_service import extract_email, extract_phone
from app.services.llm_service import ALLOW_LLM_DURING_TESTS_ENV
from app.services.project_facts_service import extract_project_facts


PROJECT_CONTEXT_FIELDS = {
    "building_type",
    "application",
    "state",
    "zip_code",
    "city",
    "is_new_construction",
    "is_egress_path",
    "fire_rating_required",
    "fire_rating_minutes",
    "accessibility_required",
    "material_preference",
    "traffic",
    "wall_or_barrier",
    "hardware_type",
}


@dataclass(frozen=True)
class ChatExtraction:
    email: str | None = None
    phone: str | None = None
    name: str | None = None
    wants_follow_up: bool = False
    project_notes: str | None = None
    project_context: dict[str, Any] = field(default_factory=dict)


def _can_use_openai_for_extraction() -> bool:
    if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv(ALLOW_LLM_DURING_TESTS_ENV):
        return False

    return bool(settings.openai_api_key)


def _clean_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _clean_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _clean_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _clean_project_context(raw_context: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for field_name in PROJECT_CONTEXT_FIELDS:
        value = raw_context.get(field_name)
        if field_name in {
            "is_new_construction",
            "is_egress_path",
            "fire_rating_required",
            "accessibility_required",
        }:
            cleaned_value = _clean_bool(value)
        elif field_name == "fire_rating_minutes":
            cleaned_value = _clean_int(value)
        else:
            cleaned_value = _clean_string(value)

        if cleaned_value is not None:
            cleaned[field_name] = cleaned_value

    return cleaned


def _name_from_text(text: str) -> str | None:
    match = re.search(
        r"\b(?:my name is|i am|i'm|this is)\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,2})(?=\s+(?:and|email|phone)|[.,]|$)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _wants_follow_up(text: str) -> bool:
    normalized_text = text.lower()
    return any(
        phrase in normalized_text
        for phrase in [
            "call me",
            "contact me",
            "email me",
            "follow up",
            "quote",
            "pricing",
            "proposal",
            "send me",
        ]
    )


def _fallback_extract(messages: list[str]) -> ChatExtraction:
    text = "\n".join(messages)
    facts = extract_project_facts(ChatRequest(message=text))
    project_context = {
        "building_type": facts.building_type,
        "application": facts.application,
        "state": facts.state,
        "zip_code": facts.zip_code,
        "city": facts.city,
        "is_new_construction": facts.new_vs_existing,
        "is_egress_path": facts.is_egress_path,
        "fire_rating_required": facts.rating_required,
        "fire_rating_minutes": facts.rating_minutes,
        "accessibility_required": facts.accessibility_required,
        "material_preference": facts.material_preference,
        "traffic": facts.traffic,
        "wall_or_barrier": facts.wall_or_barrier,
        "hardware_type": facts.hardware_type,
    }

    return ChatExtraction(
        email=extract_email(text),
        phone=extract_phone(text),
        name=_name_from_text(text),
        wants_follow_up=_wants_follow_up(text),
        project_notes=text[-2000:] if text.strip() else None,
        project_context=_clean_project_context(project_context),
    )


def _extract_with_openai(messages: list[str]) -> ChatExtraction | None:
    if not _can_use_openai_for_extraction():
        return None

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = {
        "task": (
            "Extract lead and commercial door project facts from the chat. "
            "Use only facts stated by the user or clearly implied by their chat. "
            "Return null for unknown fields. Do not invent contact details."
        ),
        "schema": {
            "email": "string|null",
            "phone": "string|null",
            "name": "string|null",
            "wants_follow_up": "boolean",
            "project_notes": "short factual summary string|null",
            "project_context": {field_name: "value|null" for field_name in sorted(PROJECT_CONTEXT_FIELDS)},
        },
        "messages": messages[-12:],
    }

    try:
        completion = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured CRM/project data as strict JSON.",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_completion_tokens=650,
        )
    except Exception:
        return None

    content = completion.choices[0].message.content
    if not content:
        return None

    try:
        raw = json.loads(content)
    except json.JSONDecodeError:
        return None

    raw_context = raw.get("project_context") if isinstance(raw.get("project_context"), dict) else {}
    return ChatExtraction(
        email=_clean_string(raw.get("email")),
        phone=_clean_string(raw.get("phone")),
        name=_clean_string(raw.get("name")),
        wants_follow_up=bool(raw.get("wants_follow_up")),
        project_notes=_clean_string(raw.get("project_notes")),
        project_context=_clean_project_context(raw_context),
    )


def extract_chat_details(messages: list[str]) -> ChatExtraction:
    llm_extraction = _extract_with_openai(messages)
    fallback_extraction = _fallback_extract(messages)

    if llm_extraction is None:
        return fallback_extraction

    merged_context = {
        **fallback_extraction.project_context,
        **llm_extraction.project_context,
    }
    return ChatExtraction(
        email=llm_extraction.email or fallback_extraction.email,
        phone=llm_extraction.phone or fallback_extraction.phone,
        name=llm_extraction.name or fallback_extraction.name,
        wants_follow_up=llm_extraction.wants_follow_up or fallback_extraction.wants_follow_up,
        project_notes=llm_extraction.project_notes or fallback_extraction.project_notes,
        project_context=merged_context,
    )
