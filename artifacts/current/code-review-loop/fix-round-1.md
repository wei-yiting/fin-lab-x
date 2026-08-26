# Fix Round 1

> Fixer: Claude (code-fixer subagent) | Date: 2026-08-19

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.3 | Added `import logging` + module-level `logger = logging.getLogger(__name__)`; in `_edgar_filing_url`'s `except (OSError, ValueError) as exc:` block, added `logger.warning("Failed to read filing-store metadata for %s FY%s: %s", ticker, fiscal_year, exc)` before `return None`. Control flow unchanged — still returns `None` in both cold-store and read-failure cases. | `backend/agent_engine/tools/sec_filing_search.py` |
| M-1.4 | Added `min_length=1` to `query` and `ticker`, `max_length=10` to `ticker`, `ge=1994` to `fiscal_year`, plus a `@field_validator("query")` that strips and rejects blank-after-strip queries. Added 4 boundary-test cases across 2 parametrized test functions asserting `pydantic.ValidationError` is raised via `.ainvoke()` and that both the `search` and `locate_filing_ref` mocks are never called. | `backend/agent_engine/tools/sec_filing_search.py`, `backend/tests/tools/test_sec_filing_search.py` |
| M-1.5 | `git mv docs/adr/0008-rag-generation-in-orchestrator-loop.md` → `docs/adr/0017-rag-generation-in-orchestrator-loop.md`; updated its H1 to `# ADR-0017: ...`; updated the 3 confirmed cross-references (`docs/adr/0010-...md` lines 4 & 36, `backend/tests/agents/test_orchestrator_prompt_rendering.py` line 144, `backend/agent_engine/tools/sec_filing_search.py` line 5) from `ADR-0008` to `ADR-0017`. Verified no remaining hits pointing at the RAG ADR — only the pre-existing, unrelated `docs/adr/0008-explicit-regression-gate-declaration.md` and its `docs/adr/0016-*` references remain, untouched. | `docs/adr/0008-...md` → `docs/adr/0017-...md`, `docs/adr/0010-...md`, `backend/tests/agents/test_orchestrator_prompt_rendering.py`, `backend/agent_engine/tools/sec_filing_search.py` |
| m-1.1 | Replaced `(schema owned by DEV-65/DEV-127)` with `(schema owned by the SEC ingestion rewrite)` in `_edgar_filing_url`'s docstring; replaced `DEV-126 evals` with `the RAG end-to-end eval` in the test module's docstring. ADR prose left untouched (repo convention allows issue-ID citations in ADRs). | `backend/agent_engine/tools/sec_filing_search.py`, `backend/tests/tools/test_sec_filing_search.py` |
| m-1.2 | Changed `` `search_sec_filings` `` to `` `sec_filing_search` `` in the capability-layer table (README.md line 90 only). | `README.md` |
| M-1.1 (docstring only — see Dismissed below for the scope-creep part) | Replaced the final sentence of `EvidenceChunk`'s docstring with the agreed wording: "This schema is the API contract the frontend citation resolver will consume once DEV-143 lands — keep both sides in sync when either changes." Rest of docstring unchanged. | `backend/agent_engine/tools/sec_filing_search.py` |

## Not Fixed

None — all approved fixes landed.

## Reverted (fix broke tests)

None.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run ruff format backend/` | ✅ Pass | 210 files left unchanged |
| `uv run ruff check backend/` | ✅ Pass | All checks passed |
| `uv run pytest backend/tests/ -q` | ✅ Pass | 1257 passed, 55 deselected (was 1253 before this round) |
| `uv run pytest backend/tests/tools/test_sec_filing_search.py -v` | ✅ Pass | 18 passed (was 14; +4 new boundary cases) |

Orchestrator independently re-ran `uv run pytest backend/tests/ -q` and `uv run ruff check backend/` after the fixer completed — both confirmed green, diff manually inspected against every agreed instruction.

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/tools/test_sec_filing_search.py` | Added `test_blank_query_rejected_before_retrieval` (parametrized: `""`, `"   "`) | Empty/whitespace `query` raises `ValidationError`; retrieval never reached |
| `backend/tests/tools/test_sec_filing_search.py` | Added `test_ticker_and_fiscal_year_bounds_rejected_before_retrieval` (parametrized: empty `ticker`, `fiscal_year=1900`) | Empty `ticker` and pre-1994 `fiscal_year` raise `ValidationError`; retrieval never reached |

---

## Discussion Gate Record (Round 1) — items NOT sent to the fixer

Recorded here for audit trail and so the Round 2 reviewers do not re-raise these. All resolved in conversation with the user before this fix round was dispatched.

### Resolved by the user's own commits (prior to fixer dispatch), not by this fix round

| Issue ID | Resolution |
|----------|------------|
| SP-1.1 | The prompt-vs-tool citation numbering mismatch is moot: commits `18926d0`/`4b9d796`/`05d650b` (rewritten before this review round completed) dropped the tool's per-call `n` ordinal entirely — `EvidenceChunk` no longer carries a chunk number, so there is no tool-side number for `[N]` to disagree with. The model owns `[N]` numbering across the whole answer; binding is via the `source` stable ID, not position. Confirmed against current code and tests (`test_prelude_once_per_group_and_no_tool_side_ordinal` asserts `"n" not in c`). |
| SP-1.2 | The same rewrite replaced the old single URL-requirement bullet with a `CITATION BY SOURCE TYPE` table in `reader/system_prompt.md` that explicitly marks SEC evidence as "no title, no URL" — the earlier contradiction (implying SEC filings need a URL) no longer exists in the current prompt text. |

### Dismissed (user decision) — will not be fixed, do not re-raise

| Issue ID | Reason |
|----------|--------|
| M-1.1 (scope-creep part: "frontend must ship in the same slice") | DEV-142's AC explicitly requires the mid-state behavior ("plain-text `[N]`, no fake source rendering — honest degradation") while frontend citation parsing is deliberately deferred to sibling ticket DEV-143 (already branched, already reviewed, tracked to adapt to this branch's 2026-08-19 tool-contract changes). Requiring frontend in this slice would violate the user's already-ratified slice split (DEV-130 comment, 2026-08-06: split into two tickets because the combined diff exceeded the 300–800 line target). Only the dangling docstring reference was fixed (see Fixed table above); a comment was posted to DEV-143 to update it once the real frontend consumer exists. |
| M-1.2 | Citation-accuracy/groundedness verification is a pre-existing, cross-cutting gap in the whole agent's citation mechanism — `baseline`'s Tavily-news and SEC-whole-section prose citations rely on the exact same unverified prompt-driven scheme and have shipped as "Live default" without an eval gate. This slice does not introduce or uniquely expose the gap; it extends an already-accepted pattern to one more source type. The correctly-scoped guard (DEV-126, RAG e2e eval: groundedness + citation accuracy + failure attribution) already exists as a scoped, queued backlog ticket, blocked only by scheduling (DEV-125, its behavioral-contract dependency, is already settled). Holding this slice to a stricter bar than the already-shipped `baseline` for the identical architectural property was judged inconsistent. |
| M-1.6 | "Phase 1" / "Phase 2" / "PRD Phase 2" are not session-local process codenames — `CONTEXT.md`'s pre-existing "Capability tier" glossary entry explicitly ratifies them as durable repo vocabulary ("Roadmap phases keep their numbers"). The reviewer rule targets ephemeral session artifacts (`S-auth-05`, `DD-3`); these labels are the opposite — long-lived, glossary-anchored, and resolvable independent of any one conversation. |
| SP-1.3 | `WORKFLOW_PROFILE` env var override in `backend/api/main.py` was kept as-is. Confirmed during discussion: this extends an existing repo pattern (`EVAL_PROFILE`, used by the regression eval gate, documented in AGENTS.md) to a second, legitimate consumer (the live API's lifespan) rather than inventing new deployment surface from scratch. Confirmed no in-flight issue conflicts — DEV-160's "production routing" controls which Qdrant *collection* the retriever hits (`SEC_TEXT_QDRANT_COLLECTION`, explicitly reusing an existing env var, per its own decision record), an orthogonal axis to which *Workflow Profile* is served. PR description will document this as the deliberate adoption of option (b) from the 2026-08-06 sync comment's three options. |
| SP-1.4 | `logging.basicConfig()` in `backend/api/main.py` kept as-is — bundled with SP-1.3 (it exists solely to make the resolved `WORKFLOW_PROFILE` observable at startup; same decision, not a separate one). |
