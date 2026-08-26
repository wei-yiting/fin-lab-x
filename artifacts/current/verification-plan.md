# Verification Plan

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Generated: 2026-08-20
- Existing test seams referenced: `backend/tests/tools/test_sec_filing_search.py` (tool function, retriever mocked), `frontend/src/lib/__tests__/markdown-sources.test.ts` (citation extraction)

---

## Implementation-Decided Points

### Adopted Decisions

Resolved via Phase 4.5 scoped code reading (not asserted from the spec alone). All four are **Reasonable decisions** — the spec was silent, the implementation's choice is sound, adopted as expected behavior.

| Decision point | Implementation chose | Why reasonable | Scenarios |
|---|---|---|---|
| Does a pre-DEV-143 frontend safely ignore an unrecognized `data-tool-artifact` SSE part? | Yes, safely, at all three layers. The AI SDK's wire schema has a deliberate wildcard for any `type` starting with `"data-"` (`ai@6.0.142/dist/index.mjs:5184-5192`); the backend's part is not marked `transient` so it flows into `state.message.parts` without validation (no `dataPartSchemas` configured); app-level rendering (`AssistantMessage.tsx:127-152`) uses a plain if/else, not an exhaustive switch with `assertNever` — no error boundary exists anywhere in `frontend/src`, but nothing throws, so none is needed for this case. | S-degrade-03 |
| Does the existing citation extraction operate at line or block granularity? | Line (per-`definition`-AST-node) granularity. `frontend/src/lib/markdown-sources.ts:137-141` iterates `remark-parse`'s AST nodes independently; a rejected scheme (`markdown-sources.ts:36`) only skips that one node, the loop continues unconditionally. Empirically verified: a `sec://` line between two `https://` lines in one block does not affect either. | S-degrade-01 |
| Is `fiscal_year_end` guaranteed present whenever a tool call succeeds? | Yes, unconditionally — `sec_filing_search.py:293-294` sets it before branching on whether any chunks were found (see also the next row). `locate_filing_ref` (`sec_core.py:415-431`) validates the date via `date.fromisoformat` before a `FilingRef` can be constructed at all; malformed dates raise rather than producing a null field. | (Closes an open question from S-tool-09/10's discovery; no dedicated scenario needed — the guarantee holds by construction.) |
| Does a "zero indexed chunks" response preserve already-resolved identity metadata, or drop it to match the ticker-not-found shape? | Preserves it. `sec_filing_search.py:289-297` builds `fiscal_year`/`fiscal_year_end`/`fiscal_year_source`/`total_chunks` unconditionally, *before* branching on `if chunks:` — the zero-chunks branch (`:305-312`) only adds `message`, never removes the already-set identity fields. Confirms PO's "honestly reflect whatever was actually resolved" principle is exactly what the code does. | S-tool-17 |
| Does citation numbering (and the reference-definition list) reset at the start of each conversation turn, or accumulate/reuse across the whole conversation? | **User decision (2026-08-20): resets per turn.** One agent response is its own numbering universe; a new chat turn starts back at `[1]`, even when re-citing a passage a prior turn already cited under a different number. Matches Dev's technical lean, but decided by the user because of its DEV-143 Sources-UI implications, not adopted from engineering reasoning alone. | (see Action item below) |

### Action item — this decision is not yet reflected in the implementation

`reader/system_prompt.md:27-28` is currently silent on turn boundaries (confirmed via Phase 4.5) — it only says numbering is continuous "across the whole answer... across all tools and all tool calls," which doesn't by itself imply per-turn reset. **The prompt text should be updated to state the per-turn-reset rule explicitly** (e.g., "each new user turn starts its citation numbering fresh at `[1]`, independent of any earlier turn's numbers"), otherwise the model's actual behavior on a follow-up question remains unspecified from its own instructions and the decision above is not actually enforced. This is implementation work belonging to whoever picks up DEV-142's remaining polish or DEV-143 — flagging here so it isn't lost. Once updated, this becomes a one-line addition to the same parametrized prompt-content-pinning unit test recommended for B1/B8 in `bdd-scenarios.md`'s Feature B disposition table (assert the prompt states "each turn resets"), not a new BDD scenario — same reasoning as the rest of Feature B: "did the prompt say this" is a unit-test-shaped check, not a behavior trigger.

This also unblocks the B9/DEV-126 handoff note below — a citation-groundedness grader can now be built knowing a citation reusing an earlier turn's `[N]` number is out-of-scope by design (not just an unresolved ambiguity).

### Cross-ticket handoff — not verified in this plan, must not be silently dropped

- **DEV-126's eval-design must gate "model only cites IDs that actually appeared in a tool result of this conversation" as a measured, gated metric.** This rule (B9 in `bdd-scenarios.md`'s Feature B disposition table) has no structural backstop anywhere in the system — unlike the URL-writing rule, which `sec_filing_search`'s content/artifact separation structurally prevents, nothing prevents the model from typing a plausible-looking `sec://...` string it never actually saw. This is the exact motivating bug for the entire DEV-142/DEV-130 effort (a live-tested incident where the model copied a realistic-looking fake accession number from a prompt example into a real answer). **Action for whoever picks up this plan**: before closing out DEV-142, check DEV-126's eval-design (`artifacts/current/eval-design.md` if it exists, or the DEV-126 Linear issue) and confirm citation-ID groundedness is a gated scorer, not just implied by "citation accuracy" — if it's missing, flag it there, not here.

---

## Automated Verification

### Deterministic

All Feature A scenarios follow the existing tool-test seam: `backend/tests/tools/test_sec_filing_search.py`, retriever (`search`) and `locate_filing_ref` mocked via `unittest.mock.patch`, following the file's existing `_patches()` / `_make_chunk()` / `_filing_ref()` / `_tool_call()` helper pattern (see file for exact signatures — do not duplicate these helpers, extend them if a new parameter is needed).

#### S-tool-01: Model passes `ticker` as a list instead of a string
- **Method**: script (pytest)
- **Steps**:
  1. Call `sec_filing_search.ainvoke({"args": {"query": "...", "ticker": ["AAPL", "TSLA"]}, "name": "sec_filing_search", "type": "tool_call", "id": "test-call-id"})` directly (bypassing `_tool_call`'s JSON-decode helper, since this call is expected to fail before returning a normal `ToolMessage`).
  2. Assert this raises (or returns a `ToolMessage` with an error indicator, depending on how LangChain's `@tool` decorator surfaces a Pydantic `ValidationError` for a bad-typed arg — `[POST-CODING: confirm whether LangChain's tool-calling wrapper turns a schema ValidationError into a raised exception the test can `pytest.raises` on, or into an error-shaped ToolMessage, by running this exact call once and observing]`).
  3. Assert the error message is legible (mentions `ticker` and that a single value is expected) — not a raw Python traceback string.
- **Expected**: legible, structured validation failure; no unhandled exception type that would differ from Pydantic's normal `ValidationError` handling elsewhere in the codebase.

#### S-tool-02: `fiscal_year=24` (two-digit shorthand)
- **Method**: script (pytest)
- **Steps**:
  1. Call with `{"query": "...", "ticker": "AAPL", "fiscal_year": 24}`.
  2. `[POST-CODING: check whether `SecFilingSearchInput`'s `fiscal_year` field declares a range constraint (e.g. `Field(ge=1994)`) — if yes, assert a `ValidationError`/schema-level rejection; if no, assert the call proceeds to `locate_filing_ref` and produces the same message shape as S-tool-06's "structurally impossible" row, and separately assert that message differs recognizably from a schema-rejection message]`.
- **Expected**: a message distinguishable from "genuinely checked FY24 against AAPL's real filing history and found nothing" — whichever layer handles it.

#### S-tool-03 / S-tool-04: fiscal_year_source reporting
- **Method**: script (pytest)
- **Steps**:
  1. Using `_patches(chunks, resolved_fy=2024)` with `_tool_call({"query": "...", "ticker": "AAPL"})` (fiscal_year omitted) — assert `result["fiscal_year"] == 2024` and `result["fiscal_year_source"] == "latest"` (the exact string constant confirmed at `sec_filing_search.py:263`).
  2. Using the same patches with `_tool_call({"query": "...", "ticker": "AAPL", "fiscal_year": 2024})` (explicit, matching what auto-resolve would pick) — assert `result["fiscal_year_source"] == "requested"` (not `"latest"`), proving the condition checked is argument-presence, not value-equality.
- **Expected**: `"latest"` vs `"requested"` distinguish correctly in both directions, including the coincidence case.

#### S-tool-05: Ticker with no 10-K history ever
- **Method**: script (pytest)
- **Steps**:
  1. Patch `locate_filing_ref` to raise the appropriate `FinLabError` subtype for "no 10-K found" — `[POST-CODING: confirm exact exception raised by `_locate_filing_cached` when `company.get_filings(form="10-K")` returns empty, in `backend/common/sec_core.py` around line 395-522; likely a sibling of `TickerNotFoundError` — check `backend/common/errors.py`]`.
  2. Call with `{"query": "...", "ticker": "XYZ"}` (fiscal_year omitted).
  3. Assert the resulting error is legible and distinguishable from `TickerNotFoundError`'s message (this ticker DOES exist, it just has no 10-K) — not an unhandled exception from an empty-sequence operation.
- **Expected**: legible, root-cause-accurate failure.

#### S-tool-06: Three non-existence reasons (table-driven)
- **Method**: script (pytest, parametrized)
- **Steps**: for each row (pre-IPO year / not-yet-due year / real year with transient failure), patch `locate_filing_ref` to reproduce that condition and assert the resulting message's content differs across rows in a way a human could tell apart — `[POST-CODING: once `locate_filing_ref`'s actual exception taxonomy for these three cases is confirmed (grep `backend/common/errors.py` for SEC-related error classes and `_classify_edgar_error` in `sec_core.py`), assert on the specific exception type/message per row rather than a generic string match]`.
- **Expected**: three distinguishable outcomes; specifically assert the "temporarily unavailable" row's message does NOT contain phrasing implying the filing doesn't exist (e.g., does not match `/no .* 10-K/i` if that phrasing is reserved for the other two rows).

#### S-tool-07: Grouping and document-order within group
- **Method**: script (pytest) — **this scenario already has a passing test**: `test_groups_by_item_and_orders_chunks_by_document_order` at `backend/tests/tools/test_sec_filing_search.py:141-166`. No new test needed; cite as existing coverage.

#### S-tool-08: Prelude once per group per call (including the legitimate per-call reprint)
- **Method**: script (pytest)
- **Steps**:
  1. `[POST-CODING: find where "prelude" text is generated — likely inside `_build_groups` (`sec_filing_search.py:185-228`) or a helper it calls; confirm the exact field name in the output (e.g. `group["prelude"]`)]`. Assert one call hitting 2 items produces exactly one prelude string per group.
  2. Make two separate `_tool_call()` invocations in the test (simulating two calls in one answer) both hitting the same item; assert each call's own result independently contains that item's prelude — this is a positive assertion (prelude present in both), not a dedup assertion, since dedup across calls is explicitly out of scope.
- **Expected**: prelude present once per group, per call; explicitly do NOT assert "absent on the second call."

#### S-tool-09 / S-tool-10: Chunk field shape, FlatItem degradation
- **Method**: script (pytest)
- **Steps**:
  1. Using `_make_chunk(...)`, assert the resulting `EvidenceChunk` in `result["groups"][0]["chunks"][0]` has `source`, `title`, `content`, `score` keys, and does NOT have any ordinal/number/index-position key (grep the actual `EvidenceChunk` TypedDict definition near `sec_filing_search.py:63` for the authoritative field list, assert against exactly that set).
  2. Construct a chunk fixture representing a FlatItem (`[POST-CODING: confirm how FlatItem-ness is signaled in the `Chunk` input — likely `header_path` has no sub-heading segment beyond the Item level; check `_build_groups`'s title-composition logic for the exact condition]`) and assert `title` degrades to Item-level text and the call succeeds (no exception, no missing-field error).
- **Expected**: exact field-set match; FlatItem case produces a normal successful result.

#### S-tool-11 / S-tool-12: EDGAR URL via artifact only, warm and cold
- **Method**: script (pytest) — **these scenarios already have passing coverage** via `_patches(chunks, source_url=...)` (warm, default) and presumably a `source_url=None` variant (cold) — `[POST-CODING: confirm the cold case is already parametrized in the existing file; if not, add `source_url=None` as a case]`. For both, assert (a) `json.dumps(result)` (the model-visible `content`) contains no substring matching a URL pattern, and (b) the second element of the `(content, artifact)` tuple returned by `sec_filing_search.func(...)` (not `.ainvoke`, to access the raw pair) has `artifact["edgar_url"]` equal to the expected value.
- **Expected**: content never contains a URL; artifact carries the real URL (warm) or `None` (cold).

#### S-tool-13: [CONFIRMED DEFECT] Artifact-side metadata error must not discard content
- **Method**: script (pytest) — **extends existing parametrized test, currently missing this exact case**
- **Steps**:
  1. The existing test at `backend/tests/tools/test_sec_filing_search.py:337-349` already parametrizes `_make_failing_filing_store` over `[OSError("disk read failed"), ValueError("corrupt metadata")]` — both of which `_edgar_filing_url`'s except clause (`sec_filing_search.py:163-182`) already catches.
  2. Add two more cases to that same parametrize list: a `yaml.YAMLError` (or a concrete subclass like `yaml.scanner.ScannerError`) and a plain `TypeError` (simulating `FilingMetadata(**meta_dict)` receiving a non-mapping) — both are realistic outputs of `LocalFilingStore.get()` hitting malformed on-disk frontmatter, per `backend/ingestion/sec_filing_pipeline_html/filing_store.py:123-136`.
  3. Run the test as currently written (asserting the call still succeeds with `edgar_url: None`) against these two new cases.
- **Expected — and this is the point of the scenario**: the test currently **fails** for these two new cases, because `sec_filing_search.py:163-182`'s except clause only catches `(OSError, ValueError)`. This is not a test-writing mistake; it demonstrates the confirmed defect. **Recommended fix** (for whoever implements against this plan): widen the except clause to catch bare `Exception` (matching the "always degrade to null, never propagate" intent already stated in the surrounding code's comments), or explicitly add `yaml.YAMLError` and `TypeError` to the tuple.

#### S-tool-14 / S-tool-15: Multi-call artifact attribution and warm-to-cold transition
- **Method**: script (pytest)
- **Steps**:
  1. Two separate `sec_filing_search.func(...)` calls in one test (simulating the same answer), with different `_patches(..., source_url=...)` configurations per call (one real URL, one `None`). Assert each call's returned artifact matches its own patch configuration — trivially true for two independent function calls with independent mocks, but write the test to make the *intent* explicit (a comment referencing `toolCallId`-keyed attribution being the API layer's job to preserve, not this tool's) since the tool itself doesn't do cross-call bookkeeping.
  2. For the warm-to-cold transition (S-tool-15), this specific temporal transition is **not independently testable at the tool-function level** — the tool is stateless per call by design (confirmed throughout Phase 1-3 discovery), so "call 1 makes it warm, call 2 sees warm" is a property of the underlying `LocalFilingStore`/ingestion pipeline, not `sec_filing_search`'s own logic. `[POST-CODING: if this transition needs verification, it belongs to the JIT ingestion pipeline's own test suite (`backend/ingestion/`), not here — confirm whether such a test already exists there; if not, this is worth flagging back to whoever owns that pipeline rather than adding scope to this tool's tests]`.
- **Expected**: S-tool-14 passes as a straightforward two-call assertion; S-tool-15 is noted as verified-by-design (statelessness) rather than needing a new test.

#### S-tool-16 / S-tool-17 / S-tool-18: Identity-resolution failures and honest metadata preservation
- **Method**: script (pytest)
- **Steps**:
  1. S-tool-16: patch `locate_filing_ref` to raise `TickerNotFoundError` (confirmed import at `test_sec_filing_search.py:17`); call with `ticker="ZZZZ"`, `fiscal_year` omitted; assert the raised/returned error is ticker-attributed, not fiscal-year-shaped.
  2. S-tool-17: using `_patches(chunks=[], resolved_fy=2024)` (empty chunks list, valid ticker/year), call `_tool_call({"query": "...", "ticker": "AAPL", "fiscal_year": 2024})`; assert `result["fiscal_year"] == 2024`, `result["fiscal_year_end"]` is present, `result["fiscal_year_source"] == "requested"`, `result["groups"] == []`, and `result["message"]` matches the format at `sec_filing_search.py:307-312`.
  3. S-tool-18: patch `locate_filing_ref` to raise `TickerNotFoundError` for `ticker="$AAPL"` (confirming the current, un-normalized behavior); assert the message is identical in shape to the `ticker="ZZZZ"` case from step 1 — this assertion documents current behavior, it is expected to **pass**, not fail (unlike S-tool-13). Separately, assert `ticker="aapl"` (lowercase) resolves successfully (case-fold normalization confirmed present at `sec_filing_search.py:254`).
- **Expected**: S-tool-16 and S-tool-18 pass, documenting current (accurate for -16, imprecise-but-legible for -18) behavior. S-tool-17 passes, confirming the Adopted Decision above.

#### S-tool-19: Mixed-outcome multi-call
- **Method**: script (pytest)
- **Steps**:
  1. Two `sec_filing_search.func(...)` calls in one test — call 1 with a valid, mocked-successful `ticker="AAPL"`; call 2 with `locate_filing_ref` patched to raise `TickerNotFoundError` for `ticker="ZZZZ"`.
  2. Assert call 1 returns normally (a `(content, artifact)` pair) and call 2 raises/returns its legible error independently — i.e., that nothing in the tool's own implementation couples the two calls (there's no shared mutable state between invocations to check, but this test documents and pins the expectation for whoever wires orchestration-level handling of multiple tool calls in one turn).
  3. `[POST-CODING: the orchestration-level assertion (does the LangGraph tool-calling loop actually surface BOTH ToolMessages to the model without early-aborting the turn when one raises) requires either a higher-level integration test around the Orchestrator/tool-node, or a live smoke run — check whether an existing integration test harness exists for multi-tool-call turns before adding a new one; this is the one Feature A scenario most likely to need integration-level (not pure unit) testing]`.
- **Expected**: both calls resolve independently; orchestration-level behavior confirmed via the POST-CODING step above.

#### J-tool-01: Full retrieval pipeline, fiscal_year omitted
- **Method**: script (pytest) — this is the one scenario that should NOT reuse the individually-mocked-per-behavior pattern above; it exists specifically to prove the pieces compose, so mock only at the `search()`/`locate_filing_ref`/`LocalFilingStore` boundary (same as every other test in this file) and assert on the *combination* of properties, not any single one in isolation.
- **Steps**:
  1. Using `_patches(chunks, resolved_fy=2024, source_url=<a real-looking URL>)` with `chunks` containing multiple chunks across two different Items (reusing the fixture shape from `test_groups_by_item_and_orders_chunks_by_document_order`), call `sec_filing_search.func({"query": "supply chain risk", "ticker": "AAPL"})` — `fiscal_year` omitted — via the raw function (not `.ainvoke`) to get the `(content, artifact)` pair directly.
  2. Assert, together in one test: `content["fiscal_year"] == 2024` and `content["fiscal_year_source"] == "latest"` (resolution happened), `content["groups"]` has 2 entries correctly grouped and ordered (shaping happened), no URL substring appears anywhere in `json.dumps(content)` (content/artifact separation happened), and `artifact["edgar_url"]` equals the configured URL (artifact delivery happened).
- **Expected**: all four properties hold simultaneously from one realistic call — the point is proving composition, not re-testing any single property already covered above.

#### S-prompt-01: `baseline` excludes `sec_filing_search`, `reader` includes it
- **Method**: script (config read, no mocking needed) — **already confirmed via Phase 4.5**, write as a simple regression-pinning test if one doesn't already exist
- **Steps**:
  1. Load `backend/agent_engine/agents/profiles/reader/orchestrator_config.yaml` and `backend/agent_engine/agents/profiles/baseline/orchestrator_config.yaml` (via `config_loader.py`'s normal loading path, not a raw YAML read, so the test exercises the same path production uses).
  2. Assert `"sec_filing_search"` is in `reader`'s `tools` list and not in `baseline`'s.
- **Expected**: as confirmed in Phase 4.5 — `[POST-CODING: check `backend/tests/agent_engine/` for an existing `EXPECTED_TOOLS_BY_PROFILE`-style test (mentioned in the DEV-142 Linear history) this can extend, rather than writing a standalone new test]`.

---

### Browser Automation

Feature C scenarios only — these behaviors exist solely in frontend rendering and cannot be observed via curl. Use the `webapp-testing` skill (Playwright).

#### S-degrade-01: Mixed Tavily + SEC reference lines extract correctly
- **Method**: Unit test (Vitest) — this is fully deterministic and doesn't need a live browser; add to the existing suite
- **Steps**:
  1. Add a new test to the `"extractSources — security: scheme allowlist"` describe block in `frontend/src/lib/__tests__/markdown-sources.test.ts` (pattern-match the existing `"allows http and https schemes"` test at lines 86-96), using markdown with three adjacent lines: `[1]: https://example.com/a "Source A"`, `[2]: sec://0000320193-24-000123/Item1A#7 "SEC chunk"`, `[3]: https://example.com/c "Source C"`.
  2. Call `extractSources(md)`.
  3. Assert the result has exactly 2 entries (labels `1` and `3`), with `2` absent — not an empty result, not a thrown error, not a 1-entry or 0-entry result.
- **Expected**: matches the Phase 4.5 empirical verification exactly (already run once by the investigating agent; this codifies it as a permanent regression test, since the existing suite had this exact gap — mixed valid/invalid lines in one block — noted explicitly by the Phase 4.5 investigation).

#### S-degrade-02: Dangling inline `[N]` marker (documented expected behavior)
- **Method**: Browser automation (Playwright script)
- **Steps**:
  ```python
  page.goto("http://localhost:5173/chat")  # [POST-CODING: confirm dev server port/route]
  page.wait_for_load_state("networkidle")
  # Requires a reader-profile conversation whose answer mixes a Tavily and a SEC citation.
  # [POST-CODING: determine the most reliable way to trigger this deterministically —
  #  either a live question known to trigger both tools, or a test-only seam that
  #  injects a fixed assistant message with both citation types already in its parts.
  #  A live LLM-driven trigger is unreliable for this specific test; prefer a fixture.]
  page.wait_for_selector("[data-status='ready']")
  # Assert the rendered message text contains a literal, unparsed "[2]" (or whichever
  # number was assigned to the SEC citation) as plain text.
  # Assert the Sources panel/list does NOT contain an entry for it.
  page.screenshot(path="/tmp/s-degrade-02.png")
  ```
- **Expected**: `[N]` visible as inert plain text, no corresponding Sources entry, no visible error state, no crash. **If this scenario is ever reported as a "bug" during manual/UAT verification, the correct response is to point to this note — it is documented, accepted, expected behavior**, not something to fix under this ticket.

#### S-degrade-03: `data-tool-artifact` doesn't break rendering on an older frontend build
- **Method**: Browser automation (Playwright script) — lower priority than S-degrade-02/J-degrade-01 given Phase 4.5 already confirmed this safe via code reading + empirical trace; this is a live-environment sanity check, not the primary evidence
- **Steps**:
  ```python
  page.goto("http://localhost:5173/chat")
  page.wait_for_load_state("networkidle")
  page.get_by_role("textbox").fill("What does AAPL's 10-K say about supply chain risk?")
  page.get_by_role("button", name="Send").click()
  page.wait_for_selector("[data-status='streaming']")
  page.wait_for_selector("[data-status='ready']")
  # Assert: no console errors were logged during this turn (use the browser tool's
  # console-message reading, not just visual inspection).
  # Assert: the final answer text is complete (non-empty, ends coherently — not
  # truncated mid-sentence, which would indicate the stream died partway).
  ```
- **Expected**: clean completion, no console errors, full answer text present.

#### J-degrade-01: Full mixed-citation journey on a pre-DEV-143 frontend
- **Method**: Browser automation (Playwright script)
- **Steps**: combine S-degrade-01 through S-degrade-03's live-environment checks into one flow — send a compound question naturally triggering both Tavily and `sec_filing_search`, screenshot the completed answer and Sources panel, assert no console errors, assert the Sources panel has exactly the Tavily entries (not the SEC ones), assert the answer body is complete.
- **Expected**: coherent full experience, matching the individual scenarios' expectations combined.

---

## Manual Verification

### User Acceptance Test

#### J-tool-01 + J-degrade-01: Does the intermediate (pre-DEV-143) state feel acceptable to ship?
- **Acceptance Question**: Reviewing a live `reader`-profile conversation that mixes SEC and web citations — does the dangling `[N]` marker (S-degrade-02) feel like an acceptable, temporary rough edge, or does it undermine trust in the tool enough to warrant delaying this merge until DEV-143 ships?
- **Steps**:
  1. Run a few pinpoint SEC questions against `reader` profile, including at least one that naturally also triggers a Tavily search.
  2. Observe the dangling-marker behavior directly, not just read about it.
  3. Decide: ship as-is (per the team's Round 3 recommendation), or hold for DEV-143.
- **Expected**: this is a judgment call the design envelope's §1 scale assumptions (≤3 users, reversible decision) support shipping through, per PO's Round 3 reasoning — but the acceptance test exists because a human should see it once before it goes live, not just take the team's word for it.

#### The one open product question
- **Acceptance Question**: does citation numbering reset per conversation turn, or accumulate across the whole conversation? (See "Unresolved — needs the user's decision" above.) This has no automated test because it's not yet decided — resolve it here or separately before DEV-143's Sources UI design locks in an answer implicitly.
