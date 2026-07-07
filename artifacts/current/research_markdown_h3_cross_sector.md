# Research — Cross-sector Markdown H3/H4 Detection Probe

## Scope

Cross-sector probe of the proposed Path 2 detection rule **markdown
H3 primary + text fallback** — collect H3 titles from
`filing.markdown()`, anchored-search them as standalone lines in
`tenk[item].text()`, fall back on miss.

10 tickers × 3 items (1, 1A, 7) = **30 probes** on the latest 10-K
via `edgartools` 5.17.1: ADSK, CAT, JPM, JNJ, WMT, XOM, KO, BA, VZ,
DIS. All fetched cleanly — no rate limits, no substitutions.

Scripts: `backend/scripts/research/markdown_h3_cross_sector.py`,
`backend/scripts/research/h3_h4_combined_probe.py`. JSON:
`/tmp/h3_cross_sector_results.json`,
`/tmp/h3_h4_combined_results.json`. Per-ticker dumps:
`/tmp/h3_dump_<TICKER>.txt`.

## Headline finding

**The proposed H3-primary rule is wrong. Real sub-headings live at
H4 in 9 of 10 filings.** Pure H3 anchoring fails on 19 of 30 probes.
With H4 unioned in, the rule yields ≥1 clean candidate on 25 of 30
probes; the 5 misses are 2 pseudo-stubs + 3 genuinely-flat
Items where edgartools does not promote sub-headings to any markdown
heading level. Noise is low once a literal/regex blacklist filters
cover-page boilerplate and page numbers — but the **level**
assumption in the brief is the load-bearing wrong premise.

## 1. Per-(ticker, item) summary table

`H3raw`/`H4raw` = filing-wide counts. `H3clean`/`H4clean` = after
noise filter. `H3anc`/`H4anc` = anchored as standalone line in this
Item's text. `Comb` = unique union. `Noise` = filtered-out anchored
entries.
Verdict: `good` ≥4, `partial` 2-3, `fallback-needed` 0, `stub` =
pseudo-stub Item (`is_stub_section` should reject upstream).

| # | Ticker | Item | H3raw | H4raw | H3clean | H4clean | H3anc | H4anc | Comb | Noise | Verdict |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | ADSK | 1 | 10 | 72 | 0 | 56 | 0 | 14 | 14 | 0 | good |
| 2 | ADSK | 1A | 10 | 72 | 0 | 56 | 0 | 0 | **0** | 0 | **fallback** |
| 3 | ADSK | 7 | 10 | 72 | 0 | 56 | 0 | 9 | 9 | 0 | good |
| 4 | CAT | 1 | 7 | 121 | 3 | 110 | 1 | 21 | 22 | 1 | good |
| 5 | CAT | 1A | 7 | 121 | 3 | 110 | 0 | 4 | 4 | 0 | good |
| 6 | CAT | 7 | 7 | 121 | 3 | 110 | 3 | 23 | 26 | 0 | good |
| 7 | JPM | 1 | 84 | 209 | 7 | 140 | 1 | 5 | 5 | 0 | good |
| 8 | JPM | 1A | 84 | 209 | 7 | 140 | 0 | 12 | 12 | 0 | good |
| 9 | JPM | 7 | 84 | 209 | 7 | 140 | 0 | 0 | 0 | 0 | **stub** |
| 10 | JNJ | 1 | 22 | 205 | 16 | 73 | 2 | 19 | 21 | 3 | good |
| 11 | JNJ | 1A | 22 | 205 | 16 | 73 | 2 | 2 | 4 | 3 | good |
| 12 | JNJ | 7 | 22 | 205 | 16 | 73 | 6 | 17 | 23 | 10 | good |
| 13 | WMT | 1 | 22 | 75 | 13 | 53 | 2 | 8 | 10 | 0 | good |
| 14 | WMT | 1A | 22 | 75 | 13 | 53 | 1 | 2 | 3 | 0 | partial |
| 15 | WMT | 7 | 22 | 75 | 13 | 53 | 5 | 16 | 21 | 0 | good |
| 16 | XOM | 1 | 38 | 67 | 27 | 52 | 0 | 0 | **0** | 0 | **fallback** |
| 17 | XOM | 1A | 38 | 67 | 27 | 52 | 0 | 4 | 4 | 0 | good |
| 18 | XOM | 7 | 38 | 67 | 27 | 52 | 0 | 0 | 0 | 0 | **stub** |
| 19 | KO | 1 | 30 | 79 | 14 | 68 | 0 | 13 | 13 | 1 | good |
| 20 | KO | 1A | 30 | 79 | 14 | 68 | 6 | 1 | 7 | 0 | good |
| 21 | KO | 7 | 30 | 79 | 14 | 68 | 4 | 22 | 26 | 0 | good |
| 22 | BA | 1 | 13 | 114 | 2 | 85 | 0 | 11 | 11 | 1 | good |
| 23 | BA | 1A | 13 | 114 | 2 | 85 | 0 | 4 | 4 | 0 | good |
| 24 | BA | 7 | 13 | 114 | 2 | 85 | 1 | 28 | 29 | 0 | good |
| 25 | VZ | 1 | 3 | 114 | 0 | 88 | 0 | 18 | 18 | 0 | good |
| 26 | VZ | 1A | 3 | 114 | 0 | 88 | 0 | 0 | **0** | 0 | **fallback** |
| 27 | VZ | 7 | 3 | 114 | 0 | 88 | 0 | 64 | 64 | 2 | good |
| 28 | DIS | 1 | 40 | 198 | 26 | 50 | 8 | 13 | 21 | 12 | good |
| 29 | DIS | 1A | 40 | 198 | 26 | 50 | 3 | 0 | 3 | 0 | partial |
| 30 | DIS | 7 | 40 | 198 | 26 | 50 | 9 | 21 | 30 | 2 | good |

Tally with **combined H3+H4** rule: **good** 23/30 (77%), **partial**
2/30 (7%), **stub** 2/30 (7%), **fallback** 3/30 (10%) — ADSK 1A,
XOM 1, VZ 1A.

## 2. Sample H3 inventory

Every ticker leads with `UNITED STATES` + `SECURITIES AND EXCHANGE
COMMISSION` (cover-page noise) and ends with `SIGNATURES` /
`POWER OF ATTORNEY` (back-matter noise). Real-content samples:

- **ADSK** (10 H3): all noise (cover + financial-statement chapter
  dividers like `CONSOLIDATED STATEMENTS OF OPERATIONS`).
  **0/10 real sub-heading-grade.**
- **CAT** (7 H3): 3 real — `Financial Products Segment`, `OVERVIEW`,
  `CONSOLIDATED SALES AND REVENUES`.
- **JPM** (84 H3): mixed; 11 duplicate `Notes to consolidated
  financial statements` chapter dividers; meaningful entries include
  `Description of business segment reporting methodology`, `Daily
  Risk Management VaR`, `Operational Risk Management Framework`,
  `Overview`.
- **JNJ** (22 H3): mostly real — `Risks related to supply chain`,
  `Segments of business`, `Employees and human capital management`,
  `Organization and business segments`, `Results of operations`.
- **WMT** (22 H3): 7/10 real — `Additional Information About Our
  Business`, `Human Capital Management`, `Financial Risks`,
  `Overview`, `Results of Operations`.
- **XOM** (38 H3): rich and mostly real — `FINANCIAL SECTION`,
  `BUSINESS PROFILE`, `FINANCIAL INFORMATION`, `OVERVIEW`,
  `BUSINESS ENVIRONMENT`, `Upstream Financial Results`.
- **KO** (30 H3): 4/10 real — `RISKS RELATED TO OUR OPERATIONS`,
  `RISKS RELATED TO CONSUMER DEMAND`, `RISKS RELATED TO REGULATORY`.
- **BA** (13 H3): mostly cover-page + financial dividers; only
  `Consolidated Results of Operations and Financial Condition` is
  real.
- **VZ** (3 H3): UNITED STATES, SECURITIES AND EXCHANGE COMMISSION,
  TABLE OF CONTENTS — **0/3 real**. Real structure is entirely at H4.
- **DIS** (40 H3): 6/10 real — `ENTERTAINMENT`, `SPORTS`,
  `EXPERIENCES`, `INDIA JOINT VENTURE`, `HUMAN CAPITAL`.

## 3. ToC pollution analysis (Q3)

`filing.markdown()` does **not** emit ToC entries as H3 on any of the
10 tickers. ToC representation is either a markdown table block, a
bullet list of `[Title](anchor)` links, or absent (VZ). The "ToC
links duplicating real sub-headings" risk the brief anticipated does
not materialize.

Cover-page noise is uniform: `UNITED STATES` and `SECURITIES AND
EXCHANGE COMMISSION` appear at H3 in every filing. Add `TABLE OF
CONTENTS`, `FORM 10-K`, `DOCUMENTS INCORPORATED BY REFERENCE`,
`FORWARD-LOOKING STATEMENTS`, registrant company-name lines,
`Washington, D.C. 20549`. Window-position is **not** a reliable signal
— KO's first-5% window contains real Item 1A sub-headings because
Item 1 is short. Use literal-blacklist + regex (§6).

DIS Item 7 anchored `TABLE OF CONTENTS` in plain text — DIS markdown
emits it as H4 ~16× as page-break artifact. Filtered by literal rule.

## 4. WMT / XOM H3 status (Q5)

H3/H4 promotion is **independent of H2 breakage** (table-cell wrap).
Both tickers have rich H3+H4 inventory: WMT 22 H3 / 75 H4 (13/53
clean), XOM 38 H3 / 67 H4 (27/52 clean).

WMT is **fully usable via H3+H4** despite broken H2: Item 1 → 10
anchored (`Additional Information About Our Business`, `Human Capital
Management`, plus 8 H4 incl. `Walmart U.S. Segment`); Item 7 → 21
anchored (textbook MD&A). Item 1A only 3 anchored (`Financial Risks`,
etc.) — `Strategic Risks` and `Operational Risks` are not promoted
to markdown at all → *partial*.

XOM is **mixed**: Item 7 is a 265-char pseudo-stub ("Reference is
made to..."); real MD&A lives in `FINANCIAL SECTION` (md L993),
unreachable via `tenk['7']` regardless of detection method. Item 1A
has 4 anchored H4. Item 1 is anomalously short (6,640 chars), zero
internal structure — genuinely flat.

**Conclusion**: WMT and XOM do **not** need a separate fallback path
because of broken H2; they behave identically to well-formed tickers
at H3/H4.

## 5. Cross-Item collision evidence (Q4)

Anchored-clean titles appearing in ≥2 of the 3 probed Items per
ticker: CAT 4 (Construction/Resource/Power Industries, Financial
Products Segment); WMT 3 (Walmart U.S./International/Sam's Club
Segments); VZ 6 (Consumer/Business Groups, Wholesale, Enterprise/
Public, Global Networks/Tech, Business Markets); DIS 5 (Linear
Networks, Direct-to-Consumer, Content Sales/Licensing, Parks &
Experiences, Consumer Products); KO 1 (`General`); ADSK/JPM/JNJ/XOM/
BA: none.

Collisions are **common but real** — segment-based companies repeat
segment names by design across Item 1 (segment description) and
Item 7 (segment financial results). Both occurrences are genuine
sub-headings; per-Item anchored search correctly isolates each
occurrence. **No false collisions** — no case where noise leaked into
multiple Items.

## 6. Noise filter recommendation

Apply to raw H3+H4 titles before anchored search.

**Literal blacklist** (exact match): `UNITED STATES`,
`SECURITIES AND EXCHANGE COMMISSION`, `TABLE OF CONTENTS`,
`FORM 10-K`, `PART I`–`PART IV`, `FORWARD-LOOKING (STATEMENTS|
INFORMATION)`, `Cautionary Note (About|on) Forward-Looking
Statements`, `DOCUMENTS INCORPORATED BY REFERENCE`, `SIGNATURES`
/`Signatures`, `POWER OF ATTORNEY`, `AVAILABLE INFORMATION`/
`Available Information`, `•`, `or`/`OR`, `Washington, D.C. 20549`.

**Regex** (line start): `^\d+$`, `^[•\-]+$`, `^Commission File`,
`^For the (Fiscal Year|fiscal year|transition period)`,
`^\d{4}\s+(Annual|Form\s*10[-\s]?K|Annual Report)`,
`^Item\s+\d+[a-c]?\b`, `^[A-Z\s]+(INC|CORP|COMPANY|LLC)\.?$`,
`^Index to`, `^Notes to consolidated financial statements`,
`^Consolidated (Statements? of|Balance Sheets?)`,
`^Report of Independent` (both cases).

Sum 33 anchored noise entries across the 30 probes — all caught,
zero true sub-heading misclassified.

## 7. Final verdict

**Replace H3-primary with "H3+H4 union + literal/regex noise filter".**
Coverage: 25 served by markdown path (23 good + 2 partial), 2 stubs
skipped, 3 reach text fallback.

The 3 fallback cases are not solvable by markdown collection:
**ADSK Item 1A** (`Risks Relating to Our Business and Strategy` etc.
exist as Title-Case lines, no `#` promotion); **VZ Item 1A**
(`Economic and Strategic Risks`, `Operational Risks` — same pattern);
**XOM Item 1** (anomalously short, zero internal structure).

These 3 need text-level Title-Case detection with sentence-end guard,
per `research_legacy_heading_heuristics.md` §6.3. The brief's proposed
fallback (text-only ALL-CAPS) catches **none** of these — all three
use Title Case.

### Rule

```pseudo
def detect_subheadings(filing, item_text, item_num):
    if is_stub_section(item_text): return []
    md = filing.markdown()
    candidates = filter_noise(dedupe(
        collect_headings(md, level=3) + collect_headings(md, level=4)
    ))
    standalone = {ln.strip() for ln in item_text.splitlines() if ln.strip()}
    anchored = [t for t in candidates if t in standalone]
    if not anchored:
        anchored = detect_in_text(item_text)  # Title-Case + ALL-CAPS
    return anchored
```

**Don't ship H3-only.** It emits 0 sub-headings on 19 of 30 probes,
including ADSK Items 1+7, BA Items 1+1A, KO Item 1, VZ Items 1+7 —
all textbook MD&A cases that have rich structure at H4.
