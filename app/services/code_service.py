from app.schemas.code import CodeDocument


CODE_REFERENCES = [
    CodeDocument(
        id="egress-001",
        title="IBC Chapter 10 Means of Egress",
        content="Egress doors may require compliant swing, unlatching, panic or fire exit hardware depending on occupancy, occupant load, and use.",
        section="means of egress",
        url="https://codes.iccsafe.org/content/IBC2021P2/chapter-10-means-of-egress",
        tags=["egress_analysis", "egress", "exit", "panic hardware", "exit device"],
    ),
    CodeDocument(
        id="fire-rating-001",
        title="NFPA 80 Fire Door Guidance",
        content="Fire-rated openings require compatible labeled doors, frames, latching, closing hardware, and field modifications reviewed against the listed assembly.",
        section="fire rating",
        tags=["fire_rating_analysis", "fire_rating", "fire rated", "closer", "latching"],
    ),
    CodeDocument(
        id="accessibility-001",
        title="2010 ADA Standards Section 404 Doors, Doorways, and Gates",
        content="Accessible openings may require compliant clear width, maneuvering clearances, thresholds, opening force, and operable hardware.",
        section="accessibility",
        url="https://www.access-board.gov/ada/",
        tags=["accessibility_analysis", "accessibility", "ada", "automatic_operator_recommendation", "automatic operator"],
    ),
    CodeDocument(
        id="access-control-001",
        title="Access Control Door Guidance",
        content="Access control hardware must be reviewed with egress, fire rating, and local code requirements.",
        section="access control",
        tags=["maglock_analysis", "access_control", "maglock", "electric strike", "access control", "hardware_allowance"],
    ),
    CodeDocument(
        id="code-lookup-001",
        title="ICC Codes by Location",
        content="State, city, and county adopted code editions and amendments should be resolved before final local-code guidance.",
        section="jurisdiction lookup",
        url="https://codes.iccsafe.org/codes/united-states",
        tags=["applicable_code_lookup", "code_section_navigation", "local code"],
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
