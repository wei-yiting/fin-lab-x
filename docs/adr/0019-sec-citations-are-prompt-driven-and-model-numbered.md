# ADR-0019: SEC citations are prompt-driven and model-numbered, bound to stable per-chunk IDs (2026-08-20)

*(Carved out of ADR-0018 on 2026-08-20 to give this decision its own record; the underlying
decision was made 2026-08-05 in the DEV-125 grilling session and refined 2026-08-19.)*

**Decision**: `sec_filing_search` returns **structured evidence objects**, not prose: each
chunk carries a stable citation ID (`source`, e.g. `sec://{accession_number}/{item}#{chunk_index}`),
a composed display `title` (ticker + fiscal year + item + subsection, e.g. `"AAPL FY2024
10-K · Item 1A · Competition"`), an optional `subsection` locator, its `content`, and a
retrieval `score` — but no per-chunk ordinal. Ticker, fiscal year, and item are properties of
the enclosing evidence group (chunks are grouped by ticker/fiscal-year/item), not of the
individual chunk. Citations are **prompt-driven, model-numbered references**: the model
assigns `[N]` itself, in first-use order across the whole answer (across tools and across
calls), and binds each `[N]` to a chunk via its stable ID in a bottom reference definition
(`[N]: sec://…`); it never writes URLs or titles itself — the reference list (EDGAR
filing-level URL + section locator text) is resolved mechanically from chunk metadata at the
API/frontend boundary — see ADR-0020 for how the EDGAR URL specifically stays out of the
model's context. Grounded in the vendor survey
`artifacts/current/research_agentic_rag_generation_citation.md`.

**Rejected**:

1. **Model-emitted URLs** (status quo for news citations, extended to SEC). SEC chunks have
   no per-passage public URL, and letting the model write URLs is the known
   fabricated-URL failure mode. Rejected in favor of ID-based references resolved outside
   the model.

**Why**:

1. **Global, first-use numbering is the only scheme that survives cross-retrieval
   synthesis.** A question spanning multiple `sec_filing_search` calls (cross-ticker,
   cross-year, multi-aspect) puts all their chunks in one context and one answer; if each
   tool call numbered its own chunks starting at 1, an answer built from two calls would
   emit duplicate `[1]`s. Only the model — the one party that sees the whole answer being
   written — can assign non-colliding numbers across every chunk it decides to cite, in the
   order it first cites them.

**Consequences / accepted trade-offs**:

- **Prompt-driven `[N]` markers are the weakest of the three citation schemes surveyed**
  (vs. code-verified structured citations `{claim, source_id, quote}`, vs. API-verified
  citations): nothing checks at generation time that `[N]` actually supports the claim.
  Accepted because the alternatives each carry a blocking cost today — structured-output
  citations conflict with token-streaming the answer (one-blob delivery or a second LLM
  pass whose citations can diverge from the streamed text), and API-verified citations
  require switching the orchestrator to a Claude model, a decision that must not be driven
  by citations alone. The guardrail is offline evaluation: citation accuracy /
  groundedness scoring in the RAG end-to-end eval (DEV-126). If those evals show
  unacceptable citation error rates, the upgrade path is a post-answer structured
  verification pass — added on evidence, not speculatively.
- The Orchestrator system prompt gains SEC-citation rules (model-assigned `[N]` usage keyed
  to stable chunk IDs, the no-model-written-URLs rule for SEC sources), and the frontend
  Sources block gains an ID-resolved reference path alongside the existing URL-based one.
- Evidence chunks deliberately carry no per-call ordinal — only the model numbers `[N]`, in
  first-use order across the whole answer, across tools and across calls. An earlier shape
  had the tool number chunks itself, restarting at 1 on every call; that invited the model
  to copy the tool's numbering literally, producing duplicate `[1]`s once an answer
  synthesized chunks from multiple calls (e.g. cross-year comparisons). Reference resolution
  at the frontend boundary keys on each chunk's stable `source` ID, never on position.
