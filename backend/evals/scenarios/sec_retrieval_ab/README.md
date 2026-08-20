# sec_retrieval_ab — curated retrieval eval dataset (DEV-162)

The 50-row SEC 10-K retrieval eval dataset shared by two consumers: the
HTML-vs-text pipeline A/B comparison (DEV-138) and, after sunset, the
`sec_retrieval` regression-gate promotion (DEV-164). Single SSOT, two
consumers. This directory currently holds only the dataset and its curation
provenance — the A/B `eval_spec.yaml` and scorer wrapper are DEV-138
deliverables.

**Status: draft — pending human annotation review** (`curation/review.csv`).
Rows enter the final dataset only after each is approved there.

## Ground-truth contract (ADR-0016)

Ground truth is a **pipeline-independent document span**, validated against
the filing store (`data/sec_text/`) only — never against a Qdrant
collection, never a chunk id. Two layers per expected entry, index-aligned
across the JSON-list columns:

- `answer_spans[i]` — one contiguous evidence region: exact substring
  (case-insensitive only) of the target Item's text, inside a single block
  (or the flat body / prelude), at most ~300 cl100k tokens (half a chunk).
- `answer_snippets[i]` — the single key sentence inside that span,
  50–200 chars, unique across the whole parsed corpus (boilerplate that
  recurs across filings is rejected — it would create false negatives).
  This is the hit key of the current strict-containment scorer; the span
  layer exists so DEV-164 can move to span-overlap scoring without
  re-annotation.
- `expected_header_paths[i]` — Item level only, new payload contract:
  `TICKER / FY / Item N. Title` (no Part, no block heading). Sub-heading
  precision is the snippet/span's job; the two A/B arms' sub-heading
  structures are not comparable.

No text normalization anywhere in the dataset: normalizing the legacy
`_html` arm's output for fair comparison is the DEV-138 scorer wrapper's
responsibility, not the dataset's.

## Query types

`question` is always English and simulates the retrieval query an LLM
orchestrator sends to the vector search tool (Language Policy: tool
arguments are English) — never the end user's words.

| query_type | evidence shape | rows |
|---|---|---|
| `factoid` | one sentence; span == snippet | 10 |
| `passage` | 2–6 contiguous sentences in one block | 25 |
| `multi_passage` | 2 spans in different blocks (or different Items) of the same filing, one snippet each | 15 |

**No cross-company comparison rows** — production retrieval
(`retriever.search()`) is a single-ticker-filter interface; comparison
happens at the agent layer across separate retrieval calls. Do not
reintroduce this query type.

## Sampling axes

Four axes are covered marginally (50 rows cannot support a full factorial;
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

Distribution tables: see below (generated from the draft dataset).

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
- Over-generation: 25 alternate candidates accompany the 50 primaries in
  the review sheet; rejected primaries are replaced from approved
  alternates.

## Curation pipeline

```
uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.ingest_tickers
uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.generate_candidates
uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.validate_dataset
```

1. `ingest_tickers.py` — parses the ticker grid's latest 10-Ks into the
   filing store and prints the detection-path table.
2. `generate_candidates.py` — sampling + LLM generation + programmatic
   filters; writes `curation/candidates.json`, the draft `dataset.csv`,
   and the review surfaces (`curation/review.md` to read,
   `curation/review.csv` to mark `approved` / `reviewer_comment`).
3. `validate_dataset.py` — the store-anchored validator (rules in its
   docstring); also runs automatically at emit time. Unit tests:
   `backend/tests/evals/test_sec_retrieval_ab_validator.py`.

Human review is the final gate (DEV-162 Human todo): confirm each snippet
really is ground-truth evidence and the Item attribution is right.

## Column contract

Scorer-mapped columns are identical to the `sec_retrieval` scenario
(`question`, `expected_header_paths`, `expected_tickers`, `match_mode`,
`answer_snippets`, `query_type`) so the dataset drops in without scorer
changes. All other columns are provenance and are ignored by the dataset
loader: `answer_spans`, `block_heading`, `detection_source`, `sector`,
`market_cap_bucket`, `generation_mode`, `user_intent`, `curation_note`,
`generated_by`, `fiscal_year`, `accession_number`.

## Ticker grid and distributions

<!-- generated by curation/dataset_stats.py — regenerate after any dataset change -->

### Detection path (rows touching each bucket)

| value | rows |
|---|---|
| markdown_h4 | 22 |
| markdown_h3 | 16 |
| text_fallback | 7 |
| flat | 5 |
| **total (rows)** | **50** |

### Item (rows touching each Item)

| value | rows |
|---|---|
| 1A | 16 |
| 7 | 16 |
| 1 | 9 |
| 1C | 3 |
| 7A | 3 |
| 2 | 1 |
| 3 | 1 |
| 5 | 1 |
| 9A | 1 |
| **total (rows)** | **51** |

### Query type

| value | rows |
|---|---|
| passage | 25 |
| multi_passage | 15 |
| factoid | 10 |
| **total (rows)** | **50** |

### Sector

| value | rows |
|---|---|
| Information Technology | 8 |
| Consumer Discretionary | 7 |
| Financials | 6 |
| Health Care | 6 |
| Industrials | 6 |
| Communication Services | 3 |
| Consumer Staples | 3 |
| Energy | 3 |
| Materials | 3 |
| Real Estate | 3 |
| Utilities | 2 |
| **total (rows)** | **50** |

### Market-cap bucket (provenance)

| value | rows |
|---|---|
| large | 32 |
| mid | 18 |
| **total (rows)** | **50** |

### Generation mode

| value | rows |
|---|---|
| passage_first | 42 |
| intent_first | 8 |
| **total (rows)** | **50** |

### Ticker grid (rows / FY / accession)

| ticker | sector | cap | rows | FY | accession |
|---|---|---|---|---|---|
| AMZN | Consumer Discretionary | large | 4 | 2025 | 0001018724-26-000004 |
| AXON | Industrials | mid | 3 | 2025 | 0001628280-26-011360 |
| CAT | Industrials | large | 3 | 2025 | 0000018230-26-000008 |
| COIN | Financials | mid | 4 | 2025 | 0001679788-26-000015 |
| COST | Consumer Staples | large | 3 | 2025 | 0000909832-25-000101 |
| DDOG | Information Technology | mid | 4 | 2025 | 0001628280-26-008819 |
| DECK | Consumer Discretionary | mid | 3 | 2026 | 0001628280-26-037664 |
| GOOGL | Communication Services | large | 3 | 2025 | 0001652044-26-000018 |
| JPM | Financials | large | 2 | 2025 | 0001628280-26-008131 |
| LIN | Materials | large | 3 | 2025 | 0001628280-26-011430 |
| LLY | Health Care | large | 2 | 2025 | 0000059478-26-000013 |
| NEE | Utilities | large | 2 | 2025 | 0000753308-26-000015 |
| NVDA | Information Technology | large | 4 | 2026 | 0001045810-26-000021 |
| PLD | Real Estate | large | 3 | 2025 | 0001193125-26-051453 |
| PODD | Health Care | mid | 4 | 2025 | 0001145197-26-000028 |
| XOM | Energy | large | 3 | 2025 | 0000034088-26-000045 |
