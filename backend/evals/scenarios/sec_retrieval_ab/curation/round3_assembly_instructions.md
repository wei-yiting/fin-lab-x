# Round 3 — dataset assembly instructions

Instructions for the agents assembling the final `sec_retrieval_ab` dataset from the
round-2 traversal results (`round2_ticker_results/*.json`, `ticker_tasks/*.md`).
All decisions below were ratified by the human reviewer on 2026-08-27 and are not
open for reinterpretation. When a task conflicts with an older document (round-1
review notes, the original DEV-162 spec text, prompt v3 wording), **this file wins**.

## A. Ratified decisions (context — do not revisit)

1. **Contract stays at the original limits**: `answer_snippet` 50–200 chars,
   `answer_span` ≤ 300 cl100k tokens, both case-insensitive exact substrings of the
   `sec_text_pipeline` filing store text (ADR-0016: the filing store is the only
   validation target — never Qdrant, never the canonical HTML text used for
   round-2 traversal).
2. **`multi_passage` is removed entirely.** No row in the final dataset carries it.
   Remaining query types: `factoid`, `passage`.
3. **OR-set semantics**: for every row, `expected_header_paths` /
   `answer_snippets` / `answer_spans` are index-aligned lists of **alternatives** —
   retrieval hitting ANY listed location counts as a hit. (The scorer change
   implementing this ships as its own PR; the dataset is assembled in this shape now.)
4. **Item 8 is excluded from retrieval scope** on both arms:
   - HTML arm (frozen): query-time Qdrant payload filter `must_not item = "Item 8"`
     applied at the eval-task layer (DEV-138). No re-ingestion.
   - Text arm: DEV-137 will not ingest Item 8.
   - Dataset: no expected location may carry an Item 8 header_path (see task T2).
5. **n10 (JPM)** keeps its human-approved question
   (`Which types of market risk does JPMorganChase include in its Value-at-Risk measure?`).
   Its evidence must be rebuilt from filing-store text (task T3).
6. Snippet corpus-uniqueness rule becomes **enumerated exemption**: a snippet may
   occur more than once across the parsed corpus only if every occurrence's location
   is listed in the row's OR-set (or excluded by decision 4). Unlisted extra
   occurrences remain a validation failure.
7. **a16 (LIN)** uses the corrected single-intent question
   (`How did currency translation affect Linde's APAC sales in 2025?`). Its two
   acceptable source occurrences are the APAC sales bridge table and the APAC sales
   narrative; rebuild both from filing-store text and retain them as OR alternatives.

## B. Assembly tasks

### T1 — Re-anchor whitespace-mismatched occurrences to filing-store text

**Completed 2026-08-27.** The reconciled occurrences and exceptions are recorded
in `round3_t1_t2_reconciliation.md`; the affected ticker JSON files now carry the
store-exact strings and `store_anchor` offsets.

Round-2 span/snippet strings were extracted from an independently normalized HTML
text; 10 occurrences do not exact-match the filing store purely due to whitespace.
For each: locate the passage in the store (whitespace-insensitive match), then
**re-extract span and snippet as exact substrings of the store text**. Never edit
store text; never keep the canonical-text variant.

| candidate | ticker | occurrence | location |
|---|---|---|---|
| n06 | COIN | occ2 | Item 7 |
| p45 | DDOG | occ1 | Item 7A |
| a18 | DDOG | occ0 | Item 7 |
| p23 | DECK | occ0 | Item 7 |
| n08 | DECK | occ0 | Item 1 |
| n08 | DECK | occ1 | Item 7 |
| a24 | GOOGL | occ0 | Item 7 |
| n02 | LLY | occ1 | Item 7 |
| p28 | NEE | occ0 | Item 7 |
| p32 | XOM | occ0 | Item 1 |

Any other occurrence that fails exact-substring against the store gets the same
treatment. Re-verify snippet length (50–200) after re-extraction; if a re-anchored
snippet leaves the range, choose the closest conforming sentence within the same span.

### T2 — Drop Item 8 locations from OR-sets, with label-escape verification

**Completed 2026-08-27 for the filing-store arm.** Drop/relabel provenance is
recorded per candidate in the affected ticker JSON files and summarized in
`round3_t1_t2_reconciliation.md`. Cross-arm header-path verification is owned by a
separate issue and is intentionally outside this reconciliation.

Remove every occurrence whose location is Item 8 (notes, auditor's report,
financial statements). Known cases: p45 (Notes 2/8), a24 (Note 6), a25 (Note 25),
p16 (Item 8 copies incl. the auditor's critical-audit-matter text), p17 (Note 16),
n08 (Note 1), p48 (Note 8).

**Label-escape verification (mandatory, per dropped location):** exclusion works by
each arm's own `item` label on the chunk, and some filings do not place their
financial statements under the "Item 8" heading (e.g. NVDA's Item 8 in the filing
store is a 207-char pointer stub; the notes text lives elsewhere). For each dropped
location, check whether its text is still reachable in either arm under a non-8
item label:

1. Search the filing store for the occurrence text outside Item 8.
2. If found under another item, that location is NOT excluded by the filter — keep
   it in the OR-set with its actual store header_path (so the same-text copy cannot
   become a false negative).
3. If not found outside Item 8, drop it and record the drop in the row's provenance.

A row must retain at least one non-Item-8 location; if dropping Item 8 leaves a row
with zero locations, escalate to the human reviewer instead of improvising.

### T3 — Rebuild n10 (JPM) evidence from store text

**Completed 2026-08-30.** The filing-store exact strings, anchors, and provenance
for JPM `n10` and LIN `a16` are recorded in their ticker result JSON files and
`round3_t1_t2_reconciliation.md`. `n10` enumerates both reachable store copies;
`a16` retains the APAC sales bridge table and narrative as two independently
sufficient OR alternatives.

The round-2 evidence is table text extracted from the canonical HTML linearization
and does not exact-match the store. Rebuild: locate the CIB trading VaR risk-type
table region in the store's Item 7A text and extract a store-exact span/snippet
covering the four risk types (fixed income, foreign exchange, equities, commodities
and other) within the 50–200 char snippet limit. This row and corrected `a16` are
the dataset's two table-anchored evidence cases; mark them as such in their
`curation_note`. If no store-exact 50–200 char substring can establish the
VaR-to-risk-types relation, escalate — do not substitute a different question.

### T4 — Rework n09 (PODD): replace the question

**Completed 2026-08-27.** Option 1 was selected. The corrected single-intent
question, one independently sufficient occurrence, and full-filing rejection audit
are recorded in `T15_PODD.json` and `T15_PODD_correction_research.md`.

The round-2 question and its 11 accepted occurrences are rejected (too broad, and
over-accepted practices that do not answer "responsibility allocation"). Replace
with ONE of the following, in order of preference, subject to the checks stated:

- **Option 1**: `Has Insulet experienced cybersecurity incidents that materially affected the company?`
  - answer_requirement: One independently sufficient span must state whether
    cybersecurity threats or incidents have (or have not) materially affected
    Insulet's business, operations, or financial condition to date; generic
    warnings that an incident could cause harm are partial.
  - Check first: the impact-to-date sentence is semi-boilerplate. Verify the chosen
    snippet is corpus-unique across all 16 filings (or that every extra occurrence
    is enumerable per decision 6). If it fails, fall back to Option 2.
- **Option 2**: `How does Insulet oversee cybersecurity risks from third-party service providers?`
  - answer_requirement: One independently sufficient span must describe how Insulet
    assesses or manages cybersecurity risk arising from third-party vendors or
    service providers; internal-practice statements without the third-party
    dimension are partial.

Pick exactly one; do not merge them.

### T5 — Narrow p17 (NVDA)

**Completed 2026-08-27.** The corrected factoid and three independently sufficient
store locations (Item 1A, Item 7, and the Item 15 label escape) are recorded in
`T13_NVDA.json`.

Replace the round-2 question with:

- Question: `What share of NVIDIA's fiscal 2026 revenue came from its largest direct customer?`
  (query_type: factoid)
- answer_requirement: One independently sufficient span must state the percentage
  of total fiscal 2026 revenue attributable to NVIDIA's largest direct customer;
  qualitative concentration statements without the percentage are partial.
- Expected OR-set after T2: the "one direct customer represented 22% of total
  revenue" statements in Item 1A and Item 7 (round-2 occ 3 and occ 6). The Note 16
  copy follows T2's label-escape verification.

### T6 — Strict re-verification of multi-occurrence rows

**Completed 2026-08-30.** Seventeen candidates and 41 surviving occurrences were
re-tested literally against their answer requirements. No semantically accepted
occurrence was removed. Corpus enumeration found two additional reachable NEE
`n01` copies under the store's Item 6 label; both were added to the OR-set. The
candidate-level provenance and `round3_t6_semantic_audit.md` record the results.

For every row with 2+ occurrences after T1–T5 (at least: a21, n03, n06, n08, p43,
a19, p45, a24, a25, n01, p16, p20, p29, p48, corrected a16), re-test each occurrence against the
row's `answer_requirement` "must" clause literally. An occurrence that is
"related to the topic" but does not independently satisfy the must clause is
removed. Record removals with one-line reasons. (Round-2 lesson: acceptance
criteria drift during enumeration — n09 accepted practices when the requirement
said responsibility allocation.)

### T7 — Emit the final dataset

- Assemble surviving rows into `dataset.csv` using the existing column contract;
  list columns (`expected_header_paths`, `answer_snippets`, `answer_spans`,
  `block_heading`, `detection_source`) are index-aligned across the OR-set.
- Carry provenance: `answer_requirement`, `investor_intent`/`user_intent`,
  occurrence count, dropped-location notes, `generated_by`, accession numbers.
- Target size and per-item distribution follow the human reviewer's final row
  selection (51 active → ~40); do not invent rows to hit a count.
- Regenerate the README distribution tables from the emitted rows.

## C. Code/contract changes (separate deliverables — not for the assembly agent)

1. Revert `SNIPPET_MAX_CHARS` 350→200 and `SPAN_MAX_TOKENS` 450→300 in
   `validate_dataset.py` (and the matching prompt v3 wording in
   `generate_candidates.py`) — the ratified contract is 50–200 / ≤300.
2. Validator: implement OR-set rules — entry lists are alternatives for every
   query_type; uniqueness becomes enumerated exemption (decision 6); remove
   multi_passage-specific placement rules.
3. `scorer.py`: hit = any listed (header_path, snippet) alternative matches;
   ships as its own PR with tests; note the old 10-row placeholder's 3
   cross-company rows lose their AND semantics (accepted — placeholder slated for
   replacement in DEV-164).
4. DEV-138 eval task: Qdrant filter `must_not item = "Item 8"` on the HTML arm's
   search calls (see DEV-162 issue comment, 2026-08-27).

## D. Verification checklist (before handing back for human review)

- [x] Every span/snippet is a case-insensitive exact substring of the filing store
      text at its listed (ticker, FY, item) location.
- [x] Every snippet is 50–200 chars; every span ≤ 300 cl100k tokens.
- [x] No expected location has an Item 8 header_path.
- [x] Every snippet occurring >1× in the corpus has all occurrences either listed
      in its OR-set or excluded under a documented T2 drop.
- [x] No question is compound (one information need per row; no ", and" clause
      joins, no "and <wh-word>" joins).
- [x] Rows changed in round 3 (T3, T4, T5, T6 removals) are flagged for human
      re-review; unchanged approved rows keep their round-1/round-2 status.
