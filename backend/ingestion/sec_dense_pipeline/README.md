# SEC Dense Pipeline

Dense vector retrieval pipeline for SEC 10-K filings. Chunks filing markdown with structural awareness, embeds via OpenAI `text-embedding-3-large` (3072-dim), and stores in Qdrant.

## Quick Start

```bash
# 1. Start Qdrant
docker compose up -d qdrant

# 2. Batch ingest filings (downloads from EDGAR automatically; requires EDGAR_IDENTITY in env)
uv run python -m backend.scripts.embed_sec_filings NVDA AAPL INTC

# Optional: pin a fiscal year (default: latest 10-K per ticker)
uv run python -m backend.scripts.embed_sec_filings NVDA --year 2024

# 3. Search from Python
from backend.ingestion.sec_dense_pipeline.retriever import search
chunks = await search(query="NVIDIA export control risks", top_k=10)
```

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
| `EDGAR_IDENTITY` | _(required)_ | User-Agent string for SEC EDGAR API (e.g. `Company Name admin@company.com`). Required when JIT triggers an EDGAR download. |

## Error Hierarchy

Defined in `retriever.py`:

| Exception | Meaning | Retryable? |
|---|---|---|
| `EmbeddingServiceError` | OpenAI embedding API failure | Yes |
| `CorpusUnavailableError` | Qdrant connection, collection-missing, or non-404 HTTP error | Yes |
| `JITTickerNotFoundError` | Base class for EDGAR resolution failures | No |
| `JITInvalidTickerError` | EDGAR has no record of the ticker (subclass of `JITTickerNotFoundError`) | No |
| `JITFilingNotFoundError` | Ticker exists but no 10-K for the requested year (subclass of `JITTickerNotFoundError`) | No |
| `JITDisabledError` | JIT requested but `SEC_DISABLE_JIT=1` | No |
| `ConfigurationError` | Re-raised from `sec_filing_pipeline.filing_models` when EDGAR config is missing | No |

## JIT Ingest Contract

When `search()` receives a filter with `ticker` (and optionally `year`):

1. **Year resolution.** If `year` is specified, use it. If omitted, call `SECFilingPipeline.resolve_latest_year(ticker, "10-K")` — a cheap EDGAR metadata lookup — to learn the truly latest year. Local store is never consulted for "what is latest"; EDGAR is the source of truth.
2. **Embedding cache check.** Look up the (ticker, resolved_year) sentinel in Qdrant. If status is `complete`, JIT is skipped and search proceeds against existing embeddings.
3. **Filing acquisition.** On embedding miss: check `LocalFilingStore` for a cached `ParsedFiling`. If missing, call `pipeline.download_raw()` then `pipeline.parse_raw()` to fetch from EDGAR and persist the markdown locally.
4. **Ingestion.** Run `ingest_filing()` to chunk, embed, and upsert into Qdrant. Sentinel transitions `pending` → `complete`.
5. **Disable.** If `SEC_DISABLE_JIT=1` is set, all of the above is skipped and `JITDisabledError` is raised.

Error mapping: `TickerNotFoundError` from EDGAR becomes `JITInvalidTickerError`, `FilingNotFoundError` becomes `JITFilingNotFoundError` (both subclasses of `JITTickerNotFoundError` so a single `except JITTickerNotFoundError` still catches both). `ConfigurationError` propagates unchanged. Other `SECPipelineError` subtypes (e.g., `TransientError`) fall through to the outer handler and are wrapped as `CorpusUnavailableError`. Qdrant HTTP 404 responses also surface as `CorpusUnavailableError` via explicit `UnexpectedResponse.status_code` checking — no substring matching on error messages.

`EDGAR_IDENTITY` must be set whenever JIT may trigger an EDGAR call (which now includes the year-resolution lookup, even when local cache is warm).
