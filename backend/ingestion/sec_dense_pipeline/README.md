# SEC Dense Pipeline

Dense vector retrieval pipeline for SEC 10-K filings. Chunks filing markdown with structural awareness, embeds via OpenAI `text-embedding-3-large` (3072-dim), and stores in Qdrant.

## Key Components

- **`vectorizer.py`** -- Ingestion: parses markdown into section-aware chunks, generates embeddings, upserts into Qdrant. Manages sentinel points to track ingestion status per (ticker, year).
- **`retriever.py`** -- Search: embeds a query, runs vector similarity search against Qdrant, and returns ranked `Chunk` results. Supports JIT (just-in-time) ingestion when a requested filing is not yet indexed.

## Qdrant Payload Schema

Each **content point** stores:

| Field | Type | Description |
|---|---|---|
| `ticker` | keyword | Uppercased ticker symbol (e.g. `NVDA`) |
| `year` | integer | Fiscal year of the filing |
| `filing_date` | string | Filing date from SEC metadata |
| `filing_type` | string | Filing type (e.g. `10-K`) |
| `accession_number` | string/null | SEC accession number |
| `item` | keyword | Extracted Item number (e.g. `Item 1A`) |
| `header_path` | string | `TICKER / YEAR / Section / Subsection` path |
| `chunk_index` | integer | Sequential index within the filing |
| `text` | string | Chunk text content |
| `ingested_at` | string | ISO 8601 ingestion timestamp |

Each **sentinel point** stores `ticker`, `year`, and `status` (`"pending"` or `"complete"`).

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SEC_EMBED_MODEL` | `text-embedding-3-large` | OpenAI embedding model name |
| `SEC_EMBED_DIM` | `3072` | Embedding output dimension (must match model and Qdrant collection) |
| `SEC_CHUNK_SIZE` | `512` | Chunk size in tokens |
| `SEC_CHUNK_OVERLAP` | `50` | Chunk overlap in tokens |
| `SEC_QDRANT_COLLECTION` | `sec_filings_openai_large_dense_baseline` | Qdrant collection name |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `SEC_DISABLE_JIT` | _(unset)_ | Set to `1` to disable JIT ingestion |

## JIT Ingest Contract

When `search()` receives a filter with `ticker` (and optionally `year`):

1. If `year` is specified: check the sentinel for that exact (ticker, year). If missing or not complete, fetch and ingest.
2. If `year` is omitted: resolve the latest filing year from the local store, then check the sentinel for that year. If missing, ingest.
3. If `SEC_DISABLE_JIT=1` is set, JIT is skipped and `JITDisabledError` is raised instead.
