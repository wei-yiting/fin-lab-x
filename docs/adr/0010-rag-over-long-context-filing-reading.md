# ADR-0010: Retrieval (RAG) is the default SEC evidence path, not whole-filing long-context reading (2026-08-05)

**Decision**: Pinpoint SEC questions (answer lives in a few specific passages — see
CONTEXT.md) are served by chunk retrieval (`sec_filing_search`, ADR-0008), not by loading
whole filings or whole sections into the model context. The existing whole-section tools
(`sec_filing_list_sections` / `sec_filing_get_section`) stay, repositioned for **synoptic**
questions — "summarize Item 1A", "the overall tone of the MD&A" — where the information
need genuinely spans a full section. The routing between the two is a
prompt-level guideline for now, explicitly gated by evidence: the RAG end-to-end eval
(DEV-126) includes a forced-arm A/B (same question set answered with each tool forced) plus
tool-selection accuracy measurement, and the routing default is revisited on those numbers.
Decided in the DEV-125 grilling session after challenging the premise "context windows are
big enough that RAG is unnecessary".

**Rejected**: whole-filing long-context reading as the primary evidence strategy. This is a
serious alternative, not a strawman — Anthropic's contextual-retrieval guidance says a
knowledge base under ~200k tokens should skip RAG and go straight into context, and a
single 10-K (~55–110k tokens) clears that bar. The strongest case for it is a single-filing
deep-dive session ("let's analyze NVDA's 10-K"): full filing + prompt caching would likely
beat retrieval on answer quality there. It was rejected as the *default* for the reasons
below; its home turf is served by keeping the whole-section tools.

**Why** (three structural reasons, all product-level rather than benchmark-level):

1. **The corpus is JIT-unbounded filings × years, not one document.** The <200k-tokens
   rule presupposes a fixed knowledge base loaded every time. FinLab-X's per-question
   filing set is dynamic (any US ticker, any year, on demand), and cross-ticker comparison
   questions (two 10-Ks ≈ 150k+ tokens) exceed the orchestrator model's 128k window
   outright — "it fits" is false before cost is even discussed.
2. **Multi-turn accumulation.** Conversation state is a LangGraph checkpointer thread;
   a whole section (15–30k tokens) or filing pulled into a ToolMessage stays in the thread
   and is re-sent every subsequent turn. By turn three, earlier filing dumps crowd the
   context and inflate every later turn's cost and latency. Single-shot QA comparisons
   systematically understate this penalty. Retrieval keeps the per-call footprint at
   ~5k tokens (top-10 × 512-token chunks).
3. **Chunk-level citations only exist on the retrieval path.** Per ADR-0008, the product's
   zero-hallucination citation chain is built on numbered evidence chunks with stable IDs.
   A whole-section answer can only cite at Item granularity — honest for a section summary,
   but a verification black hole for specific claims.

**Consequences / accepted trade-offs**:

- **Single-filing deep-dive sessions may be underserved by retrieval** (top-k chunks are
  query-biased; synoptic coverage is not guaranteed). Accepted: those tasks route to
  `sec_filing_get_section`, whose Item-level citation granularity matches the synoptic
  information need.
- **Tool-selection errors between the two SEC tools are a real risk and are prompt-
  controlled only.** Accepted with a measurement plan instead of a belief: DEV-126 carries
  the forced-arm A/B (quality / groundedness / token cost / latency per arm) and
  tool-selection accuracy tracking (Baseline behavior diagnostic pattern — trace review of
  whether the appropriate tool was reached). If the data shows chaotic selection or a
  systematic quality win for one arm, the routing design is reopened — including the
  options "search as sole entry" and its inverse.
- If a future orchestrator model ships a much larger window with cheap caching, reason 1
  weakens for small filing sets but reasons 2–3 stand; any revisit should re-run the
  DEV-126 forced-arm comparison rather than re-argue from first principles.
