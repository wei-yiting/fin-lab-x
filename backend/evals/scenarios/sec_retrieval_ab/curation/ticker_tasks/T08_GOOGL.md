# T08 GOOGL — pipeline-independent filing traversal

## Scope and result

- Ticker: `GOOGL`
- Fiscal year: `2025`
- Accession: `0001652044-26-000018`
- Active non-`multi_passage` candidates, ordered Round 1 `o` before `?`: `p41`, `a24`, `p24`
- Excluded split-dataset candidates: `p09`, `a09` (`multi_passage`)
- Full traversal coverage: `31/31` fixed neutral windows; `363,560/363,560` canonical characters
- Acceptable distinct occurrences: `p41 = 1`, `a24 = 2`, revised `p24 = 2`
- Human review fields changed: no
- Final Round 2 review or dataset artifacts generated: no

`a24` and revised `p24` each have one Item 7 occurrence and one Note 6 occurrence. They are
separate OR-hit alternatives even where the disclosures communicate the same answer.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/0001652044-26-000018-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/0001652044-26-000018.txt)
- [Primary 10-K document](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm)
- Filing date: `2026-02-05`
- Accepted: `2026-02-04 21:56:03 ET`
- Period of report: `2025-12-31`
- Complete-submission bytes / SHA-256: `15,653,193` / `66662b7992c979bb14d45147156d589e3bdf33c227f513efedfc3196f67e8b9a`
- Primary document: `goog-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`, `DESCRIPTION=10-K`)
- Primary-document bytes / SHA-256: `2,616,499` / `c2f6301004f35411a20611c14ff01d80a85c0bcbab6053c80d8cc7f6fc747161`
- Canonical visible-text bytes / chars / lines: `364,195` / `363,560` / `6,141`
- Canonical visible-text SHA-256: `3224c37b8c2e941f7210e97555272acd0cf84f8abd839fd35be5ad64c1e3e612`

The accession-pinned complete submission contains exactly one `TYPE=10-K` document. A separate
download of the SEC primary document equals the extracted document plus its single trailing
newline.

Canonicalization uses the shared `round2_traversal` transport path: remove only the SEC XBRL
wrapper, parse visible HTML in source order, remove non-visible transport content, insert neutral
separators at HTML block boundaries, decode entities, and normalize transport whitespace. No
Item, heading, block, sentence, candidate evidence, prior retrieval result, or repository-pipeline
hierarchy determined traversal order or coverage. Offsets below are zero-based and end-exclusive
against exactly this canonical text.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | [0, 12000) | `9e9b7a09467495370084852e01d5d0c42d47facbaebc840929c39266891cd7b5` | inspected |
| W0002 | [12000, 24000) | `26f085a987b350d3f4bae10ab5cbc655d8543c8d1ba9a339ae0887481e0aa948` | inspected |
| W0003 | [24000, 36000) | `b12b0c8ef6d1446331a6701604470789422fe0669706c51ac6d63bf39bc03e02` | inspected |
| W0004 | [36000, 48000) | `b245e2729c9d7702157d8c98f7a31be963933624fcbd7c8ffa163c3194b1217e` | inspected |
| W0005 | [48000, 60000) | `987dd0887c29441c0b4d50763a2af084277505015fb611336058a1fa25976c21` | inspected |
| W0006 | [60000, 72000) | `296ce55f7e59cb96ba23a58437febce6a0d7daa86bbc7c8dacac44b95a0597dd` | inspected |
| W0007 | [72000, 84000) | `dc8a7ea616ff60fa26ec757066f3963f060a9ce9a48a3bec24309b5200ad2102` | inspected |
| W0008 | [84000, 96000) | `c51588e1c62e92c0498720d6e93bdf215aa69a3546629dff950f67b7d7632a4d` | inspected |
| W0009 | [96000, 108000) | `3b3808da422474b7eeecd4c3d6b13eb0bdb29996ed360ee7de7f3b434bdc9e52` | inspected |
| W0010 | [108000, 120000) | `ab48c7a1b844e0be532ea5a173a6bb51c529e3bc921aac6437932fd98c4db5d4` | inspected |
| W0011 | [120000, 132000) | `cfc2c3150ea8aea4ce13495cdd991b8f310c1e029d4c48f4d6b5499e943f2c40` | inspected |
| W0012 | [132000, 144000) | `5a6d283a7f010e5cc569743bad4e6d432709007fb724e7b30a54af6688132b02` | inspected |
| W0013 | [144000, 156000) | `ab955144a1fffd084f3a63ba6795f3cb399344db09041503c0f0178c56e511f9` | inspected |
| W0014 | [156000, 168000) | `c028e8b2d55d3bc3ac2f39d7a4cc64c153832f5daecc53dc71dee5cffd467720` | inspected |
| W0015 | [168000, 180000) | `c639db3894bca3199993a10c92b0a41d6ac86e1d1669da8baaa610d60f4ea6e6` | inspected |
| W0016 | [180000, 192000) | `17d26d3cd06af06079d32aa735bf34e94ba19a68ba3c66736958f1aa7a1a5497` | inspected |
| W0017 | [192000, 204000) | `01fded0a8726448aaa7dcbce9fbf095a395717636f7307537f52a250ff11be91` | inspected |
| W0018 | [204000, 216000) | `f72df08ebc48222a9651409966afe91bf9bbde6143a6f94e4acd3b8548fc2cc0` | inspected |
| W0019 | [216000, 228000) | `8db1e4e5299e9e10e16cc1173fcdfd979fca41648a1cf63761d6d67fb0d91ded` | inspected |
| W0020 | [228000, 240000) | `b2cdf21d960eab17ad80e42420319185c1bd580c9f728a13732efcd28bb05458` | inspected |
| W0021 | [240000, 252000) | `e409e755676bf38641d6ef51c22d4930a9358a2316f810c93c6be90fedf0e36b` | inspected |
| W0022 | [252000, 264000) | `b22cbd254e801e730a310658b25e14ac2b54de8a8e2998d06da422f9dfd62b7a` | inspected |
| W0023 | [264000, 276000) | `da98cceb317cafae8067a548a9c059a4b34bbb7408f22e0e0c8fdf0754488344` | inspected |
| W0024 | [276000, 288000) | `392ae7f98f701752c2544518192e37295247ce6d1aa53d5489c2bc86c24a05dc` | inspected |
| W0025 | [288000, 300000) | `1469355114751eff23804e2eb3fd4cd1d60f04625c35ea308d7381c804e13f62` | inspected |
| W0026 | [300000, 312000) | `946e2587e6735ff08f1250a67885551bfed721ebf32ad85b58a52b46c01a159f` | inspected |
| W0027 | [312000, 324000) | `688b17598fda70d9ff2489d90f1bb881f15ccf4595cd613a372a3d9b6c89518e` | inspected |
| W0028 | [324000, 336000) | `c57fa7b46bd303af27fc23d19677cde5a9239be1545af05c40330c74e9aaf181` | inspected |
| W0029 | [336000, 348000) | `65789cee29dec65496f6533a9053992fa144ca550750d31845531afc05b64912` | inspected |
| W0030 | [348000, 360000) | `1d5a5285b483204025a9f0428eb41e6021d92bb7e346565b179cf65aadb7a54f` | inspected |
| W0031 | [360000, 363560) | `3f7da88beb1ef2fabc6fa9afcffa4d4a0e83e5268d6f5347e6e96f8d5e52d199` | inspected |

Traversal checkpoints:

- `W0001–W0003`: cover, Item 1, business model, products, competition, workforce, regulation,
  and start of Item 1A; no acceptable occurrence.
- `W0004–W0010`: Item 1A risk factors. Cybersecurity, financing, foreign-currency, and
  infrastructure risks do not identify the independent cyber-control tester or the specific debt
  facilities and issuances requested here.
- `W0011`: end of Item 1A and complete Item 1C. Contains the sole `p41` occurrence.
- `W0012–W0014`: Item 7 trends, revenue drivers, expenses, profitability, cash flow, and liquidity;
  no acceptable occurrence.
- `W0015`: Item 7 financing. Contains the first `p24` and `a24` occurrences.
- `W0016`: Item 7A. Fixed- and floating-rate investment-risk disclosures describe portfolio risk,
  not the November debt issuance mix; no acceptable occurrence.
- `W0017–W0018`: auditor reports and primary financial statements; no acceptable occurrence.
- `W0019–W0021`: Notes 1–2 and start of Note 3; no acceptable occurrence.
- `W0022–W0023`: Note 3 financial instruments and derivatives. General fixed/floating investment
  and hedge disclosures do not state the candidate answers.
- `W0024`: Notes 4–6. Contains the second `p24` and `a24` occurrences.
- `W0025–W0029`: Notes 7–16, controls, and Part III incorporation; no additional occurrence.
- `W0030–W0031`: exhibit index and signatures. The exhibit list enumerates individual note series
  but omits the issuance amounts needed for revised `p24`.

After sequential traversal, full-text cross-checks covered `Internal Audit`, `independently
tests`, `cybersecurity controls`, `revolving credit facilities`, borrowing/outstanding status,
`floating-rate`, `fixed-rate`, `dollar-denominated`, `euro-denominated`, and `weighted-average
coupon rate`. They found no additional independently sufficient occurrence.

## Candidate findings

### `p41` — keep question; one acceptable occurrence

- Candidate ID: `p41`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `o`
- Round 1 question: `Who independently evaluates Alphabet's cyber defenses?`
- Round 1 comment: `但是這個 query 是蠻罕見的問題，不會優先選這題`
- Proposed question change: none
- Proposed query type: `factoid`

Occurrence 1:

- Filing location: Item 1C, Cybersecurity, governance and oversight
- Window and canonical offsets: `W0011`, `[123761, 123878)`
- Canonical line: `1025`
- Character count: `117`
- Snippet SHA-256: `bc3b125f6e2c16c9f08323843f3635cdeff79befaf124810b3e7840ceb7d3bce`

> Internal Audit maintains a dedicated cybersecurity auditing team that independently tests our cybersecurity controls.

This is the only occurrence that identifies both the independent function and its cyber-control
testing role. Risk and Compliance Committee oversight, outside-counsel consultation, and the
independent public accounting firm concern different responsibilities. The Round 1 concern is
candidate value, not evidence correctness, and remains for human filtering.

### `a24` — keep question; add the Note 6 occurrence

- Candidate ID: `a24`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `o`
- Round 1 question: `What borrowing capacity and maturity schedule did Alphabet's unused revolvers have?`
- Round 1 comment: none
- Proposed question change: none
- Proposed query type: `passage`

Occurrence 1:

- Filing location: Item 7, Liquidity and Material Cash Requirements, Financing
- Window and canonical offsets: `W0015`, `[172698, 172852)`
- Canonical line: `1875`
- Character count: `154`
- Snippet SHA-256: `3739869e142e18534daad545c0a45d859b823d91b17f85b125b47da40c813b12`

> As of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring in April 2026 and $6.0 billion expiring in April 2030.

Occurrence 2:

- Filing location: Item 8, Note 6, Debt, Credit Facility
- Window and canonical offsets: `W0024`, `[284798, 284959)`
- Canonical line: `4017`
- Character count: `161`
- Snippet SHA-256: `8dffd8eee4a54c2e3a304a6cfcee3c3c237619c36d252e116f64d3edf8f43b03`

> As of December 31, 2025, we had $10.0 billion of revolving credit facilities, of which $4.0 billion expires in April 2026 and $6.0 billion expires in April 2030.

Each occurrence independently states the total capacity and expiration split. Their immediately
following sentences confirm unused status: Item 7 says no amounts had been borrowed, while Note 6
says no amounts were outstanding as of 2024 and 2025. The separate commercial-paper program,
senior-note maturity tables, lease commitments, and generic financing disclosures are not
acceptable alternatives.

### `p24` — revise to one contrast; two acceptable occurrences

- Candidate ID: `p24`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `How did Alphabet vary debt by denomination and coupon structure?`
- Round 1 comment: `query 問的是「如何在幣別跟票面利率結構上做出不同安排」——重點是「vary（不同）」，需要對比才能回答，選的粗體不對`
- Proposed revised question: `What mix of floating- and fixed-rate U.S. dollar notes did Alphabet issue in November 2025?`
- Proposed query type: `factoid`
- Proposed answer requirement: one span must state both the floating-rate and fixed-rate U.S.
  dollar note amounts issued in November 2025

The original question has a real evidence-contract failure. The filing establishes the full
denomination and coupon-structure variation only by combining multiple May and November clauses;
the shortest complete source span exceeds 200 characters. The Round 1 euro-only snippet is one
data point and cannot answer `vary`. The proposed revision preserves the requested contrast while
narrowing it to one issuance and one denomination: `$500 million floating-rate` versus `$17.0
billion fixed-rate`.

Occurrence 1:

- Filing location: Item 7, Liquidity and Material Cash Requirements, Financing, November 2025 issuance
- Window and canonical offsets: `W0015`, `[172245, 172406)`
- Canonical line: `1873`
- Character count: `161`
- Snippet SHA-256: `297610cb04b6d1386241f124f10463e3e12e9e44e1d30118ac2cc4c4367f0683`

> We issued $500 million of US dollar-denominated floating-rate senior unsecured notes and $17.0 billion of US dollar-denominated fixed-rate senior unsecured notes

Occurrence 2:

- Filing location: Item 8, Note 6, Debt, Long-Term Debt, November 2025 issuance
- Window and canonical offsets: `W0024`, `[281729, 281890)`
- Canonical line: `3919`
- Character count: `161`
- Snippet SHA-256: `c78c6f1f075e7e3d6e4263682f1f396b24fc72e2b1db51e84c2358bca43fd763`

> we issued $500 million of US dollar-denominated floating-rate senior unsecured notes and $17.0 billion of US dollar-denominated fixed-rate senior unsecured notes

These are the shortest self-contained source clauses that preserve the full floating-versus-fixed
amount contrast. The source sentences continue with weighted-average coupon and maturity details,
but those details are unnecessary for the revised question and would weaken the 200-character
contract. The Note 6 debt table and exhibit list omit the paired issuance amounts.

## Open human decisions

1. `p41` has a sound and unique evidence contract, but its Round 1 comment says the question is
   too rare to prioritize. Full filing traversal cannot decide whether it deserves one of the
   final 40 slots.
2. `a24` remains unchanged, with the Note 6 disclosure added as a second OR alternative. The
   word `unused` is confirmed by each location's immediately following source sentence, while
   the canonical snippet itself answers the requested capacity and maturity schedule.
3. `p24` cannot keep its original cross-denomination plus coupon-structure contract under the
   50–200 character limit. The proposed rewrite retains a real contrast rather than accepting
   the Round 1 euro-only data point.
4. `a24` and revised `p24` each retain both source locations. Deduplicating semantically repeated
   disclosures would incorrectly mark a valid retrieval from the other location as a miss.

All five proposed occurrences are exact source substrings and satisfy the 50–200 character
contract. All Round 2 human review fields are intentionally blank.
