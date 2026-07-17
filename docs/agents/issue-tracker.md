# Issue tracker: Linear

Issues for this repo live in Linear — team **Project-Dev** (prefix `DEV-`), project **FinLab-X**.
All operations use the Linear MCP tools (`mcp__claude_ai_Linear__*`); if they are deferred, load
them in one ToolSearch call before use.

The full session protocol (issue-start / issue-sync / issue-ship / issue-close, the stage-based
status model, and the `🙋 human-action` label semantics) lives in the user-level `linear-flow`
skill. This file covers only what the engineering skills need in order to read and write issues.

## Conventions

- **Create an issue**: `save_issue` with `team: "Project-Dev"`, `project: "FinLab-X"`, a title,
  and a Markdown description. Every issue description gets `## 🧑 Human todo` and
  `## 🤖 Agent todo` checklist sections.
- **Read an issue**: `get_issue` (pass `includeRelations: true` whenever blocking state matters),
  plus `list_comments` for discussion context.
- **List issues**: `list_issues` filtered by team / state / label.
- **Comment**: `save_comment` with `issueId`.
- **Labels**: `save_issue` `labels` replaces the full label set — always pass the complete list.
- **Close**: `save_issue` moving `state` to a completed status.
- **Descriptions are durable, not precise**: behavioral contracts, acceptance criteria, explicit
  out-of-scope — never file paths, line numbers, or code snippets (they go stale).

## Feature → tickets structure (used by /to-tickets)

- A **feature** is a parent issue; its **tickets** are sub-issues (`parentId`).
- Tickets are tracer-bullet vertical slices: behavior + acceptance criteria + the rough seams
  agreed at ticket time. Seams are re-validated against current code when the ticket starts.
- **Dependencies** are native Linear relations (`blockedBy`) declared at creation time — never
  prose alone.
- **Frontier** = sub-issues with no open blockers; visible directly in the Linear UI.
- Every feature ends with one **journey-verification ticket**: verify the feature's user journey
  against the real backend — browser-driven (browser-use CLI) for UI journeys, CLI/script runs
  for non-UI subsystems (eval, ETL). Mocks (MSW) are for error/edge cases only, never the
  journey pass.
- **PR size cap: 300–800 net lines per PR.** If the feature's projected diff exceeds the cap,
  split the tickets into multiple PR batches at to-tickets time (one batch = one PR, each batch
  ends with its own verification gate).

## When a skill says "publish to the issue tracker"

Create a Linear issue in team Project-Dev via `save_issue`. Bugs filed from `/qa` get the `Bug`
label; attach the FinLab-X project when clearly feature-scoped.

## When a skill says "fetch the relevant ticket"

`get_issue` with the `DEV-XX` identifier (plus `list_comments` when discussion context matters).

## PR ↔ issue linking

PR bodies end with a trailing `Linear: DEV-XX` line — this creates the GitHub-integration link
that drives status automation (PR opened → `Human Code Review`; merged → `Merge & Deployed`).
The line must be in the body passed to `gh pr create`, not patched in afterwards. Branch names
stay clean (`<type>/<description>`, no issue ids).

## Wayfinding operations

Used by `/wayfinder`. The **map** is a parent issue labelled `wayfinder:map`; tickets are its
sub-issues labelled `wayfinder:<type>` (`research` / `prototype` / `grilling` / `task`).

- **Blocking**: native `blockedBy` relations between sub-issues.
- **Frontier query**: open sub-issues with no open blockers and no assignee; first in map order
  wins.
- **Claim**: assign the issue (`save_issue` with `assignee: "me"`) — the session's first write.
- **Resolve**: `save_comment` with the answer, move the ticket to a completed status, then append
  a one-line pointer to the map issue's Decisions-so-far section.
