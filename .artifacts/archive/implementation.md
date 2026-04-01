# V1 Streaming Chat — Implementation Plan

> Execution contract for AI agents to implement the V1 streaming chat path.

## 1. Header
- **Title**: V1 Streaming Chat Implementation
- **Goal**: Establish a complete end-to-end streaming chat experience using FastAPI (Backend) and Vite + React + AI SDK (Frontend).
- **Architecture Summary**: Additive SSE v1 protocol support in FastAPI; New Vite-based React frontend using Vercel AI SDK `useChat`.
- **Tech Stack**:
    - **Backend**: FastAPI, LangChain (`astream_events`), Pydantic.
    - **Frontend**: Vite, React, TypeScript, AI SDK (v5), Tailwind CSS, shadcn/ui, Vitest, React Testing Library.
- **TL;DR**: 
    - **Deliverables**: Streaming-capable `Orchestrator`, FastAPI SSE endpoint, Vite/React scaffold, `useChat` UI.
    - **Estimated Effort**: 3-4 days (13 tasks).
    - **Critical Path**: T4 (Contracts) -> T5 (Orchestrator Async) -> T6 (Router) -> T8 (UI) -> T12 (E2E).

## 2. Context
- **Original Request**: Create a streaming chat feature with a modern React frontend in a new worktree.
- **Research Findings**: AI SDK v5 requires `x-vercel-ai-ui-message-stream: v1` header and specific JSON payload format. LangChain `astream_events(version="v2")` is the recommended way to capture tool/text deltas.
- **Metis Review Gaps**: Addressed need for LangChain streaming spike (T1) and byte-level protocol verification (T4/T7).

## 3. Work Objectives
- **Core Objective**: Provide a responsive, stable streaming chat interface where users see agent reasoning and text responses in real-time.
- **Definition of Done**:
    - [ ] Backend `/api/v1/chat/stream` emits valid SSE v1 data.
    - [ ] Frontend `useChat` renders deltas without flickering.
    - [ ] Unit tests pass for both Backend and Frontend.
    - [ ] E2E scenario (T12) succeeds with recorded evidence.
- **Must Have**:
    - Text streaming (SSE).
    - AI SDK v5 protocol compliance.
    - Error handling for mid-stream disconnects.
    - TDD for all new logic.
- **Must NOT Have**:
    - Modification of existing sync `/chat` endpoint.
    - Message persistence (V2).
    - Multi-session support (V2).
    - Generative UI components (V2).

## 4. Verification Strategy
- **TDD**:
    - **Backend**: `pytest` using `httpx.AsyncClient` for SSE streaming assertions.
    - **Frontend**: `vitest` + `React Testing Library` for hook state and component rendering.
- **QA**:
    - **Agent-executed scenarios**: Mandatory evidence recording at `.sisyphus/evidence/task-{N}-{scenario}.{ext}`.
    - **Tools**: `curl` for protocol check, `vitest` for unit, `playwright` (optional) for E2E.

## 5. Execution Strategy

### Dependency Matrix & Waves

| Wave | Task | Category | Dependencies | Description |
| :--- | :--- | :--- | :--- | :--- |
| **W1** | **T1** | Deep | - | Streaming feasibility spike (LangChain + SSE) |
| **W1** | **T2** | Quick | - | Frontend Vite+React+TS scaffold + vitest |
| **W1** | **T4** | High | - | Backend SSE protocol serializer contracts |
| **W1** | **T3** | Visual | T2 | Tailwind + shadcn/ui foundation |
| **W1** | **T5** | Deep | T1 | Orchestrator async streaming adapter |
| **W2** | **T6** | Middle | T4, T5 | FastAPI stream router + CORS wiring |
| **W2** | **T7** | Middle | T4, T5, T6 | Backend TDD suite for stream protocol |
| **W2** | **T8** | Visual | T2, T3, T6 | Frontend `useChat` + MVP chat UI |
| **W2** | **T9** | Middle | T2, T8 | Frontend TDD for streaming states |
| **W2** | **T10** | Quick | T2 | Vite proxy + env config hardening |
| **W3** | **T11** | Middle | T6, T8 | Frontend/Backend contract compatibility |
| **W3** | **T12** | Middle | T6-T11 | E2E streaming verification + evidence |
| **W3** | **T13** | Quick | T12 | Documentation/README sync |

---

### Wave 1: Foundation & Scaffolding

#### T1: Streaming feasibility spike
- **What to do**: Create a temporary script `scripts/spike_streaming.py` to verify `Orchestrator.agent.astream_events(version="v2")` outputs text deltas. Verify `StreamingResponse` flushes deltas immediately.
- **Must NOT do**: Do not modify any production code yet.
- **Recommended Agent Profile**: category: deep, skills: [python, langchain]
- **QA Scenario**: 
    - Tool: `python scripts/spike_streaming.py`
    - Steps: Run script with a prompt that triggers long output.
    - Expected Result: Real-time print of tokens to terminal.
    - Evidence: `.sisyphus/evidence/task-1-spike-output.txt`

#### T2: Frontend Scaffold
- **What to do**: Initialize `frontend/` using `npm create vite@latest . -- --template react-ts`. Install `ai`, `@ai-sdk/react`, `vitest`, `@testing-library/react`. Setup `vitest.config.ts`.
- **Must NOT do**: Do not create UI components yet.
- **Recommended Agent Profile**: category: quick, skills: [vite, react, vitest]
- **QA Scenario**:
    - Tool: `npm run test`
    - Steps: Create a dummy `App.test.tsx` and run.
    - Expected Result: Tests pass.
    - Evidence: `.sisyphus/evidence/task-2-vitest-baseline.txt`

#### T3: UI Foundation
- **What to do**: Setup Tailwind CSS. Add shadcn/ui components: `Button`, `Input`, `ScrollArea`. Configure `@/` path alias.
- **Must NOT do**: Do not implement chat logic.
- **Recommended Agent Profile**: category: visual-engineering, skills: [tailwind, shadcn-ui]
- **Parallel**: Blocks T8.

#### T4: SSE Protocol Contracts
- **What to do**: Define `backend/api/routers/models_stream.py` with Pydantic models matching AI SDK UI Message Stream protocol (v1).
- **Must NOT do**: Do not implement the router yet.
- **Recommended Agent Profile**: category: unspecified-high, skills: [pydantic, fastapi]
- **Acceptance Criteria**:
    - [ ] `StreamEvent` model defined.
    - [ ] Serialization helper for `data: {json}\n\n` format.

#### T5: Orchestrator Streaming Adapter
- **What to do**: Add `astream(prompt: str)` method to `Orchestrator` in `backend/agent_engine/agents/base.py`. Use `self.agent.astream_events`.
- **Must NOT do**: Do not break `arun()`.
- **Recommended Agent Profile**: category: deep, skills: [langchain, async-python]
- **References**: `backend/agent_engine/agents/base.py`

---

### Wave 2: Endpoint & Client Implementation

#### T6: FastAPI Stream Router
- **What to do**: Create `backend/api/routers/chat_stream.py`. Implement `POST /api/v1/chat/stream` returning `StreamingResponse`. Add required header `x-vercel-ai-ui-message-stream: v1`.
- **Must NOT do**: Do not modify `chat.py`.
- **Recommended Agent Profile**: category: middle, skills: [fastapi, async-python]
- **References**: `backend/api/main.py` (wiring).

#### T7: Backend TDD Suite
- **What to do**: Add `backend/tests/api/test_chat_stream.py`. Test partial deltas, error handling (401, 500), and protocol headers.
- **Recommended Agent Profile**: category: middle, skills: [pytest, httpx]
- **QA Scenario**:
    - Tool: `pytest backend/tests/api/test_chat_stream.py`
    - Expected Result: All tests green.

#### T8: Frontend useChat + MVP UI
- **What to do**: Implement `frontend/src/components/ChatInterface.tsx` using `useChat`. Point to `/api/v1/chat/stream`. Render messages in `ScrollArea`.
- **Must NOT do**: No complex styling yet.
- **Recommended Agent Profile**: category: visual-engineering, skills: [react, ai-sdk]
- **References**: `frontend/src/App.tsx`

#### T9: Frontend TDD (Streaming States)
- **What to do**: Test `ChatInterface` for `isLoading` state, error display, and message accumulation.
- **Recommended Agent Profile**: category: middle, skills: [vitest, react-testing-library]
- **QA Scenario**:
    - Tool: `vitest`
    - Evidence: `.sisyphus/evidence/task-9-frontend-tests.txt`

#### T10: Environment & Proxy
- **What to do**: Configure `vite.config.ts` proxy `/api` to `http://localhost:8000`. Setup `.env` for frontend.
- **Recommended Agent Profile**: category: quick, skills: [vite, dev-ops]

---

### Wave 2: Endpoint & Client Implementation

#### T11: Contract Compatibility
- **What to do**: Verify that tool-call events in the stream don't crash the frontend (should be ignored by text parser).
- **Recommended Agent Profile**: category: middle, skills: [frontend, debugging]
- **QA Scenario**: Log stream output via browser devtools.

#### T12: E2E Verification
- **What to do**: Run full stack. Ask "Analyze Nvidia stock". Record screen/logs.
- **Recommended Agent Profile**: category: middle, skills: [qa, automation]
- **Evidence**: `.sisyphus/evidence/task-12-e2e-success.mp4` or screenshots.

#### T13: Documentation
- **What to do**: Update `frontend/README.md` and `backend/README.md`. Sync architecture diagrams in `docs/`.
- **Recommended Agent Profile**: category: quick, skills: [documentation, technical-writing]

---

### 6. Final Verification

- **F1: Plan compliance audit**: Verify all DoD items in this plan are met. (Agent: oracle)
- **F2: Code quality review**: Ruff check + ESLint check.
- **F3: Real QA execution**: Test mid-stream network interruption.
- **F4: Scope fidelity check**: Ensure no persistence or v2 features were accidentally added.

## 7. Commit Strategy
- **Group A (Foundation)**: T2, T3, T4 (Scaffolds and models)
- **Group B (Backend Stream)**: T1, T5, T6, T7 (Orchestrator and Router)
- **Group C (Frontend Integration)**: T8, T9, T10 (UI and Tests)
- **Group D (Stabilization)**: T11, T12, T13 (E2E and Docs)

## 8. Success Criteria
- `uv run pytest backend/tests/api/test_chat_stream.py` -> PASS
- `npm run test` -> PASS
- `curl -N -X POST http://localhost:8000/api/v1/chat/stream ...` -> Valid SSE stream.

---

### SSE WIRE FORMAT for reference:
```
data: {"type":"start","messageId":"msg-123"}\n\n
data: {"type":"text-start","id":"text-1"}\n\n  
data: {"type":"text-delta","id":"text-1","delta":"..."}\n\n
data: {"type":"text-end","id":"text-1"}\n\n
data: {"type":"finish"}\n\n
data: [DONE]\n\n
```
Required headers: Content-Type: text/event-stream, Cache-Control: no-cache, x-vercel-ai-ui-message-stream: v1

