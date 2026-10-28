# HTML vs Text Parsing A/B — SEC 10-K Retrieval

> **One-line takeaway:** On 40 reviewed questions over 16 10-K filings, the
> edgartools-based text pipeline reaches recall@10 **0.95** vs **0.60** for the
> frozen hand-written HTML parser (Δ **+0.35**, 95% CI [+0.20, +0.50];
> 14 text-only hits, 0 HTML-only). **Most of that gap is Item attribution, not
> evidence retrieval:** once Item labels and formatting are ignored, the HTML arm
> still puts the evidence in its top 10 on 0.875 of rows, and the gap shrinks to
> +0.075 [+0.000, +0.175]. The text pipeline's win is that it knows *which Item*
> a passage belongs to. The frozen parser loses Items outright: some filings
> 100%, others for scattered sections.

This is the reference report: design, tables, per-row results, failure examples,
claim boundary, and how to reproduce. For what else is in this directory, see
[`README.md`](README.md).

## Reproduce

| | |
|---|---|
| Git tag | `experiment/2026-10-28-parsing-ab` |
| Retrievals produced at | `6ca3fe8` (clean tree; recorded in `run_meta.json`) |
| Harness | `backend/evals/experiments/parsing_ab/` (`ingest` → `run` → `analyze`) |
| Dataset | `backend/evals/scenarios/sec_retrieval_ab/dataset.csv`, sha256 `e9c7367a…` (40 rows) |
| Collections | `sec_ab_parsing_html_20261028` (7,366 chunks), `sec_ab_parsing_text_20261028` (3,137 chunks) |
| Linear | DEV-138 (DEV-181 HTML measurement, DEV-182 text measurement, DEV-183 paired analysis) |

```bash
# 1. both arms, every dataset filing (EDGAR + OpenAI embeddings; ~25 min)
uv run python -m backend.evals.experiments.parsing_ab.ingest \
    --dataset backend/evals/scenarios/sec_retrieval_ab/dataset.csv \
    --out backend/evals/results/parsing_ab/ingest_manifest.json
# 2. 40 rows x 2 arms (put raw/query_embeddings.json.gz, gunzipped, at
#    <out-dir>/query_embeddings.json to reuse the exact query vectors)
uv run python -m backend.evals.experiments.parsing_ab.run \
    --dataset backend/evals/scenarios/sec_retrieval_ab/dataset.csv \
    --out-dir backend/evals/results/parsing_ab/final
# 3. scoring + tables (re-scoring only needs raw/retrievals.jsonl.gz)
uv run python -m backend.evals.experiments.parsing_ab.analyze \
    --dataset backend/evals/scenarios/sec_retrieval_ab/dataset.csv \
    --raw backend/evals/results/parsing_ab/final/retrievals.jsonl \
    --out-dir backend/evals/results/parsing_ab/final \
    --manifest backend/evals/results/parsing_ab/ingest_manifest.json
```

The text arm reads the filing store (`data/sec_text/`, gitignored). Regenerate it
under edgartools 5.62 with `parse_filing(ticker, fiscal_year, force=True)` for the
16 filings in `run_meta.json`; the dataset validator
(`curation/validate_dataset.py`) must report `OK — 40 rows` before step 1.

## 1. Question and design

**Question:** with everything downstream held fixed, does replacing the
hand-written HTML→markdown parser with the edgartools-based text pipeline
(Item detection + block detection) change what dense retrieval finds?

Two arms, paired by question: each dataset row is sent to both arms, and each arm
is its **production** ingest and `search()` path, unmodified, pointed at its own
Qdrant collection.

| | HTML arm (frozen baseline) | Text arm (candidate) |
|---|---|---|
| Parse | `sec_filing_pipeline_html` (EDGAR HTML → markdown, own heading detection) | `sec_text_pipeline` (edgartools Item sections → block detection → `ParsedFiling`) |
| Chunk/embed/search | `sec_dense_pipeline_html` | `sec_dense_pipeline` (JIT retriever) |
| Item label on a chunk | parsed from the markdown heading path; `_unknown` when none | the `ParsedFiling` Item |
| Item 8 exclusion | query-time `must_not item = "Item 8"` (`exclude_items`) | Item 8 not ingested |
| Scoring | OR-set `sec_retrieval` scorer via the DEV-180 compat wrapper (#74) | OR-set `sec_retrieval` scorer as-is |

## 2. Controlled variables

| Variable | Value (both arms) | How it is enforced |
|---|---|---|
| Filing | same accession per (ticker, FY) | checked per filing at ingest (`same_accession: true` ×16) |
| edgartools | 5.62.0 | recorded in `ingest_manifest.json` |
| Embedding | `text-embedding-3-large`, 3072 dims | asserted equal at run start |
| Query vector | identical per question | both arms' `_embed_texts` routed through one disk-persisted cache |
| Chunking | 512 / 50 tokens, cl100k `RecursiveCharacterTextSplitter` | each arm's production constants |
| Top-k | 10 | harness constant |
| Scope filter | ticker + fiscal year | each arm's production filter |
| Item 8 | excluded | see §1 table |
| Dataset | same 40 rows, same OR-set ground truth | one CSV, sha256 in `run_meta.json` |

**The only variable is parse + chunk.** One consequence is not controlled, by
design: chunk *count* follows from the parse (7,366 HTML vs 3,137 text chunks;
the HTML arm renders tables as pipe markdown, which costs tokens).

## 3. Corpus and ingestion

16 filings (the dataset's ticker grid), 16/16 ingested in both arms, no failures.

| Filing | Text chunks | HTML chunks | HTML `Item 8` | HTML `_unknown` |
|---|---:|---:|---:|---:|
| AMZN/2025 | 113 | 332 | 184 | 22 |
| AXON/2025 | 140 | 387 | 204 | 24 |
| CAT/2025 | 172 | 628 | 334 | 46 |
| COIN/2025 | 247 | 554 | 232 | 10 |
| **COST/2025** | 88 | 162 | 0 | **162 (100%)** |
| DDOG/2025 | 159 | 344 | 140 | 5 |
| **DECK/2026** | 409 | 288 | 0 | **288 (100%)** |
| GOOGL/2025 | 137 | 397 | 216 | 7 |
| **JPM/2025** | 371 | 1,124 | 1 | **1,087 (97%)** |
| LIN/2025 | 126 | 415 | 232 | 21 |
| LLY/2025 | 145 | 342 | 166 | 5 |
| NEE/2025 | 188 | 658 | 338 | 114 |
| NVDA/2026 | 209 | 338 | 1 | 14 |
| PLD/2025 | 326 | 550 | 1 | 6 |
| PODD/2025 | 130 | 336 | 151 | 50 |
| XOM/2025 | 177 | 511 | 1 | 17 |
| **Total** | **3,137** | **7,366** | | |

**Frozen-parser Item detection fails on three filings**, with three different causes:
- **COST:** Item headings are plain-text lines (`Item 7—Management's Discussion…`), not markdown headings.
- **DECK:** Item headings sit inside a table row (`| ITEM 7. … |`).
- **JPM:** headings are detected, but the 10-K body lives outside the Item sections.

None of this was patched, because it is the arm under test. Two side effects:
- Every row on these filings is an HTML label-miss by construction.
- Item 8 content in these filings is labelled `_unknown`, so the HTML arm's exclusion filter does not remove it. HTML retrieval scope there is wider than the text arm's.

## 4. Dataset

`sec_retrieval_ab` (DEV-162): 40 rows, 20 factoid / 20 passage, OR-set ground
truth (index-aligned alternative locations; a hit on any one counts), English
queries written as an orchestrator's tool call, anti-lexical-overlap with the
evidence. Ground truth is a filing-store span plus a 50–200-char snippet,
validated against the store, never against Qdrant (ADR-0016).

**Re-anchored to edgartools 5.62 for this run.** The rows were assembled on a
store parsed under edgartools 5.17.1. Both arms run on 5.62, so the store was
re-parsed and every row re-anchored (`curation/reanchor_to_store.py`).
- **Unchanged:** questions, answer requirements, and the evidence text.
- **Re-anchored by location:** 3 rows. 5.62 fixes Item mis-assignments (`n04` Item 16 → 7, `n10` Items 1/15 → 7, `n01`'s Item 6 copies merged into Item 7).
- **Re-extracted for table whitespace:** 4 rows, including `p48`'s snippet widened within its span to stay ≥ 50 chars.
- **Metadata refreshed:** `block_heading` on 29 rows and `detection_source` on 22. 5.62 emits no `markdown_h4` Items.
- Each changed row says so in `review_provenance`. Validator: `OK — 40 rows`.

The superseded 5.17.1 text-arm ingest manifest is kept under `raw/` for comparison.

## 5. Results

### 5.1 Aggregate (n = 40; 95% row-bootstrap CI, 10,000 resamples, seed 20261028)

| Metric | HTML (frozen) | Text | Δ text − html | text-only / html-only hits | McNemar exact p |
|---|---:|---:|---:|---:|---:|
| recall@5 | 0.525 [0.375, 0.675] | 0.850 [0.725, 0.950] | +0.325 [+0.175, +0.475] | 14 / 1 | 0.001 |
| recall@10 | 0.600 [0.450, 0.750] | 0.950 [0.875, 1.000] | +0.350 [+0.200, +0.500] | 14 / 0 | < 0.001 |
| MRR | 0.464 [0.317, 0.611] | 0.683 [0.561, 0.801] | +0.219 [+0.084, +0.360] | — | — |

MAP is not reported: under OR-set scoring each row has a single relevant target,
so MAP equals MRR.

### 5.2 Where the gap comes from

Recall@10 under progressively relaxed hit rules. Each step drops one requirement
of the strict scorer, symmetrically for both arms.

| Hit rule | HTML | Text | Δ text − html |
|---|---:|---:|---:|
| **Strict** (primary: Item path + exact snippet) | 0.600 [0.450, 0.750] | 0.950 [0.875, 1.000] | +0.350 [+0.200, +0.500] |
| **Format-insensitive** (Item path required; snippet ignores case, whitespace, table syntax) | 0.675 [0.525, 0.825] | 0.950 [0.875, 1.000] | +0.275 [+0.150, +0.425] |
| **Label-agnostic** (snippet anywhere in top 10, same relaxed matching) | 0.875 [0.775, 0.975] | 0.950 [0.875, 1.000] | +0.075 [+0.000, +0.175] |

Per-row miss classes at @10:

| Arm | hit | format-miss | label-miss | retrieval-miss |
|---|---:|---:|---:|---:|
| HTML | 24 | 3 | 8 | 5 |
| Text | 38 | 0 | 0 | 2 |

The +0.35 decomposes into roughly +0.075 formatting, +0.20 Item attribution, and
+0.075 evidence retrieval. The last component's CI touches zero.

Of the HTML arm's 8 label-misses:
- **7** retrieved the evidence in a chunk with **no Item at all** (`_unknown`, path ends at `Part I` / `Part II` or the bare filing). These cover COST, DECK and JPM, but also isolated sections of GOOGL (1C), XOM (1) and PODD (1C).
- **1** (`n04`, XOM) is a genuine labelling disagreement, discussed in §6.

### 5.3 Sensitivity: degraded filings excluded (n = 34)

Rows on COST, DECK, JPM dropped (≥ 50% of HTML chunks `_unknown`):

| Metric | HTML | Text | Δ text − html | text-only / html-only | McNemar p |
|---|---:|---:|---:|---:|---:|
| recall@5 | 0.618 [0.441, 0.765] | 0.853 [0.735, 0.971] | +0.235 [+0.088, +0.412] | 9 / 1 | 0.021 |
| recall@10 | 0.706 [0.559, 0.853] | 0.971 [0.912, 1.000] | +0.265 [+0.118, +0.412] | 9 / 0 | 0.004 |
| MRR | 0.546 [0.391, 0.702] | 0.695 [0.566, 0.817] | +0.149 [+0.014, +0.292] | — | — |

The gap is not just three broken filings: it survives their removal.

### 5.4 Breakdowns (recall@10 / MRR means; a row counts in every bucket it touches)

| Query type | n | HTML r@10 | Text r@10 | HTML MRR | Text MRR |
|---|---:|---:|---:|---:|---:|
| factoid | 20 | 0.450 | 0.900 | 0.249 | 0.624 |
| passage | 20 | 0.750 | 1.000 | 0.679 | 0.743 |

| Detection path (text pipeline, 5.62) | n | HTML r@10 | Text r@10 | HTML MRR | Text MRR |
|---|---:|---:|---:|---:|---:|
| markdown_h3 | 25 | 0.720 | 0.920 | 0.538 | 0.627 |
| text_fallback | 16 | 0.438 | 0.938 | 0.335 | 0.639 |
| flat | 2 | 0.000 | 1.000 | 0.000 | 1.000 |

The HTML arm is weakest where the text pipeline itself had to fall back to
Title-Case text detection: those are the filings whose headings are not clean
markup, which is exactly what the frozen parser depends on. Factoid rows hurt the
HTML arm more than passage rows: a single sentence has less surrounding context to
pull its chunk up the ranking. Per-ticker numbers are in `tables.md`; at 1–5 rows
per ticker they are anecdotes, not measurements.

## 6. Failure examples

**HTML misses, text hits (14 rows).** Representative cases by class:

| Row | Class | What happened |
|---|---|---|
| `n05` COST — "What drove Costco's comparable-sales growth in fiscal 2025?" | label-miss | HTML rank-1 chunk contains the evidence, but its path is `COST / 2025`: no Item was ever detected in this filing. Text: rank 1. |
| `a23` DECK — constant-currency net sales growth | label-miss | Same pattern: evidence at HTML rank 1 under `DECK / 2026 / Part II`. |
| `p41` GOOGL — "Who independently evaluates Alphabet's cyber defenses?" | label-miss | GOOGL's Item detection works overall (7 `_unknown` chunks of 397), but the evidence chunk is one of them (`Part I`). Text: rank 1. |
| `n04` XOM — lower crude prices and Upstream earnings | label-miss (**disputed**) | XOM's 10-K places MD&A in a Financial Section after Item 16; Item 7 is a cross-reference. The HTML arm labels the chunk `Item 16 / FINANCIAL INFORMATION / MANAGEMENT'S DISCUSSION…` (positional). The 5.62 text pipeline attributes it to Item 7 (semantic), and the dataset follows the text store. Both readings are defensible. |
| `a18` DDOG — net retention rate change | format-miss | HTML rank-1 chunk is correctly labelled Item 7 and holds the figure, but as a pipe table; the strict snippet does not match its whitespace. |
| `a20` PODD, `a21` COIN, `p44` COST | retrieval-miss | The evidence is not in the HTML arm's top 10 at all. Text found it at ranks 9, 10 and 5, so these are near the cutoff on the text side too. |

**Text misses, HTML hits:** none at @10. At @5, one row (`p20` PODD: HTML rank 1,
text rank 7).

**Both arms miss (2 rows):**
- `n10` (JPM): a table-anchored VaR question; the evidence is a table region that neither arm ranks into the top 10.
- `p49` (NVDA).

The full per-row table is in §8, and both arms' top-10 chunks per row are in `raw/retrievals.jsonl.gz`.

## 7. Claim boundary

What this supports:
- On this dataset and corpus, the text pipeline retrieves correctly-attributed evidence substantially more often than the frozen HTML parser: recall@10 Δ +0.35 [+0.20, +0.50], McNemar p < 0.001, 14 of 14 discordant rows favour text. The direction holds with the three degraded filings removed.
- The mechanism is mostly **Item attribution**: the frozen parser leaves passages with no Item, from 100% of a filing down to isolated sections. Pure evidence retrieval differs little: Δ +0.075, CI [0.000, +0.175].

What it does **not** support:
- **Not a full human review.** The dataset's round-2 review was done by two independent LLM reviewers, with the user deciding their disagreements. It was then mechanically re-anchored to the 5.62 parse (§4).
- **The Item-label component is measured against the text pipeline's own Item attribution.** Ground-truth locations come from the text pipeline's filing store (ADR-0016), so when the two parsers disagree on an Item, the text arm wins by construction. In this run that changed exactly one row (`n04`), where the HTML label is arguably as correct. The arm-neutral comparison is the label-agnostic row in §5.2.
- **Small n.** 40 rows over 16 filings. Per-ticker and per-Item cells are 1–5 rows. Item 1A is under-covered (one pure 1A row). Interval widths of ±0.15 on the deltas are the honest resolution.
- **Retrieval only.** Nothing here measures answer quality, citation quality or end-to-end agent behaviour.
- **One corpus snapshot.** Latest 10-K per ticker, edgartools 5.62. The text pipeline's output is sensitive to the edgartools version: the 5.17.1 → 5.62 re-parse changed every filing, removing up to 53% of a filing's chunks (NEE: 402 → 188).
- **Scope is not perfectly symmetric.** On COST/DECK/JPM, Item 8 content stays in the HTML arm's search space (labelled `_unknown`), which can crowd its top 10.

## 8. Per-row results

Rank = 1-based rank of the first strict hit (— = none in top 10). Outcome classes
as in §5.2. Full columns, including the format-insensitive and label-agnostic
ranks, are in `per_row.csv`.

| row | ticker | type | detection | HTML rank | Text rank | HTML outcome | Text outcome |
|---|---|---|---|---:|---:|---|---|
| p20 | PODD | passage | markdown_h3 | 1 | 7 | hit | hit |
| p38 | COIN | passage | markdown_h3 | 1 | 1 | hit | hit |
| p41 | GOOGL | factoid | flat | — | 1 | label-miss | hit |
| p43 | AXON | factoid | markdown_h3, text_fallback | — | 4 | format-miss | hit |
| p44 | COST | factoid | text_fallback | — | 5 | retrieval-miss | hit |
| p45 | DDOG | factoid | text_fallback | 9 | 9 | hit | hit |
| p48 | PLD | factoid | markdown_h3, text_fallback | 4 | 3 | hit | hit |
| p49 | NVDA | factoid | markdown_h3, text_fallback | — | — | retrieval-miss | retrieval-miss |
| a24 | GOOGL | passage | markdown_h3 | — | 1 | format-miss | hit |
| p16 | LIN | factoid | markdown_h3 | 1 | 1 | hit | hit |
| p17 | NVDA | factoid | markdown_h3 | 1 | 1 | hit | hit |
| p18 | DDOG | passage | markdown_h3 | 1 | 1 | hit | hit |
| p21 | COIN | factoid | markdown_h3 | 9 | 3 | hit | hit |
| p22 | AMZN | passage | text_fallback | 1 | 3 | hit | hit |
| p23 | DECK | factoid | text_fallback | — | 1 | label-miss | hit |
| p24 | GOOGL | factoid | markdown_h3 | 6 | 1 | hit | hit |
| p26 | AXON | passage | markdown_h3 | 1 | 1 | hit | hit |
| p29 | PLD | factoid | markdown_h3 | 1 | 1 | hit | hit |
| p30 | LIN | factoid | markdown_h3 | 3 | 4 | hit | hit |
| p32 | XOM | factoid | flat | — | 1 | label-miss | hit |
| p33 | NVDA | passage | text_fallback | 1 | 1 | hit | hit |
| p34 | DDOG | passage | text_fallback | 1 | 1 | hit | hit |
| p35 | PODD | factoid | markdown_h3 | 1 | 1 | hit | hit |
| p36 | PODD | passage | markdown_h3 | 1 | 1 | hit | hit |
| p37 | AMZN | passage | text_fallback | 1 | 1 | hit | hit |
| a16 | LIN | passage | markdown_h3 | 3 | 3 | hit | hit |
| a17 | NVDA | passage | markdown_h3 | 4 | 3 | hit | hit |
| a18 | DDOG | factoid | text_fallback | — | 1 | format-miss | hit |
| a19 | LLY | passage | markdown_h3 | 1 | 1 | hit | hit |
| a20 | PODD | passage | markdown_h3 | — | 9 | retrieval-miss | hit |
| a21 | COIN | passage | markdown_h3 | — | 10 | retrieval-miss | hit |
| a22 | AMZN | passage | text_fallback | 1 | 1 | hit | hit |
| a23 | DECK | factoid | text_fallback | — | 1 | label-miss | hit |
| a25 | CAT | passage | markdown_h3 | 1 | 1 | hit | hit |
| n01 | NEE | passage | markdown_h3 | 1 | 1 | hit | hit |
| n04 | XOM | passage | markdown_h3 | — | 2 | label-miss | hit |
| n05 | COST | passage | text_fallback | — | 1 | label-miss | hit |
| n08 | DECK | factoid | text_fallback | — | 2 | label-miss | hit |
| n09 | PODD | factoid | text_fallback | — | 2 | label-miss | hit |
| n10 | JPM | factoid | markdown_h3 | — | — | retrieval-miss | retrieval-miss |

## 9. Methods notes

- **Statistics.** Rows are the unit; both arms answer the same row, so deltas are paired.
  - Arm means and mean deltas use percentile row-bootstrap CIs.
  - Recall@k is 0/1 per row, so an exact two-sided McNemar test on discordant rows is reported alongside.
- **Deterministic query vectors.** Each question is embedded once and both arms search with that vector (`raw/query_embeddings.json.gz`), so embedding-API nondeterminism cannot differ between arms.
- **HTML scoring.** HTML chunks pass through `html_arm_compat.normalize_chunks` (#74), which rebuilds the Item segment to the dataset's `TICKER / FY / Item N. Title` shape. A chunk with no detected Item passes through unchanged and scores as a miss, by the wrapper's design.
- **Process history.**
  - A smoke run on the pre-review draft dataset validated the harness. Those numbers were superseded and are not reported.
  - The first ingest of the text arm used the 5.17.1 store. It was redone on 5.62, together with the dataset re-anchoring, so both arms share one edgartools version.
