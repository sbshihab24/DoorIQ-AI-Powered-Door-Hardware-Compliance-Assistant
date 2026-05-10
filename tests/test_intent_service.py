from app.services.intent_service import detect_intent


def test_detects_egress_intent() -> None:
    assert detect_intent("Do I need panic hardware on this exit?") == "egress"


def test_detects_access_control_intent() -> None:
    assert detect_intent("Can I use a maglock here?") == "access_control"


def test_detects_door_recommendation_intent_for_office_door() -> None:
    assert detect_intent("I need a door for my office") == "door_type_recommendation"


def test_detects_dataset_specific_operator_intent() -> None:
    assert (
        detect_intent("Do I need an automatic operator on a hospital entrance door?")
        == "automatic_operator_recommendation"
    )


def test_detects_product_match_intent() -> None:
    assert detect_intent("What door frame should I use for a masonry opening?") == "product_match"


def test_detects_short_fire_rating_minutes() -> None:
    assert detect_intent("60 mins") == "fire_rating"


def test_detects_greeting_intent() -> None:
    assert detect_intent("hello") == "greeting"


def test_detects_unrelated_question_as_out_of_scope() -> None:
    assert detect_intent("What is the capital of France?") == "out_of_scope"
