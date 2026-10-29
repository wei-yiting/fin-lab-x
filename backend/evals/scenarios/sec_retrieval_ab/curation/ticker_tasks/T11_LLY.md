# T11 LLY — pipeline-independent filing traversal

## Scope and result

- Ticker / CIK: `LLY` / `0000059478`
- Fiscal year: `2025`
- Accession: `0000059478-26-000013`
- Active non-`multi_passage` candidates: `a19`, `n02`
- Excluded Round 1 `x` candidate: `p19`
- Full traversal coverage: `32/32` fixed neutral windows; `383,149/383,149` canonical characters
- Acceptable distinct occurrences: `a19 = 3`, `n02 = 2`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

The identical manufacturing-expansion sentence appears once in Item 1 and once in Item 7. Both
source locations independently answer `a19`, so they remain separate OR-hit alternatives. The
Round 1 pronoun-led snippet is not retained as a second overlapping variant from the same source
occurrence; the preceding 91-character cause sentence is the canonical snippet for that location.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/0000059478-26-000013-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/0000059478-26-000013.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/lly-20251231.htm)
- Filing date: `2026-02-12`
- Period of report: `2025-12-31`
- Primary document: `lly-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Complete-submission bytes / SHA-256: `14,222,091` / `b405bc2ba1024b52d08e6caba50c6b04850dff86ae8a140eecbf489eb7cf0b6f`
- Extracted primary-document bytes / SHA-256: `2,369,960` / `b697a898706245e4c704c5120e9307fd2de850038ae8d90caf2224da4a5326e0`
- Canonical visible-text bytes / chars / lines: `383,842` / `383,149` / `4,809`
- Canonical visible-text SHA-256: `8e0a9a7133429a6fbf480ec03a2396e63b514f5995c899215d9c6c994f1699f1`

The accession-pinned complete submission identifies sequence 1 as exact `TYPE=10-K` with
`FILENAME=lly-20251231.htm`. A separate SEC download of the primary HTML matches the extracted
document after removal of its single trailing newline.

Canonicalization used the repository's pipeline-independent Round 2 traversal helper. It removed
only the SEC XBRL transport wrapper, non-visible HTML content, and transport whitespace; visible
text stayed in source order with neutral separators at generic HTML block boundaries. No Item,
heading, block, sentence, candidate evidence, repository-pipeline hierarchy, or prior retrieval
output determined traversal order or coverage.

Offsets below are zero-based, end-exclusive intervals in this canonical text. Filing locations
are descriptive provenance assigned after the sequential traversal.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | `[0, 12000)` | `25cefefe326ed7bb05fa32440b1fdede01ef178217b3dc224c4a72ac2a726b4e` | inspected |
| W0002 | `[12000, 24000)` | `bf631f1b9ee03d355de53d740fa809de348575c500c52d5986fe95b5e88e782c` | inspected |
| W0003 | `[24000, 36000)` | `06d2ac3786fa0d3cbbadcabfce77b86f349f14f8984ee95c7933f7c8a57f9c27` | inspected |
| W0004 | `[36000, 48000)` | `6b3469dc11bf28009b3535b6b0defd34eb185176217e8120480505165e84b3f7` | inspected |
| W0005 | `[48000, 60000)` | `818c5c92b9e957c40a826ce31912ef876074efbc157f626509553160add85ec3` | inspected |
| W0006 | `[60000, 72000)` | `5b1901083ac576741cfac167ee1a6602ba56f275c5017326fc012d97eaac015e` | inspected |
| W0007 | `[72000, 84000)` | `3c766791e527e21326efc7edd6386dc549d289e67a5de6973252c66b50655ec4` | inspected |
| W0008 | `[84000, 96000)` | `3f09176bc0e57529b32b9f31206ea6d977e0aaa03c879839bce1c76664e26f8e` | inspected |
| W0009 | `[96000, 108000)` | `d9760e1eca6c742f2ca12cfafc8ac8c4fce1685e39b939a2d4ef605753d4e9ab` | inspected |
| W0010 | `[108000, 120000)` | `8d7382d611e7004d205a9cefb4c80a99ebc840b1698452156ef400d3fe14ac61` | inspected |
| W0011 | `[120000, 132000)` | `f77fd76a7f30cb4b15c33696d38e32869f947ef77ef613c319f2411b961b38c1` | inspected |
| W0012 | `[132000, 144000)` | `cecb2cdbb35f1a88e89dd02047ef6fec796d43c63667ef5fa98486357ec2f504` | inspected |
| W0013 | `[144000, 156000)` | `1d42bd8250b9629ae457085ab19afc41d2d00ca55c438a4649202096f7607ac8` | inspected |
| W0014 | `[156000, 168000)` | `1d8e187f41bcf24da6d8386f3c89e762cd9c764691f90bf17e5c5a34321e32d6` | inspected |
| W0015 | `[168000, 180000)` | `8240dc49b50abc545276700f22aba3422a6c865df1df0eb90d8e9cd7eb2a84ad` | inspected |
| W0016 | `[180000, 192000)` | `79718c36868de9b22955c2944f1eb6043fdb94af51cadba2bd6548be4499e437` | inspected |
| W0017 | `[192000, 204000)` | `0a5a6b8fc268799a379724e1bb67866844d9068328361d25c19ab619131e01d2` | inspected |
| W0018 | `[204000, 216000)` | `912354c8f44858ad84b263c69547113c214d8e20bc0984c62f78f666aab323da` | inspected |
| W0019 | `[216000, 228000)` | `3a53f1e32b34b4ccc616fbcf4f76ab9c1521bbcf0731bde4e818e683f5cd543c` | inspected |
| W0020 | `[228000, 240000)` | `65b38b1fb31791957af95db348293b6168921d4634094f8b7ac301e25d499166` | inspected |
| W0021 | `[240000, 252000)` | `5bac88db8ec699ae5febd85eb9a576e70db073638cb7f84f0a6b844e79e6b856` | inspected |
| W0022 | `[252000, 264000)` | `75a337bb2cd8a1953e76b867a711f1ea9b045e5b47ea4e27edf9717a52ff96c9` | inspected |
| W0023 | `[264000, 276000)` | `0c3afa27ec10ecba3e161cc96dfff0e8c27c0b7981f94fd0ee156baacebae26a` | inspected |
| W0024 | `[276000, 288000)` | `8fd6d6dc224e32d880eeb64e830b568c870b1364382c9ccc407cf234670f239e` | inspected |
| W0025 | `[288000, 300000)` | `d3ce680f064e8b5219b7343b79014a343a287ac12841a5410025ae8bc74f151f` | inspected |
| W0026 | `[300000, 312000)` | `26f4a16ee72a1fa0e26dc30226cac49c754c75456d8f158dba2ee5ca1fb946d2` | inspected |
| W0027 | `[312000, 324000)` | `803ac15eb824c09936ffedc9f1ebed90e16ee2389aa5d075cdc9bf3d30d38986` | inspected |
| W0028 | `[324000, 336000)` | `2b8e4c0b85de9380d553a8aff8f8ed660e7b20959f60e30bb9fb1be90aceb222` | inspected |
| W0029 | `[336000, 348000)` | `50fee9d8cc3ef371b29f26c1e3f952e87060eeba00508a3420aac4d8483fdb79` | inspected |
| W0030 | `[348000, 360000)` | `83454bbccac74edf3241c1be3978eaa22cd8c41246740ff1cf42e5923f351fee` | inspected |
| W0031 | `[360000, 372000)` | `e2c2305b6adc53c965dc66c316cada8f65a35b86056178a74cfe38e02718cacb` | inspected |
| W0032 | `[372000, 383149)` | `ada9b837573a28ffdffdd7a5dd80ea43049861b473620caba15e2af315b8af49` | inspected |

The intervals are contiguous from `0` through `383149`, with zero gaps and zero overlaps.

Traversal checkpoints:

- `W0001–W0006`: cover, Item 1 business, products, competition, regulation, and R&D; no
  company-level revenue-driver occurrence. `W0003` contains incretin competition disclosures
  for excluded `p19`, which is not part of this task.
- `W0007–W0008`: raw materials, product supply, management, and human capital. `W0007` contains
  the first `a19` manufacturing-expansion occurrence.
- `W0009–W0015`: Item 1A risk factors and most of Item 1C. Several manufacturing and capital
  disclosures are generic, conditional, or longer than 200 characters; none adds an acceptable
  occurrence.
- `W0016`: end of Item 1C through Item 7 Executive Overview. It contains the first `n02`
  company-level revenue-driver occurrence.
- `W0017`: Item 7 pipeline and Other Matters. It contains the second `a19` occurrence in the
  Incretin Medicines discussion.
- `W0018`: Item 7 Results of Operations and Financial Condition and Liquidity. It contains the
  second `n02` occurrence and the third `a19` occurrence.
- `W0019–W0020`: remaining Item 7, critical accounting estimates, Item 7A, and the start of Item
  8; no additional occurrence.
- `W0021–W0028`: financial statements and Notes 1–16. Note 2 provides product and geography
  revenue tables but no independently sufficient narrative growth-driver span.
- `W0029–W0032`: contingencies, segment information, auditor reports, Parts III–IV, exhibits,
  and signatures; no additional occurrence.

After sequential traversal, full-text audits covered direct terms and plausible alternatives for
revenue growth, volume, demand, realized price, Mounjaro, Zepbound, capital expenditures,
manufacturing expansion, capacity, global facilities, and anticipated demand. They found no
additional independently sufficient 50–200 character occurrence.

## Candidate findings

### `a19` — keep question, replace evidence, three acceptable occurrences

- Candidate ID: `a19`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Why will Lilly's near-term capital spending remain elevated?`
- Round 1 comment: `粗體字選錯句了，但整個 block 是有涵蓋到的`
- Proposed revised question: unchanged
- Proposed query type: `passage`

The Round 1 question is answerable. Its selected 195-character sentence begins with “These
investments” and is not the best independently readable cause sentence. For that source location,
the preceding 91-character sentence is the canonical snippet. Full traversal also found the same
underlying manufacturing-expansion answer in two other source locations.

Occurrence 1:

- Filing location: Item 1, Business, Raw Materials and Product Supply
- Window and canonical offsets: `W0007`, `[81769, 81908)`
- Canonical line: `1107`
- Character count: `139`
- Exact occurrences in canonical text: `2`

> To support anticipated demand for our current and prospective products, we have undertaken
> significant manufacturing expansion initiatives.

Occurrence 2:

- Filing location: Item 7, Executive Overview, Other Matters, Incretin Medicines
- Window and canonical offsets: `W0017`, `[202988, 203127)`
- Canonical line: `1731`
- Character count: `139`
- Exact occurrences in canonical text: `2`

> To support anticipated demand for our current and prospective products, we have undertaken
> significant manufacturing expansion initiatives.

The two snippets are textually identical but have distinct source provenance. Item 7 immediately
adds that the new capacity should become operational over the next several years, while Item 1
lists the manufacturing sites. Neither occurrence is deduplicated by snippet text.

Occurrence 3:

- Filing location: Item 7, Financial Condition and Liquidity
- Window and canonical offsets: `W0018`, `[214383, 214474)`
- Canonical line: `1897`
- Character count: `91`
- Exact occurrences in canonical text: `1`

> We are making investments in global facilities to manufacture existing and future products.

This is the sentence the Round 1 evidence block needed to emphasize: it states the operational
cause, while the following sentence states the capital-expenditure effect. The following sentence
is not added as another overlapping variant from the same occurrence.

### `n02` — keep question, two acceptable occurrences

- Candidate ID: `n02`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: not applicable; new Round 2 candidate
- Question: `What were the principal drivers of Lilly's 2025 revenue growth?`
- Proposed query type: `passage`

Occurrence 1:

- Filing location: Item 7, Executive Overview, Financial Results
- Window and canonical offsets: `W0016`, `[188613, 188719)`
- Canonical line: `1553`
- Character count: `106`
- Exact occurrences in canonical text: `1`

> Revenue increased in 2025 driven primarily by increased volume, partially offset by lower
> realized prices.

The next sentence attributes both dynamics primarily to Mounjaro and Zepbound. It belongs to the
same disclosure occurrence, so it is retained in `answer_span` but is not added as a second
overlapping canonical snippet.

Occurrence 2:

- Filing location: Item 7, Results of Operations, Operating Results—2025, Revenue
- Window and canonical offsets: `W0018`, `[208980, 209179)`
- Canonical line: `1799`
- Character count: `199`
- Exact occurrences in canonical text: `1`

> In the U.S., the volume increase and the lower realized prices in 2025 were primarily driven by
> Mounjaro and Zepbound.
>
> Outside the U.S., the volume increase in 2025 was primarily driven by Mounjaro.

This distinct disclosure supplies the geographic volume and price drivers within the unchanged
200-character cap. Product-by-product growth sentences and Note 2 tables are partial or require
calculation, so they are not independently sufficient alternatives.

## Open human decisions and uncertainties

1. `a19` keeps its question and changes only the evidence set. Human review still decides whether
   its three occurrences are useful enough for the final 40; no Round 2 decision was prefilled.
2. The two identical `a19` snippets are separate source occurrences under OR-hit semantics. A
   scorer or assembly step must not deduplicate them solely by snippet text.
3. `n02` occurrence 1 is the concise company-level answer; occurrence 2 is a more detailed
   geography-level restatement. Both independently answer the same question and neither expands
   the metric denominator.
4. The 209-character two-sentence Executive Overview paragraph was not forced into one snippet.
   Its first 106-character sentence is the canonical snippet and the full paragraph remains the
   answer span.

No candidate has a confirmed question/evidence contract failure under this handling, and no
snippet exceeds the 50–200 character limit.
