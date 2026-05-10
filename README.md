# DoorIQ Chatbot

Backend chatbot API for United Doors & Hardware door, frame, hardware, product, and code-guidance questions. The included static page is only a local chatbot test harness.

## Local Python

Create or review `.env`:

```text
APP_NAME=DoorIQ Chatbot API
APP_ENV=development
APP_DEBUG=true
DATABASE_URL=sqlite:///./dooriq_local.db
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
GROQ_API_KEY=
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
LOCAL_EMBEDDING_DIMENSIONS=128
```

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Initialize or migrate the local SQLite database:

```powershell
.\.venv\Scripts\python.exe scripts\init_local_db.py
```

Run the API against local SQLite:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Run the API against the Docker pgvector PostgreSQL database:

```powershell
$env:DATABASE_URL="postgresql+psycopg://dooriq:dooriq_password@localhost:5433/dooriq"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

## Docker + pgvector

Start the app and pgvector database:

```powershell
docker compose up --build app
```

Open:

```text
http://127.0.0.1:8766/
```

The database is exposed on host port `5433` and container port `5432`.

## Database Modes

- SQLite is supported for tests and lightweight local development: `DATABASE_URL=sqlite:///./dooriq_local.db`.
- PostgreSQL with pgvector is the production target: `DATABASE_URL=postgresql+psycopg://...`.
- Always run `alembic upgrade head` before starting the production app.
- Use `scripts/init_local_db.py` for local SQLite so Alembic versioning stays in sync.

## Chatbot Data Boundary

DoorIQ answers are grounded in the processed dataset generated from `united_doors_ai_training_dataset.pdf`. The dataset says local-code precision requires ZIP, state, city/county/jurisdiction, adopted building code, fire code, accessibility code, amendment URL, AHJ contact when available, and last verification timestamp. Without those fields, exact code-section answers stay conditional.

Product recommendations use the dataset product fields only: name, category, compatible applications, fire rating, starting price, source URL when present, and notes.

## LLM Providers

The chatbot uses the current structured rule/retrieval pipeline first, then optionally asks an LLM to write the final answer.

Provider order:

1. OpenAI when `OPENAI_API_KEY` is set.
2. Groq when `GROQ_API_KEY` is set and OpenAI is not set.
3. Template fallback when neither key is set or the LLM call fails.

Example `.env` values:

```text
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4.1-mini
GROQ_API_KEY=
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
```

Groq is used through its OpenAI-compatible API at:

```text
https://api.groq.com/openai/v1
```

## Ingest Dataset

The processed dataset is generated from:

```text
united_doors_ai_training_dataset.pdf
```

Regenerate processed JSON and ingest vector chunks into Postgres:

```powershell
docker compose --profile ingest run --rm ingest
```

This runs:

```text
alembic upgrade head
python scripts/ingest_dataset.py
python scripts/ingest_chunks.py
```

Expected result:

```text
Ingested 38 document chunks.
```

## Useful Checks

Verify pgvector is enabled:

```powershell
docker compose exec db psql -U dooriq -d dooriq -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Verify chunks are stored as vectors:

```powershell
docker compose exec db psql -U dooriq -d dooriq -c "SELECT count(*) AS document_chunks, pg_typeof(embedding) AS embedding_type FROM document_chunks GROUP BY pg_typeof(embedding);"
```

## Demo Questions

- What code applies to a school entrance in my state?
- Can I use a maglock and a panic bar together?
- What products on your site fit a 90-minute corridor pair?
- Do I need an automatic operator on a hospital entrance door?
- Can I electrify this fire-rated opening?
- What information do you need before giving an exact answer?
