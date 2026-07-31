# Code Review Improvement Report

> **Task:** DEV-106 — native reasoning parts + reasoning chips + placeholder ActivityIndicator（review-fix loop，2026-07-28 manual-test fixes 之後）
> **Date:** 2026-07-28
> **Rounds:** 3（quality 軸 3 輪、spec 軸 3 輪；Round 3 剩餘 2 個一行文件修正由 orchestrator 直接處理，未另開 Round 4）
> **Reviewer model:** Codex `gpt-5.5`（quality 軸與 spec 軸皆為 Codex，per user 指定;cross-model isolation vs. Claude fixer）
> **Fixer model:** Claude Sonnet 5（general-purpose subagent，read/write，兩輪 fixer dispatch + orchestrator 直接處理 Round 3 尾項）

## 架構影響摘要

本次 review 無架構層面的變更，所有修正皆為 correctness / stability / documentation。範圍限定在 DEV-106 refactor 已實作完成之後的品質收斂，不涉及新設計決策（唯一例外：window(a) 的文件更正屬於既有裁決的事後承認，非新決策，且已明確標記完整裁決收斂留給 DEV-108）。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 3（+ orchestrator 直接修正的收尾） |
| 發現 issues 總數（去重後，含 Quality + Spec） | 16 個真實 issue（另有 3 個經查證為 false positive / 已知接受，見「未處理項目」） |
| Blocking | 2/2 fixed |
| Major | 5/5 fixed |
| Minor | 7/7 fixed |
| Suggestion | 0/0 |
| Spec findings（SP-，扣除重複與 false positive） | 3/3 fixed（1 Blocking 程式碼修正、1 Blocking 文件刪除、1 Major 文件修正） |
| 文件修正 | 9 處（跨 8 個檔案） |

## Spec Conformance（Spec 軸）

> 與 Quality 軸並列呈現，不合併排序。Spec 軸全程由 Codex 執行（user 指定，取代原先 Claude 執行的第一輪）。

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| tool-call-chunk 強制關閉 reasoning part | Misimplemented | "Chip/tool-card time overlap ... 不強制立即收合"（2026-07-26 comment §B；`bdd-scenarios.md` S-chip-06） | ✅ fixed（Round 1，Round 2/3 重新確認） |
| `backend/tests/scripts/README.md` 未依 envelope §6 刪除 | Missing | "backend 測試資料夾 README 依 design-envelope §6 刪除（named precedent）"（DEV-106 AC5） | ✅ fixed（Round 2，Round 3 重新確認無殘留引用） |
| window(a) 文件與 shipped code 不符 | Misimplemented（文件面） | "`useChat.status`...placeholder 空窗 (a) 應 key 在 `status === 'submitted'`"（2026-07-26 comment §C） | ✅ fixed（文件更正為現況，Round 2/3 確認準確；code 本身的工程判斷已由兩輪獨立 review 認可，完整裁決收斂明確留給 DEV-108） |
| Reload 會清掉 user prompt | Missing | "Reload during an in-flight stream...user prompt 留著"（2026-07-26 comment §B） | ⏸ accepted — user 明確確認這是預期中未實作的功能，非本 slice 缺陷 |
| Zero-delta reasoning 仍送 wire start/end | Misimplemented（誤判） | 誤引 `verification-plan.md` S-parts-05 | ❌ 已查證為 false positive（實際跑 `test_empty_delta_not_emitted`，確認對應的是 S-chip-08，非 S-parts-05） |
| `LiveStatusAnnouncer` 留在 production | Scope creep（誤判） | 誤引「被刪的 LiveStatusAnnouncer」措辭 | ❌ 已查證為 false positive（DEV-60 2026-07-23 comment 明文裁決保留，早於且優先於後續措辭不精準的 comment） |

## Reading Guide

> 給人類 reviewer 的建議閱讀順序，依 review loop 這 15 個觸及檔案的依賴順序排列，不是整份 DEV-106 diff（那份已在此 loop 開始前完成並經過 two-axis-review）。

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/agent_engine/streaming/event_mapper.py` | 移除 tool-call-chunk 強制關閉 reasoning part 的錯誤 boundary，改用既有的 chunk-id-transition/text/finalize 邊界 | ⚠️ wire-format 相關 core logic |
| 2 | `backend/tests/streaming/test_event_mapper.py` | 對應第 1 項的測試重寫 + docstring 更正 | |
| 3 | `frontend/src/components/pages/ChatPanel.tsx` | `resetForNewTurn()` 不再清空整個 chip 計時 map，只有 `handleClearSession` 保留全清 | ⚠️ 影響 transcript 歷史顯示正確性 |
| 4 | `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` | 新增測試鎖住第 3 項的 regression | |
| 5 | `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` | 加強既有測試斷言，從寬鬆 regex 改為精確文字比對 | |
| 6 | `frontend/tests/e2e/smoke/slow-start-stream.spec.ts` | E2E 斷言更正（`toHaveText` 對應實際 DOM textContent，非 CSS 生成內容） | |
| 7 | `frontend/src/lib/reasoning-chips.ts` | 檔案註解更正非 derived store 數量（3→4） | |
| 8 | `frontend/src/hooks/README.md`、`frontend/src/components/pages/README.md`、`backend/agent_engine/streaming/README.md`、`backend/agent_engine/agents/README.md`、`backend/scripts/validation/README.md` | 文件與現況同步（5 個檔案，見「文件修正」表） | |
| 9 | `backend/scripts/validation/verify_langfuse_trace.py` | docstring 更正 + 刪除死碼 `_latest_generation()` | |
| 10 | `backend/tests/scripts/README.md` | 依 envelope §6 precedent 刪除 | |
| 11 | `artifacts/current/bdd-scenarios.md` | window(a) 設計註記更正為現況，標記舊框架 superseded | |

## 所有修正問題詳解

### M-1.1（Major，Quality）— chip 計時 map 在每次新一輪對話時被整批清空
- **問題：** `resetForNewTurn()` 呼叫 `useReasoningTimers().reset()` 清空整個計時 `Map`；`observe()` 每次 render 都會對**全部** messages（含已完成的舊 turn）重新推導計時，舊 chip 因為 `hasLaterPart` 已為 true 而立即凍結在 `0s`，導致 transcript 上先前顯示的 `Thought for 3s` 在下一輪 send/regenerate/retry 時瞬間變成 `0s`。
- **修法：** `resetForNewTurn()` 不再呼叫 `resetTimers()`；全清邏輯只保留在 `handleClearSession()`（整個 chat 重置，畫面上沒有任何殘留內容可污染）。`chipKey(msg.id, i)` 本身已依 message id 隔離，不需要 turn 級別清空；另確認 `regenerate()` 不會重用舊 assistant message id（查證 AI SDK 原始碼），因此不需要額外的 per-message pruning API。
- **影響：** transcript 上已完成 turn 的 `Thought for Xs` 標籤在後續對話中維持穩定，不再被新一輪送出干擾。
- **驗證：** 新增 `useReasoningTimers.test.ts` 測試（觀察不相關新 turn 的 messages 不影響已凍結的舊 chip 計時）；`ChatPanel.integration.test.tsx` 加強為精確文字比對(`Stopped — thought for Ns` 送出前後逐字不變)，並手動用 `git stash` 驗證此測試在修復前的程式碼上會 fail。

### tool-call-chunk 強制關閉 reasoning part（Blocking，Spec）
- **問題：** `_handle_tool_call_chunk_block()` 無條件呼叫 `_close_reasoning_part()`，在 tool 參數還沒完全組好前就送出 `reasoning-end`，牴觸 S-chip-06 裁決（Gemini 提前送 tool 參數時，tool card 應排在還開著的 chip 下方，不強制提前收合）。連鎖 test 也把錯誤行為鎖進去當作預期。
- **修法：** 移除該行強制關閉呼叫。reasoning part 改為只在既有、已測試過的邊界關閉：text block 到達、下一輪 LLM call id 轉換（`_handle_messages` 既有的 chunk-id-transition guard）、同一 chunk 內連續兩個 reasoning block、或 `finalize()`。重寫對應測試 `test_tool_call_chunk_does_not_close_open_reasoning_part`，新增 `test_tool_call_chunk_then_new_llm_call_closes_part_exactly_once` 驗證 terminal case 仍正確關閉恰好一次。
- **影響：** 前端現在能真正實現 S-chip-06 的視覺行為（tool card 顯示在還開著的 reasoning chip 下方），先前這個裁決在後端從未被正確實作過。
- **驗證：** `backend/tests/streaming/` + `backend/tests/agents/` 221/221 通過；Round 2、Round 3 兩輪 Spec review 各自獨立重新檢視程式碼，確認修正正確且無遺漏 edge case。

### m-1.1 ~ m-1.4（Minor ×4，Quality）— backend F5 重構遺留的文件/死碼漂移
- **問題：** `verify_langfuse_trace.py` docstring 誤述為 per-generation 而非實際的 per-trace 契約；`scripts/validation/README.md` 仍描述已刪除的 `reasoning_tail_aborted` per-generation marker；`agent_engine/agents/README.md` 仍說 abort cleanup 會撈取已刪除的 segmenter tail；`_latest_generation()` 是刪除 per-generation 斷言後留下的死 helper。
- **修法：** 逐一改寫為對應現況的正確描述；確認 `_latest_generation()` 全 repo 零引用後刪除。
- **影響：** 消除 4 處會誤導未來維護者的文件/死碼殘留。
- **驗證：** `uv run ruff check backend/` 全綠；相關檔案的既有測試無回歸。

### M-2.1（Major，Quality）— E2E 測試斷言與實際 DOM 文字不符
- **問題：** `slow-start-stream.spec.ts` 斷言 `toHaveText("Thinking…")`，但 `ActivityPlaceholder` 的實際 DOM 文字是 `"Thinking"`（點點動畫是另一個 `aria-hidden` span 的 CSS `::after` 生成內容，不算進 `textContent`）。此為這個 session 稍早 dots 動畫修正（`5ddb0f6`）遺留的 regression，當時只跑了 vitest + tsc/eslint，沒人跑過 Playwright e2e。
- **修法：** 改為 `.toHaveText("Thinking")`，與元件、既有 unit test、docs 一致。
- **影響：** 修復一個原本會在 CI 或任何實際 Playwright 執行時失敗的測試。
- **驗證：** orchestrator 實際安裝 Playwright chromium 並執行此測試——修復前重現失敗（`Expected: "Thinking…" ... unexpected value "Thinking"`），修復後通過；Final Verification 階段整個 `@smoke` 套組（5 個測試）全數通過。

### 非 derived state「恰好三個」措辭漂移（Major，Quality + Spec 共同發現）
- **問題：** `useDeadAirPlaceholder.ts` 實際擁有第 4 個非 derived store（`elapsedGapKey` + `PLACEHOLDER_GRACE_MS` timeout，用來區分「chip 收合→tool」與「chip 收合→reply text」），但 `hooks/README.md`、`ChatPanel.tsx` 註解、`pages/README.md`、`reasoning-chips.ts` 檔案註解都還宣稱「恰好三個」。此問題被 Round 1（Claude spec run）、Round 2（Quality + Spec 兩軸）、Round 3（Quality 軸）分別獨立抓到，`reasoning-chips.ts` 那處在 Round 2 fixer dispatch 中刻意留到 Round 3 才處理。
- **修法：** Round 2 修正 `hooks/README.md`、`ChatPanel.tsx`、`pages/README.md` 為「四個」並明確列出 placeholder grace timer；Round 3 由 orchestrator 直接修正 `reasoning-chips.ts` 的檔案註解，使四處說法一致。機制本身（grace timer 的必要性）已由兩輪獨立 spec review 判斷為合理的必要 plumbing，未變更任何行為邏輯，純文件更正。
- **影響：** 消除同一系統內互相矛盾的文件描述。
- **驗證：** `npx prettier --check` / `npx eslint` 乾淨；後續全套 vitest 196/196 無回歸。

### m-2.1（Minor，Quality）— streaming README 描述已移除的 tool_call_chunk 關閉邊界
- **問題：** README 仍列 `tool_call_chunk` 到達為 reasoning part 關閉邊界之一，與「tool-call-chunk 強制關閉」修正後的實際行為矛盾。
- **修法：** 從關閉邊界清單移除 `tool_call_chunk`，補充說明同輪 tool-call chunk 會讓 reasoning part 保持開啟,實際關閉點為 text block / 下輪 LLM call id 轉換 / 同 chunk 第二個 reasoning block / `finalize()`。
- **影響：** README 與實際 `event_mapper.py` 行為一致。
- **驗證：** 人工比對現行程式碼確認描述準確。

### `backend/tests/scripts/README.md` 未依 envelope §6 刪除（Blocking，Spec）+ validation README segmenter 殘留（Minor，Quality）
- **問題：** 這是 DEV-106 refactor 已刪除的兩份 per-test-folder README（`tests/agents/`、`tests/streaming/`）的同類遺漏——`backend/tests/scripts/` 資料夾也被本次改動觸及（`test_verify_langfuse_trace.py`），且該 README 仍描述已刪除的 `reasoning_tail_aborted` 契約,牴觸 design-envelope §6 named precedent。另外 `backend/scripts/validation/README.md` 仍在 operator 指引裡提到已刪除的 segmenter。
- **修法：** 依前例直接刪除 `backend/tests/scripts/README.md`（確認 repo 內無任何檔案引用其路徑）；從 `validation/README.md` 的部署指引句子移除 "segmenter" 字樣。
- **影響：** 消除文件與 envelope 規則的矛盾，統一三份 test-folder README 皆依規則刪除。
- **驗證：** `uv run pytest backend/tests/scripts/ backend/tests/streaming/` 136 通過（確認只刪 README、測試檔案仍在）;Round 3 spec review 重新 grep 全 repo 確認無殘留引用。

### M-3.1 + m-3.1（Major + Minor，Quality）— Round 2 fixer 刻意留下的最後兩處文件漂移
- **問題：** `reasoning-chips.ts` 檔案註解仍稱「恰好三個 store」（見上方合併說明）；`test_event_mapper.py` 的 `TestReasoningPartBoundaries` class docstring 仍稱「tool 會關閉 reasoning part」，與 SP-1.2 修正後的實際測試內容矛盾（底下的測試名稱/斷言本身已是正確的，只有 class docstring 沒跟上）。
- **修法：** 兩處皆為一行註解/docstring 更正,風險為零、無需完整 fixer+reviewer round,orchestrator 直接動手修正。
- **影響：** Round 3 兩軸 review 收斂為 quality 軸 0 Blocking/0 Major/0 Minor 待辦、spec 軸 0 findings。
- **驗證：** `uv run ruff check` + `ruff format --check`（backend）、`eslint` + `prettier --check`（frontend）皆乾淨;修正後未再開 Round 4，直接進 Final Verification。

## 文件修正

| 目錄 / 檔案 | 修正內容 |
| --- | --- |
| `backend/scripts/validation/verify_langfuse_trace.py` | docstring 改為 per-trace 契約；刪除死碼 `_latest_generation()` |
| `backend/scripts/validation/README.md` | `--expect-aborted` 改為 root-status-only；移除 segmenter 殘留字樣 |
| `backend/agent_engine/agents/README.md` | abort cleanup 描述改為 root Langfuse status stamp only |
| `backend/agent_engine/streaming/README.md` | 移除 tool_call_chunk 關閉邊界，補充正確的 4 個關閉條件 |
| `backend/tests/scripts/README.md` | 依 envelope §6 precedent 刪除 |
| `frontend/src/hooks/README.md` | 非 derived store 數量 3→4，列出 placeholder grace timer |
| `frontend/src/components/pages/README.md` | 同上 + prettier 表格寬度 reflow |
| `frontend/src/lib/reasoning-chips.ts` | 檔案註解非 derived store 數量 3→4 |
| `artifacts/current/bdd-scenarios.md` | window(a) 設計註記更正為現況，標記舊框架 superseded，完整裁決收斂留給 DEV-108 |
| `backend/tests/streaming/test_event_mapper.py` | class docstring 更正 tool-call-chunk 邊界描述 |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| 已知缺口（user 確認接受） | Reload 中的 assistant turn 不會保留 user 自己的 prompt（無 history hydration） | user 明確確認：這是本 slice 尚未實作的功能，非缺陷 | 若未來要做 reload persistence，開新 issue；不影響本 loop 收斂 |
| False positive（已查證推翻） | Codex 聲稱 zero-delta reasoning 違反 S-parts-05「0 parts」要求 | 實際執行 `test_empty_delta_not_emitted` 確認通過，且其 docstring 明確對應 S-chip-08（不同情境：reasoning 開啟但零內容，wire 仍送 start+end，前端才抑制 chip），S-parts-05 講的是 reasoning 整個關閉的不同情境 | 無需動作 |
| False positive（已查證推翻） | Codex 聲稱 `LiveStatusAnnouncer` 留在 production 是 scope creep | 查證 DEV-60 2026-07-23 comment 明文裁決保留（「保留不動，非 F5 專屬，ARIA 公告無 reasoning 專屬邏輯」），早於且優先於後續一則 comment 用詞不精準的「被刪的 LiveStatusAnnouncer」措辭 | 無需動作 |

## Final Verification Results

### Code Level

- [x] Unit Tests: backend `uv run pytest backend/tests/` 910/910 passed（含 restore 手動測試遺留的 `orchestrator_config.yaml` 後重跑,排除該筆非本 diff 的干擾）；frontend `npm run test -- --run` 196/196 passed（24 files）
- [x] Lint: `uv run ruff check backend/` all checks passed；`npx eslint .`（frontend）0 errors（僅 1 個 `public/mockServiceWorker.js` 的既有無關 warning）
- [x] Type Check: `npx tsc -b` clean，無輸出

### Behavior Level

- [x] S-chip-06（tool card 排在還開著的 chip 下方，不強制提前收合）: `test_tool_call_chunk_does_not_close_open_reasoning_part` + `test_tool_call_chunk_then_new_llm_call_closes_part_exactly_once` 通過
- [x] chip 計時在跨 turn 時維持穩定（本輪新增行為驗證）: `useReasoningTimers.test.ts` + `ChatPanel.integration.test.tsx` 通過

### Runtime / Observable Level

- [x] `npm run build`（frontend）: clean build
- [x] Playwright `@smoke` 套組（chromium，5 tests）: 全數通過，含修正後的 `slow-start-stream.spec.ts`（實際安裝瀏覽器並執行，非僅靜態推論）
- [x] `npx prettier --check`（frontend）+ `uv run ruff format --check`（backend）: 皆乾淨

## All Changed Files

> 僅列本次 review-fix loop 自身觸及的 15 個檔案（不含 loop 開始前已完成並經過 two-axis-review 的 DEV-106 原始 diff）。

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/agent_engine/streaming/event_mapper.py` | 移除 tool-call-chunk 強制關閉 reasoning part 的錯誤邏輯 |
| `backend/tests/streaming/test_event_mapper.py` | 對應測試重寫 + docstring 更正 |
| `backend/agent_engine/agents/README.md` | abort cleanup 描述更正 |
| `backend/agent_engine/streaming/README.md` | 關閉邊界清單更正 |
| `backend/scripts/validation/verify_langfuse_trace.py` | docstring 更正 + 刪死碼 |
| `backend/scripts/validation/README.md` | `--expect-aborted` 描述更正 + segmenter 殘留移除 |
| `backend/tests/scripts/README.md` | 刪除（envelope §6 precedent） |
| `frontend/src/components/pages/ChatPanel.tsx` | chip 計時 reset 邏輯修正 |
| `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` | 新增回歸測試 |
| `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` | 斷言精確化 |
| `frontend/tests/e2e/smoke/slow-start-stream.spec.ts` | 斷言更正 |
| `frontend/src/lib/reasoning-chips.ts` | 檔案註解更正 |
| `frontend/src/hooks/README.md` | 非 derived store 數量更正 |
| `frontend/src/components/pages/README.md` | 同上 + prettier reflow |
| `artifacts/current/bdd-scenarios.md` | window(a) 設計註記更正 |

## Learning Notes

### 採用的工程策略

- Cross-model isolation 在這個 loop 中發揮實際作用：Codex 在 Round 1 spec 軸抓到 Claude 那輪完全沒看到的兩個 Blocking 發現（tool-call-chunk 強制關閉、zero-delta 誤判），也各自對同一個 window(a)/reload 問題獨立收斂到一致結論——不同模型的 blind spot 確實不同。
- Round 1 起就堅持「reviewer 說的不直接採信,要親自查證」：對 Codex 的 4 個 spec 發現，2 個透過實際執行既有測試（`test_empty_delta_not_emitted`、`test_tool_call_chunk_closes_open_reasoning_part`）與翻查 Linear 歷史（DEV-60 2026-07-23 comment）確認為 false positive，避免了在不存在的問題上浪費 fixer 資源。
- M-2.1（E2E 斷言）的驗證方式：沒有停在「讀 Playwright 文件、推論應該會 fail」，而是實際 `npx playwright install chromium` 裝瀏覽器跑一次，拿到真實的 failure 訊息再動手修——這個 loop 裡凡是能實際執行驗證的，都優先用執行結果取代推論。

### 權衡取捨

- Round 2 fixer 被要求「window(a) 只修文件、不動 code」——因為該行為已由兩輪獨立 spec review 判斷工程方向正確，真正的問題只在文件/裁決紀錄沒跟上。這個取捨避免了在已經驗證過的正確行為上做不必要的回退,同時誠實記錄了「完整裁決收斂仍留給 DEV-108」，沒有假裝這個 loop 已經把治理流程補完。
- Round 2 fixer dispatch 明確排除了 `reasoning-chips.ts` 的同一處文件漂移（當時判斷風險夠低、可以留到下一輪），Round 3 quality review 準確地把它抓回來——這證明「先窄後寬」的漸進式 fixer 範圍劃分沒有讓問題真的漏掉，只是延後一輪處理。

### 關鍵收穫

- **同一個底層事實會被兩個不同 severity 框架描述**：`backend/tests/scripts/README.md` 這個問題，Quality 軸標成 Minor（「文件過期」）、Spec 軸標成 Blocking（「違反 acceptance criterion」）——兩者都對，只是視角不同。這印證了「兩軸不合併排序」的設計:如果只看其中一軸的嚴重度，會低估或誤判這類「文件同時是品質問題也是規格違反」的項目。
- **`toHaveText` 與 CSS 生成內容的落差是一種容易被忽略的測試脆弱性**：M-2.1 的根因不是邏輯 bug，而是「DOM textContent 不包含 `::after` 的生成內容」這個瀏覽器行為冷知識。任何把「動畫效果」實作成 CSS pseudo-element、卻沒有同步檢查既有 E2E 斷言的改動，都有這個風險——這類跨層（CSS ↔ E2E 斷言）的一致性,不會被 unit test（jsdom 不算 pseudo-element）攔到，只有真的跑瀏覽器才會現形。
- **裁決文件與程式碼的漂移會像滾雪球一樣在多輪 review 中反覆現身**（「非 derived state 恰好三個」這句話，從 Round 1 Claude spec review、到 Round 2 兩軸、到 Round 3 quality 軸,總共被抓到 4 次，分散在 4 個不同檔案）：這代表當一個系統層級的不變量（invariant）描述散落在多份文件/註解裡，任何一次變更都容易漏掉某一處——比起逐一補救，更值得注意的是這類「同一句話出現在 N 個地方」的模式本身，未來若再遇到類似情況，一次搜尋全部出現位置會比等 review 逐輪抓出更有效率。
