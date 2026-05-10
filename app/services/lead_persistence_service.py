from sqlalchemy.orm import Session

from app.db.models import ChatSession, Lead
from app.schemas.lead import LeadCreate


def create_lead_record(db: Session, lead: LeadCreate) -> Lead:
    chat_session = db.get(ChatSession, lead.session_id)

    if chat_session is None:
        chat_session = ChatSession(id=lead.session_id)
        db.add(chat_session)

    if lead.email:
        chat_session.email = lead.email
    if lead.phone:
        chat_session.phone = lead.phone
    if lead.name:
        chat_session.lead_name = lead.name

    lead_record = Lead(
        session_id=lead.session_id,
        email=lead.email,
        phone=lead.phone,
        name=lead.name,
        project_notes=lead.project_notes,
    )
    db.add(lead_record)
    db.commit()
    db.refresh(lead_record)

    return lead_record
