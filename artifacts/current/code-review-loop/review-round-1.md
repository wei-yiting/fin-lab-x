# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-18

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 8 |
| Blocking | 0 |
| Major | 4 |
| Minor | 3 |
| Suggestion | 1 |
| Library checks | 4 |

## Issues

### [Major] M-1.1: Timer API mutates refs during render
- **File:** `frontend/src/hooks/useReasoningTimers.ts` L23-L47, L53-L57; `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` L19-L39
- **Problem:** The hook explicitly requires `observe` to run during render, where it reads and mutates `timingsRef.current`, calls `Date.now()`, and updates `ChipTiming` objects. React 19 permits render-time ref writes only for one-time lazy initialization; this general cache mutation can leak work from interrupted renders and behave unpredictably under the app's `StrictMode`. The tests call `observe` after render inside `act`, so they do not exercise the documented integration contract. This is live UI correctness under design-envelope §7 rubric item 3, not additional scale hardening.
- **Fix:** Accept `messages` and `chatActive` as hook inputs, commit timing changes in an effect or reducer, and expose a state-backed duration snapshot that render can read without touching refs. Use `useLayoutEffect` only if the frozen duration must be committed before paint. Add a `StrictMode` harness that invokes the hook through its real component lifecycle.
- **Context7:** React 19.2.4 says not to read or write `ref.current` during rendering except for one-time lazy initialization; ref mutations belong in effects or event handlers.

### [Major] M-1.2: ReasoningChip violates its documented atomic layer
- **File:** `frontend/src/components/molecules/ReasoningChip.tsx` L1-L46; `docs/frontend_chat_architecture.md` L81-L86
- **Problem:** `ReasoningChip` is registered as a molecule, but it owns `useRef` and `useLayoutEffect`. The architecture contract classifies components that use hooks as organisms, while molecules remain prop-driven JSX without hook-owned behavior. Updating the diagram to call this a molecule does not resolve the contradiction. This is a repository architecture-contract violation under design-envelope §7 rubric item 4.
- **Fix:** Either move `ReasoningChip` to `components/organisms/` and update the architecture diagrams/imports, or keep a pure molecule and move the pinned-scroll hook into an organism wrapper.

### [Major] M-1.3: A streaming chip cannot honor the explicit collapse override
- **File:** `frontend/src/components/molecules/ReasoningChip.tsx` L48-L49, L61-L63; `frontend/src/lib/reasoning-chips.ts` L110-L116
- **Problem:** `isChipExpanded` documents and tests that an explicit `false` override collapses a streaming chip, but `showBody = streaming || expanded` forces the body open whenever `chipState === "streaming"`. Clicking the enabled header can therefore update the override without changing the UI. This would be directly visible in a live walkthrough, so it falls under design-envelope §7 rubric item 3.
- **Fix:** Make body visibility follow the already-derived `expanded` prop, derive `data-state` consistently from that visibility, and add a component test for `chipState="streaming"` with `expanded={false}`. Update the DOM-contract wording if a collapsed live chip needs a distinct semantic state.

### [Major] M-1.4: Session-only process identifiers leaked into durable code and docs
- **File:** `frontend/src/components/molecules/ReasoningChip.tsx` L10-L13; `frontend/src/components/molecules/__tests__/ReasoningChip.test.tsx` L22-L24; `docs/adr/0015-reasoning-as-collapsed-transcript-chips.md` L17-L19
- **Problem:** `"consumer #2"`, `"(C4)"`, and `"v1 chips"` depend on numbering from the implementation process rather than describing the enduring reason. Future readers cannot recover what consumer 1, C4, or the v1 boundary means. This is readability cruft, calibrated as repository polish under design-envelope §7 rubric item 4.
- **Fix:** Replace them with durable descriptions: name the ReasoningChip header as the stall-copy consumer, remove `C4` from the test name, and replace `v1 chips` with "the current chip implementation."

### [Minor] m-1.1: The interactive header omits the required aria-label
- **File:** `frontend/src/components/molecules/ReasoningChip.tsx` L58-L76; `docs/frontend_dom_contract.md` L60-L66
- **Problem:** The DOM contract requires every interactive element to carry an `aria-label`, but the chip header button relies only on its text content. The button remains broadly accessible, so this is a contract inconsistency rather than a broken control; design-envelope §7 rubric item 4 applies.
- **Fix:** Add a dynamic `aria-label` that preserves the current header copy and communicates the expand/collapse action, then assert its accessible name in the component test.

### [Minor] m-1.2: The hooks README omits the newly added non-derived store
- **File:** `frontend/src/hooks/README.md` L15-L20; `docs/adr/0015-reasoning-as-collapsed-transcript-chips.md` L17-L20
- **Problem:** The README still says exactly two non-derived stores are allowed and enumerates only the stall and grace timers, while this change adds per-chip timing state and the ADR calls it deliberate non-derived state. The resulting state-budget documentation is internally inconsistent.
- **Fix:** Change the count to three and add `useReasoningTimers` with its timestamp-absence justification. Narrow the ADR wording from "the one deliberate piece" to "the deliberate non-derived state for reasoning chips."

### [Minor] m-1.3: The ADR carries an unnecessary issue identifier
- **File:** `docs/adr/0015-reasoning-as-collapsed-transcript-chips.md` L3-L5
- **Problem:** `DEV-105` adds process metadata to a sentence already identifying the superseded multi-provider refactor ruling. Issue IDs are tolerated but should be removed when the descriptive text stands alone; this is optional polish under design-envelope §7 rubric item 4.
- **Fix:** Remove the parenthetical issue ID, or replace it with a durable repository link if the referenced specification is needed to understand the decision.

### [Suggestion] S-1.1: Animate a wrapper instead of the SVG
- **File:** `frontend/src/components/molecules/ReasoningChip.tsx` L69-L72
- **Suggestion:** `transition-transform` and `rotate-90` animate the Lucide SVG directly. Wrap the icon in a small element and apply the transform to that wrapper so the browser can hardware-accelerate it more reliably. This is only optional polish at this app's scale under design-envelope §7 rubric item 4.
- **Vercel rule:** `rendering-animate-svg-wrapper`

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None. The affected hooks, component hierarchy, DOM contract, and architectural decision all have existing documentation; the inconsistency above is a content defect rather than a missing README. |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| React | 19.2.4 | `useRef`, `useLayoutEffect` | ❌ Wrong | `useLayoutEffect` is appropriate for pre-paint scrolling, but `useReasoningTimers` requires general `ref.current` mutation during render, which React explicitly forbids. |
| `@testing-library/react` | 16.3.2 | `render`, `renderHook`, `fireEvent.click` | ✅ Current | `fireEvent` is sufficient for the simple callback assertion; no focus, keyboard, or complete pointer sequence is under test. |
| `lucide-react` | 1.7.0 | `ChevronRight` | ✅ Current | The icon API and `aria-hidden` usage are current. The direct SVG transform is a performance suggestion, not API misuse. |
| Tailwind CSS | 4.2.2 | `[overflow-wrap:anywhere]` | ✅ Current | Valid Tailwind v4 arbitrary-property syntax. |

## Vercel Standards Check

| Rule id | Applies? | Verdict | Notes |
|---------|----------|---------|-------|
| `rerender-use-ref-transient-values` | yes — timing data is transient | ⚠️ Violated | A ref is a suitable container, but this implementation reads and mutates it during render instead of an effect or event handler. |
| `rerender-derived-state-no-effect` | yes — chip state and expansion derive from inputs | ✅ Followed | `chipStateOf` and `isChipExpanded` avoid redundant synchronized state. |
| `rendering-animate-svg-wrapper` | yes — the chevron uses a transform transition | ⚠️ Violated | The transform is applied directly to the SVG; impact is Suggestion-level at this scale. |
| `rendering-conditional-render` | yes — the body is conditionally rendered | ✅ Followed | Conditions are booleans, so there is no accidental `0` or `NaN` rendering. |
| `js-batch-dom-css` | yes — scrolling reads and writes layout properties | ✅ Followed | The effect performs one `scrollHeight` read followed by one `scrollTop` write, without interleaved write/read cycles. |
| `architecture-avoid-boolean-props` | yes — `stalled` and `expanded` are boolean props | ✅ Followed | They represent two orthogonal UI facts rather than proliferating component variants; the override bug is separate logic. |
| `state-decouple-implementation` | yes — timer state is separated from visual rendering | ✅ Followed | The chip receives derived props instead of importing the lifecycle timer hook. |
| `react19-no-forwardref` | no — no ref is exposed through component props | n/a | No `forwardRef` or public ref prop is introduced. |
| `async-*` / `server-*` | no — this is a client-only Vite component and hook | n/a | Next.js, RSC, Server Action, and server-fetch rules do not apply. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-18

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 4 |
| Missing | 3 |
| Scope creep | 0 |
| Misimplemented | 1 |

## Findings

### [Blocking] SP-1.1: Streaming chip 無法接受明確的收合 override
- **Type:** Misimplemented
- **Spec:** "- **Expansion is tail-only with a user override** — only the streaming chip is open by default; `isChipExpanded(state, override)` lets an explicit toggle win in both directions." (PR #57 description, Key decisions)
- **File:** `frontend/src/components/molecules/ReasoningChip.tsx` L49
- **Problem:** `isChipExpanded("streaming", false)` 正確回傳 `false`，但 component 使用 `streaming || expanded` 決定是否顯示 body。因此 streaming chip 即使收到明確的 `expanded={false}`，仍會顯示 body 且回報 `aria-expanded="true"`；使用者的收合操作實際上無效。
- **Fix:** 讓 body visibility 直接服從 `expanded`，並相應調整 `data-state`。auto-scroll effect 也應只在 streaming 且展開時執行，並涵蓋收合後重新展開的情況；新增 streaming + `expanded={false}` 的 component test。

### [Major] SP-1.2: Timer tests 未證明 clock 是在 next-part arrival 才 freeze
- **Type:** Missing
- **Spec:** "`useReasoningTimers` supplies the seconds: a per-chip wall-clock that starts when the part appears, freezes when the round's next part arrives, and samples on Stop." (PR #57 description, Solution)
- **File:** `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` L33
- **Problem:** 所有 freeze cases 都在加入下一個 part 的同一次 observation 中，把 reasoning state 改成 `done`。因此，若實作錯誤地在 `reasoning-end`／`state === "done"` 時 freeze，現有 tests 仍會通過，沒有真正鎖定 spec 指定的 next-part boundary。
- **Fix:** 加入中間 observation：先讓 reasoning 變成 `done`、但不加入下一個 part，推進時間並證明 elapsed time 仍會增加；之後加入 tool/text part，再證明 duration 從該時刻起固定。

### [Major] SP-1.3: Auto-scroll 行為沒有 unit test
- **Type:** Missing
- **Spec:** "each reasoning segment renders as a collapsible transcript chip — live and auto-scrolling while streaming, collapsed to a "Thought for Xs" header afterwards — interleaved with tool cards in part order." (ADR-0015, `docs/adr/0015-reasoning-as-collapsed-transcript-chips.md` L5)
- **File:** `frontend/src/components/molecules/__tests__/ReasoningChip.test.tsx` L15
- **Problem:** Streaming test 只確認 header 與 body text 存在，未驗證文字增加後 `scrollTop` 會移至 `scrollHeight`。刪除或破壞 L41–46 的 pinned-scroll effect 時，現有 test suite 仍不會失敗。
- **Fix:** Mock body 的 `scrollHeight`，以新增文字 rerender streaming chip，並斷言 `scrollTop` 更新至最新的 `scrollHeight`。

### [Major] SP-1.4: 宣告的 DOM contract 未被 tests 完整鎖定
- **Type:** Missing
- **Spec:** "- `frontend/src/components/molecules/ReasoningChip.tsx` (+ test) — the chip; `data-state` / `data-round` / `aria-expanded` contract, `aria-live="polite"` on the header only." (PR #57 description, Key Changes)
- **File:** `frontend/src/components/molecules/__tests__/ReasoningChip.test.tsx` L14
- **Problem:** Tests 有檢查部分 `data-state` 與 `aria-live`，但未檢查 `data-round`、`aria-expanded`，也未鎖定 `data-state="collapsed"`。這些宣告為穩定 contract 的 attributes 可在不造成 test failure 的情況下消失或漂移。
- **Fix:** 對 streaming、collapsed、expanded cases 分別斷言 `data-state` 與 `aria-expanded`，並至少加入一個 `data-round` ordinal assertion。

## Covered Requirements

✅ `ChipState`、derived abort detection 與 done/aborted header labels 已實作 — `frontend/src/lib/reasoning-chips.ts`
✅ `chipKey(messageId, partIndex)` 提供跨 message 隔離 — `frontend/src/lib/reasoning-chips.ts`
✅ Timer map 使用 client-side wall clock，具備 start、next-part freeze、inactive sampling 與 full reset 實作 — `frontend/src/hooks/useReasoningTimers.ts`
✅ Streaming body 使用約四行視窗並具有 pinned-bottom effect — `frontend/src/components/molecules/ReasoningChip.tsx`
✅ Done 與 aborted chips 可展開查看完整 raw transcript text — `frontend/src/components/molecules/ReasoningChip.tsx`
✅ `data-state`、`data-round`、`aria-expanded` 與 header-only `aria-live="polite"` attributes 已輸出 — `frontend/src/components/molecules/ReasoningChip.tsx`
✅ Reasoning chip styles 提供四行 max-height — `frontend/src/index.css`
✅ Component、helpers 與 timing hook 維持 dark，沒有 page 或 organism import — `frontend/src/components/molecules/ReasoningChip.tsx`
✅ ADR-0015 記錄 collapsed transcript chip 決策、reload 限制及 client-side duration — `docs/adr/0015-reasoning-as-collapsed-transcript-chips.md`
