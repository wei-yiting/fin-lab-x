# T13 NVDA — pipeline-independent filing traversal

## Scope and result

- Ticker / CIK: `NVDA` / `0001045810`
- Fiscal year: `2026`
- Accession: `0001045810-26-000021`
- Active non-`multi_passage` candidates: `p17`, `p33`, `p49`, `a17`
- Excluded `multi_passage` candidates: `a01`, `p01`
- Full traversal coverage: `30/30` fixed neutral windows; `353,596/353,596` canonical characters
- Acceptable distinct occurrences: `p17 = 3`, `p33 = 1`, `p49 = 2`, `a17 = 1`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

Repeated text at different source offsets remains separately represented. These occurrences are
OR-hit alternatives for retrieval evaluation; they do not add metric denominators.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/0001045810-26-000021-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/0001045810-26-000021.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm)
- Filing date: `2026-02-25`
- Period of report: `2026-01-25`
- Primary document: `nvda-20260125.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Complete-submission bytes reported by the index: `11,461,765`
- Primary-document bytes reported by the index: `1,967,816`
- Browser DOM serialization bytes / SHA-256: `1,983,796` / `e5c2ebf40ccf36251b7818eb95d2ce9c94e6bfc4995c833c71860ed7bea5ab87`
- Canonical visible-text bytes / chars / lines: `354,707` / `353,596` / `4,613`
- Canonical visible-text SHA-256: `eeb14bc871982207d1862529575bfb219588da43e9dbfb09862f40b44f42c0b0`

The accession-pinned SEC filing index identifies sequence 1 as the exact `TYPE=10-K` document.
The local SEC Archives transport returned HTTP 403 for raw downloads, while the official primary
document rendered successfully in the browser. Canonical text was therefore derived from that
official browser DOM serialization. This task does not claim raw complete-submission or raw
primary-document hashes; it records the index-reported sizes and hashes the saved DOM
serialization instead.

Canonicalization removed only non-visible transport content, inserted separators at neutral HTML
block boundaries, decoded entities, normalized transport whitespace, and preserved visible source
order. It did not produce or use Item, heading, block, sentence, candidate-evidence, or
repository-pipeline hierarchy.

Offsets below are zero-based and end-exclusive against exactly that canonical text. Filing
locations were assigned after occurrence discovery and did not determine traversal order.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | `[0, 12000)` | `0a9e0cad36ef4fc8246a5caad0b474bfc6536d157310cd7251ce0a1217abd292` | inspected |
| W0002 | `[12000, 24000)` | `79e24f9f84e6c4ea95888c909aec6a2a73e10f9f03c70f4142c8a26b4f1144a8` | inspected |
| W0003 | `[24000, 36000)` | `d0d2dfc8853836aa5dd06eefd48bb2141ba884fbe519599dd35c750fd0eaa981` | inspected |
| W0004 | `[36000, 48000)` | `d2406a2116f323526daef368089ff28e139965e7de7d2d634719a150e332b858` | inspected |
| W0005 | `[48000, 60000)` | `e23cd6349bf92409525f9f41059e3aee56bb38181a39ed5eb4542f89b3065f9b` | inspected |
| W0006 | `[60000, 72000)` | `d749f98037229b4d057d7739e8cffafc82637afcee479659a8eb3a250351208a` | inspected |
| W0007 | `[72000, 84000)` | `4dc78f3cbd3b0a1a6953e30fd59419be8a2d1ca5c0c89ce12219c88fa6f75d42` | inspected |
| W0008 | `[84000, 96000)` | `4b09ecfed85ab89da7ad7f83a27c2161b1f779fecaaf6d0427232cef55741ff1` | inspected |
| W0009 | `[96000, 108000)` | `e0ae2f5e965400acab04ea6a34298b0242dd2ffdfaea4996292a889f361d02dc` | inspected |
| W0010 | `[108000, 120000)` | `a5ab54fc301135a8891431a87f6e3ef58b5b1c3af17930a8f5a26ada5dd0b2c0` | inspected |
| W0011 | `[120000, 132000)` | `cde249f2959643bfedb11fc7c747b2f584d45ab5ff19efc51312505a806dd8eb` | inspected |
| W0012 | `[132000, 144000)` | `5afa6503e3c7e4071bc377ab9687f20b6097d9d5e798a7c1e5ea2648e39bfd35` | inspected |
| W0013 | `[144000, 156000)` | `a17e4d02e7f9b1d255924860acf6f07bb55433e3db0a83e6e0bd1b0e6fe310f6` | inspected |
| W0014 | `[156000, 168000)` | `6633f197164250fef68ad1168a09e881a2ac681ce36df7464319a4e4e00c5349` | inspected |
| W0015 | `[168000, 180000)` | `25f6b07229a0dd651133b8ec318c166db2036317923e61a974bca4a4814855b3` | inspected |
| W0016 | `[180000, 192000)` | `fff595d60fdd9f890546dc4131af23cf30941e88e14740d2894fc28a5341f8e7` | inspected |
| W0017 | `[192000, 204000)` | `d7a3802ce49dd20fdff118bd6a54d6907f5b1c1e9ce375d829fce3f6131eb3fd` | inspected |
| W0018 | `[204000, 216000)` | `8bfcd87ab57dcc0dd8c7cf58748ecb90beb274d668c674cf3307a401d1393bd6` | inspected |
| W0019 | `[216000, 228000)` | `ea1f280dbf2c9cbe13c6fd8df8fd91e813ce9343ddd040abd7321ce9e2803569` | inspected |
| W0020 | `[228000, 240000)` | `6895a3e160b2e6fecd4071d57487569f80c26c728a645c8490fd9500c180196b` | inspected |
| W0021 | `[240000, 252000)` | `57e7ceec8168851131db1289e3e3b74d5c4d96babdaf6c4d01cfeffdf763dc3e` | inspected |
| W0022 | `[252000, 264000)` | `7b1ed57f354db97a21f93f88228649b04be0bfd5ddd06de83f32d32a4edad94f` | inspected |
| W0023 | `[264000, 276000)` | `1053f7438bb2963df901e54cc25dd7a22c61eaeb204526c08f4938c64a58da81` | inspected |
| W0024 | `[276000, 288000)` | `4669f09449bc8339aa59320618f747e6b8d491fd22a7ebef9b3c46c1739e14a4` | inspected |
| W0025 | `[288000, 300000)` | `7497e908545651b72f4fd23bd8bd54eb7836f3630f1393f9a4283f692a48ff38` | inspected |
| W0026 | `[300000, 312000)` | `65465d0b92b821c465deda416ed472488cb59b1ff24289341b471609b782bf4d` | inspected |
| W0027 | `[312000, 324000)` | `8917bf533c06b4569c11cc4f82bc93ec8b2183f31fb3ecd334b5785205e9d4c2` | inspected |
| W0028 | `[324000, 336000)` | `0f419e418961c31a6e632ed340d005618f186aa331a121cd4e88378bf49a9748` | inspected |
| W0029 | `[336000, 348000)` | `2735e93740abd71052a50c1e7cfea0e054f7c559c8b9d073bc59fe336cd19c83` | inspected |
| W0030 | `[348000, 353596)` | `7d4cdaf141b334201e1705f9b8e3a40ee2359bda6f7cc0bb28b249f06b5fd7c8` | inspected |

The intervals are contiguous from `0` through `353596`, with zero gaps and zero overlaps.

Traversal checkpoints:

- `W0001–W0005`: cover and Item 1 business descriptions. `W0002` contains the sole `p33`
  occurrence.
- `W0006–W0015`: Item 1A and Item 1C. The first corrected `p17` occurrence appears in
  `W0010`; an alternate ERP occurrence for `p49` appears in `W0011`.
- `W0016–W0019`: Items 5, 7, 7A, and 9A. `W0018` contains `a17` plus one corrected `p17`
  occurrence; `W0019` contains the original `p49` occurrence.
- `W0020–W0028`: financial statements and Notes 1–15. No additional active-candidate
  occurrence appears in this range.
- `W0029–W0030`: Note 16, remaining disclosures, exhibits, and signatures. Note 16 repeats the
  corrected `p17` occurrence at a third distinct offset.

After sequential traversal, full-text audits covered direct terms and plausible alternatives for
customer and partner concentration, Rubin cost-per-token and production timing, ERP modernization,
and Data Center compute versus networking growth. They found no additional independently
sufficient occurrence.

## Candidate findings

### Correction — `p17` largest direct customer share (supersedes the Round 2 proposal below)

- Candidate ID: `p17`
- Round 2 decision:
- Round 2 reviewer comment:
- Corrected question: `What share of NVIDIA's fiscal 2026 revenue came from its largest direct customer?`
- Corrected query type: `factoid`
- Corrected answer requirement: One independently sufficient span must state the percentage of
  total fiscal 2026 revenue attributable to NVIDIA's largest direct customer. Qualitative
  concentration statements, indirect-customer disclosures, and percentages for accounts
  receivable or another fiscal year are partial or non-responsive.
- Result: `3` acceptable distinct source occurrences, all answering `22%`.

The source remains the accession-pinned [SEC filing index](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/0001045810-26-000021-index.html),
which identifies `nvda-20260125.htm` as sequence 1 and `TYPE=10-K`, and the official
[SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm).
The pipeline-independent canonical text and its existing `30/30` neutral-window coverage ledger
were re-verified before the query-specific audit: `353,596` characters, SHA-256
`eeb14bc871982207d1862529575bfb219588da43e9dbfb09862f40b44f42c0b0`, contiguous from offset
`0` through `353596` with no gaps or overlaps.

| Occurrence | Filing location | Window / offsets | Canonical line | Chars | Snippet SHA-256 |
|---|---|---:|---:|---:|---|
| 1 | Item 1A, customer-concentration risk | `W0010` `[116355, 116508)` | 937 | 153 | `7d7c630fdba2e391e806c8ba50d09f74bacbcd661c3f94afbfa48990b1ef6633` |
| 2 | Item 7, Concentration of Revenue / Direct Customers | `W0018` `[205958, 206111)` | 1499 | 153 | `7d7c630fdba2e391e806c8ba50d09f74bacbcd661c3f94afbfa48990b1ef6633` |
| 3 | Item 8, Note 16 / Direct Customers | `W0029` `[337687, 337840)` | 4007 | 153 | `7d7c630fdba2e391e806c8ba50d09f74bacbcd661c3f94afbfa48990b1ef6633` |

All three occurrences use this exact canonical snippet:

> For fiscal year 2026, sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14% of total revenue

The comparison with the next disclosed direct-customer share makes `22%` identifiable as the
largest disclosed share while keeping the snippet independently interpretable and within the
50–200 character contract. The shorter `22%` clause was not selected because it would not itself
show why that customer is the largest. Identical wording is retained at all three offsets because
each is a distinct retrievable source occurrence. The Note 16 copy is visible narrative text in
the primary 10-K under `Note 16 - Segment Information`; it is not a hidden XBRL fact or a label
borrowed from outside Item 8.

The full-text audit found exactly three copies of the selected snippet. Broader, case-insensitive
checks for `fiscal year 2026`, `direct customer`, `22%`, and `revenue` found the same three source
locations and no alternate wording. The following formerly acceptable `p17` classes are excluded
under the corrected answer requirement:

- general partner, distributor, or customer-concentration statements without the `22%` share;
- indirect-customer `10% or more` language and the qualitative AI-company disclosure;
- fiscal 2025 or fiscal 2024 direct-customer percentages;
- customer accounts-receivable concentration percentages, which measure receivables rather than
  fiscal 2026 revenue;
- table labels, XBRL facts, or isolated percentages that require non-contiguous context.

This correction is the assembly input for `p17`. The older broad customer-concentration proposal
and its 11 occurrences below remain only as the Round 2 audit trail. Human review fields remain
blank. `round2_ticker_results/T13_NVDA.json` contains the corrected question and the three
acceptable occurrences.

### Previous `p17` proposal — broad customer concentration; 11 occurrences (audit only)

- Candidate ID: `p17`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `NVIDIA reliance on large downstream buyers and AI lab demand`
- Round 1 comment: `我覺得題目可以簡化成對大型下游買家的依賴程度就好，然後 evidence 再找過，也可以不止一個 evidence`
- Proposed revised question: `How concentrated is NVIDIA's revenue among its largest customers?`
- Proposed query type: `passage`

The revision removes the separate AI-lab-demand intent and retains the original intent of customer
concentration. Qualitative and quantitative disclosures about direct or indirect concentration are
independently responsive OR alternatives.

| Occurrence | Filing location | Window / offsets | Chars | Snippet |
|---|---|---:|---:|---|
| 1 | Item 1A, risk summary | `W0006` `[61221, 61313)` | 92 | A significant amount of our revenue stems from a limited number of partners and distributors |
| 2 | Item 1A, customer-concentration heading | `W0010` `[115903, 116000)` | 97 | We receive a significant amount of our revenue from a limited number of partners and distributors |
| 3 | Item 1A, customer-concentration risk | `W0010` `[116209, 116354)` | 145 | We have experienced periods where we receive a significant amount of our revenue from a limited number of customers, and this trend may continue. |
| 4 | Item 1A, direct customers | `W0010` `[116355, 116508)` | 153 | For fiscal year 2026, sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14% of total revenue |
| 5 | Item 1A, indirect customers | `W0010` `[118122, 118289)` | 167 | We generate a significant amount of our revenue from a limited number of indirect customers, and we estimate some individually representing 10% or more of our revenue. |
| 6 | Item 7, concentration of revenue | `W0018` `[205825, 205937)` | 112 | Our revenue is concentrated among a limited number of direct and indirect customers and this trend may continue. |
| 7 | Item 7, direct customers | `W0018` `[205958, 206111)` | 153 | For fiscal year 2026, sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14% of total revenue |
| 8 | Item 7, indirect customers | `W0018` `[206882, 207033)` | 151 | We generate a significant amount of our revenue from a limited number of indirect customers, some individually representing 10% or more of our revenue. |
| 9 | Item 7, indirect AI company | `W0018` `[207135, 207306)` | 171 | We estimate that one AI research and deployment company contributed to a meaningful amount of our revenue purchasing cloud services from our customers in fiscal year 2026. |
| 10 | Item 8, Note 16, customer concentration | `W0029` `[337554, 337666)` | 112 | Our revenue is concentrated among a limited number of direct and indirect customers and this trend may continue. |
| 11 | Item 8, Note 16, direct customers | `W0029` `[337687, 337840)` | 153 | For fiscal year 2026, sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14% of total revenue |

The complete per-occurrence line numbers, hashes, exact-text counts, and acceptance reasons are in
`round2_ticker_results/T13_NVDA.json`. Identical wording in Items 1A, 7, and Note 16 remains
separate because a retriever can hit any one source location.

### `p33` — select token-cost improvement; one acceptable occurrence

- Candidate ID: `p33`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `Rubin production timeline and token-cost improvement over Blackwell`
- Round 1 comment: `題目應該只問單一事，production timeline 或 token-cost improvement over Blackwell`
- Proposed revised question: `How does NVIDIA say Rubin improves cost per token compared with Blackwell?`
- Proposed query type: `factoid`

This selects the token-cost comparison already supported by the original snippet and drops the
separate production-timeline intent.

Occurrence 1:

- Filing location: Item 1, Business / Our Markets / Data Center
- Window and canonical offsets: `W0002`, `[23747, 23943)`
- Canonical line: `377`
- Character count: `196`
- Snippet SHA-256: `897eb219451483860d66543b507624c3877a275598013566c84aad83282ebf88`

> Built for agentic AI and reasoning, it excels at processing multi-step problem-solving and massive long-context workflows, delivering up to a 10x reduction in cost per token compared to Blackwell.

### `p49` — keep question; two acceptable occurrences

- Candidate ID: `p49`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `o`
- Round 1 question: `What corporate software modernization initiative is NVIDIA continuing?`
- Round 1 comment: none
- Proposed question change: none
- Proposed query type: `factoid`

Occurrence 1:

- Filing location: Item 1A, business processes and information systems
- Window and canonical offsets: `W0011`, `[121635, 121766)`
- Canonical line: `953`
- Character count: `131`
- Snippet SHA-256: `2a6061b3c19edcfa3bcdd176d7e0f004c1c630272162cd6b10da8b44e7766909`

> We continue to design and implement updated accounting functionality related to a new enterprise resource planning, or ERP, system.

Occurrence 2:

- Filing location: Item 9A, Changes in Internal Control Over Financial Reporting
- Window and canonical offsets: `W0019`, `[227546, 227679)`
- Canonical line: `1769`
- Character count: `133`
- Snippet SHA-256: `b10677e4c50de47041c94e7407baf829abbc3e1f3533702f619b0f77953c6fc6`

> We are continuing a phased upgrade of our enterprise resource planning, or ERP, system to update our existing core financial systems.

The Round 1 question remains unchanged; complete traversal adds the Item 1A disclosure as a
second independently sufficient OR alternative.

### `a17` — narrow to networking revenue growth; one acceptable occurrence

- Candidate ID: `a17`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 question: `What propelled NVIDIA's Data Center compute and networking expansion?`
- Round 1 comment: `query 同時問資料中心運算與網路業務的成長，應該只問單一一個`
- Proposed revised question: `What drove the growth in NVIDIA's Data Center networking revenue in fiscal 2026?`
- Proposed query type: `passage`

This keeps only the networking-growth intent directly supported by the Round 1 snippet and removes
the separate compute-growth intent.

Occurrence 1:

- Filing location: Item 7, Results of Operations / Reportable Segments
- Window and canonical offsets: `W0018`, `[204588, 204785)`
- Canonical line: `1485`
- Character count: `197`
- Snippet SHA-256: `ae199d371089fbca3f18553666e62a8bedb3ad4d664ceb75e15b202b69db3af2`

> Revenue from Data Center networking grew 142% driven by the introduction and continued ramp of NVLink compute fabric for GB200 and GB300 systems and the growth of Ethernet and InfiniBand platforms.

## Open human decisions

1. `p17` is narrowed to the largest direct-customer share. Its three accepted occurrences each
   report `22%` and the next direct-customer share of `14%`; indirect and qualitative occurrences
   are excluded.
2. `p33` selects token-cost improvement rather than production timing, preserving the original
   evidence while making the question single-intent.
3. `p49` remains unchanged and gains the independently sufficient Item 1A ERP occurrence.
4. `a17` selects networking growth rather than compute growth, matching its original evidence.

All 7 proposed occurrences are exact canonical substrings and contain 50–200 characters. All
Round 2 review fields are intentionally blank for human review.
