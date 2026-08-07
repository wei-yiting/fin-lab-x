# SEC Text Pipeline

Structured 10-K parsing built on edgartools' section API. Fetches a filing from SEC EDGAR, isolates and classifies each Item, and persists a typed `ParsedFiling` as JSON — the parse-stage cache the downstream embedding stage reads from.

## Scope and A/B Coexistence

This pipeline is the **new parse path**. It coexists with the frozen HTML baseline:

- **`sec_filing_pipeline_html/`** — the frozen HTML pipeline (A/B baseline). Its behavior does not change while the two paths coexist.
- **`sec_text_pipeline/`** (this package) — Item boundaries come from edgartools sections instead of HTML heuristics; output is a typed `ParsedFiling`, with no markdown intermediate.
- **`backend/common/sec_core.py`** — shared domain core. **Only-add during coexistence**: existing public functions (notably `is_stub_section`) keep bit-identical behavior; new needs are met by adding helpers, never by changing existing ones.

## Module Map

| Module | Responsibility |
|---|---|
| `parser.py` | `parse_filing()` — the single public entry point. Fetch (via `sec_core.fetch_filing_bundle`), per-Item boundary trimming, stub classification, store round-trip. Raises `EmptyFilingError` instead of caching a zero-item parse. |
| `filing_models.py` | The frozen `ParsedFiling` schema (`FilingMetadata`, `FlatItem`, `StructuredItem`, `Block`). All models forbid unknown fields so stored JSON cannot drift from the schema silently. |
| `filing_store.py` | `LocalFilingStore` — schema-validated JSON cache under `data/sec_text/{TICKER}/10-K/{YEAR}.json`, written atomically. |
| `stub_detection.py` | `is_stub_section_v2()` — v1 incorporated-by-reference detection plus pseudo-stub pointer patterns, via the shared `classify_stub_section` mechanism. |

## Data Flow

```
parse_filing(ticker, fiscal_year)
  ├─ FilingStore.get()              cache hit → return (skipped with force=True)
  ├─ sec_core.fetch_filing_bundle() EDGAR fetch + citation metadata
  │                                 (in-process LRU; filings are immutable
  │                                 per ticker+year, so force does not
  │                                 re-download)
  ├─ _parse_items()               per section:
  │     trim to own Item boundary → drop empty/stub/duplicate → FlatItem
  ├─ EmptyFilingError             if zero substantive items (nothing saved)
  └─ FilingStore.save()           → ParsedFiling
```

## Two Cache Stages

The filing store is the **fetch+parse** cache; Qdrant (in `sec_dense_pipeline_html/`, and in this pipeline's own dense-ingest stage once built) is the **embedding** cache. They invalidate under different conditions — a parser change invalidates the filing store, an embedding-model change invalidates only Qdrant — hence both exist. The filing store is machine-facing; a planned inspect helper (future extension, not yet built) will derive a human-facing markdown view from it.

## Extension Guidelines

- **Detection chain slot**: detection is currently degenerate — every non-stub Item is emitted as a `FlatItem`. The markdown H3/H4 detection chain plugs into `_parse_items()` in `parser.py` and upgrades qualifying Items to `StructuredItem` (`detection_source` records which path found the blocks).
- **Schema is frozen**: downstream stages (block detection, dense ingest, inspect view) build against `filing_models.py` without changes. Do not add or rename fields casually — stored JSON validates against this schema on every read.
- **New stub patterns** go into `PSEUDO_STUB_PATTERNS` in `stub_detection.py` and must run through `classify_stub_section`'s remove-then-measure mechanism — pattern presence alone must never classify a stub, because a large substantive Item can casually contain one pointer sentence.
- **`sec_core` stays only-add** until the HTML baseline is retired.
