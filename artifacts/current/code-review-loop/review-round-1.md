# Code Review Round 1

> Reviewer: gpt-5.5 | Date: 2026-07-21

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 2 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 3 |

## Issues

### [Major] M-1.1: `Commit marker` glossary contradicts the implementation it describes
- **File:** `CONTEXT.md` L48
- **Problem:** The glossary says the commit marker is "written as its very last step", but `backend/ingestion/sec_dense_pipeline/vectorizer.py` writes the same marker point with `status: "pending"` before chunking/upsert work, then overwrites it with `status: "complete"` at the end. L49 is also stale: it says `sentinel point` is the current RAG-path code identifier, but this diff renames the code to `commit_marker_*`. This is not just wording; future agents could remove the pending marker or misunderstand the committed/absent invariant.
- **Fix:** Rewrite the entry to match the actual state machine: marker point is written as `pending` at ingest start and overwritten as `complete` as the final commit step; retrieval treats only `complete` as present. Remove "current identifier name in the RAG-path code" or update active docs that still say `sentinel`.
- **Context7:** N/A

### [Major] M-1.2: `Production-Grade Zone` entry expands the Design Envelope without changing the SSOT
- **File:** `CONTEXT.md` L137
- **Problem:** The glossary lists "retrieval correctness" as a Production-Grade Zone, but `docs/design-envelope.md` §4 lists only Eval measurement rigor, Observability, ADRs, JIT failure legibility, and API contract. The Design Envelope explicitly says it is the calibration SSOT; adding a new zone in `CONTEXT.md` silently changes review severity and can make agents over-require robustness outside the envelope.
- **Fix:** Make this entry mirror `docs/design-envelope.md` §4 exactly, or change `docs/design-envelope.md` in the same PR if "retrieval correctness" is intentionally being promoted to a Production-Grade Zone. If the intended concept is committed/absent retrieval visibility, cite it as a §2 JIT reliability invariant instead of a §4 zone.
- **Context7:** N/A

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| | None |

## Official Standards Check

Results of Context7 verification for each library used in the changes:

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| qdrant-client | 1.17.1 | `client.retrieve(collection_name=..., ids=[...], with_payload=True)` | ✅ Current | UUID string IDs are valid; API is not deprecated. |
| qdrant-client | 1.17.1 | `client.upsert(collection_name=..., points=[...])` | ✅ Current | Matches official `upsert` usage. |
| qdrant-client | 1.17.1 | `models.PointStruct(id=..., vector=..., payload=...)` | ✅ Current | UUID string IDs and payload dicts are supported. |

---

# Spec Conformance Round 1

> Reviewer: claude-fable-5 | Date: 2026-07-21

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 1 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 1 |

## Findings

### [Major] SP-1.1: CONTEXT.md commit-marker note states the code rename is still pending, contradicting R1
- **Type:** Misimplemented
- **Spec:** "Commit marker + Committed or absent: ... _Avoid_ sentinel point (noting the code rename status)." (R2) — and "The canonical term \"commit marker\" replaces \"sentinel point\" ... `sentinel_id` → `commit_marker_id` ..." (R1)
- **File:** `CONTEXT.md` L45 (the `_Avoid_` line of the **Commit marker** entry)
- **Problem:** The note reads `_Avoid_: sentinel point (current identifier name in the RAG-path code; rename when that code is next touched)`. But R1 renamed the code identifiers in this very changeset (`sentinel_id` → `commit_marker_id`, `check_sentinel_complete` → `check_commit_marker_complete`, all locals/tests/docstrings). After 7bdae8d there is no `sentinel` identifier left anywhere in `backend/ingestion/sec_dense_pipeline/` code — the only surviving "sentinel point" usage is prose in that module's `README.md`. So "current identifier name in the RAG-path code; rename when that code is next touched" is factually false for the delivered state: it describes a pre-R1 world and misinforms a future reader into thinking the code symbols still need renaming. R2 required the note to *accurately* reflect the code rename status; here R1 (done) and R2 (says pending) contradict each other within one diff.
- **Fix:** Reword the note to reflect that the code identifiers are already renamed and that the only remaining legacy surface is documentation, e.g. `_Avoid_: sentinel point (legacy term; code identifiers already renamed to commit_marker_id — remaining references live only in backend/ingestion/sec_dense_pipeline/README.md, to be updated when that doc is next touched)`. (Renaming the README itself is out of R1's enumerated scope, so it is not required here — but the note must stop claiming the code still uses the old identifier.)

## Covered Requirements

✅ R1 code rename (`sentinel_id`→`commit_marker_id`, `check_sentinel_complete`→`check_commit_marker_complete`, locals, test names, comments/docstrings) — `backend/ingestion/sec_dense_pipeline/common.py`, `retriever.py`, `vectorizer.py`, `sec_filing_pipeline/pipeline.py`, `evals/eval_tasks.py`, `tests/.../integration/test_ingest.py`, `tests/.../unit/test_retriever.py`
✅ R1(a) uuid5 seed `f"{ticker}:{year}:_status"` byte-identical — `backend/ingestion/sec_dense_pipeline/common.py`
✅ R1(b) payload `status` values `"pending"`/`"complete"` unchanged — `backend/ingestion/sec_dense_pipeline/vectorizer.py` L122/L238
✅ R1(c) object-sentinel preserved — `backend/tests/common/test_sec_core_inflight.py` (untouched)
✅ R1(c) `[Reserved]` parsing sentinel preserved — `backend/common/sec_core.py` (untouched)
✅ R2 Capability tier entry (baseline→reader→quant→graph→analyst; Avoid v1–v5; roadmap phases keep numbers) — `CONTEXT.md`
✅ R2 Two-path SEC architecture (RAG path / fundamentals path; Avoid V2/V3 pipeline & Quant path; path=source→store, pipelines are components) — `CONTEXT.md`
✅ R2 Pipeline entry (component-layer ETL word; agents query stores, never pipelines) — `CONTEXT.md`
✅ R2 Commit marker + Committed or absent (written last; trust only marker-complete) — `CONTEXT.md`
✅ R2 EDD entry (steered by evals throughout lifecycle; Avoid final-gate framing & eval-driven-for-postponing) — `CONTEXT.md`
✅ R2 Defer until evidence as its own entry, distinct from EDD — `CONTEXT.md`
✅ R2 Eval run (one scenario × one agent config, one Braintrust experiment) — `CONTEXT.md`
✅ R2 Baseline behavior diagnostic (replaces near-v1; core/boundary/reach bands + deterministic checks; never grades answer quality) — `CONTEXT.md`
✅ R2 Waiting indicator (replaces reasoning/thinking indicator; reasoning reserved for Reasoning stream) — `CONTEXT.md`
✅ R2 sec_retrieval (span + eval scenario; qualify which) — `CONTEXT.md`
✅ R2 User-authored entries preserved (Prompt Regression Suite, Quality Track, Guardrail) — `CONTEXT.md`
✅ R2 Capability four pillars (Tools/Skills/MCP/Subagents; only Tools today) — `CONTEXT.md`
✅ R3 capability-tier renames deferred (`v1_baseline` etc. untouched) — grep across `backend/`
✅ R3 `quant_data_pipeline`→`fundamentals_pipeline` deferred (untouched) — grep across `backend/`
✅ R3 ReasoningIndicator component rename deferred (untouched) — grep across `frontend/`
✅ R3 near_v1 diagnostic rename deferred (untouched) — glossary marks it _Avoid_ with legacy note
✅ R4 issue-tracker doc (team Project-Dev/`DEV-`, project FinLab-X; parent/sub-issue + native `blockedBy`; journey-verification ticket; 300–800 net-line PR cap; trailing `Linear: DEV-XX`) — `docs/agents/issue-tracker.md`
✅ R5 domain doc (single `CONTEXT.md` + `docs/adr/`; consume/update rules) — `docs/agents/domain.md`
✅ R6 AGENTS.md `## Agent skills` section pointing to both docs/agents files — `AGENTS.md`
✅ R7 `.gitignore` ignores `.ua/` — `.gitignore`
