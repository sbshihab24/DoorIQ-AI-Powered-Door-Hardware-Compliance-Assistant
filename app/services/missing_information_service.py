from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.schemas.chat import ChatRequest
from app.services.data_loader import load_processed_json
from app.services.intent_service import normalize_intent
from app.services.project_facts_service import ProjectFacts, extract_project_facts


def normalize_missing_field(value: str) -> str:
    if value.strip().lower() == "zip":
        return "zip_code"

    value = value.strip().lower()
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value)
    return value.strip("_").lower()


@lru_cache
def get_required_entities_by_intent() -> dict[str, list[str]]:
    intents = load_processed_json("intents.json")
    required_entities_by_intent = {}

    for intent_data in intents:
        intent = intent_data.get("intent")
        required_entities = intent_data.get("required_entities", [])
        if not isinstance(intent, str) or not isinstance(required_entities, list):
            continue

        required_entities_by_intent[intent] = [
            str(entity)
            for entity in required_entities
            if str(entity).strip()
        ]

    return required_entities_by_intent


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _has_rating_minutes(text: str) -> bool:
    return bool(re.search(r"\b(20|45|60|90)\s*(?:min|mins|minute|minutes)?\b", text))


def _has_wall_or_barrier_context(text: str) -> bool:
    if _has_any(text, ["masonry", "drywall", "stud", "wall type"]):
        return True

    return bool(
        re.search(
            r"\b(?:[a-z0-9-]+\s+){0,3}(?:wall|barrier|partition|enclosure)\b",
            text,
        )
    )


def _has_project_application(request: ChatRequest) -> bool:
    return bool(request.building and request.building.application)


def _has_entity(request: ChatRequest, entity: str, facts: ProjectFacts) -> bool:
    normalized_entity = normalize_missing_field(entity)
    text = facts.text
    building = request.building
    location = request.location

    entity_checks: dict[str, Any] = {
        "state": lambda: bool(facts.state),
        "city": lambda: bool(facts.city),
        "zip": lambda: bool(facts.zip_code),
        "zip_code": lambda: bool(facts.zip_code),
        "building_type": lambda: bool(facts.building_type),
        "application": lambda: bool(facts.application),
        "new_vs_existing": lambda: bool(
            building and building.is_new_construction is not None
        )
        or facts.new_vs_existing is not None,
        "door_type": lambda: bool(facts.application)
        or _has_any(text, ["door", "frame", "opening"]),
        "hardware_type": lambda: bool(facts.hardware_type),
        "finish": lambda: _has_any(text, ["finish", "paint", "painted", "stain", "primed", "galvanized"]),
        "rating": lambda: bool(building and building.fire_rating_required is not None)
        or facts.rating_required is not None
        or facts.rating_minutes is not None,
        "brand_preference": lambda: _has_any(text, ["tell", "schlage", "dormakaba", "assa", "accentra"]),
        "location": lambda: bool(facts.application or facts.location_type or facts.city or facts.state or facts.zip_code),
        "interior_exterior": lambda: bool(facts.location_type),
        "traffic": lambda: bool(facts.traffic),
        "material_preference": lambda: bool(facts.material_preference),
        "occupancy": lambda: bool(facts.building_type and facts.building_type != "general"),
        "occupant_load": lambda: facts.occupant_load_known,
        "path_of_egress": lambda: bool(building and building.is_egress_path is not None)
        or facts.is_egress_path is not None,
        "egress_path": lambda: bool(building and building.is_egress_path is not None)
        or facts.is_egress_path is not None,
        "lock_type": lambda: _has_any(
            text,
            [
                "maglock",
                "lock",
                "lockset",
                "latchset",
                "electric strike",
                "access control",
                "panic",
                "panic bar",
                "panic hardware",
                "push bar",
                "exit device",
                "rim exit",
                "rim device",
            ],
        ),
        "wall_type": lambda: bool(facts.wall_or_barrier),
        "barrier_type": lambda: bool(facts.wall_or_barrier)
        or _has_any(text, ["corridor", "stair"]),
        "opening_location": lambda: bool(facts.application),
        "accessible_route": lambda: bool(building and building.accessibility_required is not None)
        or facts.accessibility_required is not None,
        "entrance_type": lambda: _has_any(text, ["entrance", "public entrance", "main entrance"]),
        "user_controls": lambda: _has_any(text, ["lever", "operator", "controls", "push button", "actuator"]),
        "thresholds": lambda: _has_any(text, ["threshold"]),
        "access_control": lambda: facts.access_control is not None,
        "access_control_intent": lambda: facts.access_control is not None,
        "patient_security_use_case": lambda: _has_any(text, ["memory care", "patient", "secured", "security"]),
        "sprinkler_alarm_status": lambda: _has_any(text, ["sprinkler", "alarm", "fire alarm"]),
        "egress_function": lambda: _has_any(text, ["egress", "exit", "breakout"]),
        "user_population": lambda: _has_any(text, ["patient", "public", "students", "staff", "users"]),
        "power_access": lambda: _has_any(text, ["power", "wired", "electrical", "120v"]),
        "resolved_jurisdiction": lambda: bool(
            location and location.state and (location.zip_code or location.city)
        ),
        "code_family": lambda: _has_any(text, ["ibc", "ada", "nfpa", "ifc", "a117"]),
        "section_number": lambda: bool(re.search(r"\b\d{3,4}(?:\.\d+)?\b", text)),
        "conversation_stage": lambda: True,
        "intent_value": lambda: True,
        "user_engagement_score": lambda: False,
        "selected_products": lambda: _has_any(text, ["product", "products", "quote", "package"]),
        "jurisdiction": lambda: bool(facts.state or facts.zip_code or facts.city),
        "contact_details": lambda: _has_any(text, ["email", "phone", "call me", "contact me"]),
        "project_notes": lambda: bool(request.message.strip()),
    }

    check = entity_checks.get(normalized_entity)
    if check is not None:
        return bool(check())

    # Unknown future dataset fields are considered missing unless the literal
    # phrase appears in the request. This keeps ingestion schema-tolerant while
    # still surfacing newly-added requirements to the user.
    return entity.lower() in text


def get_missing_information_for_intent(
    request: ChatRequest,
    intent: str,
) -> list[str]:
    normalized_intent = normalize_intent(intent)
    required_entities = get_required_entities_by_intent().get(normalized_intent)

    if not required_entities:
        required_entities = [
            "building type",
            "application",
            "state",
            "ZIP",
        ]

    missing_information = []
    facts = extract_project_facts(request)
    for entity in required_entities:
        if not _has_entity(request, entity, facts):
            missing_information.append(normalize_missing_field(entity))

    return missing_information
