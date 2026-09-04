# Code Review Improvement Report

> **Task:** DEV-175 — [rag-ingestion] Degraded ingest（parser 端）：detection method 觸發 + schema 分支 + 去雜訊全文 + 儲存
> **Date:** 2026-08-21
> **Rounds:** 2
> **Reviewer model:** gpt-5.5（Codex CLI，reasoning effort high）
> **Fixer model:** Claude Fable 5（code-fixer subagent，session 預設 model）

## 架構影響摘要

- `ParsedFiling` schema 新增一個 additive 分支：`degraded_text: str | None` + `is_degraded` property；`FilingMetadata` 新增 `section_detection_method: str`。這是對凍結 schema 的一次 ratified 變更（ADR-0018），additive 帶 default，既有 stored JSON 讀取相容。
- 新模組 `degraded.py`：對降級全文做去雜訊（cover page + INDEX、簽名頁、page-break 產物、多餘空行），每條規則都是「匹配到錨點才切，匹配不到就整份放行」的 opt-in 設計。
- `parser.py` 新增 filing 層級 detection-method 觸發規則：`pattern` / `html_fallback` / `unknown`（以及標準路徑跑出 0 substantive items 的情況）改走降級分支，不再直接拋 `EmptyFilingError`；`EmptyFilingError` 語意收斂為「降級路徑的全文清理後仍是空的」。
- `inspect_view.py` 的三個渲染函式（`to_inspect_markdown` / `to_summary_text` / `to_section_text`）依 `filing.is_degraded` 分支：呈現降級標記 + 全文預覽、單行 verdict、以及說明性錯誤（取代原本的 per-Item 邏輯）。
- 文件：新增 ADR-0018 + CONTEXT.md「Degraded ingest」詞條，範圍嚴格對齊 parser 端本次交付的狀態；dense 端的檢索能力明確延後到 DEV-177，並已在該票補上對應的 acceptance criterion。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 2 |
| 發現 issues 總數 | 2（Quality 軸）+ 0（Spec 軸） |
| Blocking | 0/0 fixed |
| Major | 1/1 fixed |
| Minor | 1/1 fixed |
| Suggestion | 0/0 |
| Spec findings (SP-) | 0/0（兩輪皆零 findings） |
| 文件修正 | 3 個檔案 |

## Spec Conformance（Spec 軸）

Spec 軸無 findings（Round 1、Round 2 皆為 0）— 需求覆蓋完整、無 scope creep。DEV-175 的 8 條 acceptance criteria 全數確認 covered；round 2 額外驗證了 fix round 對 `CONTEXT.md` 措辭的修正仍準確反映 parser 端交付範圍，未誤植 DEV-177（dense 端 chunking）的終態描述。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/ingestion/sec_text_pipeline/filing_models.py` | `ParsedFiling` schema 的 additive 降級分支 + `section_detection_method`（凍結 schema 的 ratified 變更） | ⚠️ |
| 2 | `backend/ingestion/sec_text_pipeline/degraded.py` | 降級全文去雜訊規則（新模組，正則錨點式清理） | |
| 3 | `backend/ingestion/sec_text_pipeline/parser.py` | filing 層級降級觸發規則 + `EmptyFilingError` 語意收斂（核心 ingest 路徑分支點） | ⚠️ |
| 4 | `backend/ingestion/sec_text_pipeline/inspect_view.py` | 三個 inspect view 函式的降級分支渲染 | |
| 5 | `CONTEXT.md` | 「Degraded ingest」詞條 | |
| 6 | `docs/adr/0018-degraded-ingest-for-fallback-detected-filings.md` | 降級 ingest 決策 + 否決方案記錄 | |
| 7 | `backend/ingestion/sec_text_pipeline/README.md` | Module map / pipeline flow 圖更新 | |
| 8 | `backend/tests/ingestion/sec_text_pipeline/test_filing_models.py` | Schema 相容性測試（舊 stored JSON 缺新欄位仍可 validate） | |
| 9 | `backend/tests/ingestion/sec_text_pipeline/test_degraded.py` | 去雜訊規則逐條正反例單元測試 | |
| 10 | `backend/tests/ingestion/sec_text_pipeline/test_parser.py` | 降級觸發 + `EmptyFilingError` 新語意的 parse_filing seam 測試 | |
| 11 | `backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py` | 三個 inspect view 函式的降級分支渲染測試 | |
| 12 | `backend/tests/ingestion/sec_text_pipeline/conftest.py` | pattern-detection shape fixture 輔助函式 | |

## 所有修正問題詳解

### M-1.1（Major）
- **問題：** `CONTEXT.md` 新增的「Degraded ingest」詞條寫著「All content stays retrievable, but without Item anchors.」，但 dense pipeline 的 chunking 目前只迭代 `filing.items`——降級 filing（`items=[]` + `degraded_text`）送進 embed 流程會產生 0 個 chunk 並拋 `EmptyIngestError`。內容存進了 filing store，但今天還檢索不到，詞條的現在式陳述與現狀不符。
- **修法：** 使用者裁決「fix with modified direction」——只修 `CONTEXT.md` 措辭，不把 dense chunking 提前做進這個 PR（那是 DEV-177 的完整 slice，提前做屬於 cross-slice scope creep）。措辭改為準確描述 parser 端已交付的狀態：全文已保存供後續平面 chunking 使用，檢索能力隨 DEV-177 落地。同時在 DEV-177 補上一條 acceptance criterion，要求該票落地後把終態描述（「全部內容可檢索、無 Item 錨點」）補回詞條。
- **影響：** 避免文件對讀者做出「今天就能檢索降級 filing」的錯誤承諾；DEV-172 三票（175 → 177 → 178）的 slice 邊界維持清楚，未提前擴大本 PR 範圍。
- **驗證：** Round 2 quality reviewer 確認措辭已改為「The full text is thereby preserved for later unstructured flat chunking; retrieval of degraded filings (without Item anchors) arrives with the dense-side flat-chunking slice (DEV-177).」；Round 2 spec reviewer 額外確認新措辭未誤植 DEV-177 的終態描述、未偏離 DEV-175 的 slice 範圍。

### m-1.1（Minor）
- **問題：** 新增的 `docs/adr/0018-*.md`（5 處）與 `README.md`（2 處）裡，DEV-* issue id 以「id 當主詞」的方式出現在說明文字中（例如「DEV-176 sweep」「the DEV-138 A/B evidence」），讓 id 而非描述性內容成為句子的負重點。
- **修法：** 使用者裁決「fix with modified direction」——不採用 reviewer 原建議（整段刪除 id），改為保留 id 供追溯，但把每處引用重排成「描述文字為主體、id 退到括號」的形式，例如「the section-detection sweep (DEV-176)」「the A/B retrieval evaluation's evidence (DEV-138)」。這條規則同時更新進團隊慣例記憶，並排入 background task 去修正舊有 7 份 ADR 裡同樣 id-first 的引用。
- **影響：** 未來讀者不需要回頭查 id 才能看懂引用內容在講什麼；id 仍保留供需要追溯決策脈絡時使用。
- **驗證：** Round 2 quality reviewer 逐一比對 7 處引用，確認皆已改為 description-first、id 括號化，判定「fixed under the ratified convention」。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `CONTEXT.md` | 「Degraded ingest」詞條的可檢索性陳述改為準確反映 parser 端交付範圍（M-1.1） |
| `docs/adr/0018-degraded-ingest-for-fallback-detected-filings.md` | 5 處 DEV-* 引用改為 description-first、id 括號化（m-1.1） |
| `backend/ingestion/sec_text_pipeline/README.md` | 2 處 DEV-* 引用改為 description-first、id 括號化（m-1.1） |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Design issue（範圍延後，非 dismiss） | Dense 端平面 chunking（讓降級 filing 真正可被檢索） | Reviewer 原建議的完整修法；使用者裁決這屬於 DEV-177 的獨立 slice，提前做在本 PR 屬於 cross-slice scope creep | DEV-177 已存在且已補上「CONTEXT.md 終態描述補回」的 acceptance criterion；依既定 frontier（175→177→178）排程 |

## Final Verification Results

### Code Level

- [x] Unit Tests: `uv run pytest backend/tests/` → 1258 passed, 55 deselected（eval-marked，不燒 LLM）
- [x] Lint: `uv run ruff check backend/` → All checks passed
- [x] Format: `uv run ruff format --check backend/` → 209 files already formatted
- [x] Type Check: `uv run pyright backend/ingestion/sec_text_pipeline/` → 0 errors, 0 warnings

### Behavior Level

- 未執行。本 issue 走 issue-direct 流程，無 `implementation.md` / `bdd-scenarios.md` / `verification-plan.md`。DEV-175 spec 本身指定的驗證方式是 `parse_filing → ParsedFiling` seam 上的結構斷言（fixture 模擬 pattern-detection shape）與去雜訊函式的直接單元測試——這些已由 Code Level 的既有測試（`test_parser.py`、`test_degraded.py`、`test_filing_models.py`、`test_inspect_view.py`）覆蓋，不另外自行推導 BDD 場景。

### Runtime / Observable Level

- 未執行。真實語料 E2E（AMD/NVDA 實際 parse → embed → 檢索）與 `sec_retrieval` regression gate 屬於 DEV-178（Journey verification）的獨立 slice；DEV-175 本身已記載 AMD FY2025 repro 為非決定性（2026-08-21 上游偵測為 toc、27 sections，當日不可重現 pattern 分支），降級分支本就只能靠 fixture 在 parse_filing seam 驗證。

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `CONTEXT.md` | M-1.1：「Degraded ingest」詞條可檢索性措辭修正 |
| `backend/ingestion/sec_text_pipeline/README.md` | m-1.1：2 處 DEV-* 引用改為 description-first |
| `backend/ingestion/sec_text_pipeline/degraded.py` | 無 review 修正（兩輪皆無 issue） |
| `backend/ingestion/sec_text_pipeline/filing_models.py` | 無 review 修正（兩輪皆無 issue） |
| `backend/ingestion/sec_text_pipeline/inspect_view.py` | 無 review 修正（兩輪皆無 issue） |
| `backend/ingestion/sec_text_pipeline/parser.py` | 無 review 修正（兩輪皆無 issue） |
| `backend/tests/ingestion/sec_text_pipeline/conftest.py` | 無 review 修正（兩輪皆無 issue） |
| `backend/tests/ingestion/sec_text_pipeline/test_degraded.py` | 無 review 修正（兩輪皆無 issue） |
| `backend/tests/ingestion/sec_text_pipeline/test_filing_models.py` | 無 review 修正（兩輪皆無 issue） |
| `backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py` | 無 review 修正（兩輪皆無 issue） |
| `backend/tests/ingestion/sec_text_pipeline/test_parser.py` | 無 review 修正（兩輪皆無 issue） |
| `docs/adr/0018-degraded-ingest-for-fallback-detected-filings.md` | m-1.1：5 處 DEV-* 引用改為 description-first |

## Learning Notes

> 本 issue 走 issue-direct 流程（無 design.md / briefing.md），以下皆為本次 review loop 首次浮現的收穫，無需 recap 既有筆記。

### 採用的工程策略

- DEV-172 → DEV-175/176/177/178 的票拆分在兩輪 review 中都被 spec 軸驗證為乾淨：parser 端的 PR 沒有滲入 dense chunking 或真實語料驗證的範圍，slice 邊界設計本身經得住審查。

### 權衡取捨

- Spec 原文（DEV-172）描述的是「degraded ingest」這個概念的**終態**（全部內容可檢索），但 DEV-175 只交付其中 parser 端的一半。CONTEXT.md 詞條原本直接照抄終態描述，在只有一半落地的當下就變成 overclaim（M-1.1）。實際處理方式：詞條扣回「本 slice 實際交付的狀態」，終態描述遞延到促成它的那張票（DEV-177）落地時再補回——而不是為了「文件要完整」就把 dense chunking 提前塞進這個 PR。

### 關鍵收穫

- 描述多票 spec 的長效文件（CONTEXT.md、ADR）必須寫「本 slice 交付了什麼」，不能寫「spec 最終要什麼」——即使兩者都是「真的」，時間軸不同；不然一份純文件 PR 就可能在不知不覺間對讀者超額承諾能力（M-1.1）。
- Issue id 出現在說明文字裡時，描述性內容才該是句子主詞，id 退到括號只做追溯用；「the DEV-176 sweep」這種 id-as-noun 的寫法即使有 repo 慣例先例，也應視為尚未校準到位，而非既成標準（m-1.1，已回寫團隊慣例記憶並排入 7 份舊 ADR 的修正）。
- Spec 軸連續兩輪零 findings，本身就是「slice 拆分是否乾淨」的可觀察證據——不需要額外去猜票與票之間有沒有滲透；reviewer 對 M-1.1 的原建議（把 dense chunking 做進來）如果被採納，就會是這個乾淨紀錄的第一個反例。
