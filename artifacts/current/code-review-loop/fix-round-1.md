# Fix Round 1

> Fixer: claude-fable-5 subagent (isolated) | Date: 2026-08-12
> Scope: user-approved dispositions from Round 1 discussion gate (M-1.1 narrow fix; m-1.1 as suggested). The reviewer's heading-shape predicate redesign was Dismissed (user decision) and NOT implemented.

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 | Added module-level constant `_FALLBACK_FOOTNOTE_LABEL_RE = re.compile(r"^\(\d+\)")` with an evidence comment (MSFT FY2026 Item 7 `(1)ppt` footnotes; review finding M-1.1) in the neighboring constants' style, plus one rejection check in `_fallback_heading_idxs` right after the item-self-reference check. No other rules added. Verified the delta empirically before pinning: MSFT Item 7 heading list diff with rule off vs on is exactly `['- (1)ppt', '- (1)ppt', '- (1)ppt']` (41 → 38); items 1/1a/7a heading lists byte-identical. Updated `expected_blocks` to `{"1": 27, "1a": 14, "7": 38, "7a": 5}`, added a per-block assertion in `test_msft_items_structure_via_fallback` that no heading in any of the four MSFT items matches `^\(\d+\)`, updated the "(27/14/41/5)" comment to explain the 41 → 38 change, and added `TestKnownLimitations::test_msft_1_officer_table_cell_heading_current_behavior` pinning that `Vice Chair and President` IS present in MSFT Item 1 blocks, with a docstring (DIS-7 style) explaining the deliberate non-fix and A/B failure-mining deferral. | `backend/ingestion/sec_text_pipeline/block_detection.py`, `backend/tests/ingestion/sec_text_pipeline/test_block_detection.py`, `backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py` |
| m-1.1 | Fixture: added `"section_item_attr": "populated"` to CAT and JPM via a json round-trip (verified beforehand that `json.dumps(..., indent=1, ensure_ascii=False)` reproduces the existing file byte-identically, so the edit is surgical — 4 insertions / 2 deletions); key placed in the same last position as WMT's. Test: `parse_probe` now uses required access `data["section_item_attr"]` and asserts the value is exactly `"missing"` or `"populated"` with a ticker-labeled message before constructing `FakeTenK`. | `backend/tests/ingestion/sec_text_pipeline/fixtures_detection_probes.json`, `backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py` |

### Not Fixed (with reason)

None.

### Reverted (fix broke tests)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/ingestion/sec_text_pipeline/ -q` | ✅ 129 passed | Re-run after ruff format; still green |
| `uv run pytest backend/tests/ -q` | ✅ 1047 passed, 49 deselected | Full default suite |
| `uv run ruff format backend/` + `ruff check backend/` | ✅ Clean | |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `test_block_detection.py` | Added `TestTextFallback::test_footnote_label_rejected_but_real_heading_anchors` | Positive/negative pair: `(1)ppt` line (passing every other gate) rejected; real headings in same text still anchor |
| `test_detection_probes.py` | Modified `test_msft_items_structure_via_fallback` | MSFT 7 count 38; no MSFT block heading matches `^\(\d+\)`; 1/1a/7a counts unchanged |
| `test_detection_probes.py` | Added `TestKnownLimitations::test_msft_1_officer_table_cell_heading_current_behavior` | Current-behavior pin for the officer-table-cell heading; fails loudly on drift |
| `test_detection_probes.py` | Modified `parse_probe` fixture | Required `section_item_attr` with value validation |
