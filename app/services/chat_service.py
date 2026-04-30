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
from app.services.code_service import find_code_references
from app.services.guidance_service import get_guidance_for_intent
from app.services.intent_service import detect_intent, normalize_intent
from app.services.lead_service import should_capture_lead
from app.services.product_service import (
    find_products_for_application,
    get_product_match_reason,
)
from app.services.retrieval_service import find_relevant_knowledge


def get_missing_information(request: ChatRequest) -> list[str]:
    missing_information = []

    if not request.building or not request.building.building_type:
        missing_information.append("building_type")

    if not request.building or not request.building.application:
        missing_information.append("application")

    if not request.location or not request.location.state:
        missing_information.append("state")

    if not request.location or not request.location.zip_code:
        missing_information.append("zip_code")

    return missing_information


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
    missing_information: list[str],
    confidence: str,
) -> bool:
    return bool(missing_information) or confidence != "medium"


def build_chat_response(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid4())
    intent = detect_intent(request.message)
    normalized_intent = normalize_intent(intent)
    guidance = get_guidance_for_intent(normalized_intent)
    application = request.building.application if request.building else None
    state = request.location.state if request.location else None
    product_query = " ".join(
        query_part
        for query_part in [application, request.message, normalized_intent]
        if query_part
    )
    products = find_products_for_application(product_query)
    recommended_products = [
        RecommendedProduct(
            name=product.name,
            category=product.category,
            reason=get_product_match_reason(product, product_query),
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
        for code_reference in find_code_references(normalized_intent, state)
    ]
    knowledge_references = [
        KnowledgeReference(
            title=snippet.title,
            source=snippet.source,
            summary=snippet.content,
        )
        for snippet in find_relevant_knowledge(product_query, normalized_intent)
    ]
    missing_information = get_missing_information(request)
    confidence = get_response_confidence(
        missing_information=missing_information,
        recommended_products=recommended_products,
        code_references=code_references,
        knowledge_references=knowledge_references,
    )

    return ChatResponse(
        session_id=session_id,
        intent=intent,
        answer=get_answer_for_intent(intent),
        requirements=guidance.requirements,
        allowed_options=guidance.allowed_options,
        risky_or_not_allowed=guidance.risky_or_not_allowed,
        recommended_products=recommended_products,
        code_references=code_references,
        knowledge_references=knowledge_references,
        missing_information=missing_information,
        should_capture_lead=should_capture_lead(request),
        confidence=confidence,
        human_review_recommended=should_recommend_human_review(
            missing_information,
            confidence,
        ),
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

    return chat_session


def save_chat_exchange(
    db: Session,
    request: ChatRequest,
    response: ChatResponse,
) -> None:
    get_or_create_chat_session(db, request, response.session_id)
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
    response = build_chat_response(request)
    save_chat_exchange(db, request, response)
    return response
