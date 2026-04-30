import re

from app.schemas.product import Product
from app.services.data_loader import load_processed_json


DEFAULT_PRODUCT_LIMIT = 5


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
    query_tokens = _tokenize(query)
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

    if product.category.lower() in query:
        score += 3

    for compatible_application in product.compatible_applications:
        normalized_compatible_application = compatible_application.lower()

        if normalized_compatible_application in query:
            score += 5

        if query in normalized_compatible_application:
            score += 2

    return score


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
