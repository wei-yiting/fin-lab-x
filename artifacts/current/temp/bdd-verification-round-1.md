# BDD Verification — Round 1

**Source read**: `backend/ingestion/sec_text_pipeline/block_detection.py`, `parser.py`, `filing_models.py`, `filing_store.py`, and the existing test suite (`test_block_detection.py`, `test_detection_probes.py`, `conftest.py`, `fixtures_detection_probes.json`) — confirmed the Entry Points section of the plan matches the real code.

**Throwaway script**: `artifacts/current/temp/test_verification_round1.py` (34 new test functions/cases, all through the public `detect_blocks`/`parse_filing` seams — no production code touched).

**Baseline**: existing suite confirmed green before writing anything new — `test_block_detection.py` (43 passed), `test_detection_probes.py` (14 passed).

---

### S-fallback-01: 候選行需通過全部 7 條 rejection 規則,含精確邊界值
- **Status**: PASS
- **Method**: script (pytest, synthetic `detect_blocks` calls)
- **Command**: `PYTHONPATH=. pytest artifacts/current/temp/test_verification_round1.py -k s_fallback_01 -v`
- **Actual**: 12/12 PASSED — every row (5/4/120/121 char boundaries, digit cluster, self-ref, footnote, `%`, trailing colon, prev-sentence-end, next-line 80/81) matched the plan exactly.

### S-fallback-02: 候選行前後鄰接空白行或短行時的上下文判定
- **Status**: PASS
- **Method**: script (pytest)
- **Actual**: 4/4 PASSED.

### S-fallback-03: Item 自引比對的格式容忍度
- **Status**: FAIL
- **Method**: script (pytest)
- **Expected**: row1 reject, row2 **pass** ("Item 1A Compliance Program" should anchor as its own heading), row3 both occurrences reject.
- **Actual**: row1 PASS, row2 **FAILED** (plan expects PASS, code rejects it), row3 PASS.
- **Root cause**: `_FALLBACK_ITEM_SELF_RE = re.compile(r"^item\s+\d+[a-c]?\.?", re.IGNORECASE)` (`block_detection.py:106`), applied via `re.match()` at `block_detection.py:138`. `re.match()` anchors only at the start, not the end — it matches the "Item 1A" **prefix** and accepts anything trailing it. Any heading legitimately starting with "Item `<N><letter>`" is indistinguishable from a true self-reference under the current regex.

### S-fallback-04: 攤平表格殘留行不應被誤判為候選標題
- **Status**: FAIL
- **Method**: script (pytest)
- **Expected**: both rows reject.
- **Actual**: row1 PASS, row2 **FAILED** (plan expects reject, code accepts).
- **Root cause**: none of the 7 rejection rules catch space-separated short digit groups. `"12  34  56  78".isdigit()` is `False` (spaces present); `_FALLBACK_DIGIT_CLUSTER_RE = re.compile(r"\d{3,}")` needs 3+ *consecutive* digits, and each group here is only 2 digits wide.

### S-fallback-05 through S-fallback-10, J-fallback-01, J-fallback-02
- **Status**: PASS (all 8)
- Full detail in the task-notification transcript; highlights:
  - S-fallback-07 confirmed the `<=` boundary (3,000 passes whole, 3,001 reclassifies) precisely.
  - S-fallback-08 confirmed all real-ticker detection_source/block-count facts (CAT 7 = markdown_h3, WMT 1A = markdown_h4, WMT 7A/DIS 7A/MSFT ×4 = text_fallback with exact block counts).
  - S-fallback-10 confirmed GE Item 1A is exactly 61,747 chars, zero content loss.

---

## Summary

| Metric | Value |
|--------|-------|
| Total | 12 |
| Passed | 10 |
| Failed | 2 |
| Errors | 0 |

**Failed scenario IDs**: S-fallback-03, S-fallback-04
**Error scenario IDs**: (none)

**Consolidated cross-check**: `pytest backend/tests/ingestion/sec_text_pipeline/test_block_detection.py backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py artifacts/current/temp/test_verification_round1.py -v` → 91 collected, 89 passed, 2 failed, 0 errors. Both pre-existing test files remain 100% green — the 2 failures are isolated to genuinely mismatched rows, not regressions or flakiness introduced by the new script.

Both failures are code-vs-plan mismatches in the fallback rejection-rule set. Per explicit instruction, no fix was attempted this round.
