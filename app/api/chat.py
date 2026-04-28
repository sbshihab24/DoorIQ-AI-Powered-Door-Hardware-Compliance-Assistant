from uuid import uuid4

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def create_chat_message(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid4())

    return ChatResponse(
        session_id=session_id,
        answer="I need more project details before I can give a door and hardware recommendation.",
        missing_information=["building_type", "application", "state", "zip_code"],
        confidence="low",
        human_review_recommended=True,
    )
