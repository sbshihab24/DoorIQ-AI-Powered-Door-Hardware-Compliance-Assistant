from app.services.data_loader import load_processed_json
from app.services.product_service import get_product_catalog
from app.services.retrieval_service import get_knowledge_base


def test_load_processed_json_reads_products() -> None:
    products = load_processed_json("products.json")

    assert isinstance(products, list)
    assert any(product["name"] == "KD Masonry Frame" for product in products)


def test_product_catalog_loads_from_processed_data() -> None:
    product_names = [product.name for product in get_product_catalog()]

    assert "Accentra 2100 Series Rim Exit Device" in product_names


def test_knowledge_base_loads_from_processed_data() -> None:
    snippet_titles = [snippet.title for snippet in get_knowledge_base()]

    assert "Dataset Implementation Note" in snippet_titles


def test_generated_dataset_files_match_pdf_counts() -> None:
    products = load_processed_json("products.json")
    hardware = load_processed_json("hardware.json")
    intents = load_processed_json("intents.json")
    seed_qa = load_processed_json("seed_qa.json")
    knowledge_chunks = load_processed_json("knowledge_chunks.json")

    assert len(products) == 45
    assert len(hardware) == 19
    assert len(intents) == 14
    assert len(seed_qa) == 30
    assert len(knowledge_chunks) >= len(seed_qa)
