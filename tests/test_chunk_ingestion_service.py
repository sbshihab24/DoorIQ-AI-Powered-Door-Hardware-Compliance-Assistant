from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.services.chunk_ingestion_service import ingest_knowledge_chunks
from app.services.retrieval_service import find_relevant_knowledge_from_db


def test_ingest_knowledge_chunks_upserts_generated_chunks(db_session: Session) -> None:
    count = ingest_knowledge_chunks(db_session)

    chunks = db_session.query(DocumentChunk).all()

    assert count == 38
    assert len(chunks) == 38
    assert chunks[0].embedding is not None
    assert len(chunks[0].embedding) > 0
    assert chunks[0].embedding_model.startswith("local-hash-")


def test_ingest_knowledge_chunks_is_idempotent(db_session: Session) -> None:
    ingest_knowledge_chunks(db_session)
    ingest_knowledge_chunks(db_session)

    assert db_session.query(DocumentChunk).count() == 38


def test_find_relevant_knowledge_from_db_uses_ingested_chunks(db_session: Session) -> None:
    ingest_knowledge_chunks(db_session)

    snippets = find_relevant_knowledge_from_db(
        db_session,
        "What door frame should I use for a masonry opening?",
        "product_match",
    )

    titles = [snippet.title for snippet in snippets]
    assert "Seed QA: What door frame should I use for a masonry opening" in titles
