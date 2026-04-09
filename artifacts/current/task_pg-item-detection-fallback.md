# Task: PG Item Detection Fallback (non-bold + body-equal font-size)

## Origin

Surfaced during BDD verification of `feat/enhance-sec-html-heading-promotion` (round 6, 2026-04-09). PG is one of the 5 random discovery tickers (seed=408 stratified sample). The HTMLPreprocessor's three existing Item detection paths all reject PG's body Item headings, leaving `h2_count=0` while `h1_count=4` (PART promotion works fine).

Tracked in [`bdd-verification-report.md`](bdd-verification-report.md) as one of 2 remaining `NEEDS_REVIEW` tickers explicitly out of scope for the heading promoter PR.

## Problem

PG's body Item headings have a unique combination of properties that defeats every existing detection path:

| Property | Value | Effect |
|---|---|---|
| HTML element | `<div>` containing `<span>` | Standard block container, OK |
| `font-weight` | `400` (non-bold) | `_has_bold_signal()` returns False |
| `font-size` | `10pt` | Same as body 10pt → `_has_item_strong_size_signal` rejects (ratio 1.0 < 1.1) |
| Title visual cue | `<span style="text-decoration:underline">` on title portion | Underline is the only heading signal — currently unused |
| Item text | `'Item\xa01.Business.'` (after BeautifulSoup strip; `\xa0` = `&nbsp;`) | Regex `_ITEM_RE` matches OK |
| Next sibling | Real body `<div>` (PG uses `<div>` as paragraph container, not `<p>`) | `_is_isolated_item_block` sibling check rejects |

PG has 23 unique Item headings (Items 1, 1A, 1B, 1C, 2-9, 9A-9C, 10-15) — none are detected. The result is `h2=0` while the actual filing has a normal Item structure.

### What the existing detection paths miss

```
_promote_headings Item branch:
  should_promote = (
      _has_bold_signal(tag)               # ❌ PG is font-weight:400
      or _is_isolated_item_block(tag, …)  # ❌ next sibling is real body <div>
      or _has_item_strong_size_signal(…)  # ❌ tag font 10pt == body font 10pt
  )
```

All three paths fail simultaneously.

## Requirements

### R1: Recognize `text-decoration:underline` as a heading signal for short Item-regex blocks

Add a fourth fallback path in `_promote_headings`'s Item branch:

```
fourth_path = _has_item_underline_title_signal(tag, text, body_font_size)
```

Where `_has_item_underline_title_signal` returns True when:
- `len(text) < 150` (same length guard as `_has_item_strong_size_signal`)
- The tag contains a `<span>` with `style="...text-decoration:underline..."` whose text length covers ≥30% of the tag's total text (the title portion)
- The tag's dominant font-size **equals** body font-size (this is the discriminator from C2 strong-signal — PG-style filings have no font-size jump)

The 30% threshold prevents promoting tags where a single underlined word in body prose accidentally matches `_ITEM_RE`. PG's Item headings have format `Item N. <underlined title>` where the underlined portion is most of the visible content.

### R2: Validate cross-ticker — PG must rise, the 26 sane tickers must NOT regress

The 26 currently-sane tickers do not depend on underline signal — their Items are bold or have font-size jump. The underline path should be additive and not affect them. **Mandatory validation step**: re-run discovery harness against all 28 tickers and compare round 6 baseline against the post-fix snapshot:

```bash
diff <(jq '.summary' artifacts/current/temp/discovery_round_6.json) \
     <(jq '.summary' artifacts/current/temp/discovery_round_post_pg.json)
```

Expected delta: PG moves from `NEEDS_REVIEW (h2=0)` to `ok (h2≥18)`. Other 27 tickers unchanged.

### R3: Unit tests

In `test_html_preprocessor.py`, add `TestUnderlineTitleSignal` class with at least:

- `test_pg_style_underline_title_promotes` — non-bold `<div><span>Item 1.</span><span style="text-decoration:underline">Business</span></div>` with body font 10pt → promotes to h2
- `test_underline_too_short_rejects` — `<div>Item 1. <span style="text-decoration:underline">x</span> long body text follows here with many many characters</div>` (underline portion < 30% of total text) → does NOT promote
- `test_underline_with_size_jump_uses_strong_signal_instead` — `<div><span style="font-size:12pt">Item 1.</span><span style="text-decoration:underline">Business</span></div>` with body 10pt → promotes via existing strong-signal path (precedence verification)
- `test_underline_path_rejects_non_item_text` — `<div><span style="text-decoration:underline">Some other heading</span></div>` (regex doesn't match) → does NOT promote

## Acceptance Criteria

| Criterion | Standard |
|---|---|
| **PG h2 unlocked** | discovery harness round 7: PG `sanity_status=ok`, `h2_count` in [18, 30] |
| **No cross-ticker regression** | 26 sane tickers stay sane; per-ticker `h2_count` delta = 0 (or ±1 with explanation) |
| **Hard-gate still passes** | 23/23 with re-bootstrapped baseline including PG-equivalent change |
| **Unit tests added** | TestUnderlineTitleSignal with at least 4 cases (positive + negative) |
| **No false positive on running prose** | underline portion threshold (30%) prevents false matches |

## Out of Scope

- INTC color-based hierarchy — separate task ([`task_intc-color-hierarchy.md`](task_intc-color-hierarchy.md))
- Refactoring `_has_item_strong_size_signal` — leave as-is, just add a sibling fourth path
- Detecting underline as a sub-section (h3/h4/h5) signal — out of scope; this task only addresses Item-level h2

## Implementation Location

- Modify `backend/ingestion/sec_filing_pipeline/html_preprocessor.py`:
  - Add `_has_item_underline_title_signal(tag, text, body_font_size)` helper
  - Extend `_promote_headings` h2 branch's `should_promote` chain
- Add tests to `backend/tests/ingestion/sec_filing_pipeline/test_html_preprocessor.py`
- Re-bootstrap baseline: `--mode bootstrap-baseline --tickers existing23` after fix verified

## Estimated Complexity

| Item | Lines |
|---|---|
| `_has_item_underline_title_signal` helper | ~30 |
| `_promote_headings` extension | ~3 |
| TestUnderlineTitleSignal (4-6 cases) | ~80 |
| Validation re-run + baseline rebootstrap | n/a (script) |
| **Total** | **~115** |

Complexity: **medium** (the underline-title heuristic is novel — not a generalization of an existing pattern — and needs careful unit test boundaries).

## Risks

- **PG might use `<u>` tag instead of `style="text-decoration:underline"` in some sections**. The detection should accept both. Verify via grep on the cached `PG_*.html` before implementation.
- **Other Workiva filings may use underline for non-heading purposes** (e.g. emphasized phrases in body prose). The 30% length threshold mitigates but doesn't eliminate. Cross-ticker validation is mandatory before merge.
- **The 30% threshold is arbitrary**. May need tuning after running against the 28-ticker cache. If a sane ticker regresses, adjust before merging.
