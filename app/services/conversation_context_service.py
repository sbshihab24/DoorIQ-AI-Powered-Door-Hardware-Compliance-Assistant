from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.db.models import ChatMessage, ChatSession
from app.schemas.chat import ChatRequest
from app.schemas.common import BuildingContext, LocationInput
from app.services.intent_service import detect_intent


STATE_NAMES = {
    "texas": "TX",
    "tx": "TX",
    "california": "CA",
    "ca": "CA",
    "florida": "FL",
    "fl": "FL",
    "new york": "NY",
    "ny": "NY",
}

BUILDING_KEYWORDS = {
    "hospital": "hospital",
    "clinic": "healthcare",
    "healthcare": "healthcare",
    "memory care": "healthcare",
    "school": "school",
    "office": "office",
    "warehouse": "warehouse",
}


def _first_zip_code(text: str) -> str | None:
    match = re.search(r"\b\d{5}(?:-\d{4})?\b", text)
    return match.group(0) if match else None


def _state_from_text(text: str) -> str | None:
    normalized_text = text.lower()
    for keyword, state_code in STATE_NAMES.items():
        if re.search(rf"\b{re.escape(keyword)}\b", normalized_text):
            return state_code

    return None


def _building_type_from_text(text: str) -> str | None:
    normalized_text = text.lower()
    for keyword, building_type in BUILDING_KEYWORDS.items():
        if keyword in normalized_text:
            return building_type

    return None


def _application_from_text(text: str) -> str | None:
    normalized_text = text.lower()

    if "masonry" in normalized_text and "frame" in normalized_text:
        return "masonry opening frame"
    if "main entrance" in normalized_text:
        return "main entrance"
    if "hospital" in normalized_text and "corridor" in normalized_text:
        return "hospital corridor"
    if "corridor" in normalized_text:
        return "corridor opening"
    if "patient room" in normalized_text:
        return "patient room"
    if "restroom" in normalized_text:
        return "restroom"
    if "egress" in normalized_text or "exit door" in normalized_text:
        return "egress door"
    if "rated opening" in normalized_text:
        return "rated opening"

    return None


def infer_request_context(message: str) -> ChatRequest:
    normalized_message = message.lower()
    building = BuildingContext(
        building_type=_building_type_from_text(message),
        application=_application_from_text(message),
        is_new_construction=True
        if "new construction" in normalized_message or "new work" in normalized_message
        else False
        if "existing" in normalized_message or "renovation" in normalized_message
        else None,
        is_egress_path=True
        if any(term in normalized_message for term in ["egress", "exit path", "exit door"])
        else None,
        fire_rating_required=True
        if any(term in normalized_message for term in ["fire-rated", "fire rated", "rated", "fire rating"])
        else None,
        accessibility_required=True
        if any(term in normalized_message for term in ["ada", "accessible", "handicap"])
        else None,
    )
    location = LocationInput(
        state=_state_from_text(message),
        zip_code=_first_zip_code(message),
    )

    return ChatRequest(message=message, building=building, location=location)


def _merge_building_context(
    session: ChatSession | None,
    inferred: BuildingContext | None,
    explicit: BuildingContext | None,
) -> BuildingContext | None:
    building_type = (
        (explicit.building_type if explicit else None)
        or (inferred.building_type if inferred else None)
        or (session.building_type if session else None)
    )
    application = (
        (explicit.application if explicit else None)
        or (inferred.application if inferred else None)
        or (session.application if session else None)
    )
    is_new_construction = (
        (explicit.is_new_construction if explicit and explicit.is_new_construction is not None else None)
        if explicit
        else None
    )
    if is_new_construction is None and inferred:
        is_new_construction = inferred.is_new_construction
    if is_new_construction is None and session:
        is_new_construction = session.is_new_construction

    is_egress_path = (
        (explicit.is_egress_path if explicit and explicit.is_egress_path is not None else None)
        if explicit
        else None
    )
    if is_egress_path is None and inferred:
        is_egress_path = inferred.is_egress_path
    if is_egress_path is None and session:
        is_egress_path = session.is_egress_path

    fire_rating_required = (
        (explicit.fire_rating_required if explicit and explicit.fire_rating_required is not None else None)
        if explicit
        else None
    )
    if fire_rating_required is None and inferred:
        fire_rating_required = inferred.fire_rating_required
    if fire_rating_required is None and session:
        fire_rating_required = session.fire_rating_required

    accessibility_required = (
        (explicit.accessibility_required if explicit and explicit.accessibility_required is not None else None)
        if explicit
        else None
    )
    if accessibility_required is None and inferred:
        accessibility_required = inferred.accessibility_required
    if accessibility_required is None and session:
        accessibility_required = session.accessibility_required

    if not any(
        value is not None
        for value in [
            building_type,
            application,
            is_new_construction,
            is_egress_path,
            fire_rating_required,
            accessibility_required,
        ]
    ):
        return None

    return BuildingContext(
        building_type=building_type,
        application=application,
        is_new_construction=is_new_construction,
        is_egress_path=is_egress_path,
        fire_rating_required=fire_rating_required,
        accessibility_required=accessibility_required,
    )


def _merge_location_context(
    session: ChatSession | None,
    inferred: LocationInput | None,
    explicit: LocationInput | None,
) -> LocationInput | None:
    state = (
        (explicit.state if explicit else None)
        or (inferred.state if inferred else None)
        or (session.state if session else None)
    )
    zip_code = (
        (explicit.zip_code if explicit else None)
        or (inferred.zip_code if inferred else None)
        or (session.zip_code if session else None)
    )
    city = (
        (explicit.city if explicit else None)
        or (inferred.city if inferred else None)
        or (session.city if session else None)
    )

    if not any([state, zip_code, city]):
        return None

    return LocationInput(state=state, zip_code=zip_code, city=city)


def _latest_non_general_user_message(db: Session, session_id: str) -> str | None:
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id, ChatMessage.role == "user")
        .order_by(ChatMessage.id.desc())
        .limit(6)
        .all()
    )

    for message in messages:
        if detect_intent(message.content) != "general":
            return message.content

    return None


def _looks_like_context_update(message: str) -> bool:
    normalized_message = message.strip().lower()
    return (
        normalized_message.startswith(("it is", "it's", "this is", "that is"))
        or normalized_message.startswith(("yes", "no"))
        or " zip " in f" {normalized_message} "
    ) and "?" not in normalized_message


def merge_conversation_context(db: Session, request: ChatRequest) -> ChatRequest:
    session = db.get(ChatSession, request.session_id) if request.session_id else None
    inferred = infer_request_context(request.message)

    message_for_response = request.message
    if request.session_id and (
        detect_intent(request.message) == "general"
        or _looks_like_context_update(request.message)
    ):
        previous_message = _latest_non_general_user_message(db, request.session_id)
        if previous_message:
            message_for_response = f"{previous_message} {request.message}"

    return ChatRequest(
        session_id=request.session_id,
        message=message_for_response,
        building=_merge_building_context(session, inferred.building, request.building),
        location=_merge_location_context(session, inferred.location, request.location),
    )
