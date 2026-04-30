from functools import lru_cache
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


@lru_cache
def load_processed_json(file_name: str) -> list[dict[str, Any]]:
    file_path = PROCESSED_DATA_DIR / file_name
    with file_path.open(encoding="utf-8") as data_file:
        data = json.load(data_file)

    if not isinstance(data, list):
        raise ValueError(f"{file_name} must contain a JSON array.")

    return data
