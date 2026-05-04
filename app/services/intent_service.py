from app.services.seed_qa_service import find_seed_qa_for_question, get_primary_seed_intent


INTENT_KEYWORDS = {
    "maglock_analysis": [
        "maglock",
        "mag lock",
        "magnetic lock",
        "electromagnetic lock",
    ],
    "delayed_egress_analysis": ["delayed egress", "delay egress"],
    "sliding_door_analysis": ["sliding door", "pocket door", "bifold", "bi-fold"],
    "automatic_operator_recommendation": [
        "automatic operator",
        "door operator",
        "low-energy operator",
        "low energy operator",
    ],
    "accessibility_analysis": [
        "ada",
        "accessible",
        "accessibility",
        "handicap",
        "clear width",
        "latch-side clearance",
        "latch side clearance",
        "revolving door",
    ],
    "fire_rating_analysis": [
        "fire rated",
        "fire-rated",
        "fire rating",
        "rated door",
        "rated opening",
        "smoke",
        "stair enclosure",
        "corridor door",
    ],
    "egress_analysis": [
        "egress",
        "exit",
        "panic hardware",
        "exit device",
        "panic bar",
        "door swing",
        "balanced door",
    ],
    "code_section_navigation": [
        "exact code section",
        "code section",
        "section covers",
        "take me to",
    ],
    "applicable_code_lookup": [
        "what code applies",
        "code applies",
        "local code",
        "state code",
        "city code",
        "compliance",
        "jurisdiction",
    ],
    "product_match": [
        "product",
        "products",
        "show me",
        "options",
        "frame should",
        "door frame",
        "metal building",
        "hinge",
        "closer",
        "lockset",
        "wood door with glass",
    ],
    "hardware_allowance": [
        "hardware",
        "closer",
        "hinge",
        "lock",
        "lockset",
        "electric strike",
        "electrify",
    ],
    "door_type_recommendation": [
        "what door",
        "door can be used",
        "door should",
        "best door",
        "door type",
        "entrance door",
        "double egress frame",
    ],
    "quote_handoff": ["quote", "pricing", "submittal", "price"],
}

INTENT_ALIASES = {
    "access_control": "maglock_analysis",
    "accessibility": "accessibility_analysis",
    "code": "applicable_code_lookup",
    "egress": "egress_analysis",
    "fire_rating": "fire_rating_analysis",
    "hardware": "hardware_allowance",
}

LEGACY_INTENTS = {value: key for key, value in INTENT_ALIASES.items()}


def detect_intent(message: str) -> str:
    seed_qa = find_seed_qa_for_question(message)
    if seed_qa is not None:
        seed_intent = get_primary_seed_intent(seed_qa)
        return LEGACY_INTENTS.get(seed_intent, seed_intent)

    normalized_message = message.lower()

    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in normalized_message for keyword in keywords):
            return LEGACY_INTENTS.get(intent, intent)

    return "general"


def normalize_intent(intent: str) -> str:
    return INTENT_ALIASES.get(intent, intent)
