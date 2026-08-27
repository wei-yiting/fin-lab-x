# T10 LIN — pipeline-independent filing traversal

## Scope and result

- Ticker / CIK: `LIN` / `0001707925`
- Fiscal year: `2025`
- Accession: `0001628280-26-011430`
- Active non-`multi_passage` candidates: `p16`, `p30`, `p50`, `a16`
- Excluded `multi_passage` candidates: none
- Full traversal coverage: `31/31` fixed neutral windows; `362,087/362,087` canonical characters
- Acceptable distinct occurrences: `p16 = 3`, `p30 = 1`, `p50 = 2`, corrected `a16 = 2`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

The two identical `p16` cost-component sentences and the two identical `p50` security-failure
clauses remain separate occurrences because they appear at distinct source locations. They are
OR-hit alternatives, not additional metric denominators. One `p50` occurrence crosses the neutral
boundary between `W0005` and `W0006`; the boundary is recorded as traversal provenance and is not
treated as an evidence boundary.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1707925/000162828026011430/0001628280-26-011430-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1707925/000162828026011430/0001628280-26-011430.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/1707925/000162828026011430/lin-20251231.htm)
- Filing date: `2026-02-25`
- Period of report: `2025-12-31`
- Primary document: `lin-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Complete-submission bytes / SHA-256: `19,138,106` / `5b2cf22620dc089b8b4bd909a5a8b469b851677c9996759e9093ad0e5ae82b92`
- Extracted primary-document bytes / SHA-256: `3,356,474` / `3bf3783e80c92a93280a1194233d733670f713b7c36f4268c3cedec23212431c`
- Canonical visible-text bytes / chars / lines: `363,578` / `362,087` / `6,145`
- Canonical visible-text SHA-256: `43aee847b2febb6d2270630d3dcd5fd9643b932e7197d02d2ddc0f32b2f5e376`

The accession-pinned complete submission identifies sequence 1 as the exact `TYPE=10-K`
document. A separate official SEC download of the primary HTML contained one additional trailing
newline; after removing it, the primary-document SHA-256 matched the document extracted from the
complete submission.

Canonicalization removed only non-visible HTML content and SEC transport markup, converted NBSP
to ordinary spaces, normalized horizontal and block-boundary whitespace, and retained visible
text in source order. It did not produce or use Item, heading, block, sentence,
candidate-evidence, or repository-pipeline hierarchy.

Offsets below are zero-based, end-exclusive intervals in this canonical text. Filing locations
are descriptive provenance assigned after sequential traversal; they did not determine traversal
order.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | `[0, 12000)` | `ae90760d1d9b785d31c76c725bfd6810896ecd8a90d4ae110f99b62c08784169` | inspected |
| W0002 | `[12000, 24000)` | `0a0042b233309392daeac1cbf920e9e8a3dbd37ccd870c9f3142c9768727b2bc` | inspected |
| W0003 | `[24000, 36000)` | `50e9374de3aa93a95253beaeb3897447c79bc1377a70fcf592febc9fb90f2d7c` | inspected |
| W0004 | `[36000, 48000)` | `c1511032834952c2e7285265cc210d410a2cd77eae593d33f165939b5464d8b9` | inspected |
| W0005 | `[48000, 60000)` | `9f64f050c98789d0af897f1f2443a792c4a562db0c75b267c35aa3bf3701c39c` | inspected |
| W0006 | `[60000, 72000)` | `42a2490574d73b7a77f4752e3e3acaed4a8c38d8a727a32358864aa3830954df` | inspected |
| W0007 | `[72000, 84000)` | `30cffdd3af850c00170b47ce7bcbacf2f0b788e9a369725760e707404044c6b6` | inspected |
| W0008 | `[84000, 96000)` | `4d3770fbdf548f11259a53dcdc71c742597d1508373e9b0d7c1c1abed59147b5` | inspected |
| W0009 | `[96000, 108000)` | `a3e450e41a2da0a74af8d573422912f594980726d51ba7e4f01066deb826008d` | inspected |
| W0010 | `[108000, 120000)` | `abd6b6a1894750a288cac8776b397e8e4a27a682cde5c975292997083f21d9b1` | inspected |
| W0011 | `[120000, 132000)` | `19efebb37055348e37caabbfec1deb80d2611e8a0a16a9a976e844e110e79833` | inspected |
| W0012 | `[132000, 144000)` | `787c54850edd602a363574fc57745c7727d8b0c4c009262be4a7e8ccd192eff1` | inspected |
| W0013 | `[144000, 156000)` | `c73ce0ba0dbe811634106d833a5a76ebe2101d00959a505c087702278642110c` | inspected |
| W0014 | `[156000, 168000)` | `b28b16085dd7ed484c1536dd97cc6f038ebd50044dc6ad20adb3be156e8afd43` | inspected |
| W0015 | `[168000, 180000)` | `8494c80a8386af475d4dfd82c233a77d6ce2ce9e3df2d429ddb7518c6947b771` | inspected |
| W0016 | `[180000, 192000)` | `30ca98865deda1cdc42471d708d25d7c9b83613592d2c118aa22495dc5ddfded` | inspected |
| W0017 | `[192000, 204000)` | `db0d008d0303c0c90797a958a691dd0815df835c972abbe298ce639ff1eb5637` | inspected |
| W0018 | `[204000, 216000)` | `1813b3f6cecc79b0b49b4edd9dc578a85c8b06e0210603d9ca2a220e506bea6a` | inspected |
| W0019 | `[216000, 228000)` | `b36abc99179dc2ae6ebedb34e9f720c3486a8a0c3dc5b304f653cf424d32b7cb` | inspected |
| W0020 | `[228000, 240000)` | `381fcd89333ab72a0c13f559e4454166f66aa0b4a12ff52db2c4f963c5e37610` | inspected |
| W0021 | `[240000, 252000)` | `ed49f21f8e78d77d8c66ea9eff298d1916893d2f802abd03400763901183abf3` | inspected |
| W0022 | `[252000, 264000)` | `313600317f45e8e9aafc2ff6bba9eafc84de59d76d400aa95dd56843bb5ff40c` | inspected |
| W0023 | `[264000, 276000)` | `f75d51e5200608e07b088b169e0baa959bf51154103f10bbc0d40ade4411352a` | inspected |
| W0024 | `[276000, 288000)` | `095d8f91eb818aba1993aabe75023e728a9a014446edf8b1da7bd47d410efca9` | inspected |
| W0025 | `[288000, 300000)` | `3e8e5dd996286e170e29c2bf4d18c2a8a2366a7072b7650780a3bcbfce96fbf0` | inspected |
| W0026 | `[300000, 312000)` | `3d03eaf3fd83137945ff098f28317b331daa736f6676bd1d872e3e5928dc5971` | inspected |
| W0027 | `[312000, 324000)` | `b726222b13c6b8fc68b369aeb5ec05a3017bda09c2d0fec288523cc23164b5f5` | inspected |
| W0028 | `[324000, 336000)` | `c290529a7f12dd037a3ebc76dec34f3e00743fe23788198413a660ec8ef28551` | inspected |
| W0029 | `[336000, 348000)` | `22b74c61d7e6fb1c0b5c3f3c9a91737a606797614c4699b7c58c9de45700bfff` | inspected |
| W0030 | `[348000, 360000)` | `ef30a9235e619b55553a6d76532ab4385172b56e32d06ab66dfa0c43b82ebe29` | inspected |
| W0031 | `[360000, 362087)` | `d88f3fe86f8da42a36397a6303843e58de3cccc4ab26dc42749ce1ed773c0435` | inspected |

The intervals are contiguous from `0` through `362087`, with zero gaps and zero overlaps.

Traversal checkpoints:

- `W0001–W0003`: cover, business overview, executive officers, and the beginning of Item 1A.
- `W0004–W0006`: remaining risk factors, Item 1C, properties, and the start of Part II. They
  contain the two `p50` occurrences.
- `W0007–W0009`: consolidated and segment MD&A. `W0009` contains both corrected `a16`
  occurrences: the APAC sales bridge table and the APAC sales narrative.
- `W0010–W0013`: liquidity, critical accounting estimates, non-GAAP disclosures, and Item 7A.
  `W0010` contains the sole `p30` occurrence and the first `p16` occurrence.
- `W0014–W0020`: auditor report, primary financial statements, and Notes 1–11. `W0014`
  contains the second `p16` occurrence.
- `W0021–W0027`: Notes 12–19. `W0027` contains the third `p16` occurrence.
- `W0028–W0031`: remaining revenue tables, Parts III–IV, exhibit index, and signatures; no
  additional acceptable occurrence.

After sequential traversal, full-text audits covered direct terms and plausible alternatives for
equipment-contract cost estimates, material/labor/overhead, inflation and scope, capital
expenditure allocation, cyber attacks and breaches, confidential and personal data, and APAC
sales drivers. No additional independently sufficient occurrence was found.

## Candidate findings

### `p16` — narrow to cost components; three acceptable occurrences

- Candidate ID: `p16`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Linde project exposure to materials, staffing, inflation, and scope changes`
- Round 1 comment: `我覺得整個 block 才能夠回答問題，光是粗體沒辦法回答`
- Round 1 snippet: `The key source of estimation uncertainty is the total estimated costs at completion including material, labor and overhead costs and the resultant state of completion of the contracts.`
- Proposed revised question: `Which cost components does Linde include when accounting for equipment contracts?`
- Proposed query type: `factoid`

The Round 1 question combines material and labor cost categories with technical complexity,
construction duration, inflation, and scope. Those facts span multiple sentences. The complete
uncertainty sentence alone exceeds 200 characters, so expanding the Round 1 snippet cannot satisfy
the unchanged contract. The proposed revision asks one thing and admits three source locations.

Occurrence 1:

- Filing location: Item 7, Critical Accounting Estimates, Revenue Recognition
- Window and canonical offsets: `W0010`, `[116578, 116762)`
- Canonical line: `1593`
- Character count: `184`
- Snippet SHA-256: `95987baf21275b9745e619e4f89dab4897a62aad7404faab8ad1b194fc9df371`

> The key source of estimation uncertainty is the total estimated costs at completion including material, labor and overhead costs and the resultant state of completion of the contracts.

Occurrence 2:

- Filing location: Item 8, auditor report, critical audit matter
- Window and canonical offsets: `W0014`, `[161275, 161427)`
- Canonical line: `2265`
- Character count: `152`
- Exact identical-text occurrences: `2`
- Snippet SHA-256: `1e5098a4a229bcfe58733f97d860cd7385e33cdedba1184e4aa91f1ff3d2b022`

> Costs incurred include material, labor, and overhead costs and represent work contributing and proportionate to the transfer of control to the customer.

Occurrence 3:

- Filing location: Item 8, Note 19, Revenue Recognition, Engineering
- Window and canonical offsets: `W0027`, `[320932, 321084)`
- Canonical line: `5221`
- Character count: `152`
- Exact identical-text occurrences: `2`
- Snippet SHA-256: `1e5098a4a229bcfe58733f97d860cd7385e33cdedba1184e4aa91f1ff3d2b022`

> Costs incurred include material, labor, and overhead costs and represent work contributing and proportionate to the transfer of control to the customer.

The technical-complexity, duration, inflation, and scope sentence is not an alternative for the
revised question and cannot support the original compound contract within 200 characters.

### `p30` — ask only geographic concentration; one acceptable occurrence

- Candidate ID: `p30`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `What drove Linde's 2025 investment spending and where was it concentrated?`
- Round 1 comment: `「驅動因素」跟「地區集中度」兩件事，問題應問單一一件事，以 evidence 來說應該問地區集中度`
- Round 1 snippet: page number `30` followed by the geographic-allocation sentence
- Proposed revised question: `Where were Linde's 2025 capital expenditures concentrated geographically?`
- Proposed query type: `factoid`

The revised question follows the Round 1 direction and removes both the separate spending-driver
intent and the page-number formatting artifact.

Occurrence 1:

- Filing location: Item 7, Liquidity, Capital Resources and Other Financial Data, Investing
- Window and canonical offsets: `W0010`, `[108671, 108816)`
- Canonical line: `1549`
- Character count: `145`
- Snippet SHA-256: `e93efa220d27ffb4d57f53e32fd2e7351132364a6f51a62dea060f30e636a45b`

> Approximately 60% of the capital expenditures were in the Americas segment with 21% in the APAC segment and the rest largely in the EMEA segment.

The adjacent backlog-growth sentence answers the removed driver question. Note 18's
`expenditures for long-lived assets` table uses a different measure and total, so it is not an
acceptable alternative.

### `p50` — replace unresolved historical reference; two acceptable occurrences

- Candidate ID: `p50`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Have cyber incidents materially affected Linde's performance so far?`
- Round 1 comment: `還要看更完整的整個 chunk, 現在看不出來這段是不是在想 cyber incidents`
- Round 1 snippet: `To date, such attempts have not had any significant impact on Linde's operations or financial results.`
- Proposed revised question: `What types of information could operational security failures or breaches expose at Linde?`
- Proposed query type: `factoid`

The Round 1 sentence appears in both Item 1A and Item 1C, but `such attempts` has no antecedent
inside the snippet. In both locations, including the cyber-attack antecedent and historical impact
requires more than 200 characters. The proposed revision stays within cybersecurity and can be
answered independently at both locations.

Occurrence 1:

- Filing location: Item 1A, information technology and cybersecurity risk
- Window and canonical offsets: `W0004`, `[44684, 44830)`
- Canonical line: `509`
- Character count: `146`
- Exact identical-text occurrences: `2`
- Snippet SHA-256: `fcd5f40c3f3fd575ca75ab0469b1f5389d9824df2bcfa18b537265f452eb3134`

> Operational failures and breaches of security from such attempts could lead to the loss or disclosure of confidential information or personal data

Occurrence 2:

- Filing location: Item 1C, Cybersecurity, Risk Management and Strategy
- Window and canonical offsets: `W0005–W0006`, `[59961, 60107)`
- Canonical line: `623`
- Character count: `146`
- Exact identical-text occurrences: `2`
- Snippet SHA-256: `fcd5f40c3f3fd575ca75ab0469b1f5389d9824df2bcfa18b537265f452eb3134`

> Operational failures and breaches of security from such attempts could lead to the loss or disclosure of confidential information or personal data

Occurrence 2 crosses a fixed neutral window boundary. It remains one continuous canonical source
occurrence; splitting or rejecting it because of the traversal boundary would reintroduce the
pipeline bias this task is designed to avoid.

### Correction — `a16` currency effect on APAC sales (supersedes the Round 2 proposal below)

- Candidate ID: `a16`
- Round 2 decision:
- Round 2 reviewer comment:
- Corrected question: `How did currency translation affect Linde's APAC sales in 2025?`
- Corrected query type: `passage`
- Corrected answer requirement: One independently sufficient source occurrence must state the
  direction or magnitude of currency translation's effect on APAC sales in 2025. Consolidated or
  other-segment sales effects, APAC operating-profit effects, exchange-rate tables without a sales
  effect, and generic foreign-exchange disclosures are partial or non-responsive.
- Result: `2` acceptable distinct source occurrences.

The pipeline-independent canonical text and its existing `31/31` neutral-window coverage ledger
were re-verified before the query-specific audit: `362,087` characters, SHA-256
`43aee847b2febb6d2270630d3dcd5fd9643b932e7197d02d2ddc0f32b2f5e376`, contiguous from offset
`0` through `362087` with no gaps or overlaps.

Occurrence 1 — APAC sales bridge table:

- Filing location: Item 7, Segment Discussion, APAC, Factors Contributing to Changes - Sales
- Window: `W0009`
- Answer-span offsets: `[100223, 100737)`
- Answer-span character count / cl100k tokens: `514` / `206`
- Answer-span SHA-256: `ce83ddf775c2f95b436c5afac4e8b81fbe6d28183d836fe76653bcf305fe1dc0`
- Answer-snippet offsets: `[100573, 100737)`
- Canonical line: `1295`
- Answer-snippet character count: `164`
- Exact snippet occurrences: `1`
- Answer-snippet SHA-256: `a0f35db28c63221e4a1fc4a3f44eaae4e1e4187c2f4cd9b9bd6dd4f21231bcce`

The answer span starts at the `APAC` heading and includes the sales-change table through the
`Currency (1)%` row, so the source occurrence identifies the segment, measure, comparison period,
and effect. The 50–200 character snippet below is the unique retrieval anchor inside that span:

> 2025 vs 2024
>
> \| \| % Change
>
> Factors Contributing to Changes - Sales
>
> \| \|
>
> Volume \| \| (1) \| %
>
> Price/Mix \| \| — \| %
>
> Cost pass-through \| \| — \| %
>
> Currency \| \| (1) \| %

Occurrence 2 — APAC sales narrative:

- Filing location: Item 7, Segment Discussion, APAC, Sales
- Window and canonical offsets: `W0009`, `[101099, 101237)`
- Canonical line: `1319`
- Answer-span and answer-snippet character count: `138`
- Exact snippet occurrences: `1`
- Answer-span and answer-snippet SHA-256: `c001c6e503e6190e1ce8e380d4db830e1f0d37b97198002910f050a210443216`

> Currency translation decreased sales by 1% primarily due to the weakening of the Australian dollar and Korean won against the U.S. dollar.

These are separate OR-hit alternatives: the first is the APAC table disclosure, and the second is
the narrative disclosure. The table's answer span, rather than the snippet alone, carries the
`APAC` structural context; it remains below the ratified 300-token span limit. The table separators
are literal output of the pipeline-independent visible-text traversal and must later be re-anchored
to the `sec_text_pipeline` filing-store text during dataset assembly.

The full-text audit covered all `33` literal `APAC` locations, `136` matches across the
`currency` / `currencies` / `foreign exchange` / `exchange rate` / `FX` family, and every
proximity zone joining APAC, sales or revenue, and a currency term. The following classes were
rejected:

- consolidated sales disclosures, which say currency translation was flat but do not give an
  APAC-specific currency effect;
- Americas (`-1%`), EMEA (`+3%`), Engineering (`+3%`), and Other (`+1%`) sales disclosures;
- the APAC operating-profit paragraph, because its measure is operating profit rather than sales;
- Australian-dollar and Korean-won exchange-rate tables, which do not state an APAC sales effect;
- APAC total-sales rows, AOCI, goodwill, derivatives, and generic exchange-rate risk disclosures.

No other source occurrence independently satisfies the corrected answer requirement. Human review
fields remain blank.

### `a16` — superseded Round 2 three-driver proposal; one acceptable occurrence

- Candidate ID: `a16`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Factors behind unchanged APAC revenue in 2025`
- Round 1 comment: `整個 block 有涵蓋 query 資訊，但粗體本身沒有`
- Round 1 snippet: `Currency translation decreased sales by 1% primarily due to the weakening of the Australian dollar and Korean won against the U.S. dollar.`
- Proposed revised question: `How did acquisitions, volumes, and currency translation affect Linde's APAC sales in 2025?`
- Proposed query type: `passage`

The Round 1 snippet contains only one component. The shortest canonical clause that includes the
three offsetting effects is 109 characters. Pricing and cost pass-through were flat and are not
part of the revised question.

Occurrence 1:

- Filing location: Item 7, Segment Discussion, APAC, Sales
- Window and canonical offsets: `W0009`, `[101032, 101141)`
- Canonical line: `1319`
- Character count: `109`
- Snippet SHA-256: `e5cfaa7abda6d5a4d82e42201fef383b72a4e83ff689f68d54b05dd49932ea45`

> Acquisitions increased sales by 2%. Volumes decreased sales by 1%. Currency translation decreased sales by 1%

The full paragraph exceeds 200 characters. Consolidated and other-segment sales bridges do not
answer the APAC-specific question.

## Open human decisions

1. `p16` moves from a broad project-risk question to the three cost components used in
   equipment-contract accounting. This follows the single-intent and 200-character contracts but
   deliberately drops inflation and scope.
2. `p50` cannot preserve the historical-impact question without an unresolved pronoun or an
   over-limit span. The proposal keeps cybersecurity but changes the requested fact to exposed
   information types.
3. `p30` follows the Round 1 preference for geographic concentration; the backlog-growth driver
   is deliberately excluded.
4. The earlier three-driver `a16` proposal is superseded by the single-intent currency-effect
   correction above. Its Round 2 text remains only as an audit trail.
5. The repeated `p16` and `p50` disclosures should remain separate OR-hit locations despite
   identical text. They do not change Recall, MRR, or MAP denominators.

No proposed occurrence violates the 50–200 character contract. All Round 2 review fields are
intentionally blank for human review.
