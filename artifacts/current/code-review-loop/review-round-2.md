# Code Review Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-07

## Summary

| Metric | Count |
|--------|-------|
| Total NEW issues | 5 |
| Blocking | 0 |
| Major | 1 |
| Minor | 4 |
| Suggestion | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | B-1.1 | ✅ Fixed | Integration test renamed, asserts `"failed"`, and pins FAIL_TICKER `process()` call count == 1. Not executed locally (Qdrant unavailable) but seam and assertion verified consistent. |
| 2 | M-1.1 | 🚫 Dismissed-by-owner (accepted) | Owner sanctioned this slice's `sec_core` contract changes. |
| 3 | M-1.2 | 🚫 Dismissed-by-owner (accepted) | Owner sanctioned the frozen-tree changes. ADR misdescription of the actual scope filed separately as m-2.1. |
| 4 | M-1.3 | 🚫 Dismissed-by-owner (accepted) | ADR-0013 records the time-boxed §0 exception; DEV-137/DEV-69 carry removal conditions. |
| 5 | M-1.4 | ⚠️ Partially Fixed | `stop_after_attempt(2)` + tests correct; but the ADR's 429 reconciliation rests on a false edgartools premise → M-2.1. |
| 6 | M-1.5 | 🚫 Dismissed-by-owner (accepted) | Deferred to DEV-137, recorded in its description. |
| 7 | M-1.6 | ✅ Fixed | Fused ADR split into three one-decision ADRs (~346-372 words each). Old filename's only grep hit is the historical round-1 record, not a live link. House-style gap filed as m-2.3. |
| 8 | m-1.1 | ✅ Fixed | `--max-retries` removed from example + table; current failure semantics documented. |
| 9 | m-1.2 | ✅ Fixed | `with_retry`/deleted-module references gone; module ownership current. New taxonomy misstatement filed as m-2.2. |
| 10 | S-1.1 | ⚠️ Partially Fixed | Module docstring narrowed, but the `FinLabError` **class** docstring still claims "all FinLab-X domain errors". |

## New Issues

### [Major] M-2.1: ADR-0013's edgartools 429-backoff premise is contradicted by the pinned version's implementation
- **File:** `docs/adr/0013-single-tenacity-retry-policy.md` L17
- **Problem:** The ADR claims edgartools runs exponential backoff before any 429 reaches this layer, pinned by `test_fetch_filing_obj_429_raises_rate_limit_error_immediately`. In pinned edgartools 5.17.1, `TooManyRequestsError` is NOT in `RETRYABLE_EXCEPTIONS` and `should_retry()` returns False for it — 429 is fail-fast at the vendor layer too. The cited test mocks `get_filings` to throw directly and asserts one call/no sleep; it bypasses the edgartools retry layer entirely and pins only this repo's fail-fast.
- **Fix:** Remove the false claim; re-ground the owner-accepted §2 reconciliation in the pinned version's actual behavior, or return it to the owner for re-adjudication rather than treating M-1.4 as closed.
- **Orchestrator verification:** CONFIRMED against vendored source (`.venv/.../edgar/httprequests.py`): `TooManyRequestsError` absent from `RETRYABLE_EXCEPTIONS`; its docstring documents SEC 429 ≈ 10-min IP block and "Do NOT retry immediately"; pre-emptive throttle exists (`max_requests_per_second = 8`, enabled by default). Codex is right; the false claim originated in a pre-existing test docstring on main and was propagated into the ADR unverified. Surfaced to owner → **owner chose option A**: keep fail-fast behavior; rewrite ADR-0013 truthfully; fix the stale test docstrings; amend envelope §2 to per-source rate-limit semantics in this same PR (legitimate §11 channel).

### [Minor] m-2.1: ADR-0012 misstates the frozen tree's change scope
- **File:** `docs/adr/0012-unified-error-taxonomy-under-finlaberror.md` L25
- **Problem:** Claims the `_html` tree "receives only the minimal handler-widening lines" / "everything else there is untouched"; the sanctioned refactor also changed a path default, a constructor signature, and a dataclass field type.
- **Fix:** Stop making diff-content claims in the ADR; state the forward-looking rule instead. (Resolved by the owner-directed ADR style rewrite.)

### [Minor] m-2.2: Fundamentals README still classifies rate limits as TransientError
- **File:** `backend/ingestion/fundamentals_pipeline/README.md` L51, L78
- **Problem:** API table says `TransientError` covers rate limits, and the extension example instructs `YFinanceRateLimitError(TransientError)` — following it would make `retry_transient` retry rate limits, contradicting the taxonomy and retry policy.
- **Fix:** Remove rate limit from `TransientError`'s description; add a `RateLimitError` row; example uses the shared source-parameterized `RateLimitError` directly.

### [Minor] m-2.3: ADR-0013 lacks the house-style Context section
- **File:** `docs/adr/0013-single-tenacity-retry-policy.md` L15
- **Fix:** Add a bold `**Context**` section. (Resolved by the rewrite.)

### [Minor] m-2.4: Round-1 audit record omits S-1.1's original finding
- **File:** `artifacts/current/code-review-loop/review-round-1.md` L9
- **Problem:** Summary counts 1 Suggestion; body has no S-1.1 heading, yet the fixer report references fixing it — audit trail incomplete.
- **Fix:** Restore the original S-1.1 finding verbatim.

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| tenacity | 9.1.4 | `stop_after_attempt(2)`, `retry_if_exception_type`, `.retry_with(wait=wait_none())`, `reraise=True` | ✅ Current | `stop_after_attempt` counts total attempts; usage correct. |
| edgartools | 5.17.1 | `get_with_retry`, `TooManyRequestsError`, 429 handling | ❌ Wrong (documentation claim, not code) | Pinned version's retry predicate excludes `TooManyRequestsError`; the ADR/test-docstring claim of internal 429 backoff is incorrect. Code behavior itself is fine. |

---

# Spec Conformance Round 2

> Reviewer: claude-fable-5 | Date: 2026-08-07

## Summary

| Metric | Count |
|--------|-------|
| Previous findings resolved | 2/2 |
| New findings | 0 |

## Previous Findings Status

| Issue ID | Status | Evidence |
|----------|--------|----------|
| SP-1.1 | ✅ Fixed | Test asserts `"failed"` (matches script emission); renamed `test_batch_cli_failure_isolation_and_summary`; exactly-once assertion correct (script calls `pipeline.process(ticker, "10-K", year)` positionally → `call.args[0]` counting valid); repo-wide grep shows zero remaining embed-script-related `"skipped"` references. |
| SP-1.2 | ✅ Fixed | Verified on both surfaces: ADR-0013 carries the testing-seam note; DEV-141 (fetched live) carries the matching dated Testing Decisions correction. The two records agree. |

## New Findings

None found.

## Amended-Spec Conformance

- ✅ `stop_after_attempt(2)` — `backend/common/retry.py`, docstring cites §2
- ✅ Tests assert 2-attempt behavior; no stale 3-attempt assertions outside the frozen tree
- ✅ 429 fail-fast + §2 reconciliation documented in ADR-0013 (note: reconciliation text superseded by M-2.1's option-A rewrite)
- ✅ Docs consistent (`backend/common/README.md` retry row: 2 attempts, ADR-0013 link)

## Regression Sweep

Taxonomy single-definition intact; `RateLimitError` still generic; frozen tree untouched by the fixer commit; ADR cross-references consistent. One observation folded back by the orchestrator: DEV-141's "恰好 3 attempts" phrase clarified in-place as frozen-tree-only behavior (Linear description patched 2026-08-07).
