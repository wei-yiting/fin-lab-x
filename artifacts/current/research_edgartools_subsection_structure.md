# Research — edgartools Sub-section Structure & `filing.markdown()` Cross-sector Quality

## Scope

Cross-sector ground-truth probe to inform Path 2 第二輪 detection rule.
Same 6 tickers as the prelude probe — ADSK, JPM, JNJ, WMT, XOM, CAT —
× Items 7 + 1A = 12 probes. edgartools 5.17.1 vs upgraded 5.30.2
sanity-checked side by side.

Throwaway scripts: `backend/scripts/research/subsection_structure_probe.py`,
`markdown_subheading_inventory.py`, `check_filing_markdown.py`. Per-ticker
dumps in `/tmp/subsec_md_{ticker}_*.txt` and `/tmp/subsec_dump_*.txt`.

## Headline finding

**`Section.node` cannot be drilled into. `filing.markdown()` is the
only viable structural surface — but it is inconsistent across
companies in a high-variance way.** WMT and XOM (4 of 12 probes) wrap
ITEM headings inside markdown table cells (`| ITEM 7. | ... |`)
instead of emitting `## ITEM 7.`. JPM emits the right H2 but glues
the next 1.5kB of body onto the heading line. ADSK, JNJ, CAT behave
well. The new rule must be hybrid (markdown primary, text fallback)
and measured per-(ticker, item) probe, not aggregated.

## 1. Section object dump

`tenk.sections.get(key)` returns `edgar.documents.document.Section`.

| Attribute | Type | Useful? | Notes |
|---|---|---|---|
| `name` / `title` | `str` | no | Both equal section_key (`part_ii_item_7`); no human title. |
| `item` / `part` | `str?` | partial | Set for ADSK/JPM/WMT/CAT; **`None` for JNJ/XOM** (key-format inconsistency). |
| `confidence` | `float` | no | Constant 0.95 in every probe. |
| `detection_method` / `validated` | const | no | Constants. |
| `start_offset` / `end_offset` | `int` | **NO** | Mis-named: section-local (always `start=0, end=len(sec.text())`). Verified — `filing.text()[0:78668]` for ADSK Item 7 returns the cover page. Cannot slice per-section markdown. |
| `text()` | method → `str` | no for headings | Plain text, sub-headings flattened. |
| `tables()` | method → `list[TableNode]` | tangential | CAT Item 7 has 48 tables; orthogonal to sub-section detection. |
| `node` | `SectionNode` | **NO** | Marker, not subtree. `node.children` = 0, `node.walk()` = self only, `node.text()` = `""`, `node.html()` = `'<section></section>'` (19 chars). Verified on every probe. |

**Conclusion**: no `Section.subsections`, no `Section.headings`, no
per-Item markdown slice. `Section` is a body-text indexer; structure
lives elsewhere.

## 2. Markdown heading hierarchy — cross-sector statistics

### Filing-level totals

| Ticker | md chars | H1 | H2 | H3 | H4 |
|---|---|---|---|---|---|
| ADSK | 572,954 | 4 | 45 | 10 | 72 |
| JPM | 1,982,110 | 20 | 19 | 84 | 209 |
| JNJ | 583,937 | 4 | 23 | 22 | 205 |
| WMT | 474,968 | 4 | **0** | 22 | 75 |
| XOM | 938,710 | 4 | **0** | 38 | 67 |
| CAT | 724,218 | 4 | 44 | 7 | 121 |

WMT and XOM emit **zero H2 filing-wide**. JPM emits 20 H1s because
`# Part I` repeats on every page-break artifact.

### Per-Item markdown range

| Ticker | Item | sec.text | md_range | clean H | by-level | by-case | v1 ALL-CAPS hits |
|---|---|---|---|---|---|---|---|
| ADSK | 7 | 78,640 | L1084-1682 | 11 | H2:2 H4:9 | ALL_CAPS:11 | 11 |
| ADSK | 1A | 103,734 | L424-963 | 2 | H2:2 | ALL_CAPS:2 | 1 |
| JPM | 7 | 396 | L1645-1648 | 1 | H2:1 | TitleCase:1 | 0 |
| JPM | 1A | 112,862 | L325-1609 | 26 | H2:2 H1:11 H4:13 | TitleCase:24 other:2 | 0 |
| JNJ | 7 | 65,912 | L656-1260 | 40 | H2:1 H3:8 H4:31 | TitleCase:12 other:28 | 18 |
| JNJ | 1A | 43,439 | L356-520 | 9 | H2:1 H3:2 H4:6 | TitleCase:4 other:5 | 0 |
| WMT | 7 | 58,168 | **NOT FOUND** | 0 | — | — | 3 |
| WMT | 1A | 93,314 | **NOT FOUND** | 0 | — | — | 1 |
| XOM | 7 | 265 | **NOT FOUND** | 0 | — | — | 1 |
| XOM | 1A | 35,671 | **NOT FOUND** | 0 | — | — | 1 |
| CAT | 7 | 103,090 | L759-1596 | 26 | H2:2 H3:2 H4:22 | TitleCase:12 ALL_CAPS:12 other:2 | 14 |
| CAT | 1A | 53,467 | L332-571 | 6 | H2:2 H4:4 | TitleCase:2 ALL_CAPS:4 | 4 |

**4 of 12 probes have no `## ITEM` heading in markdown.** v1 ALL-CAPS
hits and clean markdown heading counts are uncorrelated — CAT Item 7
has 14 v1 hits and 22 H4s; JNJ Item 1A has 0 v1 hits and 9 clean
markdown headings.

## 3. Sub-heading ground-truth cross-check vs SEC

True structure verified by inspecting markdown excerpts in
`/tmp/subsec_md_*_headings.txt`.

| Probe | True sub-headings (canonical) | MD level | v1 ALL-CAPS hits | Notes |
|---|---|---|---|---|
| CAT 1A | MACROECONOMIC / OPERATIONAL / FINANCIAL / LEGAL & REGULATORY RISKS | 4×H4 | 4/4 | Both surfaces work |
| JPM 1 | Overview, Business segments & Corporate, Competition, Supervision and regulation, Human capital | 5×H4 | 0/5 | **Markdown is only path** |
| JPM 1A | Legal and Regulatory, Political, Market, Credit, Liquidity, Capital, Operational, Strategic, Conduct, Reputation, Country, People (12 categories) | 12×H4 | 0/12 | + 11 noise `# Part I` H1s + heading-glued-with-body |
| JNJ 1A | Risks related to our business / IP / financial conditions / Other risks | mix H3/H4 | 0/4 | Sentence-case ("other" classifier — fix classifier) |
| WMT 1A | Strategic Risks (H4), Operational Risks (H4), Financial Risks (H3) | yes (H3/H4) | 0/3 anchored | **`## Item 1A.` absent** — `\| ITEM 1A. \| RISK FACTORS \|` table-cell-wrap at L379 unanchors sub-headings |
| XOM 1A | Supply and Demand, Government and Political Factors, Climate Change and Energy Transition, Operational and Other Factors | 4×H4 | 0/4 anchored | Same table-wrap pathology |

## 4. edgartools 5.17.1 vs 5.30.2

5.30.2 (released 2026-04-29 — current as of today) is 13 minor
versions ahead. Tested WMT/XOM/JPM/JNJ markdown:

- **Identical heading counts**: WMT 4/0/22/75, XOM 4/0/38/67,
  JPM 20/19/84/209, JNJ 4/23/22/205.
- **Identical `| ITEM 1A. RISK FACTORS |` table-cell wrapping**.
  Item-heading promotion not improved.
- 87 releases between 5.17.1 and 5.30.2; relevant 10-K touchpoints
  (5.23.4 combined "Items 1 and 2", 5.28.1 TOC split-link for TSLA,
  5.29.0 agent-aware TOC parsing) target Section detection, not the
  markdown surface.

**Upgrading does not solve the problem.** Worth doing for bug fixes,
but the new rule cannot rely on upstream improving markdown.

## 5. Recommendation — hybrid detection rule

**Works**: (a) `filing.markdown()` H1-H4 levels capture Title Case
sub-headings v1 ALL-CAPS rule misses; on 8 well-formed probes, MD
captures 2-40 clean headings vs v1's 0-18. (b) `tenk[item]` for body
content — reliable across all 6 tickers.

**Does NOT work**: (a) Pure section.text() heuristics — miss
JPM/JNJ/WMT/XOM structure (4 of 6 companies); Title-Case in text
false-positives on every paragraph start. (b) `Section.node` /
offsets. (c) `Document.headings` — 252 of 266 ADSK headings are
bullet `•` / page-number fragments; JPM returns 0.

### Hybrid rule outline

```pseudo
for each Item:
    item_md_range = find_h2_item_heading(filing.markdown(), item_num)
    if item_md_range is None:
        # WMT/XOM table-cell-wrap pathology — text fallback
        signals = run_v1_caps_detector(tenk[item])
    else:
        signals = collect_headings_at_levels(md_range, levels={3, 4})
        signals = drop_noise(signals)
```

### Required noise filters

- Drop `# Part I/II/III/IV` H1s inside any Item range (11× in JPM
  Item 1A alone — page-break artifacts).
- Drop short numeric-only headings (`#### 14`, `#### 18` — JNJ page
  numbers).
- Drop `2025 Annual Report\d+` H4s (JNJ page-footer leakage).
- Drop `^•$`, `^\d+\.?$`.
- Treat heading-glued-with-body lines (JPM `## Item 1A. Risk
  Factors.The following...`) as Item H2 boundary; split on first
  sentence-terminator + capital pattern.

### Per-company surface table (codify as fallback)

| Company | ITEM-H2 in MD | Sub-heading via MD | Primary surface |
|---|---|---|---|
| ADSK | yes | high (ALL_CAPS H4) | markdown |
| JPM | partial (glued + `# Part I` noise) | high once cleaned | markdown + page-break filter |
| JNJ | yes | high (sentence-case H3+H4) | markdown |
| CAT | yes (split-title H2 ×2) | high (mixed CAPS + Title Case) | markdown |
| WMT | **no** (table-wrap) | n/a in Item range | section.text() ALL-CAPS fallback |
| XOM | **no** (table-wrap) | n/a in Item range | section.text() fallback |

### Hard constraint

**Test the new rule against all 12 (ticker, item) probes before
shipping** with the same fail-loud tests the prelude research
recommended (≥70% non-stub Items must yield ≥1 sub-heading; no false
sub-headings ≥1500 chars from heading-glued-body cases). Per-probe
measurement, not aggregate.

## Final verdict

`filing.markdown()` is the only viable structural surface but
high-variance: 8/12 probes well-formed, 4/12 (WMT, XOM) need text
fallback because the Item heading is table-cell-wrapped. JPM Item 1A
adds 11 page-break H1 noise inside the Item range — filter-able. The
hybrid rule must be measured per-probe, not aggregated. Do not
attempt to detect Title Case from text alone (false-positives every
paragraph start) and do not trust offsets or `Document.headings`.
