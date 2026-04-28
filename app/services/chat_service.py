from uuid import uuid4

from app.schemas.chat import ChatRequest, ChatResponse, RecommendedProduct
from app.services.intent_service import detect_intent
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


def build_chat_response(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid4())
    application = request.building.application if request.building else None
    products = find_products_for_application(application)
    recommended_products = [
        RecommendedProduct(
            name=product.name,
            category=product.category,
            reason=f"Matches the application: {application}.",
        )
        for product in products
    ]

    return ChatResponse(
        session_id=session_id,
        intent=detect_intent(request.message),
        answer="I need more project details before I can give a door and hardware recommendation.",
        recommended_products=recommended_products,
        missing_information=get_missing_information(request),
        confidence="low",
        human_review_recommended=True,
    )
