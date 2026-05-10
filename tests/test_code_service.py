from app.services.code_service import find_code_references


def test_find_code_references_for_fire_rating_intent() -> None:
    references = find_code_references("fire_rating")

    assert references
    assert references[0].title == "NFPA 80"
    assert references[0].section == "fire door standard"


def test_find_code_references_returns_state_review_fallback() -> None:
    references = find_code_references("general", state="ca")

    assert references[0].title == "CA Local Code Review"
    assert references[0].url == "https://codes.iccsafe.org/codes/united-states"
