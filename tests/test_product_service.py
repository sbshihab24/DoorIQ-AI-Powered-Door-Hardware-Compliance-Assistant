from app.services.product_service import find_products_for_application


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
