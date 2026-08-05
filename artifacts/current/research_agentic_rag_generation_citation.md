# Research: Agentic RAG pipeline structure — where grounded generation and citations live

- **Research question**: How do modern search agents / agentic RAG systems structure the pipeline beyond plain retrieval, and where should grounded answer generation + citation live in a single-orchestrator tool-calling agent?
- **Decision at stake**: (A) retrieval-as-tool returning chunks, generation in the orchestrator loop with prompt-driven citations vs (B) a grounded-generation sub-pipeline (retrieve → context construction → generate → structured answer w/ citations) wrapped as one tool.
- **Date**: 2026-08-05. Sources are current-era (2025–2026) official docs unless noted; the Anthropic contextual-retrieval blog is 2024 but still the referenced SSOT for that technique.

---

## TL;DR

- **All four vendors converge on the same top-level split: retrieval is a tool, answer generation stays in the orchestrator's LLM loop.** Nobody's current flagship agent pattern puts a second "answerer LLM" inside the retrieval tool — that is option A, not option B.
- **What differs is how citations are wired**, and there are exactly three families: (1) **API-native citation features** (Anthropic Citations API / `search_result` blocks; OpenAI `file_search` annotations) where the platform attaches verified pointers to the generated text; (2) **structured output** where the model emits `{answer, citations: [source_id, quote?]}` against IDs injected into the context (LangChain's recommended portable pattern); (3) **prompt-driven inline markers** ("Source N" / `[N]`), which is what LlamaIndex's `CitationQueryEngine` and FinLab-X's current scheme do — the weakest guarantee of the three.
- **Anthropic**: retrieval tool returns `search_result` content blocks (`source` can be *any stable string*, e.g. `kb://article-1234` — explicitly designed for non-URL sources); with `citations: {enabled: true}` the API attaches `search_result_location` citations (`cited_text`, `search_result_index`, block index range) to the model's text blocks. Generation = orchestrator loop; citation = API feature; granularity = your content-block splitting.
- **OpenAI**: `file_search` is a *hosted retrieval tool* over OpenAI vector stores; the advanced-RAG stages (query rewriting, parallel sub-queries, hybrid keyword+semantic search, reranking) run **inside the tool**; the model's message then carries `file_citation` annotations (`file_id`, `filename`, output-text `index`). Not usable for FinLab-X's self-hosted DuckDB/dense store, but the architecture (fat retrieval tool, thin citation annotations, generation in the loop) is the reference shape.
- **LlamaIndex**: historically the strongest option-B vendor (`CitationQueryEngine` = retrieve → re-split into numbered "Source N" citation chunks → synthesize with a citation prompt, wrappable as a `QueryEngineTool`), but their **current agent guidance wraps retrieval/query engines as tools under a `FunctionAgent`**, and their Anthropic integration added `CitableBlock` tool returns that map onto Anthropic's `search_result` — i.e. they built a bridge from B to A.
- **LangChain/LangGraph**: the official agentic-RAG tutorial is pure option A — retriever tool returning concatenated text, plus *orchestrator-level* nodes for document grading (`grade_documents`, structured binary score) and query rewriting (`rewrite_question`). Their citation guidance (legacy how-to, now folded into integration pages): prefer tool-calling/structured output citing source IDs (+ optional quotes) over free-form prompting; post-hoc attribution is the fallback.
- **Advanced-RAG stage placement** is consistent across vendors: index-time enrichment (contextual chunks), hybrid search, and reranking go **inside the retrieval tool**; query (re)writing and retry-on-bad-evidence go **in the orchestrator**; groundedness checking is either an **API guarantee** (Anthropic `cited_text` is extracted, not generated) or an **offline eval** (faithfulness metrics), not an inline pipeline stage.
- **For FinLab-X (OpenAI `gpt-4o` orchestrator, self-hosted retriever, no per-chunk URL)**: option A with *structured* citation handling is what the evidence supports — expose `retriever.search()` as a tool that returns numbered chunks with stable IDs built from `accession_number + item + chunk_index`, have the orchestrator cite those IDs (prompted inline `[N]` at minimum; structured output for stronger guarantees), and resolve IDs → EDGAR filing-level URLs (+ item/heading anchor text) at the API/frontend boundary. Option B's real-world habitat is multi-index routing and report generation, not a single-corpus QA agent; it would also break cross-filing synthesis (comparing 2 retrievals in one answer) and double LLM spend.

---

## 1. Anthropic

### 1.1 Citations API (documents)

Source: https://platform.claude.com/docs/en/build-with-claude/citations (redirect target of docs.claude.com; all active models support it).

- You pass `document` content blocks (plain text, PDF, or **custom content**) with `"citations": {"enabled": true}`. The model's response then contains `text` blocks each carrying a `citations` list with typed locations:
  - plain text → `char_location` (`cited_text`, `document_index`, `document_title`, `start_char_index`, `end_char_index`)
  - PDF → `page_location`
  - custom content → `content_block_location` (block index range into the `content` list you provided)
- **Chunk granularity is yours to control**: plain-text and PDF documents are auto-chunked into sentences ("sentence chunking lets Claude cite a single sentence or chain together multiple consecutive sentences"); **custom content documents are "used as-is and no further chunking is done"**. The docs give RAG-specific advice verbatim: "if you want Claude to be able to cite specific sentences from your RAG chunks, you should put each RAG chunk into a plain text document… if you do not want any further chunking… put RAG chunks into custom content document(s)."
- **Reliability guarantee**: "citations are guaranteed to contain valid pointers to the provided documents" — the model emits citations in an internal standardized format that the API parses and validates; `cited_text` is extracted server-side and **does not count toward output tokens** (nor input tokens when replayed in later turns).
- **Streaming**: supported; citations arrive as `citations_delta` inside `content_block_delta` events.

### 1.2 Search result content blocks (the tool-calling RAG path)

Source: https://platform.claude.com/docs/en/build-with-claude/search-results (GA, standard Messages API, no beta header; all active models except Haiku 3).

- A `search_result` block: `{type: "search_result", source, title, content: [text blocks], citations: {enabled}}`. Critically, **`source` is "any stable string… a URL, or an internal identifier such as `kb://article-1234`"** — the schema is explicitly designed for non-URL knowledge bases.
- Two integration methods, both first-class: **(1) returned from a custom tool's `tool_result`** ("dynamic RAG applications: tools fetch content at runtime, and Claude cites it in the response") and **(2) top-level user-message content** for pre-fetched context. The docs' worked example is exactly the option-A shape: a `search_knowledge_base` tool whose handler returns `SearchResultBlockParam` objects; the final assistant turn cites them automatically — "no special prompting is needed."
- Resulting citations are `search_result_location`: `{cited_text, source, title, search_result_index, start_block_index, end_block_index}`. **"The text block is the minimal citable unit: Claude cites whole blocks, not substrings within a block. To get finer-grained citations, split your search result content into smaller blocks."** So citation granularity = how you split each chunk into `content` text blocks.
- Citation enabling is all-or-nothing across the request's search results.

### 1.3 Architecture guidance

- *Building effective agents* (https://www.anthropic.com/engineering/building-effective-agents): start with the simplest thing — "optimizing single LLM calls with retrieval and in-context examples is usually enough"; the base building block is the **augmented LLM** (retrieval + tools + memory), and current models "generate their own search queries." Agents are LLMs "dynamically direct[ing] their own processes and tool usage." Retrieval is framed as a *capability of the reasoning LLM*, never as a competing generation site.
- *Contextual retrieval* (https://www.anthropic.com/news/contextual-retrieval, 2024-09-19): the retrieval-quality stack — contextual embeddings (prepend chunk-situating context before embedding), contextual BM25, rank-fusion hybrid, reranking (Cohere tested) — cutting retrieval failure 5.7%→1.9% (−67%), retrieving top-20 chunks. All of these are **index-time / retrieval-tool-internal** stages; the blog never places them in the agent loop.

**Anthropic's answer to the research question**: generation lives in the orchestrator loop; the retrieval tool returns structured evidence blocks; citation is an API feature attached to generated text with server-verified pointers; retrieval-quality machinery lives inside the tool/index.

## 2. OpenAI

### 2.1 `file_search` in the Responses API

Sources: https://developers.openai.com/api/docs/guides/tools-file-search (redirect target of platform.openai.com/docs/guides/tools-file-search); pipeline internals documented at https://developers.openai.com/api/docs/assistants/tools/file-search; cookbook: https://cookbook.openai.com/examples/file_search_responses.

- `file_search` is a **hosted tool** over OpenAI-managed vector stores: "semantic and keyword search," no backend needed. Inside the tool, per the file-search docs, it *rewrites user queries*, *breaks complex queries into parallel sub-searches*, runs hybrid keyword+semantic search, and *reranks* results. Default chunking 800 tokens with 400 overlap (`chunking_strategy` tunable, 100–4096 / overlap ≤ size/2). Knobs: `max_num_results`, metadata/attribute filtering, `include: ["file_search_call.results"]` to surface raw hits.
- The response contains two output items: a `file_search_call` (queries + status) and a `message` whose text carries **annotations** of type `file_citation`: `{type: "file_citation", file_id, filename, index}` where `index` is the position in the output text. (The old Assistants v1 annotation carried a `quote` span; the current Responses-era annotation is file-level + text position — coarser than Anthropic's block-level `cited_text`.)
- **Generation happens in the model's message, not inside the tool**; the tool returns chunks, the platform attaches citations to the generated text.

### 2.2 Agents SDK

Source: https://openai.github.io/openai-agents-python/tools/

- `FileSearchTool(vector_store_ids=[...], max_num_results=…, include_search_results=…, filters, ranking_options)` is a **hosted tool declared in the agent's `tools=[...]` list** next to `WebSearchTool` etc. — "retrieval as a declarative tool alongside other capabilities rather than a separate preprocessing step."
- Cookbook agentic-RAG entries (e.g. multi-tool orchestration, https://developers.openai.com/cookbook/examples/responses_api/responses_api_tool_orchestration) route queries between retrieval tools, web search, and functions from one model loop; the deep-research cookbook composes web+file search in an agent pipeline. None of them nest a generation LLM inside the retrieval tool.

**OpenAI's answer**: identical top-level split to Anthropic — fat retrieval tool (which is where they hide query rewriting/hybrid/rerank), generation in the loop, citations as platform annotations. The hosted tool itself can't serve FinLab-X (chunks live in FinLab-X's own store), but the placement of stages is the reference.

## 3. LlamaIndex

Sources: `CitationQueryEngine` example https://developers.llamaindex.ai/python/examples/query_engine/citation_query_engine and API reference (class signature via developers.llamaindex.ai framework-api-reference); workflow rebuild https://developers.llamaindex.ai/python/examples/workflow/citation_query_engine; agent tools https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/tools; 10-Q agent example https://developers.llamaindex.ai/python/examples/agent/openai_agent_context_retrieval; Anthropic citable tools https://developers.llamaindex.ai/python/examples/llm/anthropic.

### 3.1 Query engine = the packaged option-B unit

- A LlamaIndex *query engine* is retrieval + synthesis in one object: `retriever` → `node_postprocessors` (rerankers such as Cohere/Voyage cross-encoders live here) → `response_synthesizer` (modes: `refine`, `compact`, `tree_summarize`; `CitationQueryEngine` defaults to `ResponseMode.COMPACT`).
- **`CitationQueryEngine`** (`from_args(index, citation_chunk_size=512, citation_chunk_overlap=20, similarity_top_k=…)`) implements grounded generation with citations as a sub-pipeline: retrieve nodes → **re-split retrieved nodes into finer "citation chunks"** via `SentenceSplitter`, each prefixed `Source {n}:` → synthesize with `CITATION_QA_TEMPLATE` / `CITATION_REFINE_TEMPLATE` so the answer contains inline "Source N" references → response object exposes `source_nodes` for post-hoc resolution of N → provenance metadata. This is **prompt-driven** citation: no API verification, correctness depends on the model following the template. `citation_chunk_size` is the granularity dial (their example bumps it to 1024).
- The workflow-framework rebuild of the same engine makes the internal stages explicit: `retrieve → create_citation_nodes → synthesize` — i.e., exactly option B's "retrieve → context construction → generate → structured answer."

### 3.2 Agentic RAG = query engines (or plain functions) as tools

- `QueryEngineTool.from_defaults(query_engine, name=…, description=…)` wraps a whole query engine as an agent tool; the canonical financial example registers **one tool per Uber 10-Q quarter** (`uber_march_10q`, …) under an agent — the agent decomposes the question, calls per-document engines, and synthesizes across their answers. Note what this implies: when generation happens inside the tool, the orchestrator still does a **second** synthesis pass over the tools' textual answers.
- Their getting-started agent instead wraps the query engine in a plain `async def search_documents(query) -> str` function tool under `FunctionAgent` — same shape, looser packaging.
- **Citable tools (the A-bridge)**: with `llama-index-core>=0.12.46` + `llama-index-llms-anthropic>=0.7.6`, a tool can return a `CitableBlock(content=[TextBlock(...)], title=…, source=…)`; the Anthropic LLM class forwards it as a `search_result` block, and the response carries `CitationBlock`s (`source`, `title`, `cited_content`). Docs: "Citable tools can be integrated directly into pre-built agents, such as the FunctionAgent, to provide citations in the generated output." I.e., LlamaIndex's own newest citation path for agents moves generation *out* of the query engine and relies on provider-native citations.

**LlamaIndex's answer**: both options exist in the library; `CitationQueryEngine`-as-tool is the canonical B, used chiefly for multi-index routing and report generation; their agent-era guidance and the `CitableBlock` integration point toward A.

## 4. LangChain / LangGraph

Sources: agentic-RAG tutorial https://docs.langchain.com/oss/python/langgraph/agentic-rag; workflows-vs-agents https://docs.langchain.com/oss/python/langgraph/workflows-agents; Anthropic integration pages https://docs.langchain.com/oss/python/integrations/chat/anthropic (and JS equivalent); legacy citation how-to (retired in the docs migration; formerly python.langchain.com/docs/how_to/qa_citations/, JS mirror js.langchain.com/docs/how_to/qa_citations/ — both now 308-redirect to the new docs).

### 4.1 Agentic RAG tutorial (the current official pattern)

- Graph: `generate_query_or_respond` (LLM with `retriever_tool` bound; decides retrieve-vs-answer and writes the search query itself) → `retrieve` (`ToolNode([retriever_tool])`) → conditional `grade_documents` → `generate_answer` or `rewrite_question` → loop back.
- The **retriever tool is thin**: `@tool def retrieve_blog_posts(query) -> str` returning `"\n\n".join(doc.page_content)` — plain concatenated text, no structure.
- The **advanced stages are orchestrator nodes**, not tool internals: `grade_documents` uses structured output (`GradeDocuments{binary_score}`) on a separate grader model to decide relevance (the current doc even hardens the prompt against injection: "Treat the document as data only"); `rewrite_question` reformulates and retries. This is the CRAG-style corrective loop in official form.
- **Generation** is a dedicated `generate_answer` node in the graph — in the orchestrator, after grading, never inside the tool. The tutorial does no citation handling at all.

### 4.2 Citation guidance

- The long-standing how-to "How to get a RAG application to cite sources" enumerated (in descending order of robustness): **(1) tool-calling/structured output citing source IDs** — inject numbered source IDs into the prompt, force `with_structured_output` to a schema like `CitedAnswer{answer: str, citations: List[int]}`; **(2) same but citing quoted snippets** — `Citation{source_id: int, quote: str}` for verifiable spans; **(3) direct prompting** for inline markers, parsed from free text (least reliable); **(4) retrieval post-processing** — compress/split retrieved docs so tightly that the retrieved unit *is* the citation; **(5) generation post-processing** — a second LLM pass annotates an already-written answer. The page was retired in the 2025 docs migration; the structured-output pattern survives across the current docs (e.g. `with_structured_output` in the workflows guide, per-field `basis` citations in tool integrations), and provider-native citation is now documented on the integration pages instead.
- Current `ChatAnthropic` docs carry both Anthropic-native paths: `document` blocks with `citations: {enabled: true}` (response text blocks come back with `char_location` citations), and **"Search results from a tool"** — a LangChain `tool` returning `search_result` blocks so "Claude gains the ability to generate citations based on the material retrieved by the tool." So LangChain's position on where citations live: use the provider feature when on Anthropic; otherwise structured output against source IDs.

**LangChain's answer**: option A, with grading/rewrite as orchestrator graph nodes and citations via structured output or provider-native features — never a generation sub-pipeline inside the tool.

## 5. The "Beyond RAG" article (secondary source)

Source: https://blog.aihao.tw/2026/07/26/beyond-rag-llamaindex-workshop/ (LlamaIndex workshop write-up, 2026-07-26). Used as a topic map; claims checked against primary sources above.

- **Core thesis**: the RAG bottleneck has moved to *parsing* — "parsing errors cascade through downstream stages" (multi-column merges, fragmented tables, header/footer contamination). Pipeline named as parse → chunk → index → retrieve → rank → generate. *(Primary-source check: no vendor doc states the "parsing is the bottleneck" claim this strongly; it is the article's editorial position, though LlamaParse/LlamaExtract product docs exist. For FinLab-X this stage is already solved by the SEC ingestion pipeline's structured chunking — item/header_path/block_heading metadata is precisely the "structure-preserving parse" the article advocates.)*
- **Agentic loops / CRAG**: grade retrieved content before generation; route to synthesize / reformulate / fallback. *(Verified: this is literally the LangGraph agentic-RAG tutorial graph, §4.1.)*
- **Reranking as a node postprocessor** (cross-encoders, Cohere/Voyage, +4–14 nDCG@10). *(Verified: LlamaIndex `node_postprocessors`, §3.1; consistent with Anthropic contextual-retrieval's reranking stage, §1.3.)*
- **Citations via persistent metadata linkage** — page numbers, section paths, bbox coordinates attached to chunks; LlamaExtract returns validated JSON with page/bbox citations. *(Verified in spirit: this is the "document id + location span" family, the same shape as Anthropic `content_block_location` / OpenAI `file_id`+position — none of these are URL-based.)*
- **Eval hierarchy**: faithfulness → relevance → recall; RAGAS/DeepEval, Langfuse/Phoenix tracing — groundedness as *offline evaluation*, not an inline pipeline stage. *(Consistent with all four vendors' silence on inline groundedness checkers.)*
- Nothing in the article advocates a generation-inside-the-tool architecture; its agentic sections assume the evaluative loop wraps retrieval, with generation at the loop's end.

## 6. Cross-cutting: where each advanced-RAG stage goes

| Pipeline stage | Anthropic | OpenAI | LlamaIndex | LangChain/LangGraph | Verdict for a tool-calling agent |
|---|---|---|---|---|---|
| Chunking / structure-preserving parse | index-time (contextual chunks) | inside hosted tool (800/400 default) | ingestion (parsers, splitters) | ingestion | **index-time / ingestion** |
| Query rewriting / decomposition | orchestrator LLM writes queries ("augmented LLM") | **inside `file_search` tool** (rewrite + parallel sub-queries) | agent decomposes across `QueryEngineTool`s | **orchestrator node** (`rewrite_question`) + the agent writes tool queries | orchestrator by default; tool-internal only when the tool is a hosted black box |
| Hybrid retrieval (dense+BM25) | inside retrieval pipeline (contextual BM25 + rank fusion) | inside tool (keyword+semantic) | retriever composition | retriever composition | **inside the retrieval tool** |
| Reranking | inside retrieval pipeline (Cohere) | inside tool | `node_postprocessors` | retriever wrapper / compressor | **inside the retrieval tool** |
| Context construction / ordering / granularity | you split `search_result.content` blocks (block = min citable unit) | tool returns top-k, `max_num_results` | `create_citation_nodes` re-split + "Source N" labels | tool formats doc text | **tool-result formatting** — this is where citation granularity is decided |
| Evidence grading / corrective retry | (agent loop, implicitly) | (agent loop) | agent re-calls tools | **orchestrator nodes** (`grade_documents` → `rewrite_question`) | **orchestrator** |
| Answer generation | **orchestrator loop** | **orchestrator loop** (model message) | inside query engine (B) *or* agent loop with citable tools (A) | **orchestrator node** (`generate_answer`) | **orchestrator loop** |
| Citation attachment | **API feature** (`search_result_location`, verified `cited_text`) | **API feature** (`file_citation` annotations) | prompt-driven "Source N" (B) or provider-native via `CitableBlock` (A) | structured output (`CitedAnswer`) or provider-native | API feature > structured output > prompt-driven > post-hoc |
| Insufficient evidence / refusal | uncited text is visible; prompt-level policy | prompt-level | grading loops route away from synthesis | grade→rewrite loop; prompt-level | orchestrator prompt + loop; no vendor ships an inline refusal stage |
| Groundedness verification | API-verified pointers at cite time | — (offline evals) | offline evals (faithfulness) | offline evals; LangSmith | **offline evals**, unless the provider verifies pointers |

## 7. Implications for FinLab-X

**Repo facts that constrain the options** (checked 2026-08-05): orchestrator profiles run OpenAI models (`gpt-4o` / `gpt-4o-mini` in `backend/agent_engine/agents/profiles/*/orchestrator_config.yaml`); the retriever is self-hosted (`backend/ingestion/sec_dense_pipeline/retriever.py`, chunks carry `ticker/year/item/header_path/block_heading/prelude/chunk_index/text/accession_number`); citations today are inline `[N]` + markdown `[N]: url "title"` reference definitions extracted post-hoc by the frontend; SEC chunks have **no per-passage public URL** (EDGAR resolves only to filing-level URLs via accession number).

### 7.1 Option A vs Option B against the evidence

**Option A (retrieval tool returns chunks; generation in the orchestrator loop)** is the pattern all four vendors' current agent guidance converges on (§1.2 method 1, §2.2, §3.2 citable tools, §4.1). Concrete supporting facts:

- The LangGraph agentic-RAG tutorial — the closest published blueprint to FinLab-X's stack (LangGraph + tool-calling orchestrator) — is exactly this shape, with grading/rewrite loops living in the graph, not the tool.
- Anthropic's `search_result` docs describe tool-returned evidence + loop-side generation as *the* dynamic-RAG pattern; LlamaIndex's newest citation mechanism (`CitableBlock`) was built to serve that same shape.
- A follow-up question class FinLab-X must handle — "compare AAPL's 2023 vs 2024 risk factors" — requires the orchestrator to synthesize across **multiple** retrieval calls in one answer. Under A this is native; under B the orchestrator would summarize two pre-written answers (LlamaIndex's 10-Q example does exactly this double-generation), losing chunk-level provenance in the second pass unless the sub-pipeline's citation format survives re-synthesis — which prompt-driven inline markers generally do not.

**Option B (grounded-generation sub-pipeline as one tool)** is a real, documented pattern (LlamaIndex `CitationQueryEngine` + `QueryEngineTool`, §3), but note where it earns its keep in the vendor material: **multi-index routing** (one tool per document/corpus, agent as router) and **report generation** (fixed pipeline, no conversational loop). Its costs for FinLab-X:

- A second LLM call (and prompt) inside the tool per retrieval → duplicate token spend and latency in a loop that may retrieve several times per turn.
- The orchestrator receives prose, not evidence — it cannot grade, cross-check, or partially reuse chunks (the LangGraph `grade_documents` pattern becomes impossible).
- Streaming: the sub-pipeline's answer arrives as one tool-result blob; FinLab-X's UIMessage-stream UX streams the orchestrator's text, so the user-visible answer would be a paraphrase of the tool's answer — or the orchestrator degenerates into a relay.
- Citation guarantees do not improve: `CitationQueryEngine`'s citations are themselves prompt-driven "Source N" markers; wrapping them in a tool adds no verification.

**Assessment: the evidence favors A.** B should only be revisited if FinLab-X grows multiple heterogeneous indexes needing routing, or a non-conversational report-generation mode.

### 7.2 Citation wiring under Option A — three tiers, given the OpenAI-model constraint

The strongest scheme found (Anthropic `search_result` + Citations API: server-verified `cited_text`, free output tokens, streaming `citations_delta`) **requires Claude models**, and OpenAI's annotation scheme requires their hosted `file_search` over OpenAI vector stores. With `gpt-4o` + a self-hosted retriever, neither platform feature applies directly, leaving:

1. **Prompt-driven inline `[N]` against tool-returned numbered chunks** (current-scheme-compatible; LlamaIndex `CITATION_QA_TEMPLATE` precedent; LangChain's "least reliable" tier). Minimum change: the tool result labels each chunk `[N]` with a stable ID; the system prompt mandates `[N]` markers + reference definitions. Failure mode: unverified — the model can mis-number or cite nothing; needs an eval (faithfulness/citation-accuracy) as the guardrail, per §5/§6.
2. **Structured citations** (LangChain's recommended portable pattern): the final answer (or a post-answer structured call) emits `{answer, citations: [{source_id, quote?}]}` against the chunk IDs in context. More robust than prose markers, machine-checkable (does `quote` appear in chunk `source_id`?), but interacts awkwardly with token-streaming a conversational answer — vendors use it for non-streaming or two-pass flows.
3. **Post-hoc attribution** (LangChain approach 5): generate freely, then a second pass aligns sentences to chunks. Most expensive, weakest coupling; no vendor recommends it as the primary scheme.
- **Forward-compatible hedge**: since models are admin-configured per profile, designing the tool's return type as *structured evidence objects* (id, source-id string, title, content text) — the `search_result`/`CitableBlock` shape — keeps tier-0 (Anthropic-native citations) a config-flip away if a profile ever runs Claude, while tiers 1–2 consume the same objects today.

### 7.3 Non-URL sources: the ID scheme

Every serious scheme found is **document-ID + location-span**, not URL: Anthropic's `source` is "any stable string… such as `kb://article-1234`" with block-index spans; OpenAI cites `file_id` + `filename`; LlamaIndex resolves "Source N" → `source_nodes` metadata; the workshop article's LlamaExtract cites page + bbox. FinLab-X's chunk metadata already contains everything needed:

- **Stable citation ID**: e.g. `sec://{accession_number}/{item}#{chunk_index}` (accession number is the EDGAR-canonical filing key).
- **Human-facing title**: `{ticker} {year} 10-K, {item}, {header_path or block_heading}` — this replaces the "url + title" role in the current `[N]: url "title"` contract.
- **URL resolution at the boundary**: accession number → filing-level EDGAR URL (`https://www.sec.gov/Archives/edgar/data/{cik}/{accession-no-dashless}/...`), computed by the API layer or frontend when rendering the reference list; the deep location (item/heading) is carried as citation *text*, not as a fragment URL, since EDGAR has no passage anchors. The frontend's post-hoc `[N]`-extraction can stay, with the reference-definition line now built from structured citation metadata rather than model-emitted URLs — which also eliminates the model-invents-URL failure mode entirely.

### 7.4 Placement of the remaining stages (per the §6 table)

- Inside the tool: hybrid/reranking upgrades if ever needed (Anthropic contextual-retrieval stack), metadata filters (`ticker`/`year`/`item` as tool parameters — the orchestrator, like OpenAI's and Anthropic's agents, writes its own queries and filters), chunk formatting/numbering.
- In the orchestrator: query decomposition across filings, retry-on-thin-evidence, refusal when retrieval returns nothing relevant (prompt policy; optionally a LangGraph-style grade node later — but note the envelope's over-engineering rule before adding graph nodes speculatively).
- Post-hoc / offline: citation-accuracy and faithfulness evals in `backend/evals/` (RAGAS-style faithfulness → relevance → recall hierarchy), which is the only groundedness verification any vendor actually ships for prompt-driven citations.

---

## Appendix: primary sources

| Topic | URL |
|---|---|
| Anthropic Citations API | https://platform.claude.com/docs/en/build-with-claude/citations |
| Anthropic search results (RAG blocks) | https://platform.claude.com/docs/en/build-with-claude/search-results |
| Anthropic — Building effective agents | https://www.anthropic.com/engineering/building-effective-agents |
| Anthropic — Contextual retrieval | https://www.anthropic.com/news/contextual-retrieval |
| OpenAI file_search (Responses) | https://developers.openai.com/api/docs/guides/tools-file-search |
| OpenAI file search internals (rewrite/parallel/hybrid/rerank, chunk defaults) | https://developers.openai.com/api/docs/assistants/tools/file-search |
| OpenAI Agents SDK tools (FileSearchTool) | https://openai.github.io/openai-agents-python/tools/ |
| OpenAI cookbook — file search + citations | https://cookbook.openai.com/examples/file_search_responses |
| OpenAI cookbook — multi-tool RAG orchestration | https://developers.openai.com/cookbook/examples/responses_api/responses_api_tool_orchestration |
| LlamaIndex CitationQueryEngine | https://developers.llamaindex.ai/python/examples/query_engine/citation_query_engine |
| LlamaIndex citation workflow (stages explicit) | https://developers.llamaindex.ai/python/examples/workflow/citation_query_engine |
| LlamaIndex QueryEngineTool / agent tools | https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/tools |
| LlamaIndex 10-Q agent (per-filing tools) | https://developers.llamaindex.ai/python/examples/agent/openai_agent_context_retrieval |
| LlamaIndex Anthropic citable tools (CitableBlock) | https://developers.llamaindex.ai/python/examples/llm/anthropic |
| LangGraph agentic RAG tutorial | https://docs.langchain.com/oss/python/langgraph/agentic-rag |
| LangChain ChatAnthropic citations / search-result tools | https://docs.langchain.com/oss/python/integrations/chat/anthropic |
| LangChain legacy citation how-to (retired; JS mirror) | https://js.langchain.com/docs/how_to/qa_citations/ (308 → new docs) |
| Workshop article (secondary) | https://blog.aihao.tw/2026/07/26/beyond-rag-llamaindex-workshop/ |
