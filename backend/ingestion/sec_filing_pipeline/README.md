# SEC Filing Pipeline

Downloads SEC 10-K filings, converts them to RAG-friendly Markdown with YAML frontmatter, and caches locally.

## Architecture

```mermaid
graph LR
    subgraph "SEC Filing Pipeline"
        A[SECDownloader<br/>edgartools] --> B[HTMLPreprocessor<br/>strip XBRL/noise]
        B --> C[HTMLToMarkdownConverter<br/>adapter pattern]
        C --> M[MarkdownCleaner<br/>strip boilerplate +<br/>normalize headings]
        M --> D[LocalFilingStore<br/>atomic write]

        C1[HtmlToMarkdownAdapter<br/>Rust, primary] -.-> C
        C2[MarkdownifyAdapter<br/>Python, fallback] -.-> C
    end

    subgraph "Entry Points"
        CLI[CLI __main__.py<br/>single + batch] --> A
        Tool[Agent Tool<br/>sec_filing_downloader] --> A
    end

    subgraph "Downstream"
        D2[S3FilingStore] -.-> D
        E["sec_dense_pipeline<br/>chunk + embed + upsert"] --> F[Qdrant]
    end

    D -- "ParsedFiling" --> E
```

## Pipeline Stages

| Stage | File | Responsibility |
|-------|------|----------------|
| Download | `sec_downloader.py` | Fetches filing HTML from SEC EDGAR via edgartools. Maps edgartools exceptions to domain errors. Requires `EDGAR_IDENTITY` env var. |
| Preprocess | `html_preprocessor.py` | Strips XBRL tags, removes decorative styles/hidden elements, unwraps `<font>` tags, normalizes hard-wrapped text whitespace (browser-equivalent collapsing), and promotes SEC Item patterns to semantic `<h>` headings. |
| Convert | `html_to_md_converter.py` | Converts cleaned HTML to Markdown. Primary: html-to-markdown (Rust-based). Fallback: markdownify (pure Python, for linux-aarch64). |
| Clean Markdown | `markdown_cleaner.py` | Strips converter-output boilerplate that has zero RAG value (cover pages, page separators, Part III stubs), and normalizes inconsistent Part / Item heading shapes across tickers. Conservative — preserves any section with substantive real content. See [Markdown Cleanup](#markdown-cleanup) below. |
| Store | `filing_store.py` | Persists `.md` files with YAML frontmatter at `data/sec_filings/{TICKER}/10-K/{fiscal_year}.md`. Atomic writes via temp file + `os.replace`. |
| Orchestrate | `pipeline.py` | `SECFilingPipeline` wires all stages. `process()` for single filing (JIT), `process_batch()` for multiple tickers with retry. |

## Heading Promotion Pipeline

`HTMLPreprocessor` promotes raw SEC 10-K block elements to semantic `<h1>`–`<h5>` in four ordered stages. Stage 2a pre-computes the single source of truth (SSOT) anchor sets for PART and Item headings so the main promotion loop (Stage 2b) and the sub-section pass (Stage 3) can never disagree on region boundaries. Stage 2b runs a three-path ladder (bold / isolated / strong font-size signal) to cover bold Workiva-style headings, non-bold isolated INTC-style headings, and non-bold-but-visually-larger JPM-style headings. Stage 4's `_strip_decorative_styles` is deliberately last so font-size is still visible to Stages 2b and 3. Tickers are bucketed into Class A/B/C by how well the ladder handles their markup; see the taxonomy table below.

```mermaid
flowchart TD
    Start([Raw 10-K HTML]) --> Clean

    subgraph Clean["Stage 1 — Pre-cleanup"]
        direction TB
        C1["<b>_strip_xbrl_tags</b><br/>Remove every &lt;ix:*&gt; element<br/>(SEC inline-XBRL metadata for<br/>parsers, not human content)"]
        C2["<b>_remove_hidden_elements</b><br/>Drop any element with<br/>style='display:none'<br/>(invisible to humans → must not<br/>reach the markdown output)"]
        C3["<b>_unwrap_font_tags</b><br/>Unwrap legacy &lt;font&gt; tags<br/>(pre-CSS layout artifact —<br/>keep inner text, drop the wrapper)"]
        C4["<b>_normalize_text_whitespace</b><br/>Collapse runs of \\s inside text nodes<br/>down to a single space<br/>(mirrors browser rendering — markdown<br/>converters don't do this on their own)"]
        C1 --> C2 --> C3 --> C4
    end

    Clean --> Pre

    subgraph Pre["Stage 2a — Pre-compute SSOT anchor sets"]
        direction TB
        DetectItem["<b>detect_item_regions(soup)</b><br/>Find body Item anchors, dedup against TOC<br/><br/>1. Scan blocks whose text starts with 'Item N.'<br/>or 'Item NA.' (regex: ^Item \\d+&#91;A-Z&#93;? \\.)<br/>2. Group by item number — keep the LAST<br/>occurrence in document order<br/>(TOC always before body, so 'last' = body anchor)<br/>3. ★ BRK.A/B fix: drop items that ONLY exist<br/>inside the TOC &lt;table&gt; — Berkshire cross-references<br/>Items 10–14 to a consolidated section, so without<br/>this drop the final list would be non-monotonic<br/>4. Sort kept anchors by doc position<br/>→ list&#91;ItemRegion(item_num, start_tag, end_tag)&#93;"]
        DetectPart["<b>detect_part_anchors(soup, is_eligible=_has_bold_signal)</b><br/>Find body PART anchors, dedup against TOC<br/><br/>1. Scan blocks whose text starts with PART I/II/III/IV<br/>(regex: ^PART &#91;IVX&#93;+)<br/>2. ★ Filter to BOLD candidates only — rescues<br/>JNJ/MSFT/BAC where TOC PARTs are bold but<br/>body PARTs are visually styled non-bold<br/>(pure last-occurrence would lose the only usable anchor)<br/>3. Group by Roman numeral, keep last bold candidate<br/>4. Sort by doc position → list&#91;Tag&#93;"]
        BodyFont["<b>_estimate_body_font_size(soup)</b><br/>Character-weighted histogram of span font-sizes<br/>→ used by isolation & strong-signal checks<br/>in Stage 2b to decide what counts as 'larger than body'"]
        DetectItem --> RegionIds["<b>region_start_ids</b> = &#123;id(r.start_tag) for r in regions&#125;<br/>Pre-computed set for O(1) membership lookup<br/>in the main loop — drives the SSOT filter"]
        DetectPart --> PartIds["<b>part_anchor_ids</b> = &#123;id(t) for t in part_anchors&#125;<br/>Same purpose for PART headings"]
    end

    Pre --> PartItem

    subgraph PartItem["Stage 2b — PART / Item promotion (main loop)"]
        direction TB
        Scan["<b>Walk every &lt;div&gt;/&lt;p&gt;/&lt;td&gt;/&lt;th&gt; in REVERSE document order</b><br/>for tag in reversed(soup.find_all(&#123;div, p, td, th&#125;))<br/>(reverse traversal so inner matches promote first;<br/>outer wrappers get filtered by the descendant guard)"]
        Scan --> Q1{"Does this tag's text start with<br/><b>'PART I', 'PART II', 'PART III' or 'PART IV'</b>?<br/>(regex: ^PART &#91;IVX&#93;+)"}

        Q1 -- Yes --> QPid{"Is this tag the body PART anchor<br/>chosen in Stage 2a?<br/>(id(tag) ∈ part_anchor_ids)<br/><br/>Pre-computed check —<br/>guarantees TOC duplicates are skipped"}
        QPid -- No --> SkipP["<b>Skip</b><br/>Either a TOC duplicate, or the body PART<br/>is non-bold so no anchor exists for this<br/>Roman numeral (rare; affects no current ticker)"]
        QPid -- Yes --> H1["<b>Rewrite as &lt;h1&gt;</b><br/>Bold check already enforced by<br/>Stage 2a's eligibility filter, so promotion<br/>is unconditional once we get here"]

        Q1 -- No --> Q2{"Does this tag's text start with<br/><b>'Item N.' or 'Item NA.'</b>?<br/>(regex: ^Item \\d+&#91;A-Z&#93;? \\.)"}

        Q2 -- Yes --> QIid{"Is this tag the body Item anchor<br/>chosen in Stage 2a?<br/>(id(tag) ∈ region_start_ids)<br/><br/>SSOT — h2 promotion uses the SAME<br/>region set as Stage 3 sub-section detection,<br/>so h2 anchors and h3+ region boundaries<br/>can never disagree"}
        QIid -- No --> SkipI["<b>Skip</b><br/>TOC duplicate or non-selected anchor<br/>(another tag for the same item number<br/>was chosen as the body anchor)"]
        QIid -- Yes --> QIpath{"Does this Item heading have<br/><b>ANY of three promotion signals</b>?"}

        QIpath -- "(a) _has_bold_signal<br/>tag has &lt;b&gt;/&lt;strong&gt; ancestor<br/>OR font-weight:700/bold<br/>on tag or any descendant span" --> H2bold["<b>Rewrite as &lt;h2&gt;</b><br/>Standard Workiva path<br/>(majority of tickers)"]
        QIpath -- "(b) is_isolated_item_block<br/>non-bold but visually a heading:<br/>font-size ≥ body AND tag is alone<br/>(no real-text block siblings,<br/>no &lt;table&gt; ancestor)" --> H2iso["<b>Rewrite as &lt;h2&gt;</b><br/>Class C fallback —<br/>non-bold but spatially isolated"]
        QIpath -- "(c) _has_item_strong_size_signal<br/>non-bold but a clear visual jump:<br/>text length &lt; 150 chars AND<br/>tag font-size &gt; body × 1.1<br/>(bypasses sibling check — the size<br/>jump + short text + strict regex<br/>make false positives unlikely)" --> H2ssig["<b>Rewrite as &lt;h2&gt;</b><br/>JPM-style strong-signal path —<br/>12pt non-bold over 10pt body,<br/>surrounded by real &lt;div&gt; paragraphs<br/>that the isolation check rejects"]
        QIpath -- "none of the three" --> R2miss["<b>Leave as &lt;div&gt;</b><br/>(reportable miss)<br/><br/>Currently only PG (font equals body,<br/>no signal at all) and INTC (color-only<br/>hierarchy, fully unsupported) hit this branch.<br/>See task_pg-item-detection-fallback.md<br/>and task_intc-color-hierarchy.md"]

        Q2 -- No --> Keep["<b>Leave untouched</b><br/>(text doesn't match PART or Item regex —<br/>just a regular block)"]
    end

    PartItem --> SubSec

    subgraph SubSec["Stage 3 — Sub-section h3/h4/h5 promotion"]
        direction TB
        S0["<b>promote_subsections(soup, regions)</b><br/>★ REUSES the same `regions` from Stage 2a<br/>SSOT alignment: every h2 anchor IS a sub-section<br/>region boundary; no possibility of disagreement<br/>between Stage 2b's h2 list and Stage 3's regions"]
        S0 --> S1["<b>build_noise_tokens(soup)</b><br/>Build a 'NOT a heading' blacklist:<br/>collect every short text (≤ 50 chars) that<br/>appears 4 or more times in the document.<br/>(e.g. 'Bank of America' page footer,<br/>'Part I' pagination strip — these would<br/>otherwise look like sub-section headings)"]
        S1 --> S2["<b>For each ItemRegion:</b><br/>walk every block in [start_tag, end_tag)<br/>(these are the candidates for h3/h4/h5<br/>inside this Item's content)"]

        S2 --> G1{"Is this a <b>bold-only sub-section candidate</b>?<br/>(is_bold_only_block — ALL of:)<br/>• tag is &lt;div&gt; or &lt;p&gt;<br/>• no &lt;table&gt; ancestor<br/>• no nested div/p/table inside<br/>• 3 ≤ text length ≤ 200<br/>• not purely numeric (page-number guard)<br/>• if text &gt; 30 chars, doesn't end in .!?<br/>• every text descendant is bold"}
        G1 -- No --> Skip1["<b>Skip</b><br/>Not a bold-only block — could be<br/>body prose, a table cell, or just<br/>not styled as a heading"]

        G1 -- Yes --> G2{"Is this text on the<br/><b>noise blacklist</b>?<br/>(text ∈ noise_tokens —<br/>i.e. it's a repeating page header/footer,<br/>not a real sub-section heading)"}
        G2 -- Yes --> Skip2["<b>Skip</b><br/>Page header/footer noise"]

        G2 -- No --> G3{"Is this text a <b>back-reference</b><br/>to its own enclosing Item?<br/>(regex: ^Item \\d+&#91;A-Z&#93;? \\b)<br/><br/>e.g. 'Item 7. (continued)' inside Item 7,<br/>or 'see Item 1A above' — these are<br/>links, not sub-headings"}
        G3 -- Yes --> Skip3["<b>Skip</b><br/>Self-reference, not a sub-section heading"]

        G3 -- No --> Collect["<b>Collect candidate</b><br/>+ measure dominant font-size<br/>(extract_dominant_font_size — char-weighted<br/>across every text span inside this tag,<br/>so the 'biggest contributor' wins)"]
        Collect --> Rank["<b>Per Item region:</b><br/>sort the unique font-sizes of all collected<br/>candidates in descending order (largest first)"]
        Rank --> Map{"Where does this candidate's<br/><b>font-size rank</b> in the descending list?"}
        Map -- "index 0 (largest in region)" --> Rh3["<b>Rewrite as &lt;h3&gt;</b>"]
        Map -- "index 1 (second largest)" --> Rh4["<b>Rewrite as &lt;h4&gt;</b>"]
        Map -- "index ≥ 2 (third or smaller)" --> Rh5["<b>Rewrite as &lt;h5&gt;</b><br/>(capped at h5 even if<br/>more font-size tiers exist)"]
    end

    SubSec --> Strip["<b>Stage 4 — _strip_decorative_styles</b><br/>Remove inline font-size, color, margin, padding<br/>from every remaining tag<br/><br/>⚠ MUST run AFTER Stage 2 and Stage 3 (R-10 hard-gate)<br/>Stage 2's strong-signal path AND Stage 3's per-region<br/>font-size ranking BOTH need font-size to still be<br/>visible in the DOM. Running this before promotion<br/>would erase the heuristic's only signal."]
    Strip --> End(["Cleaned HTML<br/>h1..h5 hierarchy<br/>zero inline decorative styles"])

    classDef success fill:#bee0ff,stroke:#2b6cb0,color:#1a365d
    classDef fallback fill:#ffe4b3,stroke:#c05621,color:#5a2d0c
    classDef ssot fill:#d8b4fe,stroke:#7c3aed,color:#4c1d95
    classDef miss fill:#ffcccc,stroke:#c53030,color:#4a1515
    classDef skip fill:#e2e8f0,stroke:#718096,color:#2d3748
    classDef endpoint fill:#c6f6d5,stroke:#2f855a,color:#1c4532

    class H1,H2bold,Rh3,Rh4,Rh5 success
    class H2iso,H2ssig fallback
    class DetectItem,DetectPart,RegionIds,PartIds,S0 ssot
    class R2miss miss
    class Skip1,Skip2,Skip3,SkipP,SkipI,Keep skip
    class Start,End endpoint
```

**Color legend:**
- Blue (`success`) — terminal nodes where h1/h2/h3/h4/h5 promotion succeeds
- Purple (`ssot`) — Stage 2a pre-compute nodes and the Stage 3 node that reuses the same `regions` (single source of truth)
- Orange (`fallback`) — non-bold h2 paths: (b) Class C isolated block or (c) JPM-style strong size signal
- Red (`miss`) — reportable misses (do not break the build, surface in round reports) — currently only PG/INTC
- Grey (`skip`) — intentionally not promoted (SSOT filter rejects, fails candidate gates, or text does not match PART/Item)
- Green (`endpoint`) — pipeline entry and exit nodes

### Ticker Taxonomy

| Class | Sample tickers | Expected outcome |
|-------|----------------|------------------|
| **A: Clean** | NVDA, AAPL, GOOGL, … (12 tickers) | Full h2 + h3 (+ h4 where applicable) hierarchy; every chunk carries a valid `header_path` |
| **B: Messy** | BRK.B, UNH, CAT, … (10 tickers) | Most Items get a sub-section hierarchy; a few show region overflow or self-reference noise but remain usable |
| **C: Hard fallback** | INTC | Only Item-level h2 promotion via the isolated-block fallback; no sub-sections — downstream chunking must use token-based splitting |

### Item Promotion Ladder

| Path | Trigger | Example ticker class |
|------|---------|----------------------|
| (a) `_has_bold_signal` | Standard bold Item heading | Class A (most filings) |
| (b) `is_isolated_item_block` | Non-bold, font-size ≥ body, block is spatially isolated | Class C INTC-style |
| (c) `_has_item_strong_size_signal` | Non-bold, text < 150 chars, font-size > body × 1.1 | JPM-style (non-isolated but visually larger) |

### Validation CLI

Operator-facing CLI for running the heuristic ladder against real EDGAR filings — see `python -m backend.ingestion.sec_filing_pipeline.validation --help` for hard-gate, discovery, and bootstrap-baseline modes.

## Data Model

Defined in `filing_models.py`:

- `FilingType` — StrEnum (`"10-K"`)
- `FilingMetadata` — Pydantic model with ticker, CIK, fiscal year, dates, converter name
- `ParsedFiling` — metadata + markdown content
- `RawFiling` — dataclass for downloader output (raw HTML + metadata)

## Cache Behavior

- **`fiscal_year` specified**: checks local cache first, skips download on hit
- **`fiscal_year=None`**: always contacts SEC to resolve the latest year, then checks cache for that year
- **`force=True`**: bypasses cache entirely

## Error Hierarchy

All inherit from `SECError` (defined in `backend/common/sec_core.py`):

| Exception | Meaning | Retryable? |
|-----------|---------|------------|
| `TickerNotFoundError` | Invalid ticker | No |
| `FilingNotFoundError` | No filing for ticker/year | No |
| `UnsupportedFilingTypeError` | Filing type not supported | No |
| `TransientError` | Network/SEC temporary failure | Yes |
| `ConfigurationError` | Missing `EDGAR_IDENTITY` | No |

## Entry Points

### CLI

```bash
# Single filing (latest fiscal year)
uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K

# Specific fiscal year, bypass cache
uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --fiscal-year 2024 --force

# Batch download
uv run python -m backend.ingestion.sec_filing_pipeline batch AAPL NVDA TSLA --filing-type 10-K

# Output control: --verbose (full metadata) or --json (machine-readable)
uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --json
```

Defined in `__main__.py`. Uses `argparse`, no extra dependencies.

### Agent Tool

`sec_filing_downloader` — LangChain `@tool` wrapping `SECFilingPipeline.process()`. Returns metadata + local file path for downstream RAG consumption. Registered in `backend/agent_engine/tools/sec_filing.py`.

For section-level access without going through the full pipeline (no Markdown conversion, no local cache), see `sec_filing_list_sections` and `sec_filing_get_section` in `backend/agent_engine/tools/sec_filing_tools.py`.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Download tool | edgartools (existing dependency) | Free, AI-ready, built-in SEC rate limiting (10 req/sec) and caching, XBRL parsing for future v3 |
| edgartools role | Download + metadata only | Don't depend on its parsing — keep general HTML parsing skills transferable |
| Intermediate format | Markdown with heading hierarchy | Best LlamaIndex ecosystem support, human-readable for debugging, preserves all chunking options |
| HTML→MD converter | html-to-markdown (Rust) + markdownify fallback | ~208 MB/s compresses JIT latency; adapter pattern guarantees cross-platform compatibility |
| html-to-markdown version | `>=3.0.2,<4.0.0` | v3 API is better (structured result), v3.0.2 contains panic fix, v2 is EOL |
| LlamaParse | Not used | Portfolio project — practice chunking hands-on, reduce external dependencies and cost |
| Metadata format | YAML frontmatter in .md | Single file, no orphaned metadata, native support in Obsidian and similar tools |
| Storage key | `{ticker}/{filing_type}/{fiscal_year}.md` | Naturally unique, flat lookup, no index needed |
| Table handling | No special treatment — converted to Markdown tables inline | Numeric tables reserved for v3 DuckDB (XBRL); text/mixed tables go through RAG; eval-driven if special handling needed |
| Docker platform | `--platform linux/amd64` in Dockerfile | html-to-markdown lacks linux-aarch64 wheel; Rosetta 2 emulation perf impact is negligible |

## Known Constraints

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| html-to-markdown lacks linux-aarch64 wheel | Docker on Apple Silicon needs platform flag | `--platform linux/amd64`; markdownify fallback |
| SEC HTML format inconsistency | Different companies/years have varying HTML structure | Preprocessor is rule-based and extensible — add a rule per noise pattern |
| Complex nested table conversion | colspan/rowspan may not convert perfectly | Not special-cased now; eval-driven decision if needed |
| Heading promotion uses a heuristic ladder calibrated on 23 SEC tickers | Class A/B filings get the full h1/h2/h3/h4/h5 hierarchy from a bold/isolated/strong-size ladder; Class C filings (e.g. INTC color-only hierarchy) degrade gracefully to Item-level h2 only | Downstream chunking must fall back to token-based splitting on Class C filings. Revisit when a new vendor pattern is observed — add a calibrated rule to `sec_heading_promoter.py` or `html_preprocessor.py`, then re-run the validation harness to confirm no Class A/B regression |
| html-to-markdown is single-maintainer | Long-term maintenance risk | Adapter pattern allows switching to markdownify at any time |
| html-to-markdown major version churn | v3 lifecycle may be short | Pinned `<4.0.0`; adapter isolates library internals |

## Markdown Cleanup

`MarkdownCleaner` runs after `convert_with_fallback()` to strip boilerplate and normalize headings. It operates at the markdown layer because page separators (`---`) are converter artifacts invisible in HTML, and heading casing inconsistencies only manifest after conversion.

Design principle: **prefer leaving noise over risking deletion of real content.** The downstream LLM can filter noise, but deleted content is gone for good.

### Cleanup rules

| Rule | What it does | Safety |
|------|-------------|--------|
| **Cover page strip** | Removes content between frontmatter and `# Part I` (or fallback `## Item 1`). | Pass-through + warning if no anchor found. |
| **Page separator strip** | Removes bare `---` lines with optional digit-line and `[Table of Contents]` link. | Pipe-flanked table separators never match. |
| **Part III stub strip** | Removes Item 10-14 sections that are pure "incorporated by reference" stubs. Drops ref-sentences first, then checks if < 100 chars remain. | Preserves hybrid sections (e.g. AMT exec biographies, CRM Code of Conduct). `\b` boundary protects Item 1C/9A/9B/9C. |
| **Heading normalization** | Standardizes to `# Part {Roman}` / `## Item {num}. {Title}`. Title-cases ALL CAPS and sentence-case titles. Merges split-line titles. | Mixed-case left alone. Abbreviations (`MD&A`, `SEC`, `U.S.`) preserved. |

### Re-running validation

```bash
uv run python -m backend.scripts.validation.validate_sec_md_cleanup \
  --cache-dir data/sec_filings \
  --output artifacts/current/validation_cleanup_patterns.md
```

Validated against 24 tickers / 29 filings across 8 industries. Existing cached filings are not retroactively cleaned — use `--force` to reprocess.
