# Code Review Improvement Report

> **Task:** DEV-180 — Frozen-HTML-arm header_path compatibility layer for `sec_retrieval_ab` (`html_arm_compat.py` + unit tests)
> **Date:** 2026-08-26
> **Rounds:** 5
> **Reviewer model:** gpt-5.6-luna（透過 Codex，quality 軸與 spec 軸各自獨立 dispatch，cross-model isolation）
> **Fixer model:** claude-sonnet-5（獨立 subagent，每輪與 reviewer 無 context 共享）

## 架構影響摘要

本次 review 無架構層面的變更，所有修正皆為 correctness / stability / documentation。這支模組本身是一支獨立、範圍限定的新模組（`sec_retrieval_ab/html_arm_compat.py`），未修改既有 `sec_retrieval` scorer、未修改 frozen pipeline，也未新增任何跨模組相依。5 輪修正的重心分兩類：

- **Test fixture 完整性**（Round 1-3）：module docstring 明文承諾「fixture 取材自真實錄下的 pipeline 輸出，不是憑空編的字串」，但實際檢查發現多處違反這個承諾——從最明顯的假資料（`"text": "unchanged"`）到最隱蔽的（逗號被悄悄改成句號、header_path 少一段真實存在的 tail、`ingested_at`/`score` 被跨 chunk 混用）。
- **Production code 正確性**（Round 2、4）：兩個真正會影響計分結果的邏輯漏洞（`Item 9A(T)` 歷史格式、header_path 段落前導空白），兩者都不是從 diff 表面看得出來的，而是靠逐一比對 frozen pipeline 自己的原始碼（`vectorizer.py`）才挖出來的。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 5 |
| 發現 issues 總數 | 8（跨軸合併重複項目後計數） |
| Blocking | 3/3 fixed |
| Major | 3/3 fixed |
| Minor | 2/3 fixed（1 個由使用者決定 dismiss） |
| Suggestion | 0/0 |
| Spec findings (SP-) | 2/2 fixed |
| 文件修正 | 1（module docstring 的 synthetic-test 數量宣稱） |

## Spec Conformance（Spec 軸）

> 與 Quality 軸並列呈現，不合併排序。每筆引用對應的 spec 來源行。

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented | "unit test 的 fixture 是從真實錄下的 frozen HTML pipeline 輸出取出來的，不是憑空編的字串"（User Story #9） | Fixed（Round 1，commit `23befb6`） |
| SP-2.1 | Misimplemented | 同上（User Story #9），針對 Round 1 修正後仍殘留的截斷問題 | Fixed（Round 2，commit `8f979a0`） |

Round 3-5 的 spec 軸複核均為 0 findings（Round 4 做了完整重新掃描全部 spec 需求，包含針對 `Item 9A(T)` 修正是否算 scope creep 的獨立判斷——結論是 in-spec，是 User Story #3「用 canonical title 重建」原則的自然延伸）。

## Reading Guide

> 給人類 reviewer 的建議閱讀順序。這是 slice PR 的導覽表——不必從上到下讀整個 diff，依此表逐檔查看即可。

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py` | 核心邏輯：`normalize_chunk`/`normalize_chunks`，header_path 正規化演算法 | |
| 2 | `backend/evals/scenarios/sec_retrieval_ab/__init__.py` | package docstring，說明這個目錄目前只有相容層，dataset/eval_spec 待後續票 | |
| 3 | `backend/tests/evals/test_html_arm_compat.py` | 9 個 unit test，覆蓋 Part 移除、title 重建（兩種落差情境）、nested tail 保留、未偵測 item、`Item 9A(T)` 歷史格式、header_path 前導空白 | |

三個檔案都不觸及外部 API、schema、wire format、migration 或 security 路徑，故無 `⚠️` 標記。

## 所有修正問題詳解

### M-1.1 / SP-1.1（Major / Blocking，Round 1，已修正 — commit `23befb6`）
- **問題：** Module docstring 宣稱所有 fixture 都是真實錄下的 chunk，只有一個防禦性測試例外。實際上三處違反：`test_normalize_chunks_maps_normalize_chunk_over_a_list` 用了憑空編的 `"text": "unchanged"`；nested-heading 測試把真實的多欄位財報表格手動簡化成單行；`Item 15` wording-divergence 測試的文字寫成「Taiwan-headquartered **suppliers**」，但真實錄下的內容是「...**customers** was attributed to end customers...」——這個字根本不存在於原始資料裡（此為 orchestrator 自行比對 CSV 發現，兩個 reviewer 都沒抓到）。
- **修法：** 從 `backend/evals/regression/reference_measurements/sec_retrieval/2026-08-19_73faf5f.csv` 逐一撈出對應 `chunk_index` 的真實逐字內容，取代三處假資料。
- **影響：** 這些欄位本身不影響 `normalize_chunk` 的邏輯（`text` 只是原樣傳遞），但直接違背測試檔案對下一個 reviewer 的完整性承諾，也是 spec User Story #9 明文要求的驗收條件。
- **驗證：** `pytest backend/tests/evals/test_html_arm_compat.py -v` 7/7 通過；`pytest backend/tests/evals/ -v` 254/254 通過；後續 Round 2-5 reviewer 逐字元複核確認無誤。

### B-2.1 / SP-2.1（Blocking，Round 2，已修正 — commit `8f979a0`）
- **問題：** Round 1 修正時「照抄」了另外兩個原本以為正確的 fixture，實際上它們也各自被動過手腳：`NVDA chunk_index=25` 的截斷處把逗號改成句號、製造出一個假的完整句子；`AMD chunk_index=152` 同樣手法，而且它的 `header_path` 還少了真實存在的 `/ Overview` tail 段。
- **修法：** 兩個欄位都改回從 CSV 逐字複製，在真實的句子邊界截斷（不新增標點），並補回 `header_path` 缺的 tail。
- **影響：** 同 M-1.1 性質——不影響程式邏輯，但持續違背 fixture 完整性承諾；兩個獨立的 Round 2 reviewer（quality 軸、spec 軸）各自獨立判定這是真正的 spec violation。
- **驗證：** `pytest backend/tests/evals/ -v` 255/255 通過；Round 3 reviewer 用 `csv.DictReader` + hash 比對逐字元確認兩處 fixture 現在都是 CSV 的 verbatim prefix。

### B-3.1（reviewer 標 Blocking；orchestrator 建議降級但改用不同修法，Round 3，已修正 — commit `df42914`）
- **問題：** 完整逐欄位 re-audit 發現多個「真實」fixture 的 `ingested_at`/`score` 也對不上 CSV。追查後拆成兩種性質：`ingested_at` 對每個 chunk 是固定值（跟哪個 query 撈到它無關），有兩處被跨 chunk 誤植（`INTC/134`、`NVDA/25` 都誤用了 `AMD/152` 的時間戳）；`score` 本質上是 (query, chunk) pair 的屬性（來自 `retriever.py` 的 Qdrant `point.score`，即 embedding cosine similarity），同一個 chunk 在不同 query 下分數不同，而這些 unit test 完全沒有 query 語境，所以「正確值」這個概念本身就不成立。
- **修法：** 沒有嘗試把兩個欄位「修對」，而是直接從 5 個真實 fixture 移除 `ingested_at`/`score`——因為 `normalize_chunk`/`normalize_chunks` 完全不讀這兩個欄位，且這個檔案本來就有「fixture 只放測試真正關心的欄位」的既有慣例（`test_normalize_chunks_maps_normalize_chunk_over_a_list` 一直都沒有這兩個欄位）。
- **影響：** 不影響任何邏輯覆蓋率；比起保留一個看似權威、其實是編造或混用的數字，直接拿掉更誠實。
- **驗證：** `pytest backend/tests/evals/ -v` 255/255 通過；Round 4 reviewer 完整重新掃描確認移除後仍完整覆蓋 Testing Decisions 指定的代表性情境（Part 移除、兩種 title 落差、nested tail、未偵測 item）。

### M-2.1（Major，Round 2，已修正 — commit `8f979a0`）
- **問題：** 真正的 production code bug，非測試問題。Frozen pipeline 自己的 item 偵測 regex（`vectorizer.py` `parse_item()`）明確支援歷史格式 `Item 9A(T)`（約 2008-2010 年，內控簽證暫時豁免條款），`html_arm_compat.py` 的 `_ITEM_SEGMENT_RE` 也複製了同一個 regex 去定位 header_path 段落，證明作者知道這個格式存在。但 canonical title 查表用的 key（`item[len("Item "):].lower()`）沒有去掉 `(T)` 後綴，`"Item 9A(T)"` 算出來是 `"9a(t)"`，`TENK_STANDARD_TITLES` 裡只有 `"9a"`，查不到就把整個 chunk 當「查無此 item」原樣放行——Part 段留著，變成一次不誠實的 false miss。
- **修法：** 在查表前對 key 做 `.removesuffix("(t)")`，讓 `"Item 9A(T)"` 解析到跟 `"Item 9A"` 一樣的 canonical title。新增一個明確標示為 synthetic 的回歸測試（真實 CSV 裡沒有這個歷史格式的樣本，測試 docstring 有說明）。
- **影響：** 這是三輪裡唯一會實際影響計分正確性的邏輯漏洞（另一個是 M-4.1）。Round 4 spec reviewer 額外判定這個修正屬於 in-spec，不是 scope creep。
- **驗證：** orchestrator 手動追過一次程式邏輯確認修正正確；`pytest backend/tests/evals/ -v` 256/256 通過。

### M-4.1（Major，Round 4，已修正 — commit `62dd476`）
- **問題：** 第二個真正的 production code bug。`vectorizer.py` 的 `_build_header_path()` 組出 `header_path` 時，只 strip 整條字串的頭尾跟自己這層的 heading text，沒有對每個中間層級（祖先 heading）個別 strip；而 `parse_item()` 抽 `item` 欄位時則有對每個 level 個別 strip。所以理論上 `header_path` 裡某段可能帶有前導空白（例如 `"Part I /   Item 1. Business"`），而 `item` 欄位本身是乾淨的。`html_arm_compat.py` 的 `_ITEM_SEGMENT_RE.match(segment)` 沒有 strip，遇到這種段落會直接比對失敗、整個 chunk 原樣放行。
- **修法：** 比對前先對 `segment` 做 `.strip()`。新增一個明確標示為 synthetic 的防禦性測試（真實 CSV 裡 84 個不重複 chunk 都沒有這個問題，orchestrator 已逐一查證，這是理論上可達成但目前未觀察到的情境）。
- **影響：** 修正成本是一行 regex 加固，不是新機制；即使可達成性證據比 M-2.1 弱，成本效益仍然favor修。
- **驗證：** orchestrator 手動追過邏輯確認：若無此修正，該測試案例會因為 regex match 失敗而斷言不符，證明測試真的在保護這個行為；`pytest backend/tests/evals/ -v` 256/256 通過。

### m-3.1（Minor，Round 3，已修正 — commit `df42914`）
- **問題：** Module docstring 說「except the one test」，但經過 M-2.1 的修正後已經有兩個 synthetic test（`Item 99`、`Item 9A(T)`），文件跟現況不符。
- **修法：** 改成「except the tests that exercise defensive paths...」，不特別點名哪幾個（避免文件跟測試名稱綁死）。
- **影響：** 純文件準確性問題。
- **驗證：** 目視確認文字與現況相符；`ruff check`/`ruff format` 通過。

### m-4.1（Minor，Round 4，已修正 — commit `62dd476`）
- **問題：** Module docstring 明文承諾 `normalize_chunk` 「回傳新 dict，chunk 不會被 mutate」，但既有斷言全部是 `normalized == {**chunk, ...}` 形狀——就算實作改成直接 mutate 輸入再回傳同一個物件，測試一樣會過，完全沒保護這個承諾。
- **修法：** 對每個直接呼叫 `normalize_chunk` 的測試，補上 `normalized is not chunk`（物件不同）與呼叫前後 `chunk == original` 快照比對（內容不變）；`normalize_chunks` 的 list 測試同理，對兩個輸入 chunk 都做相同檢查。
- **影響：** 補齊測試嚴謹度，讓 docstring 的承諾真正被驗證，而不只是宣稱。
- **驗證：** `pytest backend/tests/evals/test_html_arm_compat.py -v` 9/9 通過（含新增與修改的斷言）。

### m-1.1（Minor，Round 1，Dismissed — 使用者決定）
- **問題：** Reviewer 建議把 `normalize_chunk(chunk: dict)` 的 `dict` 換成 `TypedDict`，明確標出 `item`/`header_path`/`ticker`/`year` 等必要欄位的 schema。
- **決定：** Dismissed。這支模組要餵資料進去的對象——`backend/evals/scenarios/sec_retrieval/scorer.py`——同一份 chunk 形狀全部也是用純 `dict`，完全沒有 `TypedDict`。替 `html_arm_compat.py` 單獨加型別會跟它要互通的 sibling module 型別慣例不一致，而這支模組本身還有排定的刪除時間點（隨 frozen pipeline 一起在 sunset 時砍掉），投資型別基礎建設的報酬率偏低。
- **後續：** 不會在後續 round 重提。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `backend/tests/evals/test_html_arm_compat.py` | Module docstring 的 synthetic-test 數量宣稱從「one」改為準確反映現況的「the tests that exercise defensive paths...」（m-3.1） |

## 未處理項目

無。所有 undisputed findings 都已修正並驗證；唯一的 disputed finding（m-1.1）已由使用者明確 dismiss，不是延後處理。

## Final Verification Results

### Code Level

- [x] Unit Tests：`backend/tests/evals/test_html_arm_compat.py` 9/9 通過；`backend/tests/` 全套 1225 passed, 55 deselected（`-m eval` regression gate 案例，依 AGENTS.md 慣例排除在預設跑法之外）、0 failed
- [x] Lint（`ruff check backend/`）：All checks passed!
- [x] Format（`ruff format --check backend/`）：210 files already formatted
- [x] Type Check（`pyright` 針對三個變更檔案）：0 errors, 0 warnings, 0 informations

### Behavior Level

未執行。此變更是無 UI／無 API endpoint 的純 Python 內部工具模組，且不存在 `bdd-scenarios.md`/`verification-plan.md`/`implementation.md`。曾提議額外跑一次「把 `normalize_chunks()` 輸出接上真正未修改的 `sec_retrieval` scorer 函式」的整合驗證，經與使用者確認，Code Level 已足夠，不需額外執行。

### Runtime / Observable Level

不適用（無執行環境、無外部服務相依，測試完全離線跑在 fixture 資料上）。

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/evals/scenarios/sec_retrieval_ab/__init__.py` | 無修正（package docstring，Round 1-5 皆無 findings） |
| `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py` | 2 個 production code bug 修正：`Item 9A(T)` canonical title 查表（M-2.1）、header_path 段落前導空白比對（M-4.1） |
| `backend/tests/evals/test_html_arm_compat.py` | Fixture 完整性修正 3 輪（M-1.1/SP-1.1、B-2.1/SP-2.1、B-3.1）；新增 2 個回歸測試（`Item 9A(T)`、前導空白）；補齊 non-mutation 斷言（m-4.1）；docstring 準確性修正（m-3.1） |

## Learning Notes

### 採用的工程策略

- 原始設計「fixture 必須取材自真實錄下的 pipeline 輸出」這個策略本身在實作中存活下來，但比預期更難一次到位——花了 3 輪、從最表層（`text` 內容）到中層（`header_path` 結構）到最深層（`ingested_at`/`score` 這種 code under test 根本不讀的旁支欄位）才真正做到滴水不漏（M-1.1/SP-1.1、B-2.1/SP-2.1、B-3.1）。
- Cross-model review（Codex 當 reviewer、Claude 當 fixer）在這個 slice 裡展現出實質價值：兩個真正的 production bug（M-2.1、M-4.1）都不是從 diff 表面看得出來的，reviewer 主動去讀了 frozen pipeline 自己的原始碼（`vectorizer.py`）才挖出來——同一個 session 寫完就自己審，大概率不會想到去翻依賴的上游程式碼。

### 權衡取捨

- Spec 原文對 fixture 的要求是字面上的「不是憑空編的字串」，一開始的直覺修法是把 `score`/`ingested_at` 也「修到跟 CSV 一致」。但深入追問「`score` 到底是什麼」之後才發現：它是 (query, chunk) pair 的屬性，這些 unit test 完全沒有 query 語境，所謂「正確值」根本不存在——所以最後選擇移除欄位而非強行湊一個看似正確的數字。這是一個從「照字面遵守 spec」到「理解 spec 背後的意圖」的修正，記在 B-3.1。
- M-4.1 的可達成性證據明顯比 M-2.1 弱（84 個真實 chunk 裡一個都沒出現這個問題，純粹是讀程式碼推論出的理論可能性），但因為修正成本趨近於零（一行 `.strip()`），最終還是選擇修——這跟 design-envelope 的「YAGNI cost/benefit」判斷邏輯一致：便宜的加固不需要跟昂貴的新機制用同一把尺衡量可達成性門檻。

### 關鍵收獲

- **Fixture provenance 的驗證範圍必須涵蓋每一個欄位，不只是 code under test 實際讀取的欄位**——`ingested_at`/`score` 從未被 `normalize_chunk` 使用，卻仍然是文件承諾「fixture 是真實資料」的一部分，也仍然可能被跨 chunk 誤植（B-3.1）。
- **當一個欄位在特定情境下沒有唯一正確值時，誠實的做法是拿掉它，而不是編一個看起來合理的值**——這個原則不只適用於這支模組，任何測試 fixture 只要牽涉到 context-dependent 的欄位都適用（B-3.1）。
- **抄用別處「已驗證正確」的 fixture 前，要重新驗證，不能只信任來源標籤**——Round 1 修正時「借用」了另外兩個測試裡的 chunk，以為它們沒問題，結果 Round 2 才發現它們自己也帶著同樣的截斷瑕疵（B-2.1/SP-2.1）。
- **一個 regex pattern 只要被複製到第二個地方比對同一份資料，就必須複製它原本的正規化步驟（這裡是 `.strip()`），而不能假設輸入已經是乾淨的**——這是 M-4.1 的直接教訓，也是 M-2.1（`(T)` 後綴沒有一併處理）背後同一類疏漏的變形。
