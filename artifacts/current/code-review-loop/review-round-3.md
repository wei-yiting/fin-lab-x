# Code Review Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-08-06

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 1 |
| Blocking | 0 |
| Major | 1 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 2 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | SP-2.1 | ⚠️ Partially Fixed | Inline space-preceded cross-references survive;newline/glued/ALL-CAPS 正確。但新 regex 會匹配較大單字內的 `Item` → X-3.1。 |
| 2 | M-2.1 | ✅ Fixed | legacy `fetch_filing_obj()` 只 locate + `filing.obj()`,不讀 `filing.document`;cache 共用。 |
| 3 | M-2.2 | ✅ Fixed | metadata access 走 `_classify_edgar_error`;429/503/missing-document 有 regression tests。 |
| 4 | M-2.3 | ✅ Fixed | ticker 需 alphanumeric 起首;path-special 拒絕。 |
| 5 | M-2.4 | Accepted | AGENTS.md coexistence subsection 與現狀一致。 |
| 6 | m-2.1 | ✅ Fixed | 零 `design.md` token;inspect helper 為 future extension。 |
| 7 | m-2.2 | ✅ Fixed | force test 驗證 bypass + reparse + overwrite。 |

## Issues

### [Major] X-3.1: `Item` 出現在較大單字內仍會觸發 destructive trim
- **File:** parser.py(_ITEM_HEADING_RE / _is_structural_boundary)
- **Problem:** regex 無左側 lexical boundary,`SubItem 1.` / `LineItem 1A.` 中的 `Item` 被匹配;前方字母被 `_is_structural_boundary` 視為 glued boundary → 靜默截斷後續 substantive text(例:"...SubItem 1. remains..." 截斷在 "Sub")。
- **Fix:** 拒絕一般 alphabetic glue,只對觀察到的 `PART <roman>Item` artifact 保留例外;加 SubItem/LineItem regression tests。

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| edgartools | 5.17.1 | Company.get_filings / Filings.latest / Filing.obj / Filing.document / metadata / Attachment.document | ✅ Current | Context7 + installed source 確認 |
| pydantic | 2.12.5 | ConfigDict(extra="forbid") / discriminated union / Field(min_length=1) / model_copy / JSON | ✅ Current | |

---

# Spec Conformance Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-08-06

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Findings Status

| Issue ID | Status | Notes |
|----------|--------|-------|
| SP-2.1 | Ruling accepted | `EmptyFilingError` 已納入 final contract。 |

## Findings

(無)

## Covered Requirements

12 項全數確認:簽名 + keyword-only store、boundary trim 先於 stub classification、inline cross-ref 保留、stub drop(AAPL bleed stub + JPM/XOM pseudo-stub)、remove-then-measure 機制 + 60k MD&A 存活、degenerate FlatItem-only、frozen schema 完整、citation 三欄由 Filing object 擷取、JSON store 路徑 + round-trip、force 語意、EmptyFilingError legible failure、Seam-1 tests 不打 EDGAR。

---

# Fix Round 3(orchestrator,reviewer-specified fix)

> Date: 2026-08-06

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| X-3.1 | `_is_structural_boundary`:前一字元為字母時,僅當前綴以 `PART <roman>` 結尾(`_TRAILING_PART_RE`)才視為 structural glue;其餘字母黏接(SubItem/LineItem)判為 prose。Regression test 加入 SubItem 1. / LineItem 1A. 保留案例;既有 PART-glue / newline / ALL-CAPS 測試全數維持。 | parser.py, test_parser.py |

Verification: focused 130 passed; full suite 979 passed, 49 deselected; ruff clean.

---

# Code Review Round 4 (targeted: X-3.1)

> Reviewer: gpt-5.6-sol | Date: 2026-08-06

## Verdict

| Issue ID | Status | Notes |
|----------|--------|-------|
| X-3.1 | ✅ Fixed | 一般 letter-glue(SubItem、LineItem、proseItem、ExhibitXIIIItem)不再觸發 trim;string/line start、PART IIIItem、53PART IVItem、period/digit/quote glue 與 ALL-CAPS headings 仍正確截斷。唯讀 assertion matrix 共 14 案例全數通過,未發現 fix 引入的新 trim-path defect。 |

## New Issues

(無)
