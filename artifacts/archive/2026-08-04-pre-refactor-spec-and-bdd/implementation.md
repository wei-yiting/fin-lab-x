# Implementation Plan: Multi-Provider Streaming with Reasoning Status

> Design Reference: [`design.md`](./design.md)
> BDD Scenarios: [`bdd-scenarios.md`](./bdd-scenarios.md) · Verification Plan: [`verification-plan.md`](./verification-plan.md)

**Goal:** 修掉 streaming pipeline 對多 provider 的 list-of-blocks bug、把 v1–v5 五個 agent 統一切到 `google_genai:gemini-2.5-flash`、新增 reasoning ephemeral UX (`data-reasoning-status` transient SSE event + Variant A reasoning indicator) 並把 reasoning 寫進 Langfuse `metadata.reasoning`（per chat_model span）。

**Architecture / Key Decisions:**
- Backend：`StreamEventMapper` 改用 LangChain v1 `chunk.content_blocks`（D1）；新增 `ReasoningSegmenter`（D3 / D26 80-char fallback）+ `ReasoningStatus` domain event + `data-reasoning-status` transient SSE 事件（D2）；新增 `ReasoningTraceCallback` extends `BaseCallbackHandler`，在 `on_chat_model_end` 把 reasoning 寫到 chat_model span `metadata.reasoning`（D4 / D29 mode-aware schema — completed path 必填 `reasoning`；abort path 必填 `reasoning_tail_aborted` + `status="aborted"`，三 key 共構同一 contract，optional 語意視 path 而定）。Mapper instance per-request（D33），新增 `finalize()`（D34）+ abort cleanup（D35）。
- Frontend：新增 `useReasoningStatus` hook（含 `clearedRef` + `finishedRef` guards · D31）；改寫 `ReasoningIndicator` 支援 idle/streaming/frozen 三態（Variant A · D5）+ stalled modifier（D14）；新增 `LiveStatusAnnouncer` ARIA hybrid（D22）；`AssistantMessage` 加 `data-reasoning-` filter（D39 belt-and-suspenders）。
- Provider matrix：v1–v5 全部用 `google_genai:gemini-2.5-flash`；judge 改 `gpt-5-mini`（不掛 `ReasoningTraceCallback`，D30）。Anthropic 與 OpenAI Responses 進 6-case acceptance matrix 但無 default agent binding（D7）。
- 推進策略：Phase 1 segmenter／schema → Phase 2 mapper rewire → Phase 3 SSE wire + serializer + callback → Phase 4 provider swap + agent capability config → Phase 5 frontend hook + indicator → Phase 6 ARIA + filter → Phase 7 abort/finalize cleanup → Phase 8 E2E acceptance + Langfuse trace verification（對應 `verification-plan.md`）。

**Tech Stack:** Python 3.11 / FastAPI / LangChain v1 (`langchain>=1.2.10`) + `langgraph>=0.5.0` + `langchain-google-genai` + `langchain-anthropic` + `langfuse>=4.5.0` / React 19 + AI SDK `@ai-sdk/react` v3 + `ai` v6 / Vite + Vitest + Playwright (含 video recording for BDD lifecycle specs)

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| ---------- | ------- | ------ | ----------------- | ----- |
| `langchain` | `>=1.2.10` | LangChain docs MCP — `oss/python/langchain/streaming.mdx#streaming-thinking-/-reasoning-tokens` | `AIMessageChunk.content_blocks` lazy property normalises Anthropic / OpenAI / Gemini reasoning into `[{"type":"reasoning","reasoning":...,"id":...}]`；filter `block["type"] == "reasoning"` for streaming, `block["type"] == "text"` for final answer text | already in `pyproject.toml` |
| `langchain` | `>=1.2.10` | LangChain docs MCP — `oss/python/langchain/messages.mdx#standard-content-blocks` | `AIMessage.content_blocks` 同樣可在 `on_chat_model_end` 對 `LLMResult.generations[0][0].message` 取出已組裝的 reasoning blocks；OpenAI multi-summary 攤平為多個 `{"type":"reasoning","id":"rs_abc","reasoning":...}` blocks（D12）| 用在 ReasoningTraceCallback |
| `langchain.chat_models.init_chat_model` | `>=1.2.10` | LangChain docs MCP — `oss/python/langchain/models.mdx#google-gemini` | `init_chat_model("google_genai:gemini-2.5-flash")` 為官方 provider-prefix 路徑；需要 `langchain[google-genai]` extra（提供 `langchain_google_genai`） | `init_chat_model` 在 base.py 已使用 |
| `langchain-google-genai` | latest | LangChain docs MCP — `oss/javascript/integrations/chat/google.mdx#reasoning-/-thinking` | Gemini 2.5 thinking 預設 emit thought summaries 但需要明確設 `thinking_budget`（即 `maxReasoningTokens`）才會輸出；`0` 關 reasoning、`-1` 模型預設 | reasoning-on / reasoning-off 透過 `thinking_budget` 設定 |
| `langchain-anthropic` | latest | LangChain docs MCP — `oss/python/langchain/streaming.mdx` | Anthropic extended thinking via `thinking={"type":"enabled","budget_tokens":N}`；reasoning 出現在 `content_blocks` 為 `{"type":"reasoning","reasoning":...,"extras":{"signature":...}}` | reasoning-on agent 需要明確設 thinking |
| `langfuse` | `>=4.5.0` | Context7 — `/langfuse/langfuse-docs` + `backend/agent_engine/docs/streaming_observability_guardrails.md` | (1) `langfuse.langchain.CallbackHandler` request-scoped；(2) `langfuse.update_current_observation(metadata={...})` 可在 `BaseCallbackHandler.on_chat_model_end` 內呼叫，會 attach 到當前 chat_model span；(3) `propagate_attributes(session_id=..., trace_name=...)` contextvar 在 async coroutine 天然 isolated（per-request scope）；(4) `@observe()` 在 4.5+ 支援 async generator | 已在 `pyproject.toml` |
| `@ai-sdk/react` | `^3.0.144` | already in repo (`useChat`, `onData`) | `useChat({ onData })` callback 接收 SSE 上 `data-*` events；`transient: true` payload 不進 `message.parts`（D2）；`useChat.stop()` 觸發 frontend abort | 已在 ChatPanel 使用 |
| `ai` | `^6.0.142` | AI SDK v6 native event types — design.md §5 wire format | `data-tool-progress` (transient) 已 wire 通；`data-reasoning-status` 沿用同一 transient pattern | 既有實作 reference |
| Playwright | latest (matches existing `playwright.config.ts`) | memory `feedback_msw_vs_real_backend.md` + `verification-plan.md` Browser Automation section | 用於 frontend BDD lifecycle scenarios（S-rsn-* / S-chan-03 / S-rsn-12 / S-trace-05 / S-trace-09 / J-rsn-02 / J-chan-01）：`page.goto / fill / click / waitForSelector / screenshot / evaluate / locator(...).innerHTML` + `use.video: 'on'` 錄全程 video | 主要 frontend BDD 驗證工具，commit 進 `frontend/tests/e2e/`；Browser-Use CLI 不在本期使用，僅留給 agent-driven 一次性探索 |
| Playwright | `^1.59.0` | `frontend/playwright.config.ts` + `frontend/tests/e2e/` | 用於 J-stream-01 6-case matrix video record | 既有 setup |

## Constraints

- **不 mutate per-chunk trace state**：依 `streaming_observability_guardrails.md` Rule 6，禁止在 streaming loop 內 call `update_current_observation()` per chunk；`ReasoningTraceCallback` 必須在 `on_chat_model_end`（per LLM call）一次性 attach metadata。
- **Reasoning 永遠不進 `message.parts`**（F5 / D2 hard contract）：SSE event 必須帶 `transient: True`；`AssistantMessage.parts.map` 必須 filter `data-reasoning-*`（D39 belt-and-suspenders）；server-side serializer assert 在 dev/CI raise，prod warn log（D39）。
- **Judge model `gpt-5-mini` 不掛 `ReasoningTraceCallback`**（D30）：避免 rubric 內容洩漏到 production Langfuse trace；judge 觀測 100% 由 Braintrust 處理（per memory `feedback_braintrust_host_only.md`）。
- **Per-request mapper scope**（D33）：每個 chat HTTP request 建立獨立 `StreamEventMapper`；不允許 module-global 或 per-session 共享（multi-tab 並發 streaming 會 cross-contamination）。
- **Backend 三路 boot failure 不可被抹平**（D23）：pre-SSE-open 失敗 → HTTP 5xx；mid-stream 失敗 → SSE `error` event；hung 30s → backend timeout 後 fall through 到 mid-stream。
- **Plain-text reasoning 渲染**（D20）：`<span>{text}</span>` + escape；不引入 markdown / inline-code render（reasoning ephemeral 1-2s 一閃過）。
- **All system UI labels in English**（D16）：`STOPPED` / `Synthesizing` / `Thinking` / `Stream interrupted` / `Generating response` 等 ARIA announce 字串、idle text、frozen labels 全部英文寫死，per memory `feedback_ui_labels_english.md`。
- **不引入 i18n infra**（D16）：直接 hardcode 字串；未來 refactor 為 translation module 是另一個 task。
- **Frontend test layer policy**（per `frontend-test-writing` skill）：純邏輯（`useReasoningStatus` guards / `reasoning-indicator-logic` post-tool gap）走 Vitest + RTL；視覺 lifecycle / abort sub-states / 6-case matrix 全部走 Playwright（commit 進 `frontend/tests/e2e/`），video record 由 `playwright.config.ts` `use.video: 'on'` 自動產出。

---

## File Plan

| Operation | Path | Purpose |
| --------- | ---- | ------- |
| Create | `backend/agent_engine/streaming/reasoning_segmenter.py` | `ReasoningSegmenter` — sentence-boundary segmentation with 80-char CJK fallback (D3 / D26) |
| Create | `backend/agent_engine/streaming/reasoning_trace_callback.py` | `ReasoningTraceCallback` — `BaseCallbackHandler.on_chat_model_end` writes `metadata.reasoning` to current chat_model span (D4 / D29) |
| Update | `backend/agent_engine/streaming/domain_events_schema.py` | Add `ReasoningStatus` frozen dataclass + extend `DomainEvent` union |
| Update | `backend/agent_engine/streaming/event_mapper.py` | Switch to `chunk.content_blocks`；新增 reasoning block dispatch；segmenter integration；hold-and-flush ordering (D28)；finalize() (D34)；per-request scope ctor (D33) |
| Update | `backend/agent_engine/streaming/sse_serializer.py` | `@serialize_event.register` for `ReasoningStatus` → `data-reasoning-status` (transient)；server-side assert (D39) |
| Update | `backend/agent_engine/agents/base.py` | Inject `ReasoningTraceCallback` into orchestrator callback list；abort cleanup protocol (D35)；mapper.finalize() always called |
| Update | `backend/agent_engine/agents/config_loader.py` | Extend `ModelConfig` with `provider_prefix: str` + `reasoning: Literal["on","off","unsupported"]` + `thinking_budget: int \| None` (D29 / D38 graceful degrade) |
| Update | `backend/agent_engine/agents/versions/v{1..5}/orchestrator_config.yaml` | Switch `model.name` → `google_genai:gemini-2.5-flash`；add `reasoning: on` flag default for production agents |
| Update | `backend/api/main.py` (lifespan / Orchestrator init) | Pass `ReasoningTraceCallback` reference into Orchestrator wiring (production path only) |
| Update | `pyproject.toml` | Add `langchain-google-genai` + `langchain-anthropic` to runtime deps |
| Create | `frontend/src/hooks/useReasoningStatus.ts` | React hook subscribing `data-reasoning-status` SSE events with two guard refs (D31)；exports `{ reasoningStatusText, handleData, clearReasoningStatus, resetForNewTurn }` |
| Update | `frontend/src/components/atoms/ReasoningIndicator.tsx` | Three modes: idle (3-dot bouncing) / streaming (text + dots cycler) / frozen (text dim + STOPPED label)；vertical-slot alignment with text mode (D17 9a base) |
| Update | `frontend/src/components/atoms/ReasoningIndicator.module.css` (or inline `index.css`) | Variant A visuals: 0.72rem italic / dots cycler / `.stalled` modifier / `.reasoning-status-frozen-label` (D5 / D14 / D17 / D21) |
| Update | `frontend/src/lib/reasoning-indicator-logic.ts` | Add `reasoningStatusText` param + post-tool idle gap branch (D15 §7.4) |
| Create | `frontend/src/components/atoms/LiveStatusAnnouncer.tsx` | ARIA `role="status" aria-live="polite" .sr-only` 高層級 transition status (D22) |
| Update | `frontend/src/components/organisms/AssistantMessage.tsx` | Filter `parts` 開頭為 `data-reasoning-` (D39 belt-and-suspenders) |
| Update | `frontend/src/components/pages/ChatPanel.tsx` | Wire `useReasoningStatus` 到 `useChat({ onData })`；compose `LiveStatusAnnouncer`；on stop / clear / send 呼叫 `clearReasoningStatus()` / `resetForNewTurn()` |
| Update | `frontend/src/index.css` | `.sr-only` standard pattern + Variant A reasoning-status CSS classes |
| Create | `backend/tests/streaming/test_reasoning_segmenter.py` | Unit tests for sentence boundary + 80-char fallback (D26) |
| Create | `backend/tests/streaming/test_reasoning_trace_callback.py` | Unit tests for `on_chat_model_end` schema (D29 5 scenarios) |
| Update | `backend/tests/streaming/test_event_mapper.py` | Add reasoning block dispatch + chunk.id boundary + hold-and-flush ordering + finalize() tests |
| Update | `backend/tests/streaming/test_sse_serializer.py` | Add `ReasoningStatus → data-reasoning-status` test + missing-flag assert test |
| Create | `backend/tests/streaming/test_event_mapper_reasoning_integration.py` | Integration: feed real LangChain `AIMessageChunk` sequences (Anthropic interleave / OpenAI multi-summary / Gemini empty) end-to-end through mapper |
| Create | `frontend/src/hooks/__tests__/useReasoningStatus.test.ts` | RTL `renderHook` tests covering 6 clear triggers + 2 guards (D31) |
| Create | `frontend/src/components/atoms/__tests__/ReasoningIndicator.test.tsx` | RTL tests for 3 modes + stalled modifier + frozen STOPPED visual (state-based) |
| Update | `frontend/src/lib/__tests__/reasoning-indicator-logic.test.ts` | Add post-tool idle gap branch tests (D15 §7.4) |
| Create | `frontend/src/components/atoms/__tests__/LiveStatusAnnouncer.test.tsx` | RTL tests for transition→announce string mapping (D22 8 transitions) |
| Update | `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` (create if missing) | Test `data-reasoning-*` filter (D39.b) |
| Create | `backend/tests/streaming/test_orchestrator_invoke_reasoning_path.py` | S-stream-05: invoke path 也產出 `metadata.reasoning`（與 streaming path 等價） |
| Create | `frontend/tests/e2e/critical/multi-provider-matrix.spec.ts` | Playwright spec 跑 6-case matrix → video output (J-stream-01)；`@critical` tag |
| Create | `frontend/tests/e2e/critical/fixtures/agent-capability/` | 6 yaml fragments (per matrix row：provider × reasoning mode) consumed by the matrix spec |
| Create | `backend/scripts/validation/verify_langfuse_trace.py` | Operator CLI helper：給 `trace_id` 等 SDK flush + 取 chat_model spans + 驗證 `metadata.reasoning` schema (D29) + `metadata.reasoning_tail_aborted` (D35 abort) + `metadata.status="aborted"` (S-trace-06)。同 folder 既有 `validate_*.py` 慣例 |
| Create | `backend/tests/scripts/test_verify_langfuse_trace.py` | Mock-based unit test for the verifier helper's parsing/schema-check logic (no live Langfuse) |

**Optional structure sketch** — backend streaming surface:

```text
backend/agent_engine/streaming/
  domain_events_schema.py        ← + ReasoningStatus
  event_mapper.py                ← rewire to content_blocks + segmenter + finalize
  reasoning_segmenter.py         ← NEW
  reasoning_trace_callback.py    ← NEW
  sse_serializer.py              ← + data-reasoning-status registered
  tool_error_sanitizer.py        ← unchanged
```

Frontend reasoning surface:

```text
frontend/src/
  hooks/
    useReasoningStatus.ts        ← NEW
  components/atoms/
    ReasoningIndicator.tsx       ← rewrite (3 modes)
    LiveStatusAnnouncer.tsx      ← NEW
  components/organisms/
    AssistantMessage.tsx         ← + data-reasoning-* filter
  components/pages/
    ChatPanel.tsx                ← wire useReasoningStatus + LiveStatusAnnouncer
  lib/
    reasoning-indicator-logic.ts ← + post-tool idle gap branch
```

---

### Task 1: Add `ReasoningStatus` domain event + `data-reasoning-status` SSE serialization

**Files:**
- Update: `backend/agent_engine/streaming/domain_events_schema.py`
- Update: `backend/agent_engine/streaming/sse_serializer.py`
- Update: `backend/tests/streaming/test_domain_events_schema.py`
- Update: `backend/tests/streaming/test_sse_serializer.py`

**What & Why:** 把 wire-format contract 先落地（schema 跟 serializer 之間有依賴）。下游 mapper / callback 才能引用。對應 BDD：S-chan-01 SSE 線上 reasoning 一定帶 `transient: true`（serializer-level 保證）；S-chan-04 missing-flag assert（dev/CI raise）。

**Implementation Notes:**
- 沿用既有 `@dataclass(frozen=True)` 慣例，**不**引入 Pydantic（design §4.1 說明）。
- Serializer 用 `@functools.singledispatch`，跟 `ToolProgress` 同 transient pattern（payload 含 `"transient": True`）。
- D39.c server-side guard：assert 在 dev/CI raise（環境變數 `APP_ENV=production` 改 warn log，避免 abort 整個 stream）。

**Critical Contract:**

```python
# domain_events_schema.py — add inside the dataclasses block
@dataclass(frozen=True)
class ReasoningStatus:
    reasoning_id: str
    text: str

DomainEvent = (
    MessageStart | TextStart | TextDelta | TextEnd |
    ToolCall | ToolResult | ToolError | ToolProgress |
    ReasoningStatus | StreamError | Finish
)
```

```python
# sse_serializer.py — register new event
@serialize_event.register
def _(event: ReasoningStatus) -> str:
    payload = {
        "type": "data-reasoning-status",
        "id": event.reasoning_id,
        "data": {"text": event.text},
        "transient": True,
    }
    _assert_reasoning_transient(payload)  # D39.c
    return _sse(payload)


def _assert_reasoning_transient(payload: dict) -> None:
    if not (payload.get("type", "").startswith("data-reasoning-")
            and payload.get("transient") is True):
        msg = "reasoning SSE event missing transient=True flag"
        if os.environ.get("APP_ENV", "").lower() == "production":
            logger.warning(msg, extra={"payload_type": payload.get("type")})
        else:
            raise AssertionError(msg)
```

**Test Strategy:**
- `test_domain_events_schema.py`: assert `ReasoningStatus("r-0", "理解問題")` is frozen, eq-equal to itself, in `DomainEvent` union (covers C5.2 completed-path always-write-key contract via separate `ReasoningTraceCallback` test).
- `test_sse_serializer.py`:
  - happy: `serialize_event(ReasoningStatus("r-0","理解問題"))` → JSON 字串含 `"type":"data-reasoning-status"` + `"transient":true` + `"id":"r-0"` + `"data":{"text":"理解問題"}`.
  - assert (S-chan-04 dev/CI portion): monkeypatch internal `_assert_reasoning_transient` 接受 payload missing `transient` → `pytest.raises(AssertionError)`.
  - prod warn (S-chan-04 prod portion): set `APP_ENV=production`，monkeypatch payload missing `transient` → `caplog` 含 `"reasoning SSE event missing transient=True flag"`、無 raise.
- 不需 integration test（無 framework wiring）。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/streaming/test_domain_events_schema.py backend/tests/streaming/test_sse_serializer.py -v` | All pass; new tests appear in output | wire-format contract anchored |
| Lint | `uv run ruff check backend/agent_engine/streaming/` | No errors | code style baseline |

**Execution Checklist:**

- [ ] 🔴 Add failing tests for `ReasoningStatus` schema + serializer (5 cases above)
- [ ] 🔴 Run `uv run pytest backend/tests/streaming/test_domain_events_schema.py backend/tests/streaming/test_sse_serializer.py` and confirm RED (`ReasoningStatus` not defined / serializer raises `TypeError`)
- [ ] 🟢 Add `ReasoningStatus` dataclass to `domain_events_schema.py`; register serializer + assert helper in `sse_serializer.py`
- [ ] 🟢 Re-run targeted tests → all pass
- [ ] 🔵 Review: 確認 assert helper unique enough message + caplog format with extra fields；無 duplicate code with existing transient pattern
- [ ] 🔵 Re-run targeted tests
- [ ] Commit: `git commit -m "feat(streaming): add ReasoningStatus domain event + data-reasoning-status SSE serializer with transient guard"`

---

### Task 2: Implement `ReasoningSegmenter` (sentence-boundary + 80-char fallback)

**Files:**
- Create: `backend/agent_engine/streaming/reasoning_segmenter.py`
- Create: `backend/tests/streaming/test_reasoning_segmenter.py`

**What & Why:** Backend sentence segmentation (D3) — frontend 不該塞語言邏輯。含 D26 80-char fallback 解決 Gemini 繁中無 `。` 問題。對應 BDD：S-stream-09（80-char fallback 觸發 soft-emit）。

**Implementation Notes:**
- API：`feed(delta) → Iterator[str]`、`flush() → str | None`、`reset() → None`。
- Sentence boundary：半形 `.!?` + whitespace（避免 `3.14` 誤切）；全形 `。！？` + `\n` 直接算。
- 80 字 fallback：當 buffer length ≥ 80 且本輪 feed 完仍無 terminator → soft-emit 整段、reset 該段 buffer，下個 chunk 從 0 開始累積。
- Trade-off 已知：`Dr. Smith` 仍會誤切，acceptable（D3）。

**Critical Contract:**

```python
class ReasoningSegmenter:
    SOFT_EMIT_CHAR_THRESHOLD = 80  # D26

    def __init__(self) -> None:
        self._buffer: str = ""

    def feed(self, delta: str) -> Iterator[str]:
        """Append delta, yield each completed sentence (terminator-bounded
        or soft-emit on 80+ char buffer without terminator)."""
        ...

    def flush(self) -> str | None:
        """Return remaining buffer as a sentence (no terminator);
        clears buffer. Returns None if buffer empty."""
        ...

    def reset(self) -> None:
        self._buffer = ""
```

**Test Strategy:**
- Happy paths (per delta scenarios): single half-width `.` w/ trailing space → split；single CJK `。` → split；`\n` → split；no terminator + < 80 chars → buffer (no yield)；no terminator + ≥ 80 chars → soft-emit.
- D26 fallback specific: feed 85 CJK chars no terminator in single feed → yields 1 sentence (=80-char prefix? or full 85-char since check 在 feed 完?) — 確定行為：實作上 buffer 累積 ≥ 80 才 emit 整段（含已超過 80 的部分），剩下 0 字進下一輪。對應 verification-plan S-stream-09 "80 字觸發 soft-emit + 餘下進新 buffer"。
- Edge: empty `feed("")` → no yield；`flush()` on empty buffer → None；mixed CJK + half-width terminator within same feed.
- Integration-level：`test_event_mapper.py` 會驗證 mapper 跟 segmenter 的 wire-up（Task 3）.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/streaming/test_reasoning_segmenter.py -v` | All pass | segmenter contract |

**Execution Checklist:**

- [ ] 🔴 Write tests covering 6+ scenarios above (terminator bounds + 80-char fallback + edge)
- [ ] 🔴 Run targeted pytest → RED (module not defined)
- [ ] 🟢 Implement `ReasoningSegmenter`
- [ ] 🟢 Re-run → GREEN
- [ ] 🔵 Refactor: extract terminator regex / threshold constant；ensure `feed` is generator (lazy) not list-returning
- [ ] 🔵 Re-run targeted tests
- [ ] Commit: `git commit -m "feat(streaming): add ReasoningSegmenter with 80-char CJK fallback"`

---

### Task 3: Rewire `StreamEventMapper` to `content_blocks` + reasoning dispatch + finalize()

**Files:**
- Update: `backend/agent_engine/streaming/event_mapper.py`
- Update: `backend/tests/streaming/test_event_mapper.py`
- Create: `backend/tests/streaming/test_event_mapper_reasoning_integration.py`

**What & Why:** Core streaming bug 的修復（content_blocks）+ reasoning block dispatch + LLM-call boundary detection + hold-and-flush ordering + stream-loop finalize。對應 BDD：S-stream-01/02/03（multi-provider streaming 跑通）、S-stream-09（segmenter integration）、S-rsn-10（hold-and-flush ordering）、S-trace-05（finalize 補洞）、S-stream-07（per-request mapper isolation）。

**Approach Decision:** Keep using `chunk["data"]` tuple `(msg_chunk, metadata)` — already what existing mapper does. New: switch from `msg_chunk.content` (raw string / list-of-blocks polymorphic per provider) to `msg_chunk.content_blocks` (LangChain v1 normalized iterator). Decision recorded in design D1.

**Implementation Notes:**
- `__init__(self, session_id)` 沿用 — instance per-request 由 `astream_run` 已保證（D33 既有設計，新加 docstring 強調）。
- `_handle_messages` 改寫核心 loop：iterate `msg_chunk.content_blocks`；對每個 block dispatch on `block["type"]`：
  - `"text"`: 沿用既有 TextStart/Delta/End emit（block 含 `text` field）。
  - `"reasoning"`: `block["reasoning"]` 餵給 `_segmenter.feed()`，每個 yielded sentence emit `ReasoningStatus(reasoning_id=self._current_reasoning_id, text=sentence)`. 第一個 reasoning chunk 在新 LLM call 內 lazy mount `_current_reasoning_id`（用 `f"reasoning-{self._reasoning_id_counter}"` 然後 `+=1`）.
  - `"tool_call_chunk"`: 沿用既有 tool_call_chunks lookup（也保留 `msg_chunk.tool_call_chunks` 為 backup — 部分 provider 不 expose 在 content_blocks）.
- D27 `chunk.id` boundary：
  - `msg_chunk.id is None` → continuation, no boundary trigger.
  - `msg_chunk.id != self._current_llm_call_id` (and not None) → 真正 boundary：先 `flush_segmenter_into_events(events)`、`reset()`、set `_current_llm_call_id`、`_current_reasoning_id = None`.
- D28 hold-and-flush ordering：在 emit `TextStart` 或 `ToolCall` event **之前**，必須先 emit segmenter buffer 內所有 sentences + 任何 `flush()` 殘留尾段（包成 `ReasoningStatus`）。
- D34 `finalize()` 擴充既有 `finalize` method：
  - 既有：emit 殘留 `TextEnd` + `Finish`.
  - 新增：先 emit `_segmenter.flush()` 殘留尾段為 `ReasoningStatus`（如果非 None）, 再 emit TextEnd + Finish。
- **D38 graceful degrade behavior** (S-trace-09): If a provider's `content_blocks` returns no `"reasoning"` blocks (regression / version drift), `_handle_reasoning_block` simply never fires — `_current_reasoning_id` stays None, no `ReasoningStatus` events emit, but text + tool dispatch continues normally. This is the natural behavior of the dispatch loop above; no extra graceful-degrade code path is needed in the mapper. Task 15's `STUB_CONTENT_BLOCKS_NO_REASONING=<provider>` dev-only flag stubs `chunk.content_blocks` to filter out reasoning blocks for the named provider, exercising this degraded path against the real backend for S-trace-09 verification (UX falls back to D15 `"Synthesizing"` idle text via Task 9's selector).

**Critical Contract:**

```python
class StreamEventMapper:
    def __init__(self, session_id: str) -> None:
        # ... existing ...
        self._segmenter = ReasoningSegmenter()
        self._current_llm_call_id: str | None = None
        self._current_reasoning_id: str | None = None
        self._reasoning_id_counter = 0

    def _handle_messages(self, chunk: dict) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        msg_chunk, _metadata = chunk["data"]
        if isinstance(msg_chunk, ToolMessage):
            return events

        # D27 boundary detection (None == continuation, no flush)
        if msg_chunk.id is not None and msg_chunk.id != self._current_llm_call_id:
            self._flush_segmenter_into(events)
            self._segmenter.reset()
            self._current_llm_call_id = msg_chunk.id
            self._current_reasoning_id = None

        if not self._message_started:
            events.append(MessageStart(message_id=msg_chunk.id, session_id=self._session_id))
            self._message_started = True

        for block in msg_chunk.content_blocks:
            block_type = block.get("type")
            if block_type == "reasoning":
                self._handle_reasoning_block(block, events)
            elif block_type == "text":
                self._handle_text_block(block, events)
            elif block_type == "tool_call_chunk":
                self._handle_tool_call_chunk_block(block, events)

        # usage_metadata still summed at chunk level (independent of content_blocks)
        if getattr(msg_chunk, "usage_metadata", None):
            self._total_input_tokens += msg_chunk.usage_metadata.get("input_tokens", 0)
            self._total_output_tokens += msg_chunk.usage_metadata.get("output_tokens", 0)

        return events

    def _handle_reasoning_block(self, block: dict, events: list[DomainEvent]) -> None:
        if self._current_reasoning_id is None:
            self._current_reasoning_id = f"reasoning-{self._reasoning_id_counter}"
            self._reasoning_id_counter += 1
        for sentence in self._segmenter.feed(block.get("reasoning", "")):
            events.append(ReasoningStatus(reasoning_id=self._current_reasoning_id, text=sentence))

    def _handle_text_block(self, block: dict, events: list[DomainEvent]) -> None:
        # D28 hold-and-flush: emit reasoning tail first
        self._flush_segmenter_into(events)
        text = block.get("text", "")
        if not text:
            return
        if not self._text_block_open:
            self._current_text_id = self._next_text_id()
            events.append(TextStart(text_id=self._current_text_id))
            self._text_block_open = True
        events.append(TextDelta(text_id=self._current_text_id, delta=text))

    def _handle_tool_call_chunk_block(self, block: dict, events: list[DomainEvent]) -> None:
        # D28 hold-and-flush: emit reasoning tail first
        self._flush_segmenter_into(events)
        if self._text_block_open:
            events.append(TextEnd(text_id=self._current_text_id))
            self._text_block_open = False
        tc_id = block.get("id")
        tc_name = block.get("name")
        if tc_id and tc_name and tc_id not in self._pending_tool_calls:
            self._pending_tool_calls[tc_id] = tc_name

    def _flush_segmenter_into(self, events: list[DomainEvent]) -> None:
        tail = self._segmenter.flush()
        if tail and self._current_reasoning_id is not None:
            events.append(ReasoningStatus(reasoning_id=self._current_reasoning_id, text=tail))

    def finalize(self) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        # D34 stream-loop finalize: emit segmenter tail if any
        self._flush_segmenter_into(events)
        if self._text_block_open:
            events.append(TextEnd(text_id=self._current_text_id))
            self._text_block_open = False
        events.append(
            Finish(finish_reason="stop",
                   usage=Usage(input_tokens=self._total_input_tokens,
                               output_tokens=self._total_output_tokens))
        )
        return events
```

**Test Strategy:**

`test_event_mapper.py` (extend existing):
- Reasoning happy: feed `AIMessageChunk(content=[{"type":"reasoning","reasoning":"理解問題。"}], id="msg-A")` → `[MessageStart, ReasoningStatus(text="理解問題")]` (note `flush()` not called yet — sentence already emitted on terminator).
- Reasoning + text in same chunk → events ordered `[..., ReasoningStatus, TextStart, TextDelta]` (D28 hold-and-flush preserves order via `_handle_text_block` calling `_flush_segmenter_into` first).
- chunk.id boundary (D27.1): two chunks with same `id="msg-A"` continuation → no flush between；third chunk `id="msg-B"` → segmenter flush + reset + new `_current_reasoning_id`.
- chunk.id None continuation (D27.1): chunk with `id=None` after `id="msg-A"` → not treated as boundary, no flush.
- Reasoning ID lifecycle (D27.2): same LLM call, three reasoning blocks (Anthropic interleaved)：all emit with same `reasoning_id`；下一 LLM call 重 mount 新 id.
- finalize() (D34): mapper sees only reasoning chunks no terminator → finalize 結果含 `ReasoningStatus(text=<tail>)` 在 `Finish` 之前.
- finalize() with no segmenter content → only `Finish` emitted (regression guard).
- usage_metadata still aggregated correctly across chunks (existing tests preserved).

`test_event_mapper_reasoning_integration.py` (new file):
- Anthropic interleave: feed sequence of `AIMessageChunk` representing `reasoning_A → text_1 → reasoning_B → text_2` (same `id`)。Assert event ordering：`[MessageStart, ReasoningStatus(A), TextStart, TextDelta(1), ReasoningStatus(B), TextDelta(2)]` — verify D13 / S-rsn-05 boundary backend.
- OpenAI multi-summary: build `AIMessage(content=[{"type":"reasoning","id":"rs_abc","summary":[{"type":"summary_text","text":"summary 1"},{"type":"summary_text","text":"summary 2"}]}])` then call `.content_blocks` → expect 2 reasoning blocks. Feed sequence to mapper → segmenter sees `summary 1\nsummary 2` joined (D12), emit 2 `ReasoningStatus` events.
- Gemini reasoning content present but no `。` for first 110 chars (CJK) → `_segmenter` triggers 80-char soft-emit per S-stream-09.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/streaming/test_event_mapper.py backend/tests/streaming/test_event_mapper_reasoning_integration.py -v` | All pass; integration covers 3 provider styles | mapper rewire + segmenter integration |
| Regression | `uv run pytest backend/tests/streaming/ -v` | All existing streaming tests still pass | guard against breaking text/tool path |

**Execution Checklist:**

- [ ] 🔴 Write reasoning dispatch + boundary + finalize tests in `test_event_mapper.py`; create `test_event_mapper_reasoning_integration.py` with 3 provider scenarios
- [ ] 🔴 Run targeted pytest → RED
- [ ] 🟢 Rewrite `_handle_messages` to iterate `content_blocks` + extract `_handle_reasoning_block` / `_handle_text_block` / `_handle_tool_call_chunk_block` / `_flush_segmenter_into`; update `__init__` for segmenter+state; update `finalize()`
- [ ] 🟢 Re-run targeted → GREEN
- [ ] 🔵 Refactor: ensure helpers cohesive；docstring on `__init__` 注明 per-request scope (D33)；no dead branch on legacy `msg_chunk.content` field
- [ ] 🔵 Re-run targeted + regression
- [ ] Commit: `git commit -m "refactor(streaming): rewire StreamEventMapper to content_blocks + reasoning dispatch + finalize"`

---

### Task 4: Implement `ReasoningTraceCallback` (per-LLM-call Langfuse metadata)

**Files:**
- Create: `backend/agent_engine/streaming/reasoning_trace_callback.py`
- Create: `backend/tests/streaming/test_reasoning_trace_callback.py`

**What & Why:** D4 / D29 Langfuse persistence — 把每個 LLM call 的 reasoning 內容寫到 chat_model span `metadata.reasoning`。對應 BDD：S-trace-01（per-LLM-call metadata）、S-trace-02 schema 5 cases（empty / sentinel / truncate）、S-trace-03 operator query（4 種語意）、S-trace-05/06（finalize/abort 不丟 reasoning）.

**Implementation Notes:**
- Subclass `langchain_core.callbacks.BaseCallbackHandler`；只 override `on_chat_model_end(self, response: LLMResult, *, run_id, parent_run_id, ...) -> None`.
- 從 `response.generations[0][0].message` 取 `AIMessage`；filter `content_blocks` for `block["type"] == "reasoning"`；`reasoning_text = "\n".join(block.get("reasoning", "") for block in reasoning_blocks)`.
- D29 schema for **completed path**（abort path 由 Task 6 `_handle_abort_cleanup` 單獨處理 — 寫 `reasoning_tail_aborted` + `status="aborted"`，與本 callback 的 `reasoning` key 同屬 D29 mode-aware contract）：
  - reasoning text non-empty → 直接寫入。
  - reasoning text empty (reasoning-on but no emission, or reasoning-off mode) → `""` empty string.
  - Provider not reasoning-capable (`agent_capability == "unsupported"`，via callback ctor arg) → `"<unsupported>"`.
  - len > 500_000 bytes → 截斷 `text[:500_000] + f"... [truncated, original {original_len} bytes]"`.
- 用 `langfuse.get_client().update_current_observation(metadata={"reasoning": value})`：當前 observation 在 `on_chat_model_end` 觸發點是該 chat_model span（因為 `langchain.CallbackHandler` 已 push span 到 contextvars stack）.
- D30 scope限制：callback 只在 production agent invocation 註冊；judge model 路徑不傳遞 — 由 caller (Orchestrator vs Braintrust eval runner) 控制。

**Critical Contract:**

```python
class ReasoningTraceCallback(BaseCallbackHandler):
    SIZE_CAP_BYTES = 500_000  # D29.2
    UNSUPPORTED_SENTINEL = "<unsupported>"  # D29.3

    def __init__(self, *, agent_reasoning_capability: Literal["on","off","unsupported"]) -> None:
        super().__init__()
        self._capability = agent_reasoning_capability

    def on_chat_model_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        try:
            value = self._compute_reasoning_value(response)
        except Exception:
            logger.exception("ReasoningTraceCallback failed; emitting empty string")
            value = ""
        get_client().update_current_observation(metadata={"reasoning": value})

    def _compute_reasoning_value(self, response: LLMResult) -> str:
        if self._capability == "unsupported":
            return self.UNSUPPORTED_SENTINEL
        gens = response.generations
        if not gens or not gens[0]:
            return ""
        message = getattr(gens[0][0], "message", None)
        if message is None:
            return ""
        reasoning_blocks = [b for b in message.content_blocks
                            if isinstance(b, dict) and b.get("type") == "reasoning"]
        joined = "\n".join(b.get("reasoning", "") for b in reasoning_blocks)
        if not joined:
            return ""
        encoded = joined.encode("utf-8")
        if len(encoded) > self.SIZE_CAP_BYTES:
            truncated = encoded[: self.SIZE_CAP_BYTES].decode("utf-8", errors="ignore")
            return f"{truncated}... [truncated, original {len(encoded)} bytes]"
        return joined
```

**Test Strategy:**
- D29 5-scenario schema (S-trace-02) — table-driven `pytest.mark.parametrize`：
  1. capability="on" + reasoning blocks present → exact joined string written via mock `update_current_observation`.
  2. capability="on" + no reasoning blocks (empty `content_blocks` or all text blocks) → `""`.
  3. capability="off" + no reasoning blocks → `""`.
  4. capability="unsupported" → `"<unsupported>"` regardless of message content.
  5. > 500_000 bytes → suffix matches `... [truncated, original {N} bytes]`.
- Defensive: `response.generations == []` → `""` (no exception).
- Defensive: callback raises internally (mock to raise inside `_compute_reasoning_value` via monkeypatch) → caught + `""` written, `caplog` records `"ReasoningTraceCallback failed"` exception log.
- **Always-write-key contract (D29 / C5.2 explicit guard)** — table-driven test: for every (capability ∈ {on, off, unsupported}) × (response shape ∈ {empty generations, all-text content, has-reasoning, internally-raises}) combination, `mock_client.update_current_observation.call_count == 1` AND `"reasoning"` is in `call_args.kwargs["metadata"]`. Closes the gap that S-trace-02 + S-trace-03 operator queries (`WHERE metadata.reasoning IS NOT NULL`) depend on.
- Mock strategy: monkeypatch `langfuse.get_client` to return a `MagicMock` whose `update_current_observation` calls are asserted via `call_args`.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/streaming/test_reasoning_trace_callback.py -v` | All 5 schema cases + 2 defensive + completed-path always-write-key contract test pass | D29 mode-aware schema (completed-path portion) anchored |

**Execution Checklist:**

- [ ] 🔴 Write 8 tests (5 schema + 2 defensive + 1 completed-path always-write-key contract)
- [ ] 🔴 Run targeted pytest → RED
- [ ] 🟢 Implement `ReasoningTraceCallback` (Critical Contract above)
- [ ] 🟢 Re-run targeted → GREEN
- [ ] 🔵 Refactor: extract reasoning extraction helper if shared with mapper later (don't pre-optimize); ensure all 3 sentinel constants are class-level
- [ ] 🔵 Re-run targeted
- [ ] Commit: `git commit -m "feat(streaming): add ReasoningTraceCallback for per-LLM-call Langfuse metadata.reasoning"`

---

### Flow Verification: Backend reasoning emit + persist (Tasks 1–4)

> Tasks 1–4 complete the backend reasoning emit + persistence flow. Verify the
> following before moving to provider switch (Task 5).

| #   | Method                | Step                                                                                                                                                                                          | Expected Result                                                                                                       |
| --- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1   | Runtime invocation    | Build a fake `AIMessageChunk` sequence (`reasoning_A`, `text_1`, `reasoning_B`, `text_2`, all same `id="msg-A"`) and feed through a fresh `StreamEventMapper`; collect all yielded events.    | Event ordering: `MessageStart, ReasoningStatus(A.s1), TextStart, TextDelta(1), ReasoningStatus(B.s1), TextDelta(2)`   |
| 2   | Runtime invocation    | Build `AIMessage` with two reasoning blocks (`b1.reasoning="abc"`, `b2.reasoning="def"`) wrap in `LLMResult`. Call `ReasoningTraceCallback(capability="on").on_chat_model_end(result, ...)`. | Mock `update_current_observation` called once with `metadata={"reasoning": "abc\ndef"}`                              |
| 3   | Targeted pytest       | `uv run pytest backend/tests/streaming/ -v`                                                                                                                                                   | All streaming tests pass (segmenter + mapper + callback + serializer + schema)                                        |
| 4   | Lint + type check     | `uv run ruff check backend/agent_engine/streaming/ && uv run pyright backend/agent_engine/streaming/`                                                                                         | No errors                                                                                                             |

- [ ] All flow verifications pass

---

### Task 5: Switch v1–v5 agents to `google_genai:gemini-2.5-flash` + extend `ModelConfig`

**Files:**
- Update: `backend/agent_engine/agents/config_loader.py`
- Update: `backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml`
- Update: `backend/agent_engine/agents/versions/v2_reader/orchestrator_config.yaml`
- Update: `backend/agent_engine/agents/versions/v3_quant/orchestrator_config.yaml`
- Update: `backend/agent_engine/agents/versions/v4_graph/orchestrator_config.yaml`
- Update: `backend/agent_engine/agents/versions/v5_analyst/orchestrator_config.yaml`
- Update: `backend/agent_engine/agents/base.py` (init_chat_model arg passing)
- Update: `pyproject.toml` (add `langchain-google-genai`, `langchain-anthropic`)
- Update: `backend/agent_engine/utils/model_context_registry.yaml` (add Gemini context window entry)
- Update: `backend/tests/agents/` (existing config_loader / orchestrator tests)

**What & Why:** F1 + D24 — admin-configured provider binding. 對應 BDD：S-stream-01（default v3 用 Gemini）、S-stream-02（切 agent version 仍走 Gemini）、S-stream-03 6-case matrix（reasoning capability 來自 config）、S-trace-04（judge gpt-5-mini scope 限制）.

**Approach Decision:** Reasoning capability 標記放在 agent config（不是 model registry），因為 agent 的 reasoning-on/off 是 admin 行為決定（D24），不只是 model 物理能力。`ModelConfig.reasoning: Literal["on","off","unsupported"]` 同時驅動：(a) `init_chat_model` 的 thinking budget 參數、(b) `ReasoningTraceCallback(agent_reasoning_capability=...)` 的 sentinel 行為、(c) 6-case test matrix 篩選。

**Implementation Notes:**
- `ModelConfig` 加：
  - `name: str` — 仍接受 `"google_genai:gemini-2.5-flash"`（provider prefix 直接寫在 name 內）；保留既有命名 convention.
  - `reasoning: Literal["on","off","unsupported"] = "off"` — 預設 off，避免 silently 開啟 reasoning 浪費 token.
  - `thinking_budget: int | None = None` — Anthropic `budget_tokens` / Gemini `thinking_budget`（reasoning-on 才設）.
- `Orchestrator.__init__` 把 reasoning + thinking_budget 轉成 `init_chat_model` kwargs：
  - Gemini：`reasoning=="on"` 時 `thinking_budget` 從 config 傳（`None` → 由 LangChain / Gemini 走 default）；`reasoning=="off"` 時 `thinking_budget=0` 強制關閉.
  - Anthropic：`reasoning=="on"` 時 `thinking={"type":"enabled","budget_tokens": config.thinking_budget}` — Anthropic API 要求 budget_tokens 必填（且 ≥1024），所以本期只在 6-case matrix 對 Anthropic row fixture 顯式設 budget；其它 path（包括 v1–v5 default agent，全部用 Gemini）保持 `thinking_budget=None` 不會打到這條 Anthropic-required 路徑.
  - OpenAI Responses：`init_chat_model("openai:gpt-5-mini", reasoning_effort="medium" if on else None, use_responses_api=True)`.
- v1–v5 yaml 統一：
  ```yaml
  model:
    name: "google_genai:gemini-2.5-flash"
    temperature: 0.0
    reasoning: "on"
    thinking_budget: null   # 本期暫用 None（讓 provider 走 default）；具體數字待 6-case matrix 觀察 reasoning depth 行為後另行決定
  ```
- Update `model_context_registry.yaml`: add `gemini-2.5-flash: { max_input_tokens: 1048576, source: google_official }`. 確認 `compute_section_soft_cap_chars` 不破.
- pyproject.toml: 新增 `langchain-google-genai>=2.0.0` 跟 `langchain-anthropic>=0.4.0` 在 main deps（不放 optional dev）.

**Critical Contract:**

```python
# config_loader.py
class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = "gpt-4o-mini"
    temperature: float = 0.0
    reasoning: Literal["on", "off", "unsupported"] = "off"  # NEW
    thinking_budget: int | None = None                       # NEW
```

```python
# base.py — _init_model() helper inside Orchestrator.__init__
def _init_model(config: ModelConfig) -> BaseChatModel:
    name = config.name  # e.g. "google_genai:gemini-2.5-flash"
    provider = name.split(":", 1)[0] if ":" in name else "openai"
    kwargs: dict[str, Any] = {"temperature": config.temperature}
    if provider == "google_genai":
        # reasoning="on" + thinking_budget=None → Gemini 走 default thinking budget
        # reasoning="off" → 強制 0 關閉 thinking
        kwargs["thinking_budget"] = config.thinking_budget if config.reasoning == "on" else 0
    elif provider == "anthropic":
        if config.reasoning == "on":
            if config.thinking_budget is None:
                raise ValueError(
                    "Anthropic provider with reasoning='on' requires explicit thinking_budget "
                    "(Anthropic API requires budget_tokens, minimum 1024). Set in agent yaml."
                )
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": config.thinking_budget}
    elif provider == "openai":
        if config.reasoning == "on":
            kwargs["reasoning_effort"] = "medium"
            kwargs["use_responses_api"] = True
    return init_chat_model(name, **kwargs)
```

**Test Strategy:**
- `test_config_loader.py`: `reasoning` defaults to `"off"`; YAML with `reasoning: on, thinking_budget: null` parses correctly; YAML with explicit integer also parses; `reasoning: invalid` raises Pydantic ValidationError.
- `test_orchestrator_init.py` (extend existing):
  - mock `init_chat_model`，assert called with appropriate kwargs for v3 default config (Gemini + reasoning="on" + thinking_budget=None → kwargs has `thinking_budget=None`，讓 LangChain 走 default).
  - assert reasoning="off" path 傳 `thinking_budget=0`（強制關閉）.
  - assert Anthropic + reasoning="on" + thinking_budget=None **raises ValueError** with message about Anthropic API requirement.
  - assert Anthropic + reasoning="on" + thinking_budget=2048 → kwargs has `thinking={"type":"enabled","budget_tokens":2048}`.
- 5 yaml files smoke-load via `VersionConfigLoader("v{N}_{name}").load()` → all expose `model.name == "google_genai:gemini-2.5-flash"` and `model.reasoning == "on"`.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/agents/ -v -k "config or init"` | All pass | config schema + orchestrator init wiring |
| Smoke | `for v in v1_baseline v2_reader v3_quant v4_graph v5_analyst; do uv run python -c "from backend.agent_engine.agents.config_loader import VersionConfigLoader; c=VersionConfigLoader('$v').load(); assert c.model.name=='google_genai:gemini-2.5-flash', c.model.name; assert c.model.reasoning=='on', c.model.reasoning; print('$v OK')"; done` | 5 lines `vN_xxx OK` | All 5 versions migrated |
| Deps install | `uv sync` | No resolver errors | new google_genai/anthropic deps installable |

**Execution Checklist:**

- [ ] 🔴 Write/extend config_loader + orchestrator init tests for `reasoning` field & `_init_model` provider branching
- [ ] 🔴 Run pytest → RED
- [ ] 🟢 Extend `ModelConfig`; refactor `Orchestrator.__init__` to call `_init_model(config)`; update 5 yaml files; add registry entry; bump pyproject + uv sync
- [ ] 🟢 Re-run pytest → GREEN
- [ ] 🔵 Refactor: ensure no duplicate provider-name parsing (extract `_provider_prefix(name)` helper if used in 2+ places)
- [ ] 🔵 Re-run pytest + smoke loop
- [ ] Commit: `git commit -m "feat(agents): switch v1-v5 to gemini-2.5-flash + add reasoning capability config"`

---

### Task 6: Wire `ReasoningTraceCallback` + `mapper.finalize()` + abort cleanup into `Orchestrator`

**Files:**
- Update: `backend/agent_engine/agents/base.py`
- Update: `backend/tests/agents/test_orchestrator_streaming.py` (extend existing)
- Create: `backend/tests/streaming/test_orchestrator_invoke_reasoning_path.py`

**What & Why:** F4 / F7 / F8 — make Orchestrator inject `ReasoningTraceCallback` next to `langfuse.langchain.CallbackHandler` for both streaming (`astream_run`) and invoke (`run` / `arun`)；implement D35 abort cleanup protocol；ensure `mapper.finalize()` runs on natural finish AND on `asyncio.CancelledError`. 對應 BDD：S-stream-05（invoke 也產 reasoning trace）、S-stream-08（abort 後新 turn 不污染）、S-trace-01（per-LLM-call spans）、S-trace-06（abort cleanup status="aborted" + tail reasoning preserved）、S-trace-08（multi-tab contextvars isolation, 已天然由 D33 保證）.

**Approach Decision — abort segmenter tail path:**

| Option | Summary | Status | Why |
| ------ | ------- | ------ | --- |
| A | Abort handler explicitly extracts segmenter tail from `mapper.finalize()` events and calls `update_current_observation(metadata={"reasoning_tail_aborted": text})` for the in-flight chat_model span (separate metadata key to avoid colliding with normal `metadata.reasoning` written by `on_chat_model_end` for completed calls) | Selected | When abort cancels mid-LLM-call, `on_chat_model_end` may never fire — `ReasoningTraceCallback` (which subscribes to `on_chat_model_end`) won't see the partial AIMessage and Langfuse `metadata.reasoning` would be missing. The tail must be written explicitly. Using a distinct key (`reasoning_tail_aborted`) keeps S-trace-02 schema clean (`metadata.reasoning` always reflects completed-call content) while still satisfying S-trace-06 step 5 |
| B | Have `mapper.finalize()` itself call into Langfuse via a callback hook | Rejected | Couples the mapper (pure event translator) to Langfuse client; violates Rule 8 "keep streaming glue thin"; harder to test |
| C | Discard segmenter tail on abort entirely, weaken S-trace-06 step 5 | Rejected | Loses Langfuse observability for the most interesting moments (user aborted because something was off — operator wants to see what model was thinking right before stop). Conflicts with design D35 step (3) intent |

S-trace-06 verification step 5 will assert against `metadata.reasoning_tail_aborted` (not `metadata.reasoning`); this requires updating the BDD verifier helper accordingly (Task 14).

**Implementation Notes:**
- `_build_langfuse_config` 改為接受 `agent_reasoning_capability` (從 `self.config.model.reasoning`)；callbacks list 變成 `[langfuse_handler, ReasoningTraceCallback(agent_reasoning_capability=...)]`. 對 `mode="stream"` 跟 `mode="invoke"` 兩條路徑都建立同樣的 callback list（F8 contract — invoke path 也要 reasoning metadata）.
- `astream_run` 既有 `try / except` 改寫為三段：
  1. natural finish path：`async for raw_chunk` 結束 → `for event in mapper.finalize()` (含 D34 segmenter tail).
  2. `asyncio.CancelledError`：執行 D35 cleanup helper（見 Critical Contract `_handle_abort_cleanup`）：drain `mapper.finalize()` 收集 ReasoningStatus events、join text、explicitly write to current observation `metadata.reasoning_tail_aborted`、寫 root trace `metadata.status="aborted"`、re-raise `CancelledError`.
  3. 其他 `Exception`：既有 `mapper.finalize()` + `StreamError` + `Finish(error)` 路徑保留.
- 注意 `update_current_trace` 跟 design 寫的「on agent.run root span」一致：在 `with propagate_attributes(...)` block 結束前呼叫，contextvars 仍有效；`update_current_observation` 在 cancellation 觸發點 contextvars 仍指向最近活躍的 chat_model span（async cleanup 在 contextvars unwind 之前執行）。
- `run` / `arun` 路徑：`_build_langfuse_config(mode="invoke", ...)` 已經回傳同樣 callbacks list；invoke 完成後 `on_chat_model_end` 自然觸發 callback；不需要額外 abort handling（invoke 是 blocking, 沒有 mid-call cancel UX）.

**Critical Contract:**

```python
def _build_langfuse_config(self, *, mode: Literal["invoke","stream"], request_id: str,
                          session_id: str | None = None, **extra_metadata) -> tuple[RunnableConfig, _LangfusePropagationAttributes]:
    handler = CallbackHandler()
    reasoning_callback = ReasoningTraceCallback(
        agent_reasoning_capability=self.config.model.reasoning,
    )
    # ... existing trace_name / metadata logic ...
    config: RunnableConfig = {
        "callbacks": [handler, reasoning_callback],   # NEW: reasoning_callback for both invoke + stream
        "run_name": "chat-turn",
        "metadata": metadata,
    }
    return config, propagation


async def astream_run(self, *, message, session_id, ...):
    config, propagation = self._build_langfuse_config(mode="stream", ...)
    config["configurable"] = {"thread_id": session_id}
    mapper = StreamEventMapper(session_id=session_id)  # per-request (D33)

    with propagate_attributes(**propagation):
        try:
            input_data = ...  # existing
            async for raw_chunk in self.agent.astream(input_data, config=config,
                                                     stream_mode=["messages","updates","custom"],
                                                     version="v2"):
                chunk = ...  # existing tuple normalization
                for event in mapper.process_chunk(chunk):
                    yield event
            # natural finish (D34)
            for event in mapper.finalize():
                yield event
        except asyncio.CancelledError:
            self._handle_abort_cleanup(mapper)
            raise
        except Exception as e:
            for event in mapper.finalize():
                if not isinstance(event, Finish):
                    yield event
            yield StreamError(error_text=sanitize_tool_error(str(e)))
            yield Finish(finish_reason="error")


def _handle_abort_cleanup(self, mapper: StreamEventMapper) -> None:
    """D35 abort cleanup. Drains segmenter, writes tail to in-flight chat_model
    span via metadata.reasoning_tail_aborted (distinct key from on_chat_model_end's
    metadata.reasoning so the schema stays consistent), and marks root trace as
    aborted. Swallows internal exceptions so cancellation propagation isn't
    blocked by Langfuse failures."""
    tail_segments: list[str] = []
    try:
        for event in mapper.finalize():
            if isinstance(event, ReasoningStatus):
                tail_segments.append(event.text)
    except Exception:
        logger.exception("mapper.finalize raised during abort cleanup")
    client = get_client()
    if tail_segments:
        try:
            client.update_current_observation(
                metadata={"reasoning_tail_aborted": "\n".join(tail_segments)},
            )
        except Exception:
            logger.exception("failed to write reasoning_tail_aborted to current observation")
    try:
        client.update_current_trace(metadata={"status": "aborted"})
    except Exception:
        logger.exception("failed to mark trace aborted")
```

**Test Strategy:**
- `test_orchestrator_streaming.py` (extend):
  - Mock `agent.astream` to yield reasoning + text chunks → assert config["callbacks"] includes `ReasoningTraceCallback` instance.
  - Mock `agent.astream` to raise `asyncio.CancelledError` mid-flight after at least one reasoning chunk in segmenter buffer (un-terminated) → assert (a) `client.update_current_observation` called with `metadata={"reasoning_tail_aborted": <segmenter tail>}`，(b) `client.update_current_trace` called with `metadata={"status":"aborted"}`，(c) `CancelledError` propagated to caller.
  - Mock abort with empty segmenter buffer (no in-flight reasoning) → assert `update_current_observation` **not** called for `reasoning_tail_aborted`；only `update_current_trace(metadata.status=aborted)` called.
  - Mock `update_current_trace` raises (Langfuse down) → `CancelledError` still propagates (cleanup is best-effort).
  - Mock natural finish → assert `mapper.finalize()` called once + abort cleanup helper not entered.
- `test_orchestrator_invoke_reasoning_path.py` (new, S-stream-05):
  - Mock `agent.ainvoke` returning `{"messages":[AIMessage(content_blocks=[{"type":"reasoning","reasoning":"think..."},{"type":"text","text":"answer"}])]}`.
  - Mock `langfuse.get_client` so `update_current_observation` calls are captured.
  - Wire callback handler manually (because we mock agent.ainvoke, the callback chain isn't auto-fired by LangChain in test — instead, assert that `_build_langfuse_config(mode="invoke")` returns a config with `ReasoningTraceCallback` in `callbacks`，AND directly invoke `ReasoningTraceCallback(...).on_chat_model_end(LLMResult(generations=[[ChatGeneration(message=AIMessage(...))]]))` to verify the chain wiring).
  - For end-to-end equivalence assertion, run actual `Orchestrator.run(prompt)` against a stubbed `agent.invoke` that calls the callback's `on_chat_model_end` directly → assert observed `metadata.reasoning` matches what streaming path's mock would produce for the same `AIMessage`.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `uv run pytest backend/tests/agents/ backend/tests/streaming/test_orchestrator_invoke_reasoning_path.py -v` | All pass | callback wiring + abort + invoke parity |
| Regression | `uv run pytest backend/tests/ -v -m "not integration and not eval and not sec_integration"` | All non-external tests pass | Catch broken Orchestrator wiring elsewhere |

**Execution Checklist:**

- [ ] 🔴 Write callback-list assertion + abort cleanup test + invoke-path test
- [ ] 🔴 Run pytest → RED
- [ ] 🟢 Modify `_build_langfuse_config` to inject `ReasoningTraceCallback`; restructure `astream_run` try/except per Critical Contract
- [ ] 🟢 Re-run targeted → GREEN
- [ ] 🔵 Refactor: extract `_handle_abort_cleanup(mapper)` helper if astream_run gets long
- [ ] 🔵 Re-run regression
- [ ] Commit: `git commit -m "feat(agents): inject ReasoningTraceCallback + abort cleanup protocol (D35)"`

---

### Flow Verification: Backend end-to-end with real Gemini call (Tasks 1–6)

> First time we hit a real LLM. Validates content_blocks + callback ordering +
> session_id propagation (R5 POC ship gate). Requires `GOOGLE_API_KEY` + `LANGFUSE_*` env.

| #   | Method                      | Step                                                                                                                                                                                                                                                | Expected Result                                                                                                                                                                                                  |
| --- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | curl + jq                   | `SESSION_ID=$(uuidgen); curl -s -N -X POST $BACKEND_BASE/api/v1/chat -H "Content-Type: application/json" -d "{\"id\":\"$SESSION_ID\",\"messages\":[{\"role\":\"user\",\"parts\":[{\"type\":\"text\",\"text\":\"$PROMPT\"}]}],\"trigger\":\"submit-message\"}" > /tmp/poc.sse` | SSE 含 `data: {"type":"data-reasoning-status",...,"transient":true}` ≥ 1 個；`data: {"type":"finish",...}` 結尾；無 `error` event                                                                          |
| 2   | Trace inspection            | Extract trace_id from `start` event; `uv run python backend/scripts/validation/verify_langfuse_trace.py $TRACE_ID`                                                                                                                                  | Trace tree 含 1 個 `agent.run` parent + ≥3 個 `chat_model.invoke` children；每個 chat_model span `metadata.reasoning` key 存在且 non-empty；parent `agent.run.metadata.reasoning` **不**存在 (S-trace-01) |
| 3   | Trace inspection (R5 gate)  | `curl -s -H "Authorization: Bearer $LANGFUSE_KEY" "$LANGFUSE_API_BASE/api/public/observations?sessionId=$SESSION_ID&type=GENERATION" \| jq '.data \| length'`                                                                                       | Returns ≥3 (chat_model spans 透過 `session_id` filter 撈得到 — D37 contextvars propagation OK, S-cross-01)                                                                                                  |
| 4   | Targeted pytest             | `uv run pytest backend/tests/streaming/ backend/tests/agents/ -v`                                                                                                                                                                                   | All pass                                                                                                                                                                                                          |

- [ ] All flow verifications pass — POC ship gate cleared

---

### Task 7: `useReasoningStatus` hook with two guards (D31)

**Files:**
- Create: `frontend/src/hooks/useReasoningStatus.ts`
- Create: `frontend/src/hooks/__tests__/useReasoningStatus.test.ts`

**What & Why:** Subscribe `data-reasoning-status` SSE 事件、在 6 個 clear trigger 清空 text、在 `clearedRef`/`finishedRef` 兩個 race condition 防 ghost。對應 BDD：S-rsn-11 (clear race)、S-rsn-12 (late events after finish), S-chan-01 (transient flag 不進 parts — hook 永遠不寫 parts), S-trace-08 part of frontend isolation.

**Implementation Notes:**
- Pattern mirror `useToolProgress` (existing) for `useChat({ onData })` integration.
- API：`{ reasoningStatusText: string | null, handleData: (part) => void, clearReasoningStatus: () => void, resetForNewTurn: () => void }`.
- `handleData` switch on `part.type`:
  - `data-reasoning-status` → `setText(part.data.text)` (受 guards check)
  - `text-start` / `tool-input-available` → `setText(null)`
  - `finish` / `error` → `setText(null)` + `finishedRef.current = true`
- `clearReasoningStatus` → `setText(null)` + `clearedRef.current = true`.
- `resetForNewTurn` → `setText(null)` + reset both refs to false.
- `handleData` 開頭 check：`if (clearedRef.current || finishedRef.current) return`.

**Critical Contract:**

```typescript
type ReasoningStatusDataPart = {
  type: string;
  id?: string;
  data?: { text?: string };
};

export function useReasoningStatus(): {
  reasoningStatusText: string | null;
  handleData: (part: ReasoningStatusDataPart) => void;
  clearReasoningStatus: () => void;
  resetForNewTurn: () => void;
};
```

**Test Strategy** (per `frontend-test-writing` skill — RTL `renderHook` for hook unit tests):

- 6 clear trigger tests:
  - SSE: `text-start` clears；`tool-input-available` clears；`finish` clears + sets finishedRef；`error` clears + sets finishedRef.
  - App-level: `clearReasoningStatus()` clears + sets clearedRef；`resetForNewTurn()` clears + resets both refs.
- D31 guards:
  - `clearedRef` (S-rsn-11): after `clearReasoningStatus()`, subsequent `data-reasoning-status` events ignored (text stays null) until `resetForNewTurn()`.
  - `finishedRef` (S-rsn-12): after `finish` event, subsequent `data-reasoning-status` events ignored.
- Routing isolation: non-`data-reasoning-status` `data-*` event (e.g. `data-tool-progress`) doesn't affect `reasoningStatusText`.
- Idempotent `resetForNewTurn`: call twice → still works.
- **Anti-patterns to avoid** (per `frontend-test-writing` `anti-patterns.md`): no `waitForTimeout`; assert on `result.current.reasoningStatusText` directly (state-based); no `vi.useFakeTimers` needed (pure synchronous state).

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `cd frontend && npm test -- useReasoningStatus` | All pass | hook contract |
| Type | `cd frontend && npx tsc --noEmit -p tsconfig.app.json` | No errors | typing correct for SSE payload shape |

**Execution Checklist:**

- [ ] 🔴 Write 8+ tests covering 6 triggers + 2 guards + routing isolation; reference `frontend-test-writing` skill
- [ ] 🔴 Run targeted vitest → RED
- [ ] 🟢 Implement `useReasoningStatus` (state + 2 refs + 4 callbacks)
- [ ] 🟢 Re-run → GREEN
- [ ] 🔵 Refactor: ensure useCallback deps correct; ref reset symmetry
- [ ] 🔵 Re-run targeted
- [ ] Commit: `git commit -m "feat(frontend): add useReasoningStatus hook with clearedRef + finishedRef guards"`

---

### Task 8: Rewrite `ReasoningIndicator` for 3 modes (idle / streaming / frozen) + Variant A CSS

**Files:**
- Update: `frontend/src/components/atoms/ReasoningIndicator.tsx`
- Update: `frontend/src/index.css` (or new module CSS file co-located)
- Create: `frontend/src/components/atoms/__tests__/ReasoningIndicator.test.tsx`

**What & Why:** Make existing 3-dot bouncing component support text mode + frozen mode. Vertical-slot alignment so transitions don't jump (D17 base / S-rsn-02). Variant A visual (D5). 對應 BDD：S-rsn-02（pre-response 3-dot vertical alignment）、S-rsn-03（plain text rendering, S-rsn-04 long-sentence overflow）、S-rsn-04（hard-clip without ellipsis）、S-rsn-06（stalled modifier）、S-rsn-08 9a（pre-response idle abort 顯示 STOPPED）、S-rsn-08 9c（abort during text — STOPPED label inline 同樣使用 frozen-label 視覺）、S-rsn-13 part (frozen visual).

**Approach Decision:**

| Option | Summary | Status | Why |
| ------ | ------- | ------ | --- |
| A | Single `ReasoningIndicator` component with `mode` discriminated prop (`'idle'` \| `'streaming'` \| `'frozen'`) | Selected | Vertical-slot alignment (D17 9a) requires sharing one DOM container between idle dots + text mode；one component prevents drift between two implementations |
| B | Split into `IdleIndicator` + `ReasoningStatusText` 兩個 components | Rejected | DOM container alignment（dots 底部 = text 底部）會被 React tree 隔開，難保證 visual continuity |

**Implementation Notes:**
- Variant A CSS classes (D5 / D14 / D17 / D21):
  - `.reasoning-status` wrapper: `display:flex`, `align-items:flex-end`, `padding: 4px 12px 6px`, `margin-top: -8px`, `font-size: 0.72rem`, `font-style: italic`, `color: var(--muted-foreground)`, container height `calc(0.72rem * 1.5)`.
  - `.reasoning-status-text`: `flex:1`, `min-width:0`, `overflow:hidden`, `white-space:nowrap` (D21 hard-clip, no ellipsis).
  - `.reasoning-status-dots-cycler`: `flex-shrink:0`, `letter-spacing:0.08em`, `padding-left:5px` — 0→1→2→3 dot cycle via animation.
  - `.idle-dots`: 3 spans `0.4rem` diameter, `gap:3px`, bouncing animation (`translateY(-25%)↔0`, 1s, `0.15s` stagger).
  - `.stalled` modifier: dots cycler `animation-duration: 2.5s`, opacity `0.55`, `transition: opacity 800ms ease`.
  - `.reasoning-status-frozen-label`: `font-size: 0.62rem`, `padding: 1px 5px`, `color: var(--status-aborted)`, `background: var(--status-aborted-bg)`. Inline next to text. Used both by 9a (standalone STOPPED in vertical slot) and 9c (after partial answer text — same class, embedded by parent component).
- Add CSS variable `--status-aborted` if missing；reuse existing if present.
- Plain text rendering (D20): `<span>{text}</span>` 直接渲染；不需要 escape — React 自動 escape.
- Component props:
  ```typescript
  interface ReasoningIndicatorProps {
    text?: string | null;          // null → idle 3-dot；string → streaming/frozen
    state?: 'streaming' | 'frozen';// only meaningful when text is non-null
    stalled?: boolean;             // applies .stalled modifier
  }
  ```
- For idle mode (text=null): render 3-dot bouncing inside `.reasoning-status` container (vertical slot shared).
- For streaming mode: render `<span class="reasoning-status-text">{text}</span><span class="reasoning-status-dots-cycler">...</span>` (cycler is animated CSS pseudo / static dot count cycling via animation).
- For frozen mode: render `<span class="reasoning-status-text" style="opacity:0.65">{text}</span><span class="reasoning-status-frozen-label">STOPPED</span>` (D16 English).

**Test Strategy** (per `frontend-test-writing` skill — RTL state-based tests):

- Idle mode: render with no `text` → 3 dot spans visible (`getAllByTestId('idle-dot')` length 3)；no text element.
- Streaming mode: render with `text="理解問題"` → `screen.getByText('理解問題')` visible；`reasoning-status-dots-cycler` element present；no STOPPED label.
- Frozen mode: render with `text="理解問題" state="frozen"` → text visible with `style.opacity` = `0.65`；`screen.getByText('STOPPED')` visible；no dots cycler animation (cycler hidden).
- Stalled modifier: render `text="..." stalled={true}` → wrapper has class `stalled`；assert via `container.querySelector('.reasoning-status.stalled')`.
- Plain text rendering (D20): render `text="run \`list_sec_sections\` and **bold**"` → exact substring visible (no `<code>` / `<strong>` element rendered).
- Long sentence overflow (D21 visual contract — assert CSS class presence, not actual computed pixel; pixel-level deferred to Playwright S-rsn-04 spec): assert `.reasoning-status-text` element has class containing nowrap rule via class selector (or simpler: assert the class is applied, computed style verified at Playwright stage via `page.evaluate(...)` reading computed style).
- **Anti-patterns to avoid**: no `getByTestId` for content that has accessible name (use `getByText`); no whole-component snapshots; no regex `toHaveAttribute`.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `cd frontend && npm test -- ReasoningIndicator` | All pass | 3 modes + stalled + plain-text |
| Lint | `cd frontend && npm run lint -- src/components/atoms/ReasoningIndicator.tsx` | No errors | code style |
| Build | `cd frontend && npm run build` | No type errors | TS contract |

**Execution Checklist:**

- [ ] 🔴 Write tests for 3 modes + stalled + plain-text + class-presence per checklist; reference `frontend-test-writing` skill
- [ ] 🔴 Run vitest → RED (existing component only renders 3 dots)
- [ ] 🟢 Rewrite component per Approach A; add CSS classes to `index.css`
- [ ] 🟢 Re-run → GREEN
- [ ] 🔵 Refactor: extract dot cycler markup if same JSX repeated；ensure aria-hidden="true" on the wrapper (D22 — hides from screen reader, LiveStatusAnnouncer handles it instead)
- [ ] 🔵 Re-run + visual sanity via `npm run dev` (load chat page, manually trigger via mocked SSE if available)
- [ ] Commit: `git commit -m "feat(frontend): rewrite ReasoningIndicator for 3 modes with Variant A visuals"`

---

### Task 9: Add `resolveReasoningDisplayText` selector for post-tool idle text (D15 §7.4)

**Files:**
- Update: `frontend/src/lib/reasoning-indicator-logic.ts` (add `shouldShowReasoningIndicator` post-tool gap branch + new `resolveReasoningDisplayText` selector)
- Update: `frontend/src/lib/__tests__/reasoning-indicator-logic.test.ts`

**What & Why:** F6 補洞 — reasoning-off + tool-using turn 在 tool 結束到 next text-start 之間 3-7 秒空窗顯示 idle text "Synthesizing"。對應 BDD：S-rsn-07（post-tool idle table-driven 2 cases）.

**Approach Decision — where the idle-text fallback lives:**

| Option | Summary | Status | Why |
| ------ | ------- | ------ | --- |
| A | Pure selector `resolveReasoningDisplayText({reasoningStatusText, status, lastMessage})` co-located with `shouldShowReasoningIndicator` in `reasoning-indicator-logic.ts`; `useReasoningStatus` stays as a pure SSE subscription hook (no `lastMessage` / `status` awareness); `ChatPanel` (or a small derived selector at the render site) calls both | Selected | Keeps `useReasoningStatus` testable in isolation (no stubbing of `lastMessage` shape required); idle-text logic is pure, deterministic, easy to unit-test;  follows existing repo pattern (`shouldShowReasoningIndicator` already lives in `lib/`) |
| B | Push `lastMessage` + `status` into `useReasoningStatus` and have it set `reasoningStatusText = "Synthesizing"` internally | Rejected | Couples a pure SSE-event subscriber to `useChat` state shape; harder to test (every test has to construct a `lastMessage` mock); harms reusability if a non-chat surface ever subscribes to reasoning |

**Implementation Notes:**
- `shouldShowReasoningIndicator` 接受新參 `reasoningStatusText: string | null`；保留既有 lastMessage / status 入參。`reasoningStatusText` truthy → 永遠 true；其他既有條件保留；新增 post-tool gap branch（last part 是 completed tool + status streaming）.
- `resolveReasoningDisplayText` is a new pure selector returning `string | null`：
  - If `reasoningStatusText` truthy → return it (real reasoning takes precedence over idle text).
  - Else if status is `"streaming"` AND last part is a completed tool → return `IDLE_SYNTHESIZING_TEXT` constant (`"Synthesizing"`).
  - Else if `parts.length === 0` AND status streaming → return null (let caller render 3-dot idle via `<ReasoningIndicator text={null} />`).
  - Else → return null (no idle text).
- D15 6-反問題 MVP simplification: 永遠用 `"Synthesizing"`，不做 `"Thinking"` heuristic 區分；定義 `IDLE_SYNTHESIZING_TEXT` 跟 `IDLE_THINKING_TEXT` 兩個 exported 常數（"Thinking" 暫不使用，標 `// reserved for future heuristic per D15`），保留 future iterate 空間。
- `useReasoningStatus` (Task 7) stays unchanged — no new responsibilities added here.
- `ChatPanel` (Task 11) wires it: `const displayText = resolveReasoningDisplayText({ reasoningStatusText, status, lastMessage }); ... <ReasoningIndicator text={displayText} state={...} />`.

**Critical Contract:**

```typescript
// reasoning-indicator-logic.ts
export const IDLE_SYNTHESIZING_TEXT = "Synthesizing";
export const IDLE_THINKING_TEXT = "Thinking";  // reserved for future heuristic per D15

export function shouldShowReasoningIndicator(args: {
  status: ChatStatus;
  lastMessage: Pick<UIMessage, "role" | "parts"> | null;
  reasoningStatusText: string | null;  // NEW
}): boolean {
  const { status, lastMessage, reasoningStatusText } = args;
  if (status === "ready" || status === "error") return false;
  if (!lastMessage || lastMessage.role !== "assistant") return true;
  if (reasoningStatusText) return true;
  if (lastMessage.parts.length === 0) return true;
  // Post-tool idle gap (D15 §7.4 / S-rsn-07)
  const lastPart = lastMessage.parts.at(-1);
  if (lastPart && isCompletedToolPart(lastPart) && status === "streaming") {
    return true;
  }
  return false;
}

export function resolveReasoningDisplayText(args: {
  reasoningStatusText: string | null;
  status: ChatStatus;
  lastMessage: Pick<UIMessage, "role" | "parts"> | null;
}): string | null {
  const { reasoningStatusText, status, lastMessage } = args;
  if (reasoningStatusText) return reasoningStatusText;
  if (status !== "streaming") return null;
  if (!lastMessage || lastMessage.role !== "assistant") return null;
  const lastPart = lastMessage.parts.at(-1);
  if (lastPart && isCompletedToolPart(lastPart)) return IDLE_SYNTHESIZING_TEXT;
  return null;
}

function isCompletedToolPart(part: { type?: unknown; state?: unknown }): boolean {
  // mirror the existing `isRunningToolState` inverse — completed states are
  // anything that isn't currently running and is a tool-shaped part
  if (typeof part.type !== "string" || (!part.type.startsWith("tool-") && part.type !== "dynamic-tool")) return false;
  return !isRunningToolState(part.state as string);
}
```

**Test Strategy:**
- Existing tests still pass after `shouldShowReasoningIndicator` signature change (3rd param required, update existing test fixtures to pass `null`).
- `shouldShowReasoningIndicator` new tests:
  - `reasoningStatusText="text"` overrides everything → true even when `parts.length>0` and last part is text.
  - `parts.length===0` returns true.
  - Last part is completed tool + status streaming + `reasoningStatusText` null → true (post-tool gap).
  - Last part is completed tool + status ready → false (existing rule).
  - Last part is text → false.
- `resolveReasoningDisplayText` new tests:
  - `reasoningStatusText="thinking..."` → returns `"thinking..."` (passthrough).
  - `reasoningStatusText=null + status=streaming + last part completed tool` → returns `"Synthesizing"`.
  - `reasoningStatusText=null + status=streaming + last part is text` → returns `null` (post-text gap, no idle).
  - `reasoningStatusText=null + status=ready` → returns `null`.
  - `reasoningStatusText=null + parts.length=0` → returns `null` (caller renders 3-dot idle).
  - Constants exported are exactly `"Synthesizing"` / `"Thinking"` (English per D16).

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `cd frontend && npm test -- reasoning-indicator-logic` | All pass (existing + 11 new tests across `shouldShowReasoningIndicator` + `resolveReasoningDisplayText`) | pure selector contract |

**Execution Checklist:**

- [ ] 🔴 Update existing `shouldShowReasoningIndicator` tests to pass new `reasoningStatusText` param (likely as `null`); write 5 new branch tests for it; write 6 tests for `resolveReasoningDisplayText`
- [ ] 🔴 Run vitest → RED
- [ ] 🟢 Update `shouldShowReasoningIndicator` signature + post-tool gap branch; add `resolveReasoningDisplayText` + `IDLE_SYNTHESIZING_TEXT` / `IDLE_THINKING_TEXT` constants + private `isCompletedToolPart` helper
- [ ] 🟢 Re-run → GREEN
- [ ] 🔵 Refactor: ensure `isRunningToolState` import path matches existing usage in `models.ts`; no duplication of tool-state classification logic
- [ ] 🔵 Re-run targeted
- [ ] Commit: `git commit -m "feat(frontend): add resolveReasoningDisplayText for post-tool idle text (D15)"`

---

### Task 10: `LiveStatusAnnouncer` ARIA hybrid + `aria-hidden` on visual components (D22)

**Files:**
- Create: `frontend/src/components/atoms/LiveStatusAnnouncer.tsx`
- Create: `frontend/src/components/atoms/__tests__/LiveStatusAnnouncer.test.tsx`
- Update: `frontend/src/components/organisms/ToolCard.tsx` (add aria-hidden="true")
- Update: `frontend/src/components/organisms/ErrorBlock.tsx` (ensure role="alert")
- Update: `frontend/src/index.css` (add `.sr-only` standard pattern if missing)

**What & Why:** ARIA hybrid pattern — high-level status announce 給 screen reader，個別視覺元件對 a11y 透明。對應 BDD：S-rsn-14（screen reader transition-level status，無逐句 reasoning）。Manual portion (real VoiceOver test) 不在 plan scope.

**Implementation Notes:**
- `LiveStatusAnnouncer` props: `{ status: ChatStatus, lastEvent: { type: string, toolName?: string, errorText?: string } | null }`.
- Render: `<div role="status" aria-live="polite" className="sr-only">{currentStatusText}</div>`.
- Transition→string mapping (D22, all English D16):
  - `lastEvent.type === 'start'` → "Generating response"
  - `lastEvent.type === 'tool-input-available'` → `Calling ${lastEvent.toolName}`
  - `lastEvent.type === 'tool-output-available'` → `Tool ${lastEvent.toolName} completed`
  - `lastEvent.type === 'tool-output-error'` → `Tool ${lastEvent.toolName} failed`
  - `lastEvent.type === 'finish'` → "Response complete"
  - `status === 'error'` → `Error: ${lastEvent.errorText ?? "stream interrupted"}`
- 不 announce: reasoning text events, idle text, text-start, text-delta（screen reader 自然讀 message body）.
- ChatPanel 必須把 SSE last event 傳進 announcer — 加一個 `lastSSEEventRef` 在 onData 內 set.

**Critical Contract:**

```typescript
interface LiveStatusAnnouncerProps {
  status: ChatStatus;
  lastEvent: AnnouncedEvent | null;
}

interface AnnouncedEvent {
  type: 'start' | 'tool-input-available' | 'tool-output-available'
      | 'tool-output-error' | 'finish';
  toolName?: string;
  errorText?: string;
}

// Component renders:
// <div role="status" aria-live="polite" className="sr-only">{text}</div>
```

**Test Strategy:**
- 6 transition tests: each event type → asserted text via `getByRole('status')` text content.
- Reasoning events not announced: pass `{type:'data-reasoning-status', text:'内部思考'}` → announcer text **not** changed (defensive, since component shouldn't receive them — but assert silent if it does).
- Error status overrides last event mapping.
- DOM structure: assert `role="status"` + `aria-live="polite"` + `.sr-only` class present.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `cd frontend && npm test -- LiveStatusAnnouncer` | All pass | transition mapping + ARIA structure |
| ARIA | `cd frontend && npm run lint` | No `jsx-a11y` warnings around new file | code style |

**Execution Checklist:**

- [ ] 🔴 Write 6+ transition + structure tests
- [ ] 🔴 Run vitest → RED
- [ ] 🟢 Implement component + add `.sr-only` CSS + add `aria-hidden="true"` to ToolCard wrapper + ensure ErrorBlock has `role="alert"`
- [ ] 🟢 Re-run → GREEN
- [ ] 🔵 Refactor: extract transition→string map as exported constant for testability
- [ ] 🔵 Re-run targeted
- [ ] Commit: `git commit -m "feat(frontend): add LiveStatusAnnouncer ARIA hybrid + aria-hidden on visual components (D22)"`

---

### Task 11: Wire frontend integration in `ChatPanel` + `AssistantMessage` filter (D39.b)

**Files:**
- Update: `frontend/src/components/pages/ChatPanel.tsx`
- Update: `frontend/src/components/organisms/AssistantMessage.tsx`
- Create: `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` (if missing)
- Update: `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx`

**What & Why:** Compose all frontend pieces — wire `useReasoningStatus` to `useChat({ onData })`；render `<ReasoningIndicator>` based on `shouldShowReasoningIndicator` + reasoning text；render `<LiveStatusAnnouncer>` with last-event ref；call `clearReasoningStatus()` on stop / clear；call `resetForNewTurn()` on send。Add D39.b filter to `AssistantMessage`. 對應 BDD：S-stream-04 frontend pre-SSE error path (already wired via existing onError)、S-rsn-01 lifecycle, S-rsn-08 (abort sub-states), S-rsn-13 (abort then resend coexist), S-chan-01/02/03 (data-reasoning-* never persisted).

**Implementation Notes:**
- ChatPanel:
  - Add `const { reasoningStatusText, handleData: handleReasoningData, clearReasoningStatus, resetForNewTurn } = useReasoningStatus();`
  - Compose two `onData` callbacks: `(part) => { handleData(part); handleReasoningData(part); setLastSSEEvent(part); }` (or merge).
  - In `handleSend`: call `resetForNewTurn()` 在 sendMessage 之前.
  - In `handleStop`: call `clearReasoningStatus()` 同 stop().
  - In `handleClearSession`: call `clearReasoningStatus()`.
  - Compute `displayText = resolveReasoningDisplayText({ reasoningStatusText, status, lastMessage })` (Task 9 selector); pass `displayText` and `shouldShow = shouldShowReasoningIndicator({ ... })` to MessageList → render `<ReasoningIndicator text={displayText} state={status === 'error' ? 'frozen' : 'streaming'} />` at chat-area child position when `shouldShow` true.
- `AssistantMessage` filter (D39.b):
  ```typescript
  const filteredParts = message.parts.filter(
    (part) => typeof part.type !== 'string' || !part.type.startsWith('data-reasoning-')
  );
  // use filteredParts in subsequent .map loops
  ```

**Test Strategy:**

`AssistantMessage.test.tsx` (D39.b filter):
- message with `parts = [{type:'text',text:'hello'}, {type:'data-reasoning-status', data:{text:'should hide'}}]` → rendered transcript contains `'hello'` but **not** `'should hide'`.
- This guarantees defense-in-depth even if backend `transient: true` flag broken.

`ChatPanel.integration.test.tsx` (extend existing):
- Mock SSE stream including `data-reasoning-status` event → assert `<ReasoningIndicator>` shows text mid-stream (state-based, not snapshot).
- After `text-start` event → reasoning indicator hidden.
- Click stop button → `clearReasoningStatus` called (assert text gone).
- Send new message → `resetForNewTurn` called (assert hooks resettable).
- **S-rsn-13 abort-then-resend coexistence**: send first message, wait for assistant reasoning (mock SSE), click stop → assistant bubble freezes with STOPPED label visible. Immediately send second message → both assistant bubbles present in `screen.getAllByTestId('assistant-message')` (length 2); first bubble retains STOPPED label visible; second bubble shows new streaming reasoning text. Confirms D32 message-list multi-bubble persistence.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `cd frontend && npm test -- ChatPanel AssistantMessage` | All pass | integration |
| Build | `cd frontend && npm run build` | No type/build errors | TS surface intact |

**Execution Checklist:**

- [ ] 🔴 Write D39.b filter test + ChatPanel SSE wiring tests; reference `frontend-test-writing` skill
- [ ] 🔴 Run vitest → RED
- [ ] 🟢 Wire useReasoningStatus into ChatPanel; add filter to AssistantMessage; add lastSSEEvent ref + LiveStatusAnnouncer
- [ ] 🟢 Re-run → GREEN
- [ ] 🔵 Refactor: extract `useChat` onData composition if it gets long
- [ ] 🔵 Re-run + manual visual sanity via `npm run dev`
- [ ] Commit: `git commit -m "feat(frontend): wire useReasoningStatus + LiveStatusAnnouncer + AssistantMessage data-reasoning-* filter"`

---

### Flow Verification: Frontend reasoning UX with mocked SSE (Tasks 7–11)

> Validates frontend reasoning indicator + state machine + persistence boundary
> using MSW or direct SSE mock (per memory `feedback_msw_vs_real_backend.md` —
> MSW for error/edge cases only; real backend for happy path).

| #   | Method                | Step                                                                                                                                                                                                              | Expected Result                                                                                                          |
| --- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1   | Vitest                | `cd frontend && npm test`                                                                                                                                                                                         | All unit + integration tests pass                                                                                        |
| 2   | TypeScript            | `cd frontend && npm run build`                                                                                                                                                                                     | No type or bundle errors                                                                                                  |
| 3   | Browser (manual dev)  | Start backend (`uv run uvicorn backend.api.main:app`) + frontend (`cd frontend && npm run dev`); open chat; send `$PROMPT`                                                                                       | Reasoning text 出現 / 消失 / 切換 視覺平順；State 1 (3-dot) → State 2 (text+cycler) → State 7 (text streaming) → State 8 (done) |
| 4   | Browser DOM check     | DevTools console: `document.querySelectorAll('[data-testid="assistant-message"]').forEach(el => console.log(el.textContent))` after stream complete                                                                | Output 不含原 reasoning text（reasoning ephemeral，per F5 / D2）                                                       |

- [ ] All flow verifications pass

---

### Task 12: Stalled modifier polling (D14) + reasoning indicator placement in MessageList

**Files:**
- Update: `frontend/src/hooks/useReasoningStatus.ts` (add stalled detection)
- Update: `frontend/src/components/templates/MessageList.tsx` (or wherever reasoning indicator renders inline)
- Update: `frontend/src/hooks/__tests__/useReasoningStatus.test.ts` (stalled tests)

**What & Why:** D14 long-silence stalled modifier — 10s 無新 chunk 時切 stalled visual. 對應 BDD：S-rsn-06 (stalled visual after 10s).

**Implementation Notes:**
- `useReasoningStatus` 加 `lastUpdateAtRef = useRef<number>(0)` + `stalled: boolean` state.
- `setInterval(checkStalled, 1000)` 在 `useEffect` 每秒比較 `Date.now() - lastUpdateAtRef.current > 10_000` → set stalled true.
- 接 `data-reasoning-status` 時 update `lastUpdateAtRef.current = Date.now()`、stalled false.
- Cleanup interval on unmount.
- 在 MessageList / ChatPanel 把 `stalled` prop 傳給 `<ReasoningIndicator stalled={stalled} ... />`.

**Test Strategy** (per `frontend-test-writing` — RTL with `vi.useFakeTimers`):
- `vi.useFakeTimers(); vi.setSystemTime(...)`. Render hook. Call `handleData(...)`. Advance 9s → `stalled === false`. Advance 2 more → `stalled === true`. Trigger another `handleData` → `stalled === false`.
- Cleanup: unmount unmounts interval (no leaks via `vi.getTimerCount()`).

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `cd frontend && npm test -- useReasoningStatus` | All pass | stalled timing correct |

**Execution Checklist:**

- [ ] 🔴 Write 3 stalled tests with fake timers
- [ ] 🔴 Run vitest → RED
- [ ] 🟢 Implement stalled detection + wire to indicator
- [ ] 🟢 Re-run → GREEN
- [ ] 🔵 Refactor: ensure no setInterval leak (return cleanup); extract STALLED_THRESHOLD_MS const
- [ ] 🔵 Re-run targeted
- [ ] Commit: `git commit -m "feat(frontend): stalled modifier when reasoning silent ≥10s (D14)"`

---

### Task 13: 已移出 scope（編號保留 gap 避免 Task 14/15/16 cross-reference 大改）

> 原本 Task 13 規劃 backend SSE keepalive + 30s first-chunk timeout（對應 D14 / D23 backend portion）。**本期移出 scope**，理由：current main `backend/api/routers/chat.py`（131 行）完全沒有 timeout / keepalive，這次 PR focus 在 reasoning streaming 本身，不變更既有 streaming infra。
>
> 連帶影響：
> - `backend/api/routers/chat.py` 不修改
> - `backend/tests/api/test_chat_sse_keepalive.py` / `backend/tests/agents/test_orchestrator_provider_hung_timeout.py` 不新增
> - S-stream-04 verification 縮回 pre-SSE-open + mid-stream 兩個 sub-cases（hung sub-case 拿掉，行為等同 main：user 必須手動 Stop）
> - S-stream-06 整個 scenario 移出本期 scope，等 backend keepalive 另立 PR 再驗
> - D14 long-silence UX 由 Task 12（frontend stalled modifier）獨立提供視覺訊號，不依賴 backend keepalive
> - D23 三路分流退回兩路（pre-SSE-open / mid-stream），hung case 留作後續 PR

---

### Task 14: 6-case matrix Playwright spec + Langfuse trace verifier CLI

**Files:**
- Create: `frontend/tests/e2e/critical/multi-provider-matrix.spec.ts` (P0 guardrail，`@critical` tag — 對應 J-stream-01 ship gate)
- Create: `frontend/tests/e2e/critical/fixtures/agent-capability/` (6 yaml fragments per matrix row — 跟 spec 同 colocated 的 fixture)
- Create: `backend/scripts/validation/verify_langfuse_trace.py` (operator CLI helper；同 folder 既有 `validate_*.py` 慣例)
- Update: `frontend/playwright.config.ts` (確保 video record `use.video: 'on'` for matrix spec)

**What & Why:** Operational glue for BDD E2E. 對應 BDD：J-stream-01 (6-case matrix video), J-trace-01 (trace tree alignment), J-rsn-01/02 (lifecycle + abort journey), J-chan-01 (channel isolation lifecycle), S-cross-01 (POC ship gate).

**Implementation Notes:**
- `multi-provider-matrix.spec.ts` is the only commit artifact for matrix execution — no shell wrapper script. Operator runs it via `cd frontend && npx playwright test tests/e2e/critical/multi-provider-matrix.spec.ts --grep @critical`. Spec internally iterates 6 rows, switches the agent capability fixture per row (via test parameter or fixture loader), records video per row, and emits Langfuse `trace_id` to stdout for the verifier step.
- `frontend/tests/e2e/critical/fixtures/agent-capability/`: 6 yaml fragments overriding `model.name` + `reasoning` + `thinking_budget` for each row. The spec loads the right fragment per parameterized case.
- `backend/scripts/validation/verify_langfuse_trace.py`:
  - Args: `trace_id`, `--expect-reasoning-on / --expect-reasoning-off / --expect-unsupported`, `--expect-aborted` (S-trace-06).
  - Polls Langfuse `/api/public/traces/{id}` 5×1s with backoff (per memory `feedback_tracing_verification.md`).
  - Asserts:
    - agent.run parent exists；each chat_model child has `metadata.reasoning` per expected schema (D29).
    - When `--expect-aborted` is set: root span's `metadata.status == "aborted"` (D35); the in-flight (last) chat_model child has `metadata.reasoning_tail_aborted` non-empty (the segmenter tail written by `_handle_abort_cleanup`); fallback acceptable if segmenter buffer was empty at abort (no reasoning content during the cancelled call).
  - Outputs JSON summary to stdout for shell capture.
- Playwright spec uses `request` API + page navigation per design §9 — record video via `playwright.config.ts` `use.video: 'on'`.

**Test Strategy:**
- The verifier CLI is operationally important; cover its arg parsing + Langfuse JSON parsing in `backend/tests/scripts/test_verify_langfuse_trace.py` (mock-based, no live Langfuse).
- The Playwright spec itself is the verification — running it end-to-end exercises J-stream-01 (Flow Verification below).

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted (verifier) | `uv run pytest backend/tests/scripts/test_verify_langfuse_trace.py -v` (mock-based) | Parsing logic passes | helper correctness |
| Smoke (matrix spec) | `cd frontend && npx playwright test tests/e2e/critical/multi-provider-matrix.spec.ts --list` | All 6 parameterized cases listed | spec shape sound |

**Execution Checklist:**

- [ ] 🟢 Write `verify_langfuse_trace.py` + minimal unit tests
- [ ] 🟢 Create 6 yaml fragments under `fixtures/agent-capability/` + Playwright spec
- [ ] 🔵 Refactor: extract reusable Langfuse polling helper if it's needed elsewhere in `backend/scripts/`
- [ ] Commit: `git commit -m "test(bdd): 6-case matrix Playwright spec + Langfuse trace verifier CLI"`

---

### Task 15: Backend dev-only feature flags + Playwright specs for visual lifecycle scenarios

**Files:**
- Update: `backend/agent_engine/streaming/event_mapper.py` (gate on `STUB_REASONING_ONLY`, `STUB_CONTENT_BLOCKS_NO_REASONING`, `EMIT_LATE_REASONING`, `EMIT_DELAYED_REASONING`)
- Update: `backend/agent_engine/streaming/sse_serializer.py` (gate on `FORCE_REASONING_NON_TRANSIENT`)
- Update: `backend/agent_engine/agents/base.py` or `orchestrator.py` (gate on `FORCE_LLM_FAIL`)
- Create: `frontend/tests/e2e/lifecycle/reasoning-indicator-states.spec.ts` (covers S-rsn-01 / S-rsn-02 / S-rsn-03 / S-rsn-04 / S-rsn-08 — 視覺 state 序列、CSS 屬性 assertion、video record)
- Create: `frontend/tests/e2e/lifecycle/reasoning-stalled.spec.ts` (S-rsn-06 — `EMIT_DELAYED_REASONING` stub + 11s wait + class assertion)
- Create: `frontend/tests/e2e/lifecycle/reasoning-late-events.spec.ts` (S-rsn-12 — `EMIT_LATE_REASONING=1` 注入 + finishedRef guard 驗證)
- Create: `frontend/tests/e2e/lifecycle/reasoning-channel-isolation.spec.ts` (J-chan-01 + S-chan-01 / S-chan-02 / S-chan-03 — 4 階段 mid-stream / post-finish / reload / new turn DOM polling，含 `FORCE_REASONING_NON_TRANSIENT=1` 注入)
- Create: `frontend/tests/e2e/journeys/abort-then-resend.spec.ts` (J-rsn-02 + S-rsn-13 — abort 中段然後 resend，video record 全程)
- Create: `frontend/tests/e2e/lifecycle/trace-tail-stream-only.spec.ts` (S-trace-05 — `STUB_REASONING_ONLY=1` 注入 + verifier 驗證 metadata.reasoning 含尾段)
- Create: `frontend/tests/e2e/lifecycle/trace-no-reasoning-blocks.spec.ts` (S-trace-09 — `STUB_CONTENT_BLOCKS_NO_REASONING=gemini` 注入 + 確認 stream 仍完整)
- Update: `frontend/playwright.config.ts` (確保 `use.video: 'on'` 對 lifecycle / journeys 路徑生效；可分 project 或共用設定)

**What & Why:** Visual lifecycle BDD scenarios (S-rsn-* / S-chan-03 / S-trace-05 / S-trace-09 / J-rsn-02 / J-chan-01) 改用 **Playwright tests + video recording** — repeatable CI guardrail，不再用 inline `browser-use`（per memory `feedback_msw_vs_real_backend.md` + 用戶 directive：browser-use 是給 agent 一次性探索才用的，repeatable 驗證走 Playwright）。本 task 同時 ship：(1) 6 個 backend dev-only env-flag handler 給 Playwright spec 拿來注入 stub，不需 real LLM 也能跑出視覺；(2) 對應的 Playwright spec 檔案。

**Implementation Notes:**
- Dev-only feature flags consumed from `os.environ` in backend:
  - `FORCE_LLM_FAIL=1` — backend stub raise on first LLM call (S-stream-04 mid-stream row)
  - `FORCE_REASONING_NON_TRANSIENT=1` — SSE serializer omits `transient: true` (S-chan-03)
  - `EMIT_DELAYED_REASONING=1` — backend emits first reasoning chunk then forces ≥12s silence before next (S-rsn-06 stalled visual)
  - `EMIT_LATE_REASONING=1` — backend emits a `data-reasoning-status` 100ms after `finish` (S-rsn-12)
  - `STUB_REASONING_ONLY=1` — backend emits reasoning blocks then immediately finishes, no text/tool (S-trace-05)
  - `STUB_CONTENT_BLOCKS_NO_REASONING=<provider>` — simulates content_blocks normalizer failure (S-trace-09)
  - (`STUB_LLM_HANG` 已隨 Task 13 移出 scope，不再實作)
- Implement these flags behind clear `if os.environ.get("...")` guards. Add `# DEV-ONLY: ...` comment + `# noqa` if needed.
- Playwright specs 透過 `page.goto` / `page.waitForSelector` / `page.screenshot` / `page.evaluate` 驗證 DOM、computed styles、class presence。Backend 需要 stub 行為時，由 spec 內 `process.env.X = '1'` 設定後 spawn 一個 isolated backend instance（或在 playwright global setup 階段用 fixture 控制）；具體實現視 backend startup 機制決定。
- Video output 經 `playwright.config.ts` `use.video: 'on'` 自動產出到 `frontend/test-results/`，PR Reviewer 直接看 video 驗收。

**Test Strategy:**
- Backend flag handlers 由 existing `test_event_mapper.py` / `test_sse_serializer.py` / `test_orchestrator_streaming.py` 加 `monkeypatch.setenv` 的 unit case 覆蓋。
- Playwright specs 本身就是 test layer — 跑通 = 驗證通過。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Backend flag handlers | `uv run pytest backend/tests/streaming/ backend/tests/agents/ -v -k "dev_flag or stub or force"` | All flag-guarded paths covered | flag handlers correct |
| Playwright specs (smoke) | `cd frontend && npx playwright test tests/e2e/lifecycle/ tests/e2e/journeys/abort-then-resend.spec.ts --list` | 所有新 spec 列出 | spec shapes sound |
| Playwright specs (run) | `cd frontend && npx playwright test tests/e2e/lifecycle/ tests/e2e/journeys/abort-then-resend.spec.ts` | All pass + video files at `frontend/test-results/` | actual visual verification |

**Execution Checklist:**

- [ ] 🟢 Add 6 dev-only env-flag handlers in backend
- [ ] 🟢 Add unit-test cases per flag
- [ ] 🔴 Write Playwright specs for S-rsn-* / S-chan-* / S-trace-05 / S-trace-09 / J-rsn-02 / J-chan-01 — RED first（spec runs but DOM doesn't yet match expected states）
- [ ] 🟢 Make specs pass — adjust frontend code if any visual gaps revealed; ensure `use.video: 'on'` outputs proper video files
- [ ] 🔵 Refactor: 抽 shared fixture (e.g. `setupBackendStubFlag(page, flag)`) if 重複 setup 邏輯出現
- [ ] Commit: `git commit -m "test(e2e): Playwright specs + dev-only feature flags for visual reasoning lifecycle"`

---

### Flow Verification: 6-case acceptance matrix (E2E ship gate, per design §9)

> J-stream-01 — the hard ship gate. All 6 rows must pass before merging.
> Reviewer reviews 6 video recordings.

| #   | Method                          | Step                                                                                                                                                                                                                                                                                          | Expected Result                                                                                                                                       |
| --- | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Acceptance matrix Playwright spec | `cd frontend && npx playwright test tests/e2e/critical/multi-provider-matrix.spec.ts --grep @critical`                                                                                                                                                                                       | All 6 rows complete; per-row `pass/fail` from Playwright test result; 6 video files in `frontend/test-results/`                                       |
| 2   | Per-row trace verification      | For each row: `uv run python backend/scripts/validation/verify_langfuse_trace.py $TRACE_ID --expect-reasoning-{on/off}` (trace_id emitted by spec)                                                                                                                                            | reasoning-on rows: ≥1 `data-reasoning-status` in SSE log + chat_model spans `metadata.reasoning` non-empty;<br/>reasoning-off rows: 0 events + `""` |
| 3   | Console / network               | Open each video file, look for browser console errors / failed network requests across the streaming                                                                                                                                                                                          | Zero unexpected errors                                                                                                                                |
| 4   | Reviewer manual review          | Reviewer watches 6 videos start-to-end                                                                                                                                                                                                                                                          | Reasoning UX feels polished per design §7; no jarring jumps; STOPPED / Synthesizing / stalled visuals match mockup                                    |

- [ ] All 6 rows pass — ship gate cleared

---

### Flow Verification: Visual lifecycle + isolation BDD scenarios (Tasks 12 + 15)

> Cover S-rsn-01 to S-rsn-14, S-chan-01 to S-chan-04, S-stream-04/06/07/09,
> S-trace-05/06/07/08/09, J-rsn-01/02, J-chan-01, J-trace-01.

| #   | Method                         | Step                                                                                                                                                                                                                                                                                                                                                                                                       | Expected Result                                                                                                                                                                                                  |
| --- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Playwright lifecycle / journey specs | `cd frontend && npx playwright test tests/e2e/lifecycle/ tests/e2e/journeys/abort-then-resend.spec.ts tests/e2e/lifecycle/reasoning-channel-isolation.spec.ts` (with backend started under appropriate dev flag env, e.g. `FORCE_REASONING_NON_TRANSIENT=1 uvicorn ...` for S-chan-03)                                                                                                                                                                                                                          | All specs pass; video files at `frontend/test-results/` (one per spec)；visual matches mockup `mockups/reasoning_status_states.html`                                                          |
| 2   | Backend trace inspection       | For each S-trace-* scenario, after the inline run, `uv run python backend/scripts/validation/verify_langfuse_trace.py $TRACE_ID --schema-check`                                                                                                                                                                                                                                                              | All assertions pass per scenario expectation in verification-plan.md                                                                                                                                              |
| 3   | Production-like keepalive test | ~~Deploy backend behind nginx... S-stream-06 ...~~ — **移出本期 scope**（Task 13 backend keepalive 沒做，無 keepalive 可驗）                                                                                                                                                                                                                                                                                  | N/A — 本期略過                                                                                                                                                                                                    |

- [ ] All BDD scenarios pass

---

### Task 16: Pre-delivery cleanup + documentation polish

**Files:**
- Update: `backend/agent_engine/streaming/README.md`
- Update: `frontend/src/components/atoms/README.md` (mention LiveStatusAnnouncer)
- Update: `artifacts/current/design.md` — only if behavior diverged from design during implementation (else leave as-is)
- Update: `backend/agent_engine/CLAUDE.md` — add note on reasoning callback if needed

**What & Why:** Make sure the README files in the touched packages mention the new components for future maintainers (single-source-of-truth principle).

**Implementation Notes:**
- Keep README updates minimal: short paragraph + file path reference.
- No new docs (per CLAUDE.md commenting rules).

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Lint | `uv run ruff check backend/ && cd frontend && npm run lint && npm run format:check` | All pass | code style baseline before final review |
| Type | `uv run pyright backend/agent_engine/streaming/ && cd frontend && npx tsc --noEmit` | All pass | type contract |

**Execution Checklist:**

- [ ] 🟢 Update READMEs
- [ ] 🔵 Final lint + type pass
- [ ] Commit: `git commit -m "docs: update streaming + atoms READMEs for reasoning components"`

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] Targeted verification for each task (1-16) passes
- [ ] `uv run pytest backend/tests/ -v -m "not integration and not eval and not sec_integration"` — all backend non-external tests pass
- [ ] `cd frontend && npm test` — all frontend unit + integration tests pass
- [ ] `uv run ruff check backend/` — backend lint passes
- [ ] `cd frontend && npm run lint` — frontend lint passes
- [ ] `cd frontend && npm run format:check` — frontend format passes
- [ ] `uv run pyright backend/agent_engine/streaming/ backend/agent_engine/agents/` — backend type check on touched packages passes
- [ ] `cd frontend && npm run build` — frontend build (tsc -b + vite build) passes

### Flow Level (Behavioral)

- [ ] Flow: Backend reasoning emit + persist (Tasks 1–4) — PASS / FAIL
- [ ] Flow: Backend end-to-end with real Gemini (Tasks 1–6, R5 POC ship gate) — PASS / FAIL
- [ ] Flow: Frontend reasoning UX with mocked SSE (Tasks 7–11) — PASS / FAIL
- [ ] Flow: 6-case acceptance matrix (J-stream-01 ship gate) — PASS / FAIL
- [ ] Flow: Visual lifecycle + isolation BDD scenarios (Tasks 12 + 15) — PASS / FAIL

### Summary

- [ ] Both levels pass → ready for delivery
- [ ] Any failure is documented with cause and next action in `artifacts/current/code-review-loop/` if entering review loop

---

## BDD ↔ Implementation Cross-Reference

> Map of every scenario in `bdd-scenarios.md` to the task or flow that exercises it.
> Used by `bdd-e2e-loop` skill after coding completes.

| BDD ID | Source | Covered by |
| ------ | ------ | ---------- |
| S-stream-01 | scenarios | Task 5 + Backend E2E flow (real Gemini) #1-2 |
| S-stream-02 | scenarios | Task 5 — agent-version switch test + flow #1 |
| S-stream-03 | scenarios | Task 14 — 6-case matrix Playwright spec + ship gate flow |
| S-stream-04 | scenarios | Task 15 dev flag `FORCE_LLM_FAIL` driving Playwright spec (pre-SSE-open + mid-stream sub-cases only — hung sub-case 隨 Task 13 移出本期 scope) |
| S-stream-05 | scenarios | Task 6 — `test_orchestrator_invoke_reasoning_path.py` |
| S-stream-06 | scenarios | **移出本期 scope** (Task 13 backend keepalive 未實作；scenario 留待 backend keepalive 另立 PR 再驗) |
| S-stream-07 | scenarios | Task 6 — D33 per-request mapper test + Playwright spec with concurrent context (`frontend/tests/e2e/lifecycle/multi-tab-concurrent.spec.ts` planned) |
| S-stream-08 | scenarios | Task 6 — abort cleanup test + Playwright spec |
| S-stream-09 | scenarios | Task 2 (segmenter unit) + Task 3 (mapper integration) + Playwright spec |
| S-chan-01 | scenarios | Task 1 (transient flag asserted) + Task 11 (filter test) + Playwright spec |
| S-chan-02 | scenarios | Task 11 (filter applied to rehydrated parts) + Playwright spec |
| S-chan-03 | scenarios | Task 11 (D39.b filter) + Task 15 dev flag `FORCE_REASONING_NON_TRANSIENT` driving Playwright spec |
| S-chan-04 | scenarios | Task 1 (assert helper test) |
| S-rsn-01 | scenarios | Task 8 (3 modes) + Playwright spec (10-state visual sequence) |
| S-rsn-02 | scenarios | Task 8 (vertical-slot CSS) + Playwright spec |
| S-rsn-03 | scenarios | Task 8 (plain-text test) + Playwright spec |
| S-rsn-04 | scenarios | Task 8 (overflow CSS class test) + Playwright spec |
| S-rsn-05 | scenarios | Task 3 (Anthropic interleave integration test) + Playwright spec |
| S-rsn-06 | scenarios | Task 12 (stalled fake-timer test) + Playwright spec |
| S-rsn-07 | scenarios | Task 9 (post-tool idle gap) + Playwright spec |
| S-rsn-08 | scenarios | Task 8 (frozen mode + 9a STOPPED) + Task 11 (9b 9c interactions) + Playwright spec |
| S-rsn-09 | scenarios | Task 11 (existing ErrorBlock + ephemeral hide) + Playwright spec |
| S-rsn-10 | scenarios | Task 3 (hold-and-flush ordering test) + Playwright spec |
| S-rsn-11 | scenarios | Task 7 (clearedRef test) + Playwright spec |
| S-rsn-12 | scenarios | Task 7 (finishedRef test) + Task 15 dev flag `EMIT_LATE_REASONING` driving Playwright spec |
| S-rsn-13 | scenarios | Task 11 (abort-then-resend integration) + Playwright spec |
| S-rsn-14 | scenarios | Task 10 (LiveStatusAnnouncer transition tests) + manual VoiceOver portion (verification-plan Manual section) |
| S-trace-01 | scenarios | Task 4 (per-LLM-call) + Backend E2E flow #2 |
| S-trace-02 | scenarios | Task 4 (5-scenario schema tests) |
| S-trace-03 | scenarios | Operational verification — `uv run python backend/scripts/validation/verify_langfuse_trace.py --schema-check` covers query semantics |
| S-trace-04 | scenarios | Task 6 — Orchestrator does not inject ReasoningTraceCallback for judge path; Braintrust eval CLI bypass test |
| S-trace-05 | scenarios | Task 3 (finalize() test) + Task 6 (mapper.finalize on natural finish) |
| S-trace-06 | scenarios | Task 6 (abort cleanup test — `metadata.status="aborted"` on root + `metadata.reasoning_tail_aborted` on in-flight chat_model span; the `tail` key is intentionally distinct from `metadata.reasoning` so the on-`on_chat_model_end`-completed schema D29 stays unmuddled) + Task 14 verifier `--expect-aborted` flag |
| S-trace-07 | scenarios | Task 4 + Task 3 — divergence acceptable; manual comparison via verification-plan |
| S-trace-08 | scenarios | Task 6 — D33 per-request mapper + contextvars (auto-isolated) |
| S-trace-09 | scenarios | Task 3 (graceful degrade — 0 reasoning emit but stream completes) + Task 9 (idle text fallback) + Task 15 dev flag `STUB_CONTENT_BLOCKS_NO_REASONING` driving Playwright spec |
| S-cross-01 | scenarios | Backend E2E flow #3 (POC ship gate, R5) |
| J-stream-01 | scenarios | Task 14 — 6-case matrix Playwright spec |
| J-chan-01 | scenarios | Playwright spec at `frontend/tests/e2e/lifecycle/reasoning-channel-isolation.spec.ts` with 4-stage DOM polling |
| J-rsn-01 | scenarios | Playwright spec covering S-rsn-01 in `frontend/tests/e2e/lifecycle/reasoning-indicator-states.spec.ts` + Task 8 component-level coverage |
| J-rsn-02 | scenarios | Playwright spec at `frontend/tests/e2e/journeys/abort-then-resend.spec.ts` with video record |
| J-trace-01 | scenarios | Task 14 — `verify_langfuse_trace.py` + Backend E2E flow #2 |

> Demoted scenarios (per `bdd-scenarios.md` 註記) covered as unit tests:
> C1.6 → Task 6; C2.4 → Task 11 filter; C5.2 → Task 4 completed-path always-write-key (mode-aware schema completed portion);
> C6.9 → Task 2 segmenter; CR.7 → Task 3 reasoning_id_counter test.
