from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import build_and_save_chat_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def create_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    return build_and_save_chat_response(db, request)
