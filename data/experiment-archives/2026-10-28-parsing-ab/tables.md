## Aggregate (95% row-bootstrap CI, 10,000 resamples, seed 20261028)

| Metric | HTML (frozen) | Text | Δ text − html | text-only / html-only hits | McNemar exact p |
|---|---:|---:|---:|---:|---:|
| recall_at_5 | 0.525 [0.375, 0.675] | 0.850 [0.725, 0.950] | +0.325 [+0.175, +0.475] | 14 / 1 | 0.001 |
| recall_at_10 | 0.600 [0.450, 0.750] | 0.950 [0.875, 1.000] | +0.350 [+0.200, +0.500] | 14 / 0 | 0.000 |
| mrr | 0.464 [0.317, 0.611] | 0.683 [0.561, 0.801] | +0.219 [+0.084, +0.360] | — | — |

n = 40 rows. MAP is not reported: under OR-set scoring each row has one relevant target, so MAP equals MRR.

## Sensitivity: filings with failed HTML Item detection excluded

Excluded tickers (≥50% of HTML-arm chunks labelled `_unknown`): COST, DECK, JPM — 6 rows dropped.

| Metric | HTML (frozen) | Text | Δ text − html | text-only / html-only hits | McNemar exact p |
|---|---:|---:|---:|---:|---:|
| recall_at_5 | 0.618 [0.441, 0.765] | 0.853 [0.735, 0.971] | +0.235 [+0.088, +0.412] | 9 / 1 | 0.021 |
| recall_at_10 | 0.706 [0.559, 0.853] | 0.971 [0.912, 1.000] | +0.265 [+0.118, +0.412] | 9 / 0 | 0.004 |
| mrr | 0.546 [0.391, 0.702] | 0.695 [0.566, 0.817] | +0.149 [+0.014, +0.292] | — | — |

n = 34 rows.

## Decomposition: recall@10 under progressively relaxed hit rules

| hit rule | HTML (frozen) | Text | Δ text − html |
|---|---:|---:|---:|
| strict (primary: scorer as-is) | 0.600 [0.450, 0.750] | 0.950 [0.875, 1.000] | +0.350 [+0.200, +0.500] |
| format-insensitive (Item path required; snippet ignores case/whitespace/table syntax) | 0.675 [0.525, 0.825] | 0.950 [0.875, 1.000] | +0.275 [+0.150, +0.425] |
| label-agnostic (snippet anywhere in top 10, same relaxed matching) | 0.875 [0.775, 0.975] | 0.950 [0.875, 1.000] | +0.075 [+0.000, +0.175] |

## Breakdown by query_type (recall@10 / MRR means; a row counts in every bucket it touches)

| bucket | n | HTML r@10 | Text r@10 | HTML MRR | Text MRR |
|---|---:|---:|---:|---:|---:|
| factoid | 20 | 0.450 | 0.900 | 0.249 | 0.624 |
| passage | 20 | 0.750 | 1.000 | 0.679 | 0.743 |

## Breakdown by detection_source (recall@10 / MRR means; a row counts in every bucket it touches)

| bucket | n | HTML r@10 | Text r@10 | HTML MRR | Text MRR |
|---|---:|---:|---:|---:|---:|
| markdown_h3 | 25 | 0.720 | 0.920 | 0.538 | 0.627 |
| text_fallback | 16 | 0.438 | 0.938 | 0.335 | 0.639 |
| flat | 2 | 0.000 | 1.000 | 0.000 | 1.000 |

## Breakdown by ticker (recall@10 / MRR means; a row counts in every bucket it touches)

| bucket | n | HTML r@10 | Text r@10 | HTML MRR | Text MRR |
|---|---:|---:|---:|---:|---:|
| PODD | 5 | 0.600 | 1.000 | 0.600 | 0.551 |
| DDOG | 4 | 0.750 | 1.000 | 0.528 | 0.778 |
| NVDA | 4 | 0.750 | 0.750 | 0.562 | 0.583 |
| AMZN | 3 | 1.000 | 1.000 | 1.000 | 0.778 |
| COIN | 3 | 0.667 | 1.000 | 0.370 | 0.478 |
| DECK | 3 | 0.000 | 1.000 | 0.000 | 0.833 |
| GOOGL | 3 | 0.333 | 1.000 | 0.056 | 1.000 |
| LIN | 3 | 1.000 | 1.000 | 0.556 | 0.528 |
| AXON | 2 | 0.500 | 1.000 | 0.500 | 0.625 |
| COST | 2 | 0.000 | 1.000 | 0.000 | 0.600 |
| PLD | 2 | 1.000 | 1.000 | 0.625 | 0.667 |
| XOM | 2 | 0.000 | 1.000 | 0.000 | 0.750 |
| CAT | 1 | 1.000 | 1.000 | 1.000 | 1.000 |
| JPM | 1 | 0.000 | 0.000 | 0.000 | 0.000 |
| LLY | 1 | 1.000 | 1.000 | 1.000 | 1.000 |
| NEE | 1 | 1.000 | 1.000 | 1.000 | 1.000 |

## Miss diagnosis (@10)

`format-miss` = a top-10 chunk under an expected Item path holds the snippet once case, whitespace and table syntax are ignored; `label-miss` = the snippet is in a top-10 chunk (same relaxed matching) but none under an expected Item path; `retrieval-miss` = no top-10 chunk holds the snippet.

| arm | hit | format-miss | label-miss | retrieval-miss |
|---|---:|---:|---:|---:|
| html | 24 | 3 | 8 | 5 |
| text | 38 | 0 | 0 | 2 |

## Discordant rows (@10: one arm hits, the other misses)

### p41 (GOOGL, factoid, flat) — text hits, html misses

- Question: Who independently evaluates Alphabet's cyber defenses?
- Expected: GOOGL / 2025 / Item 1C. Cybersecurity
- text rank: 1
- html miss kind: label-miss (snippet at rank 5)
- html top-3 paths: GOOGL / 2025 / Item 1C. Cybersecurity ‖ GOOGL / 2025 / Item 1A. Risk Factors ‖ GOOGL / 2025 / Item 1. Business / Overview

### p43 (AXON, factoid, markdown_h3, text_fallback) — text hits, html misses

- Question: How much credit could Axon draw at year-end 2025?
- Expected: AXON / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations | AXON / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk
- text rank: 4
- html miss kind: format-miss (snippet at rank 2)
- html top-3 paths: AXON / 2025 / Item 5. Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities ‖ AXON / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations ‖ AXON / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations

### p44 (COST, factoid, text_fallback) — text hits, html misses

- Question: Impact of one-percentage-point rate shift on Costco investments
- Expected: COST / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk
- text rank: 5
- html miss kind: retrieval-miss
- html top-3 paths: COST / 2025 ‖ COST / 2025 / Part I ‖ COST / 2025

### a24 (GOOGL, passage, markdown_h3) — text hits, html misses

- Question: When do Alphabet's revolving credit lines expire?
- Expected: GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
- text rank: 1
- html miss kind: format-miss (snippet at rank 8)
- html top-3 paths: GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations / Other Information: ‖ GOOGL / 2025 / Item 15. Exhibits, Financial Statement Schedules ‖ GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations

### p23 (DECK, factoid, text_fallback) — text hits, html misses

- Question: How did Deckers' total unit volume change in fiscal 2026?
- Expected: DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
- text rank: 1
- html miss kind: label-miss (snippet at rank 1)
- html top-3 paths: DECK / 2026 / Part II ‖ DECK / 2026 / Part II ‖ DECK / 2026 / Management contract or compensatory plan or arrangement.

### p32 (XOM, factoid, flat) — text hits, html misses

- Question: How large was ExxonMobil's active patent portfolio at the end of 2025?
- Expected: XOM / 2025 / Item 1. Business
- text rank: 1
- html miss kind: label-miss (snippet at rank 4)
- html top-3 paths: XOM / 2025 / Item 16. Form 10-K Summary ‖ XOM / 2025 / Item 16. Form 10-K Summary / FINANCIAL INFORMATION / Actual and Pro Forma Impact of Merger ‖ XOM / 2025 / Item 16. Form 10-K Summary / FINANCIAL INFORMATION

### a18 (DDOG, factoid, text_fallback) — text hits, html misses

- Question: How did Datadog’s trailing 12-month dollar-based net retention rate change from 2024 to 2025?
- Expected: DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
- text rank: 1
- html miss kind: format-miss (snippet at rank 1)
- html top-3 paths: DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations ‖ DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations / Comparison of the Years Ended December 31, 2025 and 2024 ‖ DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations / Expanding Within Our Existing Customer Base

### a20 (PODD, passage, markdown_h3) — text hits, html misses

- Question: What investments drove Insulet's higher capital spending in 2025?
- Expected: PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
- text rank: 9
- html miss kind: retrieval-miss
- html top-3 paths: PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations / Comparison of the Years Ended December 31, 2025 and December 31, 2024 ‖ PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations / Comparison of the Years Ended December 31, 2025 and December 31, 2024 / Costs and Expenses ‖ PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations / Comparison of the Years Ended December 31, 2025 and December 31, 2024

### a21 (COIN, passage, markdown_h3) — text hits, html misses

- Question: Does Coinbase actively trade the crypto it keeps on its balance sheet as an investment?
- Expected: COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations | COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
- text rank: 10
- html miss kind: retrieval-miss
- html top-3 paths: COIN / 2025 / Item 1. Business ‖ COIN / 2025 / Item 1. Business / Other policies and procedures ‖ COIN / 2025 / Item 1. Business / Custodial practices

### a23 (DECK, factoid, text_fallback) — text hits, html misses

- Question: How much did Deckers' net sales increase on a constant-currency basis in fiscal 2026?
- Expected: DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
- text rank: 1
- html miss kind: label-miss (snippet at rank 1)
- html top-3 paths: DECK / 2026 / Part II ‖ DECK / 2026 / Management contract or compensatory plan or arrangement. ‖ DECK / 2026 / Part II

### n04 (XOM, passage, markdown_h3) — text hits, html misses

- Question: How did lower crude prices affect ExxonMobil's 2025 Upstream earnings?
- Expected: XOM / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
- text rank: 2
- html miss kind: label-miss (snippet at rank 1)
- html top-3 paths: XOM / 2025 / Item 16. Form 10-K Summary / FINANCIAL INFORMATION / MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS ‖ XOM / 2025 / Item 16. Form 10-K Summary / FINANCIAL INFORMATION / MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS ‖ XOM / 2025 / Item 16. Form 10-K Summary / FINANCIAL INFORMATION / MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS

### n05 (COST, passage, text_fallback) — text hits, html misses

- Question: What drove Costco's comparable-sales growth in fiscal 2025?
- Expected: COST / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
- text rank: 1
- html miss kind: label-miss (snippet at rank 1)
- html top-3 paths: COST / 2025 ‖ COST / 2025 ‖ COST / 2025

### n08 (DECK, factoid, text_fallback) — text hits, html misses

- Question: Which brands does Deckers identify as its principal product brands?
- Expected: DECK / 2026 / Item 1. Business
- text rank: 2
- html miss kind: label-miss (snippet at rank 3)
- html top-3 paths: DECK / 2026 / Part I / Brands ‖ DECK / 2026 / Part II ‖ DECK / 2026 / Part II / Overview

### n09 (PODD, factoid, text_fallback) — text hits, html misses

- Question: Has Insulet experienced cybersecurity incidents that materially affected the company?
- Expected: PODD / 2025 / Item 1C. Cybersecurity
- text rank: 2
- html miss kind: label-miss (snippet at rank 1)
- html top-3 paths: PODD / 2025 / Part I ‖ PODD / 2025 / Item 1C. Cybersecurity ‖ PODD / 2025 / Part I

