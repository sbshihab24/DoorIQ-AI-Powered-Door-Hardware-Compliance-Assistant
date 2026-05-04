from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

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
