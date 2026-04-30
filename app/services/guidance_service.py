from dataclasses import dataclass


@dataclass(frozen=True)
class IntentGuidance:
    requirements: list[str]
    allowed_options: list[str]
    risky_or_not_allowed: list[str]


GUIDANCE_BY_INTENT = {
    "maglock_analysis": IntentGuidance(
        requirements=[
            "Confirm whether the door is part of an egress path.",
            "Confirm occupancy, fire rating, release method, and local code limits before selecting magnetic locking hardware.",
        ],
        allowed_options=[
            "Maglock reviewed against egress, fire alarm, sensor, and manual release requirements.",
            "Electric strike, electrified exit device, or controlled entry hardware when code conditions are met.",
        ],
        risky_or_not_allowed=[
            "Magnetic lock without confirming release and egress requirements.",
        ],
    ),
    "accessibility_analysis": IntentGuidance(
        requirements=[
            "Confirm whether the opening is on an accessible route.",
            "Review clear opening, maneuvering clearance, threshold, opening force, and operator needs.",
        ],
        allowed_options=[
            "Automatic operator where accessibility or user needs require it.",
            "Lever-style hardware suitable for accessible operation.",
        ],
        risky_or_not_allowed=[
            "Hardware that is difficult to operate or blocks required clearances.",
        ],
    ),
    "egress_analysis": IntentGuidance(
        requirements=[
            "Confirm occupancy, occupant load, and whether the door is in the exit path.",
            "Review panic or fire exit hardware needs for the specific opening.",
        ],
        allowed_options=[
            "Listed exit device where panic hardware is required.",
            "Closer and latch hardware compatible with the door use.",
        ],
        risky_or_not_allowed=[
            "Locking hardware that prevents free egress.",
        ],
    ),
    "fire_rating_analysis": IntentGuidance(
        requirements=[
            "Confirm required fire rating for the opening.",
            "Use compatible rated doors, frames, latching, and closing hardware.",
        ],
        allowed_options=[
            "Labeled hollow metal door and frame where rating is required.",
            "Listed closer and positive latching hardware.",
        ],
        risky_or_not_allowed=[
            "Non-labeled hardware on a rated opening.",
        ],
    ),
    "hardware_allowance": IntentGuidance(
        requirements=[
            "Confirm door application, traffic level, egress use, and rating needs.",
        ],
        allowed_options=[
            "Commercial-grade hinges, locks, closers, and exit devices matched to the opening.",
        ],
        risky_or_not_allowed=[
            "Choosing hardware before confirming egress and rating requirements.",
        ],
    ),
    "applicable_code_lookup": IntentGuidance(
        requirements=[
            "Collect state, ZIP, building type, and whether the work is new or existing.",
            "Resolve city, county, adopted code edition, and local amendments before giving exact code guidance.",
        ],
        allowed_options=[
            "Use ICC code-by-location sources, ADA guidance, and local amendment URLs as source metadata.",
        ],
        risky_or_not_allowed=[
            "Treating the starter dataset as the final official jurisdictional code source.",
        ],
    ),
    "door_type_recommendation": IntentGuidance(
        requirements=[
            "Confirm location, interior or exterior use, fire rating, traffic level, and material preference.",
        ],
        allowed_options=[
            "Hollow metal, wood, storefront, frame, or specialty door family matched to the opening.",
        ],
        risky_or_not_allowed=[
            "Recommending a door family before confirming rating and egress role.",
        ],
    ),
    "product_match": IntentGuidance(
        requirements=[
            "Confirm door type, hardware type, rating, finish, dimensions, and brand preference where relevant.",
        ],
        allowed_options=[
            "Match website catalog products to the opening requirements and explain tradeoffs.",
        ],
        risky_or_not_allowed=[
            "Product matching without verifying dimensions, rating labels, and local code conditions.",
        ],
    ),
    "sliding_door_analysis": IntentGuidance(
        requirements=[
            "Confirm occupancy, accessible route status, egress function, and whether a breakout or alternate swing door is provided.",
        ],
        allowed_options=[
            "Sliding, storefront slider, pocket, or bifold door only where egress and accessibility conditions are satisfied.",
        ],
        risky_or_not_allowed=[
            "Using a sliding door as required egress without confirming code allowances.",
        ],
    ),
    "delayed_egress_analysis": IntentGuidance(
        requirements=[
            "Confirm occupancy, security use case, sprinkler/fire alarm status, and AHJ requirements.",
        ],
        allowed_options=[
            "Delayed egress only where the adopted code and occupancy conditions allow it.",
        ],
        risky_or_not_allowed=[
            "Delayed egress on a life-safety path without AHJ and code review.",
        ],
    ),
    "automatic_operator_recommendation": IntentGuidance(
        requirements=[
            "Confirm entrance type, accessible-route status, user population, and power availability.",
        ],
        allowed_options=[
            "Manual, low-energy, or full-power operator recommendation based on usage and accessibility needs.",
        ],
        risky_or_not_allowed=[
            "Assuming an operator replaces required clear width, maneuvering clearance, or compliant hardware.",
        ],
    ),
    "code_section_navigation": IntentGuidance(
        requirements=[
            "Resolve the jurisdiction and code family before linking to an exact section.",
        ],
        allowed_options=[
            "Return a source URL and section-level citation when an official source is available.",
        ],
        risky_or_not_allowed=[
            "Providing exact local section text without confirming the adopted edition and amendments.",
        ],
    ),
}

INTENT_ALIASES = {
    "access_control": "maglock_analysis",
    "accessibility": "accessibility_analysis",
    "code": "applicable_code_lookup",
    "egress": "egress_analysis",
    "fire_rating": "fire_rating_analysis",
    "hardware": "hardware_allowance",
}


def get_guidance_for_intent(intent: str) -> IntentGuidance:
    intent = INTENT_ALIASES.get(intent, intent)

    return GUIDANCE_BY_INTENT.get(
        intent,
        IntentGuidance(
            requirements=[
                "Provide building type, application, state, and ZIP code for a better recommendation.",
            ],
            allowed_options=[],
            risky_or_not_allowed=[],
        ),
    )
