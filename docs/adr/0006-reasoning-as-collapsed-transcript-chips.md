# Reasoning rendered as collapsed transcript chips

Status: accepted (2026-07-24) — supersedes the F5 sub-ruling "transcript never shows reasoning" (DEV-60 ruling table / DEV-105 spec).

Provider reasoning streams to the client as AI SDK native `reasoning-*` parts. The original F5 ruling hid reasoning from the transcript entirely, surfacing it only through an ephemeral activity indicator that disappeared once reply text started. We reversed the rendering half of that ruling: each reasoning segment renders as a collapsible transcript chip — live and auto-scrolling while streaming, collapsed to a "Thought for Xs" header afterwards — interleaved with tool cards in part order. The wire protocol and "one part per provider reasoning block" mapping are unchanged; one part = one chip.

**Why.** The agent roadmap is multi-round tool loops (reason → tool → reason → tool → answer). With an ephemeral indicator, every round after the first is invisible and nothing is verifiable after the fact. Chips make the loop's rhythm legible in the transcript itself, which serves manual testing (each round's reasoning is inspectable post-hoc) and the project's portfolio goal of a visibly multi-round agent. A UX survey (2026-07-24) showed the two coherent industry patterns: ephemeral-only thinking is the single-answer-chat convention (ChatGPT, Gemini, Perplexity — thinking never reappears after answer text), while every product exposing multi-step agent runs (Claude.ai interleaved thinking, Cursor, Claude Code, Copilot agent mode) keeps a persistent thinking surface that recurs between steps. The combination we almost shipped — an ephemeral indicator that pops back mid-answer — is the one no product ships.

## Considered options

1. **Ephemeral 3-state indicator, hide on first text** (original F5+F6 ruling) — rejected: rounds 2..n of the tool loop leave no visible trace.
2. **Ephemeral indicator that reappears after answer text** — rejected: a moving element interrupting the answer the user is reading, with no precedent in any surveyed product.
3. **Collapsed transcript chips** (Claude.ai pattern) — chosen.

## Consequences

- Reasoning parts now live in the transcript as data *and* UI; the former `AssistantMessage` reasoning filter becomes a chip renderer.
- v1 chips do not survive a page reload — history replay of reasoning parts is deliberately out of scope until evidence demands it.
- The activity indicator shrinks to a placeholder for dead-air windows (submit → first content, chip collapse → reply text); it never contains reasoning text.
- The chip's "Thought for Xs" duration is measured client-side (parts carry no timestamps) — the one deliberate piece of non-derived frontend state.
