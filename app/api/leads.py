from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadResponse
from app.services.lead_persistence_service import create_lead_record

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadResponse)
def create_lead(
    lead: LeadCreate,
    db: Session = Depends(get_db),
) -> LeadResponse:
    lead_record = create_lead_record(db, lead)

    return LeadResponse(
        id=lead_record.id,
        session_id=lead_record.session_id,
        email=lead_record.email,
        phone=lead_record.phone,
    )
