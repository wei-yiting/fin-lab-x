# SEC Dense Pipeline (structured contract)

Ingest and JIT-retrieval stages of the new RAG path: consumes the typed
`ParsedFiling` produced by `sec_text_pipeline`, upserts chunk points into the
new-contract Qdrant collection, and serves semantic search over it. Coexists
with the frozen `sec_dense_pipeline_html` baseline (A/B) and deliberately
shares no code with it — the frozen tree is deleted whole at sunset.

| Module | Responsibility |
| --- | --- |
| `chunking.py` | `build_chunk_payloads(filing)` — pure, per-block token chunking (512/50, boundaries never cross a block) into full payload dicts; global `chunk_index`; deterministic `chunk_point_id`. |
| `vectorizer.py` | `ingest_filing(filing: ParsedFiling)` — commit-marker lifecycle (`pending` → wipe → embed → upsert → `complete`), OpenAI embeddings, direct `PointStruct` upserts. |
| `retriever.py` | `search(query, filters, top_k)` — the single JIT query entry point: commit-marker check, in-process concurrency claim, parse/ingest on a miss, then a filtered Qdrant query. See [JIT retrieval](#jit-retrieval-retrieverpy) below. |
| `collection_schema.py` | Race-safe collection + payload-index bootstrap (`ticker` tenant / `fiscal_year` / `item`). |
| `common.py` | Marker helpers (`commit_marker_id`, `check_commit_marker_complete`, `marker_status_condition`) + `canonicalize_ticker` — the primitives the retrieval side builds on. |

## Payload schema (per chunk)

`ticker`, `fiscal_year`, `filing_date`, `filing_type`, `item` (normalized key,
e.g. `7a`), `block_heading`, `prelude`, `header_path` (no Part level),
`chunk_index` (filing-wide), `text`, `ingested_at`, plus the citation chain
fields `accession_number` / `cik` / `primary_document` (denormalized per chunk;
EDGAR URLs are always derived, never stored).

A valid prelude (≤3,000 chars, gated upstream by the detection layer) is both
searchable and contextual: it produces its own heading-less leading chunk —
same path as a FlatItem body or a reclassified leading block, so financial
content that lands in a prelude never disappears from the index — and it is
additionally attached whole to every *block* chunk of its Item as
retrieve-time context. The validity threshold governs only that metadata
attachment, never search visibility. `prelude` and `block_heading` are `None`
on every leading chunk (prelude-own, FlatItem, reclassified) and on block
chunks of items without a valid prelude.

## Configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `SEC_TEXT_QDRANT_COLLECTION` | `sec_filings_openai_large_dense_text` | New-contract Qdrant collection name (test isolation; A/B run switching). |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant endpoint (alternate local/eval instances). |
| `SEC_DISABLE_JIT` | unset | Set to `1` to block genuine JIT work (a marker miss, or resolving an omitted `fiscal_year` via EDGAR) in `retriever.search()`; set in CI so no test can reach real EDGAR. An already-ingested hot hit still succeeds regardless. |

Chunking (512/50 tokens, cl100k_base) and embedding (`text-embedding-3-large`,
3072 dims) are fixed module constants, not runtime knobs — they are part of the
collection's contract and of A/B comparability. To experiment, change the
constant in code (recorded in git) and re-ingest.

Extension note: any change to the payload filter fields must be applied in
lockstep to payload construction (`chunking.py`), the payload-index bootstrap
(`collection_schema.py`), the marker exclusion (`common.py`), and the retrieval
side.

## Integrity: commit marker

One marker point per (ticker, fiscal_year), same collection as the chunks:
ingest starts by (over)writing it to `pending`, wipes previous content points,
and flips it to `complete` only after the last upsert. Retrieval treats
anything but `complete` as absent (committed or absent — a failed ingest looks
like no ingest), and every content query excludes marker points via
`marker_status_condition()`. A filing that chunks to zero payloads raises
`EmptyIngestError` before any marker/wipe mutation, so it stays absent to
readers. Re-running the ingest is the recovery path for anything not
already covered by this module's own retries: `ingest_filing` itself
carries none, `ingest_filing_with_retry` retries transient Qdrant failures
once, and the embedding client separately retries transient upstream
failures internally — see [JIT retrieval](#jit-retrieval-retrieverpy)'s
retry-boundaries note below for the full breakdown.

## JIT retrieval (`retriever.py`)

`search(query, filters, top_k)` is the single query entry point. `filters` is
a required parameter matching the `SearchFilters` shape: mandatory `ticker`,
optional `fiscal_year` (omitted resolves to the ticker's latest 10-K via
EDGAR). Python does not enforce type hints at runtime, so a caller that
still passes an absent, empty, or ticker-less `filters` value gets a
`ValueError` before any Qdrant or EDGAR work runs — an unfiltered,
collection-wide search is a proven-harmful retrieval mode with no legitimate
production caller. Unknown filter keys (e.g. a leftover `year` key) and
wrong-typed `ticker`/`fiscal_year` values are rejected the same way, at the
same boundary (`_validate_filters()`), so a caller-input mistake never gets
misreported as a vector-store failure.

**Hot/cold flow:** every call checks the (ticker, fiscal_year) commit marker
first.

- **Hot** (marker `complete`): search Qdrant directly — no parsing or embedding.
- **Cold** (marker missing or `pending`): parse the filing
  (`parse_filing_with_retry`), ingest it (`ingest_filing_with_retry`), then
  search — all within the one `search()` call.

**In-process concurrency:** `_inflight_ingests` is a module-level set of
(ticker, fiscal_year) pairs currently being JIT-ingested. A second concurrent
call for the same key gets an immediate `IngestionInProgressError` — no
coalescing or waiting (envelope §1: single backend process, ≤3 concurrent
users). The commit marker is re-checked right after claiming the slot, so a
caller that raced a concurrent committer gets a clean hot hit instead of a
redundant re-ingest.

**Error mapping** — `search()` raises:

| Exception | When |
| --- | --- |
| `ValueError` | Bad `top_k`, or a `filters` shape/type rejected by `_validate_filters()` |
| `JITDisabledError` | `SEC_DISABLE_JIT=1` blocks a genuine marker miss or latest-year resolution |
| `IngestionInProgressError` | Another in-process JIT ingest already holds this (ticker, fiscal_year) |
| `EmbeddingServiceError` | Query embedding failed |
| `CorpusUnavailableError` | Qdrant/vector-store failure, including a missing collection |
| `FinLabError` subclasses (`TickerNotFoundError`, `FilingNotFoundError`, `EmptyFilingError`, etc.) | Propagated unwrapped from `parse_filing`/EDGAR — never swallowed into a generic error |

**Retry boundaries:** `parse_filing_with_retry` and
`resolve_latest_fiscal_year_with_retry` each carry one `retry_transient`
retry around their EDGAR call; Qdrant connection/timeout failures and 5xx
responses get one retry inside `ingest_filing_with_retry` (see
`vectorizer.py`'s `_TRANSIENT_SOURCE_TYPES`). Embedding relies on the OpenAI
SDK's own internal retry — no additional wrapper.
