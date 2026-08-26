# Fix Round 2

> Fixer: Claude (code-fixer subagent) | Date: 2026-08-20

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| SP-2.1 + M-2.2 | `_filing_key`/`_citation_id`/`_build_groups` now take an authoritative `accession_number` (threaded from `filing_ref.accession_number` at the call site in `sec_filing_search()`); chunk's own `accession_number` is still preferred when present, and it's the fallback only when a legacy chunk lacks one. Docstrings rewritten to describe the new fallback accurately (the old "degrade to ticker-year key" framing is gone — that path is effectively unreachable now, since `locate_filing_ref` raises before this code runs if the filing can't be found). Test renamed to `test_missing_chunk_accession_falls_back_to_filing_ref_accession` and its assertion updated to expect `sec://0000320193-24-000123/1a#3` instead of the degraded `sec://AAPL-FY2024/1a#3`. | `backend/agent_engine/tools/sec_filing_search.py`, `backend/tests/tools/test_sec_filing_search.py` |
| SP-2.1 + M-2.2 (FilingRef.filing_date removal) | Removed the unused `filing_date: str` field from `FilingRef` and its construction in `locate_filing_ref()`. Removed the now-pointless `filing_date` parameter from the `_make_indexed_filing` test helper and updated its 3 call sites plus the `FilingRef(...)` equality assertion. Dropped `filing_date=...` from the unrelated `_filing_ref()` test helper in `test_sec_filing_search.py`. Confirmed via grep that all other `filing_date` occurrences in the repo belong to separate, still-used classes (`Chunk`, `FetchedFiling`) and were left untouched. | `backend/common/sec_core.py`, `backend/tests/common/test_sec_core.py`, `backend/tests/tools/test_sec_filing_search.py` |
| M-2.1 | Rewrote ADR-0017's Decision paragraph to describe the real, final design directly (stable per-chunk ID, no per-chunk ordinal, model self-numbers `[N]` in first-use order and binds it to a chunk via its stable ID). Fixed the stale "numbered-chunk `[N]` usage" wording in the Consequences section. Removed the "Amendment (2026-08-19, DEV-142 reader prompt review)" section entirely, folding its two refinements into two new/expanded Consequences bullets (the anti-duplicate-`[1]` rationale for model-side numbering; the `ToolMessage.artifact`/`data-tool-artifact`/`fiscal_year_end` detail). ADR number, H1 title, and every other ADR file untouched. Verified via `grep -n "numbered chunk\|Amendment (2026-08-19"` — no remaining hits. | `docs/adr/0017-rag-generation-in-orchestrator-loop.md` |
| M-2.3 | Added a `_make_failing_filing_store(exc)` helper (variant of `_make_filing_store` whose `.get()` raises) and a new parametrized test `test_edgar_url_read_failure_is_logged` covering both `OSError` and `ValueError`. Asserts the tool call still completes with `msg.artifact == {"edgar_url": None}` (control flow unchanged) and, via `caplog`, that a `WARNING`-level record naming the ticker and fiscal year was emitted. | `backend/tests/tools/test_sec_filing_search.py` |
| m-2.1 | Added a short note after the Quick start code block documenting `WORKFLOW_PROFILE` (what it selects, default `baseline`) plus one example command. | `README.md` |
| m-2.2 | Fixed `search_sec_filings` → `sec_filing_search` in the `tools/` bullet example and the Mermaid diagram edge label; fixed "traceable via LangSmith" → "traceable via Langfuse" in the Observability First principle (matches the actual stack — `backend/agent_engine/CLAUDE.md` treats adding LangSmith as a stop-and-ask condition, so the doc's prior claim was simply wrong). Added a `sec_filing_search.py` bullet to the `tools/` file list. | `docs/agent_architecture.md`, `docs/file_structure.md` |
| S-2.1 | Added a `sec_filing_search.py` bullet to `## Map`. Renamed `## Why two SEC paths` → `## Why three SEC paths` and extended the body to place `sec_filing_search.py` as the third surface (pinpoint/RAG via dense retrieval, complementing the whole-section reads). Fixed the stale `versions/` directory reference in Extension Algorithm step 5 to `agents/profiles/`. | `backend/agent_engine/tools/README.md` |

## Not Fixed

None — all approved fixes landed.

## Reverted (fix broke tests)

None.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run ruff format backend/` | ✅ Pass | 2 files reformatted (pure line-wrap, no semantic change) |
| `uv run ruff check backend/` | ✅ Pass | All checks passed |
| `uv run pytest backend/tests/ -q` | ✅ Pass | 1259 passed, 55 deselected (was 1257 before this round; +2 from the new `test_edgar_url_read_failure_is_logged` cases, the rename is net-zero) |

Orchestrator independently re-ran `uv run ruff check backend/`, `uv run ruff format --check backend/`, and `uv run pytest backend/tests/ -q` after the fixer completed — all green — and manually diffed every changed file against the agreed instructions (the tool/citation-ID fix, `FilingRef` field removal, the ADR rewrite, and all four doc fixes all match exactly).

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|----------------|
| `backend/tests/tools/test_sec_filing_search.py` | Renamed + updated | `test_missing_accession_falls_back_to_ticker_year_key` → `test_missing_chunk_accession_falls_back_to_filing_ref_accession`: a chunk with `accession_number=None` now gets the `FilingRef`'s accession number, not a degraded ticker-year key |
| `backend/tests/tools/test_sec_filing_search.py` | Added | `_make_failing_filing_store(exc)` helper + `test_edgar_url_read_failure_is_logged` (parametrized `OSError`/`ValueError`) |
| `backend/tests/tools/test_sec_filing_search.py` | Modified | `_filing_ref()` helper no longer sets `filing_date=` (field removed) |
| `backend/tests/common/test_sec_core.py` | Modified | `_make_indexed_filing` helper and its 3 call sites no longer set/pass `filing_date`; the `FilingRef(...)` equality assertion drops `filing_date=` |

---

## Discussion Gate Record (Round 2) — items resolved without a code change

### Dismissed (user decision) — will not be fixed, do not re-raise

| Issue ID | Reason |
|----------|--------|
| SP-2.2 | `_DEFAULT_SYSTEM_PROMPT` (the fallback prompt for placeholder profiles) was also updated in this branch. Investigated: it was already out of sync with `baseline/system_prompt.md` on `origin/main` *before* this branch (missing the LINK FORMAT section) — a pre-existing drift, not something this branch introduced. The fix syncs it back and adds a `test_code_coupled_prompt_contracts_present_in_every_prompt_source` regression test pinning four generic, code-coupled contract lines (the `RunBudgetMiddleware` exhaustion message, the `{max_tool_calls_per_run}` template var, the frontend's reference-definition syntax, and the half-width-bracket rule) across all three prompt sources — none of which are SEC/RAG-specific. The SEC CITATIONS block itself was confirmed absent from `_DEFAULT_SYSTEM_PROMPT`. Not scope creep. |
