from fastapi import APIRouter

from app.schemas.lead import LeadCreate, LeadResponse

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadResponse)
def create_lead(lead: LeadCreate) -> LeadResponse:
    return LeadResponse(
        id=1,
        session_id=lead.session_id,
        email=lead.email,
        phone=lead.phone,
    )
