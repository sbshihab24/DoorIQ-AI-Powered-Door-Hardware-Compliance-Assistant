from uuid import uuid4

from app.schemas.chat import ChatRequest, ChatResponse, CodeReference, RecommendedProduct
from app.services.code_service import find_code_references
from app.services.guidance_service import get_guidance_for_intent
from app.services.intent_service import detect_intent
from app.services.lead_service import should_capture_lead
from app.services.product_service import find_products_for_application


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
    answers = {
        "access_control": "Access control hardware depends on egress, fire rating, and local code limits.",
        "accessibility": "Accessibility hardware depends on the entrance type, operator needs, and clear opening requirements.",
        "code": "Code guidance depends on the building type, application, state, and ZIP code.",
        "egress": "Egress door hardware depends on occupancy, exit path use, panic hardware needs, and local code.",
        "fire_rating": "Fire-rated openings usually require compatible rated doors, frames, latching, and closing hardware.",
        "hardware": "Hardware recommendations depend on the door application, traffic level, egress use, and rating needs.",
    }

    return answers.get(
        intent,
        "I need more project details before I can give a door and hardware recommendation.",
    )


def build_chat_response(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid4())
    intent = detect_intent(request.message)
    guidance = get_guidance_for_intent(intent)
    application = request.building.application if request.building else None
    state = request.location.state if request.location else None
    products = find_products_for_application(application)
    recommended_products = [
        RecommendedProduct(
            name=product.name,
            category=product.category,
            reason=f"Matches the application: {application}.",
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
        for code_reference in find_code_references(intent, state)
    ]

    return ChatResponse(
        session_id=session_id,
        intent=intent,
        answer=get_answer_for_intent(intent),
        requirements=guidance.requirements,
        allowed_options=guidance.allowed_options,
        risky_or_not_allowed=guidance.risky_or_not_allowed,
        recommended_products=recommended_products,
        code_references=code_references,
        missing_information=get_missing_information(request),
        should_capture_lead=should_capture_lead(request),
        confidence="low",
        human_review_recommended=True,
    )
