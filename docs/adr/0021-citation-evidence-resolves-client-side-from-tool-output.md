# ADR-0021: Citation evidence resolves client-side from tool output, not a UI-only artifact channel (2026-10-27)

*(Partially revises ADR-0020. Decided in the DEV-229 grilling session.)*

**Decision**: A **Citation block** — the expandable entry behind an evidence `[N]` — is built in
the frontend by joining the model's reference definition (`[N]: sec://…` / `[N]: sql://…`) against
the tool results of the **same assistant message**, which already reach the client as the tool
part's `output` (`tool-output-available`). The evidence shown is exactly what the model read:
SEC chunk text, title, fiscal year and fiscal-year end for `sec://`; the `text_to_sql` result
(columns, rows, tables, **Derivations**) for `sql://{toolCallId}`. No new stream part is added
and the streaming contract is unchanged. The `data-tool-artifact` forwarding that ADR-0020
prescribed for the EDGAR URL stays unimplemented and is downgraded to a follow-up; its only
payload is `edgar_url`, which a citation block does not need.

**Rejected**:

1. **Implement ADR-0020's `data-tool-artifact` part and carry block content through it.** The
   content a block needs is already on the client; a second channel would send it twice and
   touch the streaming contract (event mapper, serializer, frontend hook) for no new data.
2. **Model-written evidence** (titles, excerpts, formulas in the answer text). Same
   fabrication risk ADR-0019 rejected for URLs — everything a block shows must come from a tool
   result, matched by ID.

**Why**:

1. **The join key already exists on both sides.** `sec_filing_search` chunks carry a stable
   `source` ID (ADR-0019) and every tool part carries its `toolCallId`, so `sql://{toolCallId}`
   is resolvable without any backend coordination beyond telling the model that ID.

**Consequences / accepted trade-offs**:

- Everything a block shows must live in model-visible tool content. Fine for evidence (it is
  what the model read); anything UI-only (the EDGAR URL) still needs the artifact channel.
- `text_to_sql` must hand the model `citation_id = "sql://{tool_call_id}"`, and any
  `derivations` it reports must be extracted deterministically (SQL AST / view definitions),
  never LLM-written. Without `derivations`, the block falls back to provenance + result table.
- An ID that matches no tool result renders an explicit "no matching result" entry instead of
  being dropped — a fabricated or mistyped ID stays visible as such (Legible failure).
