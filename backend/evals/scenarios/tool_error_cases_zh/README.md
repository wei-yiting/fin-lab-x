# tool_error_cases_zh

Purpose-built rows for measuring whether tool error messages change agent
behavior. Built and frozen on 2026-10-27, **before** any error message was
changed, so the rows were not chosen to flatter the new messages.

- 24 error rows, 6 per class, each naming a trigger that was confirmed to fire
  by calling the tool directly (no model): `probe_before.json` holds every probe
  with the exact message the model saw at the time.
  - `a_non_10k_filer`: 20-F / 40-F filers. SEC tools fail. Finnhub and news still work.
  - `b_non_us_listing`: non-US listing symbols. Finnhub returns 403 and SEC does not know the symbol.
  - `c_missing_section_or_year`: the 10-K exists but the requested item or fiscal year does not.
  - `d_invalid_or_delisted`: unknown or delisted tickers.
- 6 control rows (ids 25–30) are copies of `baseline_behavior_diagnostic_zh`
  rows 3, 11, 16, 20, 25 and 28 (`source_row_id`). None of them hit a tool error in
  any of the 3 luna_medium reps of the 2026-10-22 benchmark.
- Mostly Traditional Chinese, with 5 English rows (`language`).

Columns beyond the diagnostic schema:

| Column | Meaning |
|---|---|
| `error_class` | One of the four classes above, or `control` |
| `trigger_tickers` | Ticker(s) the question is about |
| `expected_failures` | JSON list of `{tool, args, exc_type, message}` from the probe, where `message` is the pre-contract text |
| `failing_sources` | Provider(s) expected to fail (`sec`, `finnhub`, or `sec_section_or_year`) |
| `acceptable_alternatives` | `|`-separated tool globs that count as recovering. `glob:TICKER` restricts the glob to one ticker |
| `must_state_gap` | Whether the answer must tell the user which data is unavailable |

Dropped candidates (trigger did not fire): SHOP (now files a 10-K), BBBY (ticker
reused by another 10-K filer), FB / PARA (Finnhub returns some other security),
JPM / BAC / C / GE / WFC Item 7 (present), MSFT FY2021 Item 1C (returned content).

`split.json` is stratified by `error_class` (seed 20261027, 3 design + 3
held-out per class). Only design rows were looked at while writing the new
messages. Rebuild with
`uv run python -m backend.evals.experiments.tool_error_messages.build_dataset --probe <probe.json> --out-dir <dir>`.
