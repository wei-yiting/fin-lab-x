# sec_core

Shared SEC filing layer used by both the agent's two-step section tools and the RAG ingestion pipeline. Implementation lives at `backend/common/sec_core.py`.

## Why a shared core

FinLab-X has two consumers of SEC EDGAR, with very different shapes:

- **Agent tool path** (`backend/agent_engine/tools/sec_filing_tools.py`) — answers natural-language questions about a single 10-K item per turn. Reads the filing's structured `TenK` object directly via edgartools and returns plain text inline; never goes near markdown conversion or local caching.
- **RAG ingestion pipeline** (`backend/ingestion/sec_filing_pipeline/`) — bulk-downloads filings, converts HTML → Markdown, and persists `.md` files for downstream chunking + embedding. Optimized for offline batch runs and S3-style cache reuse, not single-call latency.

Both paths still need the same domain primitives: a `FilingType` enum, a stable error hierarchy that callers can branch on, the canonical SEC item table, and one place that knows how to map raw edgartools / HTTP errors to typed exceptions. Without `sec_core`, those primitives would be duplicated and would drift.

```mermaid
graph TB
    subgraph Core["backend/common/sec_core"]
        T[FilingType<br/>StrEnum: 10-K]
        E[SECError hierarchy<br/>TickerNotFound / FilingNotFound /<br/>UnsupportedFilingType / Transient /<br/>RateLimit / Configuration /<br/>SectionNotFound]
        TBL[TENK_STANDARD_TITLES<br/>SEC 17 CFR 229<br/>canonical item map]
        FETCH[fetch_filing_obj<br/>LRU-cached TenK fetch]
        FY[_resolve_latest_fiscal_year<br/>metadata-only FY lookup]
        PARSE[parse_item_number<br/>section_key normalization]
        STUB[is_stub_section<br/>incorporated-by-reference /<br/>Reserved detection]
        CLS[_classify_edgar_error<br/>edgartools / HTTP → SECError]
    end

    subgraph Agent["Agent tool path<br/>(real-time, structured access)"]
        L[sec_filing_list_sections<br/>canonical TOC + char_count + stub flag]
        G[sec_filing_get_section<br/>full body of one item]
    end

    subgraph Pipeline["RAG ingestion pipeline<br/>(batch, HTML → Markdown)"]
        D[SECDownloader] --> P[HTML preprocess /<br/>Markdown convert / store]
    end

    TBL --> L
    TBL --> G
    FETCH --> L
    FETCH --> G
    FY --> L
    FY --> G
    PARSE --> G
    STUB --> L
    STUB --> G
    T --> L
    T --> G
    T --> D
    E --> L
    E --> G
    E --> D
    CLS --> D
```

The thicker dependency on the agent side is intentional: agent calls are the latency-sensitive path that benefits most from a shared cache and a unified resolution rule, while the pipeline only needs the typed-error contract and the enum to stay aligned with the agent's `SECError`-aware callers.

## Design notes

### `TENK_STANDARD_TITLES` is a constant, not parsed from filing text

Section titles in 10-K filings are governed by SEC 17 CFR 229 — they are a fixed, regulator-defined list. Parsing them out of `section.text()` is unreliable in practice: the first line varies by issuer (`ITEM 1.BUSINESS` vs `Item 1.\xa0\xa0\xa0\xa0Business` vs the literal string `Table of Contents` for some sections of some filers). Looking up the title in a 23-entry constant map is correct by construction; parsing is correct only when issuers happen to format consistently.

### `fetch_filing_obj` cache key includes `fiscal_year`

The LRU cache is keyed by `(ticker_upper, filing_type, fiscal_year)`. `fiscal_year=None` resolves "latest" and is its own cache slot; passing the resolved integer is a different slot. The agent's system prompt instructs the model to forward the resolved FY from `list_sections` into `get_section` so the two calls share one cache entry. Without that hint, `None`-then-int would fetch the filing twice on a follow-up turn.

### No app-level retry on SEC 429

When `edgar.httprequests.TooManyRequestsError` propagates to `_classify_edgar_error`, edgartools' own conservative-rate-limit + exponential-backoff retry has already been exhausted and SEC has typically issued a ~10-minute IP block. SEC's documentation explicitly warns against immediate retry. We surface `RateLimitError` with `retry_after` populated from the `Retry-After` header (integer seconds — SEC's observed form) and let the caller decide; the agent's correct response is to stop and report rather than spin.

## Extending to a new SEC filing type

1. Add a variant to `FilingType` and a corresponding `TENQ_STANDARD_TITLES`-style constant.
2. Decide whether `parse_item_number`'s normalization rule is the same — if items can collide across Parts, introduce a per-filing-type key scheme instead.
3. Update `_classify_edgar_error`'s `UnsupportedFilingTypeError` branch (currently hard-codes the 20-F fallback for FPI detection on 10-K-only callers).
4. Re-evaluate `is_stub_section` thresholds against real samples from the new filing type before reusing.
