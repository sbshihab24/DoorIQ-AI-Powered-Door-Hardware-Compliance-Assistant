from app.services.product_service import find_products_for_application


def test_find_products_for_egress_application() -> None:
    products = find_products_for_application("egress door")

    product_names = [product.name for product in products]
    assert "Rim Exit Device" in product_names
    assert "Surface Door Closer" in product_names


def test_find_products_returns_empty_list_without_application() -> None:
    assert find_products_for_application(None) == []
