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

`prelude` and `block_heading` are `None` when the schema carries no such text
(FlatItem, or a reclassified heading-less leading block — whose text is in the
chunk flow, not the metadata). A valid prelude is attached whole to every chunk
of its Item and is never independently chunked or embedded.

## Integrity: commit marker

One marker point per (ticker, fiscal_year), same collection as the chunks:
ingest starts by (over)writing it to `pending`, wipes previous content points,
and flips it to `complete` only after the last upsert. Retrieval treats
anything but `complete` as absent (committed or absent — a failed ingest looks
like no ingest), and every content query excludes marker points via
`marker_status_condition()`. Re-running the ingest is the recovery path; there
is no retry wrapper inside (the embedding client already retries transient
failures internally).
