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


class CodeReference(BaseModel):
    title: str
    section: str | None = None
    url: str | None = None
    summary: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    requirements: list[str] = Field(default_factory=list)
    allowed_options: list[str] = Field(default_factory=list)
    risky_or_not_allowed: list[str] = Field(default_factory=list)
    recommended_products: list[RecommendedProduct] = Field(default_factory=list)
    code_references: list[CodeReference] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    should_capture_lead: bool = False
    confidence: str
    human_review_recommended: bool = False
