from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import ChatMessage, ChatSession
from app.schemas.chat import ChatRequest
from app.schemas.common import BuildingContext, LocationInput
from app.services.intent_service import detect_intent
from app.services.project_facts_service import extract_project_facts


def infer_request_context(message: str) -> ChatRequest:
    facts = extract_project_facts(ChatRequest(message=message))
    building = BuildingContext(
        building_type=facts.building_type,
        application=facts.application,
        is_new_construction=facts.new_vs_existing,
        is_egress_path=facts.is_egress_path,
        fire_rating_required=facts.rating_required,
        accessibility_required=facts.accessibility_required,
    )
    location = LocationInput(
        state=facts.state,
        zip_code=facts.zip_code,
        city=facts.city,
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


def _recent_user_context(db: Session, session_id: str) -> str | None:
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id, ChatMessage.role == "user")
        .order_by(ChatMessage.id.desc())
        .limit(6)
        .all()
    )
    ordered_messages = [
        message.content.strip()
        for message in reversed(messages)
        if message.content.strip()
    ]
    return " ".join(ordered_messages) if ordered_messages else None


def _looks_like_context_update(message: str) -> bool:
    normalized_message = message.strip().lower()
    return (
        normalized_message.startswith(("it is", "it's", "this is", "that is"))
        or normalized_message.startswith(("yes", "no"))
        or " zip " in f" {normalized_message} "
        or any(
            term in normalized_message
            for term in [
                "interior",
                "exterior",
                "fire rating",
                "fire rate",
                "fire-rated",
                "fire rated",
                "rated",
                "mins",
                "minutes",
                "min",
                "light",
                "normal",
                "high traffic",
                "heavy traffic",
                "wood",
                "hollow metal",
                "metal",
                "aluminum",
                "storefront",
                "wall",
                "barrier",
                "corridor wall",
                "smoke barrier",
                "fire barrier",
                "stair enclosure",
            ]
        )
    ) and "?" not in normalized_message


def merge_conversation_context(db: Session, request: ChatRequest) -> ChatRequest:
    session = db.get(ChatSession, request.session_id) if request.session_id else None

    message_for_response = request.message
    is_context_update = _looks_like_context_update(request.message)
    current_intent = detect_intent(request.message)
    if request.session_id and is_context_update:
        previous_context = _recent_user_context(db, request.session_id)
        if previous_context:
            message_for_response = f"{previous_context} {request.message}"
    elif request.session_id and current_intent in {"product_match", "quote_handoff"}:
        previous_context = _recent_user_context(db, request.session_id)
        if previous_context:
            message_for_response = f"{previous_context} {request.message}"
    elif request.session_id and current_intent == "general":
        previous_context = _recent_user_context(db, request.session_id)
        if previous_context:
            message_for_response = f"{previous_context} {request.message}"
    elif request.session_id and current_intent not in {"greeting", "out_of_scope"}:
        previous_context = _recent_user_context(db, request.session_id)
        if previous_context:
            message_for_response = f"{previous_context} {request.message}"

    inferred = infer_request_context(message_for_response)

    return ChatRequest(
        session_id=request.session_id,
        message=message_for_response,
        building=_merge_building_context(session, inferred.building, request.building),
        location=_merge_location_context(session, inferred.location, request.location),
    )
