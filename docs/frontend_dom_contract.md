# Frontend DOM Observability Contract

The streaming chat UI exposes a stable set of `data-*` attributes and `aria-label`s that tests and tooling rely on. This document is the source of truth for those selectors. It is paired with `frontend_chat_architecture.md`.

## Principles

1. **ARIA first, `data-testid` second.** Interactive elements (`button`, `textarea`) always carry an `aria-label`. `data-testid` is added only where ARIA cannot express the semantic — status indicators, message containers, internal state markers.
2. **`data-testid` is permanent in production.** No babel-plugin strip, no dev-only gate. The bundle-size impact is negligible (~1KB gzipped across the app) and maintaining two build pipelines is not worth it. Exception: `data-chat-id` on `ChatPanel` is gated behind `import.meta.env.DEV` to avoid exposing UUIDs in prod HTML.
3. **`data-status` / `data-tool-state` are dual-purpose.** They serve both as test selectors and as CSS state-driven style hooks (the same pattern shadcn's `Collapsible` uses for `data-state`).
4. **Naming convention.** `kebab-case`, with a prefix matching the component domain: `composer-`, `tool-card-`, `chat-`, `stream-`, `error-`.
5. **Attributes must stay live.** `data-status` / `data-tool-state` must reflect current React state. Do not cache for performance.

## Atoms

| Component | Contract |
|---|---|
| `StatusDot` | `<span data-testid="status-dot" data-status-state="running\|success\|error\|aborted">` |
| `RefSup` | `<sup data-testid="ref-sup" data-ref-label={label}><a href={href}>` |
| `Cursor` | `<span data-testid="cursor">` |
| `TypingIndicator` | `<div data-testid="typing-indicator">` |
| `PromptChip` | `<button data-testid="prompt-chip" data-chip-index={index} aria-label={chipText}>` |
| `RegenerateButton` | `<button data-testid="regenerate-btn" aria-label="Regenerate response">` |

## Molecules

| Component | Contract |
|---|---|
| `SourceLink` | `<div data-testid="source-link" data-source-label={label} id={'src-' + label}>` — `id` is the anchor target for RefSup jump. |
| `UserMessage` | `<div data-testid="user-bubble">` |
| `Sources` | `<section data-testid="sources-block">` |
| `ToolDetail` | Root `<div data-testid="tool-detail">`; INPUT `<pre data-testid="tool-input-json">`; OUTPUT `<pre data-testid="tool-output-json">`; ERROR `<pre data-testid="tool-error-detail">` |

`ToolRow` has no separate testid — it is a structural child of `ToolCard`.

## Organisms

| Component | Contract |
|---|---|
| `ChatHeader` | Root `<header data-testid="chat-header">`. Clear button `<button data-testid="composer-clear-btn" aria-label="Clear conversation" disabled={messages.length === 0}>`. |
| `AssistantMessage` | `<article data-testid="assistant-message">` |
| `ToolCard` | Root `<div data-testid="tool-card" data-tool-call-id={toolCallId} data-tool-state={visualState}>`. Expand button `<button data-testid="tool-card-expand" aria-expanded={isOpen} aria-label="Toggle tool details">`. `visualState ∈ input-streaming \| input-available \| output-available \| output-error \| aborted`. |
| `ErrorBlock` | Pre-stream variant `<div data-testid="stream-error-block" data-error-source="pre-stream" data-error-class={errorClass}>`; mid-stream variant `<div data-testid="inline-error-block" data-error-source="mid-stream" data-error-class={errorClass}>`. Title `<h3 data-testid="error-title">` (friendly English). Detail toggle `<button data-testid="error-detail-toggle" aria-expanded={isOpen}>`. Raw detail `<pre data-testid="error-raw-detail">`. Retry `<button data-testid="error-retry-btn" aria-label="Retry">` (only when `retriable` is true). |
| `Composer` | `<form data-testid="composer">`. Textarea `<textarea data-testid="composer-textarea" aria-label="Message input" placeholder="Ask about markets, companies, or filings...">`. Send `<button data-testid="composer-send-btn" aria-label="Send message">`. Stop `<button data-testid="composer-stop-btn" aria-label="Stop response">`. |
| `EmptyState` | `<div data-testid="empty-state">` |

`Markdown` is a transparent wrapper and carries no testid; queries go through `AssistantMessage`.

## Template

| Component | Contract |
|---|---|
| `MessageList` | Root `<div data-testid="message-list" data-status={chatStatus}>`; viewport `<div data-testid="message-list-viewport">` (the ScrollArea internal div that supplies the scroll target). `chatStatus ∈ submitted \| streaming \| ready \| error`. |

## Page

| Component | Contract |
|---|---|
| `ChatPanel` | `<div data-testid="chat-panel" data-chat-id={chatId}>`. `data-chat-id` is rendered only in dev builds (`import.meta.env.DEV`). |

## `data-error-class` values

Emitted by `ErrorBlock` so tests can distinguish error flavors. The ErrorClass enum currently covers:

- `pre-stream-422` — regenerate validation failed
- `pre-stream-404` — conversation not found
- `pre-stream-409` — session busy
- `pre-stream-500` — backend internal error
- `pre-stream-5xx` — other 5xx
- `network` — `fetch` TypeError / offline
- `mid-stream` — SSE-level `error` event

These classes drive both the friendly title (via `lib/error-messages.ts`) and the Retry button visibility (`retriable` field per class).

## Adding new components

DOM contract is part of a component spec, alongside props / state / behavior. When adding a component:

1. Pick an `aria-label` for every interactive element.
2. Add a `data-testid` only if tests need to query something ARIA cannot express.
3. If the component has state that matters to tests or CSS, add a `data-{domain}-state` attribute that mirrors the React state.
4. Update this document in the same PR.
