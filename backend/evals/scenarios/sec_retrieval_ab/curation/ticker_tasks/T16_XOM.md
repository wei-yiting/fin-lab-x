# T16 XOM — pipeline-independent filing traversal

## Scope and result

- Ticker / CIK: `XOM` / `0000034088`
- Fiscal year: `2025`
- Accession: `0000034088-26-000045`
- Active non-`multi_passage` candidates: `p31`, `p32`, `n04`
- Excluded candidates: `p13`, `a13` (`multi_passage`); `p47` (Round 1 `x`)
- Full traversal coverage: `36/36` fixed neutral windows; `420,010/420,010` canonical characters
- Acceptable distinct occurrences: `p31 = 1`, `p32 = 1`, `n04 = 1`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

Full traversal found one independently sufficient source occurrence for each proposed question.
The original `n04` contract is not satisfiable by one 50–200-character span: one disclosure states
the 2025 crude-oil and natural-gas price movements, while another quantifies the earnings effect
of lower crude prices only. The proposal therefore narrows `n04` to that supported crude-price
effect instead of relaxing the global span limit.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/34088/000003408826000045/0000034088-26-000045-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/34088/000003408826000045/0000034088-26-000045.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/34088/000003408826000045/xom-20251231.htm)
- Filing date: `2026-02-18`
- Accepted: `2026-02-18 16:06:52`
- Period of report: `2025-12-31`
- Primary document: `xom-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- SEC-declared complete-submission bytes: `26,924,307`
- SEC-declared primary-document bytes: `5,591,068`
- Browser DOM bytes / SHA-256: `200,011` / `afd06eef7abc81939f3f7a1be95e9757684594c649fed0719c392836718d4047`
- Rendered visible-text bytes / SHA-256: `456,004` / `21bd0c3707a3d0453eae980cabca1f054526fbb3597ef115da0328f2307b89a4`
- Canonical visible-text bytes / chars / lines: `424,400` / `420,010` / `5,605`
- Canonical visible-text SHA-256: `83af0bcc2113031d8f0f8289948723a598ac36958dad08bb91f8288966dc3949`

The SEC filing index identifies sequence 1 as the exact primary `TYPE=10-K` document and records
the complete-submission URL and declared file sizes. Direct download of the complete submission
was blocked, so traversal used the official accession-pinned primary 10-K in the in-app browser,
not a third-party or repository filing copy. The Browser DOM hash identifies the browser's XBRL
viewer shell; it is not presented as a hash of the raw SEC primary HTML.

Canonicalization read `document.body.innerText`, converted NBSP to ordinary spaces, normalized
line endings, collapsed horizontal whitespace per line, trimmed lines, and collapsed three or
more newlines to two. It did not produce or use an Item, heading, block, sentence,
candidate-evidence, or repository-pipeline hierarchy.

Offsets below are zero-based and end-exclusive against exactly that canonical text. Filing
locations are descriptive provenance added after occurrence discovery; they did not determine
traversal order or coverage.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | `[0, 12000)` | `040647806c6eb696e17b213b783ac6ee09652a95ca3ed5939f82bd99082ff04e` | inspected |
| W0002 | `[12000, 24000)` | `7f84055ca4d3be2905626f85d5a244a5b0ce6ac51e09688649282cf80778a6f2` | inspected |
| W0003 | `[24000, 36000)` | `85b54cce99f7851907894f65d2c9ac7e7e7836344a465019145af7abf3e4daa6` | inspected |
| W0004 | `[36000, 48000)` | `4b8aaa31e380c2d623e4b87c5f81e02b7dc0dff3ac72f3d0b63e0cf2f0d55bd3` | inspected |
| W0005 | `[48000, 60000)` | `35813ada93775d761ff55a164ecef9f3ee8ce61547d18f02d45d9f8815f5d25e` | inspected |
| W0006 | `[60000, 72000)` | `ebaf7430e050b0e6f5615190c27f93735b677fd52715bcb8cf8da9cac75298e4` | inspected |
| W0007 | `[72000, 84000)` | `a6132743c0e716fbdddbf1675b6fe560472ef7fed8ff442246677838f96f67a2` | inspected |
| W0008 | `[84000, 96000)` | `32360c914bf001e49ddf8fa9659afcbc261833afe6199f7b88429361571dbcab` | inspected |
| W0009 | `[96000, 108000)` | `235943af063ed59ab7e34e4fa359d929397a7fb1e9e279d58c7d00c162184a88` | inspected |
| W0010 | `[108000, 120000)` | `2df2b63c947f7eaf445fef96e8d0ce23a7566b56049f9fca3811b1e0da6f9a48` | inspected |
| W0011 | `[120000, 132000)` | `c1d901e39b0bf918d8d16bb21ac81b2bace0e8ab237081a9294a70854a5f7101` | inspected |
| W0012 | `[132000, 144000)` | `837a1ae885d8be3fd0855d82605c42e72f50c02204a6a6c34690d76e46e88681` | inspected |
| W0013 | `[144000, 156000)` | `c3640243c27d3c7d3307506187b7ff6fad3bdd51e302bda4cdc90cf5bf265863` | inspected |
| W0014 | `[156000, 168000)` | `182444ca2a4588f3a5ff0418ac9bfefd2663aa1055a5935b8a2858a07855cf83` | inspected |
| W0015 | `[168000, 180000)` | `b513396c7495be322aa385762f4f41c033ecb759756e51dfb142bdd0a04dc5be` | inspected |
| W0016 | `[180000, 192000)` | `d1f6ae3ab8b4973afebf93ec4f8c8e20ff464d564e44f7874df1060b2c89c5a4` | inspected |
| W0017 | `[192000, 204000)` | `69f022e2aa419b504f699939c2d104ac9e3db9d124457b8b5917e4d7b04639ba` | inspected |
| W0018 | `[204000, 216000)` | `0d05820264b75aae40b7bc5ad787d8caf8940db7dd1764ab701689bf0b4b7f4c` | inspected |
| W0019 | `[216000, 228000)` | `856c1b683bd5ef15ab634f97dcadc1c9d56b75f3c7e40c36309b521f4af4f9d3` | inspected |
| W0020 | `[228000, 240000)` | `ec57733d2adfcad6a0e73c0d7486c03c930475b69e57d6e1c7ff82c80053a4b6` | inspected |
| W0021 | `[240000, 252000)` | `68976c21c813b8ff1790ac513c52e890c284b2ef23ebd72d940418dc99783340` | inspected |
| W0022 | `[252000, 264000)` | `4d13c04087c427318be348a1183b187db5817a53f0f0008f7cb4c1c63bba3c8c` | inspected |
| W0023 | `[264000, 276000)` | `b8d1893a0210eaf6fc181ca93eef6a5002a10c78ed39ae8060e1ad10608f5d34` | inspected |
| W0024 | `[276000, 288000)` | `ebbe1b3f723d332e3fe546dea3e88efa4bd3eb5daa8eb0b8bed6a08782c3bc43` | inspected |
| W0025 | `[288000, 300000)` | `c9250a9778a470ba488fb181fd648f03d4006f555facbb9407bf2881a18b7eba` | inspected |
| W0026 | `[300000, 312000)` | `9ba5d0fed5824d58a4f13c2f858377579ca1dc8e100013b24994f43ea8052f39` | inspected |
| W0027 | `[312000, 324000)` | `ac2d4eaadd8f4e42f362ef6b93842c8751faa8c944e9bd2cc42180a92b068377` | inspected |
| W0028 | `[324000, 336000)` | `3c2388964968bb2172f35f1fb8f57c102d17a8bd5157c8fa907e3b3b0aa5c1db` | inspected |
| W0029 | `[336000, 348000)` | `5bf6b163f9d5b08caa931721df4c32669c96ef4c273199d76b5f9c661223af52` | inspected |
| W0030 | `[348000, 360000)` | `31612b1c41a28f1dc39b24b2910195522172dda39a7ff31fbc4889b24a0c0917` | inspected |
| W0031 | `[360000, 372000)` | `b504659bab2e7e29e1665bf7637f570d31a8911a3c49f4cb47b715ba387a10a1` | inspected |
| W0032 | `[372000, 384000)` | `44b7098d91d0f58a8470139e787e8811e7fb8e46e7253cd6a5d4782eade25430` | inspected |
| W0033 | `[384000, 396000)` | `47bc7cb4508fa602a9f34d0ac8737c0e0c99bc83718630f9157e59130f375a8f` | inspected |
| W0034 | `[396000, 408000)` | `a7d754754e3d6a6b9985b2f45b810abd2b0cc8af12a8f752a5069dd31dcd7c3e` | inspected |
| W0035 | `[408000, 420000)` | `c5378a6ec598e2e7b86bb7eeb72377c7e712283f78a7db9a69181fa420531c4f` | inspected |
| W0036 | `[420000, 420010)` | `24acdd16468b75c62987f129b726d40708c1ed38749158266a4f0992816ca4ef` | inspected |

The intervals are contiguous from `0` through `420010`, with zero gaps and zero overlaps.

Traversal checkpoints:

- `W0001`: cover, table of contents, and Item 1 business disclosures. It contains the sole
  `p32` and `p31` occurrences.
- `W0002–W0004`: Item 1A risk factors; no active-question occurrence.
- `W0005–W0008`: Item 1C and Item 2 properties. `W0007` contains the excluded `p47`
  source location but no active occurrence.
- `W0009–W0013`: Parts II–IV transition, financial-section terms, forward-looking statements,
  overview, and business environment; no independently sufficient active occurrence.
- `W0014–W0017`: Upstream and Product Solutions results. `W0014` contains the sole acceptable
  occurrence for revised `n04`.
- `W0018–W0022`: liquidity, taxes, environmental matters, market risks, critical accounting,
  audit reports, and core financial statements; no additional active occurrence.
- `W0023–W0032`: financial-statement notes; no additional active occurrence.
- `W0033–W0036`: supplemental oil-and-gas information, standardized cash flows, and signatures;
  no additional active occurrence.

After sequential traversal, full-text audits covered direct terms and plausible alternatives for
career development, retention and tenure, patents and proprietary technology, crude-oil and
natural-gas prices, realizations, earnings drivers, sensitivities, and market risk. They found no
additional independently sufficient occurrence for the proposed questions.

## Candidate findings

### `p31` — keep approved question and evidence; one acceptable occurrence

- Candidate ID: `p31`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `o`
- Round 1 question: `How does ExxonMobil cultivate and retain long-tenured career employees?`
- Round 1 comment: none
- Proposed question change: none
- Proposed query type: `passage`

The Round 1-approved question and snippet remain unchanged. The broader paragraph also discusses
recruiting, planned experiences, training, compensation, and benefits, but those neighboring
sentences do not create another independently sufficient occurrence of the approved answer.

Occurrence 1:

- Filing location: Item 1, Business, talent development
- Window and canonical offsets: `W0001`, `[9208, 9363)`
- Canonical line: `232`
- Character count: `155`
- Snippet SHA-256: `603e5f12ec96143885818a0d1b60afd296fe06126993ed8dffa2b6b30d241b6d`

> Our career-oriented approach to talent development results in strong retention and an average
> length of service of about 30 years for our career employees.

The preceding recruiting and training sentence describes cultivation but not the retention and
tenure result. The following compensation sentence describes an additional retention approach but
does not independently answer the approved question's long-tenure result.

### `p32` — narrow to portfolio size; one acceptable occurrence

- Candidate ID: `p32`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Size and financial importance of ExxonMobil's intellectual property portfolio`
- Round 1 comment: `題目應該只問單一事，size 或 financial importance`
- Proposed revised question: `How large was ExxonMobil's active patent portfolio at the end of 2025?`
- Proposed query type: `factoid`

The proposal selects the `size` half because the original evidence already supplies that answer.
The adjacent sentence about profitability not depending on any individual intellectual-property
right answers the removed `financial importance` half and is not an alternative answer to the
revised question.

Occurrence 1:

- Filing location: Item 1, Business, proprietary technology
- Window and canonical offsets: `W0001`, `[8365, 8441)`
- Canonical line: `230`
- Character count: `76`
- Snippet SHA-256: `c89411df8780c97cd7cfe85fa31b0c43a4f74709e91cccc3572d4d68c68d32a4`

> ExxonMobil held over 8 thousand active patents worldwide at the end of 2025.

Research-and-development costs and other proprietary-technology references do not state the size
of the active patent portfolio and therefore are not acceptable alternatives.

### `n04` — narrow to the disclosed crude-price earnings effect; one acceptable occurrence

- Candidate ID: `n04`
- Round 2 decision:
- Round 2 reviewer comment:
- Candidate type: new intent-first question
- Original question: `How did changes in crude oil and natural gas prices affect ExxonMobil's 2025 earnings?`
- Proposed revised question: `How did lower crude prices affect ExxonMobil's 2025 Upstream earnings?`
- Proposed query type: `passage`

The original requirement asks one span to explain the 2025 earnings effects of both crude-oil and
natural-gas price changes. The filing states that crude prices were modestly lower and natural-gas
prices rose, but its 2025 earnings-driver disclosure attributes the quantified price effect
primarily to lower crude prices; it does not independently state a 2025 natural-gas earnings
effect. The nearest sentence pair exceeds 200 characters and still would not supply that missing
natural-gas effect. The proposal preserves the causal earnings intent while making the evidence
contract satisfiable without changing the global span limit.

Occurrence 1:

- Filing location: Item 7, 2025 Upstream Earnings Driver Analysis
- Window and canonical offsets: `W0014`, `[167393, 167562)`
- Canonical line: `1918`
- Character count: `169`
- Snippet SHA-256: `4c1bee3d3bfbecde94f2481b20d621862a9fdb99142c7fa6aa4d44d1c6f998b8`

> Price – Lower realizations decreased earnings by $6.1 billion, primarily driven by lower crude
> prices as record demand was more than offset by increased industry supply.

Rejected near-matches include the 2025 market-context sentence, which reports price movements but
not their earnings effect; the 2024 lower-gas-realizations driver, which is the wrong period;
generic risk-factor language; and 2026 benchmark-price sensitivities, which are prospective rather
than ExxonMobil's realized 2025 earnings result.

## Open human decisions

1. `p31` is preserved exactly because Round 1 approved it; traversal found no additional
   independently sufficient occurrence.
2. `p32` selects patent-portfolio size rather than financial importance, matching its original
   evidence and removing the compound intent.
3. `n04` is narrowed to lower crude prices and 2025 Upstream earnings. Keeping both crude oil and
   natural gas would require evidence the filing does not disclose in an independently sufficient
   50–200-character span.

No proposed occurrence violates the 50–200 character contract. All Round 2 review fields are
intentionally blank for human review.
