from app.db.session import SessionLocal
from app.services.chunk_ingestion_service import ingest_knowledge_chunks


def main() -> None:
    db = SessionLocal()
    try:
        count = ingest_knowledge_chunks(db)
    finally:
        db.close()

    print(f"Ingested {count} document chunks.")


if __name__ == "__main__":
    main()
