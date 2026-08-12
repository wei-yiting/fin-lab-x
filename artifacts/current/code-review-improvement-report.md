# Code Review Improvement Report

> **Task:** DEV-136 — Text fallback path:Title-Case 偵測承重牆(含實作中發現的 edgartools section-shape parse gap 修復)
> **Date:** 2026-08-12
> **Rounds:** 2
> **Reviewer model:** gpt-5.6-sol(Codex,read-only,兩軸)
> **Fixer model:** claude-fable-5(isolated subagent)

## 架構影響摘要

- **Detection 鏈補完為三路**:`detect_blocks()` 現為 markdown H3 → H4 → Title-Case text fallback,三路共用同一 plausibility gate 與 `_assemble`(prelude validity / 零內容流失)。`DetectionSource` type alias 擴為三值;frozen schema 零變更(`"text_fallback"` 本已在 Literal 中)。
- **Parser 對 edgartools 兩種 section 形狀免疫**:`_section_item_key()` 在 `Section.item` 缺值時從 section name 推導 — spaced-name 形狀(MSFT/GE/DIS 型)的 filing 從「parse 出 0 items → `EmptyFilingError`」變為正常 parse。upstream 根因記錄於 DEV-147。
- **Acceptance fixture 依實錄形狀 replay**:`section_item_attr` 欄位(必填、驗證值域)讓 MSFT/GE/DIS probes 以真實的 degraded 形狀走完整 `parse_filing`。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 2 |
| 發現 issues 總數 | 2 |
| Blocking | 0/0 fixed |
| Major | 1/1 fixed(窄修;reviewer 原方向由 user 裁決駁回) |
| Minor | 1/1 fixed |
| Suggestion | 0/0 adopted |
| Spec findings (SP-) | 0/0 |
| 文件修正 | 0(round 2 留一條 PR 描述指示,見未處理項目) |

## Spec Conformance(Spec 軸)

Spec 軸無 findings — 需求覆蓋完整、無 scope creep。Round 1 由 Codex 對照 DEV-136 spec(含三條 ratified handoff 裁決)確認 16 條 requirement 全數 covered;round 2 依 dispatch criteria 跳過(round 1 零 findings,本輪唯一語意變更 41→38 為 user 在 discussion gate ratify 的裁決)。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/ingestion/sec_text_pipeline/block_detection.py` | 核心:fallback 規則組(7 條 rejection + 2 條 context 訊號)+ `detect_blocks` 第三 attempt;`DetectionSource` 三值 alias | ⚠️ |
| 2 | `backend/ingestion/sec_text_pipeline/parser.py` | `_section_item_key()`:`.item` 缺值時由 section name 推導(parse gap 修復) | ⚠️ |
| 3 | `backend/ingestion/sec_text_pipeline/README.md` | 三路鏈的模組地圖同步 | |
| 4 | `backend/tests/ingestion/sec_text_pipeline/conftest.py` | `FakeSection.name` 欄位(鏡射兩種 edgartools 形狀) | |
| 5 | `backend/tests/ingestion/sec_text_pipeline/test_block_detection.py` | 15 個 fallback unit tests(每條規則正反例、鏈順序、降級、tiling) | |
| 6 | `backend/tests/ingestion/sec_text_pipeline/test_parser.py` | 兩個 upgrade-guard 形狀測試 + 既有測試改 kind-agnostic | |
| 7 | `backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py` | AC probes(MSFT 27/14/38/5、GE flat、WMT/DIS 7A 降級鏈)+ 2 個 known-limitation pins | |
| 8 | `backend/tests/ingestion/sec_text_pipeline/fixtures_detection_probes.json` | 實錄資料(MSFT/GE 新錄、WMT/DIS 補 7A、`section_item_attr`)— 資料非逐行 review 對象 | |

## 所有修正問題詳解

### M-1.1(Major)
- **問題:** fallback 把表格片段升格為 heading — 實錄 MSFT Item 7 有 3 個 `(1)ppt`(表格註腳標籤)、Item 1 有 1 個 `Vice Chair and President`(officer 表格 cell)成為 block heading。機制:表格插在真標題與 prose 之間,表格最後一格搶走「下行長 prose」訊號。Orchestrator 核查:4/87 headings 為垃圾,其餘 83 個品質良好;reviewer 宣稱的 bullet 案例在 committed fixture 中不存在;且這 4 個 anchor 繼承自 72-probe 參考演算法(AC 數字本身包含它們),非本實作退化。
- **修法(user 裁決的窄修):** 只加一條 `_FALLBACK_FOOTNOTE_LABEL_RE = ^\(\d+\)` rejection(括號數字 = 財務表格註腳標籤固定格式)。Reviewer 要求的 heading-shape predicate 重設計(字形/大小寫強制、bullet 規則、表格上下文偵測)由 user **駁回**:為 4/87 雜訊率重寫驗證過的 heuristic,且大小寫規則有誤殺 sentence-case 真標題之風險;調參仲裁交給 DEV-138 A/B failure mining(DEV-133 DIS-7 先例)。`Vice Chair and President` 不修,以 current-behavior 測試 pin 為 known limitation。
- **影響:** MSFT 7 blocks 41 → 38(delta 實證為恰好三個 `(1)ppt`;items 1/1a/7a heading list byte-identical)。R&D 等段落的 `block_heading` metadata 不再是垃圾註腳。
- **驗證:** 新 unit test `test_footnote_label_rejected_but_real_heading_anchors`;probe 斷言四個 MSFT items 無任何 heading 匹配 `^\(\d+\)`;known-limitation pin `test_msft_1_officer_table_cell_heading_current_behavior`;全套 1,047 tests 綠。

### m-1.1(Minor)
- **問題:** `section_item_attr` 為選填欄位,CAT/JPM 未錄;`.get()` 讓漏錄或拼錯靜默 replay populated 形狀,弱化「probes 重現真實 edgartools 邊界」的宣稱。
- **修法:** CAT/JPM fixture 補上明確 `"populated"`(orchestrator 以 live edgartools 實測驗證兩者確為 part-aware 形狀);`parse_probe` 改必填存取 + 值域驗證(`"missing"`/`"populated"`,帶 ticker 的錯誤訊息)。
- **影響:** fixture 形狀宣稱不可再靜默失真;未來新錄 ticker 漏欄位會立即炸測試。
- **驗證:** JSON 手術式 diff(4 插入/2 刪除,round-trip byte-identical 驗證);全套測試綠。

## 文件修正

無(README 三路鏈同步屬實作本體,非 review 修正)。

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Dismissed(user decision) | M-1.1 的 heading-shape predicate 重設計(字形/大小寫/bullet/表格上下文) | 4/87 雜訊率、誤殺真標題風險、DEV-133 DIS-7 先例:heuristic 調參由 eval 數據仲裁 | DEV-138 A/B failure mining 若浮現同型失敗再議 |
| Known limitation(pinned) | MSFT 1 `Vice Chair and President` officer-table heading | 無安全結構規則可區分它與真標題;硬寫即 overfit | 同上,已有 current-behavior 測試釘住 |
| PR-authoring note | Round 2 Documentation Gaps:PR 描述須依 envelope §5 以一句話說明測試行數 > 2× production 行數的原因 | 屬 PR 撰寫指示,非 code 缺陷 | 開 PR 時寫入(本 changeset 是偵測承重牆 + 實錄 fixture,測試重是刻意的) |

## Final Verification Results

### Code Level

- [x] Unit Tests:`uv run pytest backend/tests/ -q` → **1,047 passed, 49 deselected**(deselected 為需 Qdrant 的 integration marker,本 diff 未觸及 Qdrant path)
- [x] Lint:`ruff format --check` + `ruff check backend/` → clean
- [x] Type Check:`pyright` on `block_detection.py` + `parser.py` → 0 errors

### Behavior Level

- [x] AC probes(recorded replay):MSFT 1/1A/7/7A → `text_fallback` 27/14/38/5;GE 1A → FlatItem;WMT 7A / DIS 7A → markdown implausible 降級 → fallback 接手
- [x] 零內容流失:`assert_tiles` 於 fallback 路(MSFT 1A + unit)
- [x] 兩種 edgartools section 形狀經 `parse_filing` 皆正常(upgrade-guard tests)

### Runtime / Observable Level

- [x] Live EDGAR 抽查(錄製時執行):MSFT/GE/DIS/WMT 實抓 → fallback/flat 判定與 probes 一致;DIS 內文與 08-05 vintage byte-identical

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/ingestion/sec_text_pipeline/block_detection.py` | +`_FALLBACK_FOOTNOTE_LABEL_RE` 常數與 rejection(M-1.1) |
| `backend/tests/ingestion/sec_text_pipeline/test_block_detection.py` | +footnote-label 正反例 unit test(M-1.1) |
| `backend/tests/ingestion/sec_text_pipeline/test_detection_probes.py` | MSFT 7 re-pin 38、no-footnote-heading 斷言、officer-table known-limitation pin(M-1.1);`section_item_attr` 必填 + 驗證(m-1.1) |
| `backend/tests/ingestion/sec_text_pipeline/fixtures_detection_probes.json` | CAT/JPM 補 `section_item_attr: "populated"`(m-1.1) |
| `backend/ingestion/sec_text_pipeline/parser.py` | 本輪無 review 修正(round 1 即通過) |
| `backend/ingestion/sec_text_pipeline/README.md`、`conftest.py`、`test_parser.py` | 本輪無 review 修正 |

## Learning Notes

### 採用的工程策略

- **「參考實作 faithful port + 事後 ratify 擴充」的兩段式紀律存活下來**:fallback 主體逐條移植 72-probe 驗證過的規則(含 spec 短句沒列的兩條,預先在 ticket 記錄免當偏離);review 發現的 `^\(\d+\)` 缺口則以 ablation 證據走 ratify 流程補上(M-1.1)— 與 DEV-133 SP-1.1 noise-pattern 先例同構。
- **對第三方 metadata 的信任策略**:`_section_item_key` 體現「別把單一 metadata 欄位當唯一真相 — 資訊常在名字裡」;兩種形狀各一個 upgrade-guard 測試,讓 DEV-147 未來升級有明確的紅燈。

### 權衡取捨

- **預期 vs 實際:reviewer 的 Major 不等於要照 reviewer 的藥方修**。M-1.1 的觀察屬實(4 個垃圾 anchor),但其 fix(predicate 重設計)與「heuristic 調參由 eval 仲裁」的專案紀律衝突;最終落點是實證窄修 + known-limitation pin — 觀察與藥方分開評估,是本輪最重要的取捨。
- **Count-pin vs identity-assert**:AC 用 blocks 數量對照 research 證據,review 質疑 count-only 護短;折衷為 count + 定向 identity 斷言(no-footnote-heading、officer-cell pin),不走全面語意斷言(維護成本與 overfit 風險)。

### 關鍵收穫

- **Reviewer 的實證宣稱必須逐項核查**(M-1.1):三項宣稱兩實一虛(bullet 案例不存在於 committed fixture)。核查改變了裁決品質 — 若照單全收會做過度工程,若整案駁回會漏掉三個真實的 `(1)ppt`。
- **「下行長 prose」訊號的結構性盲點**(M-1.1):表格夾在真標題與 prose 之間時,訊號會被表格最後一格竊取 — 真標題被拒、表格 cell 升格。這是 fallback 這類 context-signal heuristic 的通用失敗形狀,A/B failure mining 時值得作為檢查角度。
- **Fixture 的形狀忠實度與內容忠實度同等重要**(m-1.1):replay 測試的價值取決於它重現真實邊界的程度;讓形狀欄位必填 + 驗證,把「fixture 靜默退化成理想形狀」從可能變成不可能。
