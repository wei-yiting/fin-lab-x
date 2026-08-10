# SEC Text Pipeline

Structured 10-K parsing built on edgartools' section API. Fetches a filing from SEC EDGAR, isolates and classifies each Item, and persists a typed `ParsedFiling` as JSON — the parse-stage cache the downstream embedding stage reads from.

## Scope and A/B Coexistence

This pipeline is the **new parse path**. It coexists with the frozen HTML baseline:

- **`sec_filing_pipeline_html/`** — the frozen HTML pipeline (A/B baseline). Its behavior does not change while the two paths coexist.
- **`sec_text_pipeline/`** (this package) — Item boundaries come from edgartools sections instead of HTML heuristics; output is a typed `ParsedFiling`. The filing-level markdown is used **transiently** during block detection (heading candidates only) and is never persisted — there is no markdown intermediate in the output.
- **`backend/common/sec_core.py`** — shared domain core. **The A/B data contract is frozen during coexistence**: existing public functions (notably `is_stub_section`) keep bit-identical data-path behavior; new needs are met by adding helpers. Error classification and error-message wording are outside the evaluated material and may be corrected in place.

## Module Map

| Module | Responsibility |
|---|---|
| `parser.py` | `parse_filing()` — the single public entry point. Fetch (via `sec_core.fetch_filing_bundle` + `sec_core.fetch_filing_markdown`), per-Item boundary trimming, stub classification, block detection dispatch, store round-trip. Raises `EmptyFilingError` instead of caching a zero-item parse. |
| `block_detection.py` | Markdown H3/H4 detection path: `canonicalize` (shared anchoring/scorer normalizer), noise-filtered heading-candidate collection, anchored search with the plausibility gate, prelude validity / leading-block reclassification. |
| `filing_models.py` | The frozen `ParsedFiling` schema (`FilingMetadata`, `FlatItem`, `StructuredItem`, `Block`). All models forbid unknown fields so stored JSON cannot drift from the schema silently. |
| `filing_store.py` | `LocalFilingStore` — schema-validated JSON cache under `data/sec_text/{TICKER}/10-K/{YEAR}.json`, written atomically. |
| `stub_detection.py` | `is_stub_section_v2()` — v1 incorporated-by-reference detection plus pseudo-stub pointer patterns, via the shared `classify_stub_section` mechanism. |

## Data Flow

```
parse_filing(ticker, fiscal_year)
  ├─ FilingStore.get()                cache hit → return (skipped with force=True)
  ├─ sec_core.fetch_filing_bundle()   EDGAR fetch + citation metadata
  │                                   (in-process LRU; filings are immutable
  │                                   per ticker+year, so force does not
  │                                   re-download)
  ├─ sec_core.fetch_filing_markdown() filing-level markdown (transient —
  │   └─ collect_heading_candidates() heading candidates only, not persisted)
  ├─ _parse_items()                 per section:
  │     trim to own Item boundary → drop empty/stub/duplicate
  │       → detect_blocks() plausibly anchored → StructuredItem
  │                         otherwise         → FlatItem
  ├─ EmptyFilingError               if zero substantive items (nothing saved)
  └─ FilingStore.save()             → ParsedFiling
```

## Two Cache Stages

The filing store is the **fetch+parse** cache; Qdrant (in `sec_dense_pipeline_html/`, and in this pipeline's own dense-ingest stage once built) is the **embedding** cache. They invalidate under different conditions — a parser change invalidates the filing store, an embedding-model change invalidates only Qdrant — hence both exist. The filing store is machine-facing; a planned inspect helper (future extension, not yet built) will derive a human-facing markdown view from it.

## Extension Guidelines

- **Detection chain slot**: the markdown H3/H4 paths are live in `block_detection.py` — a plausibly-anchored Item becomes a `StructuredItem` (`detection_source` records which path found the blocks), everything else stays `FlatItem`. The Title-Case text fallback path (third in the chain) plugs into `detect_blocks`' miss branch when it lands.
- **Schema is frozen**: downstream stages (block detection, dense ingest, inspect view) build against `filing_models.py` without changes. Do not add or rename fields casually — stored JSON validates against this schema on every read.
- **New stub patterns** go into `PSEUDO_STUB_PATTERNS` in `stub_detection.py` and must run through `classify_stub_section`'s remove-then-measure mechanism — pattern presence alone must never classify a stub, because a large substantive Item can casually contain one pointer sentence.
- **`sec_core`'s data contract stays frozen** (add-only for data-path behavior) until the HTML baseline is retired; error-handling fixes are allowed.
