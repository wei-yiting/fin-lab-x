# sec_retrieval_ab — curated retrieval eval dataset (DEV-162)

The 40-row SEC 10-K retrieval eval dataset shared by two consumers: the
HTML-vs-text pipeline A/B comparison (DEV-138) and, after sunset, the
`sec_retrieval` regression-gate promotion (DEV-164). Single SSOT, two
consumers. This directory currently holds only the dataset and its curation
provenance — the A/B `eval_spec.yaml` and scorer wrapper are DEV-138
deliverables.

**Status: assembled (round 3, T7).** The round-2 review was done by two
independent LLM reviewers with the user deciding their disagreements — not a
full human review. See [Review provenance](#review-provenance-round-2) before
quoting results from this dataset.

## Ground-truth contract (ADR-0016)

Ground truth is a **pipeline-independent document span**, validated against
the filing store (`data/sec_text/`) only — never against a Qdrant
collection, never a chunk id. Two layers per expected entry, index-aligned
across the JSON-list columns:

- `answer_spans[i]` — one contiguous evidence region: exact substring
  (case-insensitive only) of the target Item's text, inside a single block
  (or the flat body / prelude), at most ~300 cl100k tokens (half a chunk).
- `answer_snippets[i]` — the single key sentence inside that span,
  50–200 chars. Corpus uniqueness is an enumerated exemption: a snippet may
  recur only if every reachable copy (Item 8 excluded) is listed in the row.
  This is the hit key of the current strict-containment scorer; the span
  layer exists so DEV-164 can move to span-overlap scoring without
  re-annotation.
- `expected_header_paths[i]` — Item level only, new payload contract:
  `TICKER / FY / Item N. Title` (no Part, no block heading). Sub-heading
  precision is the snippet/span's job; the two A/B arms' sub-heading
  structures are not comparable.

The lists are an **OR-set**: each index is an independently sufficient
alternative location, and retrieving any one counts as a hit. Item 8 is
outside retrieval scope on both arms, so no expected location targets it;
copies of the same text that the filing store labels under another Item
(e.g. NVDA Item 15, PLD/XOM Item 16, NEE Item 6) are listed as alternatives.

No text normalization anywhere in the dataset: normalizing the legacy
`_html` arm's output for fair comparison is the DEV-138 scorer wrapper's
responsibility, not the dataset's.

## Query types

`question` is always English and simulates the retrieval query an LLM
orchestrator sends to the vector search tool (Language Policy: tool
arguments are English) — never the end user's words.

| query_type | evidence shape | rows |
|---|---|---|
| `factoid` | one sentence; span == snippet | 20 |
| `passage` | 2–6 contiguous sentences in one block | 20 |

`multi_passage` was removed in round 3: a row is one information need, and
multiple locations are OR alternatives, never an AND of required passages.

**No cross-company comparison rows** — production retrieval
(`retriever.search()`) is a single-ticker-filter interface; comparison
happens at the agent layer across separate retrieval calls. Do not
reintroduce this query type.

## Sampling axes

Four axes are covered marginally (40 rows cannot support a full factorial;
do not read empty cross-cells as gaps):

1. **Detection path** — `markdown_h3` / `markdown_h4` / `text_fallback`
   (from `StructuredItem.detection_source`) / `flat` (`FlatItem`). A row's
   bucket is looked up from its ground-truth Item in the filing store;
   natural distribution, deliberately not rebalanced.
2. **Item** — usage-weighted quotas (1A and 7 dominate; Item 8 is excluded:
   financial-statement content belongs to the fundamentals path, not RAG).
   Item 3 carries a single row: in this grid only one filing has
   substantive litigation text in the 10-K body; the rest point to the
   notes. Two (ticker, item) cells were swapped out during generation
   (`GENERATION_EXCLUSIONS`): JPM Item 1 (mostly incorporated-by-reference
   boilerplate whose sentences recur elsewhere, so no corpus-unique snippet
   exists) and NEE Item 7A (sentences exceed the 200-char snippet cap);
   JPM keeps 2 rows via an Item 1A alternate.
3. **Query type** — table above.
4. **Sector** (with market-cap bucket as provenance) — controlled at ticker
   selection via a GICS sector × cap grid, ~16 tickers, every sector ≥1
   large cap, about half adding one mid/small cap. The legacy HTML
   pipeline's Class A/B/C markup taxonomy was deliberately NOT used for
   selection (it would import that pipeline's calibration bias into the
   shared SSOT).

Distribution tables: see below (generated from the emitted dataset).
Review attrition moved the final distribution away from the sampling design
(see [Known limitations](#known-limitations)).

## Generation provenance

- Generator model: `gpt-5.6-sol` (OpenAI GPT-5.6 flagship tier, GA
  2026-07). Selection record: judge-client path (`gemini-3.6-flash`)
  rejected — that path exists for judge independence, which retrieval eval
  generation does not need; `gpt-5.6-luna` rejected for its long-context
  cliff; `claude-opus-5` was the runner-up (would add a first Anthropic
  SDK dependency for a one-shot script). Per-row `system_fingerprint` is
  recorded in `curation/candidates.json`.
- Prompt: `curation/generate_candidates.py` (`PROMPT_VERSION` constant).
  Rows carry the version that generated them: v1, or v2 — which added the
  multi_passage single-information-need constraint, an intent-infeasible
  escape hatch (two intent rows fell back to passage-first when their Item
  had no evidence for the intent), an abbreviation guard in sentence
  splitting, and a rejected-snippet exclusion list
  (`curation/rejected_snippets.json`);
  sentence-index technique — the model returns sentence indices, span and
  snippet strings are reconstructed from the original text, so
  exact-substring correctness holds by construction.
- Anti-lexical-overlap: queries may not reuse any 3-gram from the evidence
  span and are capped at 0.5 Jaccard vs the snippet (forces paraphrase, so
  dense retrieval is measured rather than term matching).
- Modes: passage-first (evidence → query) with 8 intent-first rows
  (lay user intent, recorded in `user_intent` → evidence). The 18 zh
  questions from the DEV-113 experiment informed intent style only; none
  were copied.
- Over-generation: alternate candidates accompany the 50 primaries in the
  review sheet; a rejected primary is replaced from the alternates and
  moved to the review sheet's trailing "Rejected candidates" section
  (provenance only, `in_draft: rejected` in review.csv).

## Review provenance (round 2)

- **Round 1** — human review of the 50 generated rows; 34% approved as is.
  Most failures were compound questions or a highlighted sentence that did
  not answer the question.
- **Round 2 rewrite** — 51 active candidates (round-1 rows rewritten, plus
  10 new intent-first rows `n01`–`n10` written by a curation agent), each
  traversed against the full filing to enumerate every independently
  sufficient location; round-3 tasks T1–T6 re-anchored them to the filing
  store (`curation/round3_assembly_instructions.md`).
- **Round 2 review — two independent LLM reviewers, user decides
  disagreements.** The planned human review of the 51 candidates was not
  done. Instead two LLM reviewers ran the same rubric independently
  (`curation/round2_llm_review_reviewer_a.csv`,
  `curation/round2_llm_review_codex.csv`); neither saw the other's output.
  Rows both approved were included unchanged (25). Disagreements were listed
  side by side in `curation/round2_reconciliation.md`, and the user approved
  a subset of fixes (15 rows: G1 where both reviewers proposed the same fix,
  and the mechanical G3 fixes). Every other disputed row is excluded (11),
  so 40 of 51 candidates remain. The 15 fixed rows were then re-reviewed
  by reviewer B against the same rubric
  (`curation/round3_llm_review_codex.csv`); all 15 were approved.
- Per-row trace: `candidate_id`, `answer_requirement` (the literal
  sufficiency test each alternative passed) and `review_provenance` (which
  of the above paths admitted the row and what was changed).

## Known limitations

- **Item 1A is under-covered.** The design weighted 1A and 7 equally; after
  review attrition only 3 rows touch Item 1A and only one (`p18`) is a pure
  Risk Factors question (the others list 1A as one OR alternative), against
  25 rows touching Item 7. A/B conclusions about Risk Factors
  parsing are weak.
- **Consumer Discretionary, CAT, JPM, LLY, NEE** are carried by 1–3 rows each;
  per-ticker results are anecdotes, not measurements.
- **Table-anchored snippets** (`a16`, `n10`, the PLD Item 16 alternative of
  `p48`) contain the filing store's table linearization; the HTML arm needs
  the DEV-138 wrapper's whitespace normalization to match them.
- **`n08`** — the same brand sentence also appears in DECK Item 7, but the
  filing store parses it there as block headings (a `text_fallback`
  misdetection), so it has no store-exact Item 7 span and an arm that
  retrieves the Item 7 copy scores a miss.
- The generator's anti-lexical filter (no 3-gram from the span) is a
  generation-time rule; reviewed rows may share standard metric or product
  terms with their evidence (e.g. "net retention rate", "constant currency").

## Curation pipeline

```
uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.ingest_tickers
uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.generate_candidates
uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.assemble_dataset
uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.validate_dataset
```

1. `ingest_tickers.py` — parses the ticker grid's latest 10-Ks into the
   filing store and prints the detection-path table.
2. `generate_candidates.py` — sampling + LLM generation + programmatic
   filters; writes `curation/candidates.json`, the round-1 draft `dataset.csv`
   (superseded — re-running its emit step overwrites the assembled dataset),
   and the review surfaces (`curation/review.md` to read,
   `curation/review.csv` to mark `approved` / `reviewer_comment`).
3. `assemble_dataset.py` — round-3 T7: builds the final `dataset.csv` from
   `curation/round2_ticker_results/*.json` plus the approved reconciliation
   decisions (encoded as tables in the module), resolving every location
   against the filing store, then runs the validator.
4. `validate_dataset.py` — the store-anchored validator (rules in its
   docstring); also runs automatically at emit time. Unit tests:
   `backend/tests/evals/test_sec_retrieval_ab_validator.py`.

`generate_candidates.py` and its round-1 surfaces (`curation/review.*`,
`curation/candidates.json`) are kept as provenance; the current `dataset.csv`
is produced by `assemble_dataset.py`, not by `generate_candidates.py`.

## Column contract

Scorer-mapped columns are identical to the `sec_retrieval` scenario
(`question`, `expected_header_paths`, `expected_tickers`, `match_mode`,
`answer_snippets`, `query_type`) so the dataset drops in without scorer
changes. All other columns are provenance and are ignored by the dataset
loader: `answer_spans`, `block_heading`, `detection_source`, `sector`,
`market_cap_bucket`, `generation_mode`, `user_intent`, `curation_note`,
`generated_by`, `fiscal_year`, `accession_number`, `candidate_id`,
`answer_requirement`, `review_provenance`. `curation_note` holds the round-2
change rationale; `generated_by` is `gpt-5.6-sol` for rows that originate
from round-1 generation and `round2-curation-agent` for `n01`–`n10`.

## Ticker grid and distributions

<!-- generated by curation/dataset_stats.py — regenerate after any dataset change -->

### Detection path (rows touching each bucket)

| value | rows |
|---|---|
| markdown_h3 | 21 |
| markdown_h4 | 13 |
| text_fallback | 7 |
| flat | 3 |
| **total (rows)** | **44** |

### Item (rows touching each Item)

| value | rows |
|---|---|
| 7 | 25 |
| 1 | 9 |
| 16 | 3 |
| 1A | 3 |
| 7A | 3 |
| 15 | 2 |
| 1C | 2 |
| 5 | 1 |
| 6 | 1 |
| 9A | 1 |
| **total (rows)** | **50** |

### Query type

| value | rows |
|---|---|
| factoid | 20 |
| passage | 20 |
| **total (rows)** | **40** |

### Sector

| value | rows |
|---|---|
| Information Technology | 8 |
| Consumer Discretionary | 6 |
| Health Care | 6 |
| Financials | 4 |
| Communication Services | 3 |
| Industrials | 3 |
| Materials | 3 |
| Consumer Staples | 2 |
| Energy | 2 |
| Real Estate | 2 |
| Utilities | 1 |
| **total (rows)** | **40** |

### Market-cap bucket (provenance)

| value | rows |
|---|---|
| large | 23 |
| mid | 17 |
| **total (rows)** | **40** |

### Generation mode

| value | rows |
|---|---|
| passage_first | 27 |
| intent_first | 13 |
| **total (rows)** | **40** |

### Ticker grid (rows / FY / accession)

| ticker | sector | cap | rows | FY | accession |
|---|---|---|---|---|---|
| AMZN | Consumer Discretionary | large | 3 | 2025 | 0001018724-26-000004 |
| AXON | Industrials | mid | 2 | 2025 | 0001628280-26-011360 |
| CAT | Industrials | large | 1 | 2025 | 0000018230-26-000008 |
| COIN | Financials | mid | 3 | 2025 | 0001679788-26-000015 |
| COST | Consumer Staples | large | 2 | 2025 | 0000909832-25-000101 |
| DDOG | Information Technology | mid | 4 | 2025 | 0001628280-26-008819 |
| DECK | Consumer Discretionary | mid | 3 | 2026 | 0001628280-26-037664 |
| GOOGL | Communication Services | large | 3 | 2025 | 0001652044-26-000018 |
| JPM | Financials | large | 1 | 2025 | 0001628280-26-008131 |
| LIN | Materials | large | 3 | 2025 | 0001628280-26-011430 |
| LLY | Health Care | large | 1 | 2025 | 0000059478-26-000013 |
| NEE | Utilities | large | 1 | 2025 | 0000753308-26-000015 |
| NVDA | Information Technology | large | 4 | 2026 | 0001045810-26-000021 |
| PLD | Real Estate | large | 2 | 2025 | 0001193125-26-051453 |
| PODD | Health Care | mid | 5 | 2025 | 0001145197-26-000028 |
| XOM | Energy | large | 2 | 2025 | 0000034088-26-000045 |
