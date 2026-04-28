INTENT_KEYWORDS = {
    "access_control": ["access control", "maglock", "magnetic lock", "electric strike"],
    "accessibility": ["ada", "accessible", "handicap", "automatic operator"],
    "code": ["code", "compliance", "section", "requirement"],
    "egress": ["egress", "exit", "panic hardware", "exit device"],
    "fire_rating": ["fire rated", "fire rating", "rated door", "smoke"],
    "hardware": ["hardware", "closer", "hinge", "lock", "operator"],
}


def detect_intent(message: str) -> str:
    normalized_message = message.lower()

    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in normalized_message for keyword in keywords):
            return intent

    return "general"
