from pydantic import BaseModel


class LocationInput(BaseModel):
    state: str | None = None
    zip_code: str | None = None
    city: str | None = None


class BuildingContext(BaseModel):
    building_type: str | None = None
    application: str | None = None
    is_new_construction: bool | None = None
    is_egress_path: bool | None = None
    fire_rating_required: bool | None = None
    accessibility_required: bool | None = None
