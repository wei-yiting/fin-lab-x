# Fix Round 3

> Fixer: Claude (code-fixer subagent) | Date: 2026-08-20

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-3.2 | Split ADR-0017 into three single-decision ADRs, per a content classification worked out collaboratively with the user across several discussion turns. **ADR-0017** (kept, trimmed to ~524 words) now covers only "generation stays in the Orchestrator loop, retrieval is a tool" — Rejected #3 (Model-emitted URLs) and 4 of 6 Consequences bullets moved out; a linking sentence to ADR-0018 was added. **New ADR-0018** ("SEC citations are prompt-driven and model-numbered, bound to stable per-chunk IDs", 526 words, dated 2026-08-20 with an honest lineage note — the decision itself dates to 2026-08-05, refined 2026-08-19) carries the citation-numbering scheme, including one new Why bullet (the fixer's judgment call, explicitly permitted) explaining why numbering must be global and model-owned. **New ADR-0019** ("SEC filing URLs travel as UI-only tool artifacts, never in model-visible content", 359 words, dated 2026-08-19) carries the `ToolMessage.artifact`/streaming decision, with a freshly written Rejected (prompt-only suppression) and Why (structural guarantee beats a prompt guarantee) since that reasoning previously only existed implicitly. All cross-references updated: `docs/adr/0010-...md` line 36, `sec_filing_search.py` docstring, and `tools/README.md` now point to ADR-0018 (citation-ID territory); `docs/adr/0010-...md` line 4 and `test_orchestrator_prompt_rendering.py` correctly stayed on ADR-0017 (tool-existence territory). Repo-wide grep confirmed no stray references. | `docs/adr/0017-rag-generation-in-orchestrator-loop.md`, `docs/adr/0018-sec-citations-are-prompt-driven-and-model-numbered.md` (new), `docs/adr/0019-sec-urls-travel-as-ui-only-tool-artifacts.md` (new), `docs/adr/0010-rag-over-long-context-filing-reading.md`, `backend/agent_engine/tools/sec_filing_search.py`, `backend/agent_engine/tools/README.md` |
| M-3.3 | Added `@field_validator("ticker")` mirroring the existing `_query_not_blank` validator: strips the value, raises `ValueError("ticker must not be blank")` if empty after stripping. Added `test_blank_ticker_rejected_before_retrieval` asserting `ticker="   "` raises `ValidationError` via `.ainvoke()` before `search`/`locate_filing_ref` run. | `backend/agent_engine/tools/sec_filing_search.py`, `backend/tests/tools/test_sec_filing_search.py` |
| M-3.4 | `locate_filing_ref()` now wraps the `filing.accession_number`/`filing.period_of_report` reads and the `int(period_of_report[:4])` parse in try/except, raising via `_classify_edgar_error(...)` on failure — mirroring the established precedent in the same file (`_fetch_filing_bundle_cached`). Added an explicit `if not accession_number: raise SECError(...)` check on the raw value so `str(None)` can never silently become the literal string `"None"` flowing into a citation ID. Added two tests: `accession_number=None` → `SECError`; malformed `period_of_report` → classified error, not a bare `ValueError`. | `backend/common/sec_core.py`, `backend/tests/common/test_sec_core.py` |
| m-3.1 | Inlined `_filing_key()`'s one-line body directly into `_citation_id()` and removed the separate function (Fowler Middle Man), keeping a short WHY comment. No test referenced `_filing_key` directly. | `backend/agent_engine/tools/sec_filing_search.py` |
| m-3.2 | `tools/README.md`'s "Why three SEC paths" section incorrectly said only the first two surfaces share `sec_core`/`FilingType`/`SECError` — `sec_filing_search.py` does too. Changed "The first two share..." to "All three share...". | `backend/agent_engine/tools/README.md` |

## Not Fixed

None — all approved fixes landed.

## Reverted (fix broke tests)

None.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run ruff format --check backend/` | ✅ Pass | 210 files already formatted |
| `uv run ruff check backend/` | ✅ Pass | All checks passed |
| `uv run pytest backend/tests/ -q` | ✅ Pass | 1262 passed, 55 deselected (was 1259 before this round; +3 new tests, 0 regressions) |

Orchestrator independently re-ran `ruff check`, `ruff format --check`, and the full test suite after the fixer completed — all green — and read every changed/new file in full (both new ADRs verbatim, the trimmed ADR-0017, every cross-reference, and each of the four code diffs) against the exact content classification and instructions given. Everything matched precisely; no discrepancies found.

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|----------------|
| `backend/tests/tools/test_sec_filing_search.py` | Added `test_blank_ticker_rejected_before_retrieval` | Whitespace-only `ticker` raises `ValidationError` before retrieval (M-3.3) |
| `backend/tests/common/test_sec_core.py` | Added `test_locate_filing_ref_none_accession_number_raises_sec_error` | Missing `accession_number` raises `SECError`, never becomes the literal string `"None"` (M-3.4) |
| `backend/tests/common/test_sec_core.py` | Added `test_locate_filing_ref_malformed_period_of_report_raises_classified_error` | Malformed `period_of_report` surfaces as a classified error, not a bare `ValueError` (M-3.4) |

---

## Discussion Gate Record (Round 3) — items resolved without a code change

### Dismissed (user decision, with investigation) — will not be fixed, do not re-raise

| Issue ID | Reason |
|----------|--------|
| M-3.1 | `@observe(name="sec_filing_search")` was flagged as contradicting `streaming_observability_guardrails.md` Rule 3. Investigated: all three of `sec_filing_search`'s sibling SEC tools (`sec_filing_list_sections`, `sec_filing_get_section`, `sec_filing_downloader`) already used `@observe` for the same "blocking I/O" reason on `origin/main`, confirmed present before this branch existed (verified via `git show origin/main:...` and `git diff` on `test_observe_decorators.py`, which shows only 4 added lines registering the new tool into an already-existing allow-list). `sec_filing_search` conforms to an established, pre-existing repo convention; it does not introduce a new violation. Whether the guardrails doc itself should be reconciled with this convention is a separate, pre-existing question out of scope for this ticket. |

### Extensively discussed, then resolved as M-3.2 above (not a dismissal)

The user pushed back twice on an initial lighter-touch proposal for the ADR-0017 length/bundling concern (first raised as M-2.1 in round 2, re-surfaced as M-3.2 in round 3). Investigation across both rounds established: (1) round 2's fix corrected the ADR's factual accuracy (the Decision text no longer contradicts the shipped design) but did not address the separate structural question of whether one file should hold three decisions; (2) checking design-envelope §4's actual ADR criterion ("every non-obvious decision... one file per decision... two fused decisions → split") against the three decisions bundled in ADR-0017 showed all three are independently reversible and non-obvious (the third — UI-only artifact transport — affects an external interface, the SSE streaming contract, which is one of the classic Nygard criteria for architectural significance); (3) the user's final call was strict: one ADR = one decision, no partial merging. Resolved via the three-way split recorded in the Fixed table above.
