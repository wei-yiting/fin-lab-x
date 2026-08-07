# Fix Round 3

> Fixer: claude (orchestrator-applied) | Date: 2026-08-07
> Rationale for orchestrator-direct application: all five items are residuals of already-adjudicated owner verdicts (option A "remove the false claim everywhere" / ADR forward-looking style directive / S-1.1-type wording narrowing) — no new decisions, doc-only edits with grep-verifiable outcomes. Per the loop's minor-only path, verified mechanically at final verification instead of a fourth reviewer round.

## Issues addressed

| Issue | Origin | How Fixed | Files |
|---|---|---|---|
| M-2.1 residual (a) | Round 3 status table | `fetch_filing_obj` docstring: "429; edgartools' retry already exhausted" → "429; surfaced immediately with `retry_after` — edgartools does not retry rate limits" | `backend/common/sec_core.py` |
| M-2.1 residual (b) | Round 3 status table | Companion doc's "edgartools' own backoff is exhausted" design note rewritten: edgartools does not retry 429; honors the limit pre-emptively via throttling; retrying before block expiry extends it | `backend/agent_engine/docs/sec_core.md` |
| m-3.1 | Round 3 | Drift-prone "8 req/s" dropped from test docstring and ADR-0013 ("throttles below SEC's rate cap"); "retrying extends it" narrowed to "retrying before it/the block expires extends it" in both | `backend/tests/common/test_sec_core.py`, `docs/adr/0013-single-tenacity-retry-policy.md` |
| m-3.2 | Round 3 | ADR-0012 rule narrowed: "any expected failure in the shared taxonomy" + explicit pointer that outside families (JIT retriever) are not covered | `docs/adr/0012-unified-error-taxonomy-under-finlaberror.md` |
| m-3.3 | Round 3 | ADR-0013 Decision scoped to "All new repo-owned transient-retry behavior", frozen `_html` exception named inline in the Decision statement | `docs/adr/0013-single-tenacity-retry-policy.md` |
| m-2.3 residual | Round 3 status table | ADR-0013 Context stripped of deleted-code characteristics: "retry logic had been reimplemented independently in three places with divergent semantics; nothing enforced a single policy" | `docs/adr/0013-single-tenacity-retry-policy.md` |

## Verification

| Check | Result |
|---|---|
| `uv run ruff check --fix backend/` | ✅ All checks passed |
| `uv run ruff format backend/` + `--check` | ✅ 175 files clean |
| `uv run pytest backend/tests/ -q` | ✅ 981 passed, 49 deselected |
| grep "edgartools' retry already exhausted \| edgartools already runs \| exponential-backoff retries before \| 8 req/s" across backend/ docs/ (excl. .venv) | ✅ ZERO HITS |
| ADR word counts | ✅ 0011: 191w / 0012: 251w / 0013: 293w, house-style sections intact |
