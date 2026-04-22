# E2E Test Tag Taxonomy

Tags are applied via Playwright's native API:
`test('title', { tag: ['@smoke', '@regression'] }, async (...) => { ... })`

Filter with `pnpm exec playwright test --grep @tag-name`.

## Tags

### `@smoke`

- **Intent**: Deploy-verification canary. Covers basic app operability — can the app load, can a user send a message, do core UI paths render?
- **Target**: < 3 min wall time. Should run on every deploy.
- **Budget**: ~5 tests. Keep small; expand via `@regression` instead.

### `@critical`

- **Intent**: P0 regression guard. If any `@critical` test fails, the build should not ship.
- **Scope**: End-to-end flows that exercise real browser behavior no lower layer can simulate — streaming abort, page refresh, retry recovery.
- **Target**: Run on every PR.

### `@security`

- **Intent**: Security-specific assertions (XSS sanitization, injection guards, dangerous URL handling).
- **Scope**: Should remain stable regardless of UI refactors. Keep assertions tight and deterministic.

### `@regression`

- **Intent**: Catch-all, every test carries this tag. Filter target for nightly full-suite runs.
- **Rule**: Every test must be tagged `@regression` in addition to its specificity tag.

## Current inventory

| Test                                                           | Tags                       |
| -------------------------------------------------------------- | -------------------------- |
| app shell loads and displays heading                           | `@smoke`, `@regression`    |
| clear session resets messages and chatId                       | `@smoke`, `@regression`    |
| overflowed content is scrollable                               | `@smoke`, `@regression`    |
| sending new message auto-scrolls to bottom                     | `@smoke`, `@regression`    |
| typing indicator persists during slow stream start             | `@smoke`, `@regression`    |
| pre-stream error recovery via Retry                            | `@critical`, `@regression` |
| pre-stream 409 surfaces retriable 'system busy' error          | `@critical`, `@regression` |
| mid-stream error preserves partial text + surfaces error block | `@critical`, `@regression` |
| page refresh produces new chatId and clean state               | `@critical`, `@regression` |
| regenerate failure → retry succeeds without duplicate history  | `@critical`, `@regression` |
| stop preserves partial text and resets Composer                | `@critical`, `@regression` |
| inline javascript: URL is sanitized end-to-end                 | `@security`, `@regression` |
| source-reference javascript: URL is sanitized end-to-end       | `@security`, `@regression` |

## Layer policy

Tests that verify pure component render / state / prop behavior belong in
Vitest + RTL, not E2E. This suite deliberately excludes duplicate coverage of:

- Tool card state rendering (`ToolCard.test.tsx`)
- Citation render / Sources block (`AssistantMessage.test.tsx` TC-comp-citation-\*)
- Regenerate button visibility + click dispatch (`AssistantMessage.test.tsx` + `ChatPanel.integration.test.tsx`)
- Markdown URL sanitization detail (`Markdown.test.tsx` TC-comp-markdown-xss-\*)

E2E scope is reserved for real-browser-only concerns: streaming abort, page
refresh, scroll, and the end-to-end security invariant that no hostile link
survives sanitization through to a rendered dialog.
