# BDD Verification Report — HTMLPreprocessor h3/h4/h5 Promotion

> Branch: `feat/enhance-sec-html-heading-promotion`
> Generated: 2026-04-09
> Loop: 6 rounds automated + 1 manual verification round

## Headline

| Metric | Initial (Round 1) | Final (Round 6) | Δ |
|---|---|---|---|
| **Discovery harness `needs_review` (28 tickers)** | **24** | **2** | **−22** |
| Discovery harness `sane` | 4 | 26 | +22 |
| Hard-gate (R-13 baseline regression) | 23/23 | 23/23 | — |
| Unit tests | 237 | 291 | +54 |
| Manual verification (Manual Behavior Test) | n/a | 3/3 PASS | — |

The 2 remaining `NEEDS_REVIEW` tickers (PG, INTC) are explicitly tracked as out-of-scope follow-ups — see [`task_pg-item-detection-fallback.md`](task_pg-item-detection-fallback.md) and [`task_intc-color-hierarchy.md`](task_intc-color-hierarchy.md). They are documented known limitations, not unflagged regressions.

> ⚠ **Methodology note** — the BDD scenario PASS count (53/53 throughout 6 rounds) is **not** a useful signal for this loop. Scenario criteria were intentionally lenient (e.g. "every h1 starts with `Part`" rather than "h1 count == 4"). The discovery harness's per-ticker sanity verdict is the strict regression detector and the only number worth tracking. For future BDD runs against this branch, monitor `discovery_round_*.json::summary.needs_review`, not scenario PASS counts.

---

## Fix journey — needs_review count progression

```
Round 1 ─── 24 ──┐
                  │  PART bold-aware last-occurrence dedup (commit 66fec6c)
Round 3 ─── 7 ───┤
                  │  Item promotion SSOT + empty-sibling skip
Round 4 ─── 5 ───┤
                  │  C1 TOC-only Item drop + C2 strong-signal helper (commit 54c8dd1)
Round 5 ─── 2 ───┤
                  │  100→150 char guard (JPM long Item titles)
Round 6 ─── 2 ───┘
```

| Round | sane | needs_review | Action | Commit |
|---|---|---|---|---|
| 1 | 4 | 24 | Initial sweep (Stage 1 Docker sandbox) | — |
| 2 | (failed) | (regression) | Fixer first attempt — pure last-occurrence broke JNJ | reverted |
| 3 | 21 | 7 | Bold-aware last-occurrence rescues TOC-bold + body-non-bold tickers | `66fec6c` |
| 4 | 23 | 5 | `_promote_headings` uses `detect_item_regions` as SSOT for h2 | (squashed into 54c8dd1) |
| 5 | 26 | 2 | C1 drops TOC-only Items; C2 promotes non-bold Items with size jump | (squashed into 54c8dd1) |
| 6 | 26 | 2 | Bumped strong-signal length guard 100→150 to admit JPM Items 5/12 | `54c8dd1` |

---

## Three root-cause buckets surfaced and resolved

### Bucket 1 — TOC PART double-promotion (21 tickers)

**Symptom**: `h1_count = 8` (expected 4) for most Workiva-vendored filings. The 4 PART headings appeared twice — once in the table-of-contents region and once in the body.

**Root cause**: `_promote_headings` had no dedup pass for PART tags. The Item branch already used `detect_item_regions`'s last-occurrence-wins heuristic, but that pattern was never extended to PART.

**Fix**: New `detect_part_anchors(soup, is_eligible=...)` mirrors `detect_item_regions`. Caller passes `_has_bold_signal` so JNJ/MSFT/BAC-style filings (TOC bold, body PART non-bold) keep the bold TOC anchor instead of being filtered to nothing. Pure last-occurrence-wins (without bold awareness) regressed JNJ in an earlier attempt — bold-aware was the minimal fix.

**Affected → fixed**: NVDA, AAPL, GOOGL, AMZN, MSFT, TSLA, KO, BA, JNJ (preserved), XOM, UNH, T, DIS, AMT, NEE, WMT, USB (preserved), ALL, SLB, JPM (h1=22→4), CRM, BAC, BRK.A/B.

**Commit**: `66fec6c` — `fix(sec-pipeline): dedup TOC PART headings via bold-aware last-occurrence`

---

### Bucket 2 — Item h2 inflation from TOC duplicates (4 tickers)

**Symptom**: CRM h2=48, BAC h2=45, BRK.A/B h2=39 (expected 18-30).

**Root cause** (the dead-code gap): `detect_item_regions` already performed last-occurrence dedup per Item number, but `_promote_headings`'s main loop **never used `regions` to filter promotion**. It independently re-scanned every `_BLOCK_TAGS` element matching `_ITEM_RE`+bold and rewrote each as `<h2>`. So TOC `<td>Item 1.</td>` and body `<div>Item 1. Business</div>` were both emitted. The dedup was load-bearing only for `promote_subsections`, not for h2 counts.

**Fix (SSOT)**: `_promote_headings` computes `region_start_ids = {id(r.start_tag) for r in regions}` and the Item branch skips any tag whose `id()` is not in that set. Item promotion is now guaranteed to match what region detection says.

**Affected → fixed**: CRM 48→24, BAC 45→23 (BAC went +1 because C2 also caught a previously-missed Item 9 — net positive correction), BRK.A/B 39→17 (further reduced by Bucket 3).

**Commit**: `54c8dd1` (combined with Buckets 3 & 4).

---

### Bucket 3 — BRK.A/B non-monotonic Items 10-14 (2 tickers, same filing)

**Symptom**: After Bucket 2 fix, BRK.A/B `h2_first3 = [Item 10, Item 11, Item 12]` — non-monotonic. Items 1, 1A, 1B appeared **after** Item 14 in document order.

**Root cause**: Berkshire's 10-K cross-references Items 10-14 to consolidated group sections — those item numbers exist **only** inside the TOC `<table>`. `detect_item_regions`'s last-occurrence picked TOC anchors at low document index. With SSOT (Bucket 2), the region list became `[10, 11, 12, 13, 14, 1, 1A, ..., 15]` which fails the monotonic check.

**Fix (C1)**: New post-pass in `detect_item_regions`:
1. Compute `body_start = min(non-table anchor positions)`
2. Drop any anchor where `idx < body_start AND has_table_ancestor=True`
3. If no non-table anchors exist (fully table-layout filing), fall through unchanged

**Affected → fixed**: BRK.A/B Items 10-14 dropped entirely (they don't have body content in Berkshire's filing — they're literal cross-references). Final: h2=17 monotonic.

**Commit**: `54c8dd1`.

---

### Bucket 4 — JPM non-bold body Items (1 ticker)

**Symptom**: JPM h2=0. PART promotion worked (h1=4 after Bucket 1) but Item detection failed entirely.

**Root cause**: JPM body Items are `<div>` containing `<span style="font-size:12pt;font-weight:400">Item 1. Business.</span>` — non-bold (12pt over 10pt body, font-family `Sons` for visual hierarchy). `_has_bold_signal` returns False. `_is_isolated_item_block` requires the prev/next sibling to NOT be a block element with content; JPM uses `<div>` as its paragraph container (not `<p>`), so every Item heading has a real-text `<div>` next sibling that the sibling check rejects as a blocker.

**Fix (C2)**: New `_has_item_strong_size_signal(tag, text, body_font_size)` helper. Returns True when:
- text length < 150 (covers JPM's longest Item 5 title at ~110 chars; rejects body paragraphs)
- tag's dominant font-size > body font-size × 1.1 (JPM 12/10 = 1.20 ✓; rejects 10.5/10 = 1.05 inter-section variance)

This becomes a third OR branch in `_promote_headings`'s `should_promote` for h2: `_has_bold_signal OR _is_isolated_item_block OR _has_item_strong_size_signal`. Bypasses sibling checks because the size jump + short text + strict regex anchor make false positives unlikely.

**Affected → fixed**: JPM h2=0→22 (full Item set, monotonic). Also caught BAC's previously-missed Item 9 (net positive).

**Initial threshold was 100 chars** — JPM Items 5 and 12 have official SEC titles ≥100 chars (e.g. "Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities"). Bumped to 150 in round 6 after confirming no false positives across all 28 tickers.

**Commit**: `54c8dd1`.

---

## Final per-ticker state (Round 6)

| Ticker | Vendor | h1 | h2 | h2 first 3 | Status |
|---|---|---|---|---|---|
| NVDA | workiva | 4 | 23 | Item 1. Business / 1A. Risk Factors / 1B. Unresolved Staff Comments | ok |
| AAPL | workiva | 4 | 23 | Item 1. Business / 1A. Risk Factors / 1B. Unresolved Staff Comments | ok |
| GOOGL | workiva | 4 | 23 | ITEM 1.BUSINESS / 1A.RISK FACTORS / 1B.UNRESOLVED STAFF COMMENTS | ok |
| AMZN | workiva | 4 | 23 | Item 1. / 1A. / 1B. | ok |
| MSFT | unknown | 4 | 23 | ITEM 1. BUSINESS / 1A. RISK FACTORS / 1B. UNRESOLVED STAFF COMMENTS | ok |
| TSLA | workiva | 4 | 23 | ITEM 1. BUSINESS / 1A. RISK FACTORS / 1B. UNRESOLVED STAFF COMMENTS | ok |
| CRM | workiva | 4 | 24 | ITEM 1. BUSINESS / 1A. RISK FACTORS / 1B. UNRESOLVED STAFF COMMENTS | ok |
| KO | workiva | 4 | 23 | ITEM 1. BUSINESS / 1A. RISK FACTORS / 1B. UNRESOLVED STAFF COMMENTS | ok |
| BA | workiva | 4 | 23 | Item 1. Business / 1A. Risk Factors / 1B. Unresolved Staff Comments | ok |
| JNJ | workiva | 4 | 23 | Item 1. Business / 1A. Risk factors / 1B. Unresolved staff comments | ok |
| **JPM** | workiva | 4 | **22** | Item 1. Business. / 1A. Risk Factors. / 1B. Unresolved Staff Comments. | **ok** ← C2 fix |
| XOM | workiva | 4 | 22 | ITEM 1. BUSINESS / 1A. RISK FACTORS / 1B. UNRESOLVED STAFF COMMENTS | ok |
| **BRK.B** | workiva | 4 | **17** | Item 1. Business Description / 1A. Risk Factors / 1B. Unresolved Staff Comments | **ok** ← C1 fix |
| UNH | workiva | 4 | 23 | ITEM 1. BUSINESS / 1A. RISK FACTORS / 1B. UNRESOLVED STAFF COMMENTS | ok |
| CAT | workiva | 4 | 24 | Item 1.Business. / 1A.Risk Factors. / 1B.Unresolved Staff Comments. | ok |
| HD | workiva | 4 | 23 | Item 1. Business. / 1A. Risk Factors. / 1B. Unresolved Staff Comments. | ok |
| T | workiva | 4 | 23 | ITEM 1. BUSINESS / 1A. RISK FACTORS / 1B. UNRESOLVED STAFF COMMENTS | ok |
| DIS | workiva | 4 | 23 | ITEM 1. Business / 1A. Risk Factors / 1B. Unresolved Staff Comments | ok |
| **BAC** | workiva | 4 | **23** | Item 1. Business / 1A. Risk Factors / 1B. Unresolved Staff Comments | **ok** ← Bucket 2+4 |
| AMT | workiva | 4 | 22 | ITEM 1. / 1A. / 1B. | ok |
| NEE | workiva | 4 | 23 | Item 1. Business / 1A. Risk Factors / 1B. Unresolved Staff Comments | ok |
| WMT | workiva | 4 | 23 | ITEM 1. / 1A. / 1B. | ok |
| **INTC** | workiva | 0 | 0 | (empty) | **NEEDS_REVIEW** ← out of scope |
| **PG** | workiva | 4 | 0 | (empty) | **NEEDS_REVIEW** ← out of scope |
| USB | workiva | 4 | 23 | Item 1. Business / 1A. Risk Factors / 1B. Unresolved Staff Comments | ok |
| ALL | workiva | 4 | 22 | Item 1A. Risk Factors / 1B. Unresolved Staff Comments / 1C. Cybersecurity | ok |
| **BRK.A** | unknown | 4 | **17** | Item 1. Business Description / 1A. Risk Factors / 1B. Unresolved Staff Comments | **ok** ← C1 fix (same file as BRK.B) |
| SLB | unknown | 4 | 22 | Item 1. Business. / 1A. Risk Factors. / 1B. Unresolved Staff Comments. | ok |

Vendor distribution: workiva ×24, unknown ×4. ALL's `h2_first3` starting at `1A` (not `1`) is a pre-existing pattern from round 1 (not introduced by any fix); ALL's actual filing structure puts Item 1 in an unusual position. Tracked as low-priority observation, not a bucket.

---

## Manual Verification — 3/3 PASS

Run on round 6 final state. Results in `temp/manual-results-round-1.json`.

| Scenario | Title | Result |
|---|---|---|
| S-prep-21 | Tied font-size visual hierarchy spot check on NVDA Item 7 | PASS |
| S-prep-discovery5 | Discovery 5-ticker spot check (PG, USB, ALL, BRK.A, SLB) | PASS |
| S-prep-48 | Promote-to-golden — review baseline_headings.json | PASS |

All three confirmed visual hierarchy and baseline correctness for the post-fix state.

---

## Pending (not in this loop, do not block PR merge)

| ID | Type | Disposition |
|---|---|---|
| S-prep-43, S-prep-44 | Manual (R-15 BAC sub-section accuracy) | DEFERRED — no human-labeled ground truth fixtures. Out of scope per Option D. |
| J-prep-08-UAT | User Acceptance Test (round report usability) | Defer to PR review. Not a Manual Behavior Test → not part of this loop. |
| PG follow-up | Follow-up task | [`task_pg-item-detection-fallback.md`](task_pg-item-detection-fallback.md) |
| INTC follow-up | Follow-up task | [`task_intc-color-hierarchy.md`](task_intc-color-hierarchy.md) |

---

## Validation artifacts preserved for future BDD runs

Code Review may surface additional changes; the next BDD run will need to detect any regressions those introduce. Preserved:

| Artifact | Path | Purpose |
|---|---|---|
| 28-ticker EDGAR HTML cache | `artifacts/current/temp/edgar_cache/` | Saves re-fetch (~131MB, EDGAR_IDENTITY not needed for cached tickers) |
| Last-known-good discovery snapshot | `artifacts/current/temp/discovery_round_6.json` + `.md` | Per-ticker sanity verdict reference. Diff against `discovery_round_N.json` from next run to detect regressions. |
| Last-known-good hard-gate snapshot | `artifacts/current/temp/hard_gate_round_6.json` + `.md` | R-13 baseline regression reference. |
| Manual verification template | `artifacts/current/temp/manual-verification-round-1.html` | Regenerable, but cheap to keep — saves re-templating for next round. |
| Executable verification plan | `artifacts/current/executable-verification.md` | Placeholder-resolved scenario→command mapping. Still valid (no new placeholders). |
| Validation harness | `backend/tests/ingestion/sec_filing_pipeline/validation/` | Committed; re-run with `--mode discovery --tickers all28 --round N`. |
| R-13 hard-gate baseline | `backend/tests/ingestion/sec_filing_pipeline/validation/ground_truth/baseline_headings.json` | Committed snapshot. Hard-gate fails if any of 23 anchor tickers' h1/h2 list diverges. |
| Item detection edge-case research | `artifacts/current/research_item-detection-edge-cases.md` | Documents why JPM/PG/INTC/BRK have different failure modes. Useful background for follow-up tasks. |

### How to re-run BDD regression check after Code Review

```bash
# 1. Unit tests (must pass)
uv run --active pytest backend/tests/ingestion/sec_filing_pipeline/ -q

# 2. Hard-gate (must exit 0; baseline diff signals real regression)
uv run --active python -m backend.tests.ingestion.sec_filing_pipeline.validation \
  --mode hard-gate --tickers existing23 \
  --report-path artifacts/current/temp/hard_gate_round_post_review.json \
  --md-report-path artifacts/current/temp/hard_gate_round_post_review.md \
  --round 7

# 3. Discovery (compare needs_review count + per-ticker h2 list against round 6)
uv run --active python -m backend.tests.ingestion.sec_filing_pipeline.validation \
  --mode discovery --tickers all28 \
  --report-path artifacts/current/temp/discovery_round_post_review.json \
  --md-report-path artifacts/current/temp/discovery_round_post_review.md \
  --round 7

# 4. Diff regression check
diff <(jq '.summary' artifacts/current/temp/discovery_round_6.json) \
     <(jq '.summary' artifacts/current/temp/discovery_round_post_review.json)
# Expected: identical summary (sane=26, needs_review=2). Any change = regression.
```

If discovery round 7 shows `needs_review > 2` or any of the 26 sane tickers regressed: Code Review introduced a regression — investigate before merge.

---

## Commits in this branch

| Commit | Subject | Loop phase |
|---|---|---|
| `b70d601` | feat(sec-pipeline): add sec_heading_promoter primitives for sub-section detection | Pre-loop (original feature) |
| `70c0093` | feat(sec-pipeline): detect Item regions with TOC last-occurrence heuristic | Pre-loop |
| `a6c019b` | feat(sec-pipeline): promote sub-sections to h3/h4/h5 per Item region | Pre-loop |
| `32a66a2` | feat(sec-pipeline): dedup repeated noise text and filter Item self-references | Pre-loop |
| `daee3ab` | feat(sec-pipeline): add Class C fallback for non-bold Item headings | Pre-loop |
| `021c5b1` | test(sec-pipeline): add validation harness for HTMLPreprocessor BDD verification | Phase 0 |
| `66fec6c` | fix(sec-pipeline): dedup TOC PART headings via bold-aware last-occurrence | Round 3 fix |
| `54c8dd1` | fix(sec-pipeline): close Item detection gaps via SSOT and strong-signal promotion | Round 4-6 fixes |

---

## Statistics

- **Branch deltas vs `main`**: 5 production files, ~410 production+test lines added
- **Unit tests added**: +54 (237 → 291)
- **BDD scenarios verified (automated)**: 53 PASS / 5 PENDING (4 deferred + 1 UAT)
- **BDD scenarios verified (manual)**: 3/3 PASS
- **Discovery harness sanity**: 4/28 sane → 26/28 sane (gain of 22 tickers)
- **Hard-gate**: 23/23 PASS (zero regression on 23 anchor tickers)
- **Loop rounds**: 6 automated + 1 manual
- **Subagent dispatches**: 1 research + 3 fixer
