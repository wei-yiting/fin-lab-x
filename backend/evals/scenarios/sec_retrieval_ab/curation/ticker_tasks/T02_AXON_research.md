# T02 AXON — pipeline-independent filing research

Research date: 2026-08-27

Scope: FY2025 Form 10-K, active non-`multi_passage` candidates only

Human review fields: not assigned in this note

## Scope and result

- Ticker / CIK: `AXON` / `0001069183`
- Accession: `0001628280-26-011360`
- Active candidates: `p26`, `p43`, `n07`
- Full traversal coverage: `36/36` fixed neutral windows; `425,266/425,266` canonical characters
- Acceptable distinct occurrences: `p26 = 1`, `p43 = 3`, `n07 = 2`
- Human review fields changed: no

`p11` and `a11` are excluded because they are `multi_passage`. The three `p43` occurrences are
separate OR-hit alternatives even though each reports the same available-borrowing amount: they
appear in Item 7, Item 7A, and Item 8 Note 13, respectively.

## Filing identity and official sources

- Period of report: `2025-12-31`
- Filing date: `2026-02-25`
- Primary document: `axon-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1069183/000162828026011360/0001628280-26-011360-index.htm)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1069183/000162828026011360/0001628280-26-011360.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/1069183/000162828026011360/axon-20251231.htm)

The accession-pinned complete submission was fetched directly from SEC Archives. The exact
`<TYPE>10-K` document was extracted from its SGML `<DOCUMENT>` records. Its bytes match the
separately downloaded primary document.

Reproducibility hashes:

| Artifact | SHA-256 |
|---|---|
| Complete submission bytes | `e30b918df0bc7158fad0a9dba3bcb46f248a9093c04800186f64c7683427c385` |
| Extracted primary 10-K HTML bytes | `5b675d1765416a5be65fc6bb2498747b03d713e33f7579ead2a69deb7df94529` |
| Separately downloaded primary HTML bytes | `5b675d1765416a5be65fc6bb2498747b03d713e33f7579ead2a69deb7df94529` |
| Canonical visible-text bytes | `fbeb437c9a1b2319fa37948c80b15fcd18c0e07a04068fa87bef05345bda5f11` |

## Pipeline-independent traversal method

No `sec_text_pipeline`, repository Item/block/unit hierarchy, generated markdown, candidate
evidence, or prior retrieval result was used to determine traversal order.

1. Extract the exact primary `<TYPE>10-K` document from the complete submission and remove only
   the SEC `<XBRL>` transport wrapper when present.
2. Parse visible HTML in source reading order; remove `head`, `script`, `style`, `noscript`,
   `template`, `ix:hidden`, and inline `display:none` content.
3. Decode entities, replace non-breaking spaces, preserve neutral paragraph/table separators,
   and collapse transport whitespace. Do not introduce Item, section, block, sentence, or semantic
   hierarchy.
4. Traverse the resulting canonical text sequentially in fixed, non-overlapping 12,000-character
   windows. Only after the complete pass, audit all occurrences relevant to the active questions.

Offsets below are zero-based half-open intervals `[start, end)` in the canonical visible text.

## Sequential coverage ledger

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | [0, 12000) | `6892d4f06a20b6bb511614ddfa0d01b54b39cf8bdef260736ca1e9d10cb125dc` | inspected |
| W0002 | [12000, 24000) | `308f5b636aa8c5bd0eb6c7fe2fd12eaf9c3596dc897c95d0e452606fdc7ae331` | inspected |
| W0003 | [24000, 36000) | `6b97a034fc681bdcf0474aba0b110e656c90ef90b829bf8679c6542d152a93f2` | inspected |
| W0004 | [36000, 48000) | `4bac80f814a31840994bd90e5c553fce8d14cb01a2f6fb9e6db353320ab544a9` | inspected |
| W0005 | [48000, 60000) | `eb4d5181a37bfa595a2673757bc3fd62d1f9c6361871aa21a02410c0b12c5193` | inspected |
| W0006 | [60000, 72000) | `0b5215644e4d3421ca0b78feeb22c573f0497aab7c996d488f147de661aa2263` | inspected |
| W0007 | [72000, 84000) | `ceca27fa48b7c67883811966d7f77cdf602c9e89b449b94876edf9b4c956f11a` | inspected |
| W0008 | [84000, 96000) | `17f3c236d5a8538b8d75c7486d230980485f203d0376bd246678af0007b44cee` | inspected |
| W0009 | [96000, 108000) | `3e8f85f9079e94f801c8f33b73a7b5332ea316adaacfb890881a5deb37d7fa54` | inspected |
| W0010 | [108000, 120000) | `acc27904e80d66ffc6ef1e9a421b56bc496b817c9869b880007ff9b623de51af` | inspected |
| W0011 | [120000, 132000) | `e13e9337977354a24400d3df6699797a62e38422da75a2687552f25a91180de7` | inspected |
| W0012 | [132000, 144000) | `a90af7a87f0a8c534cef4c62f59a5411e3c9f50013e3da49c6d7377b12c8a4a3` | inspected |
| W0013 | [144000, 156000) | `b4791cbc78a4e6df19a1dcbb3548c7bf4ad92be30778be30cc5667a3fb56c293` | inspected |
| W0014 | [156000, 168000) | `451a66993514917af9202baaeede388fb2ab1c0df14a2e7c6f09afc79913e8b8` | inspected |
| W0015 | [168000, 180000) | `c9ac203e395313a700298d156a5d368baf9e59069868f14e677c8c54cdbf714f` | inspected |
| W0016 | [180000, 192000) | `850a15c14eb20cb42fe66d300ebc473436183d162f06e61548a6cd1b1f8e1506` | inspected |
| W0017 | [192000, 204000) | `baba538ed57769f0ffc5df11d0259856ededa4729717de5cfde9e8c0257debdc` | inspected |
| W0018 | [204000, 216000) | `d24aec4fe4d7ee15a7cdae814df982f2ddb96716879f77aaff5166ebd50ccb00` | inspected |
| W0019 | [216000, 228000) | `34dc80546ca3dedc3518cddcf15ee52d5d32c81c9636dfcd57569b62f15fed73` | inspected |
| W0020 | [228000, 240000) | `19a2df8c2c1fdc49d0a737d8715e1c4e9ced59c4c64ab2f1c54df3b19a2cda74` | inspected |
| W0021 | [240000, 252000) | `8d475a83eff56fc62ba0fead1255596742767ed6006eb2135d1177965cbf10b4` | inspected |
| W0022 | [252000, 264000) | `6624cdf8ee2435d73b1229d9c5f42f83db416f82caa8747e3a0a99c6c3d22d16` | inspected |
| W0023 | [264000, 276000) | `9d8db6127379a97e91c3c6c3eed6734cf5dab8a8dd85cce3f4d57c9b7eddeda8` | inspected |
| W0024 | [276000, 288000) | `d53698c3fd6afff52b02c93e83795a820e9cad9a388531bfbab12d2b2d7f697c` | inspected |
| W0025 | [288000, 300000) | `0480b98bc2cfe629f32ec44f37f9bb13d1e5ae73331092d96020025b546cfccc` | inspected |
| W0026 | [300000, 312000) | `67873941f2ce3aa2a17ffcf55e3c99ce6eadc395aaafd166a87144f18488fbfa` | inspected |
| W0027 | [312000, 324000) | `4f5a99f31bc374544eec664b89dfafb032249a1c3efe9b5e1fc8c92a7ca8bef0` | inspected |
| W0028 | [324000, 336000) | `944238b359b78e6445efd7978f745c9fc59817054bace7774b11fce657fd6e5f` | inspected |
| W0029 | [336000, 348000) | `5186c3aa88852b95d0fe602baf2abc193ced37d6f6374eca6691c0490b32a329` | inspected |
| W0030 | [348000, 360000) | `da1b98815ff67d4e2f4cd2a23537257fbeb83c50b67edbfd57803223aaaaa311` | inspected |
| W0031 | [360000, 372000) | `0c57087927da49604019295bd5fed70f94e6b6b6eb9251e78123b5eed587cbbf` | inspected |
| W0032 | [372000, 384000) | `445a569a88be8b28eb9afdbb31ed47c7262b2d6b4c649a73e827554c673eb16b` | inspected |
| W0033 | [384000, 396000) | `4f9247750b8cecdf82516418ef6ac8e2ccc437083cd9b44d41e48d47bf01e70f` | inspected |
| W0034 | [396000, 408000) | `ccf447bbf6775e3411a90caa256cef1823109aa9ac6cafe6f2f375c88e8df784` | inspected |
| W0035 | [408000, 420000) | `2d723c4c3446f9c91caa5910013c2d7f3d622dc4099ada10823dda664795b8e7` | inspected |
| W0036 | [420000, 425266) | `17cede49e231e6a280d1a8fef776380eea62c7d9411f24cc35a88cfc682baffe` | inspected |

The intervals are contiguous from `0` through `425266`, with zero gaps and zero overlaps.

## Candidate findings

### `p26` — narrow to Personal Sensors; one acceptable occurrence

- Round 1 decision: `?`
- Round 1 question: `What factors drove TASER, Personal Sensors, and Platform Solutions growth?`
- Round 1 comment: `題目應該只問單一產品，不要一次問三個`
- Recommended revised question: `What drove the increase in Axon's Personal Sensors revenue in 2025?`
- Acceptable occurrence count: `1`

#### p26-e01

- Filing location: Item 7 → Results of Operations → Connected Devices
- Window and canonical offsets: `W0016`, `[181724, 181910)`
- Character count: `186`
- Snippet SHA-256: `57f85c91881437c47ff87a82bcf75bf9c3333209e24c0b1d8b9496cacd74c360`

> Personal Sensors increased $80.1 million, which was primarily driven by the continued adoption of our newest body camera, AB4, and higher warranty revenue from more devices in the field.

`AB4` occurs once in the canonical filing. Other Personal Sensors references define the product
category or report amounts but do not independently explain the 2025 increase.

### `p43` — keep question; three acceptable occurrences

- Round 1 decision: `o`
- Round 1 question: `How much credit could Axon draw at year-end 2025?`
- Round 1 comment: none
- Recommended question change: none
- Acceptable occurrence count: `3`

#### p43-e01

- Filing location: Item 7 → Liquidity and Capital Resources → Summary
- Window and canonical offsets: `W0017`, `[198921, 199074)`
- Character count: `153`
- Snippet SHA-256: `24e3471b5d5bb6e14a667fe949fb3e81499ef1aa850d9e7451ded49ac2eae8c7`

> As of December 31, 2025, we had letters of credit outstanding of approximately $8.9 million under the facility and available borrowing of $291.1 million.

#### p43-e02

- Filing location: Item 7A → Interest Rate Risk
- Window and canonical offsets: `W0019`, `[226300, 226470)`
- Character count: `170`
- Snippet SHA-256: `7b10c1916774a664b94b3e92df7ba3e20c50c2616fe876b5b7b5d883597cc0da`

> As of the year ended December 31, 2025, there was no amount outstanding under the line of credit, and the available borrowing under the line of credit was $291.1 million.

#### p43-e03

- Filing location: Item 8 → Note 13 — Line of Credit
- Window and canonical offsets: `W0030`, `[355627, 355722)`
- Character count: `95`
- Snippet SHA-256: `32d62e61d93eb76f06d19991742f3535f75322c5c03561da0136cf9f006b6dcc`

> available borrowing of $291.1 million, excluding amounts available under the accordion feature.

The third occurrence is an answer-bearing clause from a 210-character source sentence. The
complete sentence exceeds the 200-character limit, so the 95-character clause is the shortest
self-contained answer span that preserves the accordion-feature qualification. Including this
Item 8 occurrence does not turn the question into an Item 8 sampling candidate; it only makes the
OR-answer set complete across the filing.

### `n07` — keep question; two acceptable occurrences

- Candidate type: new intent-first question
- Question: `How do Axon's subscription offerings support its recurring-revenue model?`
- Recommended question change: none
- Acceptable occurrence count: `2`

#### n07-e01

- Filing location: Item 1 → Key Product Category Revenue Drivers: What We Offer
- Window and canonical offsets: `W0002`, `[12871, 13024)`
- Character count: `153`
- Snippet SHA-256: `12f8bbad46f1454c66f9f0d63866af6429b5bec5bbb56e2e077867206f814890`

> Our revenue is derived from a combination of hardware sales, multi-year recurring software subscriptions, professional services, and extended warranties.

#### n07-e02

- Filing location: Item 1 → Software and Services
- Window and canonical offsets: `W0002`, `[13183, 13380)`
- Character count: `197`
- Snippet SHA-256: `f7cfa8d1127296dfe1a850b3f298fa0d6d514ce1dbf768f35942189a529d34b1`

> Axon has a suite of cloud-based, SaaS solutions that deeply integrate with our hardware to benefit customers and drive annual recurring revenue, which totaled $1.3 billion1 as of December 31, 2025.

The first occurrence directly identifies multi-year recurring software subscriptions as a revenue
source. The second independently connects Axon's SaaS offering suite to annual recurring revenue.

Related occurrences that are not acceptable alternatives:

| Canonical range | Disclosure | Exclusion reason |
|---:|---|---|
| `[11927, 12129)` | Software and Services includes recurring cloud-hosted software revenue | Full sentence is 202 characters and does not connect the revenue to subscription offerings |
| `[13381, 13514)` | Subscription licensing drives SaaS revenue | Does not independently establish the recurring-revenue connection |
| `[118405, 118747)` | Subscription payments differ from hardware sales and the model provides predictable recurring cash flows | Complete explanatory pair is 342 characters; the under-200 fragments rely on “this approach” or “this model” without an antecedent |
| `[263634, 265300)` | Subscription contract-asset, invoicing, and deferred-revenue accounting | Explains recognition timing rather than how the offerings support Axon's recurring-revenue model |

## Round-2 assembly recommendation

This ticker task proposes the revised `p26` question and the complete OR-evidence sets for `p26`,
`p43`, and `n07`. It does not assign `round2_decision` or a new human review comment. When the
Round-2 comparison artifacts are assembled, carry forward the Round-1 question, evidence,
decision, and reviewer comment; place `candidate_id` immediately before the blank new review
fields.
