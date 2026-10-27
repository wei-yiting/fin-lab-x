# Retry-guard diagnosis — is "agent retries a failing tool" worth fixing?

> **One-line takeaway:** No fix was warranted. Across the 540 runs of the two
> 2026-10-22 benchmarks, the agent **never** repeated an identical (tool, args) call
> after it failed, so repeats explain **0 of the 25 runs that reached the 10-call
> budget**. The behaviour was real only in the 2026-10-21 dev round (2 of 8
> `luna_medium` runs), where every SEC failure surfaced as an opaque
> `'NoneType' object has no attribute 'sections'` from the edgartools bug (DEV-219).
> What fills the budget now is per-entity fan-out on comparison questions.

Decision: the planned guard (block a (tool, normalized args) pair that already
failed in the run) was **not built**, and the re-measurement run was not spent.

## Reproduce

| | |
|---|---|
| Branch | `feat/agent-retry-guard`, cut from `feat/model-reasoning-benchmark` @ `08d1c13` |
| Inputs | `2026-10-21-agent-config-benchmark-dev/raw/` (branch `feat/dev-206-config-selectable-diagnostic-task`), `2026-10-22-model-reasoning-benchmark/raw.tar.gz`, `2026-10-22-rag-bundle-ablation/raw.tar.gz` (branch `feat/rag-bundle-ablation`). Extract the tarballs into an empty directory first. |
| Command | `python -I diagnose_repeats.py --out per_run.csv 2026-10-21-dev=<raw> 2026-10-22-model-reasoning=<raw> 2026-10-22-rag-ablation=<raw>` |
| Cost | $0 (archived records only, no model calls) |

## 1. Question

The deck's Improve section lists "agent retries a failing tool and burns its budget"
as an observed, unfixed failure. The evidence was D3 in the 2026-10-21 report:
`luna_medium` called `sec_filing_list_sections` on V three times in one run, and in
the 2026-10-22 benchmark `luna_medium` reached the tool budget in 9 of 90 runs.

Before writing a guard: **how many budget hits do repeated failing calls actually
explain?** The pre-agreed stop rule was "if repeats explain few budget hits, stop and
report instead of fixing".

## 2. Definitions

- **Hard error**: a tool call whose result carries an error, excluding the
  budget-blocked message from `RunBudgetMiddleware`.
- **Repeat after error**: a call whose (tool, normalized args) already returned a hard
  error earlier in the same run. Normalization drops `None`/empty args, strips
  strings and upper-cases `ticker`. `fiscal_year=None` and an explicit year stay
  distinct, because the tool resolves them to different requests. This is exactly the
  key the proposed guard would have used, so the count is the guard's upper bound on
  calls saved.
- **Reached tool budget**: `analyze.py`'s definition: at least one budget-blocked call,
  or 10 or more calls. "Blocked" is the stricter subset where the agent actually
  asked for an 11th call.

## 3. Results

| Round | Arm | Runs | Runs w/ hard error | Runs w/ repeat after error | Repeat calls | Runs at budget | …of which blocked | Budget runs w/ repeat | Budget runs w/ ≥2 tickers |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-21-dev | gemini_medium | 8 | 1 | 0 | 0 | 1 | 0 | 0 | 1 |
| 2026-10-21-dev | gemini_minimal | 8 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2026-10-21-dev | luna_medium | 8 | 2 | **2** | 2 | 2 | 1 | **2** | 2 |
| 2026-10-21-dev | luna_none | 8 | 3 | 0 | 0 | 1 | 0 | 0 | 1 |
| 2026-10-21-dev | reader_luna_medium | 8 | 3 | 0 | 0 | 1 | 1 | 0 | 1 |
| 2026-10-22-model-reasoning | gemini_medium | 90 | 0 | 0 | 0 | 2 | 1 | 0 | 2 |
| 2026-10-22-model-reasoning | gemini_minimal | 90 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2026-10-22-model-reasoning | luna_medium | 90 | 8 | **0** | 0 | 9 | 2 | **0** | 9 |
| 2026-10-22-model-reasoning | luna_none | 90 | 7 | 0 | 0 | 6 | 2 | 0 | 6 |
| 2026-10-22-rag-ablation | luna_medium | 90 | 6 | 0 | 0 | 6 | 1 | 0 | 6 |
| 2026-10-22-rag-ablation | reader_luna_medium | 90 | 6 | 0 | 0 | 2 | 0 | 0 | 2 |

Per-run rows are in [`per_run.csv`](per_run.csv) (580 runs).

### What the numbers say

1. **The failure no longer occurs.** In 540 post-fix runs, 30 runs hit a hard error
   and none of them repeated the failing call. The guard would have saved 0 calls and
   changed 0 of the 25 budget hits.
2. **When it did occur, the error message was opaque.** All 2026-10-21 repeats
   followed `'NoneType' object has no attribute 'sections'`: edgartools failing on
   every uncached 10-K (DEV-219, fixed by the upgrade to 5.62). The message reads like
   a transient fault, so retrying it once is a reasonable move. Post-fix errors name
   the cause and the next step ("files 20-F; only '10-K' is supported", "Section '7'
   not found … call `sec_filing_list_sections` first"), and the agent never repeated the failing call. Its next call on
   that ticker switched tool or changed args (luna_medium 2026-10-22:
   switched tool 9, changed args 3, no further call 1). In the V example, only 2 of the 3
   calls were identical: the third passed `fiscal_year=2024`, which the guard would
   not have blocked.
3. **Budget hits are fan-out, not loops.** Every one of the 25 budget runs in the
   2026-10-22 rounds touched two or more tickers, typically quote + financials +
   news + list_sections + 1–2 sections *per company*. Only 6 of them actually asked
   for an 11th call. The other 19 stopped at exactly 10, which fits the system prompt
   telling the agent its budget up front.
4. **"9 of 90" overstates the binding budget.** Under the stricter "blocked"
   definition, `luna_medium` hit the budget in 2 of 90 runs, not 9.

## 4. Why the guard was not built anyway

- **Zero measured benefit** on the current tools. A re-run would have spent
  ≈ US$1.5 to measure a null effect with no possible upside in the target metric.
- **It would add a failure mode.** A run-scoped "never retry a failed pair" rule also
  blocks retries of genuinely transient errors (timeouts, 429s, a flaky EDGAR fetch).
  Getting this right requires classifying errors as transient vs permanent, which is
  more design than a one-line guard.
- **The upstream fix already landed.** DEV-219 removed the opaque error at its source,
  and the tools now return actionable messages. Error-message quality, not a loop
  guard, is the lever the data points to. That is a hypothesis: the 2026-10-21
  evidence is 2 runs, and only `luna_medium` repeated, although other arms saw the
  same opaque error.

## 5. Claim boundary

- **Observational, archived runs only.** No intervention was run, so this shows the
  guard would have had nothing to act on in these 540 runs. It does not show the
  failure can never come back: a new tool with an opaque error could bring it back.
- **The opaque-message explanation is correlational** and rests on 2 runs in an 8-row,
  single-repetition round. The edgartools fix changed both the message and the
  underlying failure, so the two can't be separated with this data.
- **Same 30-question zh diagnostic set** as the source benchmarks (US equities plus a
  few non-US tickers), with live inputs on 2026-10-21/22. All their caveats apply:
  holdout rows not withheld, 6-way concurrency, process metrics only.
- **The repeat key is exact after normalization.** Semantic near-repeats
  (`AIR.PA` → `AIR`, a reworded Tavily query) are deliberately not counted. They are
  different requests and the proposed guard would not have blocked them either.

## 6. Follow-ups (not done here)

- If budget hits matter, test the fan-out hypothesis directly: compare budget-hit rate
  on single- vs multi-entity rows, or try a budget that scales with the number of
  entities. Only 6 of 540 runs were actually blocked, so this is low priority.
- Consider reporting `budget_blocked` next to `reached_tool_budget` in `analyze.py`,
  so a run that stops at exactly 10 calls isn't read as a blocked run.
