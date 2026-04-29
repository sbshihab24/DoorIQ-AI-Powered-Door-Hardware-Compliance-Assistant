from app.schemas.code import CodeDocument


CODE_REFERENCES = [
    CodeDocument(
        id="egress-001",
        title="Egress Door Guidance",
        content="Egress doors may require panic or fire exit hardware depending on occupancy and use.",
        section="egress",
        tags=["egress", "exit", "panic hardware", "exit device"],
    ),
    CodeDocument(
        id="fire-rating-001",
        title="Fire-Rated Opening Guidance",
        content="Fire-rated openings require compatible labeled doors, frames, latching, and closing hardware.",
        section="fire rating",
        tags=["fire_rating", "fire rated", "closer", "latching"],
    ),
    CodeDocument(
        id="accessibility-001",
        title="Accessible Door Guidance",
        content="Accessible openings may require compliant clearances, opening force, and automatic operator review.",
        section="accessibility",
        tags=["accessibility", "ada", "automatic operator"],
    ),
    CodeDocument(
        id="access-control-001",
        title="Access Control Door Guidance",
        content="Access control hardware must be reviewed with egress, fire rating, and local code requirements.",
        section="access control",
        tags=["access_control", "maglock", "electric strike", "access control"],
    ),
]


def find_code_references(intent: str, state: str | None = None) -> list[CodeDocument]:
    matches = [
        code_reference
        for code_reference in CODE_REFERENCES
        if intent in code_reference.tags
    ]

    if matches:
        return matches

    if state:
        return [
            CodeDocument(
                id=f"state-{state.lower()}-review",
                title=f"{state.upper()} Local Code Review",
                content="State and local requirements should be verified for this opening.",
                state=state.upper(),
                section="local review",
                tags=["local code"],
            )
        ]

    return []
