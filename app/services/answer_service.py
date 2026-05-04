from __future__ import annotations

from app.schemas.chat import (
    ChatRequest,
    CodeReference,
    KnowledgeReference,
    RecommendedProduct,
)
from app.services.intent_service import normalize_intent
from app.services.seed_qa_service import find_seed_qa_for_question


INTENT_SUMMARIES = {
    "maglock_analysis": "Maglocks are conditional: review egress role, release method, occupancy, fire rating, and local amendments before selecting access-control hardware.",
    "accessibility_analysis": "Accessibility depends on whether the opening is on an accessible route and on clear width, maneuvering clearance, threshold, force, and operable hardware.",
    "applicable_code_lookup": "Exact code guidance needs jurisdiction context, especially state, ZIP, adopted code edition, and local amendments.",
    "egress_analysis": "Egress hardware depends on occupancy, occupant load, exit-path use, unlatching rules, panic hardware needs, and local code.",
    "fire_rating_analysis": "Rated openings require compatible labeled doors, frames, glazing, latching, and closing hardware.",
    "hardware_allowance": "Hardware should be selected from the door use, egress role, rating, traffic level, and access-control intent.",
    "door_type_recommendation": "Door and frame selection depends on opening location, material, rating, traffic level, accessibility, and egress role.",
    "product_match": "Product matching should start with the opening type, rating, dimensions, finish, hardware family, and project constraints.",
    "sliding_door_analysis": "Sliding doors need review for occupancy, egress function, accessible-route status, and any required breakout or alternate swing door.",
    "delayed_egress_analysis": "Delayed egress is a life-safety condition that depends on occupancy, security use case, alarm/sprinkler conditions, and AHJ approval.",
    "automatic_operator_recommendation": "Automatic operator recommendations depend on entrance type, accessible-route requirements, user population, and power availability.",
    "code_section_navigation": "Exact code-section navigation requires the jurisdiction, adopted code family, edition, and amendment context.",
    "quote_handoff": "For quote handoff, package the project facts, selected products, jurisdiction, and contact details for follow-up.",
}


def _sentence_list(values: list[str], limit: int = 2) -> str:
    selected_values = [value.rstrip(".") for value in values[:limit]]
    if not selected_values:
        return ""

    return "; ".join(selected_values) + "."


def _product_summary(recommended_products: list[RecommendedProduct]) -> str:
    if not recommended_products:
        return ""

    product_names = [product.name for product in recommended_products[:3]]
    if len(product_names) == 1:
        return f"Relevant product match: {product_names[0]}."

    return f"Relevant product matches: {', '.join(product_names)}."


def _source_summary(
    code_references: list[CodeReference],
    knowledge_references: list[KnowledgeReference],
) -> str:
    source_titles = []
    for reference in [*code_references[:1], *knowledge_references[:2]]:
        source_titles.append(reference.title)

    if not source_titles:
        return ""

    return f"Grounded by: {', '.join(source_titles)}."


def _missing_information_summary(missing_information: list[str]) -> str:
    if not missing_information:
        return "I have the basic project context needed for a first-pass recommendation."

    readable_fields = [field.replace("_", " ") for field in missing_information]
    return f"To make this more precise, I still need: {', '.join(readable_fields)}."


def _seed_output_summary(request: ChatRequest) -> str:
    seed_qa = find_seed_qa_for_question(request.message)
    if seed_qa is None:
        return ""

    recommended_output = str(seed_qa.get("recommended_output", "")).lower()

    if "jurisdiction stack" in recommended_output:
        return "For exact code guidance, confirm the state and ZIP, then cite the governing jurisdiction stack and source URLs."
    if "manual vs low-energy vs full-power" in recommended_output:
        return "Compare manual, low-energy, and full-power operator paths before selecting an automatic operator."
    if "conditional answer + ahj" in recommended_output:
        return "This is conditional and should be treated as an AHJ-review item before final approval."
    if "conditional integration answer" in recommended_output:
        return "Treat the maglock and panic hardware combination as an integrated listed-hardware question, not as two separate parts."
    if "conditional allow + listed components only" in recommended_output:
        return "Electrified rated openings should use only listed components compatible with the labeled assembly."
    if "conditional allow / not allow" in recommended_output:
        return "Give this as a conditional allow-or-not-allow answer and include practical alternatives."
    if "matched product list" in recommended_output:
        return "Return this as a matched product list with the most relevant doors, frames, and hardware called out."
    if "website frame options" in recommended_output:
        return "Compare the website frame options and note the main pros, cons, rating, and wall-condition differences."
    if "website options" in recommended_output:
        return "Use website catalog options first, then add configuration notes for rating, size, finish, and hardware."
    if "exact section" in recommended_output:
        return "For section lookup, identify the likely code section and note that the adopted edition must be confirmed."
    if "state/zip" in recommended_output:
        return "For an exact answer, collect state/ZIP, building type, space type, rating status, access-control intent, and whether the work is new or existing."
    if "60%" in recommended_output:
        return "For new construction, the baseline accessibility path is at least 60% of public entrances, with project-specific caveats."
    if "separate compliant door" in recommended_output:
        return "A revolving door should not be treated as the accessible entrance by itself; plan for a separate compliant door."
    if "special maneuvering exception" in recommended_output:
        return "Check the patient-room maneuvering-clearance exception before applying the standard latch-side clearance rule."
    if "door/entrance package" in recommended_output:
        return "Package the answer around the entrance door type, operator path, panic or egress hardware, accessibility, and code links."

    return ""


def build_answer(
    request: ChatRequest,
    intent: str,
    requirements: list[str],
    allowed_options: list[str],
    risky_or_not_allowed: list[str],
    recommended_products: list[RecommendedProduct],
    code_references: list[CodeReference],
    knowledge_references: list[KnowledgeReference],
    missing_information: list[str],
) -> str:
    normalized_intent = normalize_intent(intent)
    summary = INTENT_SUMMARIES.get(
        normalized_intent,
        "I need more project details before I can give a reliable door and hardware recommendation.",
    )

    answer_parts = [summary]

    seed_output_summary = _seed_output_summary(request)
    if seed_output_summary:
        answer_parts.append(seed_output_summary)

    if requirements:
        answer_parts.append(f"Key requirements to confirm: {_sentence_list(requirements)}")

    if allowed_options:
        answer_parts.append(f"Likely viable path: {_sentence_list(allowed_options, limit=1)}")

    if risky_or_not_allowed:
        answer_parts.append(f"Watch-outs: {_sentence_list(risky_or_not_allowed, limit=1)}")

    product_summary = _product_summary(recommended_products)
    if product_summary:
        answer_parts.append(product_summary)

    source_summary = _source_summary(code_references, knowledge_references)
    if source_summary:
        answer_parts.append(source_summary)

    answer_parts.append(_missing_information_summary(missing_information))

    if normalized_intent in {"applicable_code_lookup", "code_section_navigation"}:
        answer_parts.append(
            "Treat this as guidance from the starter dataset until the adopted local code and amendments are verified."
        )

    return " ".join(part for part in answer_parts if part)
