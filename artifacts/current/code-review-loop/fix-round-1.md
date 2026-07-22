# Fix Round 1

> Fixer: claude-opus-4-8 (orchestrator-applied) | Date: 2026-06-09

Round-1 verdict was **APPROVE WITH NITS** (0 Blocking, 0 Major, 4 Minor, 3 Suggestion).
Applied the two "worth fixing now" items plus two cheap polish items; deferred the rest with rationale.

## Fixed

| Issue | Status | File | Change |
|-------|--------|------|--------|
| m-1.1 | ✅ Fixed | `finnhub_client.py` | `marketCap` description `"Market capitalization (USD millions)"` → `"...(millions of reporting currency)"`. Finnhub returns reporting-currency millions, not unconditionally USD — the prompt's own TSM (Taiwan) example would have surfaced a wrong currency claim under the zero-hallucination policy. |
| m-1.2 | ✅ Fixed | `tools/README.md` | Line 6 no longer mis-attributes Finnhub to `financial.py` (now described as Tavily-only). Added two Map bullets for the new `finnhub_tools.py` and `finnhub_client.py`. |
| m-1.4 | ✅ Fixed | `finnhub_client.py` | Added a one-line WHY comment at the all-zero guard in `fetch_quote` explaining the `c AND pc` zero-check (free-tier unknown-ticker signal; `c`-alone would false-positive a pre-market zero). |
| S-1.1 | ✅ Fixed | `test_finnhub_tools.py` | New opt-in `test_live_catalog_metric_keys_resolve` asserts ≥17/19 curated catalog metric keys resolve live for AAPL — converts the one-time manual 19-key validation into a regression guard against silent catalog-key typos. |

## Deferred (accepted as-is)

| Issue | Decision | Rationale |
|-------|----------|-----------|
| m-1.3 (None vs absent symmetry) | Won't fix | Reviewer-confirmed acceptable: the discovery tool and data tool apply the identical None-filter, so the agent's view is internally coherent. Token-efficient present-only contract is intentional. |
| S-1.2 (FinnhubAPIException bubbles raw) | Won't fix | Functionally correct and consistent with the SEC tools' contract; 429 reaches `_HandleToolErrors` and surfaces as `ToolMessage(status="error")`. Status-code mapping is YAGNI for this PR. |
| S-1.3 (stream event before fetch; writer-present path untested) | Won't fix | Cosmetic; matches the prior yfinance tools' streaming pattern. |

## Verification

- `uv run --extra dev pytest backend/tests/ -q` → **820 passed, 48 deselected**.
- `uv run --extra dev pytest backend/tests/tools/test_finnhub_tools.py -m finnhub_integration -q` → **4 passed** (incl. new catalog guard).
- `uv run --extra dev ruff check finnhub_client.py test_finnhub_tools.py` → clean.

## Round-2 re-review

Waived. All four fixes are documentation / description-string / comment / new-test changes with **no change to any production logic path** that round 1 reviewed (the `marketCap` value mapping is unchanged; only its human-readable description changed). Test suite + ruff confirm no regression. Re-dispatching the 3-lens panel would consume tokens for negligible risk reduction.
