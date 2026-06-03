from pathlib import Path
import sys
import hashlib
# pyrefly: ignore [missing-import]
from pypdf import PdfReader


# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.services.chunk_ingestion_service import ingest_knowledge_chunks, upsert_document_chunk


def chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    """Simple chunking by character count, trying to break at newlines."""
    chunks = []
    while len(text) > max_chars:
        split_pos = text.rfind("\n", 0, max_chars)
        if split_pos == -1:
            split_pos = text.rfind(". ", 0, max_chars)
        if split_pos == -1:
            split_pos = max_chars
        
        chunks.append(text[:split_pos].strip())
        text = text[split_pos:].strip()
    
    if text:
        chunks.append(text)
    return chunks


def ingest_pdfs(db: Session) -> int:
    pdf_files = [
        "detailed_us_door_codes_reference 2.pdf",
        "detailed_us_door_codes_reference.pdf",
    ]
    total_chunks = 0
    for pdf_name in pdf_files:
        pdf_path = PROJECT_ROOT / pdf_name
        if not pdf_path.exists():
            continue
        
        print(f"Reading {pdf_name}...")
        reader = PdfReader(pdf_path)
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if not text.strip():
                continue
            
            sub_chunks = chunk_text(text)
            for j, chunk_content in enumerate(sub_chunks):
                stable_id = f"pdf-{hashlib.md5(pdf_name.encode()).hexdigest()[:8]}-p{i}-c{j}"
                
                chunk_data = {
                    "id": stable_id,
                    "title": f"{pdf_name} - Page {i+1} (Part {j+1})",
                    "source": pdf_name,
                    "content": chunk_content,
                    "tags": ["code", "pdf-reference"],
                }
                
                upsert_document_chunk(db, chunk_data)
                total_chunks += 1
                
        db.commit()
    return total_chunks


def main() -> None:
    db = SessionLocal()
    try:
        json_count = ingest_knowledge_chunks(db)
        print(f"Ingested {json_count} document chunks from JSON.")
        
        pdf_count = ingest_pdfs(db)
        print(f"Ingested {pdf_count} document chunks from PDFs.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
