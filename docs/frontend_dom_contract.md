# Frontend DOM Observability Contract

The streaming chat UI exposes a stable set of `data-*` attributes and `aria-label`s that tests and tooling rely on. This document describes the **rules and semantic enums** that govern those selectors. For the per-component list of `data-testid` values, the component source files themselves are the source of truth — grep `data-testid=` under `frontend/src/components/`.

## Principles

1. **ARIA first, `data-testid` second.** Interactive elements (`button`, `textarea`) always carry an `aria-label`. `data-testid` is added only where ARIA cannot express the semantic — status indicators, message containers, internal state markers.
2. **`data-testid` is permanent in production.** No babel-plugin strip, no dev-only gate. The bundle-size impact is negligible (~1KB gzipped across the app) and maintaining two build pipelines is not worth it. Test-only attributes like `data-chat-id` on `ChatPanel` are also rendered in all environments — the UUID is already client-generated and carries no secret.
3. **`data-status` / `data-tool-state` are dual-purpose.** They serve both as test selectors and as CSS state-driven style hooks (the same pattern shadcn's `Collapsible` uses for `data-state`).
4. **Naming convention.** `kebab-case`, with a prefix matching the component domain: `composer-`, `tool-card-`, `chat-`, `stream-`, `error-`.
5. **Attributes must stay live.** `data-status` / `data-tool-state` must reflect current React state. Do not cache for performance.

## Semantic enums

These enums drive both test selectors and rendering logic. They are **not** derivable from scanning the JSX; they encode product decisions and so belong in this document.

### `data-tool-state` (on `ToolCard` root)

`input-streaming | input-available | output-available | output-error | aborted`

- `aborted` is a frontend-only 4th state (see architecture §4). AI SDK's native `ToolUIPart.state` enum has only three values.

### `data-status` (on `MessageList` root)

`submitted | streaming | ready | error` — mirrors `useChat.status`.

### `data-error-source` (on `ErrorBlock` root)

`pre-stream | mid-stream` — selects which variant of the block renders. Both variants currently render through the same `errorContent` slot inside `MessageList` (after the last message). The distinction drives the friendly-title source (pre-stream-http / network vs mid-stream-sse in `lib/error-messages.ts`) and the `data-testid` (`stream-error-block` vs `inline-error-block`).

### `data-error-class` (on `ErrorBlock` root)

Emitted so tests can distinguish error flavors and so the component can choose a friendly title + Retry visibility.

- `pre-stream-422` — regenerate validation failed
- `pre-stream-404` — conversation not found
- `pre-stream-409` — session busy
- `pre-stream-500` — backend internal error
- `pre-stream-5xx` — other 5xx
- `network` — `fetch` TypeError / offline
- `mid-stream` — SSE-level `error` event
- `unknown` — classifier fallback

These classes drive both the friendly title (via `lib/error-messages.ts`) and the Retry button visibility (`retriable` field per class).

### `data-status-state` (on `StatusDot`)

`running | success | error | aborted`

## Adding new components

DOM contract is part of a component spec, alongside props / state / behavior. When adding a component:

1. Pick an `aria-label` for every interactive element.
2. Add a `data-testid` only if tests need to query something ARIA cannot express.
3. If the component has state that matters to tests or CSS, add a `data-{domain}-state` attribute that mirrors the React state — and if the value set is closed and meaningful, add its enum to the "Semantic enums" section above.
4. Follow the naming convention (§Principles 4).
