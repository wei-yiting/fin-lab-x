# Research — 10-K Item Prelude vs Block Heading Relationship

## Scope

Validate the working hypothesis that **Item-level prelude text** (body
between the Item heading and the first ALL CAPS block heading) is
**cross-cutting context** for every block within the Item, and therefore
worth attaching as metadata to every block-derived chunk.

Method per spec: 6 tickers across sectors × 4 Items
(`1`, `1A`, `7`, `7A`) = **24 (ticker, item) probes**, all on the latest
10-K via `edgartools`. Detection rule:

```python
def is_block_heading(line):
    s = line.strip()
    return (s.isupper() and 5 <= len(s) <= 120
            and not s.isdigit()
            and not any(c in s for c in {'|', '$', '%'}))
```

Working artifacts (not committed): `backend/scripts/research/prelude_*.py`,
JSON + per-case dumps in `/tmp/prelude_*`.

## Headline finding

**The hypothesis holds qualitatively where the algorithm finds the
boundary correctly — but the ALL-CAPS detection rule itself is too
brittle to support this design as-is.** The rule succeeds on roughly
20% of probes, and silently fails (false positives, false flat-Items)
on the majority. The design needs a more robust segmentation step
before the prelude question can even be asked.

## Summary table

Verdict legend for `cross-cutting` column:
`yes` = prelude genuinely frames the whole Item.
`flat` = no block heading detected; prelude question N/A.
`pseudo-stub` = item body is a one-paragraph pointer to another section.
`algo-fail` = ALL CAPS rule missed real (Title Case) sub-headings, or
detected a table cell as a heading; reported "prelude" is unreliable.

| Ticker | Item | Total | Prelude | Headings (n) | Verdict | Note |
|---|---|---|---|---|---|---|
| ADSK | 1   |  48,223 |     83 | 14 | weak | glossary-pointer note |
| ADSK | 1A  | 103,734 |   —    |  0 | flat | no internal headings |
| ADSK | 7   |  78,640 |      0 | 11 | algo-fail | leading `Table of Contents` tricked rule |
| ADSK | 7A  |   3,860 |      0 |  4 | algo-fail | same artifact; small Item |
| JPM  | 1   |  39,220 | 34,068 |  1 | algo-fail | only "heading" = table cell `31,030AWM29,722` |
| JPM  | 1A  | 112,862 |   —    |  0 | flat | sub-headings sentence-case |
| JPM  | 7   |     396 |   —    |  — | pseudo-stub | "appears on pages 46–160" |
| JPM  | 7A  |     250 |   —    |  — | pseudo-stub | "Refer to the Market Risk…" |
| JNJ  | 1   |  34,642 |   —    |  0 | flat | sub-headings sentence-case |
| JNJ  | 1A  |  43,439 |   —    |  0 | flat | sub-headings sentence-case |
| JNJ  | 7   |  65,912 |  8,460 | 18 | algo-fail | "headings" are concatenated drug + number table rows |
| JNJ  | 7A  |     502 |   —    |  0 | flat | near-stub, very short |
| WMT  | 1   |  37,555 |   —    |  0 | flat | sub-headings sentence-case |
| WMT  | 1A  |  93,314 |   —    |  0 | flat | sub-headings sentence-case |
| WMT  | 7   |  58,168 | 14,203 |  2 | algo-fail | "headings" are end-of-Item non-GAAP table titles |
| WMT  | 7A  |   5,036 |   —    |  0 | flat | short, no internal headings |
| XOM  | 1   |   6,640 |   —    |  0 | flat | unusually short Item 1 |
| XOM  | 1A  |  35,671 |   —    |  0 | flat | risk titles sentence-case |
| XOM  | 7   |     265 |   —    |  — | pseudo-stub | "Reference is made to the section…" |
| XOM  | 7A  |     407 |   —    |  — | pseudo-stub | same + FLS sentence |
| CAT  | 1   |  39,333 | 34,845 |  1 | algo-fail | only "heading" = table cell `EAME16,70015,900` |
| CAT  | 1A  |  53,467 |  2,532 |  4 | **yes** | textbook: scope + cross-refs + FLS |
| CAT  | 7   | 103,090 |  2,503 | 14 | **yes** | textbook MD&A: scope + FLS + GAAP/non-GAAP |
| CAT  | 7A  |     675 |   —    |  0 | flat | effectively a stub |

Tally of distinct outcomes: **2 algorithm-correct cross-cutting preludes**,
**4 pseudo-stubs missed by `is_stub_section`**, **5 algorithm-failure
preludes**, **12 "flat Items"** (mostly false-flats due to sentence-case
sub-headings), **1 weak prelude** (ADSK Item 1 glossary note).

No ticker substitutions were needed; all 24 sections fetched cleanly.

## Sample evidence — algorithm-correct cross-cutting preludes

The two cases where the rule produced a clean prelude AND the content
is genuinely cross-cutting.

### CAT Item 7 (MD&A) — yes, cross-cutting

> "The following Management's Discussion and Analysis of Financial
> Condition and Results of Operations (MD&A) is intended to provide
> information that will assist the reader in understanding the
> company's Consolidated Financial Statements… This MD&A should be
> read in conjunction with our discussion of cautionary statements and
> significant risks to the company's business under Item 1A. Risk
> Factors of the 2025 Form 10-K. … Highlights for the full-year 2025
> include: …"

Hits every cross-cutting signal: "the following discussion", explicit
Item 1A cross-reference, scope-setting language, plus the GAAP-to-non-
GAAP reconciliation that downstream blocks (`OVERVIEW`, `2025 COMPARED
WITH 2024`, `LIQUIDITY`) implicitly depend on. Clear value-add to
attach.

### CAT Item 1A (Risk Factors) — yes, cross-cutting

> "The statements in this section describe the most significant risks
> to our business and should be considered carefully in conjunction
> with Part II, Item 7 'Management's Discussion and Analysis…' and
> Part II, Item 8 'Financial Statements…' to this Form 10-K. In
> addition, the statements in this section… include 'forward-looking
> statements' as that term is defined in the Private Securities
> Litigation Reform Act of 1995…"

Pure scoping + FLS disclaimer + cross-references to Items 7 and 8.
Applies equally to every downstream block (`MACROECONOMIC RISKS`,
`OPERATIONAL RISKS`, `FINANCIAL RISKS`, `LEGAL & REGULATORY RISKS`).

## Counter-examples and degenerate cases

### ADSK Item 1 — prelude exists but is not cross-cutting

> "Note: A glossary of terms used in this Form 10-K appears at the end
> of this Item 1."

83 chars; bare glossary pointer. Harmless to attach but adds nothing.

### "Pseudo-stub" Items missed by `is_stub_section` (4 of 24)

These escape the regex because they don't say "incorporated by
reference":

- **JPM Item 7 (396 chars):** "…appears on pages 46–160."
- **JPM Item 7A (250 chars):** "Refer to the Market Risk Management
  section of Management's discussion and analysis on pages 133-142…"
- **XOM Item 7 (265 chars):** "Reference is made to the section entitled
  'Management's Discussion and Analysis…' in the Financial Section of
  this report."
- **XOM Item 7A (407 chars):** "Reference is made to the section entitled
  'Market Risks'…"

Stub detection needs a second match group covering "appears on pages
N", "Refer to … section", "Reference is made to …".

### Algorithm false-positives (5 of 24)

The ALL CAPS detector matches concatenated table cells (no separators
in `edgartools`-rendered text):

- **JPM Item 1** — only "block heading" = `31,030AWM29,722`
  (region-employee table row); "prelude" of 34,068 chars is most of
  the Item.
- **CAT Item 1** — `EAME16,70015,900`; "prelude" 34,845 chars.
- **JNJ Item 7** — drug + financial strings like
  `CARVYKTI1,88796395.994.31.6`. Reported 8,460-char "prelude" is
  actually a real cross-cutting intro, but the boundary is the wrong
  cut point (a table row, not a heading).
- **WMT Item 7** — only matches are `CALCULATION OF RETURN ON ASSETS` /
  `CALCULATION OF RETURN ON INVESTMENT`, the non-GAAP table titles at
  the *end* of MD&A. Reported "prelude" (14,203 chars) sweeps in
  `Overview`, `Recent Developments`, `Liquidity` — i.e. most of the
  Item.
- **ADSK Item 7 / 7A** — leading `Table of Contents` line prepended by
  edgartools makes the rule treat the Item's own `ITEM 7.MANAGEMENT'S
  DISCUSSION…` heading as a block heading. Reported prelude is empty
  even though a genuine cross-cutting prelude exists ("The following
  discussion and analysis… should be read in conjunction with our
  consolidated financial statements…").

### "Flat Item" false-negatives

Most of the 12 flat-Items use Title Case sub-headings the ALL-CAPS rule
can't see: JPM Item 1 (`Overview`, `Business segments & Corporate`,
`Competition`), JNJ Items 1 / 1A / 7, WMT Item 1A (`Strategic Risks`,
`Operational Risks`, `Financial Risks`). Genuinely flat is rare — XOM
Item 1 at 6,640 chars total is the closest case.

## Detection rule must change before this design ships

Priority-ordered deltas:

1. **Strip prelude-junk lines** (leading `Table of Contents`,
   page-number-only lines) before picking the "first line". Without
   this, ADSK MD&A's real prelude is invisible.
2. **Exclude the Item's own heading from block-heading detection.**
   Match the first line against `ITEM \d+[A-C]?\.?` and skip it.
3. **Reject candidates with digit-adjacent-to-alphabetic patterns**
   (`EAME16,70015,900`, `CARVYKTI1,88796`). Current rule only excludes
   `$`/`%`/`|`. Adding "≥3 consecutive digits" eliminates ~all observed
   false-positive table cells.
4. **Accept Title-Case-bold segmentation as a first-class case.**
   ALL-CAPS only works for ADSK / CAT; JPM / JNJ / WMT use Title Case.
   Either (a) accept short Title Case lines on their own, or (b) reach
   for HTML/markdown (`research_filing_markdown_quality.md` shows this
   is more reliable than text-only segmentation).
5. **Extend `is_stub_section`** to cover "Reference is made to…",
   "Refer to … on pages N", "appears on pages N–M". 4 of 24 probes
   (17%) are pseudo-stubs the current regex misses.

## Final verdict

**Cross-cutting hypothesis is qualitatively correct, but only 2 of 24
probes (8%) yield a clean prelude the algorithm can identify.** The two
clean cases (CAT Item 7, CAT Item 1A) confirm the pattern: scope-setting
prose, FLS disclaimer, cross-references to other Items, GAAP/non-GAAP
definitions — all genuinely cross-cutting. Where the algorithm fails,
its reported "prelude" is usually most of the section body and would be
catastrophic context bloat to attach to every chunk.

**Recommendation — gate this design behind detection fixes:**

1. Fix the rule (items 1–4 in the previous section), then re-run this
   probe and require ≥70% of non-stub Items to yield a prelude under
   3,000 chars before shipping. Without this, attaching the algorithm's
   current output injects 14k-char false preludes into every WMT MD&A
   chunk and 34k-char false preludes into every JPM Item 1 chunk.
2. Cap attached-prelude size (e.g. ≤2,000 chars / ≤500 tokens) as a
   hard upper bound, with fallback to first paragraph when the
   algorithm overshoots — bounds the blast radius on novel filing
   formats.
3. Treat prelude-attachment as opt-in by Item, not always-on. The
   genuine yeses concentrate in Items 7 and 1A; Item 1 preludes are
   mostly weak (ADSK glossary pointer) or absent; Item 7A is mostly
   stub-shaped.
4. Extend `is_stub_section` to cover the JPM/XOM "Reference is made
   to…", "appears on pages N", "Refer to … section" patterns
   independently. These pseudo-stubs (4 of 24 probes) shouldn't be
   ingested at all, prelude or not.
