import re


GREETING_MESSAGES = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
}

DOORIQ_DOMAIN_KEYWORDS = [
    "ada",
    "access",
    "accessible",
    "building",
    "closer",
    "code",
    "commercial",
    "corridor",
    "door",
    "exact answer",
    "egress",
    "entrance",
    "exit",
    "fire",
    "frame",
    "hardware",
    "hinge",
    "hospital",
    "lock",
    "maglock",
    "operator",
    "panic",
    "rated",
    "school",
    # Code standard acronyms — must never be classified as out_of_scope
    "ibc",
    "irc",
    "nfpa",
    "ifc",
    "cbc",
    "ansi",
    "bhma",
    "a117",
    "section",
    "occupancy",
    "occupant",
    # Topics from PDF reference documents
    "glass",
    "glazing",
    "sidelight",
    "residential",
    "garage",
    "landing",
    "threshold",
    "clearance",
    "maneuvering",
    "leaf",
    "assembly",
    "educational",
    "width",
    "height",
    "swing",
    "self-closing",
    "latched",
    "label",
]

QUESTION_STARTERS = (
    "can ",
    "could ",
    "does ",
    "do ",
    "how ",
    "is ",
    "should ",
    "what ",
    "when ",
    "where ",
    "which ",
    "who ",
    "why ",
)


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
        "maneuvering clearance",
        "pull side",
        "push side",
        "grasping",
        "pinching",
        "twisting",
        "threshold height",
        "revolving door",
    ],
    "fire_rating_analysis": [
        "fire rate",
        "fire rated",
        "fire-rated",
        "fire rating",
        "rated door",
        "rated opening",
        "smoke",
        "stair enclosure",
        "corridor door",
        "self-closing",
        "positively latched",
        "nfpa 80",
        "ibc 716",
        "wall assembly",
        "fire label",
        "fire separation",
    ],
    "egress_analysis": [
        "egress",
        "exit",
        "panic hardware",
        "exit device",
        "panic bar",
        "door swing",
        "swing direction",
        "direction of egress",
        "balanced door",
        "ibc 1010",
        "irc r311",
        "occupant load",
        "landing",
        "unobstructed",
    ],
    "code_section_navigation": [
        "exact code section",
        "code section",
        "section covers",
        "take me to",
        "ibc",
        "irc",
        "nfpa",
        "ifc",
        "cbc",
        "ansi",
        "bhma",
        "a117",
        "florida building code",
        "california building code",
        "nyc code",
        "ohio building code",
        "what does",
        "what do",
        "source document",
        "according to",
        "r308",
        "r311",
        "404.2",
        "1010",
        "716",
        "leaf width",
        "maximum leaf",
        "minimum clear",
        "maximum width",
        "minimum width",
        "opening force",
        "threshold height",
        "clear opening",
        "minimum height",
        "maximum height",
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
        "suggestion",
        "suggestions",
        "show me",
        "options",
        "link",
        "links",
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
        "doors for",
        "need a door",
        "need an office door",
        "what door",
        "door can be used",
        "door should",
        "best door",
        "door type",
        "entrance door",
        "corridor renovation",
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

INTENT_TIEBREAK_ORDER = [
    "maglock_analysis",
    "delayed_egress_analysis",
    "sliding_door_analysis",
    "automatic_operator_recommendation",
    "accessibility_analysis",
    "fire_rating_analysis",
    "egress_analysis",
    "applicable_code_lookup",
    "code_section_navigation",
    "product_match",
    "hardware_allowance",
    "quote_handoff",
    "door_type_recommendation",
]


def detect_intent(message: str) -> str:
    normalized_message = message.strip().lower()
    normalized_compact_message = " ".join(normalized_message.split())

    if normalized_compact_message.rstrip("!.?") in GREETING_MESSAGES:
        return "greeting"

    if re.search(r"\b(20|45|60|90)\s*(?:min|mins|minute|minutes)\b", normalized_message):
        return LEGACY_INTENTS.get("fire_rating_analysis", "fire_rating_analysis")

    if "doors and hardware" in normalized_message and "required" in normalized_message:
        return LEGACY_INTENTS.get("door_type_recommendation", "door_type_recommendation")

    scored_intents = []
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in normalized_message)
        if score:
            scored_intents.append((score, INTENT_TIEBREAK_ORDER.index(intent), intent))

    if scored_intents:
        _, _, intent = max(scored_intents, key=lambda item: (item[0], -item[1]))
        return LEGACY_INTENTS.get(intent, intent)

    has_domain_context = any(
        keyword in normalized_message
        for keyword in DOORIQ_DOMAIN_KEYWORDS
    )
    looks_like_question = normalized_message.endswith("?") or normalized_message.startswith(
        QUESTION_STARTERS
    )
    if looks_like_question and not has_domain_context:
        return "out_of_scope"

    return "general"


def normalize_intent(intent: str) -> str:
    return INTENT_ALIASES.get(intent, intent)
