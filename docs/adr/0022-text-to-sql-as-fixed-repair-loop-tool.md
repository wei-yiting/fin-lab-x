# ADR-0022: Text-to-SQL is a tool with an internal fixed generate–validate–execute–repair loop (2026-10-27)

**Decision**: The `quant` profile reaches the fundamentals store through one Orchestrator tool,
`company_fundamentals_query(question)`. The Orchestrator passes a self-contained English question; inside the
tool a fixed loop runs: an LLM writes DuckDB SQL from the LLM-visible schema (column
`COMMENT`s) and a dedicated SQL prompt → the SQL is validated as a single read-only `SELECT` →
executed on a read-only connection → on a validation or execution error the error text is fed
back for a rewrite, at most 3 attempts. The tool returns evidence (`status`, final `sql`,
`rows`, failed `attempts`), never prose. An empty result is a valid answer and is **not**
retried. Decided in the text-to-SQL grilling session (2026-10-27).

**Rejected**:

1. **Orchestrator writes SQL; the tool only validates and executes.** Simplest (one LLM), but
   every Orchestrator turn carries the full schema plus SQL-writing rules, and each repair
   round-trip pollutes the main context and spends the per-run tool-call budget.
2. **A ReAct sub-agent with its own tools** (`list_tables`, `run_sql`, …). More flexible, but
   needs its own budget, stop conditions and tracing, and is harder to test and explain. A
   fixed loop delivers the needed benefits; upgrade only when evals show the loop is the
   bottleneck.

**Why**: ADR-0018 set the threshold for moving work out of the Orchestrator loop at *context
isolation*, not capability domain. RAG failed that threshold (one retrieval, the chunks *are*
what the Orchestrator must read). Text-to-SQL passes it: a multi-attempt repair trajectory and
a schema the Orchestrator never needs to read. ADR-0018's objection to generation inside a tool
(prose instead of evidence) does not apply because this tool returns rows and SQL. The isolated
question → SQL → result unit is also independently evaluable (execution accuracy) without
running the whole Orchestrator.

**Consequences**:

- The tool is named for what it queries (`company_fundamentals_query`), not for the technique
  (text-to-SQL), following the other tools (`sec_filing_search` is not called `rag`): the
  Orchestrator routes on the data source, and the method behind it may change.

- Follow-up questions work only if the Orchestrator rewrites them into self-contained
  questions; the inner LLM does not see the conversation.
- Retrying only on errors means a wrong-but-valid query that returns 0 rows is not
  auto-corrected; `no_rows` results carry store coverage so the Orchestrator can tell
  "absent data" from "bad query".
- Each attempt runs as a named LangChain runnable so both Langfuse (runtime) and Braintrust
  (eval experiments) receive the same nested trace.
- The inner model is a module constant for now; moving it into the Workflow Profile config is
  a tracked follow-up.
