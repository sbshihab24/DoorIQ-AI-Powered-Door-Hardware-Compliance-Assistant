from pydantic import BaseModel, Field


class CodeDocument(BaseModel):
    id: str
    title: str
    content: str
    jurisdiction: str | None = None
    state: str | None = None
    section: str | None = None
    url: str | None = None
    tags: list[str] = Field(default_factory=list)
