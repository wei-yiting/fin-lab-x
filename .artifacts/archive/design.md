# V1 Streaming Chat — Design Document

> Brainstorming 階段產出。記錄需求探索、方案比較、和最終設計決策。

---

## 背景

FinLab-X 目前的 backend 僅有同步 `POST /api/v1/chat` endpoint，frontend 尚未初始化（`frontend/package.json` 是 placeholder）。需要為 V1 建立完整的 streaming chat 路徑。

## 需求探索

### 使用者需求
- 用 Vite + React + Vercel AI SDK UI + Tailwind CSS + shadcn/ui 建立前端
- Backend 提供對應的 streaming support
- 遵循 Context7 官方文件推薦的 best practices
- 在獨立 worktree 中進行開發

### 釐清過程（逐一確認）

| 問題 | 決定 | 理由 |
|------|------|------|
| Worktree 命名 | `feat/v1-frontend-streaming`，base `main` | 使用者指定 |
| Transport 架構 | FastAPI SSE v1 | 維持 Python backend，AI SDK UI 原生支援 SSE protocol |
| V1 範圍 | MVP（single chat、text streaming、basic error/retry） | 先做最小可用版本，persistence/multi-session 留給 V2 |
| 測試策略 | TDD（backend pytest + frontend vitest） | 使用者選擇最安全的方式 |

### 排除的替代方案

| 方案 | 排除理由 |
|------|---------|
| Node BFF + Python Core | 多一層 gateway 增加複雜度，V1 不需要 |
| WebSocket | 不走 AI SDK UI 預設的 data stream protocol，整合成本高 |
| MVP+ 含 persistence | 超出 V1 最小範圍，延後交付時間 |

## 研究發現

### Context7 官方文件（AI SDK v5）
- `useChat` hook 是 React streaming 的核心入口
- 必須設定 `x-vercel-ai-ui-message-stream: v1` header，否則 `useChat` 用錯 parser
- SSE wire format：`data: {json}\n\n`，終止標記 `data: [DONE]\n\n`
- Backend 可用 `StreamingResponse` 直接實作，不需額外依賴

### Codebase 現況
- Backend：FastAPI + Pydantic models + singleton `Orchestrator`，有 `arun()` 但無 streaming method
- Frontend：空 scaffold，需從零建立
- 測試：backend 有 pytest + CI，frontend 無任何測試基礎設施

### Metis Gap Analysis
- 識別出需在 Wave 1 做 spike 驗證 LangChain `astream_events()` 支援度
- 明確列出 scope creep 風險點（tool streaming、persistence、generative UI）
- 補充了 6 類 acceptance criteria（protocol byte-level、disconnect、error mid-stream、CORS、concurrent streams）

## 設計決策

1. **D1**：使用 FastAPI 內建 `StreamingResponse`，不用 `sse-starlette` — 零新增依賴
2. **D2**：增量式 `/api/v1/chat/stream` endpoint，既有 `/api/v1/chat` 完全不動 — 零回歸風險
3. **D3**：鎖定 AI SDK `ai@^5.0.0` + `@ai-sdk/react` — Context7 確認 v5 支援 UI Message Stream protocol
4. **D4**：Vite dev proxy `/api` → `localhost:8000` — 避免 CORS 複雜度
5. **D5**：Vitest + React Testing Library — 天然 Vite 搭配
6. **D6**：streaming 邏輯放 `agent_engine`（`astream()`），不放 router — 遵循 clean architecture
7. **D7**：MVP 範圍僅 text streaming — tool-call/persistence/multi-session 為 V2+

## 架構概覽

```
Frontend (NEW)                    Backend (ADDITIVE)
┌─────────────────┐              ┌──────────────────────────┐
│ Vite + React    │              │ FastAPI                  │
│ useChat() ──────┼──SSE v1────▶│ POST /api/v1/chat/stream │ ← NEW
│ shadcn/ui       │              │ POST /api/v1/chat        │ ← UNCHANGED
└─────────────────┘              │         │                │
   :5173 ──proxy──▶ :8000        │   Orchestrator.astream() │ ← NEW method
                                 │   Orchestrator.arun()    │ ← UNCHANGED
                                 └──────────────────────────┘
```

## Must NOT Have（範圍護欄）

- ❌ Next.js patterns（no `route.ts`、no server components）
- ❌ Tool-call / source streaming
- ❌ Message persistence / resume / multi-session
- ❌ 額外 Python streaming 依賴（除非 spike 證明 `StreamingResponse` 不夠用）
- ❌ 修改既有 `POST /api/v1/chat` endpoint

## 下一步

此 design 已核准，交由 `implementation.md` 定義具體執行計畫。
