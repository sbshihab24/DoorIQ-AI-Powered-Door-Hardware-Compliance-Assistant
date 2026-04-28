from app.services.intent_service import detect_intent


def test_detects_egress_intent() -> None:
    assert detect_intent("Do I need panic hardware on this exit?") == "egress"


def test_detects_access_control_intent() -> None:
    assert detect_intent("Can I use a maglock here?") == "access_control"


def test_returns_general_when_no_keyword_matches() -> None:
    assert detect_intent("I need help choosing a door.") == "general"
