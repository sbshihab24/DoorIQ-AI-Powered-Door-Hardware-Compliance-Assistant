from app.schemas.chat import ChatRequest


LEAD_CAPTURE_KEYWORDS = [
    "call me",
    "contact me",
    "email me",
    "follow up",
    "quote",
    "pricing",
    "proposal",
]


def should_capture_lead(request: ChatRequest) -> bool:
    normalized_message = request.message.lower()

    if any(keyword in normalized_message for keyword in LEAD_CAPTURE_KEYWORDS):
        return True

    has_location = bool(request.location and request.location.state and request.location.zip_code)
    has_building_context = bool(
        request.building
        and request.building.building_type
        and request.building.application
    )

    return has_location and has_building_context
