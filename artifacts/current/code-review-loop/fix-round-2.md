# Fix Round 2

> Fixer: claude (code-fixer subagent) | Date: 2026-08-07
> Commit: `a8310231e6469d1ec30eae3964c170a6b76705f4`

## Adjudication (owner verdicts before dispatch)

| Issue ID | Verdict | Action |
|----------|---------|--------|
| M-2.1 | **Fix, option A** (owner-chosen): keep 429 fail-fast behavior; remove the false "edgartools retries 429" premise everywhere; amend envelope §2 to per-source rate-limit semantics in this PR (legitimate §11 channel); fix the stale test docstring that originated the claim | → FIX-A1/A2/A3 |
| ADR style (owner directive) | All three ADRs rewritten as forward-looking decision records (rules + rejected alternatives), never PR-description diff narrative. Recorded as durable feedback in orchestrator memory. | → FIX-A3 + FIX-B |
| m-2.1 | Fix — resolved by removing diff-content claims from ADR-0012 entirely (rule-statement instead) | → FIX-B |
| m-2.2 | Fix | → FIX-C |
| m-2.3 | Fix — resolved by the ADR-0013 rewrite (house-style sections) | → FIX-A3 |
| m-2.4 | Fix | → FIX-D |
| S-1.1 residual | Fix (class docstring) | → FIX-E |

## Fixer report

### Fixed

| Issue | How | Files |
|---|---|---|
| FIX-A1 (M-2.1) | Envelope §2 exception clause replaced with per-source semantics: Finnhub short-window → one bounded `Retry-After` backoff; EDGAR block-style 429 → pre-emptive client-side throttling + fail-fast with block surfaced. Lead sentence and trailing prohibition kept verbatim. | `docs/design-envelope.md` |
| FIX-A2 (M-2.1) | Docstring of `test_fetch_filing_obj_429_raises_rate_limit_error_immediately` rewritten to verified facts (edgartools 5.17.1 excludes 429 from its retry predicate; SEC 429 ≈ 10-min IP block, retry extends it; 8 req/s pre-emptive throttle). Test logic untouched; pinned contract unchanged. Repo-wide grep: no other stale claims. | `backend/tests/common/test_sec_core.py` |
| FIX-A3 (M-2.1, m-2.3) | ADR-0013 rewritten per forward-looking principle (276 words): Decision (single `retry_transient` policy + per-source 429 rule), compressed Context, governance exception (DEV-137 first consumer, removal conditions, DEV-141 seam correction), both Rejected alternatives, Re-evaluate triggers. False 429 claim and all diff narration removed. | `docs/adr/0013-single-tenacity-retry-policy.md` |
| FIX-B (m-2.1) | ADR-0011 (191 words) and ADR-0012 (231 words) rewritten as forward-looking rules + rejected alternatives. ADR-0012's frozen-tree line is now a rule; the false "only two handler-widening lines" claim removed. Cross-references kept; `backend/common/README.md` links verified correct. | `docs/adr/0011-repo-anchored-data-path-configuration.md`, `docs/adr/0012-unified-error-taxonomy-under-finlaberror.md` |
| FIX-C (m-2.2) | `TransientError` row no longer mentions rate limit; `RateLimitError` row added ("not retried — fail fast; carries `retry_after`"); extension example now uses shared `RateLimitError("yfinance", retry_after=...)` directly — no per-source subclass, never under `TransientError`. | `backend/ingestion/fundamentals_pipeline/README.md` |
| FIX-D (m-2.4) | S-1.1 finding restored verbatim (with orchestrator restoration note) after m-1.2, before "## Documentation Gaps". Nothing else changed. | `artifacts/current/code-review-loop/review-round-1.md` |
| FIX-E (S-1.1) | `FinLabError` class docstring narrowed to "Base of FinLab-X's shared error taxonomy (SEC and fundamentals families)." | `backend/common/errors.py` |

### Not Fixed

None.

### Tests Run

| Check | Result |
|---|---|
| `uv run ruff check --fix` + `ruff format` + `--check` | ✅ All pass, 175 files clean |
| `uv run pytest backend/tests/ -q` | ✅ 981 passed, 49 deselected |
| grep "exponential-backoff retries before\|edgartools already runs" backend/ docs/ | ✅ Zero hits |
| grep "bounded backoff, implemented once" docs/design-envelope.md | ✅ Zero hits (old wording gone) |
| ADR structure/word counts | ✅ 0011: 191w, 0012: 231w, 0013: 276w — all with bold Decision/Context/Rejected/Re-evaluate |
