# Task: INTC Color-Based Heading Hierarchy Support

## Origin

Surfaced during BDD verification of `feat/enhance-sec-html-heading-promotion` (round 6, 2026-04-09). INTC is the only ticker in the 28-sample where **all** heading counts are zero (`h1=0, h2=0, h3=0, h4=0, h5=0`). Tracked in [`bdd-verification-report.md`](bdd-verification-report.md) as one of 2 remaining `NEEDS_REVIEW` tickers explicitly out of scope for the heading promoter PR.

This task spec is referenced from the markdown_cleanup task at line 328 of `task_filing-markdown-cleanup.md` (sister project), which already noted "INTC 用 color 區分階層".

## Problem

INTC's 10-K rejects every existing heading detection mechanism because the filing uses **color** (`color:#0068b5` Intel blue) as the sole visual heading signal. Specifically:

| Property | Value | Effect |
|---|---|---|
| Bold/font-weight | None used (`font-weight:400` everywhere) | `_has_bold_signal` always False |
| Font-size | Single value throughout (~9pt Arial) | `_has_item_strong_size_signal` rejects (no jump vs body) |
| Heading visual cue | `color:#0068b5` (Intel blue) on PART/Item; `color:#262626` (dark gray) on body | Currently **not parsed at all** by the promoter |
| PART markup | `<div>` or `<td>` containing `<span style="color:#0068b5">PART I</span>` | regex matches but no signal passes the gate |
| Item markup | **2-cell table** — `<td>Item 1.</td>` (label cell) + `<td>Business:</td>` (title cell) inside the same `<tr>` | text is split across cells; `_ITEM_REGION_BLOCKS` includes `<td>` so each cell is scanned individually, but neither cell's stripped text matches `_ITEM_RE` because cell 1 = `'Item 1.'` (regex matches but cell is in `<table>`) and cell 2 = `'Business:'` (regex doesn't match) |
| `_is_isolated_item_block` | Always False for `<td>`/`<th>` per current rule | n/a |

Three failure layers stack:
1. PART/Item recognition fails because of zero bold + zero font-size variation
2. Even if recognized, the Item is split across two `<td>` cells and needs cross-cell text merge
3. Even if merged, `<td>` is filtered from `_is_isolated_item_block`

INTC has 22+ Items in its actual filing — none are detected.

## Two possible directions

### Direction A — Color-based detector (full automation)

Add a heading-color extractor:
1. Compute body color via histogram (most-frequent `color` style across body text spans, weighted by character count) → typically `#262626` or `#000000`
2. Mark any block whose text is rendered in a **distinct, less-frequent color** as a heading candidate
3. Apply existing `_PART_RE`/`_ITEM_RE` filters and add as a fourth promotion path

**Pros**: Generic — would handle any future color-only filer. **Cons**: high false-positive risk (links, footnote markers, table headers all use distinct colors). Also doesn't solve the cross-cell merge for INTC's 2-cell Item structure.

**Estimated complexity**: large (~300-500 lines including tests + cross-ticker validation against the 28-cache to confirm no false positives).

### Direction B — Vendor-specific exception list (pragmatic)

Add a known-quirks registry:
1. Identify INTC by some stable signal: company name from filing metadata, or a fingerprint heuristic (e.g. presence of `color:#0068b5` and absence of any bold styling)
2. For tagged tickers, return early with `sanity_status=CLASS_C_OR_DEGRADED` and an explanatory note
3. Hard-gate accepts CLASS_C_OR_DEGRADED for whitelisted tickers without flagging as regression
4. The validation harness's `tickers_with_zero_h3` list explicitly tags whitelisted ones so reviewers know they're not surprises

**Pros**: small change, no false-positive risk, scoped impact. **Cons**: doesn't solve the underlying problem; INTC content is still not chunked at heading boundaries — retrieval on INTC will be coarse-grained.

**Estimated complexity**: small (~80 lines including registry + harness annotation + tests).

## Recommendation

**Pursue Direction B first**. Reasons:
1. INTC is currently 1 of 28 tickers (3.5%). The cost/benefit ratio for Direction A is high.
2. Direction A would need cross-validation against many more ticker samples to confirm color-based detection isn't worse than the current "ignore" behavior. Without a larger sample, the risk is high.
3. Direction B unblocks the BDD hard-gate (currently INTC is the only ticker in `tickers_with_zero_h3`) and gives reviewers a clean signal that INTC is a known limitation, not a regression.
4. Direction A can be revisited if/when (a) more color-only filers appear in the universe, or (b) downstream chunking/retrieval shows INTC is materially worse than other tickers and worth fixing.

If both directions are eventually needed, Direction B can be implemented now and Direction A can layer on top later — they don't conflict.

## Requirements (Direction B — pragmatic path)

### R1: Vendor-quirks registry

New module `backend/ingestion/sec_filing_pipeline/vendor_quirks.py` (or extend an existing util):

```python
# Pseudo-code:
KNOWN_DEGRADED_TICKERS: dict[str, str] = {
    "INTC": "color-only heading hierarchy (Intel blue #0068b5); no bold/font-size signal",
}

def is_known_degraded(ticker: str) -> tuple[bool, str | None]:
    """Return (True, reason) if ticker is whitelisted as CLASS_C_OR_DEGRADED."""
    reason = KNOWN_DEGRADED_TICKERS.get(ticker.upper())
    return (reason is not None, reason)
```

### R2: Harness reporter integration

In `backend/tests/ingestion/sec_filing_pipeline/validation/reporter.py`:
- For each ticker, call `is_known_degraded(ticker)` after computing `sanity_status`
- If degraded: override `sanity_status` to `CLASS_C_OR_DEGRADED` (new value alongside `ok` / `NEEDS_REVIEW`)
- Add the reason to a new `degraded_reason` field
- Hard-gate (`--mode hard-gate`) treats `CLASS_C_OR_DEGRADED` as PASS instead of FAIL

### R3: Discovery report annotation

`discovery_round_*.md` should list `CLASS_C_OR_DEGRADED` tickers in their own section so reviewers can scan known limitations separately from real issues.

### R4: Unit tests

In `test_validation_harness.py`, add:
- `test_known_degraded_ticker_marked` — INTC returns `(True, ...)`
- `test_unknown_ticker_not_degraded` — random ticker returns `(False, None)`
- `test_hard_gate_accepts_degraded` — full harness run with INTC in baseline; hard-gate exits 0

## Acceptance Criteria

| Criterion | Standard |
|---|---|
| **INTC no longer triggers NEEDS_REVIEW** | discovery harness round 7: INTC `sanity_status=CLASS_C_OR_DEGRADED` with explanatory `degraded_reason` |
| **Hard-gate accepts INTC** | `--mode hard-gate --tickers existing23` exits 0 with INTC in the baseline |
| **No cross-ticker regression** | The other 27 tickers' status unchanged from round 6 |
| **Reviewer-visible signal** | discovery `.md` report has a clearly-labeled "Known Degraded (CLASS_C_OR_DEGRADED)" section listing INTC + reason |
| **Test coverage** | `vendor_quirks` registry + reporter integration each have unit tests |

## Out of Scope (this task)

- **Direction A** color-based detector — track separately if the universe expands
- INTC's Item content extraction — even with this fix, INTC has no h2 anchors. Downstream chunking treats INTC as one big chunk per Part. Acceptable for v2.
- PG follow-up — separate task ([`task_pg-item-detection-fallback.md`](task_pg-item-detection-fallback.md))
- Refactoring the `sanity_status` enum — extending with one new value is fine; full enum refactor is a separate concern

## Implementation Location

- New: `backend/ingestion/sec_filing_pipeline/vendor_quirks.py` (~30 lines)
- Modify: `backend/tests/ingestion/sec_filing_pipeline/validation/reporter.py` (~20 lines)
- Modify: `backend/tests/ingestion/sec_filing_pipeline/validation/__main__.py` if hard-gate logic lives there (~10 lines)
- Tests: extend `test_validation_harness.py` (~50 lines)

**Total**: ~110 lines.

## Future considerations (Direction A backlog)

If color-based heading detection becomes worth pursuing:

1. Pre-requisite: collect 50+ ticker sample to validate color heuristic across vendors
2. Algorithm sketch: histogram body color → mark deviant-color blocks → apply regex filters → handle cross-cell text merge for table-laid Items
3. Cross-cell merge: when a `<tr>` contains exactly two `<td>`s and the first matches `_ITEM_RE` partially (e.g. `'Item 1.'`), join with the second cell's text
4. Risk: links and footnote markers also use distinct colors → need length + position guards similar to `_has_item_strong_size_signal`

Track in this same file as a future addendum if/when prioritized.
