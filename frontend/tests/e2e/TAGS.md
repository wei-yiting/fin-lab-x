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

| Test                                                          | Tags                       |
| ------------------------------------------------------------- | -------------------------- |
| app shell loads and displays heading                          | `@smoke`, `@regression`    |
| tool + text streaming completes successfully                  | `@smoke`, `@regression`    |
| citations render as RefSup with Sources block                 | `@smoke`, `@regression`    |
| clear session resets messages and chatId                      | `@smoke`, `@regression`    |
| regenerate replaces assistant response                        | `@smoke`, `@regression`    |
| overflowed content is scrollable                              | `@smoke`, `@regression`    |
| sending new message auto-scrolls to bottom                    | `@smoke`, `@regression`    |
| pre-stream error recovery via Retry                           | `@critical`, `@regression` |
| page refresh produces new chatId and clean state              | `@critical`, `@regression` |
| regenerate failure → retry succeeds without duplicate history | `@critical`, `@regression` |
| stop preserves partial text and resets Composer               | `@critical`, `@regression` |
| inline body links with javascript: URL are sanitized          | `@security`, `@regression` |
| javascript: URL in source reference is sanitized              | `@security`, `@regression` |
