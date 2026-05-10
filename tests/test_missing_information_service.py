from app.schemas.chat import ChatRequest
from app.schemas.common import BuildingContext
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


def test_missing_information_accepts_general_wall_and_barrier_phrases() -> None:
    for phrase in [
        "fire barrier",
        "2 hour smoke barrier",
        "corridor wall",
        "rated stair enclosure",
        "gypsum partition",
    ]:
        request = ChatRequest(
            message=(
                "I need doors for a school corridor renovation. "
                f"It is interior, 60 mins, and in a {phrase}."
            ),
            building=BuildingContext(
                building_type="school",
                application="corridor opening",
                fire_rating_required=True,
            ),
        )

        missing_information = get_missing_information_for_intent(
            request,
            "fire_rating_analysis",
        )

        assert "wall_type" not in missing_information
        assert "barrier_type" not in missing_information
