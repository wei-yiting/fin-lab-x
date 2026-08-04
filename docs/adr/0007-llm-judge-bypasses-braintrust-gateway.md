# ADR-0007: LLM judge calls bypass the Braintrust gateway (2026-07-31)

**Decision**: `scorer_registry` builds every `llm_judge` scorer with an
explicitly constructed OpenAI client — `base_url` hardcoded to
`https://api.openai.com/v1`, key taken from `OPENAI_API_KEY`, injected
per-evaluator via `LLMClassifier(..., client=...)` — instead of letting
autoevals infer endpoint and key from the environment. `temperature` is an
explicit per-scorer field in `eval_spec.yaml` (default `0.0`), and a missing
`OPENAI_API_KEY` fails fast at judge construction with a message naming the
variable and the endpoint. This deliberately bypasses the Braintrust gateway
even though runtime tracing is unified on Braintrust (ADR-0005) — the
`BRAINTRUST_API_KEY` in `.env` plus this explicit detour is **not** an
oversight to be "fixed" back to the gateway.

**Context**: every `llm_judge` scorer died with
`openai.AuthenticationError: Braintrust gateway error: auth failed [401] …
org: None`. Root cause, verified in autoevals 0.1.0 source
(`autoevals/oai.py`, `prepare_openai()`): the api key default prefers
`OPENAI_API_KEY` over `BRAINTRUST_API_KEY`, while the base_url default falls
back to the Braintrust proxy when `OPENAI_BASE_URL` is unset. With both keys
in `.env` (this repo's standard) and no `OPENAI_BASE_URL`, autoevals sent the
OpenAI key to the Braintrust proxy, which cannot map it to any org.
Braintrust docs now mark `https://api.braintrust.dev/v1/proxy` as deprecated
in favor of `https://gateway.braintrust.dev/v1`; the "no account, raw
provider key" behavior belongs to the deprecated section, and the
proxy→gateway migration between April and July tightened auth (package
versions were pinned since 3/31, ruling out a version change).

**Rejected — fix via environment** (set `OPENAI_BASE_URL` in `.env`, zero
code change): patches an implicit two-variable conflict with a third
variable, enlarging the combination space; cannot be covered by a unit test;
and keeps trusting the same environment-inference mechanism that just
failed.

**Rejected — route through the Braintrust gateway**
(`https://gateway.braintrust.dev/v1` + `BRAINTRUST_API_KEY`):

1. **The cache benefit is near zero.** Braintrust auto-caches only when a
   request is eligible — `temperature=0`/`seed` present, or an explicit
   `x-bt-use-cache` header — and this PR's own `temperature=0` (D4) would
   satisfy that. But eligibility isn't a hit: the rubric embeds
   `{{output}}`, agent text differs every run, so the cache key misses
   regardless.
2. **It contradicts ADR-0006's default semantics.** The default eval run
   would silently require `BRAINTRUST_API_KEY` and spend Braintrust quota.
3. **One more invisible failure surface.** The gateway's provider keys live
   in Braintrust org settings — outside the repo, invisible in review,
   drifting only at runtime (verified empirically: requesting
   `claude-sonnet-4-5` through the gateway returned 404
   `no provider configured … Add the API key in Settings → AI Providers`).

**Rejected — global `autoevals.init()`**: `LLMClassifier` is imported in
exactly one place (`scorer_registry`), so process-wide coverage protects
call sites that don't exist (envelope §0 reachability), and `init()` makes
registry correctness depend on whether another module ran first — the very
implicit precondition this fix removes.

**Escape hatch**: client construction is a single site
(`_build_judge_client` in `scorer_registry.py`). Switching the judge to the
gateway — or any other provider — means changing two values there
(`base_url`, key env var). This is the cheap-to-reverse side of a reversible
decision; regression tests pin the contract (both keys present → OpenAI key
+ OpenAI endpoint; `OPENAI_BASE_URL` set → still the hardcoded endpoint), so
an intentional switch must update those tests, not sneak past them.

**Re-evaluate if**: eval volume grows enough that gateway-side caching with
explicit `temperature=0`/`seed` support becomes worth real money, judge
calls need multi-provider routing (e.g. DEV-123's judge-calibration work
picks a non-OpenAI judge), or autoevals fixes its inference defaults so the
key/endpoint combination can no longer diverge.
