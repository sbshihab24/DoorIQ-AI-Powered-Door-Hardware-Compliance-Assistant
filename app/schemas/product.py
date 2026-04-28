from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    category: str
    description: str | None = None
    compatible_applications: list[str] = Field(default_factory=list)
    notes: str | None = None
