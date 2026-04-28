from pydantic import BaseModel

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


class CodeReference(BaseModel):
    title: str
    section: str | None = None
    url: str | None = None
    summary: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    requirements: list[str] = []
    allowed_options: list[str] = []
    risky_or_not_allowed: list[str] = []
    recommended_products: list[RecommendedProduct] = []
    code_references: list[CodeReference] = []
    missing_information: list[str] = []
    should_capture_lead: bool = False
    confidence: str
    human_review_recommended: bool = False
