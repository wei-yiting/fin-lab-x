# FinLab-X Design Envelope

> **Purpose**: the single calibration document for all design, implementation, and review decisions.
> Cite this file instead of assuming production-scale requirements.
> Robustness beyond this envelope is **over-engineering**; shortcuts inside a Production-Grade Zone (§4) are **under-engineering**. Both are defects of the same severity (§7).

---

## 0. Calibration Principles

FinLab-X is a **portfolio demonstration project** for AI-engineering roles. Its value is *depth in the differentiating zones* (§4) — agent architecture, evaluation rigor, failure observability — not breadth of production hardening. The July 2026 audit found ~8–10k removable lines; nearly all shared one cause: machinery built for scale pressures that do not exist here. Three principles prevent recurrence:

1. **Scale-pressure test.** Every piece of defensive or infrastructural machinery must name the scale pressure that forces it (many operators, many runs, large data, real deploy risk). If the pressure is not listed in §1, the machinery is out of scope — regardless of whether it is best practice at production scale.
2. **Reachability rule.** Every code path, enum state, config option, CLI flag, and schema field must be *selected or consumed by something in the repo at merge time*. Unreachable generality is deleted, not documented. (Precedent: three-provider `_init_model` branches while every config selected `openai:gpt-5-mini`; `reasoning: "unsupported"` tri-state nothing set.)
3. **Evidence gate.** A design element whose own supporting research reports weak results does not ship without the guards that research demands — or does not ship at all. (Precedent: the prelude payload field shipped always-on although its research memo found 8% clean extraction and mandated a size cap + per-item gating.)

---

## 1. Scale Envelope

| Dimension | Assumption | Implication |
|---|---|---|
| Concurrent users | ≤ 3 | FastAPI async is sufficient. Avoid global mutable state; no other concurrency hardening, no locking, no queueing. |
| Total users | ≤ 50, non-adversarial | No accounts, no RBAC, no per-user quotas, no abuse detection. |
| LLM cost exposure | Chat LLM: **BYOK** (user-supplied key, jin-t pattern) or free tier. Server-side spend (embeddings for JIT ingest, Finnhub) exists on every request. | One global **free-tier daily cap** (counter + 503 with a clear message). This is a cost guard, not rate-limiting machinery — multi-tenant quota systems stay out of scope. |
| Operators | 1 (the author) | No cross-operator coordination anywhere: no reconciliation, no comparability guards, no run registries. Git + Braintrust experiment metadata ARE the registry. |
| Company universe | **Hybrid**: a curated batch universe (`ticker_universe.yaml`, refresh CLI, ~10–20 tickers) + **JIT ingestion** for any other ticker a user asks about | Batch path is an operator convenience, not a production ETL (see §4 observability scope). JIT must handle the happy path robustly and fail *legibly* on the rest (§2). Working set: tens of companies, corpus < 50k chunks, single Qdrant collection, payload indexing only. |
| Concurrent JIT of same ticker | May happen | Every same-ticker ingest attempt (first-time or refresh) passes through one per-ticker in-process in-flight guard before touching the marker (§2) — concurrent attempts coalesce or get a legible "ingestion in progress" response. No distributed locks, no job queues. |
| Eval workload | Golden Dataset ≈ 30–100 items; a full run takes minutes; runs are sequential, single-operator | Always run the full dataset. No slicing, no scheduling, no eval cost management. |
| Request rate | < 1 QPS sustained | No load balancing, no pool tuning, no cache layers beyond what JIT itself requires. |
| Data freshness | Batch universe on manual/scheduled refresh; JIT tickers on a single staleness rule (re-fetch if older than N days, or user-triggered) | No streaming ingestion, no incremental sync, no invalidation machinery beyond the one rule. |

---

## 2. Reliability Assumptions

- **Availability: best-effort.** Cold starts and transient failures are answered by manual retry. No SLA.
- **Crash recovery: restart-and-rerun.** Nothing survives a restart except what Neon/Qdrant/DuckDB already persist. No checkpoint/job-queue machinery.
- **External API failures (EDGAR, Finnhub, LLM providers): single retry + legible error.** One deliberate exception: **upstream rate-limit signals (429 / `Retry-After`) are honored with a bounded backoff, implemented once in the shared client layer** (`sec_core`, finnhub client) — EDGAR enforces 10 req/s and Finnhub free tier 60/min, so 429 during JIT ingest is a *normal* path, and respecting it is part of failing legibly. No other backoff ladders, no circuit breakers, no fallback providers, no jitter tuning.
- **JIT failure semantics: legible failure is the standard.** Arbitrary tickers WILL hit unsupported cases (foreign filers, missing XBRL, no EDGAR presence). Required behavior: a structured, user-facing explanation of what failed and why. Silent partial/empty answers are bugs; exhaustively *handling* every filing variant is over-engineering. Ingestion is all-or-nothing per ticker — the invariant is **committed or absent**: neither a failed nor an in-flight ingest may ever yield a false-complete marker, partial retrievable state, or a mix of old and new generations. The sanctioned mechanism tier: **one per-ticker in-process in-flight guard, entered before any marker inspection or deletion — every same-ticker ingest attempt, first-time or refresh, is coalesced or rejected with a legible "ingestion in progress" response while one is running**; **write-then-commit-marker** (upsert content first, write the completion marker last; retrieval treats only marker-complete tickers as present); and **wipe-before-rerun** for refresh (delete the marker, wipe, re-ingest, re-mark — the ticker legibly reads as not-ingested meanwhile). The guard is session-busy-guard tier — an in-process set, not a distributed lock, queue, or version/generation machinery; no cross-store transactions. Proving the invariant under the implementation's actual interleavings belongs to the implementing slice's design and tests, not to this document.
- **Data integrity: re-runnable from source.** Corruption is fixed by wiping and re-ingesting the affected ticker. No cross-store transactions.

---

## 3. Non-Goals

Reviewers MUST NOT request these; implementations MUST NOT add them. **If code implementing any of these already exists, flag it for removal or simplification, not improvement.**

**Infrastructure**: horizontal scaling; multi-region/DR; accounts/RBAC/OAuth; per-user quotas or abuse detection (the §1 cost cap is the whole story); encryption beyond managed-service defaults; migration frameworks (manual scripts fine); adversarial input *hardening* — abuse detection, WAF-style rules, fuzzing, injection-hunting beyond framework defaults (basic type/shape/size validation at API and external-data boundaries is NOT this — it belongs to the §4 API-contract standard and may never be waived by citing this line); exhaustive SEC filing-variant coverage; distributed locks / ingestion queues; concurrency hardening beyond avoiding global mutable state; LLM cost optimization beyond obvious waste.

**Eval platform machinery** (single operator, minutes-long full runs — the pressures these serve don't exist): dataset slicing / subset selectors; cross-run comparability guards; run manifests / registries; multi-annotator reconciliation or latest-wins merging; eval-gated CI (see §8 for the minimal narrative exception).

**Speculative generality**: provider branches, enum states, config options, or schema fields with no in-repo consumer (Reachability rule, §0). Multi-provider abstraction is out of scope *until a second provider config actually exists in `versions/`*.

**Observability ceremony outside §4 scope**: per-retry/per-attempt event streams; pacing/throughput statistics persisted to metadata nothing reads; span instrumentation of operator batch jobs; defensive multi-fallback wrappers around vendor-SDK private attributes.

---

## 4. Production-Grade Zones (do NOT simplify these)

These zones ARE the portfolio. Hold them to production standards; flag shortcuts as under-engineering at the same severity as over-engineering elsewhere.

| Zone | Standard |
|---|---|
| **Eval — measurement rigor** | The question: *"can these scores be trusted?"* Rigor does not depend on scale and applies in full: (a) Golden Dataset versioned in git with per-item curation rationale (why selected, which failure mode); (b) LLM judge validated against human-labeled ground truth with reported **TPR/TNR per dimension**; (c) rubrics binary and calibrated — never free-form 1–5; (d) dimensions derived from observed failures, mutually distinguishable, and **able to move when the compared thing changes** (a dimension the pinned model holds constant across versions is dead weight); (e) reproducibility: judge model, temperature, dataset version recorded per run; (f) component-level evals (retrieved chunks, SQL, tool selection), not only end-to-end. Platform machinery stays excluded per §3. |
| **Observability** | Scope: **user-facing execution paths** — agent runtime (chat, tool calls, reasoning), eval runs, and JIT ingestion triggered by a user query — fully traced in Langfuse; every failure attributable to a failure-taxonomy category from the trace alone; no silent failures. Granularity cap: deep enough to attribute root cause, no deeper — per-retry event streams and throughput stats are §3 ceremony. Operator batch refresh gets logs + one run-summary record, not span trees. |
| **Architecture decision records** | Every non-obvious decision appended to `docs/decisions.md` (ADR style: ≤100 words, decision + rejected alternatives + why). Long-lived, append-only; `design.md` files remain per-feature and disposable. Where this envelope reduced robustness, the ADR cites §9. |
| **Retrieval correctness** | Multi-ticker isolation (metadata filtering) must be *correct*, not best-effort — cross-ticker bleed is a demo-killing bug, and the JIT-grown ticker set makes this a moving surface. The filter contract carries a regression eval. |
| **JIT failure legibility** | Per §2 — this is demo-facing behavior (viewers WILL type unsupported tickers) and is held to production standard. |
| **API contract** | Response schemas typed and stable; errors structured and actionable (they appear in demos and walkthroughs). Requests get basic type/shape/size validation at the boundary (framework-level, e.g. Pydantic 422s). The same standard covers **external-data response boundaries**: EDGAR/Finnhub/LLM/tool payloads pass through typed adapters that turn shape/size violations into structured, trace-attributable errors — never silent partial answers. Neither is §3 adversarial hardening; fuzzing and abuse detection stay out of scope. |

---

## 5. Testing Envelope

Test depth follows the zone map — tests are subject to the same proportionality rules as the code they test.

| Target | Standard |
|---|---|
| §4 zones | Behavior-driven, thorough. **Scorers and judges are themselves code under test** — an untested scorer is under-engineering in the highest-value zone (precedent: `ticker_precision_scorer` shipped with zero tests while the discarded control harness had full coverage). |
| Everything else | Happy path + one legible-failure case per behavior. Stop there. |

**Global rules (same rank as the TDD iron law, not advisory):**

1. **Never test the language, stdlib, or a pinned dependency.** No asserting a frozenset is a frozenset, that classes have docstrings, or how DuckDB/yfinance behave. (Precedent: the 254-line DST spring-forward test exercised DuckDB, not our code.)
2. **Scenario ≠ test module.** N BDD scenarios collapse into parametrized cases; a scenario ID names a *verification*, not a file. No live-API "drift watchdog" suites.
3. **Shared fixtures.** Stub factories live in `conftest.py`/shared factories. DAMP applies to assertion readability, not to re-implementing stubs per file. (Precedent: `_good_info()` re-implemented in 6 files.)
4. **No test seams in production code.** No test-only env flags, branches, or methods in product source (`STUB_*`/`EMIT_*`/`FORCE_*` precedent). Determinism is injected at the test boundary (fixture chunks, MSW, fakes).
5. **Volume is a signal, not a virtue.** A diff whose test lines exceed ~2× its production lines needs one sentence of justification in the PR; "comprehensive coverage" is not praise.

---

## 6. Documentation Envelope

- README only where behavior is not evident from the code; **no per-test-folder READMEs** (precedent: two shipped already describing flags and events that don't exist).
- Schema/column comments: one line.
- `docs/decisions.md` is the durable narrative (§4); per-feature `design.md` is disposable and may go stale without maintenance obligations.
- The production alternative to any envelope-reduced behavior is one line (§9), not a design section.

---

## 7. Reviewer Rubric

Apply in order:

1. Concern inside a §4 zone? → review at full production standard. Shortcut = **Major**.
2. Concern involves machinery/scenarios excluded by §1–§3? → absence is correct. If the diff *implements* it anyway → **Major (over-engineering)**, with removal as the required fix.
3. Would the failure mode break a live demo or walkthrough — including a viewer typing an arbitrary ticker? → require the *simplest* handling that surfaces a clear error.
4. Otherwise: optional polish. Mention once, never block.

**Severity floor:** over-engineering findings are at minimum **Major** when they add API surface, config options, schema fields, or a new module — they are never mere style suggestions.

**Deletion is a fix.** The fix round is empowered (and expected) to delete reviewer-flagged unreachable branches, consumer-less abstractions, forbidden-zone machinery, and rule-violating tests — without escalation.

**Review the plan before the diff.** Spec-conformance review first checks the *plan* against this envelope; a diff faithfully implementing an over-scoped plan is still over-engineered. Plans are not ground truth; this document is.

**Tie-breakers.** Eval concern → "measurement rigor (can the score be trusted?)" is in scope; "platform (does this survive many people/runs/data?)" is not. JIT concern → "fails legibly" is in scope; "succeeds on every input" is not.

---

## 8. Narrative-Value Exception

A §3-excluded component may be reinstated in **minimal form** only if it directly serves the demonstration narrative (interview walkthrough, talk, published content). The reinstated version must be the simplest that tells the story (e.g., a ~5-item CI smoke-eval, not an eval gate), and the narrative purpose must be recorded in `docs/decisions.md` citing this section. "Might be useful someday" is not a narrative purpose.

---

## 9. Production Path Convention

Where this envelope deliberately reduces robustness, note the production alternative in one line at the site:

```
# Envelope §1: ≤3 concurrent users. Production path: per-ticker ingestion queue + distributed lock.
```

This preserves the interview narrative ("I know the production version; here's why I didn't build it") without building it.

---

## 10. Case Law

Canonical precedents from the July 2026 audit — reviewers pattern-match against these:

| Precedent | Rule it anchors |
|---|---|
| `compare_guard.py` — 166-line CLI + 6 verdicts to tell one operator two full runs are comparable | §3 eval platform; §0 scale-pressure |
| 4-mode `dataset_selector` + SHA-256 slice hashing for a 31-row CSV | §3 eval platform |
| Prelude payload field vs its own 8%-success research memo | §0 evidence gate |
| Dead Anthropic/Gemini branches; `reasoning:"unsupported"` tri-state | §0 reachability |
| `STUB_*`/`EMIT_*`/`FORCE_*` env flags in streaming prod code | §5 rule 4 |
| 254-line DST test (tests DuckDB); frozenset-is-frozenset tests | §5 rule 1 |
| Live yfinance "drift watchdog" suite guarding an abandoned vendor | §5 rule 2 |
| Per-retry OTel events + pacing stats persisted to audit metadata nothing reads | §4 observability granularity cap |
| Test-folder READMEs documenting nonexistent flags | §6 |
| `ticker_precision_scorer` shipped untested while throwaway control code had full coverage | §5 zone standard (under-engineering) |

---

## 11. Change Control

This envelope changes only via explicit PR. If a task appears to require exceeding it, stop and surface the conflict to the author instead of silently expanding scope. Reviews cite sections by number (e.g., "out of scope per §3; see case law: compare_guard").
