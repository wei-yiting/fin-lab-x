# T14 PLD — pipeline-independent filing traversal

## Scope and result

- Ticker: `PLD`
- Fiscal year: `2025`
- Accession: `0001193125-26-051453`
- Active non-`multi_passage` candidates: `p48`, `p29`, `n03`
- Excluded `multi_passage` candidates: `p15`, `a15`
- Full traversal coverage: `58/58` fixed neutral windows; `459,299/459,299` canonical characters
- Acceptable distinct occurrences: `p48 = 2`, `p29 = 2`, `n03 = 3`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

The second `p48` occurrence is a table-shaped disclosure in Note 8. It is not deduplicated from
the prose occurrence in Item 5 because each source location independently reports the Series Q
per-share dividend. Likewise, the three `n03` occurrences separately state the 2025 lease
mark-to-market mechanism, quantify the rollover rent increase, and explicitly identify higher
rental rates on lease rollover as a key driver of increasing rental income.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1045609/000119312526051453/0001193125-26-051453-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1045609/000119312526051453/0001193125-26-051453.txt)
- [Primary 10-K document](https://www.sec.gov/Archives/edgar/data/1045609/000119312526051453/pld-20251231.htm)
- [SEC submissions metadata](https://data.sec.gov/submissions/CIK0001045609.json)
- Filing date: `2026-02-13`
- Period of report: `2025-12-31`
- Primary document: `pld-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Complete-submission bytes / SHA-256: `59,058,670` / `eeb2691ee1558e63e042810b99ceec57c8b2a995a2c1ae6bd9cf7853de2cce52`
- Official primary-document bytes / SHA-256: `11,507,278` / `bc5ac05737e3384253c1fdd6ff16feccd9769e75fc62b9b279d2e7f86fceaf5b`
- Extracted primary-document SHA-256 after trimming the SGML wrapper: `26897d8f0c5208ca642a0374401626719ec722749f14da0a042014111c5d9715`
- Canonical visible-text chars / bytes / SHA-256: `459,299` / `461,111` / `229ffceb3e59c0c6402b3a4767032aadc37fdedb8003076715dc6d87ba9aea03`

SEC submissions metadata identifies the accession as a Form 10-K for Prologis, Inc. and identifies
`pld-20251231.htm` as its primary document. The complete submission independently identifies the
same file as sequence 1 with exact `TYPE=10-K`. The extracted `<TEXT>` content matches the official
primary-document download byte-for-byte after trimming the single wrapper newline.

Canonicalization used `round2_traversal.visible_text`: it removed only non-visible transport
content, inserted separators at generic HTML block and table-cell boundaries, decoded entities,
and normalized horizontal and repeated blank-line whitespace. It did not create or use an Item,
heading, block, sentence, or repository-pipeline hierarchy. Offsets below are zero-based,
end-exclusive character intervals against exactly this canonical text. Filing locations were
assigned only after the sequential pass.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 8,000-character slice except the final remainder.

| Windows | Canonical range | Traversal checkpoint | Status |
|---|---:|---|---|
| W0001–W0005 | `[0, 40000)` | Cover, explanatory note, Item 1 company/segments/future growth; includes `n03-e02` | inspected |
| W0006–W0010 | `[40000, 80000)` | Customers, people, sustainability, governmental matters, Item 1A through acquisition risks | inspected |
| W0011–W0015 | `[80000, 120000)` | Remaining Item 1A, Item 1C, and beginning of Item 2 | inspected |
| W0016–W0020 | `[120000, 160000)` | Items 2–7; includes `p48-e01`, `n03-e01`, `p29-e01`, and `n03-e03` | inspected |
| W0021–W0025 | `[160000, 200000)` | Item 7 liquidity/critical policies/FFO and Item 7A | inspected |
| W0026–W0030 | `[200000, 240000)` | Items 9–16, audit reports, and Prologis, Inc. financial statements | inspected |
| W0031–W0035 | `[240000, 280000)` | Prologis, L.P. financial statements and Notes 1–2 | inspected |
| W0036–W0040 | `[280000, 320000)` | Notes 2–6, including revenue recognition and real estate/unconsolidated entities | inspected |
| W0041–W0045 | `[320000, 360000)` | Notes 7–12; includes `p48-e02` and `p29-e02` | inspected |
| W0046–W0050 | `[360000, 400000)` | Notes 13–18 and most of Schedule III | inspected |
| W0051–W0055 | `[400000, 440000)` | End of Schedule III and exhibit index | inspected |
| W0056–W0058 | `[440000, 459299)` | Remaining exhibits and signatures | inspected |

Coverage checks: W0001 starts at 0, W0058 ends at 459,299, every window starts at the prior
window's end, overlap is zero, and the sum of window lengths is 459,299.

After the neutral pass, full-text cross-checks covered direct terms and plausible alternatives for
Series Q/dividend/$4.27; PPP/promotes/third-party portion/employee allocation/vesting; and rental
revenue/rental income/rent change/rollovers/mark-to-market/same-store NOI. No additional distinct
source occurrence independently satisfied the applicable question contract.

## Candidate findings

### `p48` — keep question; add one acceptable table occurrence

- Candidate ID: `p48`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `o`
- Round 1 reviewer comment: `屬於 long-tail 的題目`
- Round 1 question: `Prologis Series Q per-share dividend amount for 2025`
- Proposed question change: none
- Proposed query type: `factoid`
- Acceptable occurrence count: `2`

#### `p48-e01`

- Filing location: Item 5, Preferred Stock Dividends
- Window / canonical line / offsets: `W0016` / `2845` / `[127107, 127183)`
- Character count / exact count: `76` / `1`
- Snippet SHA-256: `af473db5f0e3368f0b925ccf611a0a33527627ef4642cfb58c7ee6a4f114ffd1`

> Dividends payable per share were $4.27 for the year ended December 31, 2025.

This is the approved Round 1 prose occurrence.

#### `p48-e02`

- Filing location: Item 8, Note 8, Stockholders' Equity of Prologis, Inc. → Dividends
- Window / canonical line / offsets: `W0043` / `12473` / `[336753, 336938)`
- Character count / exact count: `185` / `1`
- Snippet SHA-256: `e9a25f800bf92cdf2ba2a857641d80a1895e88b8a372ac981bca01dab5607d92`

```text
Preferred Stock – Series Q:

Ordinary income

$

3.85

$

3.90

$

4.05

Qualified dividend

0.02

0.02

0.00

Capital gains

0.40

0.35

0.22

Total dividend

$

4.27

$

4.27

$

4.27
```

This table occurrence independently identifies the Series Q total dividend as $4.27 for each
displayed year, including 2025. The newlines are canonical visible-table separators, not a
repository pipeline block label or generated formatting marker.

Rejected near-matches include the 8.54% annual dividend-rate disclosures, which state a rate rather
than the requested per-share dollar amount, and balance-sheet references that state liquidation
preference but not the 2025 dividend.

### `p29` — narrow to employee allocation; two acceptable occurrences

- Candidate ID: `p29`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 reviewer comment: `題目應該只問單一事，Employee allocation 或 timing for venture incentive fees`
- Round 1 question: `Employee allocation and expense timing for venture incentive fees`
- Proposed revised question: `What share of third-party promote earnings can Prologis allocate to employees under its Promote Plan?`
- Proposed query type: `factoid` (changed from `passage`)
- Proposed answer requirement: one occurrence must state the maximum third-party promote share allocated to employees
- Acceptable occurrence count: `2`

The revision follows the Round 1 instruction by retaining only employee allocation. It is the
minimal change because the approved evidence sentence already answers that half precisely; expense
timing is removed rather than combined with a second requirement.

#### `p29-e01`

- Filing location: Item 7, Results of Operations → Strategic Capital Segment
- Window / canonical line / offsets: `W0018` / `3605` / `[142515, 142671)`
- Character count / exact count: `156` / `1`
- Snippet SHA-256: `5517cd45d81b45d1ec8e87fce90cc4544282a8b8c0dcf86d47b86055ba7ca953`

> The Prologis Promote Plan ("PPP") awards up to 25% of the third-party portion of the promotes earned by us from the co-investment ventures to our employees.

#### `p29-e02`

- Filing location: Item 8, Note 11, Long-Term Compensation → Prologis Promote Plan
- Window / canonical line / offsets: `W0044` / `12819` / `[348730, 348902)`
- Character count / exact count: `172` / `1`
- Snippet SHA-256: `31d197c2288792acbfab3b674b30ddd77de3abf6be01cf936fcae6c6e9c5b38b`

> Under the PPP, for promotes earned after January 2024, we award up to 25% of the third-party portion of promotes earned by Prologis from co-investment ventures to employees

This is the shortest complete causal clause under 200 characters at the Note 11 occurrence. The
source sentence continues with “through a compensation pool,” which does not change the requested
maximum allocation. The terminal clause is omitted at a grammatical boundary, not by truncating an
answer-bearing fact.

Rejected near-matches include expense-policy references that mention PPP cost without the employee
share, the historical pre-January-2024 40% allocation (outside the current-plan answer), and exhibit
titles that name the plan without its allocation terms.

### `n03` — keep question; three acceptable driver occurrences

- Candidate ID: `n03`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1: not applicable (new intent-first candidate)
- Question: `What drove the change in Prologis's rental revenue in 2025?`
- Query type: `passage`
- Answer requirement: one independently sufficient occurrence must explain a principal company-disclosed driver of the 2025 rental-revenue change; an isolated amount or percentage is partial
- Acceptable occurrence count: `3`

#### `n03-e01`

- Filing location: Item 7, Management's Overview → Summary of 2025
- Window / canonical line / offsets: `W0017` / `2885` / `[130013, 130176)`
- Character count / exact count: `163` / `1`
- Snippet SHA-256: `9d6a6d348ef2d187f6a7a232c193aa4b2a7f7866774f9c5a8c351193bf776d75`

> Our results during 2025 continued to reflect the favorable mark-to-market of our existing leases, reflecting increases in market rents over the past several years.

This occurrence attributes 2025 results to embedded lease mark-to-market created by prior market-rent increases.

#### `n03-e02`

- Filing location: Item 1, Future Growth → Rent Growth
- Window / canonical line / offsets: `W0004` / `571` / `[30022, 30179)`
- Character count / exact count: `157` / `1`
- Snippet SHA-256: `0ee6245382d346288db7dc47d5e80bbee76a41f5222ca09c77fc1544e0d7e655`

> For lease rollovers during 2025, the increases to market on our share of the O&M portfolio resulted in increases of approximately 50% on net effective rents.

This occurrence identifies the 2025 rollover mechanism and quantifies the increase in effective rents.

#### `n03-e03`

- Filing location: Item 7, Results of Operations → Real Estate Segment
- Window / canonical line / offsets: `W0018` / `3213` / `[136602, 136756)`
- Character count / exact count: `154` / `1`
- Snippet SHA-256: `18923e83a1b343879d1d6f07ba81cd72eee36b1e3b74cd783ca69dd0ac239c96`

> Significant rent change due to higher rental rates on the rollover of leases during both periods continues to be a key driver of increasing rental income.

This is the most direct occurrence: it explicitly labels higher rollover rental rates as a key
driver of increasing rental income.

Rejected near-matches include rental-revenue and quarterly tables that state only amounts;
accounting-policy passages that explain recognition rather than the 2025 change; future minimum
lease payments; generic acquisition/development/disposition language about NOI; and the general
forward-looking sentence that lease rollovers will be the primary driver of revenue growth without
specifically describing the observed 2025 change.

## Round 2 assembly recommendation

This ticker result proposes questions and evidence only. It does not assign a human
`round2_decision` or reviewer comment. During final Round 2 assembly:

1. Preserve the Round 1 `p48` and `p29` question/evidence/decision/comment fields alongside the proposals.
2. Keep the new review fields blank.
3. Represent each candidate's listed occurrences as OR-hit alternatives; do not collapse distinct source locations because their answer content overlaps.
4. Keep `p15` and `a15` in the separate `multi_passage` review pool rather than this active non-`multi_passage` set.
