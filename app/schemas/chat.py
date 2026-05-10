from pydantic import BaseModel, Field

from app.schemas.common import BuildingContext, LocationInput


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    location: LocationInput | None = None
    building: BuildingContext | None = None


class RecommendedProduct(BaseModel):
    name: str
    category: str
    reason: str
    source_url: str | None = None
    starting_price_usd: float | None = None
    fire_rating: str | None = None
    notes: str | None = None


class CodeReference(BaseModel):
    title: str
    section: str | None = None
    url: str | None = None
    summary: str


class KnowledgeReference(BaseModel):
    title: str
    source: str
    summary: str


class LeadCaptureStatus(BaseModel):
    email_collected: bool = False
    phone_collected: bool = False
    lead_created: bool = False


class ChatResponse(BaseModel):
    session_id: str
    intent: str | None = None
    answer: str
    requirements: list[str] = Field(default_factory=list)
    allowed_options: list[str] = Field(default_factory=list)
    risky_or_not_allowed: list[str] = Field(default_factory=list)
    recommended_products: list[RecommendedProduct] = Field(default_factory=list)
    code_references: list[CodeReference] = Field(default_factory=list)
    knowledge_references: list[KnowledgeReference] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    should_capture_lead: bool = False
    lead_capture_status: LeadCaptureStatus = Field(default_factory=LeadCaptureStatus)
    confidence: str
    human_review_recommended: bool = False
