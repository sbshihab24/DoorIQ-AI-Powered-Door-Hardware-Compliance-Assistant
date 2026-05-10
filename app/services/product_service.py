import re

from app.schemas.product import Product
from app.services.data_loader import load_processed_json


DEFAULT_PRODUCT_LIMIT = 5
GENERIC_MATCH_TOKENS = {
    "and",
    "door",
    "doors",
    "for",
    "need",
    "needs",
    "our",
    "recommendation",
    "that",
    "the",
    "this",
    "type",
    "with",
    "your",
}
GENERIC_CATEGORY_BOOST_EXCLUSIONS = {"door"}


def get_product_catalog() -> list[Product]:
    return [
        Product.model_validate(product_data)
        for product_data in load_processed_json("products.json")
    ]


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2
    }


def _score_product(query: str, product: Product) -> int:
    query_tokens = _tokenize(query) - GENERIC_MATCH_TOKENS
    product_text = " ".join(
        [
            product.name,
            product.category,
            product.description or "",
            " ".join(product.compatible_applications),
        ]
    )
    product_tokens = _tokenize(product_text)
    score = len(query_tokens & product_tokens)
    product_category = product.category.lower()

    if (
        product_category not in GENERIC_CATEGORY_BOOST_EXCLUSIONS
        and product_category in query
    ):
        score += 3

    for compatible_application in product.compatible_applications:
        normalized_compatible_application = compatible_application.lower()
        compatible_application_tokens = _tokenize(normalized_compatible_application)

        if normalized_compatible_application in query:
            score += 5

        score += len(query_tokens & compatible_application_tokens)

    return score


def get_product_match_reason(product: Product, query: str) -> str:
    normalized_query = query.lower()

    if (
        product.category.lower() not in GENERIC_CATEGORY_BOOST_EXCLUSIONS
        and product.category.lower() in normalized_query
    ):
        return f"Matches the requested product category: {product.category}."

    for compatible_application in product.compatible_applications:
        normalized_compatible_application = compatible_application.lower()

        if normalized_compatible_application in normalized_query:
            return f"Matches the application: {compatible_application}."

    query_tokens = _tokenize(normalized_query) - GENERIC_MATCH_TOKENS
    product_tokens = _tokenize(
        " ".join(
            [
                product.name,
                product.category,
                product.description or "",
                " ".join(product.compatible_applications),
            ]
        )
    )
    shared_terms = sorted(query_tokens & product_tokens)

    if shared_terms:
        return f"Matches related terms: {', '.join(shared_terms[:3])}."

    return "Matches the project context."


def find_products_for_application(
    application: str | None,
    limit: int = DEFAULT_PRODUCT_LIMIT,
) -> list[Product]:
    if not application:
        return []

    normalized_application = application.lower()
    scored_products = [
        (_score_product(normalized_application, product), product)
        for product in get_product_catalog()
    ]
    matching_products = [
        (score, product)
        for score, product in scored_products
        if score > 0
    ]

    matching_products.sort(key=lambda item: (-item[0], item[1].name))
    return [product for _, product in matching_products[:limit]]
