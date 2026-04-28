from app.schemas.product import Product


PRODUCT_CATALOG = [
    Product(
        id="exit-device-001",
        name="Rim Exit Device",
        category="exit device",
        description="Panic or fire exit hardware for egress doors.",
        compatible_applications=["egress", "exit", "commercial door"],
    ),
    Product(
        id="closer-001",
        name="Surface Door Closer",
        category="closer",
        description="Self-closing hardware for commercial doors.",
        compatible_applications=["fire rated", "egress", "commercial door"],
    ),
    Product(
        id="operator-001",
        name="Automatic Door Operator",
        category="operator",
        description="Automatic opening support for accessible entrances.",
        compatible_applications=["accessible route", "entrance", "ada"],
    ),
    Product(
        id="access-control-001",
        name="Access Control Lock",
        category="access control",
        description="Electronic locking option for controlled access doors.",
        compatible_applications=["secured entry", "access control", "entrance"],
    ),
    Product(
        id="door-001",
        name="Hollow Metal Door",
        category="door",
        description="Common commercial door type for durable openings.",
        compatible_applications=["commercial door", "fire rated", "egress"],
    ),
    Product(
        id="frame-001",
        name="Hollow Metal Frame",
        category="frame",
        description="Commercial frame commonly paired with hollow metal doors.",
        compatible_applications=["commercial door", "fire rated", "egress"],
    ),
]


def find_products_for_application(application: str | None) -> list[Product]:
    if not application:
        return []

    normalized_application = application.lower()

    return [
        product
        for product in PRODUCT_CATALOG
        if any(
            compatible_application in normalized_application
            for compatible_application in product.compatible_applications
        )
    ]
