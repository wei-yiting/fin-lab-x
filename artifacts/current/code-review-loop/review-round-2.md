# Code Review Round 2

> Reviewer: gpt-5.5 | Date: 2026-07-21

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 2 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ⚠️ Partially Fixed | The state-machine definition now matches `vectorizer.py`, but the `_Avoid_` note is still false: RAG-path `sentinel` prose remains in `docs/agent_architecture.md` and `docs/file_structure.md`, not only `backend/ingestion/sec_dense_pipeline/README.md`. |
| 2 | M-1.2 | ✅ Fixed | The inline Production-Grade Zone list was removed; `CONTEXT.md` now points to `docs/design-envelope.md` §4 as the authoritative list. |

## Issues

### [Major] M-2.1: `Commit marker` glossary still misstates where the legacy term remains
- **File:** `CONTEXT.md` L49
- **Problem:** The glossary says `sentinel point` survives only in `backend/ingestion/sec_dense_pipeline/README.md` prose, but `rg` shows the same RAG-path concept still described as `sentinel` in `docs/agent_architecture.md` L102/L106/L113/L123 and `docs/file_structure.md` L48. This is agent-facing documentation, so the new canonical glossary is immediately contradicted by other repo navigation docs.
- **Fix:** Update all RAG-path prose references to use `commit marker`, or make the `_Avoid_` note accurately list every known legacy-doc location. Prefer updating the stale docs now; otherwise the glossary is not a reliable source of vocabulary.
- **Context7:** Not applicable.

### [Major] M-2.2: `Committed or absent` is documented as an invariant, but generic retrieval can still see partial ingest chunks
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L307
- **Problem:** `ingest_filing()` writes content chunks in batches before the marker is overwritten to `status: "complete"` (`vectorizer.py` L226-L242). If Qdrant accepts one content batch and a later batch or final marker upsert fails, those content chunks have no `status` payload. `search()` only excludes points whose own `status` is `pending`/`complete`, so unfiltered/general vector search can return chunks from an ingest whose commit marker is still `pending`. That contradicts `CONTEXT.md` L51-L52 and `docs/design-envelope.md` §2: retrieval must not see partial data.
- **Fix:** Make retrieval gate content by completed `(ticker, year)` markers, not merely by excluding marker points. Add a regression test that simulates failure after at least one content batch is written and proves `search(query, filters=None)` does not return that ticker/year until its marker is complete.
- **Context7:** Not applicable.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| None | N/A | N/A | ✅ Current | No library call site changed in Round 2; Round 1 qdrant-client verification remains applicable. |

## Orchestrator verification notes

- **M-2.1 CONFIRMED** by independent repo-wide grep: RAG-path "sentinel" prose remains in `docs/agent_architecture.md` L102/106/113/123, `docs/file_structure.md` L48, and `backend/ingestion/sec_dense_pipeline/README.md` L24/44/78/80. (Frontend hits are unrelated sentinels — Markdown stream sentinel, RunBudgetMiddleware sentinel — correctly out of scope.) Root cause of the Round-1 miss: the fixer's verification grep was scoped to `backend/ingestion/` by the orchestrator's own fixer prompt; the spec reviewer confirmed with the same scope.
- **M-2.2 mechanics CONFIRMED** by reading `retriever.py` `search()`: `must_not status ∈ {pending, complete}` excludes only marker points; content chunks carry no `status` payload, so they are visible to unfiltered search while their marker is `pending`. Pre-existing behavior, not introduced by this diff (rename-only). Linear DEV-73 (`guard → wipe → ingest → mark`) covers the ingest side but explicitly excludes `retriever.py` ("P2 群,另案") — the retrieval-gating fix has no owning issue yet.

---

# Spec Conformance Round 2

> Reviewer: claude-fable-5 | Date: 2026-07-21

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Spec Findings Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | SP-1.1 | ✅ Fixed | Reworded `_Avoid_` line now states code identifiers are already renamed to `commit_marker_*` and the term survives only in `backend/ingestion/sec_dense_pipeline/README.md` prose. Independent `grep -rn -i sentinel backend/ingestion/` returns exactly 4 hits, all in that README (L24, L44, L78, L80) — the note's factual claim is accurate. Confirmed via `grep -rn -i commit_marker backend/ingestion/` that code identifiers are renamed in `retriever.py`, `vectorizer.py`, `common.py` (no `sentinel` identifier remains in code). *(Orchestrator note: this ✅ holds only within the `backend/ingestion/` scope both the fixer and this reviewer used; quality-axis M-2.1 shows the note's "only in README" claim is false repo-wide — see M-2.1.)* |

## Findings

None.

## Covered Requirements

✅ **Commit marker + Committed or absent (spec R2)** — Rewritten entry (`CONTEXT.md` L47–49) is faithful to code: `vectorizer.py` L111–126 writes the `commit_marker_id(ticker, year)` point with `status: "pending"` at ingest start; L229–242 overwrites the *same* marker point ID with `status: "complete"` as the final upsert before `finally: client.close()` — the last commit step. `common.py` L39–42 `check_commit_marker_complete` returns True only when `payload.status == "complete"`. The entry carries the ratified meaning: write-`complete`-last discipline + trust-only-`complete` retrieval → "committed or absent."

✅ **Production-Grade Zone (user-directed fix)** — `CONTEXT.md` L138 matches the approved wording verbatim: "An area held to full production standard because it is the portfolio value itself. The authoritative zone list and per-zone standards live in design-envelope §4 — never enumerate them elsewhere." The prior inline enumeration (eval rigor, observability, ADRs, retrieval correctness, failure legibility, API contract) is removed; no enumeration remains. Pointer is valid: `docs/design-envelope.md` §4 "Production-Grade Zones (do NOT simplify these)" (L59) holds the authoritative `| Zone | Standard |` table (L63).

✅ **No collateral drift** — `git show --stat 5db529e` confirms the fix commit touched only `CONTEXT.md` (+3/−3); the diff is exactly the two entry rewrites above. All other ratified entries confirmed in Round 1 remain intact.
