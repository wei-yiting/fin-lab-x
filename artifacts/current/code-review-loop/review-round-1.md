# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 8 |
| Blocking | 0 |
| Major | 6 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 6 |

## Issues

### [Major] M-1.1: The advertised SEC citation path has no frontend consumer
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L37
- **Problem:** The docstring claims `frontend/src/lib/sec-citations.ts` consumes this contract, but that file does not exist. The current frontend accepts only `http:`/`https:` references in `markdown-sources.ts` and `Sources.tsx`; a `[1]: sec://...` definition is stripped but never resolved, leaving `[1]` as plain text with no Sources entry or EDGAR link. `edgar_url` and the evidence metadata therefore have no in-repo consumer at merge time, violating design-envelope §0, while the newly "Implemented" reader profile exposes a broken user-facing citation contract in the §4 API zone.
- **Fix:** Ship the frontend resolver and end-to-end contract tests in the same reachable slice: correlate `sec://` definitions with `sec_filing_search` tool output, resolve them to `edgar_url` plus locator metadata, and render clickable citations. Otherwise keep the reader profile unavailable and remove the unconsumed frontend fields until that slice lands.

### [Major] M-1.2: The acknowledged citation guardrail is deferred past feature activation
- **File:** `docs/adr/0008-rag-generation-in-orchestrator-loop.md` L59
- **Problem:** The ADR and research artifact explicitly classify prompt-driven `[N]` citations as the weakest scheme and say citation-accuracy/groundedness evaluation is the required guardrail, but this change activates and documents the reader profile without that evaluation. The existing `sec_retrieval` scenario is draft, disabled, and measures retrieval only—not citation correctness, faithfulness, evidence gaps, or tool routing. This violates design-envelope §0's Evidence Gate and under-engineers the §4 Eval zone.
- **Fix:** Add and calibrate the end-to-end citation/groundedness and routing evals before declaring the reader profile implemented, or keep the profile non-live until those guards exist.

### [Major] M-1.3: Filing-store failures are silently converted into missing citation metadata
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L144
- **Problem:** `_edgar_filing_url()` catches `OSError` and `ValueError` and returns `None`, making an unreadable or malformed persisted filing indistinguishable from a legitimate cold store. No error, warning, or trace metadata records the failure. That violates design-envelope §4 Observability ("no silent failures") and the §4 API requirement for structured, actionable failures.
- **Fix:** Distinguish an absent filing from a failed metadata read. Surface a structured warning/error in the tool result and trace, or raise a typed, legible exception; do not collapse failures into `None`.

### [Major] M-1.4: The new tool boundary provides types but no shape or size validation
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L65
- **Problem:** `query=""`, whitespace-only or unbounded queries, `ticker=""`, invalid ticker shapes, and nonsensical fiscal years all pass the Pydantic schema. They reach EDGAR or the embedding service only after normalization. Basic type/shape/size validation is explicitly required in design-envelope §4's API contract.
- **Fix:** Add explicit Pydantic constraints and normalization for non-empty bounded queries, valid ticker syntax/length, and the accepted fiscal-year domain. Add boundary tests proving invalid inputs fail before external calls.

### [Major] M-1.5: The new ADR reuses an existing ADR number
- **File:** `docs/adr/0008-rag-generation-in-orchestrator-loop.md` L1
- **Problem:** `docs/adr/0008-explicit-regression-gate-declaration.md` already defines ADR-0008. References such as "per ADR-0008" are now ambiguous between unrelated decisions. ADRs are a production-grade zone under design-envelope §4, so ambiguous decision identity is not optional polish.
- **Fix:** Rename this ADR to the next unused unique number and update every filename, heading, code comment, test comment, and cross-reference.

### [Major] M-1.6: Durable files contain roadmap phase identifiers
- **File:** `CONTEXT.md` L15
- **Problem:** The change embeds `Phase 1`, `Phase 2`, and `PRD Phase 2` in durable documentation, tests, and comments, including `profiles/README.md`, `test_orchestrator_prompt_rendering.py`, and ADR-0008. These are process-stage labels whose meaning depends on the producing plan rather than the behavior being documented.
- **Fix:** Replace each phase label with descriptive behavior such as "whole-section baseline profile" or "structured-RAG reader profile."

### [Minor] m-1.1: Issue IDs leak into code comments and durable documentation
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L141
- **Problem:** `DEV-65`, `DEV-127`, `DEV-125`, and `DEV-126` appear in production docstrings, tests, and ADR prose where the surrounding descriptive text can stand alone. Issue IDs belong in commit/PR metadata.
- **Fix:** Replace the IDs with the relevant schema constraint, evaluation responsibility, or decision rationale.

### [Minor] m-1.2: README documents a nonexistent tool name
- **File:** `README.md` L90
- **Problem:** The now-implemented RAG layer lists `search_sec_filings`, while the registered tool is `sec_filing_search`. Contributors following the architecture table will search for the wrong interface.
- **Fix:** Rename the documented entry point to `sec_filing_search`.

## Documentation Gaps

No material folder-level documentation gaps.

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| LangGraph | 1.0.9 | `get_stream_writer()` | ✅ Current | Documented async-tool pattern; `astream()` includes `stream_mode="custom"`. The fallback outside graph runs matches repo convention. |
| LangChain / langchain-core | 1.2.10 / 1.5.3 | `@tool(..., args_schema=...)`, `InjectedToolCallId` | ✅ Current | Correct decorator and injected tool-call ID pattern. |
| Langfuse | 4.5.0 | `@observe(name=...)` | ✅ Current | Correct stacking order: `@tool` outer, `@observe` inner. |
| Pydantic | 2.12.5 | `BaseModel`, `Field` | ✅ Current | API usage is current; missing domain constraints are reported separately as M-1.4. |
| FastAPI / Starlette | 0.135.1 / 0.52.1 | `TestClient(app)` context manager | ✅ Current | Correct lifespan-testing pattern. |
| Python stdlib | 3.11.9 | `logging.basicConfig` | ✅ Current | Correctly no-ops when root handlers already exist; placement matches the stated startup-log intent. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 4 |
| Missing | 0 |
| Scope creep | 2 |
| Misimplemented | 2 |

## Findings

### [Major] SP-1.1: Prompt renumbers citations instead of preserving tool chunk numbers
- **Type:** Misimplemented
- **Spec:** "SEC citation 規則：inline [N] 對應 tool result 的 chunk 編號；reference definitions 的 URL 欄位寫 stable citation ID（非 URL）" (DEV-130, System prompt 行為契約)
- **File:** `backend/agent_engine/agents/profiles/reader/system_prompt.md` L80
- **Problem:** The prompt requires citations to be renumbered sequentially in answer first-use order. If the first cited evidence is tool chunk `n=5`, the prompt directs the model to emit `[1]`, so `[N]` no longer corresponds to the chunk number assigned by the tool.
- **Fix:** Require the model to use each evidence chunk's emitted `n` as its inline marker. If multiple tool calls need one answer-wide namespace, clarify and implement that contract explicitly rather than silently redefining `[N]` in the prompt.

### [Major] SP-1.2: Generic citation instruction still tells the model SEC filings require URLs
- **Type:** Misimplemented
- **Spec:** "model 禁止為 SEC 來源書寫任何 URL" (DEV-130, System prompt 行為契約)
- **File:** `backend/agent_engine/agents/profiles/reader/system_prompt.md` L20
- **Problem:** The prompt says sources with genuine URLs include "SEC filings," implying that SEC URLs are required. This contradicts the later absolute prohibition against model-written URLs for SEC-sourced claims and weakens a core hallucination guardrail.
- **Fix:** Remove SEC filings from the URL-required examples and state at this earlier generic rule that every SEC source follows the stable-ID contract, never a model-written URL.

### [Major] SP-1.3: API serving-profile override was implemented despite the report-only instruction
- **Type:** Scope creep
- **Spec:** "調查 API 實際 serve 哪個 profile（baseline 還原後 chat 預設將摸不到 RAG）——只回報選項，不擅改" (DEV-142, Profile 歸屬修正指示 item 9)
- **File:** `backend/api/main.py` L41
- **Problem:** The changeset adds `WORKFLOW_PROFILE` as a new deployment configuration surface and lets it change the profile served by the API. The ticket explicitly limited this work to investigating and reporting the available options for an admin/product decision.
- **Fix:** Revert the environment-variable override and its tests in `backend/tests/api/test_main.py`; retain `DEFAULT_WORKFLOW_PROFILE` behavior and document the options in the PR description as requested.

### [Minor] SP-1.4: Process-wide logging configuration is unrelated runtime behavior
- **Type:** Scope creep
- **Spec:** "調查 API 實際 serve 哪個 profile（baseline 還原後 chat 預設將摸不到 RAG）——只回報選項，不擅改" (DEV-142, Profile 歸屬修正指示 item 9)
- **File:** `backend/api/main.py` L21
- **Problem:** `logging.basicConfig()` changes process-wide log level and formatting. No DEV-142 or backend-relevant DEV-130 requirement asks this slice to configure application logging; it was introduced to expose startup reporting associated with the unauthorized API-profile change.
- **Fix:** Remove `logging.basicConfig()` from this changeset. Handle application-wide logging configuration in separately authorized operational work if needed.

## Covered Requirements

✅ `baseline` remains identical to the specified main SHA and contains no RAG tool or citation prompt diff — `backend/agent_engine/agents/profiles/baseline/`
✅ New async `sec_filing_search(query, ticker, fiscal_year?)` tool exists with one required ticker and optional fiscal year — `backend/agent_engine/tools/sec_filing_search.py`
✅ The agreed interim frozen `_html` retriever and `year` filter are used — `backend/agent_engine/tools/sec_filing_search.py`
✅ Omitted fiscal year is resolved as the ticker's latest 10-K year and reported in the result — `backend/agent_engine/tools/sec_filing_search.py`
✅ Existing retriever JIT, cache, and `sec_retrieval` tracing path is reused — `backend/agent_engine/tools/sec_filing_search.py`
✅ Evidence is grouped by `(ticker, year, item)` — `backend/agent_engine/tools/sec_filing_search.py`
✅ Chunks inside each group are sorted in document order by `chunk_index` — `backend/agent_engine/tools/sec_filing_search.py`
✅ Prelude appears once per evidence group — `backend/agent_engine/tools/sec_filing_search.py`
✅ Tool-result chunk numbering is continuous across all groups in one result — `backend/agent_engine/tools/sec_filing_search.py`
✅ Stable citation IDs use `sec://{accession}/{item_key}#{chunk_index}` — `backend/agent_engine/tools/sec_filing_search.py`
✅ Missing legacy accession metadata degrades to the agreed `ticker-FY{year}` identifier — `backend/agent_engine/tools/sec_filing_search.py`
✅ Evidence objects provide `source`, `title`, and `content` plus number and score — `backend/agent_engine/tools/sec_filing_search.py`
✅ Citation metadata and EDGAR resolution data are included in the persisted tool result body — `backend/agent_engine/tools/sec_filing_search.py`
✅ EDGAR direct URLs are resolved out-of-band from persisted filing metadata — `backend/agent_engine/tools/sec_filing_search.py`
✅ A cold filing store honestly degrades `edgar_url` to null — `backend/agent_engine/tools/sec_filing_search.py`
✅ FlatItem chunks degrade to Item-level locator text without requiring a subsection — `backend/agent_engine/tools/sec_filing_search.py`
✅ Pre/post language directives sandwich the returned evidence — `backend/agent_engine/tools/sec_filing_search.py`
✅ Empty retrieval results return a legible ticker/year-specific message — `backend/agent_engine/tools/sec_filing_search.py`
✅ Retriever errors bubble through the tool for existing middleware to return error `ToolMessage`s — `backend/agent_engine/tools/sec_filing_search.py`
✅ `top_k` is the only result-size bound; no additional context truncation was introduced — `backend/agent_engine/tools/sec_filing_search.py`
✅ `reader` registers `sec_filing_search`, removes its placeholder notice, and describes Structured RAG — `backend/agent_engine/agents/profiles/reader/orchestrator_config.yaml`
✅ Recommended `reader` model and tool-call budget values are configured — `backend/agent_engine/agents/profiles/reader/orchestrator_config.yaml`
✅ `reader/system_prompt.md` is based on the baseline skeleton and renders its tool-budget placeholder — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Pinpoint questions route to search and synoptic questions route to whole-section tools — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Multi-source claims and repeated use of one source are covered by the prompt — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Evidence-gap annotations are required beside the affected claim rather than in a trailing disclaimer — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Chinese-language answers retain the citation format through the inherited language policy and example — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ The reading guide recommends search only when that tool is available — `backend/agent_engine/tools/sec_filing_tools.py`
✅ The new tool is registered and participates in SEC identity validation — `backend/agent_engine/tools/__init__.py`
✅ Tool selection and retrieval remain observable through tool and `sec_retrieval` spans — `backend/agent_engine/tools/sec_filing_search.py`
✅ Tool seam tests cover grouping, ordering, numbering, IDs, year resolution, EDGAR URL, FlatItem fallback, language sandwich, empty results, and error bubbling — `backend/tests/tools/test_sec_filing_search.py`
✅ Reader/baseline profile boundaries and prompt rendering are covered by tests — `backend/tests/agents/test_orchestrator_prompt_rendering.py`
✅ ADR-0008, ADR-0010, glossary, profile, architecture, and file-structure documentation were updated — `docs/adr/0008-rag-generation-in-orchestrator-loop.md`
✅ Existing streaming behavior is unchanged — `backend/agent_engine/agents/base.py`
✅ Frontend citation parsing and Sources UI remain outside this changeset — `frontend/`
