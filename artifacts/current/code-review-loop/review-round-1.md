# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-12
>
> (Copy the model slug and date verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 1 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 1 |

## Issues

### [Major] M-1.1: Text fallback promotes table cells and list entries to headings
- **File:** `backend/ingestion/sec_text_pipeline/block_detection.py` L118
- **Problem:** `_fallback_heading_idxs` claims to find Title-Case heading-shaped lines, but it enforces neither casing nor word shape and does not reject list prefixes or table-cell context. The committed MSFT fixture consequently promotes three `(1)ppt` table footnotes in Item 7 and `Vice Chair and President` from an officer table in Item 1 into blocks. Two bullet entries such as `•offer products to customers` also satisfy the detector and make an otherwise flat Item structured. The acceptance test at `test_detection_probes.py` L200 asserts only the resulting block counts, so it blesses these false anchors instead of checking semantic boundaries. This is already wrong on the committed flagship fixture, not a request for exhaustive filing-variant handling excluded by design-envelope §3; it falls under the live-demo calibration in §7.
- **Fix:** Add an explicit heading-shape predicate that accepts the supported Title Case, sentence-case, and ALL-CAPS heading forms while rejecting bullet/list prefixes, parenthesized table-footnote labels, and table-cell context such as preceding numeric cells. Add regressions using the actual MSFT `(1)ppt` and officer-table fragments, then replace count-only acceptance with assertions for expected heading identities and absence of known table artifacts.

### [Minor] m-1.1: Recorded section shape is optional and silently defaults to populated
- **File:** `backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py` L61
- **Problem:** The fixture documentation says each ticker records `section_item_attr`, but CAT and JPM omit it. Using `.get()` makes an omitted or misspelled value silently replay the populated shape, weakening the acceptance fixture's claim that it reproduces the real edgartools boundary and potentially bypassing the parser fallback being tested.
- **Fix:** Add an explicit `section_item_attr` value to every ticker fixture and access it as a required field. Validate that its value is exactly `missing` or `populated` before constructing `FakeTenK`.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| edgartools | 5.17.1 | Section.item / Section.name duck-typed access | ✅ Current | `_section_item_key` correctly prefers the populated `item` attribute and derives the key from spaced names such as `Item 7A` when `item` is `None`. Both attributes exist in the pinned API; `getattr` is more defensive than required but does not cause a functional issue. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-12
> (Copy the model slug and date verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Findings

None.

## Covered Requirements

✅ Markdown H3/H4 都不 plausible 時,降級到 Title-Case standalone-line fallback — `backend/ingestion/sec_text_pipeline/block_detection.py`
✅ Fallback heading 長度窗為 5–120 — `backend/ingestion/sec_text_pipeline/block_detection.py`
✅ Fallback rejects pure numbers 與 digit clusters — `backend/ingestion/sec_text_pipeline/block_detection.py`
✅ Item 自引行只作 candidate rejection,仍 verbatim 保留於 prelude — `backend/ingestion/sec_text_pipeline/block_detection.py`
✅ Fallback 使用上行非句尾與下個 non-empty line 為 long prose 的 context signals — `backend/ingestion/sec_text_pipeline/block_detection.py`
✅ Fallback rejects 含 `|`、`$`、`%` 的行,以及以 `.`, `,`, `;`, `:` 結尾的行 — `backend/ingestion/sec_text_pipeline/block_detection.py`
✅ Fallback 結果通過與 markdown 路徑相同的 plausibility gate — `backend/ingestion/sec_text_pipeline/block_detection.py`
✅ Fallback 重用 `_assemble` 的 prelude validity、leading-block reclassification 與 zero-content-loss 語意 — `backend/ingestion/sec_text_pipeline/block_detection.py`
✅ 三條 detection path 全部失敗才產出 `FlatItem` — `backend/ingestion/sec_text_pipeline/parser.py`
✅ Plausible markdown H3/H4 優先於 `text_fallback` — `backend/ingestion/sec_text_pipeline/block_detection.py`, `backend/tests/ingestion/sec_text_pipeline/test_block_detection.py`
✅ MSFT Item 1 / 1A / 7 / 7A 經 `text_fallback` 產出 27 / 14 / 41 / 5 blocks — `backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py`
✅ GE Item 1A 的 61k unstructured section 維持 `FlatItem` — `backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py`
✅ WMT 7A 與 DIS 7A 覆蓋 markdown plausibility demotion 後由 fallback 接手的完整鏈路 — `backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py`
✅ `Section.item` 缺失時,從 spaced section name 推導 item key — `backend/ingestion/sec_text_pipeline/parser.py`
✅ Spaced-name/`.item=None` 與 part-aware/`.item` populated 兩種 edgartools shapes 均有 upgrade-guard regression tests — `backend/tests/ingestion/sec_text_pipeline/test_parser.py`
✅ Fixtures 新增 MSFT 1/1A/7/7A、GE 1A,並補錄 WMT/DIS 7A,沿用 filing-level heading lines 與 raw section text 模式 — `backend/tests/ingestion/sec_text_pipeline/fixtures_detection_probes.json`

---

# Orchestrator Verification Appendix (Round 1)

Empirical check of M-1.1's factual claims against the committed MSFT fixture
(all 87 block headings across items 1/1a/7/7a enumerated):

- CONFIRMED: three `(1)ppt` headings in Item 7 (table footnote labels).
- CONFIRMED: `Vice Chair and President` heading in Item 1 (officer-table fragment).
- NOT REPRODUCED: no `•`-prefixed heading exists in any committed MSFT AC item
  (the bullet claim holds only hypothetically against the rule set, not on the
  committed fixture).
- Remaining 83 headings are semantically genuine section headings.
- Note: the reference 72-probe algorithm (same rule set) produced the identical
  27/14/41/5 counts, so the confirmed junk anchors are present in the ratified
  AC numbers themselves — they are inherited reference behavior, not a
  regression introduced by this implementation.

Session note: loop run in the implementing session at the user's direction;
reviewer isolation is cross-model (Codex, read-only) per skill Rule 2.

---

# Round 1 Discussion Gate Resolutions (user decisions, 2026-08-12)

| Issue | Resolution | Decision detail |
|---|---|---|
| M-1.1 | **Partially dismissed / fix with modified direction** | The reviewer's heading-shape predicate redesign (casing/word-shape enforcement, bullet-prefix rule, table-cell-context detection) is **Dismissed (user decision)** — 4/87 junk rate on inherited reference behavior; casing rules risk killing real sentence-case headings; arbitration belongs to DEV-138 A/B failure mining (DEV-133 DIS-7 precedent). Approved narrow fix: single `^\(\d+\)` footnote-label rejection (evidence: 3× `(1)ppt` in recorded MSFT Item 7) + probes re-pin (MSFT 7: 41→38) + no-footnote-heading assertion. `Vice Chair and President` (MSFT 1) stays as **known limitation**, pinned by a current-behavior test. |
| m-1.1 | **Fix as suggested** | Explicit `section_item_attr` for CAT/JPM (orchestrator live-verified both as populated shape); required-field access + value validation in parse_probe. |
