from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import ChatMessage, ChatSession
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CodeReference,
    KnowledgeReference,
    RecommendedProduct,
)
from app.services.answer_service import build_answer
from app.services.chat_extraction_service import ChatExtraction, extract_chat_details
from app.services.code_service import find_code_references
from app.services.conversation_context_service import merge_conversation_context
from app.services.guidance_service import get_guidance_for_intent
from app.services.intent_service import detect_intent, normalize_intent
from app.services.local_code_service import build_local_code_references
from app.services.lead_service import (
    create_lead_from_session_if_ready,
    get_lead_capture_status,
    should_capture_lead,
)
from app.services.missing_information_service import get_missing_information_for_intent
from app.services.product_service import (
    find_products_for_application,
    get_product_match_reason,
)
from app.services.project_facts_service import extract_project_facts
from app.services.retrieval_service import find_relevant_knowledge
from app.services.retrieval_service import find_relevant_knowledge_from_db


def get_missing_information(request: ChatRequest, intent: str = "general") -> list[str]:
    return get_missing_information_for_intent(request, intent)


def get_answer_for_intent(intent: str) -> str:
    intent = normalize_intent(intent)

    answers = {
        "maglock_analysis": "Maglocks and access control hardware depend on egress role, release method, fire rating, occupancy, and local code limits.",
        "accessibility_analysis": "Accessibility guidance depends on the entrance type, accessible-route status, clear opening, maneuvering clearance, hardware operation, and operator needs.",
        "applicable_code_lookup": "Code guidance depends on the building type, application, state, ZIP code, and adopted local amendments.",
        "egress_analysis": "Egress door hardware depends on occupancy, occupant load, exit path use, panic hardware needs, and local code.",
        "fire_rating_analysis": "Fire-rated openings usually require compatible labeled doors, frames, latching, and closing hardware.",
        "hardware_allowance": "Hardware recommendations depend on door application, traffic level, egress use, access control intent, and rating needs.",
        "door_type_recommendation": "Door recommendations depend on opening location, material, fire rating, traffic level, accessibility, and egress role.",
        "product_match": "Product matches depend on the opening type, rating, dimensions, finish, hardware family, and project constraints.",
        "sliding_door_analysis": "Sliding door use depends on occupancy, egress function, accessibility route status, and local code conditions.",
        "delayed_egress_analysis": "Delayed egress depends on occupancy, security use case, fire alarm or sprinkler conditions, and AHJ approval.",
        "automatic_operator_recommendation": "Automatic operator recommendations depend on entrance type, accessible-route requirements, user population, and power availability.",
        "code_section_navigation": "Exact code-section links require the jurisdiction, adopted code edition, and local amendment context.",
        "quote_handoff": "For pricing or quote handoff, the chatbot should package the project facts, selected products, jurisdiction, and contact details.",
    }

    return answers.get(
        intent,
        "I need more project details before I can give a door and hardware recommendation.",
    )


def get_response_confidence(
    missing_information: list[str],
    recommended_products: list[RecommendedProduct],
    code_references: list[CodeReference],
    knowledge_references: list[KnowledgeReference],
) -> str:
    if missing_information:
        return "low"

    if recommended_products and code_references and knowledge_references:
        return "medium"

    return "low"


def should_recommend_human_review(
    request: ChatRequest,
    missing_information: list[str],
    confidence: str,
) -> bool:
    normalized_message = request.message.lower()
    safety_terms = [
        "delayed egress",
        "maglock",
        "magnetic lock",
        "fire-rated",
        "fire rated",
        "memory care",
        "lockdown",
    ]
    if any(term in normalized_message for term in safety_terms):
        return True
    return bool(missing_information) or confidence != "medium"


def _build_special_chat_response(
    request: ChatRequest,
    session_id: str,
    intent: str,
    db: Session | None = None,
) -> ChatResponse | None:
    if intent == "greeting":
        answer = "Hi, how can I help you?"
    elif intent == "out_of_scope":
        answer = (
            "I am focused on commercial doors, frames, hardware, accessibility, "
            "egress, fire ratings, and related product or code guidance. Ask me a "
            "DoorIQ question and I will help narrow it down."
        )
    else:
        return None

    return ChatResponse(
        session_id=session_id,
        intent=intent,
        answer=answer,
        requirements=[],
        allowed_options=[],
        risky_or_not_allowed=[],
        recommended_products=[],
        code_references=[],
        knowledge_references=[],
        missing_information=[],
        should_capture_lead=False,
        lead_capture_status=get_lead_capture_status(
            db.get(ChatSession, session_id) if db is not None else None
        ),
        confidence="medium",
        human_review_recommended=False,
    )


def build_chat_response(request: ChatRequest, db: Session | None = None) -> ChatResponse:
    session_id = request.session_id or str(uuid4())
    intent = detect_intent(request.message)
    special_response = _build_special_chat_response(request, session_id, intent, db)
    if special_response is not None:
        return special_response

    normalized_intent = normalize_intent(intent)
    facts = extract_project_facts(request)
    guidance = get_guidance_for_intent(normalized_intent)
    application = facts.application
    state = facts.state
    product_query = " ".join(
        query_part
        for query_part in [
            application,
            request.message,
            "fire rated" if facts.rating_required or facts.rating_minutes else "",
            f"{facts.material_preference} door" if facts.material_preference else "",
            facts.hardware_type or "",
            normalized_intent,
        ]
        if query_part
    )
    if normalized_intent == "door_type_recommendation" and not facts.building_type:
        product_query = request.message
    products = find_products_for_application(product_query)
    recommended_products = [
        RecommendedProduct(
            name=product.name,
            category=product.category,
            reason=get_product_match_reason(product, product_query),
            source_url=product.source_url,
            starting_price_usd=product.starting_price_usd,
            fire_rating=product.fire_rating,
            notes=product.notes,
        )
        for product in products
    ]
    code_references = [
        CodeReference(
            title=code_reference.title,
            section=code_reference.section,
            url=code_reference.url,
            summary=code_reference.content,
        )
        for code_reference in [
            *build_local_code_references(request, normalized_intent),
            *find_code_references(normalized_intent, state),
        ]
    ]
    if db is not None:
        relevant_knowledge = find_relevant_knowledge_from_db(
            db,
            product_query,
            normalized_intent,
        )
    else:
        relevant_knowledge = find_relevant_knowledge(product_query, normalized_intent)

    knowledge_references = [
        KnowledgeReference(
            title=snippet.title,
            source=snippet.source,
            summary=snippet.content,
        )
        for snippet in relevant_knowledge
    ]
    missing_information = get_missing_information(request, normalized_intent)
    confidence = get_response_confidence(
        missing_information=missing_information,
        recommended_products=recommended_products,
        code_references=code_references,
        knowledge_references=knowledge_references,
    )

    human_review_recommended = should_recommend_human_review(
        request,
        missing_information,
        confidence,
    )
    answer = build_answer(
        request=request,
        intent=intent,
        requirements=guidance.requirements,
        allowed_options=guidance.allowed_options,
        risky_or_not_allowed=guidance.risky_or_not_allowed,
        recommended_products=recommended_products,
        code_references=code_references,
        knowledge_references=knowledge_references,
        missing_information=missing_information,
    )
    if human_review_recommended and should_capture_lead(request):
        answer = (
            f"{answer}\n\nHuman assistance:\n"
            "- Share email and phone if you want someone to review this opening."
        )

    return ChatResponse(
        session_id=session_id,
        intent=intent,
        answer=answer,
        requirements=guidance.requirements,
        allowed_options=guidance.allowed_options,
        risky_or_not_allowed=guidance.risky_or_not_allowed,
        recommended_products=recommended_products,
        code_references=code_references,
        knowledge_references=knowledge_references,
        missing_information=missing_information,
        should_capture_lead=should_capture_lead(request),
        lead_capture_status=get_lead_capture_status(
            db.get(ChatSession, session_id) if db is not None else None
        ),
        confidence=confidence,
        human_review_recommended=human_review_recommended,
    )


def get_or_create_chat_session(db: Session, request: ChatRequest, session_id: str) -> ChatSession:
    chat_session = db.get(ChatSession, session_id)

    if chat_session is None:
        chat_session = ChatSession(id=session_id)
        db.add(chat_session)

    if request.building:
        if request.building.building_type is not None:
            chat_session.building_type = request.building.building_type
        if request.building.application is not None:
            chat_session.application = request.building.application

    if request.location:
        if request.location.state is not None:
            chat_session.state = request.location.state
        if request.location.zip_code is not None:
            chat_session.zip_code = request.location.zip_code
        if request.location.city is not None:
            chat_session.city = request.location.city

    if request.building:
        if request.building.is_new_construction is not None:
            chat_session.is_new_construction = request.building.is_new_construction
        if request.building.is_egress_path is not None:
            chat_session.is_egress_path = request.building.is_egress_path
        if request.building.fire_rating_required is not None:
            chat_session.fire_rating_required = request.building.fire_rating_required
        if request.building.accessibility_required is not None:
            chat_session.accessibility_required = request.building.accessibility_required

    return chat_session


def _recent_user_messages(db: Session, session_id: str, current_message: str) -> list[str]:
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id, ChatMessage.role == "user")
        .order_by(ChatMessage.id.desc())
        .limit(12)
        .all()
    )
    recent_messages = [
        message.content.strip()
        for message in reversed(messages)
        if message.content.strip()
    ]
    if current_message.strip():
        recent_messages.append(current_message.strip())
    return recent_messages


def _merge_project_context(
    existing_context: dict | None,
    extracted_context: dict,
) -> dict:
    merged_context = dict(existing_context or {})
    for key, value in extracted_context.items():
        if value is not None and value != "":
            merged_context[key] = value
    return merged_context


def _apply_extraction_to_session(
    chat_session: ChatSession,
    extraction: ChatExtraction,
) -> None:
    if extraction.email:
        chat_session.email = extraction.email
    if extraction.phone:
        chat_session.phone = extraction.phone
    if extraction.name:
        chat_session.lead_name = extraction.name

    chat_session.project_context = _merge_project_context(
        chat_session.project_context,
        extraction.project_context,
    )

    context = chat_session.project_context or {}
    chat_session.building_type = context.get("building_type") or chat_session.building_type
    chat_session.application = context.get("application") or chat_session.application
    chat_session.state = context.get("state") or chat_session.state
    chat_session.zip_code = context.get("zip_code") or chat_session.zip_code
    chat_session.city = context.get("city") or chat_session.city
    for field_name in [
        "is_new_construction",
        "is_egress_path",
        "fire_rating_required",
        "accessibility_required",
    ]:
        context_value = context.get(field_name)
        if context_value is not None:
            setattr(chat_session, field_name, context_value)


def save_chat_exchange(
    db: Session,
    request: ChatRequest,
    response: ChatResponse,
    context_request: ChatRequest | None = None,
) -> None:
    chat_session = get_or_create_chat_session(
        db,
        context_request or request,
        response.session_id,
    )
    extraction = extract_chat_details(
        _recent_user_messages(db, response.session_id, request.message)
    )
    _apply_extraction_to_session(chat_session, extraction)
    if extraction.wants_follow_up or chat_session.email or chat_session.phone:
        response.should_capture_lead = True
    lead_created = False
    if (
        should_capture_lead(context_request or request)
        or extraction.wants_follow_up
        or bool(chat_session.email or chat_session.phone)
    ):
        lead_created = create_lead_from_session_if_ready(
            db,
            chat_session,
            project_notes=extraction.project_notes or request.message,
        )
        if lead_created and "Human assistance:" not in response.answer:
            response.answer = (
                f"{response.answer}\n\nHuman assistance:\n"
                "- Your contact details were saved for follow-up."
            )
        elif lead_created:
            response.answer = (
                f"{response.answer}\n"
                "- Your contact details were saved for follow-up."
            )

    response.lead_capture_status.email_collected = bool(chat_session.email)
    response.lead_capture_status.phone_collected = bool(chat_session.phone)
    response.lead_capture_status.lead_created = (
        response.lead_capture_status.lead_created or lead_created
    )
    db.add_all(
        [
            ChatMessage(
                session_id=response.session_id,
                role="user",
                content=request.message,
            ),
            ChatMessage(
                session_id=response.session_id,
                role="assistant",
                content=response.answer,
            ),
        ]
    )
    db.commit()


def build_and_save_chat_response(db: Session, request: ChatRequest) -> ChatResponse:
    context_request = merge_conversation_context(db, request)
    response = build_chat_response(context_request, db)
    save_chat_exchange(db, request, response, context_request)
    return response
