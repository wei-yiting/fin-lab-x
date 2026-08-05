# ADR-0008: SEC RAG answer generation stays in the Orchestrator loop; retrieval is a tool returning citable evidence chunks (2026-08-05)

**Decision**: Expose SEC RAG retrieval to the agent as an Orchestrator tool
(`sec_filing_search`, wrapping `retriever.search()`). Grounded answer generation happens in
the Orchestrator's own reasoning loop — the LLM reads the returned chunks and writes the
answer directly. The tool returns **structured evidence objects**: numbered chunks, each
carrying a stable citation ID derived from chunk metadata
(`sec://{accession_number}/{item}#{chunk_index}`) plus human-facing locator fields
(ticker, year, item, header_path / block_heading). Citations are **prompt-driven
numbered-chunk references**: the model emits inline `[N]` markers pointing at the numbered
chunks it was given; it never writes URLs or titles itself — the reference list (EDGAR
filing-level URL + section locator text) is resolved mechanically from chunk metadata at the
API/frontend boundary. Decided via the DEV-125 grilling session, grounded in the vendor
survey `artifacts/current/research_agentic_rag_generation_citation.md`.

**Rejected**:

1. **Multi-agent split** (a dedicated RAG agent — and later a text-to-SQL agent — behind a
   routing orchestrator). The vendor consensus threshold for splitting into sub-agents is
   *context isolation* (long sub-trajectories that would pollute the main context, or
   parallel fan-out), not capability domain. A RAG "agent" here would be one tool call plus
   reading its result — no trajectory to isolate. This also follows the repo's Single
   Orchestrator principle (AGENTS.md): capabilities are tools, behavior variants are
   Workflow Profiles (`reader` is a profile, not an agent).
2. **Generation inside the retrieval tool** (LlamaIndex `CitationQueryEngine`-as-tool
   shape: retrieve → construct context → generate → return a finished answer). Costs
   verified in the research memo: a second LLM call per retrieval; the Orchestrator
   receives prose instead of evidence, so it cannot grade, cross-check, or reuse chunks;
   cross-filing synthesis ("compare FY2023 vs FY2024 risk factors" = two retrievals, one
   answer) degenerates into paraphrasing pre-written answers, losing chunk-level provenance;
   and the user-visible stream becomes a relay of a tool-result blob. Even LlamaIndex's
   newest agent-citation mechanism (`CitableBlock`) moves generation back out of the tool.
3. **Model-emitted URLs** (status quo for news citations, extended to SEC). SEC chunks have
   no per-passage public URL, and letting the model write URLs is the known
   fabricated-URL failure mode. Rejected in favor of ID-based references resolved outside
   the model.

**Why**:

1. **All four surveyed vendors converge on this shape.** Anthropic (`search_result` blocks
   returned from custom tools, generation in the loop), OpenAI (`file_search` as a hosted
   tool + message-level citation annotations), LangGraph (official agentic-RAG tutorial:
   thin retriever tool, generation as a graph node), and LlamaIndex's current agent
   guidance all keep answer generation in the orchestrating LLM's loop. No current
   flagship pattern nests an answerer LLM inside the retrieval tool.
2. **Cross-retrieval synthesis is native.** Multi-ticker / multi-year / multi-aspect
   questions are answered by multiple `sec_filing_search` calls whose chunks coexist in one
   context, under the existing per-run tool-call budget.
3. **The evidence-object return shape is a free forward-compatibility hedge.** Structured
   evidence objects match Anthropic's `search_result` block shape, whose `source` field is
   explicitly "any stable string" (designed for non-URL sources). If a Workflow Profile is
   ever pointed at a Claude model, server-verified citations (`cited_text` extracted and
   validated by the API) become a config flip, with no tool redesign. Today's profiles run
   OpenAI models, so neither Anthropic's Citations API nor OpenAI's hosted `file_search`
   (which requires OpenAI-managed vector stores) is directly usable.

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
- **Context-construction strategy lives mostly with the LLM** (which chunks to use, how to
  weigh them), controlled via prompt rather than code. Corrective machinery
  (document-grading nodes, query-rewrite loops in the graph) is deliberately deferred until
  evals demonstrate the failure mode it would fix (envelope: defer until evidence).
- The Orchestrator system prompt gains SEC-citation rules (numbered-chunk `[N]` usage, the
  no-model-written-URLs rule for SEC sources), and the frontend Sources block gains an
  ID-resolved reference path alongside the existing URL-based one.
