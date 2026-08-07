# Code Review Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-08-07

## Summary

| Metric | Count |
|--------|-------|
| Total NEW issues | 3 |
| Blocking | 0 |
| Major | 0 |
| Minor | 3 |
| Suggestion | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-2.1 | ⚠️ Partial | Envelope §2 amendment + rewritten test docstring verified accurate against vendored source; but the old backoff claim survived in `backend/common/sec_core.py` (`fetch_filing_obj` docstring: "edgartools' retry already exhausted") and `backend/agent_engine/docs/sec_core.md` ("edgartools' own backoff is exhausted"). Fixer's replacement wording had its own imprecision → m-3.1. |
| 2 | m-2.1 | ✅ Fixed | ADR-0012 diff-scope misstatements removed; forward-looking rules only. |
| 3 | m-2.2 | ✅ Fixed | `TransientError` row excludes rate limit; `RateLimitError` row added; extension guidance uses shared source-parameterized class. Consistent with `errors.py`. |
| 4 | m-2.3 | ⚠️ Partial | House-style sections present in all three ADRs, but ADR-0013's Context still narrated deleted-code characteristics ("one retried permanent failures and stacked on an inner retry... replaces them"). |
| 5 | m-2.4 | ✅ Fixed | S-1.1 restored with note; summary matches body. |
| 6 | S-1.1 (residual) | ✅ Fixed | Class docstring narrowed to shared SEC + fundamentals taxonomy. |

## New Issues

### [Minor] m-3.1: Replacement vendor claims are still imprecise
- **Files:** `backend/tests/common/test_sec_core.py` (new docstring), `docs/adr/0013-single-tenacity-retry-policy.md`
- **Problem:** The "8 req/s" figure comes from module globals in vendored `httprequests.py` that have no consumer there; the actual limiter is constructed in `httpclient.py` with a default of 9 req/s — the precise number is drift-prone. Also "waiting-then-retrying extends the block" overstates: only retrying BEFORE the block expires extends it.
- **Fix:** Say "throttles below the SEC cap" without the precise figure; narrow the extension claim to "retrying before the block expires extends it".

### [Minor] m-3.2: ADR-0012 reintroduces the universality claim removed from FinLabError
- **File:** `docs/adr/0012-unified-error-taxonomy-under-finlaberror.md`
- **Problem:** Rule says handlers wanting "any expected domain failure" catch `FinLabError` — contradicts the same ADR's Re-evaluate line and the JIT retriever's plain-`Exception` families. Same overclaim S-1.1 removed from the docstring.
- **Fix:** Narrow to "any expected failure in the shared SEC/fundamentals taxonomy".

### [Minor] m-3.3: ADR-0013's absolute retry rule contradicts its own exception
- **File:** `docs/adr/0013-single-tenacity-retry-policy.md`
- **Problem:** Decision says "All retry behavior" / "never a hand-rolled retry loop", but the same ADR (and the repo) preserves the frozen `_html` tree's hand-rolled loop until sunset.
- **Fix:** Scope the rule to new repo-owned transient-retry behavior and name the frozen exception in the Decision statement.

## Orchestrator disposition

All three new Minors plus the two Partials are residuals of already-adjudicated owner verdicts (option A "remove the false claim everywhere"; the ADR forward-looking style directive; the S-1.1 narrowing). Applied directly by the orchestrator as fix round 3 (see `fix-round-3.md`) and verified mechanically: repo-wide greps for every stale phrase return zero hits; full suite 981 passed; ruff clean.
