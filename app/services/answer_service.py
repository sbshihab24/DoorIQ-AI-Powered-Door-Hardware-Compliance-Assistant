from __future__ import annotations

import re

from app.schemas.chat import (
    ChatRequest,
    CodeReference,
    KnowledgeReference,
    RecommendedProduct,
)
from app.services.intent_service import normalize_intent
from app.services.llm_service import generate_llm_answer
from app.services.project_facts_service import ProjectFacts, extract_project_facts


def _opening_label(facts: ProjectFacts) -> str:
    parts = []
    for part in [facts.location_type, facts.building_type, facts.application]:
        if not part or part in parts:
            continue
        parts.append(part)
    label = " ".join(part for part in parts if part)
    if not label:
        return "this opening"
    return label.replace(" opening", "").strip()


def _article_for(label: str) -> str:
    return "an" if label[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def _opening_summary(
    request: ChatRequest,
    normalized_intent: str,
    fallback: str,
    facts: ProjectFacts,
) -> str:
    label = _opening_label(facts)

    if label != "this opening":
        return f"Dataset-grounded starting point for {_article_for(label)} {label}:"

    return fallback


def _bullet_list(values: list[str], limit: int = 3) -> str:
    selected_values = [value.rstrip(".") for value in values[:limit]]
    if not selected_values:
        return ""

    return "\n".join(f"- {value}" for value in selected_values)


def _requested_rating_minutes(text: str) -> str | None:
    match = re.search(r"\b(20|45|60|90)\s*(?:min|mins|minute|minutes)?\b", text)
    return match.group(1) if match else None


def _question_list(missing_information: list[str]) -> list[str]:
    question_by_field = {
        "building_type": "What type of building is it?",
        "location": "Is the opening interior or exterior?",
        "interior_exterior": "Is it an interior or exterior opening?",
        "rating": "Does the corridor/opening need a fire rating, such as 20, 45, 60, or 90 minutes?",
        "traffic": "Is it light, normal, or high traffic?",
        "material_preference": "Do you prefer hollow metal, wood, aluminum/storefront, or no preference?",
        "state": "What state is the project in?",
        "zip_code": "What ZIP code should I use for local code context?",
        "hardware_type": "What hardware do you need: closer, exit device, lockset, hinges, access control, or a full set?",
        "finish": "Do you have a finish preference?",
        "brand_preference": "Do you have a preferred hardware brand?",
        "wall_type": "What wall or barrier is this opening in: corridor wall, smoke barrier, fire barrier, stair enclosure, or something else?",
        "barrier_type": "What wall or barrier is this opening in: corridor wall, smoke barrier, fire barrier, stair enclosure, or something else?",
        "path_of_egress": "Is this door part of the egress path?",
        "egress_path": "Is this door part of the egress path?",
        "lock_type": "Will this use panic hardware, a latchset, access control, or another lock type?",
    }
    questions = []
    seen_questions = set()
    for field in missing_information:
        question = question_by_field.get(field, field.replace("_", " ").capitalize())
        if question in seen_questions:
            continue
        seen_questions.add(question)
        questions.append(question)

    return questions


def _product_summary(
    recommended_products: list[RecommendedProduct],
    missing_information: list[str],
    include_links: bool,
    request_text: str = "",
) -> str:
    if not recommended_products:
        return ""

    product_candidates = recommended_products
    if not include_links:
        product_candidates = [
            product
            for product in recommended_products
            if product.category in {"door", "frame"}
            and product.fire_rating
            and "not stated" not in product.fire_rating.lower()
        ]
        requested_rating = _requested_rating_minutes(request_text)
        if requested_rating:
            product_candidates = [
                product
                for product in product_candidates
                if requested_rating in product.fire_rating.lower()
                or "3 hour" in product.fire_rating.lower()
                or "3-hour" in product.fire_rating.lower()
            ]

    if not product_candidates:
        return ""

    product_lines = []
    for product in product_candidates[:3]:
        details = []
        if product.fire_rating:
            details.append(f"rating: {product.fire_rating}")
        if product.starting_price_usd:
            details.append(f"from ${product.starting_price_usd:g}")
        label = f"{product.name}"
        if details:
            label = f"{label} ({', '.join(details)})"
        if include_links and product.source_url:
            label = f"{label}\n  {product.source_url}"
        if product.notes:
            label = f"{label}\n  {product.notes}"
        product_lines.append(label)

    if not include_links:
        heading = "Door options to consider"
    else:
        heading = "Possible products" if missing_information else "Recommended products"
    return f"{heading}:\n{_bullet_list(product_lines)}"


def _source_summary(
    code_references: list[CodeReference],
    knowledge_references: list[KnowledgeReference],
) -> str:
    source_lines = []
    for reference in code_references[:2]:
        if reference.url:
            source_lines.append(f"{reference.title}\n  {reference.url}")

    if not source_lines:
        return ""

    return f"Code links:\n{_bullet_list(source_lines, limit=2)}"


def _missing_information_summary(missing_information: list[str]) -> str:
    if not missing_information:
        return "What I need next:\n- Nothing else for a first-pass recommendation"

    return f"What I need next:\n{_bullet_list(_question_list(missing_information), limit=6)}"


def _should_show_products(normalized_intent: str, request: ChatRequest) -> bool:
    text = request.message.lower()
    product_terms = ["product", "products", "options", "suggestion", "suggestions", "link", "links", "quote", "pricing", "price", "submittal"]
    return normalized_intent in {"product_match", "quote_handoff"} or any(
        term in text for term in product_terms
    )


def _should_suggest_product_families(
    normalized_intent: str,
    facts: ProjectFacts,
) -> bool:
    has_rating = facts.rating_required is not None or facts.rating_minutes is not None
    return (
        normalized_intent in {"door_type_recommendation", "fire_rating_analysis"}
        and facts.has_project_shape
        and has_rating
        and facts.location_type is not None
    )


def _dataset_guidance_summary(
    knowledge_references: list[KnowledgeReference],
    code_references: list[CodeReference],
) -> str:
    guidance_lines = []

    for reference in knowledge_references[:3]:
        guidance_lines.append(f"{reference.summary}\n  Source: {reference.source} / {reference.title}")

    for reference in code_references[:2]:
        source_line = reference.title
        if reference.url:
            source_line = f"{source_line} ({reference.url})"
        guidance_lines.append(f"{reference.summary}\n  Source: {source_line}")

    if not guidance_lines:
        return "Dataset guidance:\n- No exact dataset match found. Answer using any available code references above, then optionally ask for building type, state, and ZIP to refine further."

    return f"Dataset guidance:\n{_bullet_list(guidance_lines, limit=5)}"


def _llm_context(
    request: ChatRequest,
    intent: str,
    template_answer: str,
    requirements: list[str],
    allowed_options: list[str],
    risky_or_not_allowed: list[str],
    recommended_products: list[RecommendedProduct],
    code_references: list[CodeReference],
    knowledge_references: list[KnowledgeReference],
    missing_information: list[str],
) -> dict:
    return {
        "user_question": request.message,
        "intent": normalize_intent(intent),
        "template_answer": template_answer,
        "requirements": requirements,
        "allowed_options": allowed_options,
        "risky_or_not_allowed": risky_or_not_allowed,
        "recommended_products": [
            product.model_dump()
            for product in recommended_products[:5]
        ],
        "code_references": [
            reference.model_dump()
            for reference in code_references[:3]
        ],
        "knowledge_references": [
            reference.model_dump()
            for reference in knowledge_references[:3]
        ],
        "missing_information": missing_information,
        "rules": [
            "Use only the supplied context.",
            "Do not claim final local code certainty without jurisdiction verification.",
            "If context contains the answer, state it directly first with the code citation and source document.",
            "Only ask for missing details AFTER giving the direct answer from context, not before.",
            "Keep any product recommendation conditional on rating, egress, accessibility, and local amendments.",
            "If recommended products have URLs in the context, you MUST output them as a bulleted list with their exact clickable links. Do not summarize them into a sentence.",
        ],
    }


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
    facts = extract_project_facts(request)
    summary = _opening_summary(
        request,
        normalized_intent,
        "Dataset-grounded starting point:",
        facts,
    )

    answer_parts = [summary]

    answer_parts.append(
        _dataset_guidance_summary(
            knowledge_references=knowledge_references,
            code_references=code_references,
        )
    )

    show_products = _should_show_products(normalized_intent, request) or (
        not missing_information
        and normalized_intent in {"door_type_recommendation", "fire_rating_analysis"}
    )
    suggest_product_families = _should_suggest_product_families(normalized_intent, facts)
    include_product_links = show_products or suggest_product_families
    product_summary_candidates = recommended_products
    if suggest_product_families and not _should_show_products(normalized_intent, request):
        product_summary_candidates = [
            product
            for product in recommended_products
            if product.category in {"door", "frame"}
            and product.fire_rating
            and "not stated" not in product.fire_rating.lower()
        ]
    product_summary = _product_summary(
        product_summary_candidates,
        missing_information,
        include_links=include_product_links,
        request_text=request.message.lower(),
    )
    if product_summary and (show_products or suggest_product_families):
        answer_parts.append(product_summary)

    source_summary = _source_summary(code_references, knowledge_references)
    if source_summary:
        answer_parts.append(source_summary)

    answer_parts.append(_missing_information_summary(missing_information))

    template_answer = "\n\n".join(part for part in answer_parts if part)
    return generate_llm_answer(
        context=_llm_context(
            request=request,
            intent=intent,
            template_answer=template_answer,
            requirements=requirements,
            allowed_options=allowed_options,
            risky_or_not_allowed=risky_or_not_allowed,
            recommended_products=recommended_products,
            code_references=code_references,
            knowledge_references=knowledge_references,
            missing_information=missing_information,
        ),
        fallback_answer=template_answer,
    )
