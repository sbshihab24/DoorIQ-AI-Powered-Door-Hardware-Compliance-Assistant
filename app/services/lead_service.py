import re

from sqlalchemy.orm import Session

from app.db.models import ChatSession, Lead
from app.schemas.chat import ChatRequest
from app.schemas.chat import LeadCaptureStatus


LEAD_CAPTURE_KEYWORDS = [
    "call me",
    "contact me",
    "email me",
    "follow up",
    "quote",
    "pricing",
    "proposal",
]


def should_capture_lead(request: ChatRequest) -> bool:
    normalized_message = request.message.lower()

    if any(keyword in normalized_message for keyword in LEAD_CAPTURE_KEYWORDS):
        return True

    has_location = bool(request.location and request.location.state and request.location.zip_code)
    has_building_context = bool(
        request.building
        and request.building.building_type
        and request.building.application
    )

    return has_location and has_building_context


def extract_email(message: str) -> str | None:
    match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", message)
    return match.group(0).lower() if match else None


def extract_phone(message: str) -> str | None:
    match = re.search(
        r"(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}",
        message,
    )
    if not match:
        return None

    return match.group(0).strip()


def apply_contact_details_to_session(
    chat_session: ChatSession,
    message: str,
) -> None:
    email = extract_email(message)
    phone = extract_phone(message)

    if email:
        chat_session.email = email
    if phone:
        chat_session.phone = phone


def get_lead_capture_status(chat_session: ChatSession | None) -> LeadCaptureStatus:
    if chat_session is None:
        return LeadCaptureStatus()

    return LeadCaptureStatus(
        email_collected=bool(chat_session.email),
        phone_collected=bool(chat_session.phone),
        lead_created=bool(chat_session.leads),
    )


def create_lead_from_session_if_ready(
    db: Session,
    chat_session: ChatSession,
    project_notes: str | None = None,
) -> bool:
    if not chat_session.email and not chat_session.phone:
        return False

    query = db.query(Lead).filter(Lead.session_id == chat_session.id)
    if chat_session.email:
        query = query.filter(Lead.email == chat_session.email)
    if chat_session.phone:
        query = query.filter(Lead.phone == chat_session.phone)

    existing_lead = query.first()
    if existing_lead is not None:
        if chat_session.lead_name and not existing_lead.name:
            existing_lead.name = chat_session.lead_name
        if project_notes and not existing_lead.project_notes:
            existing_lead.project_notes = project_notes
        return False

    db.add(
        Lead(
            session_id=chat_session.id,
            email=chat_session.email,
            phone=chat_session.phone,
            name=chat_session.lead_name,
            project_notes=project_notes,
        )
    )
    return True
