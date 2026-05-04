from __future__ import annotations

import hashlib
import math
import re

from openai import OpenAI

from app.core.config import settings


def get_embedding_model_name() -> str:
    if settings.openai_api_key:
        return settings.embedding_model

    return f"local-hash-{settings.local_embedding_dimensions}"


def _local_embedding(text: str) -> list[float]:
    dimensions = settings.local_embedding_dimensions
    vector = [0.0] * dimensions
    tokens = re.findall(r"[a-z0-9]+", text.lower())

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector

    return [value / magnitude for value in vector]


def embed_text(text: str) -> list[float]:
    if not settings.openai_api_key:
        return _local_embedding(text)

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return list(response.data[0].embedding)


def cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    if left is None or right is None or len(left) == 0 or len(right) == 0 or len(left) != len(right):
        return 0.0

    left_magnitude = math.sqrt(sum(value * value for value in left))
    right_magnitude = math.sqrt(sum(value * value for value in right))
    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_magnitude * right_magnitude)
