# Code Review Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 4 |
| Blocking | 0 |
| Major | 3 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Fixed | `ToolCard` no longer has `aria-hidden`; the invalid test and documentation claim were removed. |
| 2 | M-1.2 | ✅ Fixed | `handleRegenerate` clears `lastSSEEvent` before regeneration, with an integration test covering clear and re-announcement. |
| 3 | M-1.3 | ✅ Fixed | `ErrorBlock` is now the sole error announcer and `LiveStatusAnnouncer` only handles natural completion. Stale comments are reported separately as m-2.1. |
| 4 | M-1.4 | ✅ Fixed | `errorText`, the error branch, and the unused `status` parameter were removed. The remaining one-event abstraction is separately reported as M-2.1. |
| 5 | M-1.5 | ✅ Fixed | The unimplemented Reasoning transcript glossary entry and its Chat turn reference were removed. |
| 6 | M-1.6 | ⚠️ Partially Fixed | The original identifiers were removed, but the new regenerate test comment introduces `M-1.2/SP-1.1` at `ChatPanel.integration.test.tsx` L758. |
| 7 | m-1.1 | ✅ Fixed | Both README paths now correctly reference `organisms/ReasoningChip.tsx` and its test. |
| 8 | m-1.2 | ✅ Fixed | The interrupted-turn Regenerate visibility regression test was restored. |
| 9 | m-1.3 | ✅ Fixed | The redundant `DEV-106` reference was removed from the test comment. |

## Issues

### [Major] M-2.1: The one-use announcer abstraction violates the repository's own extraction rule
- **File:** `frontend/src/components/atoms/LiveStatusAnnouncer.tsx` L15
- **Problem:** `LiveStatusAnnouncer` has one call site and renders a single `<div>`, while `live-status-text.ts` wraps one reachable event literal in an exported interface and formatter. This creates two production files, dedicated unit tests, README entries, and architecture wiring for behavior that can be expressed directly in `ChatPanel`. It contradicts `docs/frontend_chat_architecture.md` L91: "inline a new visual element at first use; extract to atoms only on the second occurrence." This is Speculative Generality and new-module over-engineering under design-envelope §0 and §7.
- **Fix:** Inline the `role="status"` element in `ChatPanel`, store the announcement as a string or boolean, and remove `LiveStatusAnnouncer.tsx`, `live-status-text.ts`, their dedicated tests, and corresponding documentation entries. Retain the integration tests that verify lifecycle behavior.
- **Orchestrator note:** confirmed — single call site (`ChatPanel.tsx` L334), `AnnouncedEvent` is now a single-value type, extension rule confirmed present at the cited line. Orchestrator agrees with this direction after considering and rejecting the "keep separate for future tool-transition announcements" counter-argument (that's exactly the future-need-without-current-need pattern this repo's own review standards flag). Approved to fix.

### [Major] M-2.2: Custom CSS reimplements Tailwind's built-in `sr-only` utility
- **File:** `frontend/src/index.css` L243
- **Problem:** The project imports Tailwind (`@import "tailwindcss"`, `tailwindcss: ^4.2.2`), which already emits an `sr-only` utility when that class appears in JSX. This block duplicates and overrides the framework implementation with the same `clip: rect(...)` form Tailwind itself ships. It adds maintenance surface without changing the requested behavior.
- **Fix:** Delete the custom `.sr-only` block and continue using the existing `className="sr-only"` Tailwind utility.
- **Orchestrator note:** confirmed — Tailwind v4 present, block is byte-for-byte equivalent to Tailwind's shipped utility, newly added by this PR (not pre-existing). Safe, zero-risk deletion.

### [Minor] m-2.1: Error-path comments still describe the removed announcer behavior
- **File:** `frontend/src/components/pages/ChatPanel.tsx` L75
- **Problem:** The `onFinish` comment says disconnects and errors are handled through `status === "error"` in `LiveStatusAnnouncer`, but that component no longer accepts `status` or announces errors. The same stale claim appears in `ChatPanel.integration.test.tsx` L834 as "routes the announcement to Response failed." The actual owner is `ErrorBlock` with `role="alert"`.
- **Fix:** Update both comments to state that disconnect and error paths are announced by `ErrorBlock`; remove the nonexistent "Response failed" claim.
- **Orchestrator note:** confirmed via direct grep — both stale comments still present. Note: this is likely moot at `ChatPanel.tsx` L75-76 once M-2.1's inlining lands (the comment block will be rewritten anyway) — fixer should still explicitly verify post-inline that no stale reference survives, and separately fix the test-file comment regardless.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | No material folder-level documentation gaps. |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| — | — | — | — | No library API usage changed in the Round 1 fixer diff; prior `ai`, `@ai-sdk/react`, and `react` checks were not repeated as instructed. |

---

# Spec Conformance Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Findings Status

| ID | Status | Notes |
|----|--------|-------|
| SP-1.1 | ✅ Fixed | `handleRegenerate` 現在會在呼叫 `regenerate` 前清除 `lastSSEEvent`（`frontend/src/components/pages/ChatPanel.tsx` L156–163）；integration test 也驗證第一次完成、Regenerate 清空 live region、第二次完成再次 announce 的完整流程（`frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` L756–828）。 |
| SP-1.2 | ✅ Fixed | `ToolCard` 的 `Collapsible` 已不含 `aria-hidden`，卡片、trigger 與內容均保留給 assistive technology 存取（`frontend/src/components/organisms/ToolCard.tsx` L45–73）。 |
| SP-1.3 | ✅ Fixed | `Reasoning transcript` glossary entry 與 persistence 敘述已移除；現有 `Chat turn`、`Reasoning chip`、`Reasoning stream` 與 `Stream stall` 定義未宣稱 segment 7 的 Langfuse transcript persistence（`CONTEXT.md` L128–143）。 |

## Findings

No new findings.

## Covered Requirements

✅ `AssistantMessage` render native reasoning parts as chips — `frontend/src/components/organisms/AssistantMessage.tsx` L146–168
✅ `ChatPanel` wires chip timing、stall 與 expand/collapse state through `MessageList` — `frontend/src/components/pages/ChatPanel.tsx` L99–105、L291–306
✅ `LiveStatusAnnouncer` provides a visually hidden polite status region for natural completion — `frontend/src/components/atoms/LiveStatusAnnouncer.tsx` L15–21
✅ Abort、disconnect 與 error 不會誤 announce `"Response complete"` — `frontend/src/components/pages/ChatPanel.tsx` L65–79
✅ Error announcement 由唯一的 `ErrorBlock role="alert"` surface 負責 — `frontend/src/components/organisms/ErrorBlock.tsx` L25–38
✅ Send、Regenerate、Retry 與 Clear 均會重設 completion announcement state — `frontend/src/components/pages/ChatPanel.tsx` L145–163、L194–213
✅ `ToolCard` remains accessible while tool-transition live announcements remain deferred — `frontend/src/components/organisms/ToolCard.tsx` L45–73
✅ All five profiles set `reasoning: "on"` — `backend/agent_engine/agents/profiles/analyst/orchestrator_config.yaml` L25、`backend/agent_engine/agents/profiles/baseline/orchestrator_config.yaml` L15、`backend/agent_engine/agents/profiles/graph/orchestrator_config.yaml` L23、`backend/agent_engine/agents/profiles/quant/orchestrator_config.yaml` L23、`backend/agent_engine/agents/profiles/reader/orchestrator_config.yaml` L21
✅ The retained Playwright journey covers stop mid-reasoning followed by a clean resend — `frontend/tests/e2e/critical/stop-during-reasoning-then-resend.spec.ts` L12–50
