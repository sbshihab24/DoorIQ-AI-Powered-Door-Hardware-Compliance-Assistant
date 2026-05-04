from app.schemas.chat import ChatRequest
from app.services.missing_information_service import get_missing_information_for_intent


def test_missing_information_uses_dataset_entities_for_egress() -> None:
    request = ChatRequest(message="Do I need panic hardware?")

    assert get_missing_information_for_intent(request, "egress_analysis") == [
        "occupancy",
        "occupant_load",
        "path_of_egress",
        "lock_type",
    ]


def test_missing_information_recognizes_maglock_egress_context() -> None:
    request = ChatRequest(
        message="Can I use a maglock on this egress door?",
        building={"application": "egress door"},
    )

    missing_information = get_missing_information_for_intent(
        request,
        "maglock_analysis",
    )

    assert "door_type" not in missing_information
    assert "egress_path" not in missing_information
    assert "access_control_intent" not in missing_information
    assert "occupancy" in missing_information
    assert "rating" in missing_information


def test_missing_information_keeps_unknown_future_entities_visible() -> None:
    request = ChatRequest(message="I need a door recommendation.")

    assert get_missing_information_for_intent(request, "unknown_future_intent") == [
        "building_type",
        "application",
        "state",
        "zip_code",
    ]
