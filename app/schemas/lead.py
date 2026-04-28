from pydantic import BaseModel


class LeadCreate(BaseModel):
    session_id: str
    email: str
    phone: str
    name: str | None = None
    project_notes: str | None = None


class LeadResponse(BaseModel):
    id: int
    session_id: str
    email: str
    phone: str
