# Recall@5 under two hit definitions — HTML vs text parsing

Companion to `report.md` §5.2. Same 40 rows, same recorded top-10 retrievals
(`raw/retrievals.jsonl.gz`, nothing re-queried). Both definitions use the same
format-insensitive snippet matching (ignore case, whitespace, markdown table
syntax), so they differ **only** in whether the Item label is required:

- **Snippet only** — a hit if any top-k chunk contains the target snippet,
  whatever its Item label. Question answered: *did the evidence reach the LLM?*
- **Snippet + correct Item** — a hit only if the chunk holding the snippet is
  also labelled with the expected Item. Question answered: *did it also arrive
  with the right section label?* (what citations and the Item 8 filter rely on)
- **Strict scorer** (exact snippet + Item) — the primary metric in `report.md`
  §5.1, kept here as a reference row.

MRR uses the first hit's rank within the top 10 under each definition.

```bash
uv run python -m backend.evals.experiments.parsing_ab.hit_definitions \
    --dataset backend/evals/scenarios/sec_retrieval_ab/dataset.csv \
    --raw <gunzipped raw/retrievals.jsonl.gz> \
    --out <out.md>
```

The strict rows reproduce `report.md` §5.1 exactly, and the @10 rows of the two
relaxed definitions reproduce §5.2 (0.875 / 0.675 HTML, 0.950 text).

## Slide table (recall@5, n = 40)

| | HTML (old) | Text (new) | Δ | rows only text hits / only HTML hits |
|---|---:|---:|---:|---:|
| Content reached the LLM (snippet only) | 0.78 (31/40) | 0.85 (34/40) | +0.08 | 4 / 1 |
| …with the right Item label (snippet + Item) | 0.58 (23/40) | 0.85 (34/40) | +0.28 | 12 / 1 |
| Strict scorer (reference) | 0.53 (21/40) | 0.85 (34/40) | +0.33 | 14 / 1 |

Text loses nothing when the label is required (34 → 34); HTML drops 31 → 23.
Of the +0.28 gap at @5, about +0.08 is evidence the HTML arm never pulled up and
about +0.20 is evidence it found but could not label.

## Full table (recall@5, recall@10, MRR)
| Hit definition | Metric | HTML | Text | Δ text − html | text-only / html-only hits |
|---|---|---:|---:|---:|---:|
| Snippet only (content reached the LLM) | recall@5 | 0.775 (31/40) | 0.850 (34/40) | +0.075 | 4 / 1 |
| Snippet only (content reached the LLM) | recall@10 | 0.875 (35/40) | 0.950 (38/40) | +0.075 | 3 / 0 |
| Snippet only (content reached the LLM) | MRR | 0.649 | 0.683 | +0.034 | — |
| Snippet + correct Item (content and section label) | recall@5 | 0.575 (23/40) | 0.850 (34/40) | +0.275 | 12 / 1 |
| Snippet + correct Item (content and section label) | recall@10 | 0.675 (27/40) | 0.950 (38/40) | +0.275 | 11 / 0 |
| Snippet + correct Item (content and section label) | MRR | 0.505 | 0.683 | +0.179 | — |
| Strict scorer, reference (exact snippet + Item) | recall@5 | 0.525 (21/40) | 0.850 (34/40) | +0.325 | 14 / 1 |
| Strict scorer, reference (exact snippet + Item) | recall@10 | 0.600 (24/40) | 0.950 (38/40) | +0.350 | 14 / 0 |
| Strict scorer, reference (exact snippet + Item) | MRR | 0.464 | 0.683 | +0.219 | — |

## Uncertainty — not for the headline (95% row-bootstrap, same seed as report §5.1)
| Hit definition | Metric | HTML | Text | Δ text − html |
|---|---|---:|---:|---:|
| Snippet only (content reached the LLM) | recall@5 | 0.775 [0.650, 0.900] | 0.850 [0.725, 0.950] | +0.075 [-0.025, +0.175] |
| Snippet only (content reached the LLM) | recall@10 | 0.875 [0.775, 0.975] | 0.950 [0.875, 1.000] | +0.075 [+0.000, +0.175] |
| Snippet only (content reached the LLM) | MRR | 0.649 [0.517, 0.777] | 0.683 [0.561, 0.801] | +0.034 [-0.069, +0.142] |
| Snippet + correct Item (content and section label) | recall@5 | 0.575 [0.425, 0.725] | 0.850 [0.725, 0.950] | +0.275 [+0.125, +0.425] |
| Snippet + correct Item (content and section label) | recall@10 | 0.675 [0.525, 0.825] | 0.950 [0.875, 1.000] | +0.275 [+0.150, +0.425] |
| Snippet + correct Item (content and section label) | MRR | 0.505 [0.360, 0.649] | 0.683 [0.561, 0.801] | +0.179 [+0.048, +0.316] |
| Strict scorer, reference (exact snippet + Item) | recall@5 | 0.525 [0.375, 0.675] | 0.850 [0.725, 0.950] | +0.325 [+0.175, +0.475] |
| Strict scorer, reference (exact snippet + Item) | recall@10 | 0.600 [0.450, 0.750] | 0.950 [0.875, 1.000] | +0.350 [+0.200, +0.500] |
| Strict scorer, reference (exact snippet + Item) | MRR | 0.464 [0.317, 0.611] | 0.683 [0.561, 0.801] | +0.219 [+0.084, +0.360] |

## HTML misses at @5 under snippet + Item (17 rows)
| Row | Ticker | Miss kind | Expected Item path | Label on the top-5 chunk(s) holding the snippet | Snippet rank |
|---|---|---|---|---|---:|
| p41 | GOOGL | label: no Item (`_unknown`) | `GOOGL / 2025 / Item 1C. Cybersecurity` | `GOOGL / 2025 / Part I` | 5 |
| p44 | COST | not in top 5 | `COST / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk` | — | — |
| p45 | DDOG | not in top 5 | `DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / `DDOG / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk` | — | 9 |
| p49 | NVDA | not in top 5 | `NVDA / 2026 / Item 1A. Risk Factors` / `NVDA / 2026 / Item 9A. Controls and Procedures` | — | — |
| a24 | GOOGL | not in top 5 | `GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | — | 8 |
| p21 | COIN | not in top 5 | `COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | — | 9 |
| p23 | DECK | label: no Item (`_unknown`) | `DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | `DECK / 2026 / Part II` | 1 |
| p24 | GOOGL | not in top 5 | `GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | — | 6 |
| p32 | XOM | label: no Item (`_unknown`) | `XOM / 2025 / Item 1. Business` | `XOM / 2025 / Part I` | 4 |
| a20 | PODD | not in top 5 | `PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | — | — |
| a21 | COIN | not in top 5 | `COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / `COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | — | — |
| a23 | DECK | label: no Item (`_unknown`) | `DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | `DECK / 2026 / Part II` | 1 |
| n04 | XOM | label: wrong Item | `XOM / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | `XOM / 2025 / Item 16. Form 10-K Summary / FINANCIAL INFORMATION / MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS` | 1 |
| n05 | COST | label: no Item (`_unknown`) | `COST / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | `COST / 2025` | 1 |
| n08 | DECK | label: no Item (`_unknown`) | `DECK / 2026 / Item 1. Business` | `DECK / 2026 / Part II / Overview`, `DECK / 2026 / Part I / General` | 3 |
| n09 | PODD | label: no Item (`_unknown`) | `PODD / 2025 / Item 1C. Cybersecurity` | `PODD / 2025 / Part I` | 1 |
| n10 | JPM | not in top 5 | `JPM / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` | — | — |

## Diagnosis at @5

The HTML arm misses 17 / 40 rows under *snippet + correct Item*:

- **8 rows — evidence in the top 5, but the label is wrong or missing.**
  - 7 have **no Item label at all** (`_unknown`; the path stops at `Part I` /
    `Part II` or the bare filing): **DECK ×3** (p23, a23, n08), **COST ×1**
    (n05), plus one isolated section each in GOOGL (p41, Item 1C), XOM
    (p32, Item 1) and PODD (n09, Item 1C). In 4 of the 7 the evidence is the
    **#1** result.
  - 1 has the **wrong Item**: `n04` (XOM), labelled under the Item 16 summary
    block instead of Item 7 (the labelling disagreement discussed in
    `report.md` §6).
- **9 rows — evidence not in the top 5.** Five are missing from the top 10 too
  (p44 COST, p49 NVDA, a20 PODD, a21 COIN, n10 JPM). Four sit at ranks 6–9
  (p45 DDOG, a24 GOOGL, p21 COIN, p24 GOOGL).

**JPM is not a label case.** Its only row (`n10`, a table-anchored VaR question)
is missed by *both* arms: neither has the evidence in its top 10. JPM's 97%
`_unknown` chunks matter for the Item 8 filter and search-space scope
(`report.md` §3, §7), not for the label misses counted here.

The text arm's 6 misses at @5 are identical under both definitions: whenever it
retrieves the evidence, the label is right.
