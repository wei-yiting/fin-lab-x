# Fix Round 1

> Fixer: claude (code-fixer subagent) | Date: 2026-08-06
> Commit: `a6eadae9c8378c96a61b1a2be3f21d5200063065`

## Adjudication (user verdicts before dispatch)

| Issue ID | Verdict | Action |
|----------|---------|--------|
| B-1.1 / SP-1.1 | Fix | → FIX-1 |
| M-1.1 | **Dismissed by user** — this slice IS the sanctioned refactor; AGENTS.md freeze/only-add restrictions ruled not applicable to it | No code change |
| M-1.2 | **Dismissed by user** — same rationale as M-1.1 | No code change |
| M-1.3 | **Dismissed with conditions** — dependency (DEV-137, blockedBy this issue, landing within days) is concrete, so envelope §0 exception stands; conditions recorded | Orchestrator added ⚠️ removal-check clauses to DEV-137 + DEV-69 descriptions |
| M-1.4 | Fix (option A: conform to envelope §2) | → FIX-2; 429 fail-fast retained with §2 reconciliation documented in ADR-0013 |
| M-1.5 | **Deferred to DEV-137** — vectorizer/dense tree is sunset-bound (DEV-139) and batch-script rewrite is DEV-137's chartered work; §2 sanctions manual retry for operator tools meanwhile | Orchestrator recorded the gap + assignment in DEV-137 description |
| M-1.6 | Fix (user confirmed the ADR fuses three decisions) | → FIX-3 |
| SP-1.2 | Fix via documentation (keep tests, amend spec) | Orchestrator patched DEV-141 Testing Decisions with dated correction; ADR-0013 carries the seam note |
| m-1.1 | Fix | → FIX-4 |
| m-1.2 | Fix | → FIX-5 |
| S-1.1 | Fix | → FIX-6 |

## Orchestrator-side actions (Linear, done in parallel with fixer)

- **DEV-137** description: new「前置資產（DEV-141 預建）」section — `retry_transient` first-consumer designation, ⚠️ removal-check clause (if unused by completion and no other consumer exists, remove retry.py + tests + tenacity dep), M-1.5 embed/Qdrant transient-classification assignment.
- **DEV-69** description: same-format section — `retry_transient` + genericized `RateLimitError` ready for Finnhub; `Retry-After` pacing is this ticket's §2 fulfillment; same ⚠️ removal-check clause.
- **DEV-141** spec folded: Implementation Decisions `stop_after_attempt(3)` → `(2)` with dated M-1.4 correction citing §2/ADR-0013; Testing Decisions gained dated SP-1.2 correction authorizing `test_retry.py` as second new seam.

## Fixer report

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| FIX-1 (B-1.1/SP-1.1) | `"skipped"` assertion → `"failed"`; added proof `FAIL_TICKER` attempted exactly once via `fake_pipeline.process.call_args_list` (ticker is positional `args[0]`). Renamed test to `test_batch_cli_failure_isolation_and_summary` (no other references to old name). | `backend/tests/ingestion/sec_dense_pipeline_html/integration/test_ingest.py` |
| FIX-2 (M-1.4) | `stop_after_attempt(3)` → `(2)`; docstring "up to 2 attempts total (single retry, per design-envelope §2)"; tests updated (success on attempt 2; exhaustion `== 2`; non-transient unchanged `== 1`). Common README retry row updated too. | `backend/common/retry.py`, `backend/tests/common/test_retry.py` |
| FIX-3 (M-1.6) | Fused ADR deleted; three ADRs written (house style, cross-referenced): 0011 repo-anchored paths / 0012 error taxonomy / 0013 retry policy (incl. §2 reconciliation, §0 ratification, SP-1.2 seam note). Common README links repointed. No stale references remain. | `docs/adr/0011-repo-anchored-data-path-configuration.md`, `docs/adr/0012-unified-error-taxonomy-under-finlaberror.md`, `docs/adr/0013-single-tenacity-retry-policy.md`, `backend/common/README.md` (old fused file deleted) |
| FIX-4 (m-1.1) | Removed `--max-retries` example + table row; documented current semantics (retry inside `SECFilingPipeline.process`, failures show `failed`, exit 1). | `backend/scripts/README.md` |
| FIX-5 (m-1.2) | Removed `with_retry` row; shared error classes' module column → `backend.common.errors`; "retry.py is pipeline-scoped" line replaced with pointer to `backend/common/retry.py` + ADR-0013. agent_architecture bullet rewritten to current reality. | `backend/ingestion/fundamentals_pipeline/README.md`, `docs/agent_architecture.md` |
| FIX-6 (S-1.1) | Docstring narrowed: `FinLabError` is the shared base for the SEC and fundamentals error families (no repo-wide universality claim). | `backend/common/errors.py` |

### Not Fixed (with reason)

None.

### Reverted (fix broke tests)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run ruff check --fix backend/` | ✅ Pass | No issues |
| `uv run ruff format backend/` + `--check` | ✅ Pass | Reformatted renamed test def line; check clean |
| `uv run pytest backend/tests/ -q` | ✅ Pass | 981 passed, 49 deselected |
| `uv run pytest backend/tests/common/test_retry.py -q` | ✅ Pass | 3 passed |
| Integration test (renamed) | ⚠️ Not run | Qdrant unavailable locally (curl 000); assertion change verified by inspection — script emits `"failed"`, calls `pipeline.process(ticker, ...)` positionally so `call.args[0]` is the ticker. Will run in CI's integration step. |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/ingestion/sec_dense_pipeline_html/integration/test_ingest.py` | Modified (renamed → `test_batch_cli_failure_isolation_and_summary`) | Summary prints `failed` (not `skipped`), exit 1, permanently-failing ticker attempted exactly once (outer retry gone) |
| `backend/tests/common/test_retry.py` | Modified | Policy now 2 attempts total: success on attempt 2, exhaustion after 2, non-transient still 1 |

Note: `artifacts/` is gitignored; staged with `git add -f` per project convention (commit on branch during work, untrack pre-PR).
