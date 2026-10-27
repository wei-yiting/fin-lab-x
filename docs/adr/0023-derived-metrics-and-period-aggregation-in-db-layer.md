# ADR-0023: Derived metrics and multi-quarter aggregation live in the database layer, not the prompt (2026-10-27)

**Decision**: Ratios computed from stored columns (gross / operating / net / FCF margin, R&D
intensity, debt-to-equity, current ratio) are defined once in DuckDB views —
`quarterly_metrics` and `annual_metrics` — which also map each fiscal quarter to a calendar
quarter by its middle month. Multi-quarter windows go through one table macro,
`period_metrics(year, q_from, q_to)`, which encodes the aggregation rules: flow amounts sum,
balance-sheet amounts take the window's last quarter, ratios are recomputed from the summed
parts, and `quarters_covered` / `quarters_expected` expose partial windows — for which every
amount and ratio is NULL, so a partial sum can never be ranked against a full one (found in
the prototype's first live run: a 1-of-3-quarter 2025 window produced a fake +254% "growth"
leader). The text-to-SQL LLM
sees these objects (plus `companies` and `market_valuations`) instead of the raw financial
tables. This resolves the derived-metric question that Design Master §13.3 deferred to the
text-to-SQL design.

**Rejected**:

1. **LLM writes the formulas from prompt instructions.** No extra schema objects, but a prompt
   rule is advisory: the model may average margins across quarters, sum balance-sheet items,
   or define a ratio differently from one run to the next. None of that is unit-testable.
2. **Store derived values as ETL columns.** Goes stale when a base column is re-ingested, and
   cannot serve arbitrary user-chosen windows.

**Why**: Formulas and aggregation rules are deterministic domain knowledge, so they belong
where they can be tested and give the same result every time. The prompt keeps only
*interpretation*: mapping the user's words ("2026 前三季", "FY2026", "last quarter") onto the
right object and window. A plain view cannot take a query-time window, so the windowed rules
use a table macro (a parameterized view), which persists in the database file, carries a
`COMMENT`, is callable on a read-only connection, and parses as a `SELECT` for the read-only
guard.

**Consequences**:

- `period_metrics` covers windows within one calendar year only; cross-year windows and TTM are
  out of scope until data depth (yfinance holds ~5 quarters) makes them meaningful.
- Adding a derived metric means editing `schema.sql` (view definition + column comment), not the
  prompt.
