# Fix Round 2

> Fixer: claude-opus (subagent, same fixer as round 1) | Date: 2026-07-21
> Commit: `78b401cd4520138bffcbc94fcbbc5462c95cda32` (docs-only, not pushed until confirmation round)
> M-2.2 disposition: **deferred to backlog by user decision** — retrieval-side commit-marker gating now owned by Linear DEV-92 (relatedTo DEV-73); DEV-73 annotated with the ingest-side/retrieval-side division of labor. Not dispatched to the fixer.

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-2.1 | Swept all 9 RAG-path "sentinel" prose occurrences to commit-marker vocabulary (term-only swaps, meaning/formatting/mermaid syntax preserved): `docs/agent_architecture.md` ×4 (L102 "commit markers"; L106 "embedding commit marker"; L113 mermaid node `ES{embedding commit marker complete in Qdrant?}`; L123 "Commit-marker points … A `complete` marker means…"), `docs/file_structure.md` ×1 (L48 "commit markers"), `backend/ingestion/sec_dense_pipeline/README.md` ×4 (L24 "commit-marker points"; L44 "Each **commit marker** stores…"; L78 "commit marker"; L80 "The commit marker transitions `pending` → `complete`."). Then simplified the CONTEXT.md **Commit marker** note to exactly `_Avoid_: sentinel point (legacy term)`. | `CONTEXT.md`, `docs/agent_architecture.md`, `docs/file_structure.md`, `backend/ingestion/sec_dense_pipeline/README.md` |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| M-2.2 | Not dispatched — user ruled defer-to-backlog: design-level retrieval-behavior change outside this docs/rename slice. Owned by DEV-92. |

### Reverted (fix broke tests)

| Issue ID | What Broke | Reverted Files | Suggested Alternative |
|----------|------------|----------------|----------------------|
| — | | | |

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `git diff --stat` (before commit) | ✅ Pass | Exactly 4 files changed (3 docs + CONTEXT.md), all prose. |
| Repo-wide `grep -rn -i sentinel` (md/py/ts/tsx, excl. node_modules) | ✅ Pass | Remaining hits: the five unrelated-concept files (frontend Markdown streaming sentinel; RunBudgetMiddleware error-message sentinel + test; `sec_core.py` `[Reserved]` sentinel + inflight test) plus the intentional `CONTEXT.md` `_Avoid_` note naming the legacy term. No RAG-path descriptive prose still says "sentinel". |

No pytest run: docs-only diff.

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| — | | |
