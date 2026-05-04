from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.schemas.chat import ChatRequest
from app.services.data_loader import load_processed_json
from app.services.intent_service import normalize_intent


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


def _request_text(request: ChatRequest) -> str:
    parts = [request.message]

    if request.building:
        parts.extend(
            [
                request.building.building_type or "",
                request.building.application or "",
            ]
        )

    if request.location:
        parts.extend(
            [
                request.location.state or "",
                request.location.zip_code or "",
                request.location.city or "",
            ]
        )

    return " ".join(parts).lower()


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _has_project_application(request: ChatRequest) -> bool:
    return bool(request.building and request.building.application)


def _has_entity(request: ChatRequest, entity: str) -> bool:
    normalized_entity = normalize_missing_field(entity)
    text = _request_text(request)
    building = request.building
    location = request.location

    entity_checks: dict[str, Any] = {
        "state": lambda: bool(location and location.state),
        "city": lambda: bool(location and location.city),
        "zip": lambda: bool(location and location.zip_code),
        "zip_code": lambda: bool(location and location.zip_code),
        "building_type": lambda: bool(building and building.building_type),
        "application": lambda: _has_project_application(request),
        "new_vs_existing": lambda: bool(
            building and building.is_new_construction is not None
        )
        or _has_any(text, ["new construction", "existing", "renovation", "new work"]),
        "door_type": lambda: _has_project_application(request)
        or _has_any(text, ["door", "frame", "opening"]),
        "hardware_type": lambda: _has_any(
            text,
            [
                "hardware",
                "closer",
                "hinge",
                "lock",
                "lockset",
                "exit device",
                "panic",
                "operator",
                "maglock",
            ],
        ),
        "finish": lambda: _has_any(text, ["finish", "paint", "painted", "stain", "primed", "galvanized"]),
        "rating": lambda: bool(building and building.fire_rating_required is not None)
        or _has_any(text, ["rated", "rating", "fire", "90-minute", "3 hour", "3-hour"]),
        "brand_preference": lambda: _has_any(text, ["tell", "schlage", "dormakaba", "assa", "accentra"]),
        "location": lambda: _has_project_application(request)
        or bool(location and (location.city or location.state or location.zip_code)),
        "interior_exterior": lambda: _has_any(text, ["interior", "exterior", "outside", "inside"]),
        "traffic": lambda: _has_any(text, ["traffic", "heavy use", "high frequency", "low frequency"]),
        "material_preference": lambda: _has_any(text, ["steel", "wood", "metal", "aluminum", "glass"]),
        "occupancy": lambda: bool(building and building.building_type and building.building_type != "general"),
        "occupant_load": lambda: _has_any(text, ["occupant load", "people", "occupants"]),
        "path_of_egress": lambda: bool(building and building.is_egress_path is not None)
        or _has_any(text, ["egress", "exit path", "exit door"]),
        "egress_path": lambda: bool(building and building.is_egress_path is not None)
        or _has_any(text, ["egress", "exit path", "exit door"]),
        "lock_type": lambda: _has_any(text, ["maglock", "lock", "lockset", "panic bar", "exit device"]),
        "wall_type": lambda: _has_any(text, ["masonry", "drywall", "stud", "wall type", "corridor wall"]),
        "barrier_type": lambda: _has_any(text, ["fire barrier", "smoke barrier", "corridor", "stair"]),
        "opening_location": lambda: _has_project_application(request),
        "accessible_route": lambda: bool(building and building.accessibility_required is not None)
        or _has_any(text, ["accessible", "ada", "handicap"]),
        "entrance_type": lambda: _has_any(text, ["entrance", "public entrance", "main entrance"]),
        "user_controls": lambda: _has_any(text, ["lever", "operator", "controls", "push button", "actuator"]),
        "thresholds": lambda: _has_any(text, ["threshold"]),
        "access_control": lambda: _has_any(text, ["access control", "maglock", "electric strike", "card reader"]),
        "access_control_intent": lambda: _has_any(text, ["access control", "maglock", "electric strike", "card reader", "security"]),
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
        "jurisdiction": lambda: bool(location and (location.state or location.zip_code or location.city)),
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
    for entity in required_entities:
        if not _has_entity(request, entity):
            missing_information.append(normalize_missing_field(entity))

    return missing_information
