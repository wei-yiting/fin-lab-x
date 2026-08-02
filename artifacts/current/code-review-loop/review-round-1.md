# Code Review Round 1

> Reviewer: gpt-5.5 | Date: 2026-07-31

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 3 |
| Blocking | 0 |
| Major | 1 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 2 |

## Issues

### [Major] M-1.1: ADR violates the repo's ADR size contract
- **File:** `docs/adr/0007-llm-judge-bypasses-braintrust-gateway.md` L1
- **Problem:** `docs/design-envelope.md` §4 defines ADRs as "one file per decision" and `≤100 words`. This new ADR is 69 lines and far beyond that limit. ADRs are a Production-Grade Zone, so repo-standard violations here are Major per §7.
- **Fix:** Condense this ADR to ≤100 words: decision, rejected alternatives, why. Move detailed root-cause/cache/provider analysis to PR notes or a non-ADR artifact if it is still needed.

### [Minor] m-1.1: Programmatic scorers can still explicitly set `temperature: 0`
- **File:** `backend/evals/eval_spec_schema.py` L50
- **Problem:** The validator rejects `temperature` on programmatic scorers only when the value differs from `0.0`. That means a programmatic scorer can explicitly include `temperature: 0` and pass validation, even though the schema now claims "Programmatic ScorerConfig must not set temperature." This is unclear config behavior and weakens the strict scorer-mode split.
- **Fix:** Detect whether the field was provided, not whether its value differs from the default. In Pydantic v2, check `"temperature" in self.model_fields_set` for programmatic scorers, and add a regression test for explicit `temperature=0.0`.

### [Minor] m-1.2: README "full schema" omits the new `temperature` field
- **File:** `backend/evals/README.md` L163
- **Problem:** The README's `Eval Spec YAML Schema` section claims to show the full scorer schema, but the new `temperature` field is not documented. This leaves the public config surface inconsistent with `ScorerConfig` and `language_policy/eval_spec.yaml`.
- **Fix:** Add `temperature: float` to the `llm_judge` scorer schema example, documenting default `0.0` and that it applies only to `type: llm_judge`.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| autoevals | 0.1.0 | `LLMClassifier(..., model=..., temperature=..., client=...)` | ✅ Current | Uses the supported per-evaluator `client=` injection path. Does not use deprecated `api_key=` / `base_url=` kwargs. |
| openai | 2.24.0 | `OpenAI(api_key=..., base_url=...)` | ✅ Current | Explicit construction matches official SDK docs and correctly bypasses `OPENAI_BASE_URL` env resolution by passing `base_url` directly. |

---

# Spec Conformance Round 1

> Reviewer: claude-fable-5 | Date: 2026-07-31

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Findings

None. The changeset maps one-to-one onto the DEV-120 spec with no missing requirements, no untwisted deviations, and no additions beyond what the spec's decisions imply. Two judgment calls examined and cleared:

- The 5th unit test (`test_scorer_config_rejects_temperature_on_programmatic_scorer`) is beyond the 4 enumerated cases, but derives directly from D4's "reuse the existing programmatic/llm_judge mutual-exclusion validation" — verifying temperature participates in that exclusion is plumbing for D4, not a new capability. Not creep.
- The `_JUDGE_BASE_URL` module constant with a pointer comment to ADR-0007 is packaging of D2's hardcoded endpoint, not new surface.

## Covered Requirements

- ✅ D1: explicit client construction in scorer_registry, not env-based — `backend/evals/scorer_registry.py` (`_build_judge_client`, hardcoded `_JUDGE_BASE_URL`)
- ✅ D2: direct OpenAI `https://api.openai.com/v1` + `OPENAI_API_KEY`, no Braintrust gateway — `backend/evals/scorer_registry.py` L52-61
- ✅ D3: per-evaluator injection via `LLMClassifier(..., client=...)`; no `autoevals.init()`; no deprecated `api_key=`/`base_url=` kwargs — `backend/evals/scorer_registry.py` L83-84 (client built inside `_build_llm_judge`, per evaluator)
- ✅ D3/spec: `temperature=0` explicitly passed to LLMClassifier — `backend/evals/scorer_registry.py` L83
- ✅ D4: `ScorerConfig` gains `temperature: float = 0.0` with mutual-exclusion validation reused (programmatic branch rejects non-zero temperature inside the existing `@model_validator`) — `backend/evals/eval_spec_schema.py` L21, L50-51
- ✅ D4: language_policy `eval_spec.yaml` explicitly writes `temperature: 0` — `backend/evals/scenarios/language_policy/eval_spec.yaml` L25
- ✅ D5: missing `OPENAI_API_KEY` fails fast at judge construction; message identifies the eval judge's client, the endpoint, and the env var to set — `backend/evals/scorer_registry.py` L54-60
- ✅ D6: ADR-0007 titled "LLM judge calls bypass the Braintrust gateway", same PR, covering all six mandated points (deprecated proxy discovery, cache-benefit-near-zero with empirical detail, ADR-0006 default-semantics conflict, gateway org-side config requirement with verified 404, "two values" escape hatch, rejected alternatives with reasons) — `docs/adr/0007-llm-judge-bypasses-braintrust-gateway.md`
- ✅ Module scope exact: only scorer_registry, eval_spec_schema, language_policy eval_spec.yaml, tests, ADR touched; `eval_runner` NOT in diff — `git diff --name-only 20ad808...1ddbbb0`
- ✅ Test seam reuse: monkeypatched `scorer_registry.LLMClassifier` fake extended with `client` and `temperature` capture; base_url asserted as normalized `"https://api.openai.com/v1/"` — `backend/tests/evals/test_scorer_registry.py` (`_capture_llm_classifier`)
- ✅ Test case 1 (default construction: endpoint, key from `OPENAI_API_KEY`, temperature == 0) — `test_resolve_scorers_builds_llm_classifier`
- ✅ Test case 2 (both keys set → still OpenAI key + endpoint) — `test_llm_judge_uses_openai_key_when_braintrust_key_is_present`
- ✅ Test case 3 (`OPENAI_BASE_URL` set → still hardcoded endpoint) — `test_llm_judge_ignores_openai_base_url_env`
- ✅ Test case 4 (key absent → raises at construction, message names endpoint and variable) — `test_llm_judge_fails_fast_without_openai_api_key`
- ✅ Mock only, no real API calls — fake `LLMClassifier` never invokes the network; the `OpenAI` object is constructed but never called
- ✅ Acceptance (d)(e) verified locally: `pytest backend/tests/` → 851 passed; `ruff check backend/` → all checks passed; `ruff format --check backend/` → 156 files already formatted
- ✅ Out-of-scope guard: no dead-scorer gate changes, no judge model change, no per-run metadata recording, no gateway routing anywhere in the diff

Acceptance criterion (a) (live `eval_runner` language_policy run producing response_relevance scores) is a runtime check outside a static diff review; the mechanism that fixes it is fully present.
