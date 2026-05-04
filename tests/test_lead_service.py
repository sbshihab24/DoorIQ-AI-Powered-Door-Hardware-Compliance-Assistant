from app.schemas.chat import ChatRequest
from app.services.lead_service import extract_email, extract_phone, should_capture_lead


def test_should_capture_lead_for_quote_request() -> None:
    request = ChatRequest(message="Can you send me a quote for this hardware?")

    assert should_capture_lead(request) is True


def test_should_capture_lead_when_project_context_is_complete() -> None:
    request = ChatRequest(
        message="What hardware should I use?",
        building={
            "building_type": "office",
            "application": "egress door",
        },
        location={
            "state": "TX",
            "zip_code": "75001",
        },
    )

    assert should_capture_lead(request) is True


def test_should_not_capture_lead_for_basic_incomplete_question() -> None:
    request = ChatRequest(message="What is a door closer?")

    assert should_capture_lead(request) is False


def test_extract_email_from_message() -> None:
    assert extract_email("Email me at Brian.Test+door@example.com please") == (
        "brian.test+door@example.com"
    )


def test_extract_phone_from_message() -> None:
    assert extract_phone("Call me at (555) 123-4567") == "(555) 123-4567"
