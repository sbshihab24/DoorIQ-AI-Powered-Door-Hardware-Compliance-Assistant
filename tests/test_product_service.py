from app.services.product_service import (
    find_products_for_application,
    get_product_match_reason,
)


def test_find_products_for_egress_application() -> None:
    products = find_products_for_application("egress door")

    product_names = [product.name for product in products]
    assert "Rim Exit Device" in product_names
    assert "Surface Door Closer" in product_names


def test_find_products_returns_empty_list_without_application() -> None:
    assert find_products_for_application(None) == []


def test_find_products_for_masonry_frame_application() -> None:
    products = find_products_for_application("masonry opening frame")

    product_names = [product.name for product in products]
    assert "KD Masonry Frame" in product_names


def test_find_products_for_hospital_corridor_application() -> None:
    products = find_products_for_application("hospital corridor double egress")

    product_names = [product.name for product in products]
    assert "Double Egress Hollow Metal Frame" in product_names


def test_find_products_ranks_specific_panic_hardware_first() -> None:
    products = find_products_for_application("panic hardware for exit")

    assert products[0].name == "Accentra 2100 Series Rim Exit Device"


def test_find_products_limits_results() -> None:
    products = find_products_for_application("commercial fire rated egress door", limit=2)

    assert len(products) == 2


def test_find_products_uses_partial_application_matches() -> None:
    products = find_products_for_application("need hardware for a fire door")

    product_names = [product.name for product in products]
    assert "600 Series Heavy Duty Door Closer" in product_names


def test_get_product_match_reason_for_application_match() -> None:
    product = find_products_for_application("masonry opening frame")[0]

    reason = get_product_match_reason(product, "masonry opening frame")

    assert reason == "Matches the requested product category: frame."
