from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.services.data_loader import load_processed_json
from app.services.embedding_service import embed_text, get_embedding_model_name


REQUIRED_CHUNK_FIELDS = {"id", "title", "source", "content"}


def _stable_chunk_id(chunk_data: dict[str, Any]) -> str:
    raw_id = chunk_data.get("id")
    if isinstance(raw_id, str) and raw_id:
        return raw_id

    stable_text = "|".join(
        str(chunk_data.get(field, ""))
        for field in ["source", "title", "content"]
    )
    digest = hashlib.sha256(stable_text.encode("utf-8")).hexdigest()[:16]
    return f"chunk-{digest}"


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _metadata_for_chunk(chunk_data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in chunk_data.items()
        if key not in REQUIRED_CHUNK_FIELDS and key != "tags"
    }


def upsert_document_chunk(db: Session, chunk_data: dict[str, Any]) -> DocumentChunk:
    content = str(chunk_data.get("content", "")).strip()
    if not content:
        raise ValueError("Document chunk content cannot be empty.")

    chunk_id = _stable_chunk_id(chunk_data)
    content_hash = _content_hash(content)
    embedding_model = get_embedding_model_name()
    existing_chunk = db.get(DocumentChunk, chunk_id)

    should_embed = (
        existing_chunk is None
        or existing_chunk.content_hash != content_hash
        or existing_chunk.embedding_model != embedding_model
        or not existing_chunk.embedding
    )
    embedding = (
        embed_text(content)
        if should_embed
        else existing_chunk.embedding
    )

    if existing_chunk is None:
        existing_chunk = DocumentChunk(id=chunk_id)
        db.add(existing_chunk)

    existing_chunk.title = str(chunk_data.get("title", chunk_id))
    existing_chunk.source = str(chunk_data.get("source", "unknown"))
    existing_chunk.content = content
    existing_chunk.tags = list(chunk_data.get("tags") or [])
    existing_chunk.chunk_metadata = _metadata_for_chunk(chunk_data)
    existing_chunk.content_hash = content_hash
    existing_chunk.embedding = embedding
    existing_chunk.embedding_model = embedding_model

    return existing_chunk


def ingest_knowledge_chunks(db: Session, file_name: str = "knowledge_chunks.json") -> int:
    chunks = load_processed_json(file_name)

    for chunk_data in chunks:
        upsert_document_chunk(db, chunk_data)

    db.commit()
    return len(chunks)
