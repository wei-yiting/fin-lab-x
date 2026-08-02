# Code Review Round 2

> Reviewer: gpt-5.5 | Date: 2026-08-02

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 1 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 3 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Fixed | Accepted deviation by human owner; not re-raised under the stated rules. |
| 2 | m-1.1 | ✅ Fixed | `model_fields_set` now rejects explicit `temperature=0.0` on programmatic scorers; regression tests added. |
| 3 | m-1.2 | ✅ Fixed | README llm_judge schema now documents `temperature`. |

## Issues

### [Major] M-2.1: `temperature` is an unconstrained provider parameter
- **File:** `backend/evals/eval_spec_schema.py` L21
- **Problem:** The new schema accepts any float for `temperature`, then forwards it to `LLMClassifier`/OpenAI. That allows invalid eval specs such as negative values, values above the provider range, `nan`, or `inf` to pass repo validation and fail later at provider call time. This is a new config surface in the Eval measurement zone, so boundary validation should be explicit per design-envelope.md §4.
- **Fix:** Constrain the field at schema load time, e.g. with Pydantic `Field(default=0.0, ge=0.0, le=2.0, allow_inf_nan=False)`, and add regression tests for negative, above-range, and non-finite values.
- **Context7:** OpenAI API Reference documents chat `temperature` as "between 0 and 2"; Pydantic v2 documents `Field` numeric constraints `ge`, `le`, and `allow_inf_nan`.

### [Minor] m-2.1: README local-mode example contradicts the new required OpenAI key
- **File:** `backend/evals/README.md` L26
- **Problem:** The example still says `# Local mode (default — no upload, no API key needed)`, but `language_policy` now includes an `llm_judge` scorer and `_build_judge_client()` fails immediately without `OPENAI_API_KEY`. The prerequisites table later says the key is required, so the quick-start command is internally inconsistent.
- **Fix:** Change the comment to say local mode needs `OPENAI_API_KEY` for scenarios with LLM/tool calls, but not `BRAINTRUST_API_KEY` unless `--upload` is used.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| pydantic | 2.12.5 | `model_fields_set`, `@model_validator(mode="after")` | ✅ Current | Correct documented APIs. Missing numeric constraints for the newly added `temperature` field are covered by M-2.1. |
| autoevals | 0.1.0 | `LLMClassifier(..., model=..., temperature=..., client=...)` | ✅ Current | Matches the provided official reference; no deprecated kwargs used. |
| openai | 2.24.0 | `OpenAI(api_key=..., base_url=...)` | ✅ Current | Explicit client construction is current; hardcoded OpenAI endpoint matches the ADR decision. |

---

# Spec Conformance Round 2

Skipped per dispatch criteria: Round 1's Spec axis returned 0 findings, and Round 1's
fixes touched only schema validation strictness, a test file, and README prose — none of
which can change spec conformance. The Spec axis will not be re-dispatched unless a later
round introduces SP- findings.
