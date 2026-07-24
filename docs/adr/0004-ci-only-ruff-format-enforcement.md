# ADR-0004: CI is the only ruff-format enforcement mechanism (2026-07-24)

**Decision**: `ruff format --check backend/` in CI's lint job is the sole gate
enforcing backend formatting. No pre-commit hook, no editor format-on-save.
`AGENTS.md` instructs contributors to run `ruff format backend/` before pushing,
but nothing local enforces it — the CI gate is the only hard stop.

**Rejected — pre-commit hook**: requires each clone to run `pre-commit install`
before it takes effect. The drift this ADR responds to was found alongside a
worktree-bootstrap bug that skipped installing ruff entirely; layering another
opt-in mechanism onto an environment where auto-install has already proven
unreliable means it silently no-ops in some worktrees and manufactures false
confidence. Opt-in local machinery is envelope §3 ceremony here.

**Rejected — editor format-on-save**: most code in this repo is written by
agents through file-write tools, which never fire an editor save event. It would
protect the least-travelled write path.

**Why**: the CI gate already makes unformatted code impossible to merge. The
other two mechanisms change only *how early* drift is caught, not *whether* it
reaches main — they buy earlier feedback at the cost of setup that this repo's
environment cannot reliably guarantee. **Reopen when** a human-authored editing
workflow becomes the dominant write path, or bootstrap reliably provisions the
toolchain in every worktree — either makes a local hook pay for itself.
