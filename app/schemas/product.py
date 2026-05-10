from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    category: str
    description: str | None = None
    compatible_applications: list[str] = Field(default_factory=list)
    source_url: str | None = None
    starting_price_usd: float | None = None
    fire_rating: str | None = None
    notes: str | None = None
