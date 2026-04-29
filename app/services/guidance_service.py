from dataclasses import dataclass


@dataclass(frozen=True)
class IntentGuidance:
    requirements: list[str]
    allowed_options: list[str]
    risky_or_not_allowed: list[str]


GUIDANCE_BY_INTENT = {
    "access_control": IntentGuidance(
        requirements=[
            "Confirm whether the door is part of an egress path.",
            "Confirm fire rating and local code limits before selecting locking hardware.",
        ],
        allowed_options=[
            "Access control lock reviewed with egress requirements.",
            "Electric strike or controlled entry hardware when code conditions are met.",
        ],
        risky_or_not_allowed=[
            "Magnetic lock without confirming release and egress requirements.",
        ],
    ),
    "accessibility": IntentGuidance(
        requirements=[
            "Confirm whether the opening is on an accessible route.",
            "Review clear opening, approach clearance, and operator needs.",
        ],
        allowed_options=[
            "Automatic operator where accessibility or user needs require it.",
            "Lever-style hardware suitable for accessible operation.",
        ],
        risky_or_not_allowed=[
            "Hardware that is difficult to operate or blocks required clearances.",
        ],
    ),
    "egress": IntentGuidance(
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
    "fire_rating": IntentGuidance(
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
    "hardware": IntentGuidance(
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
}


def get_guidance_for_intent(intent: str) -> IntentGuidance:
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
