# BDD Scenarios

## Meta

- Design Reference: `artifacts/current/design.md`
- Generated: 2026-05-01
- Discovery Method: Three Amigos (Agent Teams) → 27 user-input topics → D1–D39 decisions
- Scope: Multi-Provider Streaming with Reasoning Status (frontend reasoning UX + backend per-call Langfuse trace + provider matrix)

---

## Feature: Provider Streaming Pipeline

### Context

v1–v5 五個 agent version 統一綁到 Gemini 2.5 Flash（admin-configured per D24，user 無法 runtime 切換）；streaming pipeline 對 LangChain v1 chat model provider 跑通；驗收矩陣為 3 providers × 2 modes = 6 cases；non-streaming `Orchestrator.invoke` 路徑也支援多 provider。

---

### Rule: Default agent provider binding 為 Gemini 2.5 Flash

#### S-stream-01: Default agent 跑 canonical SEC query 完成 streaming
> 驗證 v1–v5 agents 預設使用 `google_genai:gemini-2.5-flash` end-to-end streaming 跑通

- **Given** Alice 開啟 chat 介面，預設 agent version 為 v3
- **When** 她送出 D25 canonical prompt：「Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)」
- **Then** Streaming 完成、final answer 渲染、無 console / network error
- **And** Backend 的 Langfuse trace 記錄該次 agent run 走 `google_genai:gemini-2.5-flash`

Category: Illustrative
Origin: PO

#### S-stream-02: 切換 agent version 在同一 session 內，新 turn 仍走 Gemini
> 驗證 agent version 切換對 streaming pipeline 不造成 regression

- **Given** Bob 在 session abc-123 用 v3 完成 3 個 turns
- **When** 他切換 active agent 到 v5 並送出新 query
- **Then** 新 turn streaming 完成走 Gemini 2.5 Flash；之前 turns 的 persisted `message.parts` 保持完整

Category: Illustrative
Origin: PO

---

### Rule: 6-case acceptance matrix（3 providers × 2 modes）跑通

#### S-stream-03: Multi-provider × multi-mode 矩陣 streaming 行為
> 驗證 streaming pipeline 對所有 LangChain v1 chat model provider × reasoning mode 都跑通

- **Given** 設定 agent version 綁到 `<provider>` 並設 reasoning mode 為 `<mode>`
- **When** 送出 D25 canonical prompt
- **Then** Streaming 完成、final answer 渲染、`data-reasoning-status` event count `<event_expectation>`、Langfuse 各 chat_model span `metadata.reasoning` key 存在

| provider                          | mode           | event_expectation | notes                                    |
|-----------------------------------|----------------|-------------------|------------------------------------------|
| google_genai:gemini-2.5-flash     | reasoning-on   | ≥ 1               | default agent baseline                   |
| google_genai:gemini-2.5-flash     | reasoning-off  | = 0               | reasoning mode disabled                  |
| openai:gpt-5-mini-responses       | reasoning-on   | ≥ 1               | OpenAI Responses summary blocks（含 D12 multi-summary `\n` join）|
| openai:gpt-5-mini-responses       | reasoning-off  | = 0               | OpenAI Responses summary disabled        |
| anthropic:claude-4.x-sonnet       | reasoning-on   | ≥ 1               | extended thinking enabled (含 D13 interleave) |
| anthropic:claude-4.x-sonnet       | reasoning-off  | = 0               | extended thinking disabled               |

Category: Illustrative (table-driven)
Origin: PO (D6 / D12 / D25)

---

### Rule: Provider boot 失敗的 user-facing surface 三路分流

#### S-stream-04: Provider boot 失敗於不同階段對應不同 surface
> 驗證 D23 簡化版兩路分流 protocol：pre-SSE / mid-stream 各自有對應 UX。Hung sub-case 隨 Task 13（backend keepalive + first-chunk timeout）一起移出本期 scope。

- **Given** Backend 對應某 provider 處於 `<failure_state>`
- **When** Carol 送出一個 query
- **Then** Frontend 看到的 surface 是 `<expected_surface>`

| failure_state                           | expected_surface                              | notes                        |
|-----------------------------------------|-----------------------------------------------|------------------------------|
| Provider 套件缺失 / API key 無效         | HTTP 5xx via fetch error；useChat onError 觸發 | pre-SSE-open                 |
| 第一個 LLM call 立即報錯                 | SSE error event → State 10 ErrorBlock         | mid-stream                   |
| ~~Provider 30s 內無回應~~                | **移出本期 scope**（hung 行為等同 main：無自動偵測，user 必須手動 Stop） | hung 留待 backend keepalive 另立 PR  |

Category: Illustrative (table-driven)
Origin: Multiple (Dev R2 / QA R1 / D23)

---

### Rule: Non-streaming `Orchestrator.invoke` 路徑也跑通且寫 reasoning 到 Langfuse

#### S-stream-05: Batch eval `.invoke` 也產出 Langfuse reasoning trace
> 驗證 F8 + D30 contract — 非 streaming path 必須跟 streaming path 同樣產生 `metadata.reasoning`

- **Given** Internal caller 建立 `Orchestrator.invoke(query, agent_version="v3")` 跑 D25 canonical prompt
- **When** invoke 完成
- **Then** Langfuse trace 內每個 chat_model span 都有 `metadata.reasoning` key
- **And** Reasoning content 跟相同 prompt 走 streaming path 的對應 span 內容語義等價（substring match 或 high text similarity，allow per-call invocation 自然差異）

Category: Illustrative
Origin: QA R1 (C1.5) + Dev R2 contest (D30)

---

### ~~Rule: SSE keepalive 防止 idle proxy 砍連線~~ — 移出本期 scope

#### ~~S-stream-06: 90 秒 reasoning silence 不被 proxy 中斷~~ — 移出本期 scope

> Backend SSE keepalive (原 Task 13) 整體挪到後續 PR。本期不驗 keepalive 行為，因為實作不存在。等 backend keepalive 另立 PR 完成後再恢復此 scenario。

Category: Illustrative (deferred to follow-up PR)
Origin: QA R1 (C4.5) → Include scenario

---

### Rule: Multi-tab 並發 streaming 互相 isolated

#### S-stream-07: 同 session 兩 tab 並發 streaming 不互相污染
> 驗證 D33 per-request mapper scope

- **Given** Eve 在 Tab A 跟 Tab B 都開啟同一 session 的 chat
- **When** 兩 tab 同時送出不同 query 並進入 streaming
- **Then** 各 tab 的 reasoning indicator 只顯示自己 turn 的 reasoning 內容（無 cross-tab text 洩漏）
- **And** Langfuse 上對應兩個獨立 traces，各自的 chat_model span `metadata.reasoning` 只含自己 tab 的 reasoning（無 contextvars cross-coroutine 污染）

Category: Illustrative
Origin: QA R1 (CR.4 + CR.6) → Include scenario

---

### Rule: Provider 在 abort 後 next turn 不被 contaminated state 影響

#### S-stream-08: Abort 後立即 resend 同 session 仍可運作
> 驗證 backend cancellation cleanup 不留下 stale state（D35）

- **Given** Frank 送出 query 進入 reasoning streaming
- **When** 他在第 5 秒 click Stop，然後立即送出新 query
- **Then** 新 query 完整 streaming 完成；session checkpointer 不被 abort 半成品污染；Langfuse 紀錄前一個 trace `metadata.status = "aborted"`，新 trace 為正常 completed

Category: Illustrative
Origin: Dev R2 (C3.6) + D35

---

### Rule: CJK reasoning 無終止符時 segmenter 仍在 streaming 期間 emit

#### S-stream-09: 80 字 char-count fallback 在 CJK 無終止符 case 觸發 soft-emit
> 驗證 D26 backend segmenter fallback —— Gemini 繁中常無 `。`，user streaming 期間仍能看到 reasoning text 更新

- **Given** Provider 對某 reasoning chunk 累積 emit 110 個 CJK 字元，期間完全沒 `。！？\n` 終止符
- **When** Backend `ReasoningSegmenter.feed()` 處理該 chunk
- **Then** 在累積到 80 字元時觸發 char-count fallback：soft-emit 整段為一個 `ReasoningStatus` event + reset 該段 buffer；後續 30 字元繼續累積至下一個觸發點
- **And** Frontend 在該 LLM call 進行中至少看到 1 個 `data-reasoning-status` event（不需等 LLM-call boundary flush 才出現）

Category: Illustrative
Origin: QA R1 (C3.3) + Dev R2 (C3.4) + D26

---

### Journey Scenarios

#### J-stream-01: 完整 6-case matrix E2E lifecycle
> 驗證 streaming pipeline 對 3 provider × 2 mode 的 6 cases 都從 query 送出到 final answer 顯示完整跑通

- **Given** 一個新 session
- **When** 對 6 cases 各跑一次 D25 canonical prompt（含 multi-tool synthesis 流程）
- **Then** 每個 case streaming 完成；reasoning-on cases 至少 1 個 `data-reasoning-status` event；reasoning-off cases 0 events；無 console / network error；6 個 Playwright video 錄影可供 reviewer 親眼看每家 streaming 行為

Category: Journey
Origin: Multiple (PO + Dev + QA via 6-case matrix Rule 3)

---

## Feature: Reasoning Channel Isolation

### Context

Reasoning content 透過獨立的 transient SSE event `data-reasoning-status` 暴露給前端，**不**進入 `message.parts` 持久化狀態。Reasoning 為 ephemeral 一瞥 UX；reload / 不同階段都不可見於 persisted transcript。Defense in depth：backend SSE serializer + frontend parts.map filter（D39）。

---

### Rule: Reasoning 永遠不進 `message.parts`

#### S-chan-01: Streaming 期間 reasoning 不在 persisted message body
> 驗證 F5 + D2 contract — reasoning text 永遠 ephemeral

- **Given** Grace 送出 reasoning-rich D25 canonical prompt
- **When** Reasoning 期間，`data-reasoning-status` events 抵達 frontend，Reasoning text e.g.「理解 user 在問 risk factors 的變化」顯示於 ReasoningIndicator
- **Then** 同一時刻檢查 `message.parts`：找不到任何 part 內容包含該 reasoning sentence
- **And** Stream 完成後 `message.parts` 僅含 text + tool parts，reasoning 完全不存在

Category: Illustrative
Origin: Dev R1 + Dev R2 (C2.1 + C2.2 mid-stream DOM polling)

#### S-chan-02: Page reload 後 transcript 不顯示 reasoning
> 驗證 rehydration 路徑也保證 reasoning 不洩漏（D2 + D32 + D36）

- **Given** Hank 完成一個 reasoning-on multi-call turn
- **When** 他 reload 頁面，frontend 從 backend 重新 hydrate session messages
- **Then** Rehydrated transcript 僅顯示 text + tool cards；歷史 reasoning text 不出現任何位置
- **And** 在 resumed session 中送下一個 turn，LangGraph state-replay 階段不發出 `data-reasoning-status` events

Category: Illustrative
Origin: Dev R2 (C2.3) + QA R3 contest (resume-turn assertion)

---

### Rule: Defense in depth 防 transient flag 失效（D39 belt-and-suspenders）

#### S-chan-03: Frontend filter 阻擋意外進入 parts 的 reasoning event
> 驗證 D39.b — `parts.map` dispatcher 顯式 filter `data-reasoning-*` 即使該 part 因 bug 進入 parts 仍不 render

- **Given** 假設 SSE 路徑因 bug 缺漏 `transient: true` flag，導致 `data-reasoning-status` event 被 AI SDK 寫進 `message.parts`
- **When** Frontend 渲染 assistant message
- **Then** `AssistantMessage` 的 `parts.map` 顯式 filter 掉 `type.startsWith('data-reasoning-')` 的 part；Reasoning text 不在 transcript 出現

Category: Illustrative (regression-guard)
Origin: Dev R2 (C2.5) + D39

#### S-chan-04: Backend SSE serializer assert + warn missing flag
> 驗證 D39.c — server-side guard 在 dev/CI 直接 raise，prod 改 warn log

- **Given** Backend SSE serializer 嘗試輸出一個 `data-reasoning-status` payload
- **When** Payload 缺 `transient: true`（regression bug 場景）
- **Then** 在 dev / CI 環境 `assert` raise；prod 環境改 log warning（不 raise，避免 abort 整個 stream）；Operator 透過 log 監控可發現 regression

Category: Illustrative (regression-guard)
Origin: D39

---

### Journey Scenarios

#### J-chan-01: 完整 reasoning channel isolation lifecycle
> 驗證從 streaming 到 reload 的完整 lifecycle，reasoning 永不洩漏

- **Given** Ivan 開啟 chat 並送出 reasoning-rich D25 canonical prompt
- **When** 他完整看完 streaming 過程（reasoning indicator 多次出現/消失），等 finish event 後 reload page，再開新 turn
- **Then** Streaming 期間 reasoning 不在 `message.parts`；finish 後 transcript 僅含 text + tool；reload 後 transcript 仍僅含 text + tool；新 turn 不被前一 turn 的 reasoning state 污染

Category: Journey
Origin: Multiple (PO Rule 2 + Dev R1/R2 + QA R3)

---

## Feature: Reasoning Indicator Lifecycle

### Context

Reasoning UI 採 Variant A 視覺（static muted text 0.72rem + trailing dots cycler）；`ReasoningIndicator` component 同時 host pre-response 3-dot bouncing animation。涵蓋 standard 10-state lifecycle + Anthropic Option B re-entry + long-silence stalled modifier + post-tool idle text + abort sub-states + mid-text-start interruption + long-sentence overflow。Plain text 渲染（不 markdown）；ARIA hybrid（aria-hidden + LiveStatusAnnouncer）。

---

### Rule: Standard 10-state lifecycle 對應 user-visible state

#### S-rsn-01: Multi-call turn 走過 10-state 標準 lifecycle
> 驗證 §7.1 state machine：State 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 在 multi-call turn 內 visible

- **Given** Julia 送出 D25 canonical prompt（multi-tool synthesis flow）
- **When** Reasoning-on Gemini 完成完整 turn（3 LLM calls + 多個 tools + final synthesis）
- **Then** UX 依序經歷：State 1 (3-dot idle) → State 2 (reasoning #1) → State 3 (tool running) → State 4 (reasoning #2) → State 5 (parallel tools) → State 6 (synthesizing) → State 7 (text streaming with cursor) → State 8 (done)
- **And** 每個 reasoning state 顯示對應 reasoning sentence 配 trailing dots cycler

Category: Illustrative (sequence)
Origin: PO Rule 4 + Rule 6

#### S-rsn-02: Pre-response idle 顯示 3-dot 直到第一個 SSE event
> 驗證 State 1 視覺：parts.length == 0 且 reasoningStatusText null 時 3-dot bouncing

- **Given** Kevin 送出 query
- **When** 在 backend 第一個 SSE event 抵達之前
- **Then** ReasoningIndicator 渲染 3-dot bouncing animation（點直徑 0.4rem、高度 = `calc(0.72rem * 1.5)`、align-items flex-end），點底部與 reasoning text 底部對齊
- **And** 第一個 `data-reasoning-status` 抵達時切換到 State 2，無垂直跳動感

Category: Illustrative
Origin: PO Rule 6 + D17

---

### Rule: Variant A 視覺規格與渲染契約

#### S-rsn-03: Reasoning text 以 plain text 渲染不解析 markdown
> 驗證 D20 — reasoning content 含 backticks / asterisks 也字面顯示

- **Given** Reasoning content 包含 markdown 字元（如 `` `list_sec_sections` `` / `**重要**`）
- **When** ReasoningIndicator 渲染該 sentence
- **Then** Backticks 跟 asterisks 字面顯示；不被 render 成 inline-code 或 bold；HTML special chars 自動 escape 防 XSS

Category: Illustrative
Origin: QA R1 (C6.7) + D20

#### S-rsn-04: 600+ 字 CJK reasoning sentence 不破壞 layout
> 驗證 D21 hard-clip without ellipsis

- **Given** Provider emit 600+ 字的 CJK reasoning sentence 不含 `。`
- **When** Frontend 渲染該 sentence 至 ReasoningIndicator
- **Then** Container 維持單行高度（line-height = `0.72rem * 1.5`）；超出邊緣的內容 hard-clip（無 `…` ellipsis）；trailing dots cycler 在 clip 邊界右側保持完整 visible

Category: Illustrative
Origin: QA R1 (C6.8) + Dev R2 + D21

---

### Rule: Anthropic interleaved reasoning ↔ text 採 Option B re-entry

#### S-rsn-05: 同一 LLM call 內 reasoning → text → reasoning 切換
> 驗證 D13 / §7.2 — Anthropic extended thinking 中段重回 reasoning state

- **Given** Larry 用 Anthropic Claude 4.x reasoning-on 送出觸發 interleaved 行為的 prompt
- **When** 同一 chat_model call 內 backend 依序 emit `reasoning_block_A` → `text_delta_1` → `reasoning_block_B` → `text_delta_2`
- **Then** UX 依序：State 2 (reasoning A 顯示) → State 7 (text streaming 開始、indicator 隱藏) → State 7a (reasoning indicator 在已 streamed text **下方**重新顯示) → State 7b (text 繼續、indicator 再次隱藏)
- **And** 多次 re-entry 不限次數

Category: Illustrative
Origin: PO Rule 3 + Dev R1/R2 + D13

---

### Rule: Long-silence stalled modifier (10s 無新 chunk 變慢變淡)

#### S-rsn-06: Reasoning 靜默 10s+ 觸發 stalled 視覺
> 驗證 D14 — dots cycle 1.4s → 2.5s + opacity 1.0 → 0.55；text 不變

- **Given** Mary 進入 State 2 reasoning streaming，最後一個 reasoning sentence 顯示「整理 risk factors 的層次」
- **When** Backend 連續 10 秒沒送新 `data-reasoning-status` chunk（SSE keepalive ping 仍正常）
- **Then** Frontend 自動套 `.stalled` modifier：dots cycle 速度減半、dots opacity 降至 0.55、reasoning text **不變動**保留閱讀脈絡（800ms ease transition）
- **And** 下一個 reasoning chunk 抵達自動移除 modifier 恢復 normal cycle

Category: Illustrative
Origin: QA R1 (C4.3) + Dev R2 (C4.4) + D14

---

### Rule: Post-tool idle indicator 補 F6 reasoning-off 空窗洞

#### S-rsn-07: Reasoning-off model post-tool gap 顯示 idle text
> 驗證 D15 — State 11 / 12 idle text 沿用 Variant A 視覺顯示「Synthesizing」/「Thinking」

- **Given** Nora 送出 query 在 reasoning-off agent，agent 走 multi-tool flow
- **When** 處於 `<gap_type>` 階段
- **Then** ReasoningIndicator 顯示 idle text `<idle_text>` + dots cycler，視覺與 reasoning streaming 一致

| gap_type                                        | idle_text     | notes                                      |
|-------------------------------------------------|---------------|--------------------------------------------|
| Tool 結束後到 final-call text-start 之間        | "Synthesizing"| State 11 post-tool synthesis              |
| Multi-call mid-gap (tool 之間)                  | "Thinking"    | State 12 multi-call mid                    |

Category: Illustrative (table-driven)
Origin: Dev R1 (C4.6) + QA R1 + D15

---

### Rule: Stream interruption sub-states (abort + error)

#### S-rsn-08: Abort sub-state 對應 visible content 各自處理
> 驗證 D17 / D19 / §7.5 / §7.6 — 5 種 abort 階段對應 5 種視覺結果

- **Given** Olivia 在 `<abort_phase>` 期間 click Stop
- **When** Frontend useChat.stop() 觸發
- **Then** UX 結果為 `<expected_visual>`

| abort_phase                                  | expected_visual                                                                |
|----------------------------------------------|--------------------------------------------------------------------------------|
| State 1 pre-response idle (no SSE 事件)      | 9a: 3-dot 移除；只顯示 STOPPED label                                           |
| State 2/4/6 reasoning streaming              | 9: reasoning text 凍結 (opacity 0.65) + STOPPED label inline                   |
| State 3/5 pure tool running (無 reasoning)   | 9b: 該 ToolCard 變 aborted state；無額外 STOPPED label                         |
| State 7 text streaming (partial answer text) | 9c: partial text 保留可讀 + STOPPED label inline 接末尾                        |
| State 11/12 post-tool idle text              | 同 9: idle text 凍結 + STOPPED label inline                                    |

Category: Illustrative (table-driven)
Origin: Multiple (PO Rule 7 + Dev R2 missing-cases + QA R2 + D10 + D17 + D19)

#### S-rsn-09: Stream error 維持 D11 asymmetry — 隱藏 ephemeral content + ErrorBlock
> 驗證 D18 — error 處理跟 abort 不對稱，ephemeral content 一律隱藏

- **Given** Peter 處於 `<error_phase>` 階段
- **When** Backend 送 SSE `error` event 或 socket drop
- **Then** Frontend 結果：

| error_phase                                  | expected_visual                                                                |
|----------------------------------------------|--------------------------------------------------------------------------------|
| Pre-response idle / reasoning / idle text    | 10: ephemeral content 隱藏；ErrorBlock 在下方顯示                              |
| Tool running                                 | ToolCard 變 errored state（既有 tool error UI）；ErrorBlock 顯示                |
| Mid-text-start streaming                     | 10b: partial text **保留**可讀；ErrorBlock 在下方；不加 inline ERROR marker      |

Category: Illustrative (table-driven)
Origin: PO Rule 7 + Dev R2 + QA R2 + D18 + D19

---

### Rule: Final synthesizing reasoning 永遠 visible (Hold-and-flush)

#### S-rsn-10: 最後一句 synthesizing reasoning 在 text-start 之前送達 frontend
> 驗證 D28 + D34 — backend hold-and-flush ordering 保證 final reasoning 永不 lost

- **Given** Quinn 跑 D25 canonical prompt 至最後一個 chat_model invoke (synthesizing call)
- **When** Synthesizing 階段 reasoning 結束、text 開始 streaming（block.type 從 reasoning 切到 text）
- **Then** Backend 在 emit `text-start` event 之前先 emit `segmenter.flush()` 出來的最後 `ReasoningStatus` event
- **And** Frontend 看到 reasoning text「整理新增/加強/刪去 三類」visible 至少一次（slow-motion video review at 120Hz 可確認），然後才被 text-start 清除

Category: Illustrative (regression-guard)
Origin: Dev R3 contest (Contest B) + D28

---

### Rule: Frontend useReasoningStatus guards 防 race conditions

#### S-rsn-11: Clear 後 in-flight buffered SSE 不重新填上 reasoning
> 驗證 D31 / T13.A — `clearedRef` guard 防 200ms drain race

- **Given** Rachel 在 streaming 中 click Clear conversation
- **When** Frontend 呼叫 `clearReasoningStatus()`，但 backend SSE buffer 還有 in-flight events 抵達
- **Then** 200ms in-flight events 期間 reasoning indicator 保持隱藏；不會閃爍重新顯示
- **And** 下次 user 送新 message 時 `resetForNewTurn()` 重置 guards 恢復正常

Category: Illustrative
Origin: Dev R1 (C6.5) + D31

#### S-rsn-12: Finish 後 late-arriving data-* events 不出現 ghost indicator
> 驗證 D31 / T19 — `finishedRef` guard 防 ghost re-appear

- **Given** Sam 完成一個 turn，State 8 done
- **When** 因 backend bug 或 race，late `data-reasoning-status` event 在 finish 之後抵達 frontend
- **Then** Frontend `handleData` ignore 該 event；ReasoningIndicator 不重新出現（無 ghost）

Category: Illustrative (regression-guard)
Origin: QA R2 (CR.5) + D31

---

### Rule: Abort-then-resend 兩 turn 共存於 message history

#### S-rsn-13: Abort 後立即送新 message 兩個 assistant bubbles 並存
> 驗證 D32 — message-list 天然處理 multi-turn 並存，prior STOPPED 自然 persist

- **Given** Tina 送出 query 進入 reasoning streaming
- **When** 她 click Stop（看到 prior turn 進入 9c 或 9 抓住 STOPPED label），然後立即送出新 message
- **Then** Prior assistant bubble 保留顯示 9c/9 frozen 狀態 + STOPPED label；新 turn 在下方新增 assistant bubble 開始 streaming
- **And** 兩個 bubbles 同時並存於 chat list；新 turn 的 reasoning 不影響 prior bubble

Category: Illustrative
Origin: Dev R1 (C6.10/C6.11) + QA R2 + D32

---

### Rule: ARIA Hybrid — LiveStatusAnnouncer 高層級狀態 + 視覺元件 aria-hidden

#### S-rsn-14: Screen reader 收到 transition-level status 而非逐句 reasoning
> 驗證 D22 — high-level status announcement，不污染 polite queue

- **Given** Ursula 用 screen reader 操作 chat
- **When** 她跑一個 multi-call turn（含 reasoning + tool calls + final answer）
- **Then** Screen reader 依 transition 接收 announce：「Generating response」→「Calling list_sec_sections」→「Tool list_sec_sections completed」→（final answer text 自然讀出）→「Response complete」
- **And** Reasoning text（每 turn 8-12 句）跟 idle text **不**逐句 announce
- **And** ReasoningIndicator / ToolCard 的 DOM 含 `aria-hidden="true"`

Category: Illustrative
Origin: QA R1 (C6.6) + D22

---

### Journey Scenarios

#### J-rsn-01: 完整 reasoning indicator 10-state 走過一輪
> 驗證 indicator lifecycle 從 query 送出到 done 的完整視覺序列

- **Given** Victor 開啟新 chat 介面
- **When** 他送 D25 canonical prompt 並完整觀察 streaming（不 abort 不 error）
- **Then** UX 依序顯示 State 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8；每階段視覺對應 design.md §7.1 規格；最終 final answer 完成、indicator 完全消失

Category: Journey
Origin: Multiple (PO Rule 6 + Dev + QA)

#### J-rsn-02: Abort 中段然後 resend，前後 turn 都正確顯示
> 驗證 abort sub-state visualization + abort-then-resend 流程

- **Given** Wendy 在 chat 介面開啟新 turn
- **When** 她送 query → 等到 State 6 synthesizing → click Stop（看到 9 frozen + STOPPED）→ 立即送新 message → 新 turn 完整跑完
- **Then** Prior bubble 顯示 frozen reasoning + STOPPED；新 bubble 完整跑完 lifecycle 到 State 8；兩 bubbles 並存

Category: Journey
Origin: Multiple (D17 + D32 + Topic 14)

---

## Feature: Langfuse Reasoning Persistence

### Context

每個 chat_model LLM call 的 reasoning content 寫到 Langfuse `metadata.reasoning`（per LLM call 一塊）；schema 統一（empty `""` / sentinel `<unsupported>` / 500KB truncate marker）；judge model `gpt-5-mini` 不掛 `ReasoningTraceCallback`（避免 rubric 洩漏）；live UX 跟 trace 內容可接受 divergence。

---

### Rule: 每個 chat_model span 都有 `metadata.reasoning` key

#### S-trace-01: Reasoning-on multi-call turn 對應 N 個獨立 chat_model spans
> 驗證 F7 — per-LLM-call reasoning 不 cumulative

- **Given** Xiang 跑 D25 canonical prompt 走 reasoning-on Gemini，產出 3 個 LLM calls
- **When** Turn 完成、Langfuse SDK flush 後（驗證時 polling with retry+backoff 5 秒）
- **Then** Trace tree 含 1 個 `agent.run` parent span + 3 個 `chat_model.invoke` child spans
- **And** 每個 chat_model span 有自己的 `metadata.reasoning`，內容只含該 call 的 reasoning（不 cumulative）
- **And** Parent `agent.run` span 自己**不**含 `metadata.reasoning`（避免 D29 / D37 callback ordering 失效時 fallback 到 parent）

Category: Illustrative
Origin: PO Rule 5 + Dev R1 (C5.1) + D29 + D37

---

### Rule: `metadata.reasoning` schema (empty + size cap + sentinel)

#### S-trace-02: 各種 reasoning content 狀態的 schema 一致性
> 驗證 D29 / §6.2 — completed path 5 種狀態對應 5 種 value 形式。Abort path 由 S-trace-06 涵蓋，寫的是 `metadata.reasoning_tail_aborted` + `metadata.status="aborted"`，與 `metadata.reasoning` 同屬 D29 mode-aware contract（completed / aborted 兩 path 各自必填對應 key）。

- **Given** Yara 跑 turn 對應 `<scenario>`（completed path — 自然 finish，非 abort）
- **When** Turn 完成、Langfuse trace 檢查
- **Then** chat_model span `metadata.reasoning` value 為 `<expected_value>`（abort path 此 key 可缺，由 reasoning_tail_aborted 接手）

| scenario                                                        | expected_value                                              |
|-----------------------------------------------------------------|-------------------------------------------------------------|
| reasoning-on，model emit reasoning content                       | 實際 reasoning 文字（多 reasoning blocks join）             |
| reasoning-on，但 short prompt model 沒 emit reasoning             | `""` empty string                                           |
| reasoning-off mode（reasoning-capable provider）                 | `""` empty string                                           |
| Non-reasoning-capable provider（agent config 標記）              | `"<unsupported>"` sentinel                                  |
| Reasoning content > 500KB                                       | 前 500KB + `... [truncated, original {N} bytes]` marker     |

Category: Illustrative (table-driven)
Origin: Multiple (Dev + QA + D29)

#### S-trace-03: Operator query 涵蓋 4 種語意篩選
> 驗證 D29 operator query contract — 各 query 行為符合預期

- **Given** Langfuse 內已存有混合各種 reasoning state 的 traces
- **When** Operator 跑 query
- **Then** 每種 query 涵蓋對應的 spans

| query                                              | covers                                       |
|----------------------------------------------------|----------------------------------------------|
| `WHERE metadata.reasoning IS NOT NULL`             | 所有 chat_model spans（key 永遠存在）          |
| `WHERE length(metadata.reasoning) > 0`             | 有實際 reasoning content 的 spans              |
| `WHERE metadata.reasoning != '<unsupported>'`      | 排除 non-reasoning-capable provider           |
| `WHERE metadata.reasoning LIKE '%[truncated%'`     | size cap 觸發的 spans (debugging)            |

Category: Illustrative (operational verification)
Origin: D29

---

### Rule: Judge model 不寫 reasoning 至 production Langfuse trace

#### S-trace-04: Judge gpt-5-mini calls 不出現 metadata.reasoning
> 驗證 D30 — judge invocation path 顯式 exclude `ReasoningTraceCallback`

- **Given** Eval pipeline 跑一批 D25 prompts 並用 `gpt-5-mini` judge 打分
- **When** Eval 完成、檢查 Langfuse production trace
- **Then** 該批的 agent traces 含 `metadata.reasoning`；judge 對應的 chat_model spans **沒有** `metadata.reasoning` key（不掛 callback）
- **And** Judge reasoning 由 Braintrust 自己處理（per memory `feedback_braintrust_host_only.md`），rubric 不洩漏到 Langfuse

Category: Illustrative
Origin: QA R1 (C5.5/C5.6) + Dev R2 + D30

---

### Rule: Stream-loop finalize + abort cleanup 確保 trace 不 lose reasoning

#### S-trace-05: Reasoning 是 last block 自然結束 trace 仍完整
> 驗證 D34 — stream-loop finalize 補洞

- **Given** Zara 送 query model 邊角行為 emit reasoning 後直接 finish 沒 text 沒 tool（reasoning 是最後 block）
- **When** Backend stream loop 結束呼叫 `mapper.finalize()`
- **Then** Segmenter buffer 內未斷句尾段被 emit 為 ReasoningStatus event；Langfuse `metadata.reasoning` 包含完整尾段；無 reasoning content 因 LLM call boundary 不觸發 flush 而 lost

Category: Illustrative (regression-guard)
Origin: Dev R2 + D34

#### S-trace-06: User abort 後 trace 標記 status 並保留尾段 reasoning
> 驗證 D35 — abort cleanup protocol 完整跑完。`reasoning_tail_aborted` + `status="aborted"` 為 D29 mode-aware schema 的 abort-path 必填 key（與 completed-path 必填的 `reasoning` key 同屬一個 contract、各自 optional 視 path 而定）。

- **Given** Aaron 在 reasoning streaming 中段 click Stop
- **When** Backend cancellation 被觸發
- **Then** Backend 完成所有 cleanup：cancel `agent.astream` + cancel in-flight LLM API call + 呼叫 `mapper.finalize()` 把 segmenter 殘留尾段顯式寫到 in-flight chat_model span 的 `metadata.reasoning_tail_aborted`（abort path 必填 key；`metadata.reasoning` 此 path 可缺，因為 `on_chat_model_end` 沒 fire） + 寫入 `metadata.status = "aborted"` 在 `agent.run` root span
- **And** Operator 用 `WHERE agent.run.metadata.status = 'aborted'` query 可篩出 aborted traces；用 `WHERE metadata.reasoning_tail_aborted IS NOT NULL` 可篩出 mid-reasoning 被中斷的 chat_model spans

Category: Illustrative
Origin: QA R1 + Dev R2 + D35

---

### Rule: Live UX 跟 trace metadata 接受可控 divergence

#### S-trace-07: Trace 跟 UX 內容可能微小差異但都來自 model ground truth
> 驗證 D36 — accept divergence contract

- **Given** Bella 跑一個 abort case：reasoning 在 streaming 中段被 abort
- **When** 比對 user 看到的 reasoning text（從 SSE log 重組）跟 Langfuse `metadata.reasoning` 內容
- **Then** 兩者都不 empty；可能微小差異（live UX = sentence-segmented；trace = AIMessage assembled）；但 reasoning core content 對齊
- **And** 任一路徑都來自同一個 `AIMessageChunk.content_blocks` / `AIMessage.content_blocks` 來源

Category: Illustrative
Origin: QA R3 (C5.7) + Dev R2 + D36

---

### Rule: Multi-tab 並發 streaming Langfuse 各 trace 不污染

#### S-trace-08: 同 session 兩 tab 並發產生兩個獨立 traces
> 驗證 D33 + D37 — per-request mapper + contextvars 正確 propagate

- **Given** Cathy 開兩個 tab 同 session 並發送出不同 query
- **When** 兩個 streaming 並發跑
- **Then** Langfuse 上產生兩個獨立 traces（兩個 agent.run roots）
- **And** 每個 trace 內 chat_model span 的 `metadata.reasoning` 只含該 tab 對應 turn 的 reasoning（無 cross-coroutine contextvars 污染）
- **And** 兩 traces 都正確繼承 trace-level attributes (`session_id`、`user_id`)；用 `session_id` filter 可篩出來

Category: Illustrative
Origin: QA R2 (CR.6) + D37

---

### Rule: content_blocks 失敗時 graceful degrade（不 hard block ship）

#### S-trace-09: Provider content_blocks 失敗 reasoning empty 但其他正常運作
> 驗證 D38 — per-provider graceful degrade ship policy

- **Given** 假設 LangChain `content_blocks` 對 `<provider>` reasoning blocks 抽取失敗（regression / version drift）
- **When** Donna 跑 D25 canonical prompt 在該 provider reasoning-on agent
- **Then** `data-reasoning-status` events 數量為 0；Frontend 落到 D15 idle text "Synthesizing..."；Langfuse `metadata.reasoning` 為 `""`；Streaming 仍完成、final answer 渲染、tool 正常運作；Release notes 記載該 provider 為 known limitation

Category: Illustrative (regression-guard)
Origin: Dev R1 (CR.1 / R1) + D38

---

### Journey Scenarios

#### J-trace-01: Multi-call 完整 trace tree 對齊 SEC 範例
> 驗證一個 reasoning-on multi-call turn 在 Langfuse 上產生 §6.3 規格的 trace tree

- **Given** Erin 跑 D25 canonical prompt 走 reasoning-on Gemini default agent
- **When** Turn 完成 + Langfuse SDK flush
- **Then** Trace tree 結構符合 §6.3 範例：1 個 `chat_request` trace → 1 個 `agent.run` span → 3 個 `chat_model.invoke` spans + tool spans 交錯；每個 chat_model span `metadata.reasoning` 符合 §6.2 schema 規格；trace-level `session_id` / `user_id` 在所有子 spans 都繼承

Category: Journey
Origin: Multiple (PO §6 + D29/D30/D37)

---

## Cross-Feature Risk Mitigation

### Rule: R1 content_blocks 風險 + R5 callback ordering POC ship gate

#### S-cross-01: POC 階段一輪 thinking model 驗證 callback chain 正確
> 驗證 R5 mitigation 跟 D37 ship gate

- **Given** POC 階段：跑一輪 reasoning-on Gemini（thinking model）的 D25 canonical prompt
- **When** Turn 完成、檢查 Langfuse trace
- **Then** 每個 `chat_model.invoke` span 上 `metadata.reasoning` 落在該 span 自己（**不**落在 parent `agent.run` span）
- **And** trace-level `session_id` / `user_id` 透過 contextvars 自動 propagate 到 chat_model span
- **And** 用 Langfuse API 以 `session_id` filter 可篩出該 chat_model span

Category: Illustrative (POC ship gate)
Origin: Dev R1 (C5.1) + D37 + §10 R5

---

# 註記

## Scope 移除（per D24）

下列原 Three Amigos 階段提到的 challenge 因 D24 (admin-configured models, no user-facing model swap UI) 已從 BDD scope **移除**：
- **C1.3** Mid-session provider switch + signature contamination
- **C1.4** Sticky contamination across swap-back

User 不能在 runtime 切 model，cross-provider session resume 不是 user flow。

## Demoted to unit test

下列 challenges 已 demoted 不寫 BDD scenarios（單元測試 / 實作檢查）：
- **C1.6** Callback wiring parity（folded into S-stream-05 verification）
- **C2.4** Historical replay re-emit（folded into S-chan-02）
- **C5.2** Always-write key contract（覆蓋於 S-trace-02 schema 表格）
- **C6.1** React batching frame overlap < 16ms（below human perception）
- **C6.9** Segmenter buffer overflow segmenter side
- **CR.7** reasoning-id collision unit-level

## Verification method 對應 (Phase 4 will detail)

- **Backend behaviors** (S-stream-04 [pre-SSE + mid-stream only], S-stream-05, ~~S-stream-06~~ [移出本期 scope], S-stream-07, S-stream-08, S-trace-01-09, S-cross-01)：deterministic verification (curl / API / Langfuse trace inspection)
- **Frontend behaviors** (S-rsn-01 to S-rsn-14, S-chan-01 to S-chan-04)：**Playwright + video record** (`frontend/tests/e2e/lifecycle/` + `frontend/tests/e2e/journeys/`，commit 進 repo 為 repeatable CI guardrail) — Browser-Use CLI 僅用於 agent-driven 一次性探索
- **Cross-cutting matrix** (S-stream-03)：Playwright multi-browser × multi-provider runs
- **Journey scenarios** (J-stream-01, J-chan-01, J-rsn-01, J-rsn-02, J-trace-01)：both deterministic API chain + browser flow

具體 verification spec 由下一階段 `verification-plan.md` 詳細展開。
