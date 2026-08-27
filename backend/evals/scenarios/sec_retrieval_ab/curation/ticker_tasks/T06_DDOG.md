# T06 DDOG — pipeline-independent filing traversal

## Scope and result

- Ticker: `DDOG`
- Fiscal year: `2025`
- Accession: `0001628280-26-008819`
- Active non-`multi_passage` candidates: `p18`, `p34`, `p45`, `a18`
- Excluded `multi_passage` candidates: `a02`, `p02`
- Full traversal coverage: `32/32` fixed neutral windows; `383,974/383,974` canonical characters
- Acceptable distinct occurrences: `p18 = 1`, `p34 = 1`, `p45 = 4`, `a18 = 1`
- Human review fields changed: no
- Final Round2 CSV/Markdown generated: no

The four `p45` occurrences are not deduplicated. Each independently states the issuance timing and principal amount, so retrieval at any one of those source locations must count as a hit even though the answer is redundant.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1561550/000162828026008819/0001628280-26-008819-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1561550/000162828026008819/0001628280-26-008819.txt)
- [Primary 10-K document](https://www.sec.gov/Archives/edgar/data/1561550/000162828026008819/ddog-20251231.htm)
- Filing date: `2026-02-18`
- Period of report: `2025-12-31`
- Primary document: `ddog-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Browser DOM SHA-256: `924759a567ee4120007fb10e956d3626edaf22868aa702230e278fafece70dd9`
- Rendered visible-text SHA-256: `cc5441a1a42cd4b71cb842b92d26e25913b1668a55cba043b99459561e42dbc7`
- Canonical visible-text SHA-256: `d77b78582e3aedf22c40638e9cb1e30281be3356e22e8b706c25ab96a51b4c02`
- Canonical character count: `383,974`
- Canonical line count: `2,422`

The SEC filing index identifies the primary document and complete-submission URL. The in-app browser blocked direct navigation to the complete-submission `.txt`, so traversal used the official accession-pinned primary 10-K rather than a third-party or repository filing copy.

Canonicalization read `document.body.innerText`, converted NBSP to ordinary spaces, normalized line endings, collapsed horizontal whitespace per line, trimmed lines, and collapsed three or more newlines to two. It did not produce or use an Item, heading, block, sentence, or repository-pipeline hierarchy.

Offsets below are zero-based and end-exclusive against exactly that canonical text. Filing locations are descriptive provenance added after occurrence discovery; they did not determine traversal order or coverage.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder. Window SHA-256 values make the reviewed boundaries reproducible.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W001 | [0, 12000) | `d58cd6b9046449abce21f08aa44d8e518de2c851b36249e9f1aafa47c2b0dff4` | inspected |
| W002 | [12000, 24000) | `4f4a0a6c33f8e5b799341a9d794860e96e2007b6d92472eaf095efe653b17809` | inspected |
| W003 | [24000, 36000) | `73d00fd46c07b9e7b6477ba8e660c59198e5bb31c71810e6333cdeb1fbce7fcc` | inspected |
| W004 | [36000, 48000) | `bed25fd6d51282f823c1b0f44269c33aa25b6f5d3284db918687f09d67c3221f` | inspected |
| W005 | [48000, 60000) | `04b8f16968eaf2d4b4e55658aa3004e3202921be1f4817de9cba4ff7629b7be2` | inspected |
| W006 | [60000, 72000) | `5448b9448b7dce4a4d6f200d006ea9a03879af74b581080e561b9adc1ce1cdfd` | inspected |
| W007 | [72000, 84000) | `e8fa5d9c1b48a38d77c1a4cc1968d53654fcd763497e7229a3eb467b39f327a3` | inspected |
| W008 | [84000, 96000) | `288ca4ed552ec1c5b576144c60d4bf85c453cfaaf390deb3f518fec62229d880` | inspected |
| W009 | [96000, 108000) | `fcdbb139bf0cf1a13c57e1ec6f4fe1629e8c88b7b18815639f6005f8e9483a93` | inspected |
| W010 | [108000, 120000) | `fe83e869fd526cd400d65137ab37981a4ba8b92d8d179a22116ee61230f49316` | inspected |
| W011 | [120000, 132000) | `265293b8e3f9819ef6647186009ec6b49f9210af27cd083e50bf0e7ac898c4a2` | inspected |
| W012 | [132000, 144000) | `a321fa1b102b71b0e1b1dbd52ea860da836893a166e2307e670266ca00f88186` | inspected |
| W013 | [144000, 156000) | `7b2c620e76021650149fd10e11df9a6541b5bdf743e7e444fd7bac2862870c92` | inspected |
| W014 | [156000, 168000) | `773d0a8c0b8657850e539c7c1beb1d6ab029df0e91b370de5cdb8f15ad063b0d` | inspected |
| W015 | [168000, 180000) | `36f8604a2aca4b3c34fad674a8ae966219d207d61cc73439ba2188faf8764c33` | inspected |
| W016 | [180000, 192000) | `81649c793c205306f8f8b960cccb7d7a5a54ad8831ed414aa7fda29e4e372bee` | inspected |
| W017 | [192000, 204000) | `7cf2755699b8d62c5edf59d763a4d0bd1cbcd25fc6ad178962296ff247c3e3ee` | inspected |
| W018 | [204000, 216000) | `909d89bf51b6ffdc6502d93ec489b81b3c83709f513509da0a309606fd6bb221` | inspected |
| W019 | [216000, 228000) | `d27ef5708fabe80f6b8e86012f18a770d13e8c89414dd3097cff167ff0e9c93e` | inspected |
| W020 | [228000, 240000) | `d92dc4d59afc47fa6638fd2ff8d6728b85170ef6832065fc955581d3f20bffd0` | inspected |
| W021 | [240000, 252000) | `f07c7fac789a13238804ade66f9214459e79c3718cdea2785733ecb24ca181b0` | inspected |
| W022 | [252000, 264000) | `76411e9cf276f08f9f7610df03deaa314f4774e1a4fed21f0a085a6214378538` | inspected |
| W023 | [264000, 276000) | `199a6d2a54102c570689f91d7b37aca26be65814788aafaf266d4be9a89638ad` | inspected |
| W024 | [276000, 288000) | `1aa152a964ff8f6919deeef8ce1925b400baf7dab3ae447ce806e194899eb8f5` | inspected |
| W025 | [288000, 300000) | `3b04e1c34015d3b172b41e12ced79fc43962888756f4518ba4ddebdb0dab184c` | inspected |
| W026 | [300000, 312000) | `bbdf1007f1f81c125824b9695299091a68eff62b5401be9dca2bf07efcc3ae3a` | inspected |
| W027 | [312000, 324000) | `bed9c522bdf14962f53b00e30881a55fc1fbfe3facf41ed50de189ae1bc96b74` | inspected |
| W028 | [324000, 336000) | `5ba5d306bcf318e98d85db261f5cbc090fa6a1fc30ebe8c13d1e1aa1b67f4137` | inspected |
| W029 | [336000, 348000) | `b7b70dcd16b1f9a1dcbdef12b24c9f6080a0e47edf220dd8b293e55a27bfba70` | inspected |
| W030 | [348000, 360000) | `d1d223e564b92f5494a2aedbdba45257dda5dde17dd9b95ba5d5bccf5c2a7a74` | inspected |
| W031 | [360000, 372000) | `7b0e07fc882d593f68508e6195e64801099aa481e08255c5bef0fff6e6d98c89` | inspected |
| W032 | [372000, 383974) | `289595daebc2be8420f8f044b085438d6e4a981a7c320214db1e37ab99faa255` | inspected |

Traversal checkpoints:

- `W001–W004`: cover, business overview and product descriptions. `W004` contains the sole database-bottleneck occurrence for `p34`.
- `W005–W018`: remaining business disclosures and risk factors. `W013` contains the sole export-authorization sales-impact occurrence for revised `p18`.
- `W019–W022`: Item 7 and Item 7A. `W019` contains the sole two-year retention-rate occurrence for revised `a18`; `W021` and `W022` contain the first two `p45` occurrences.
- `W023–W027`: financial statements and notes. `W024` and `W027` contain the remaining two `p45` occurrences.
- `W028–W032`: remaining notes, Parts III–IV, exhibits and signatures; no additional acceptable occurrence.

After sequential traversal, full-text cross-checks covered direct terms and plausible alternatives for export controls, trade restrictions, tariffs, database bottlenecks, resource constraints, net retention, 2029 Notes, principal amount and issuance timing. These checks found no additional independently sufficient occurrence.

## Candidate findings

### `p18` — rewrite question and evidence; one acceptable occurrence

- Candidate ID: `p18`
- Round2 decision:
- Round2 reviewer comment:
- Round1 decision: `?`
- Round1 question: `How can trade barriers affect Datadog’s growth and results?`
- Round1 comment: `粗體字拿的不精準，應該比 markdown 更下面的內容才是重點`
- Round1 snippet: `Unfavorable conditions in the economy both in the United States and abroad may negatively affect the growth of our business and our results of operations.`
- Proposed revised question: `How can export-authorization requirements affect Datadog’s sales opportunities?`
- Proposed query type: `passage`

The Round1 snippet states an effect but does not identify trade barriers. The Item 7 source sentence pair that joins both concepts exceeds 200 characters, so it cannot satisfy the unchanged global snippet limit. The proposed revision preserves the intent of testing a concrete trade-control business impact while making one source occurrence independently sufficient.

Occurrence 1:

- Filing location: Item 1A, export and import controls risk
- Window and canonical offsets: `W013`, `[147331, 147496)`
- Canonical line: `592`
- Character count: `165`
- Canonical snippet: `Obtaining the necessary export license or other authorization for a particular sale may be time-consuming and may result in the delay or loss of sales opportunities.`

Rejected near-matches include the original effect-only snippet, the over-200-character Item 7 cause-and-effect sentence pair, generic tariff/economic-uncertainty references, and export-control consequences that do not answer the revised sales-opportunity question.

### `p34` — narrow to database bottlenecks; one acceptable occurrence

- Candidate ID: `p34`
- Round2 decision:
- Round2 reviewer comment:
- Round1 decision: `?`
- Round1 question: `How does Datadog identify database bottlenecks and resource constraints?`
- Round1 comment: `題目應該只問單一事，database bottlenecks 或 resource constraints`
- Round1 snippet: `With Database Monitoring, they can quickly pinpoint costly and slow queries and drill into precise execution details to address bottlenecks.`
- Proposed revised question: `How does Datadog’s Database Monitoring identify database bottlenecks?`
- Proposed query type: `passage`

The Round1 question combines two different targets, but the snippet answers only the database-bottleneck half. The proposed revision asks one thing and retains the valid existing evidence.

Occurrence 1:

- Filing location: Item 1, Database Monitoring product description
- Window and canonical offsets: `W004`, `[39147, 39287)`
- Canonical line: `322`
- Character count: `140`
- Canonical snippet: `With Database Monitoring, they can quickly pinpoint costly and slow queries and drill into precise execution details to address bottlenecks.`

The adjacent resource-constraint sentence answers the removed half of the compound Round1 question and is not an alternative answer to the revised bottleneck-only question.

### `p45` — keep question; four acceptable occurrences

- Candidate ID: `p45`
- Round2 decision:
- Round2 reviewer comment:
- Round1 decision: `o`
- Round1 question: `Timing and size of Datadog's 2029 debt issuance`
- Round1 comment: none
- Proposed question change: none
- Proposed query type: `factoid`

Full traversal found four distinct source locations that independently state both timing and size. All four should be OR-hit alternatives; deduplicating them by answer text or answer content would incorrectly score retrieval at a valid location as a miss.

Occurrence 1:

- Filing location: Item 7, liquidity and capital resources
- Window and canonical offsets: `W021`, `[245545, 245735)`
- Canonical line: `1005`
- Character count: `190`
- Canonical snippet: `In December 2024, we issued $1.0 billion aggregate principal amount of the 2029 Notes in a private placement to qualified institutional buyers pursuant to Rule 144A under the Securities Act.`

Occurrence 2:

- Filing location: Item 7A, interest rate risk
- Window and canonical offsets: `W022`, `[259341, 259427)`
- Canonical line: `1062`
- Character count: `86`
- Canonical snippet: `In December 2024, we issued $1.0 billion aggregate principal amount of the 2029 Notes.`

Occurrence 3:

- Filing location: Item 8, Note 2
- Window and canonical offsets: `W024`, `[286123, 286224)`
- Canonical line: `1389`
- Character count: `101`
- Canonical snippet: `On December 12, 2024, the Company issued $1.0 billion aggregate principal amount of the “2029 Notes”.`

Occurrence 4:

- Filing location: Item 8, Note 8
- Window and canonical offsets: `W027`, `[323068, 323210)`
- Canonical line: `1629`
- Character count: `142`
- Canonical snippet: `On December 12, 2024, the Company issued $1.0 billion aggregate principal amount of 0.00% Convertible Senior Notes due 2029 (the “2029 Notes”)`

Occurrence 4 is the shortest self-contained clause containing the exact date, amount and 2029 Notes identity. The source sentence continues with private-placement details that are unnecessary to answer the question and would push the span above 200 characters. Other references to the 2029 Notes discuss maturity, carrying value, conversion terms, proceeds or interest but omit issuance timing or principal amount.

### `a18` — narrow to the numeric change; one acceptable occurrence

- Candidate ID: `a18`
- Round2 decision:
- Round2 reviewer comment:
- Round1 decision: `?`
- Round1 question: `Datadog net retention change and its cause in 2025`
- Round1 comment: `粗體字不夠長，沒涵蓋到 net retention change 的數據`
- Round1 snippet: `The increase in our trailing 12-month dollar-based net retention rate was attributable to increased usage growth from existing customers.`
- Proposed revised question: `How did Datadog’s trailing 12-month dollar-based net retention rate change from 2024 to 2025?`
- Proposed query type: `factoid`

The Round1 question combines the numeric change and its cause. No single 50–200 character occurrence states both. The proposed revision keeps the numeric change requested in the Round1 feedback, and the 190-character evidence contains both disclosed yearly rates.

Occurrence 1:

- Filing location: Item 7, expanding within the existing customer base
- Window and canonical offsets: `W019`, `[225945, 226135)`
- Canonical line: `812`
- Character count: `190`
- Canonical snippet: `As of December 31, 2025, our trailing 12-month dollar-based net retention rate was about 120%. As of December 31, 2024, our trailing 12-month dollar-based net retention rate was high-110%'s.`

The Round1 cause-only sentence omits both rate values. Combining the two numeric sentences with the cause sentence exceeds 200 characters, so the compound question cannot satisfy the unchanged snippet contract.

## Open human decisions

1. `p18` preserves the original trade-control intent but moves from Item 7's broad macroeconomic trade-policy discussion to Item 1A's concrete export-authorization consequence. Human review should decide whether that is sufficiently close to the desired intent.
2. `a18` becomes a `factoid` focused on the numeric change. The alternative would be a `passage` question asking only for the cause, but that would not address the Round1 request to include the change data.
3. `p45` should retain all four acceptable locations even though they communicate the same answer. This follows the agreed retrieval semantics and does not require changing Recall, MRR or MAP.

No proposed occurrence violates the 50–200 character snippet contract. All Round2 review fields above are intentionally blank for human review.
