from __future__ import annotations

from dataclasses import dataclass

from app.schemas.chat import ChatRequest
from app.schemas.code import CodeDocument
from app.services.data_loader import load_processed_json


@dataclass(frozen=True)
class JurisdictionContext:
    state: str
    zip_code: str | None = None
    city: str | None = None
    jurisdiction_name: str | None = None
    source_urls: tuple[str, ...] = ()


def get_dataset_source_urls() -> tuple[str, ...]:
    source_urls = []
    for source in load_processed_json("code_framework.json"):
        source_url = source.get("source_url")
        if isinstance(source_url, str) and source_url and source_url not in source_urls:
            source_urls.append(source_url)

    return tuple(source_urls)


def get_local_code_schema_fields() -> tuple[str, ...]:
    fields = []
    for schema_item in load_processed_json("local_code_schema.json"):
        field_name = schema_item.get("field_name")
        if isinstance(field_name, str) and field_name:
            fields.append(field_name)

    return tuple(fields)


def resolve_jurisdiction_context(request: ChatRequest) -> JurisdictionContext | None:
    if request.location is None:
        return None

    zip_code = (request.location.zip_code or "").strip()
    state = (request.location.state or "").strip().upper()
    city = (request.location.city or "").strip()

    if state or zip_code or city:
        jurisdiction_name = ", ".join(part for part in [city, state] if part)
        return JurisdictionContext(
            state=state or "unknown",
            zip_code=zip_code or None,
            city=city or None,
            jurisdiction_name=jurisdiction_name or zip_code or "Unresolved jurisdiction",
            source_urls=get_dataset_source_urls(),
        )

    return None


def build_local_code_references(request: ChatRequest, intent: str) -> list[CodeDocument]:
    jurisdiction = resolve_jurisdiction_context(request)
    if jurisdiction is None:
        return []

    if intent not in {
        "applicable_code_lookup",
        "code_section_navigation",
        "accessibility_analysis",
        "egress_analysis",
        "fire_rating_analysis",
        "maglock_analysis",
        "delayed_egress_analysis",
        "automatic_operator_recommendation",
    }:
        return []

    location_parts = [jurisdiction.jurisdiction_name]
    location_parts.append(jurisdiction.zip_code)
    location_label = " / ".join(part for part in location_parts if part)
    source_url = jurisdiction.source_urls[0] if jurisdiction.source_urls else None
    source_list = ", ".join(jurisdiction.source_urls)
    schema_fields = ", ".join(get_local_code_schema_fields())

    return [
        CodeDocument(
            id=f"local-{jurisdiction.state.lower()}-{jurisdiction.zip_code or 'state'}",
            title=f"{location_label} Code Verification Packet",
            jurisdiction=location_label,
            state=jurisdiction.state,
            section="local code verification",
            url=source_url,
            content=(
                "Use this as the local-code verification path, not as final legal text. "
                f"Resolve adopted building, fire, accessibility, and local amendment sources for {location_label}. "
                f"Dataset local-code schema fields to complete: {schema_fields}. "
                f"Dataset source families: {source_list}."
            ),
            tags=["local code", intent, "jurisdiction", "official source verification"],
        )
    ]
