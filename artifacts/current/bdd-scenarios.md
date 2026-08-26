# BDD Scenarios

## Meta
- Spec Reference: Linear DEV-142 (ticket), parent DEV-130 (spec), ADR-0010, ADR-0017, ADR-0018, ADR-0019
- Generated: 2026-08-20
- Discovery Method: Three Amigos (Agent Teams — PO, Dev, QA; 3 challenge rounds + Phase 2.5 assumption check)
- Note on spec currency: `artifacts/current/design.md` (2026-08-06) predates ADR-0018/0019 (2026-08-19/20) and is stale on citation-numbering and EDGAR-URL-delivery mechanics. This document follows the ADRs and the live DEV-142/DEV-130 issue text, not design.md, wherever they conflict.

---

## Feature: `sec_filing_search` tool — evidence retrieval and shaping

### Context
New async Orchestrator tool `sec_filing_search(query, ticker, fiscal_year?)`, registered only in the `reader` Workflow Profile. Wraps the existing retriever's `search()` unchanged (JIT ingestion, cache, commit-marker, `sec_retrieval` span — none of that is retested here) and returns citable, structured evidence chunks instead of raw retrieval hits. Sits inside two design-envelope §4 Production-Grade Zones — **JIT failure legibility** and **API contract** — so this Feature is held to full rigor; every failure needs a structured, user-facing, *accurate* explanation.

### Rule: Malformed tool arguments fail legibly, not with a crash

#### S-tool-01: Model passes `ticker` as a list instead of a string
> Verifies that a schema-invalid argument produces a legible error, not an uncaught exception that kills the turn

- **Given** a `reader`-profile conversation comparing AAPL and TSLA
- **When** the model's tool call produces `ticker=["AAPL","TSLA"]` (a list, not a string — a natural mistake since a cross-ticker question itself suggests a multi-ticker call)
- **Then** the call fails with a structured, legible error explaining `ticker` must be a single value — not an uncaught exception, and the rest of the conversation turn is not aborted

Category: Illustrative
Origin: Dev

#### S-tool-02: `fiscal_year` given as a two-digit shorthand
> Verifies that a malformed (but plausible) fiscal_year value produces a message distinguishable from a genuinely-checked "doesn't exist"

- **Given** a user's question uses financial shorthand ("FY24")
- **When** the model calls `sec_filing_search(ticker="AAPL", fiscal_year=24)`
- **Then** the response is recognizable as a malformed-input rejection — not the same message shape as "AAPL has no FY24 10-K" (which would imply the tool genuinely checked and found nothing, when it never checked a real year at all)

Category: Illustrative
Origin: QA, sharpened by Dev
Note: which layer rejects this (schema-level range constraint vs. business-logic lookup) is an implementation choice the spec doesn't pin down — only the message's distinguishability from a genuine not-found result is asserted.

---

### Rule: `fiscal_year` resolution — omitted resolves to the latest 10-K and reports how; a ticker with no 10-K history fails legibly

#### S-tool-03: Omitted `fiscal_year` resolves to the latest 10-K
> Verifies auto-resolution and that the method is reported

- **Given** AAPL has multiple 10-K filings on EDGAR, the latest being FY2024
- **When** `sec_filing_search(query="supply chain risk", ticker="AAPL")` is called with `fiscal_year` omitted
- **Then** the result resolves to FY2024 and reports `fiscal_year_source` indicating auto-resolution — the model never has to guess this fact itself

Category: Illustrative
Origin: PO

#### S-tool-04: Explicit `fiscal_year` reports as caller-specified, even when it matches what auto-resolution would pick
> Verifies the condition used to determine `fiscal_year_source` is "was the argument omitted," not "does the resolved value match the auto-resolve result"

- **Given** AAPL's latest 10-K fiscal year is FY2025
- **When** `sec_filing_search(query=..., ticker="AAPL", fiscal_year=2025)` is called with `fiscal_year` explicitly given (numerically identical to what omitting it would resolve to)
- **Then** `fiscal_year_source` reports "caller-specified," not "auto-resolved"

Category: Illustrative
Origin: QA, confirmed real bug class by Dev (lower-probability but cheap regression insurance)

#### S-tool-05: A ticker with no 10-K filing history ever
> Verifies the auto-resolution failure path is legible, not a crash on an empty candidate set

- **Given** `ticker="XYZ"` is a real EDGAR filer that has only ever filed Form 20-F (a foreign private issuer), never a 10-K
- **When** `sec_filing_search(query=..., ticker="XYZ")` is called with `fiscal_year` omitted
- **Then** the tool returns a structured, legible failure explaining there is no 10-K to resolve a fiscal year from — not an uncaught exception from an empty-sequence resolution, and not a silent `fiscal_year=None` flowing into retrieval

Category: Illustrative
Origin: Dev

---

### Rule: A fiscal year that doesn't exist for a ticker fails legibly, and the message accurately distinguishes *why*

Three distinct non-existence reasons must not collapse into the same message, because at least one pairing would otherwise state something false to the user.

#### S-tool-06: Three non-existence reasons produce distinguishable, accurate messages

| Situation | fiscal_year | Reason | Expected message shape |
|---|---|---|---|
| AAPL, a year before the company existed | 1975 (Apple IPO'd 1980) | Structurally impossible — will never exist | States this year could never have a 10-K |
| AAPL, the current fiscal year, not yet ended/filed | 2026 (today is 2026-08-20; Apple's FY ends late September) | Not yet due — will exist later | States the filing isn't available yet — distinct from "will never exist" |
| AAPL, a real past fiscal year, upstream source temporarily unreachable | 2019 | Temporarily unavailable | States a transient retrieval problem — must NOT say "AAPL has no FY2019 10-K," which would be a false statement about SEC filing history |

- **Given** each row's `(ticker, fiscal_year)` and upstream condition
- **When** `sec_filing_search` is called
- **Then** the three messages are distinguishable from each other, and none states something factually false about whether the filing exists

Category: Illustrative (table-driven)
Origin: PO (2-category split) + QA (3rd category: not-yet-due) + Dev (conflation risk between "doesn't exist" and "temporarily unavailable")
Note: the *exact* cutoff logic for "not yet due" (e.g. statutory filing deadline vs. a simpler buffer heuristic) is an implementation-precision choice the spec doesn't promise — only the message-shape distinction is asserted here, per PO's Round 3 judgment.

---

### Rule: Evidence is grouped by (ticker, fiscal_year, item), ordered by document position; a prelude appears once per group, within a call

#### S-tool-07: Chunks are grouped and ordered by document position, not retrieval score
> Verifies grouping and within-group ordering

- **Given** a query hits AAPL FY2024 Item 1A at `chunk_index=3` (score 0.91) and `chunk_index=7` (score 0.95)
- **When** `sec_filing_search` returns its result
- **Then** both chunks are in the same (AAPL, FY2024, Item 1A) group, with `chunk_index=3` before `chunk_index=7` — document order, not score order

Category: Illustrative
Origin: PO

#### S-tool-08: Prelude appears once per group per call; a later call may legitimately reprint it
> Verifies prelude-once-per-group scope is per-call (a documented expected behavior, not a defect, since the tool is stateless per call)

- **Given** one call hits both Item 1A (3 chunks) and Item 7 (2 chunks)
- **When** the result is formatted
- **Then** each item's prelude appears exactly once in that call's result, not once per chunk
- **And** given a second, independent `sec_filing_search` call in the same answer also hits Item 1A, its prelude legitimately appears again in that second call's result — this is expected behavior, not a bug, and must not be reported as a defect during manual verification

Category: Illustrative
Origin: PO (base rule) + Dev (per-call scope clarification, confirmed by PO's Round 3 judgment)

---

### Rule: Each chunk carries a stable ID, composed title, and score, but no per-chunk ordinal; a FlatItem's title degrades gracefully

#### S-tool-09: Standard chunk fields
> Verifies the evidence-object shape

- **Given** a chunk from AAPL FY2024, Item 1A, subsection "Competition," `chunk_index=7`
- **When** it's returned as part of a `sec_filing_search` result
- **Then** it carries `source="sec://{accession_number}/Item1A#7"`, `title="AAPL FY2024 10-K · Item 1A · Competition"`, `subsection="Competition"`, `content` (the passage text), and `score` (a float) — and carries **no** ordinal/position number field

Category: Illustrative
Origin: PO, refined by ADR-0018 (no tool-side ordinal — the model assigns `[N]` itself, first-use order, across the whole answer and across tool calls, which is why the tool never emits one)

#### S-tool-10: A FlatItem chunk (no sub-heading) degrades its title, never errors
> Verifies FlatItem degradation is honest, not a required-field failure

- **Given** a chunk from an Item with no internal sub-block structure (a FlatItem)
- **When** it's returned
- **Then** `title` degrades to Item-level locator text (e.g. "AAPL FY2024 10-K · Item 7A") and `subsection` is absent — this state must never be treated as a missing-required-field error

Category: Illustrative
Origin: PO

*(Note: whether the same passage retrieved via two overlapping-but-different queries in one answer produces a byte-identical `source` ID was raised as a concern and demoted to a unit-test recommendation, not a BDD scenario — see verification-plan.md. The spec's own "document order, not score" wording, plus `source`'s components being ingestion-time-fixed chunk-schema fields this ticket only consumes, make determinism structurally guaranteed rather than an open runtime risk.)*

---

### Rule: The EDGAR URL travels only via the tool's artifact channel, never in model-visible content

#### S-tool-11: A warm filing store — content has no URL, artifact carries the real one
> Verifies the content/artifact separation (ADR-0019)

- **Given** AAPL FY2024's filing store has persisted metadata available ("warm")
- **When** `sec_filing_search` is called
- **Then** the model-visible `content` (evidence chunks + fiscal-year identity) contains no URL string anywhere, while the tool's `artifact` (delivered via `ToolMessage.artifact`, never sent to the model) carries the real EDGAR URL

Category: Illustrative
Origin: PO, per ADR-0019

#### S-tool-12: A cold filing store — artifact is null, not an error, not a guess
> Verifies honest degradation for the URL specifically

- **Given** a filing's store has no persisted metadata available ("cold")
- **When** `sec_filing_search` is called
- **Then** `artifact.edgar_url` is `null` — this is an explicit, honest degradation, never an error and never a fabricated/guessed URL — and the rest of `content` is unaffected

Category: Illustrative
Origin: PO

#### S-tool-13: [CONFIRMED DEFECT] An error during the artifact-side metadata check must not discard already-ready content
> Verifies content/artifact failure isolation — **this scenario currently fails against the implementation** (confirmed via Phase 4.5 code reading, not hypothesized)

- **Given** evidence chunks have already been successfully retrieved for a query, but the local filing-store metadata file has malformed YAML frontmatter (or an empty/scalar-only metadata block)
- **When** `sec_filing_search` attempts to resolve the EDGAR URL for the artifact
- **Then** the tool call should still succeed — returning the already-retrieved evidence chunks as `content`, with `artifact.edgar_url` degraded to `null` — the metadata-check failure must not discard content that was otherwise ready
- **Currently**: `backend/agent_engine/tools/sec_filing_search.py`'s `_edgar_filing_url` only catches `(OSError, ValueError)`, not bare `Exception`; a malformed frontmatter raises `yaml.YAMLError` or `TypeError` (neither caught), which propagates through the uncaught call site before the function's `return` statement — discarding the already-fetched evidence chunks and failing the entire tool call

Category: Illustrative
Origin: PO (Phase 2.5 assumption check — noticed as the backend-side mirror of the frontend's stream-part safety question), confirmed as a real, live defect via Phase 4.5 code reading (not a hypothetical)

---

### Rule: Multi-call answers correctly attribute each artifact to its own call, and reflect real-time state at the moment of each call

#### S-tool-14: Two calls, different identities, mixed warm/cold — no cross-contamination
> Verifies `toolCallId`-keyed attribution doesn't degrade to "last write wins"

- **Given** one answer issues two `sec_filing_search` calls in order — call 1 for `ticker="AAPL", fiscal_year=2024` (warm, real URL), call 2 for `ticker="AAPL", fiscal_year=2015` (cold, null)
- **When** both `data-tool-artifact` parts are emitted
- **Then** the part keyed to call 1's `toolCallId` still carries the real URL and call 2's still shows `null`, regardless of emission order — neither overwrites or infers from the other

Category: Illustrative
Origin: Dev

#### S-tool-15: Two calls, same identity, a warm-to-cold transition within one answer
> Verifies each call's artifact reflects state *at the moment of that call*, including a legitimate cold→warm disagreement between two calls for the same filing

- **Given** one answer issues two `sec_filing_search` calls for the same `ticker="AAPL", fiscal_year=2019` (different query text), where the filing starts cold
- **When** call 1 triggers JIT ingestion and completes (making the store warm), then call 2 runs afterward against the now-populated store
- **Then** it is expected and correct for call 1's artifact to show `edgar_url: null` while call 2's artifact (same underlying filing) shows the real URL — two artifacts legitimately disagreeing about the same filing within one answer is not a bug
- **And** call 2 must not wrongly inherit call 1's stale cold read via any per-answer memoization — each call's artifact must reflect real-time state at that call's moment, not a cached earlier read

Category: Illustrative
Origin: QA (Round 2 extension of Dev's original finding)

---

### Rule: Zero-evidence and identity-resolution failures produce legible messages that honestly reflect whatever was actually resolved

The response always honestly reflects whatever was actually resolved successfully up to the point of failure — neither fabricating fields that were never computed, nor hiding fields that legitimately were.

#### S-tool-16: A nonexistent ticker's message attributes the failure to the ticker, not a secondary symptom
> Verifies root-cause attribution when `fiscal_year` is also omitted

- **Given** `ticker="ZZZZ"` (not in EDGAR) and `fiscal_year` omitted
- **When** `sec_filing_search` is called
- **Then** the message clearly attributes the failure to the ticker not being found — not a fiscal-year-resolution-shaped secondary message that obscures the real root cause
- **And** the response does not carry `fiscal_year`, `fiscal_year_end`, or `fiscal_year_source` — these were never computed, not removed

Category: Illustrative
Origin: PO (Phase 2.5), same principle as S-tool-06's conflation concern applied to a different field pairing

#### S-tool-17: A resolvable identity with zero indexed chunks still reports what was already known
> Verifies the legible "no evidence" message preserves already-resolved identity metadata — contrastive pair with S-tool-16

- **Given** `ticker="AAPL", fiscal_year=2024` resolves cleanly (identity known), but the filing has zero indexed chunks for this query
- **When** `sec_filing_search` returns its legible "no evidence found" message
- **Then** the response still reports `fiscal_year`, `fiscal_year_end`, and `fiscal_year_source` — these were already resolved before hitting zero chunks, and dropping them to match the ticker-not-found response shape would discard information that helps the user ("this is FY2024, dated Sept 2024, we just found nothing on this topic" is more legible than the same sentence without the date)

Category: Illustrative
Origin: QA, resolved by PO's "honestly reflect what was actually resolved" principle
Confirmed via Phase 4.5: `sec_filing_search.py` sets `fiscal_year`/`fiscal_year_end`/`fiscal_year_source` unconditionally before branching on whether any chunks were found — the zero-chunks branch only adds `message`, it never removes the already-resolved identity fields. PO's honesty principle is exactly what the code does; adopted as expected behavior, not an open question.

#### S-tool-18: A cashtag-formatted ticker gets the same message as a genuinely nonexistent one
> Documents a confirmed, current behavior — not a defect requiring a code change for this ticket, but a real precision gap worth an explicit assertion

- **Given** a user writes "$AAPL" and the model passes `ticker="$AAPL"` literally (confirmed via Phase 4.5: no `$`-stripping exists anywhere in the codebase; only `.strip()` and `.upper()` are applied)
- **When** `sec_filing_search` performs its EDGAR-existence check
- **Then** it receives the same "ticker not found" message as a genuinely nonexistent ticker like "ZZZZ" — for one of the most heavily-covered stocks in the market
- **And** given the same request with `ticker="aapl"` (lowercase, no special characters), the case-folding normalization (confirmed present) resolves it correctly, unlike the cashtag case

Category: Illustrative
Origin: QA, confirmed real via Phase 4.5 (no shared or tool-specific cashtag normalization exists)

---

### Rule: A multi-call answer with mixed success/failure outcomes surfaces both coherently — never silently drops the failed half, never aborts the whole turn

#### S-tool-19: One comparison call succeeds, its sibling legitimately fails, in the same answer
> Verifies the orchestration layer, not answer-writing quality — the design envelope's "never silent partial answers" API-contract principle, in its most natural real-world trigger

- **Given** a user asks to compare AAPL and ZZZZ's supply-chain risk disclosures (ZZZZ not in EDGAR)
- **When** the model issues one `sec_filing_search` call for AAPL (succeeds, returns evidence) and one for ZZZZ (legitimately fails per S-tool-16)
- **Then** both ToolMessages — one success-shaped, one legible-error-shaped — reach the model; the SSE stream does not abort early and does not surface a raw, unhandled exception because one of the two calls failed

Category: Illustrative
Origin: Dev (Phase 2.5 assumption check — the first scenario to combine two already-included rules, A1's multi-call pattern and A9's legible-failure pattern, instead of testing them in isolation), scoped by PO to the observable/non-semantic layer (answer *text* quality is out of scope — LLM-quality)

---

### Journey Scenarios

#### J-tool-01: A pinpoint question with no fiscal year specified resolves end-to-end
> Proves the full retrieval → shaping → artifact-delivery pipeline works together

- **Given** a user in the `reader` profile asks a pinpoint question about AAPL's most recent 10-K, without specifying a fiscal year
- **When** `sec_filing_search` resolves the ticker and latest fiscal year, retrieves and groups evidence from the relevant Item, and assembles its response
- **Then** the model receives correctly-grouped, correctly-shaped evidence chunks with fiscal-year identity and no URLs, while the EDGAR URL is delivered out-of-band via the artifact channel to the frontend — the full pipeline produces one coherent, correctly-shaped result

Category: Journey
Origin: Multiple

---

## Feature: SEC citation system-prompt contract (`reader` Workflow Profile only)

### Context
Config-level behavior governing how the model must cite `sec_filing_search` evidence and route between tools. **This Feature was heavily thinned by the Three Amigos discovery process** — see the disposition table below. Almost every rule in the original spec collapsed into either LLM decision-quality (measured by DEV-126's eval, not here) or existing static-content unit tests, once tested against "does this have a runtime trigger, state flow, and observable system outcome" rather than "does the model's output look right." **This is a deliberate scoping outcome reached through three rounds of adversarial review, not a shortfall or incomplete coverage** — recorded explicitly here so a reviewer at the `briefing.md` gate can distinguish "deliberately thin" from "ran out of time."

### Rule: `sec_filing_search` and its citation contract are registered only in the `reader` profile, never `baseline`

This is the **only** rule in this Feature with an independent, reachable BDD surface — because it's the only one with a genuine runtime hook (tool-registry membership), rather than being either static prompt-content or model-output-quality.

#### S-prompt-01: `baseline` has no access to `sec_filing_search`, even for a dead-on SEC question
> Verifies the negative space — not "the model chose not to use it," but "the capability doesn't exist for this turn." Load-bearing for DEV-126's eval control-group integrity.

- **Given** a conversation in the `baseline` Workflow Profile
- **When** the user asks a pinpoint SEC filing question (e.g., "what does AAPL's 10-K say about supply chain concentration risk")
- **Then** this turn's available-tools set contains no `sec_filing_search` at all — checkable directly from `baseline`'s tool registry, independent of what the model does with whatever tools it does have
- **And**, contrastively, the same question in the `reader` profile has `sec_filing_search` available

Category: Illustrative
Origin: Dev
Confirmed via Phase 4.5: `reader/orchestrator_config.yaml` registers `sec_filing_search`; `baseline/orchestrator_config.yaml` does not.

### Explicitly out of scope for BDD/behavior testing in this Feature

| Rule (from spec) | Disposition | Why |
|---|---|---|
| Citation style differs by source type (Finnhub/Tavily/SEC-search/SEC-section) | Demote to unit test | Collapses to either grading model output (LLM-quality) or static prompt-text content — no runtime trigger. Recommend a parametrized content-pinning unit test if not already covered by existing contract-string tests. |
| claim↔source many-to-many (`[1][2]`, reused numbers) | Demote to unit test | Same collapse as above, applied via the identical test to a sibling rule. Lower priority than the source-type rule — thinner value (presence of one example sentence). |
| `[N]` numbering assigned by the model, first-use order, across tool calls | Reject | No runtime trigger on either half: the "no tool-side ordinal" fact is already covered by S-tool-09 (Feature A), and "did the model number correctly" is LLM-quality. |
| SEC reference list uses stable ID, never URL | Reject | The "model can't copy a URL" half is already structurally guaranteed by S-tool-11/12 (Feature A). The remaining risk — the model hallucinating a URL from training knowledge rather than copying one — has no structural guardrail and is pure LLM-quality. |
| Evidence gap annotation placed adjacent to the claim | Reject | No tool-contract or system mechanism behind this at all — purely model-generated text positioning. Spec's own out-of-scope list already names this LLM decision-quality. |
| Routing guidance (pinpoint → search, synoptic → get_section) | Reject | Spec excludes this by name twice independently. The only nearby system-level fact (both tools registered in `reader`) is S-prompt-01's territory. |
| System-prompt example IDs must be obviously fake | Demote to unit test | Pure static file-content check, no runtime trigger. Directly traces to a real, already-fixed bug (a realistic-looking fake ID was copied into a real answer) — cheap and worth writing as a regression unit test even though it's not BDD. |
| Model may only cite IDs actually in this conversation's tool results | Reject, but **escalated as a mandatory cross-ticket handoff** | No structural guardrail exists (unlike the URL rule, which S-tool-11/12 structurally prevents) — this is the exact motivating bug for the entire ticket (a fake-but-realistic accession number copied into a real answer), resting entirely on prompt compliance. **DEV-126's eval-design must treat this as a gated metric** — see verification-plan.md's handoff note. Additionally, this metric cannot be correctly graded until the cross-turn citation numbering scope question (below) is resolved, since it determines what even counts as an out-of-scope citation. |

---

## Feature: Honest degradation while DEV-143 (frontend) is unmerged

### Context
DEV-142 (backend, this ticket) can merge before DEV-143 (frontend citation parsing + Sources UI). The acceptance criteria require this intermediate state to degrade honestly — no fabricated or broken-looking sources, no crashes. Phase 4.5 code verification confirmed both of this Feature's two candidate failure modes are actually **safe** in the current frontend; the third (the dangling marker) is a real but low-severity, deliberately-accepted cosmetic gap.

### Rule: Mixed-scheme reference lists extract correctly, line by line

#### S-degrade-01: A Tavily citation and a SEC citation in the same trailing reference block
> Verifies the existing markdown-sources extraction handles mixed schemes without cross-contamination — confirmed safe via Phase 4.5 (code reading + empirical pipeline run)

- **Given** an answer cites a Tavily source as `[1]` and a `sec_filing_search` chunk as `[2]`, with both reference-definition lines adjacent in the same trailing block
- **When** a pre-DEV-143 frontend renders this answer
- **Then** the Sources panel contains exactly one entry — the `[1]` http(s) source; the `[2]` `sec://` line silently disappears from the Sources panel (no broken entry, no partial URL leaking through)
- **And** `[1]` is not dropped just because the block contains one scheme it doesn't recognize — confirmed: each reference-definition line parses as an independent AST node, extraction is line-granular

Category: Illustrative
Origin: Dev, confirmed safe via Phase 4.5

### Rule: An unresolved inline `[N]` marker survives as inert plain text — a documented, accepted, temporary degradation

#### S-degrade-02: A dangling citation marker with no corresponding Sources entry
> Documents expected behavior — not a defect. Ratified by QA (Round 2) and PO (Round 3) after evaluating and rejecting every in-scope fix as disproportionate to a low-severity, bounded-duration, reversible gap.

- **Given** an answer's body text contains "...concentration risk`[2]`..." where `[2]`'s reference line was stripped per S-degrade-01
- **When** a pre-DEV-143 frontend renders this answer
- **Then** `[2]` appears as literal, unparsed plain text in the body — with no corresponding entry anywhere explaining it
- **This is expected, accepted behavior, not a defect** — do not report it as a bug during manual verification or UAT. Rationale (for the record, since it's a judgment call a reviewer should be able to see, not rediscover): low isolated severity (cosmetic — no fabricated URL, no false content), a bounded exposure window (DEV-143 is an active near-term companion ticket), and every candidate fix is disproportionate — a frontend fix contradicts this ticket's "extraction stays unchanged" premise, a prompt-side mitigation is fragile (depends on the model reliably following a formatting constraint — the exact weakness this citation system already accepts elsewhere), and avoiding the mixed-citation state entirely would contradict the explicit "DEV-142 can merge before DEV-143" decision. Additionally confirmed structural: the frontend streams top-to-bottom and cannot know at render time whether a marker will resolve, since the reference block arrives last — any "smarter" handling would require buffering the whole answer or a post-stream re-render, real architecture cost for a low-severity, reversible issue.

Category: Illustrative
Origin: QA, reasoning independently confirmed and grounded by PO in the design envelope's §1 scale assumptions and this being a reversible decision

### Rule: An unrecognized `data-tool-artifact` stream part is safely ignored by a pre-DEV-143 frontend

#### S-degrade-03: The new artifact stream-part type doesn't break rendering on an older frontend build
> This was the team's top-flagged risk across three full rounds — confirmed **safe** via Phase 4.5 (three-layer code trace + empirical verification), not adopted on faith

- **Given** a browser running a pre-DEV-143 frontend build (compiled with zero knowledge that `data-tool-artifact` exists)
- **When** the agent calls `sec_filing_search` and the backend emits a `data-tool-artifact` SSE part for that `toolCallId`, followed by the actual answer's `text` parts
- **Then** the unrecognized part is silently ignored at every layer (wire-schema parsing via the AI SDK's deliberate `data-*` wildcard, stream-state processing, and app-level rendering — none use an exhaustive-switch-with-throw pattern), and the subsequent answer text renders normally and completely

Category: Illustrative
Origin: PO's Phase 1 top-priority question, sharpened by Dev (compile-time-vs-runtime exhaustiveness risk) and QA (blast-radius amplification under the multi-call norm) across two rounds — resolved via Phase 4.5 code verification, not team consensus alone

---

### Journey Scenarios

#### J-degrade-01: A mixed-citation answer renders coherently on a pre-DEV-143 frontend
> Proves the full intermediate-state experience is safe and honest end-to-end, not just each mechanism in isolation

- **Given** a pre-DEV-143 frontend is deployed and DEV-142 has merged
- **When** a user asks a compound question naturally hitting both Tavily and `sec_filing_search` (e.g., "what does AAPL's 10-K say about supply chain risk, and is there recent news on it?") in the `reader` profile
- **Then** the user sees a complete, readable answer: Tavily's citation resolves normally in the Sources panel, the SEC citation's reference line and its `data-tool-artifact` part are both silently and safely absorbed, and the SEC citation's inline `[N]` marker survives as inert plain text — a coherent experience with one known, accepted, cosmetic gap, and no crashes, no fabricated sources, no broken rendering

Category: Journey
Origin: Multiple
