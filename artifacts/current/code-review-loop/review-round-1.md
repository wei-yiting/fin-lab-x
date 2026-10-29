# Code Review Round 1

> Reviewer: gpt-5.6-luna | Date: 2026-08-26

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 1 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 0 |

## Issues

### [Major] M-1.1: Tests do not follow the required real-fixture contract
- **File:** `backend/tests/evals/test_html_arm_compat.py` L37
- **Problem:** Multiple tests use synthetic or altered chunks despite the module claiming that only one defensive-path test is synthetic. `test_normalize_chunks_maps_normalize_chunk_over_a_list` uses invented `"text": "unchanged"` payloads, and the nested-heading test shortens the recorded table text. This weakens confidence in a score-affecting compatibility layer. Eval measurement rigor is a §4 Production-Grade Zone requirement.
- **Fix:** Load exact chunk payloads from `2026-08-19_73faf5f.csv` through a shared fixture/parser. Keep only the `Item 99` test synthetic, and explicitly document that exception.

### [Minor] m-1.1: Chunk contract is erased by untyped `dict`
- **File:** `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py` L54
- **Problem:** `dict` and `list[dict]` provide no schema for required fields such as `item`, `header_path`, `ticker`, and `year`, contrary to the repo's strict typing guideline. This makes the reusable API's input/output contract implicit.
- **Fix:** Define a chunk payload type with `TypedDict` or an equivalent typed protocol, and use it in both normalization functions.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None identified |

## Official Standards Check

N/A — no external libraries in this change.

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-luna | Date: 2026-08-26

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 1 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 1 |

## Findings

### [Blocking] SP-1.1: Tests include invented fixtures

- **Type:** Misimplemented
- **Spec:** "As 這張 PR 的 reviewer, I want unit test 的 fixture 是從真實錄下的 frozen HTML pipeline 輸出取出來的，不是憑空編的字串, so that 我能相信測試反映的是 pipeline 的真實行為，不是簡化過的想像。" (User Stories #9)
- **File:** `backend/tests/evals/test_html_arm_compat.py` L41
- **Problem:** `test_normalize_chunks_maps_normalize_chunk_over_a_list` uses manually simplified chunks with invented `"text": "unchanged"` and incomplete metadata. The `"Item 99"` fixture at L200 is also explicitly synthetic. This conflicts with the requirement that fixtures come from recorded frozen HTML pipeline output.
- **Fix:** Use verbatim recorded chunks from the reference measurement for every input fixture. For the unknown-title branch, retain a real recorded chunk and make the canonical-title lookup unavailable through a controlled test seam rather than inventing an input payload.

## Covered Requirements

✅ Independent importable compatibility module for `sec_retrieval_ab` — `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py`
✅ Public `normalize_chunk` and `normalize_chunks` functions — `html_arm_compat.py` L54, L88
✅ `sec_retrieval` scorer remains unmodified — changeset contains no scorer changes
✅ Canonical Item title reconstruction from `item` and `TENK_STANDARD_TITLES` — `html_arm_compat.py` L60–L85
✅ Unknown item and unrecognized title pass through unchanged — `html_arm_compat.py` L60–L66
✅ Part segment removal — `html_arm_compat.py` L80–L85
✅ Nested block-heading tail preservation — `html_arm_compat.py` L80–L83
✅ Chunk `text` passes through unchanged — `html_arm_compat.py` L54–L58
✅ Explicit future text-normalization extension point — `html_arm_compat.py` L32–L34
✅ Design rationale is contained in the module docstring; no ADR or glossary entry added — `html_arm_compat.py` L36–L44
✅ No dependency on `sec_retrieval_ab` dataset or `eval_spec.yaml` — `__init__.py` L1–L5
✅ Tests are deterministic and offline, with no Qdrant, network, or LLM calls — `test_html_arm_compat.py`
✅ Added terminology uses "frozen HTML pipeline" / "HTML arm", not "baseline" — all changed files
✅ No `sec_retrieval_ab` scenario wiring or formal A/B measurement was added — changeset scope

---

## Discussion Gate Resolution (orchestrator + user, 2026-08-26)

### M-1.1 / SP-1.1 — Tests do not follow the real-fixture contract
**Status: Undisputed — fix as suggested, scope expanded.**

Orchestrator verified both reviewers' claims directly against
`backend/evals/regression/reference_measurements/sec_retrieval/2026-08-19_73faf5f.csv`
before the discussion gate. Confirmed:
- `test_normalize_chunks_maps_normalize_chunk_over_a_list` — `"text": "unchanged"` is invented, not recorded.
- `test_normalize_chunk_preserves_nested_block_heading_tail` (NVDA/2026 chunk_index=128) — the real
  recorded chunk is a full multi-column financial table with header rows; the test's `text` is a
  hand-simplified single markdown row, not a verbatim excerpt.
- **Additional instance found by the orchestrator, not flagged by either reviewer**:
  `test_normalize_chunk_replaces_wording_divergent_title_with_canonical_form` (NVDA/2026
  chunk_index=308) — the test's `text` reads "...Taiwan-headquartered suppliers." but the real
  recorded chunk reads "...Taiwan-headquartered customers was attributed to end customers based
  in the United States and Europe." "suppliers" does not appear anywhere in the source — this is
  a content fabrication, not a truncation.

User confirmed: fix all three instances. Pull exact verbatim payloads (full `text` field, not
truncated/edited) from the CSV for every fixture that claims to be a real recorded chunk. Only
the `Item 99` defensive-path test stays synthetic, as its docstring already discloses. Truncating
a real chunk's `text` to a shorter verbatim prefix (as the INTC/134, AMD/152, and NVDA/25 fixtures
already do) is acceptable — the issue is fabricated/altered content, not length.

### m-1.1 — Chunk contract is untyped `dict`
**Status: Disputed — dismissed by user.**

Orchestrator's assessment: the sibling module this compatibility layer feeds,
`backend/evals/scenarios/sec_retrieval/scorer.py`, uses plain `dict`/`list[dict]` throughout for
the exact same chunk shape (no `TypedDict`) — introducing a `TypedDict` here would be inconsistent
with the untyped scorer this module is designed to interoperate with, for a module that is itself
scheduled for deletion at frozen-HTML-pipeline sunset. Repo-convention-overrides judgment call.

User decision: dismiss. Do not re-raise in subsequent rounds.
