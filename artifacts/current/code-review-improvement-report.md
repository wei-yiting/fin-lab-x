# Code Review Improvement Report

> **Task:** DEV-107 — F7: Langfuse trace-level reasoning 寫入（trace-level reasoning transcript on self-owned root span, ADR-0007）
> **Date:** 2026-07-30
> **Rounds:** 3（review 3 輪、fix 2 輪）
> **Reviewer model:** gpt-5.5（Codex CLI，`--read-only --effort high`，Quality 與 Spec 兩軸皆是）
> **Fixer model:** Claude Fable 5（general-purpose subagent）

## 架構影響摘要

- **Trace 樹形狀改變**：每個 streamed request 的 root observation 從 LangChain 自動建立的 chain 變成 Orchestrator 自有的 `chat_turn` span，LangChain 整棵樹降一層掛在底下。reasoning 全文只存在 root span 的 `metadata.reasoning`（單一 key + `=== segment N ===` 值內 marker），generation span 上不再有 per-call reasoning metadata。
- **私有 API 依賴歸零**：`CallbackHandler._runs` 讀取、三層 drift 防禦、283 行 contract test、`langfuse_internal_contract` pytest marker 全數刪除。所有 Langfuse 互動走公開 API（`start_as_current_observation` / 持有 reference 的 `span.update` / `get_client().api.trace.get`）。
- **Transcript 語意收斂**（review 過程中 sharpen）：只渲染有文字的 segment（零文字 provider reasoning block 被過濾、剩餘 segment 重新編號 1..K，與前端 chips 一一對應）；`=== aborted ===` 只在 mid-segment abort 時出現；含截斷後綴與 marker 的最終值嚴格 ≤ 500KB。
- **LangChain root chain 命名改為 `chat_turn`**（原 `chat-turn`），全 observability 命名收斂為 snake_case。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 3 |
| 發現 issues 總數 | 9（Quality 5 + Spec 4；其中 M-1.2 與 SP-1.3 同根因） |
| Blocking | 2/2 fixed（SP-1.1、SP-1.2） |
| Major | 5/5 fixed（M-1.1、M-1.2、M-1.3、M-2.1、SP-1.3、SP-1.4 中的 Major 級）|
| Minor | 1/1 fixed（m-2.2） |
| Suggestion | 0/0 |
| Spec findings (SP-) | 4/4 fixed |
| 文件修正 | 6 處（3 個 README、guardrails 範例、docs/observability.md、value-contract 表） |

## Spec Conformance（Spec 軸）

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented (Blocking) | "observability span 命名遵循 snake_case 慣例"（AC-5） | Fixed — `run_name` `chat-turn` → `chat_turn` 全 repo 7 處 |
| SP-1.2 | Misimplemented (Blocking) | "以 Langfuse SDK 讀回"（AC-1/AC-2） | Fixed — verify script 改用 `get_client().api.trace.get(trace_id)` |
| SP-1.3 | Misimplemented (Major) | "`=== aborted ===` appears only when the conversation aborts mid-segment"（ADR-0007） | Fixed — 與 M-1.2 同根因，finalize 事件先餵 accumulator |
| SP-1.4 | Scope creep (Major) | "verify script 大幅簡化,驗證項只剩「root trace 有全文」" | Fixed — 移除 `--expect-reasoning-off`/`--expect-unsupported`；`--expect-aborted` 依使用者裁決保留（AC-2 明文要求 abort 驗證） |

Round 2 Spec 軸複查：4/4 confirmed fixed、0 新 findings — 需求覆蓋完整、無殘餘 scope creep。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `docs/adr/0007-trace-level-reasoning-transcript-on-self-owned-root-span.md` | 設計決策全景（為何 trace-level、為何自有 root span、兩平台形狀共通性） | |
| 2 | `backend/agent_engine/streaming/reasoning_transcript_accumulator.py` | 新核心：domain events → transcript 值語意（marker、過濾、cap、abort） | |
| 3 | `backend/agent_engine/agents/base.py` | Wiring：自有 root span、finalize→observe→write→yield 順序、三路寫入、abort cleanup 改寫 | ⚠️ |
| 4 | `backend/agent_engine/streaming/reasoning_trace_callback.py`（刪除） | 舊 per-call 路徑退場——確認沒有殘留引用 | |
| 5 | `backend/scripts/validation/verify_langfuse_trace.py` | SDK 讀回 + 收斂後的斷言面 | |
| 6 | `backend/tests/streaming/test_reasoning_transcript_accumulator.py` | 值語意的完整測試面（21 tests） | |
| 7 | `backend/tests/agents/test_orchestrator_langfuse.py` | 寫入時序 / abort / resilience 行為測試 | |
| 8 | `backend/tests/integration/test_langfuse_resilience.py` + `backend/tests/scripts/test_verify_langfuse_trace.py` | Resilience 契約與 verifier 單元測試 | |
| 9 | 三個 README + `docs/observability.md` + `CONTEXT.md` | 文件同步（含 `Reasoning transcript` 新術語） | |

⚠️ 說明：`base.py` 觸及 streaming 取消路徑（`CancelledError` 傳播）與 trace 對外形狀——這是本 diff 唯一有不可逆語意的整合點，建議對照 `TestAstreamAbortCleanup` / `TestFinalizeFeedsAccumulator` 閱讀。

## 所有修正問題詳解

### M-1.1（Major）
- **問題：** 自然結束路徑的 `root_span.update(metadata=...)` 位於大 `try` 內——Langfuse 在此刻拋錯會把已成功的 stream 轉成 `StreamError + Finish(error)` 給使用者，違反 observability 失敗不得影響 user stream 的 resilience 契約。
- **修法：** 該寫入包進獨立 try/except（`logger.exception` 後繼續），與 error/abort 路徑的 guard 對齊。
- **影響：** Langfuse outage 時使用者體驗不受影響，只損失該筆 transcript。
- **驗證：** 新測試 `span.update` side_effect 拋錯 → stream 仍以 `Finish("stop")` 收尾、無 `StreamError`。

### M-1.2 / SP-1.3（Major，同根因）
- **問題：** `mapper.finalize()` 實際上會對 open reasoning part 補發 `ReasoningEnd`（實作時的註解斷言相反，屬誤讀），且 finalize 事件未餵給 accumulator、寫入又發生在 finalize 之前——對話以 reasoning 結尾時 in-flight 狀態殘留，若 client 在 closing events yield 期間斷線，abort cleanup 會錯標 `=== aborted ===`。
- **修法：** 改為 `closing_events = mapper.finalize()` → 逐一 `accumulator.observe()` → `root_span.update()` → yield；錯誤路徑同步套用；錯誤註解改正。
- **影響：** `=== aborted ===` marker 嚴格遵守 D6 語意（只標 mid-segment abort），transcript 完整性訊號可信。
- **驗證：** 新增 `TestFinalizeFeedsAccumulator`（3 tests），含「reasoning 結尾 + closing yield 期間 cancel → 不帶 marker」的 regression case。

### M-1.3（Major）
- **問題：** `_cap()` 先切到 500KB 再附加截斷後綴，最終值超標約 40 bytes；abort marker 在 cap 前附加，超長 aborted transcript 的 marker 會被截尾砍掉，與 verifier 斷言矛盾。
- **修法：** cap 約束最終渲染值——預留截斷後綴與 `\n=== aborted ===` 的空間，超長 aborted transcript 仍以 marker 結尾。
- **影響：** 保險絲路徑（envelope 內實際碰不到）的行為與文件、verifier 完全一致。
- **驗證：** 測試斷言 `len(value.encode()) <= SIZE_CAP_BYTES`（一般與 aborted 兩情境）+ aborted 超長值仍以 marker 結尾。

### M-2.1（Major）
- **問題：** 零文字 reasoning block（mapper 只發 Start/End、無 Delta）會渲染成 `=== segment 1 ===\n` 假非空 transcript，且 verifier 只驗「非空 + 有 marker」會誤判通過——違反「全文」契約與 chips 一一對應的說法。
- **修法：** `value()` 渲染時過濾純空 segment（whitespace-only 保留）、保留者重新編號 1..K；空 open segment 在 abort 時不產生幽靈 header 但 marker 照 D6 出現；verifier 新增 `_has_segment_text()` 拒絕 marker-only transcript。
- **影響：** transcript 與使用者實際看到的 chips 嚴格一致；verifier 不再有 false positive。
- **驗證：** 新增 `TestEmptySegmentFiltering`（5 tests）+ verifier marker-only 失敗測試。

### SP-1.1（Blocking）
- **問題：** LangChain `run_name="chat-turn"`（kebab-case）成為 Langfuse chain span 名稱，違反 AC-5 的 snake_case 慣例（屬既有命名，AC 文字將其拉入本 slice 範圍）。
- **修法：** 全 repo 7 處改為 `chat_turn`（source 1、測試 2、文件 4）；`grep -rn "chat-turn"` 歸零。
- **影響：** observability 命名全面 snake_case。
- **驗證：** 測試 asserts 更新後全綠；grep 驗證無殘留。

### SP-1.2（Blocking）
- **問題：** verify script 用 `urllib` 打 REST endpoint，AC 字面要求「以 Langfuse SDK 讀回」。
- **修法：** 改用 `get_client().api.trace.get(trace_id)`（Context7 查證的 v4 公開讀回路徑，回傳 `TraceWithFullDetails`，`.dict()` camelCase 序列化使 `verify()` 零改動）；保留 5 次線性退避輪詢；改捕 `ApiError`/`httpx.HTTPError`；棄用手工 Basic auth。
- **影響：** 驗收與 AC 字面一致；認證/端點組態統一交給 SDK。
- **驗證：** 單元測試改配新簽名（10 passed）；對兩條真實 trace live 重跑 `ok:true`。

### SP-1.4（Major, scope creep）
- **問題：** 簡化後的 verifier 仍保留 off/unsupported capability matrix，超出「驗證項只剩 root trace 有全文」的達標即止範圍。
- **修法：** 移除 `--expect-reasoning-off` / `--expect-unsupported` 與其分支、測試；`--expect-aborted` 依使用者裁決保留（AC-2 明文要求）；accumulator 的 `"<unsupported>"`/`""` 值語意不動（D4 契約）。
- **影響：** verifier 表面積與 spec 一致；短命 Langfuse 腳手架最小化。
- **驗證：** verifier 測試重寫後全綠。

### m-2.2（Minor）+ 文件 gap
- **問題：** `agents/README.md` 記載修正前的寫入順序；`streaming/README.md` 的 oversize 行與 cap 新語意不符；round 3 再指出兩處 README 未提及空 segment 過濾與 verifier 新斷言。
- **修法：** 四處 README 描述全部對齊現行為（最後兩處由 orchestrator 直接補上）。
- **影響：** 文件與 code 零漂移。
- **驗證：** round 3 Codex 確認前兩處；後兩處為本 report 前的最終編修。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `backend/agent_engine/agents/README.md` | 自然結束順序改為 finalize → observe → write → yield；`chat_turn` 命名 |
| `backend/agent_engine/streaming/README.md` | oversize cap 語意（最終值含後綴 ≤ 500KB）；只渲染有文字 segment 的過濾規則 |
| `backend/scripts/validation/README.md` | SDK 讀回與 env vars；收斂後的 flag 表；`--expect-reasoning-on` 的非空白文字要求 |
| `backend/agent_engine/docs/streaming_observability_guardrails.md` | config 範例 `run_name` 改 `chat_turn` |
| `docs/observability.md` | `run_name` 行改 `chat_turn` |
| `backend/agent_engine/README.md` | `run_name` 行改 `chat_turn` |

## 未處理項目

無。

## Final Verification Results

### Code Level

- [x] Unit Tests: `.venv/bin/python -m pytest backend/tests/ -q` → **888 passed, 48 deselected**
- [x] Lint: `ruff check backend/` → All checks passed
- [x] Format: `ruff format --check backend/` → 165 files already formatted

### Behavior Level

- [x] 真實對話（gpt-5-mini, reasoning on）SDK 讀回：trace `bc372f8400b12e08f245ace2d6431420` → `verify --expect-reasoning-on` `ok:true`（round 2 verifier 收緊後重跑）
- [x] Abort case（SSE 讀 5 個 reasoning-delta 後斷線）：trace `01bb929d1bd4115ad6beb58b9d0e3e45` → `verify --expect-reasoning-on --expect-aborted` `ok:true`，tail 以 `=== aborted ===` 結尾 + `status: aborted`

### Runtime / Observable Level

- [x] Langfuse UI 可讀性：root `chat_turn` span 的 `metadata.reasoning` 人眼可讀（`=== segment 1 ===` 開頭全文，實測目視確認）
- [x] BDD 全量 loop（Step 5.5）**跳過**：`bdd-scenarios.md`/`verification-plan.md` 屬 DEV-106（F5/F6）scope 且已在該 issue 驗畢；本 slice 的行為驗證即上方兩條真實 trace 讀回，已執行

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/agent_engine/streaming/reasoning_transcript_accumulator.py` | M-1.3 cap 邊界、M-2.1 空 segment 過濾 |
| `backend/agent_engine/agents/base.py` | M-1.1 best-effort 寫入、M-1.2/SP-1.3 finalize 順序、SP-1.1 `chat_turn` |
| `backend/scripts/validation/verify_langfuse_trace.py` | SP-1.2 SDK 讀回、SP-1.4 flag 收斂、M-2.1 `_has_segment_text` |
| `backend/tests/streaming/test_reasoning_transcript_accumulator.py` | cap/過濾測試（+7 tests） |
| `backend/tests/agents/test_orchestrator_langfuse.py` | `TestFinalizeFeedsAccumulator`（+3 tests）、命名 asserts |
| `backend/tests/scripts/test_verify_langfuse_trace.py` | SDK 簽名、marker-only 失敗、sentinel 拒絕 |
| 6 個文件檔 | 見「文件修正」表 |

（實作本體的 changed files manifest 見 DEV-107 sync comment @ `e52bc08`；本表只列 review loop 修正觸及的檔案。）

## Learning Notes

### 採用的工程策略

- **Stream 側收集 + 自有 root span 的形狀在三輪 review 中原樣存活**——兩軸 reviewer 都未挑戰 ADR-0007 的核心結構，challenge 全部落在邊界條件（finalize 時序、cap 邊界、空 segment）。設計期用 POC 證據（Braintrust Finding 1）鎖定的形狀，實作期就不再被翻案。
- **Cross-model review 的價值實證**：M-1.2 的根因是作者對自己寫的註解過度自信（「finalize 不發 reasoning events」）——同 session 的自查不可能抓到，因為作者「知道自己的意思」；Codex 以零上下文讀 code 直接對照 `event_mapper.finalize()` 戳破。

### 權衡取捨

- **達標即止 vs 字面達標**（SP-1.2、SP-1.4）：預期中「繼承舊 script 的 fetch plumbing」是最小改動，實際上 AC 字面（"SDK 讀回"）與繼承實作（urllib）衝突——短命腳手架也要對齊 AC 字面，因為 AC 是驗收契約不是意向描述。反向地，SP-1.4 證明 reviewer 的嚴格解讀也可能與另一條 AC 自相矛盾（`--expect-aborted` 不可刪），仲裁權在人。
- **保險絲路徑的修 vs defer**（M-1.3）：envelope 內碰不到的路徑，修的理由不是「會發生」而是「行為與文件/verifier 斷言矛盾」——一致性成本低於解釋成本時就修。

### 關鍵收穫

- **「寫入時序」是 streaming observability 的第一風險點**（M-1.1、M-1.2）：在 async generator 裡，「什麼時候寫」比「寫什麼」更容易錯——寫入必須在 yield 之前（yield 後生成器可能永不恢復）、在 finalize 之後（狀態才完整）、且自帶 best-effort 保護（不能污染 user stream）。三個約束缺一即是 bug。
- **Verifier 的斷言強度要跟著資料語意走**（M-2.1）：「非空 + 有 marker」驗的是格式不是內容；當上游可能產生格式正確但語意為空的值（marker-only transcript），verifier 就有 false positive。斷言應對準契約的語意底線（「有 reasoning 文字」），不是表面形狀。
- **註解裡的事實主張需要和被引用的 code 同步驗證**（M-1.2）：引用其他模組行為的註解（"finalize() never emits X"）是最容易腐爛的一類——它斷言的事實住在別的檔案。寫這種註解時應當場重讀被引用處，或乾脆引用測試名而非重述行為。
