# Fix Round 2

> Fixer: Claude (general-purpose subagent) | Date: 2026-08-17
> Dispatched with 4 approved items (m-2.1, m-2.2, O-2.1, O-2.2). SP-2.1 was dismissed by
> the user before dispatch; SP-2.2 and SP-2.3 are not fixer tasks.

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| m-2.1 | Converted the existing `streaming strips definition lines (no flicker)` case into a `test.each` over `""` and `"   "` (three-space) indents, asserting the raw definition URL and Sources block never render during streaming. Reused the existing test module. Confirmed it is a real regression guard: temporarily narrowing `REF_DEF_LINE_RE` back to `/^\[(\d+)\]…/` makes exactly 1 of 18 fail; regex restored. | `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` |
| m-2.2 | Concrete composition graph: `MessageList --> ActivityPlaceholder` → `ChatPanel --> ActivityPlaceholder`, placed with the sibling slot edges (`EmptyState`, `ErrorBlock`). Verified by import: exactly one production importer, `ChatPanel.tsx` L14; `MessageList.tsx` imports only `UserMessage`, `InterruptedMarker`, `AssistantMessage`. The §2.1 layer diagram carried the same gap (a page composing an atom directly with no edge) — that edge was added too. Prose checked via `grep -i placeholder`; no matching claim. | `docs/frontend_chat_architecture.md` |
| O-2.1 | Dropped `export` from `isSuppressedChip` **and** from `ReasoningPartLike`. **Both could be made private** — `tsc -b --force` passes clean, so the compiler does not require `ReasoningPartLike` to stay exported despite appearing in `isReasoningPart`'s return-type predicate. Module now exports 4 functions + `ChatMessageLike`, all with external consumers. No behaviour change. | `frontend/src/lib/reasoning-chips.ts` |
| O-2.2 | Added `frontend/src/lib/__tests__/reasoning-chips.test.ts` (132 lines, 35 cases) covering the four pure predicates directly, then slimmed the hook test to window/timing behaviour (308 → 263 lines, 16 → 13 cases) with a header comment naming `reasoning-chips.test.ts` as owner of the shape enumeration. | `frontend/src/lib/__tests__/reasoning-chips.test.ts` (new), `frontend/src/hooks/__tests__/useDeadAirPlaceholder.test.ts` |

## Not Fixed

None.

## Reverted

None.

## Coverage Ledger (O-2.2)

Three hook cases deleted and one 8-shape loop reduced to 3 shapes. Every assertion has an
equivalent:

| Behaviour asserted before | Where it lives now |
|---------------------------|--------------------|
| Window (a) shape: no assistant message yet → waiting | **Kept** in hook test (hook-only structural branch `!last \|\| last.role !== "assistant"`) |
| Window (a) shape: assistant message with zero parts → waiting | **Kept** in hook test (hook-only `parts.length > 0` branch) |
| Window (a) shape: `step-start` only → waiting | `reasoning-chips.test.ts` → `isRenderablePart` "step boundary" → false; `turnHasRenderableContent` "only invisible parts" → false |
| Window (a) shape: `reasoning` `text: ""` `state: "streaming"` → waiting | `isRenderablePart` "reasoning-start before its first delta" → false; hook keeps the `state: "done"` zero-delta variant as its representative |
| Window (a) shape: `text: ""` → waiting | `isRenderablePart` "empty text" → false |
| Window (a) shape: `text: "  \n "` → waiting | `isRenderablePart` "whitespace-only text" → false |
| Window (a) shape: `text: "[1]: https://example.com"` → waiting | `isRenderablePart` "column-zero reference definition only" → false (plus a new 3-space-indented case) |
| Window (a) shape: `text: "來源："` → waiting | `isRenderablePart` "Chinese source header only" → false (plus a new `**References**` case) |
| "zero-delta suppressed chip: no chip renders, so placeholder keeps covering (S-chip-08)" — stays `waiting` before *and* after 5× grace | **Folded into** the window (a) test: its representative shape is now the S-chip-08 fixture (`reasoning` / `text: ""` / `state: "done"`), and every shape in the loop now advances 5× grace and re-asserts `waiting`. The no-blink assertion is preserved, not dropped. |
| "window (c) survives a zero-delta suppressed round between tool rounds" | Renderability half → `isRenderablePart` "reasoning closed without any delta" → false. Hook half → **already covered** by the retained "window (c) stays covering when a not-yet-painting reasoning part appends", whose fixture is the same tool-done + invisible-reasoning shape and which additionally asserts the grace timer does not restart. |
| "window (c) survives a text delta that normalizes to nothing between tool rounds" | Renderability half → `isRenderablePart` ref-def cases → false. Hook half → same retained window (c) invisible-trailing-part case. |
| All other 12 hook cases (windows A/B/C transitions, grace delay, both micro-gaps, sibling-tool-in-flight, errored terminal state, invisible-trailing-part, reply-text yield, ready/error gating) | Unchanged |

Coverage that did **not** exist before this round: `isToolPart` plain `"tool"` → false and
non-string/absent `type` → false; `isReasoningPart` negative cases; `dynamic-tool`
renderability; three-space-indented ref-def and `**References**` header suppression;
`turnHasRenderableContent` trailing-invisible-part case.

## Tests Run (fixer)

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pnpm test AssistantMessage.test.tsx` | ✅ 18/18 | was 17 before m-2.1 |
| Regression probe: narrow `REF_DEF_LINE_RE`, rerun | ❌ 1/18 (expected) | proves m-2.1's new case guards the widened regex; file restored |
| `pnpm test reasoning-chips.test.ts` | ✅ 35/35 | new file |
| `pnpm test useDeadAirPlaceholder.test.ts` + new file | ✅ 48/48 | — |
| `pnpm format:check` | ✅ Pass | flagged the new test file; ran prettier, re-checked clean |
| `pnpm lint` | ✅ 0 errors, 1 warning | pre-existing `mockServiceWorker.js` unused-directive only |
| `pnpm exec tsc -b --force` | ✅ Pass | first run surfaced 5 TS2353 from an over-narrow local `msg()` param type in the new test; widened to `Array<Record<string, unknown>>` |
| `pnpm test` (full) | ✅ 211/211 across 23 files | — |
| `pnpm build` | ✅ 453ms | pre-existing >500 kB chunk advisory only |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `frontend/src/lib/__tests__/reasoning-chips.test.ts` | Added (132 lines, 35 cases) | The four pure predicates directly — `isReasoningPart`; `isToolPart` (static `tool-*`, `dynamic-tool`, plain `"tool"`, absent/non-string `type`); `isRenderablePart` (reasoning with/without deltas, tool parts, visible prose, whitespace, ref-defs at column zero and 3-space indent, CN/EN source headers, `step-start`, unknown types); `turnHasRenderableContent` |
| `frontend/src/hooks/__tests__/useDeadAirPlaceholder.test.ts` | Modified (308 → 263 lines, 16 → 13 cases) | Slimmed to window A/B/C transitions, grace delay + both micro-gaps, invisible-trailing-part, `ready`/`error` gating. Shape loop 8 → 3, each now also asserting no blink across 5× grace. |
| `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` | Modified | Streaming definition-strip case parameterized over column-zero and three-space-indented definitions |

## Final Diff Size

| Metric | Value |
|--------|-------|
| `git diff --shortstat c57b4f3` | 25 files, 1152 insertions(+), 166 deletions(-) |
| Untracked under `frontend/src` | 170 lines — `atoms/__tests__/ActivityPlaceholder.test.tsx` (38, round 1), `lib/__tests__/reasoning-chips.test.ts` (132, round 2) |
| Total insertions incl. untracked | 1322 |
| Net (insertions − deletions, incl. untracked) | **1156** |
| Change vs. round 1 | net **+135**, driven by the new `reasoning-chips.test.ts` (+132) offset by hook-test slimming (−45) |

## Orchestrator Verification

| Claim | Verified |
|---|---|
| `reasoning-chips.ts` exports only consumed symbols | ✅ `grep "^export"` returns `ChatMessageLike`, `isReasoningPart`, `isToolPart`, `isRenderablePart`, `turnHasRenderableContent`. `ReasoningPartLike` and `isSuppressedChip` have zero references outside their own file. |
| `tsc` accepts the private `ReasoningPartLike` | ✅ `pnpm exec tsc -b --force` exits 0. |
| Hook test is now window/timing only | ✅ 13 cases, all named for windows, grace, micro-gaps, or status gating. |
| Full CI green on the working tree | ✅ format ✓ · lint 0 errors (1 pre-existing warning) ✓ · `tsc -b --force` ✓ · 211 tests / 23 files ✓ · build ✓ |
| O-2.2 would reduce the line count | ❌ **Orchestrator prediction was wrong.** The restructure added net +135 lines because the new file covers behaviour that had no test at all. Test *quality* improved; the SP-2.3 overage did not. |
