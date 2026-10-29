# Round 3 filing-store reconciliation

Completed on 2026-08-27 against `data/sec_text/<ticker>/10-K/<FY>.json`.
This artifact records the source corrections applied to
`round2_ticker_results/*.json` before final dataset assembly. The filing store is
the only validation target in this task. Cross-arm header-path behavior is owned
by a separate issue and was not inferred here.

For every surviving changed occurrence, `answer_span` and `answer_snippet` are
exact filing-store substrings. The added `store_anchor` identifies the actual
store item, unit, block and character offsets. The original canonical traversal
offsets remain only as Round 2 provenance and are not filing-store offsets.

## T1 results

### Re-anchored to exact filing-store whitespace

| Candidate | Ticker | Occurrence | Store item | Correction |
|---|---|---|---|---|
| p43 | AXON | occ0 | Item 7 | Re-extracted canonical whitespace as exact store text. |
| p43 | AXON | occ1 | Item 7A | Re-extracted canonical whitespace as exact store text. |
| n07 | AXON | occ1 | Item 1 | Re-extracted canonical whitespace as exact store text. |
| n06 | COIN | occ0 | Item 7 | Preserved the non-breaking space after `$384.4`. |
| n06 | COIN | occ2 | Item 7 | Preserved the non-breaking space after `$152.0`. |
| p45 | DDOG | occ1 | Item 7A | Preserved the non-breaking space after `In`. |
| a18 | DDOG | occ0 | Item 7 | Preserved non-breaking spaces in both dates. |
| p23 | DECK | occ0 | Item 7 | Preserved the space before the paragraph break. |
| n08 | DECK | occ0 | Item 1 | Preserved the space before the paragraph break. |
| a24 | GOOGL | occ0 | Item 7 | Preserved the non-breaking space in the date. |
| n02 | LLY | occ1 | Item 7 | Preserved the space before the paragraph break; the exact snippet is 200 characters. |
| p28 | NEE | occ0 | Item 7 | Preserved the non-breaking space in the date. |
| n01 | NEE | occ1 | Item 7 | Preserved the non-breaking space after `$5.5`; the snippet itself was already exact. |
| p32 | XOM | occ0 | Item 1 | Preserved the non-breaking space between `8` and `thousand`. |

The audit found five pure-whitespace mismatches beyond the original T1 table:
AXON `p43/occ0`, `p43/occ1`, `n07/occ1`, COIN `n06/occ0`, and NEE
`n01/occ1`.

### Store-location reconciliation

| Candidate | Ticker | Original occurrence | Result |
|---|---|---|---|
| n08 | DECK | occ1, canonical Item 7 | Collapsed into occ0 because it maps to the same Item 1 store location; no Item 7 store copy exists. |
| p50 | LIN | occ1, canonical Item 1C | Collapsed into occ0 because it maps to the same Item 1A flat-item location. |
| n01 | NEE | two Item 7 answer texts | Each text also occurs under the store's Item 6 label; both additional reachable copies were enumerated during T6. |
| n04 | XOM | occ0, canonical Item 7 | Kept and relabelled to the actual Item 16 / `Upstream Financial Results` store block. |

LIN `a16` was deferred to T3 rather than treated as a T1 whitespace correction
because its canonical table linearization required a structural filing-store
re-extraction. That rebuild is recorded below.

## T3 results

### JPM `n10` table rebuilt from filing-store text

The 183-character canonical HTML table linearization was replaced by a
151-character exact filing-store substring. The span and snippet are identical and
retain the `CIB trading VaR by risk type` heading plus all four row labels: fixed
income, foreign exchange, equities, and commodities and other.

The filing store contains two reachable non-Item-8 copies of this same source table:

| Occurrence | Store location | Span offsets |
|---|---|---|
| `JPM-2025-504303` | Item 1 / block 1 / `Segment & Corporate Results – Managed Basis` | `239167–239318` |
| `JPM-2025-store-item15-239167` | Item 15 / block 2 / `Segment & Corporate Results – Managed Basis` | `239167–239318` |

Both copies are enumerated as OR alternatives so the corpus-level uniqueness rule
does not leave an unlisted reachable copy. The official source context remains Item
7A; the filing-store Item 1/15 labels are recorded as observed, while cross-arm
header-path reconciliation remains owned by its separate issue.

### LIN `a16` table rebuilt and narrative verified against filing-store text

Both accepted alternatives resolve to Item 7, structured block 27, whose filing-store
block heading is `APAC`:

| Occurrence | Evidence | Store offsets | Snippet chars | Span tokens |
|---|---|---|---:|---:|
| `LIN-2025-100223` | APAC sales bridge table through `Currency(1)%` | span `0–304`; snippet `178–304` | 126 | 110 |
| `LIN-2025-101099` | APAC sales narrative stating the 1% decrease and currencies | span/snippet `653–791` | 138 | 27 |

The table's canonical pipe-table text was replaced by exact filing-store text. Its
`APAC` block heading plus the exact table span identify the segment, sales measure,
2025-versus-2024 comparison and `Currency(1)%` effect without relying on the narrative
copy. The narrative was already store-exact and independently states that currency
translation decreased sales by 1%, primarily because the Australian dollar and
Korean won weakened against the U.S. dollar. Each snippet occurs exactly once across
the 16-filing store corpus.

## T2 results

The complete audit found 14 Round 2 occurrences whose canonical source hint was
Item 8, including five beyond the original known-case list (`p43`, `a21`, `p24`,
`p29`, and `p20`). Eleven were dropped and three were retained under actual non-Item-8 store
labels. Every affected candidate retains at least one acceptable occurrence.

### Dropped Item 8 occurrences

| Candidate | Ticker | Occurrence | Non-Item-8 search result |
|---|---|---|---|
| p43 | AXON | occ2 / Note 9 | No same-text non-Item-8 occurrence; distinct Item 7 and Item 7A answers remain. |
| a25 | CAT | occ1 / Note 25 | Same text exists under Item 7 and is already represented by occ0; dropped as a duplicate. |
| a21 | COIN | occ2 / Note 2 | No non-Item-8 store occurrence. |
| p45 | DDOG | occ2 / Note 2 | No non-Item-8 store occurrence. |
| p45 | DDOG | occ3 / Note 8 | No non-Item-8 store occurrence. |
| n08 | DECK | occ2 / Note 1 | No matching store occurrence. |
| a24 | GOOGL | occ1 / Note 6 | No non-Item-8 store occurrence. |
| p24 | GOOGL | occ1 / Note 6 | Same text exists under Item 7 and is already represented by occ0; dropped as a duplicate. |
| p16 | LIN | occ1 / auditor critical audit matter | No non-Item-8 store occurrence. |
| p16 | LIN | occ2 / Note 19 | No non-Item-8 store occurrence. |
| p20 | PODD | occ1 / Note 16 | No non-Item-8 store occurrence. |

### Retained label escapes

| Candidate | Ticker | Original hint | Actual store location | Result |
|---|---|---|---|---|
| p17 | NVDA | Item 8 / Note 16 | Item 15 / `Note 16 - Segment Information` | Retained as the third distinct OR alternative; Item 1A and Item 7 copies were already present. |
| p48 | PLD | Item 8 / Note 8 | Item 16 / `Dividends` | Retained. The 247-token store-exact span includes the table's year headings and Series Q rows; its conforming exact anchor is the 95-character `Total dividend` row. |
| p29 | PLD | Item 8 / Note 11 | Item 16 / `Prologis Promote Plan (“PPP”)` | Retained as a distinct OR alternative. |

## Assembly contract

- Use the surviving `acceptable_occurrences` arrays as the current OR-set source.
- Use `item_hint`, `answer_span`, `answer_snippet`, and `store_anchor` after this
  reconciliation; do not reconstruct strings from Round 2 canonical offsets.
- Carry each candidate's `round3_reconciliation` into final provenance.
- Do not restore dropped occurrences or create duplicate OR alternatives for two
  canonical occurrences that resolve to one store location.
