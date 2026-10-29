# T07 DECK — pipeline-independent filing traversal

## Scope and result

- Ticker / CIK: `DECK` / `0000910521`
- Fiscal year: `2026`
- Accession: `0001628280-26-037664`
- Active non-`multi_passage` candidates: `p23`, `p40`, `a23`, `n08`
- Excluded `multi_passage` candidates: `p08`, `a08`
- Full traversal coverage: `30/30` fixed neutral windows; `357,075/357,075` canonical characters
- Acceptable distinct occurrences: `p23 = 1`, `p40 = 1`, `a23 = 1`, `n08 = 3`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

The two identical `n08` sentences at Item 1 and Item 7 remain separate occurrences because they
come from distinct source locations. They are OR-hit alternatives, not additional metric
denominators. The Item 8 Note 1 wording is a third independently sufficient occurrence.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/910521/000162828026037664/0001628280-26-037664-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/910521/000162828026037664/0001628280-26-037664.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/910521/000162828026037664/deck-20260331.htm)
- Filing date: `2026-05-22`
- Period of report: `2026-03-31`
- Primary document: `deck-20260331.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Complete-submission bytes / SHA-256: `23,018,408` / `41656b41034d017147490b1d660bf8a516ee2a1153fca240bb3db03ded0d0a2c`
- Extracted primary-document bytes / SHA-256: `5,260,148` / `f841608192e402af243e314d73468bf977cd8727929608ba5d0f049f32eb8572`
- Canonical visible-text bytes / chars / lines: `358,756` / `357,075` / `14,671`
- Canonical visible-text SHA-256: `4210750bcceb9cc0ae20a1faf5bbfcb7fb6fb3e43632169843a69b6bac999fef`

The accession-pinned complete submission identifies sequence 1 as the exact `TYPE=10-K`
document. A separate SEC download of the primary HTML matches the extracted document after
removing the download's single trailing newline.

Canonicalization removed only the SEC XBRL transport wrapper, non-visible HTML content, and
transport whitespace. Visible text was retained in source order with neutral separators at HTML
block boundaries. It did not produce or use Item, heading, block, sentence, candidate-evidence,
or repository-pipeline hierarchy.

Offsets below are zero-based, end-exclusive intervals in this canonical text. Filing locations
are descriptive provenance assigned after the sequential traversal; they did not determine the
traversal order.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | `[0, 12000)` | `53a50c8c0de3893abc79bb88f064df215f763f45fec49d227793c74e4692413b` | inspected |
| W0002 | `[12000, 24000)` | `c84c2b6552c20eeb3cf22759e37a47bbe6afff4495a8c79d9e493907c465b716` | inspected |
| W0003 | `[24000, 36000)` | `f302fd066ff51b06dea7c3c64e1e96a699fad71b46017790ba6fe01e98d86219` | inspected |
| W0004 | `[36000, 48000)` | `0507269aa312c33c40539ee0e2802594b06de56151c0983cfc87f0e32a15ad97` | inspected |
| W0005 | `[48000, 60000)` | `db56920ebb9f8f1794cc2ec0b6c79cd9a3c6395661aea5ad8ab82ec8f67169e7` | inspected |
| W0006 | `[60000, 72000)` | `7e01a179dee2e147045a2c51505b5c24d431519b95455c27c3657f66ea5639f6` | inspected |
| W0007 | `[72000, 84000)` | `cace09e3e45ebdce5a647c1599ec9571971977041556797b30aac4211349de41` | inspected |
| W0008 | `[84000, 96000)` | `e1a2e04e460a754c79d4d865a79853544a20c53f25a97ef5a589038e8f4d80cf` | inspected |
| W0009 | `[96000, 108000)` | `63c3c3ffa6061456c1fcafcb845aedd3cb2b48a2ecf29720a558ffb3b82b63a9` | inspected |
| W0010 | `[108000, 120000)` | `2add6e65b8dc2e259fd90ad800782b92a2b01d95946fc77651bbf612b286063a` | inspected |
| W0011 | `[120000, 132000)` | `2bff8e53150ecf6026027e23caff38102a9f68b5177a9cc66155242b2d96c1d4` | inspected |
| W0012 | `[132000, 144000)` | `bb182968c541e7adc063709619c06bf8881e4dd5cd1445c1a0838815c0f21195` | inspected |
| W0013 | `[144000, 156000)` | `9d9780a18ccac10633302bba689f2df83f82b68a7c6d918f0bca6dab5dafb574` | inspected |
| W0014 | `[156000, 168000)` | `3b16a097a9143df4a7d774f267df385856fca101ad84853ed9747f9098cf7ccb` | inspected |
| W0015 | `[168000, 180000)` | `4fd8fadc250568a83f8e03c62dbd1d27be680714491476b01bad307332a404e6` | inspected |
| W0016 | `[180000, 192000)` | `aa00590a2a233a879d2683f7692996e5e497142d00d803acd05d599924e84559` | inspected |
| W0017 | `[192000, 204000)` | `7ba25297c42020523037df7116788deb6a8c4ef0d2da69916e5ff75612fcbc6d` | inspected |
| W0018 | `[204000, 216000)` | `7d33e041f597a6beba393d6521bc62dd22ef94b328317b69dd232add5700dd5a` | inspected |
| W0019 | `[216000, 228000)` | `ab418603a9b4cf2fe0c5b8479304011b26276e91378725a72ad06c6e59bd2c38` | inspected |
| W0020 | `[228000, 240000)` | `6b55ecd1784dc0ec82c9fe0d469e98f471ac93dc3fbb61e364a9413ccedb16b5` | inspected |
| W0021 | `[240000, 252000)` | `91a9139ce98dc896cb8d36c5b0dd5aa253152d6fc0a157c8feffa3f60027136b` | inspected |
| W0022 | `[252000, 264000)` | `d507f5b60c6d9b7136f3e30e96ec086af854b2a1af7d7895b9b73c78cee8ba79` | inspected |
| W0023 | `[264000, 276000)` | `48fce8606457f901a6a8a96b3d3a057a9153257c26214761cd2c8e3ade09188a` | inspected |
| W0024 | `[276000, 288000)` | `d4c03644c8c9076547d1878be0f17f3d1fa40e0f4417c34c6ff5e68e955c6937` | inspected |
| W0025 | `[288000, 300000)` | `def99153824cdedc0ea958a285ca3df32776d68ad8a940cdd97950ab1d0f6752` | inspected |
| W0026 | `[300000, 312000)` | `305ec4fd568023b1510ed4f5f6801cb69494b485b96277ee718d83cc9a745646` | inspected |
| W0027 | `[312000, 324000)` | `dcc622869ed1ebd0e191a5a01b24ed5f5d0745c9f99a3218a9f3e0bd8d37b6d6` | inspected |
| W0028 | `[324000, 336000)` | `8e00e4630cda91a82d9b41a21abce52ce95e756f2e322e7692eac27ca7d3cabd` | inspected |
| W0029 | `[336000, 348000)` | `1a184dcd715e8a87003362c0586fa7b4f36f07f948090a20d2fa17d642bb0758` | inspected |
| W0030 | `[348000, 357075)` | `ae1154cd51542d46e546d8a9c9dc7963ee030c230d48f6ea9c45446d7c103d2f` | inspected |

The intervals are contiguous from `0` through `357075`, with zero gaps and zero overlaps.

Traversal checkpoints:

- `W0001–W0004`: cover, business overview, all principal-brand descriptions, distribution,
  manufacturing, ESG, and human capital. `W0002` contains the first `n08` occurrence.
- `W0005–W0010`: Item 1A risk factors. No active-question occurrence appears in this range.
- `W0011`: Item 1C through properties and legal proceedings. It contains the sole `p40`
  occurrence.
- `W0012–W0017`: equity disclosures, Item 7, and Item 7A. `W0012` contains the second `n08`
  occurrence; `W0014` contains the sole `p23` and `a23` occurrences.
- `W0018–W0030`: remaining Parts II–IV, financial statements, notes, and schedule. `W0020`
  contains the third `n08` occurrence in Note 1. No additional occurrence answers the other
  active questions.

After sequential traversal, full-text audits covered direct terms and plausible alternatives for
unit volume, constant-currency and comparable DTC sales, IRP/privacy-policy review, proprietary
brands, reportable segments, and phased-out or former brands. They found no additional
independently sufficient occurrence.

## Candidate findings

### `p23` — narrow to unit volume; one acceptable occurrence

- Candidate ID: `p23`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Deckers fiscal 2026 supplemental sales growth and unit-volume metrics`
- Round 1 comment: `query 同時問「sales growth」跟「unit-volume metrics」兩件事，但 snippet 只覆蓋「unit volume」這句，前兩個成長率 bullet 沒被凸顯`
- Proposed revised question: `How did Deckers' total unit volume change in fiscal 2026?`
- Proposed query type: `factoid`

The Round 1 query combined three separate measures. The proposed revision retains the metric its
original snippet actually supported and removes the formatting bullet.

Occurrence 1:

- Filing location: Item 7, Results of Operations, Supplemental Disclosure
- Window and canonical offsets: `W0014`, `[160539, 160661)`
- Canonical line: `4553`
- Character count: `122`
- Snippet SHA-256: `05a1a3074bd5c0a2b1b48352d5dc0373bb0fff730b5776c32d4e64cb38747d80`

> We experienced an increase of 6.2% in the total volume of units sold to 78,700 from 74,100,
>
> compared to the prior period.

The adjacent 9.0% constant-currency and 4.6% comparable DTC growth metrics answer different
single-intent questions. The following sentence defines included unit categories but does not add
another occurrence of the change.

### `p40` — ask which policies, not documents plus why; one acceptable occurrence

- Candidate ID: `p40`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Which security documents undergo periodic refresh, and why?`
- Round 1 comment: `從粗體答案中不確定是不是在講security documents, 而且題目出現了 and why, 需要多個 evidence 才能回答`
- Proposed revised question: `Which cybersecurity policies and procedures does Deckers periodically review and update?`
- Proposed query type: `factoid`

The revised wording uses the filing's own `policies/procedures` terminology and removes the
separate why-clause. It also clears the pipeline-specific bullet artifact.

Occurrence 1:

- Filing location: Item 1C, Cybersecurity Risk Management and Strategy, key components
- Window and canonical offsets: `W0011`, `[124910, 125010)`
- Canonical line: `2855`
- Character count: `100`
- Snippet SHA-256: `4b2f03ef8ca6d8839e85cdedf238437963f94cd030d95c4aa013b409833239f6`

> periodically reviewing and updating our IRP, privacy policy, and other relevant policies/procedures.

The next sentence explains the removed why-clause. Earlier IRP content describes incident-response
stages but neither periodic review nor the privacy policy; Item 1A contains only generic risks.

### `a23` — narrow to constant-currency net sales; one acceptable occurrence

- Candidate ID: `a23`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Deckers currency-neutral revenue and comparable direct-sales growth rates`
- Round 1 comment: `應該要只有單一問題，currency-neutral revenue 或 comparable direct-sales growth rates`
- Proposed revised question: `How much did Deckers' net sales increase on a constant-currency basis in fiscal 2026?`
- Proposed query type: `factoid`

This selects one of the two Round 1 metrics and keeps it distinct from revised `p23`.

Occurrence 1:

- Filing location: Item 7, Results of Operations, Supplemental Disclosure
- Window and canonical offsets: `W0014`, `[160324, 160412)`
- Canonical line: `4547`
- Character count: `88`
- Snippet SHA-256: `3f04744ebdb8d3a1a1b4cde2c4a8b342d9b92693c0bfcd19825e6a199bb5f3eb`

> On a constant currency basis, net sales increased by 9.0%, compared to the prior period.

The 4.6% comparable DTC metric answers the removed half of the compound question. The 9.8%
US-GAAP growth rate is a different measure, and methodology-only disclosures do not provide the
fiscal 2026 result.

### `n08` — keep question; three acceptable occurrences

- Candidate ID: `n08`
- Round 2 decision:
- Round 2 reviewer comment:
- Candidate type: new intent-first question
- Question: `Which brands does Deckers identify as its principal product brands?`
- Proposed question change: none
- Proposed query type: `factoid`

Full traversal found three distinct locations that each identify HOKA, UGG, and Teva as the three
proprietary or primarily marketed brands.

Occurrence 1:

- Filing location: Item 1, Business, General
- Window and canonical offsets: `W0002`, `[14599, 14685)`
- Canonical line: `537`
- Character count: `86`
- Exact identical-text occurrences: `2`

> We market our products primarily
>
> under three proprietary brands: HOKA, UGG, and Teva.

Occurrence 2:

- Filing location: Item 7, Management's Discussion and Analysis, Overview
- Window and canonical offsets: `W0012`, `[139733, 139819)`
- Canonical line: `3431`
- Character count: `86`
- Exact identical-text occurrences: `2`

> We market our products primarily
>
> under three proprietary brands: HOKA, UGG, and Teva.

Occurrence 3:

- Filing location: Item 8, Note 1, General, The Company
- Window and canonical offsets: `W0020`, `[238856, 238958)`
- Canonical line: `8567`
- Character count: `102`

> The Company’s three proprietary brands include
>
> the HOKA® (HOKA), UGG® (UGG), and Teva® (Teva) brands.

The filing's initial trademark inventory also names Koolaburra, AHNU, UGGpure, and UGGplush and
does not identify the principal brands. Individual brand descriptions are partial. Reportable-
segment disclosures list `Other brands` rather than directly naming Teva as the third principal
brand, so those are not acceptable alternatives.

## Open human decisions

1. `p23` is revised to the unit-volume metric rather than expanding evidence for the original
   compound query.
2. `p40` drops `why` instead of creating a multi-evidence contract; the new wording mirrors the
   filing's `policies/procedures` phrase.
3. `a23` selects constant-currency net-sales growth, keeping it separate from `p23` and from the
   comparable DTC metric.
4. `n08` retains both identical-text source locations plus the differently worded Note 1 location.
   They are acceptable OR alternatives and must not inflate the metric denominator.

No proposed occurrence violates the 50–200 character contract. All Round 2 review fields are
intentionally blank for human review.
