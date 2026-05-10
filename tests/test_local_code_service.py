from app.schemas.chat import ChatRequest
from app.services.local_code_service import (
    build_local_code_references,
    get_local_code_schema_fields,
    resolve_jurisdiction_context,
)


def test_resolve_jurisdiction_context_uses_only_provided_location() -> None:
    request = ChatRequest(
        message="What code applies?",
        location={"state": "TX", "zip_code": "77002"},
    )

    jurisdiction = resolve_jurisdiction_context(request)

    assert jurisdiction is not None
    assert jurisdiction.state == "TX"
    assert jurisdiction.zip_code == "77002"
    assert jurisdiction.city is None
    assert jurisdiction.jurisdiction_name == "TX"


def test_build_local_code_references_returns_verification_packet() -> None:
    request = ChatRequest(
        message="Can I use a maglock here?",
        location={"state": "TX", "zip_code": "77002"},
    )

    references = build_local_code_references(request, "maglock_analysis")

    assert references[0].title == "TX / 77002 Code Verification Packet"
    assert references[0].section == "local code verification"
    assert "not as final legal text" in references[0].content
    assert "adopted_building_code" in references[0].content
    assert "local_amendments_url" in references[0].content
    assert "last_verified_utc" in references[0].content
    assert references[0].url == "https://codes.iccsafe.org/"


def test_build_local_code_references_skips_plain_product_match() -> None:
    request = ChatRequest(
        message="What frame should I use?",
        location={"state": "TX", "zip_code": "77002"},
    )

    assert build_local_code_references(request, "product_match") == []


def test_local_code_schema_fields_are_loaded_from_dataset() -> None:
    fields = get_local_code_schema_fields()

    assert "zip" in fields
    assert "state_code" in fields
    assert "ahj_contact" in fields
    assert "last_verified_utc" in fields
