# SEC Dense Pipeline (structured contract)

Ingest stage of the new RAG path: consumes the typed `ParsedFiling` produced by
`sec_text_pipeline` and upserts chunk points into the new-contract Qdrant
collection. Coexists with the frozen `sec_dense_pipeline_html` baseline (A/B)
and deliberately shares no code with it — the frozen tree is deleted whole at
sunset.

| Module | Responsibility |
| --- | --- |
| `chunking.py` | `build_chunk_payloads(filing)` — pure, per-block token chunking (512/50, boundaries never cross a block) into full payload dicts; global `chunk_index`; deterministic `chunk_point_id`. |
| `vectorizer.py` | `ingest_filing(filing: ParsedFiling)` — commit-marker lifecycle (`pending` → wipe → embed → upsert → `complete`), OpenAI embeddings, direct `PointStruct` upserts. |
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
readers. Re-running the ingest is the recovery path; there
is no retry wrapper inside (the embedding client already retries transient
failures internally).
