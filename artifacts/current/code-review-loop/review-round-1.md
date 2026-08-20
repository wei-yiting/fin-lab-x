# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 9 |
| Blocking | 0 |
| Major | 6 |
| Minor | 3 |
| Suggestion | 0 |
| Library checks | 3 |

## Issues

### [Major] M-1.1: Tool cards are hidden from assistive technology without a replacement
- **File:** `frontend/src/components/organisms/ToolCard.tsx` L46
- **Problem:** The entire interactive `Collapsible` is now `aria-hidden="true"`, including its focusable trigger. The stated replacement does not exist: `LiveStatusAnnouncer` explicitly defers tool transitions and only announces finish/error. Screen-reader users therefore lose tool progress, failures, results, and detail controls, while keyboard focus may still enter an accessibility-hidden subtree.
- **Fix:** Remove `aria-hidden` from `ToolCard`. If a later implementation announces tool transitions separately, keep the interactive card accessible or make any hidden visual duplicate non-focusable; never hide a focusable control tree.

### [Major] M-1.2: Regenerate never rearms the completion announcement
- **File:** `frontend/src/components/pages/ChatPanel.tsx` L156
- **Problem:** `handleSend`, `handleRetry`, and `handleClearSession` clear `lastSSEEvent`, but `handleRegenerate` does not. After the first natural completion, the live region remains `"Response complete"` throughout regeneration. The next `onFinish` writes the same visible text, so assistive technology may receive no new completion mutation.
- **Fix:** Call `setLastSSEEvent(null)` before `regenerate({ messageId })`, and add an integration test covering natural completion → Regenerate → cleared live region → second completion announcement.
- **Context7:** The `useChat.onFinish` signature and completion flags are used correctly. This is local lifecycle-state handling, not an AI SDK API error.

### [Major] M-1.3: Every error is exposed through two competing live regions
- **File:** `frontend/src/components/organisms/ErrorBlock.tsx` L26
- **Problem:** An error simultaneously mounts `ErrorBlock` with `role="alert"` and changes `LiveStatusAnnouncer`'s `role="status"` content. Screen readers can announce the same failure twice—once assertively with the friendly title and once politely as the generic `"Error: stream interrupted"`.
- **Fix:** Choose one announcement owner. The simpler implementation is to keep `ErrorBlock` as the error alert and restrict `LiveStatusAnnouncer` to completion events. Remove the duplicate error mapping and add one integrated accessibility assertion.

### [Major] M-1.4: `AnnouncedEvent.errorText` is an unreachable state tested only through fabricated input
- **File:** `frontend/src/components/atoms/live-status-text.ts` L3
- **Problem:** `AnnouncedEvent` can only have `type: "finish"`, and production code only creates `{ type: "finish" }`; no producer ever supplies `errorText`. The test at `LiveStatusAnnouncer.test.tsx` L69 constructs an impossible production state. This violates the design-envelope §0 Reachability Rule; §7 sets a Major floor for consumer-less fields and branches.
- **Fix:** Remove `errorText` and its branch if `ErrorBlock` owns error announcements. Otherwise introduce a real error event producer carrying the friendly error text and model it as a distinct discriminated-union member.

### [Major] M-1.5: Current documentation claims an out-of-scope Reasoning transcript already ships
- **File:** `CONTEXT.md` L128
- **Problem:** The new definitions state that a Chat turn owns a Reasoning transcript and that the full transcript is written to the root trace at turn end. The supplied scope says that accumulator and Langfuse persistence belong to segment 7 and are untouched here. The current SSOT therefore documents nonexistent observability behavior, violating design-envelope §0 and making a false promise inside the §4 Observability production-grade zone.
- **Fix:** Remove the Reasoning transcript definition and its Chat-turn reference from this segment. Add them only when the accumulator and root-span persistence are implemented and verified.

### [Major] M-1.6: Session-local decision and scenario identifiers leaked into the change
- **File:** `frontend/src/__tests__/msw/fixtures/long-reasoning-then-text.ts` L6
- **Problem:** The diff adds `S-chip-01`, `S-chip-07`, `J-pres-01`, `D22`, `S-rsn-14`, `S-chip-05`, and `DEV-109 ruling 11` across the fixture, production comments, CSS, and test names. Notable locations include `ToolCard.tsx` L46, `LiveStatusAnnouncer.test.tsx` L6/L23/L32/L49, `ErrorBlock.test.tsx` L91, `ToolCard.test.tsx` L69, `ChatPanel.tsx` L98, `ChatPanel.integration.test.tsx` L907, and `index.css` L242. These labels conceal the actual rationale and are meaningless outside the producing artifacts.
- **Fix:** Replace every identifier with the descriptive behavior or reason. For example, explain why the tool card is accessible/hidden, name tests by their observable behavior, and let the fixture's existing `description` carry its purpose rather than adding scenario IDs.

### [Minor] m-1.1: Atoms README points contributors to a nonexistent ReasoningChip location
- **File:** `frontend/src/components/atoms/README.md` L21
- **Problem:** The README says `ReasoningChip` and its tests live under `molecules/`, while both live under `components/organisms/`. This contradicts the architecture document updated in the same diff.
- **Fix:** Change both references at L21 and L36 to `organisms/ReasoningChip.tsx` and `organisms/__tests__/ReasoningChip.test.tsx`.

### [Minor] m-1.2: The interrupted-turn Regenerate regression test was removed
- **File:** `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` L271
- **Problem:** This diff replaces the existing test proving that `interrupted=true` hides Regenerate even when all parts look complete. The new abort/resend coverage never asserts that the Regenerate control is absent, so a regression in the `!interrupted` gate would pass.
- **Fix:** Restore a compact component test that supplies both `interrupted` and `onRegenerate`, then asserts that `regenerate-btn` is absent.

### [Minor] m-1.3: Issue metadata remains in a test comment
- **File:** `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` L1130
- **Problem:** `"DEV-106 review fix"` is issue/process metadata whose surrounding explanation already stands alone.
- **Fix:** Remove the issue reference and state directly that the assertion prevents a new send from clearing an already-frozen chip duration.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | No material folder-level documentation gap; the problem is inaccurate content in an existing README, reported above. |

## Official Standards Check

Results of Context7 verification for each library used in the changes:

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| `ai` | 6.0.142 | `onData` routing / `isDataUIMessageChunk` | ✅ Current | Installed `index.mjs:5765` confirms `onData` is gated to `data-*` chunks; reasoning, text, tool, start, and finish parts do not arrive there. |
| `@ai-sdk/react` | 3.0.144 | `useChat.onFinish`, `experimental_throttle` | ✅ Current | The destructured flags are correct, and returning on `isAbort \|\| isDisconnect \|\| isError` exactly excludes every non-natural completion path. `experimental_throttle` remains the current option name. |
| `react` | 19.2.4 | `useLayoutEffect` | ✅ Current | `observe` schedules state and the frozen timing must be reflected before paint, so `useLayoutEffect` is justified. The added call site does not read or write refs during render. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 3 |
| Missing | 0 |
| Scope creep | 2 |
| Misimplemented | 1 |

## Findings

### [Blocking] SP-1.1: Regenerate 未重設 live-region 狀態
- **Type:** Misimplemented
- **Spec:** "Review question: are the `AssistantMessage`/`ChatPanel` wiring, the `LiveStatusAnnouncer` accessibility surface, and turning `reasoning="on"` across all five profiles correct?" (DEV-169, Review question)
- **File:** `frontend/src/components/pages/ChatPanel.tsx` L156
- **Problem:** 一般 send、retry 與 clear 都會清除 `lastSSEEvent`，但 `handleRegenerate` 不會。完成過一次回應後，live region 會在 regenerate 期間持續顯示舊的 `Response complete`；新回應完成時文字仍相同，因此 screen reader 可能不會再次宣告完成。這使 `LiveStatusAnnouncer` 在既有 regenerate flow 中只完成部分 wiring。
- **Fix:** 在呼叫 `regenerate` 前執行 `setLastSSEEvent(null)`，並新增 integration test 驗證 regenerate 開始後 live region 清空、完成後重新顯示 `Response complete`。

### [Major] SP-1.2: ToolCard 被隱藏，但 announcer 未提供替代資訊
- **Type:** Scope creep
- **Spec:** "`AssistantMessage`/`ChatPanel` wire up the chips, a11y announcer, profiles flip `reasoning` to `"on"`" (DEV-110, segment 6 definition)
- **File:** `frontend/src/components/organisms/ToolCard.tsx` L46
- **Problem:** Diff 額外對整個 `ToolCard` 加上 `aria-hidden="true"`，移除 screen reader 對 tool 名稱、狀態及可展開內容的存取；然而 `LiveStatusAnnouncer` 明確將 tool transitions 延後，僅宣告 finish/error。這不是 announcer wiring 所需的 plumbing，且造成未被替代的 accessibility 行為移除。
- **Fix:** 移除 `ToolCard` 的 `aria-hidden`、對應測試與錯誤文件宣稱；除非另有明確 spec 並已提供包含 tool 資訊與 details 的等價 accessibility surface，否則保留原有可存取內容。

### [Major] SP-1.3: CONTEXT.md 提前宣稱 segment 7 的 trace persistence
- **Type:** Scope creep
- **Spec:** "Not in scope: the reasoning-transcript/Langfuse root-span persistence (segment 7) and the trace verify script (segment 8) — both untouched by this diff." (DEV-169, scope note)
- **File:** `CONTEXT.md` L142
- **Problem:** 新增的 `Reasoning transcript` glossary entry 宣稱完整 reasoning 會在 turn 結束時寫入 root trace，並描述 abort marker semantics；本 diff 並未實作這些 segment 7 行為。這既觸碰明確排除的範圍，也把尚未存在的 persistence 描述成現行 contract。
- **Fix:** 從本 segment 移除 `Reasoning transcript` entry，以及 L129 對它的引用；等 segment 7 實作與驗證完成時再加入相符的 glossary contract。

## Covered Requirements

✅ `AssistantMessage`／`ChatPanel` 已將 reasoning parts 接到既有 `ReasoningChip` render path — `frontend/src/components/organisms/AssistantMessage.tsx`

✅ 五個 profiles 均已切換為 `reasoning: "on"` — `backend/agent_engine/agents/profiles/*/orchestrator_config.yaml`

✅ 保留一個 Playwright browser/MSW 的 stop mid-reasoning → resend journey — `frontend/tests/e2e/critical/stop-during-reasoning-then-resend.spec.ts`

✅ 最終 diff 未保留原先規劃的 Playwright multi-provider matrix — `frontend/tests/e2e/critical/`

> Note (orchestrator): this line was truncated in the reviewer's raw output (mid file-path). Cross-checked directly against `git diff --stat` and `git log`: confirmed — the matrix spec and its 6 yaml fixtures are absent from the final diff; only `stop-during-reasoning-then-resend.spec.ts` remains under `frontend/tests/e2e/critical/`.
