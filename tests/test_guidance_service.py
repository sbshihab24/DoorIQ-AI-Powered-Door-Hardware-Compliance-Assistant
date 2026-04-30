from app.services.guidance_service import get_guidance_for_intent


def test_get_guidance_for_egress_intent() -> None:
    guidance = get_guidance_for_intent("egress")

    assert "Confirm occupancy" in guidance.requirements[0]
    assert "Listed exit device" in guidance.allowed_options[0]
    assert "prevents free egress" in guidance.risky_or_not_allowed[0]


def test_get_guidance_for_general_intent() -> None:
    guidance = get_guidance_for_intent("general")

    assert "building type" in guidance.requirements[0]
    assert guidance.allowed_options == []
    assert guidance.risky_or_not_allowed == []


def test_get_guidance_for_dataset_code_lookup_intent() -> None:
    guidance = get_guidance_for_intent("applicable_code_lookup")

    assert "state" in guidance.requirements[0]
    assert "ZIP" in guidance.requirements[0]
    assert "starter dataset" in guidance.risky_or_not_allowed[0]
