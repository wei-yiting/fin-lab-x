# T15 PODD — pipeline-independent filing traversal

## Scope and result

- Ticker: `PODD`
- Fiscal year: `2025`
- Accession: `0001145197-26-000028`
- Active non-`multi_passage` candidates: `p20`, `p35`, `p36`, `a20`, `n09`
- Excluded `multi_passage` candidates: `p04`, `a04`
- Full traversal coverage: `39/39` fixed neutral windows; `311,405/311,405` canonical characters
- Acceptable distinct occurrences: `p20 = 2`, `p35 = 1`, `p36 = 1`, `a20 = 1`, `n09 = 11`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

The `p20` Item 7 and Note 16 sentences are retained separately because either location
independently answers the question. For `n09`, each non-overlapping operational, ERM, Board,
committee, CISO, or CTO statement is an OR-hit alternative when it independently assigns
cybersecurity oversight or management responsibility; semantic duplication is not a reason to
discard a distinct source occurrence.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1145197/000114519726000028/0001145197-26-000028-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1145197/000114519726000028/0001145197-26-000028.txt)
- [Primary 10-K document](https://www.sec.gov/Archives/edgar/data/1145197/000114519726000028/podd-20251231.htm)
- Filing date: `2026-02-18`
- Period of report: `2025-12-31`
- Primary document: `podd-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- SEC-index complete-submission bytes: `40,457,019`
- SEC-index primary-document bytes: `2,085,246`
- Canonical visible-text chars / bytes / lines / SHA-256: `311,405` / `313,181` / `2,776` / `20452e5f82c15da66ddb12f2793227513b86c09406aecdfafefcab1f06844941`

The SEC filing index identifies the accession as Insulet Corporation's Form 10-K and identifies
`podd-20251231.htm` as sequence 1. Command-line SEC delivery returned 403, so the primary document
was loaded directly from the official SEC Archives URL in the user's Chrome session. Raw-file
hashes are not asserted; source identity is accession-pinned and the complete derived canonical
text is hashed.

Canonicalization read the rendered primary document's `document.body.innerText`, replaced
non-breaking spaces, normalized CRLF and horizontal whitespace per rendered line, trimmed rendered
lines, and collapsed runs of three or more newlines to two. It did not use an Item, heading, block,
sentence, repository-pipeline hierarchy, or prior retrieval result. Offsets below are zero-based,
end-exclusive intervals against this exact canonical text. Filing locations were assigned only
after the neutral pass.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 8,000-character slice except the final 7,405-character
remainder.

| Windows | Canonical range | Traversal checkpoint | Status |
|---|---:|---|---|
| W0001–W0005 | `[0, 40000)` | Cover, table of contents, Item 1 business/products/development/manufacturing and regulation; includes `p36-e01` and `p35-e01` | inspected |
| W0006–W0010 | `[40000, 80000)` | Item 1A risk factors through product, regulatory, operational, supplier, IP, and international risks | inspected |
| W0011–W0015 | `[80000, 120000)` | Remaining Item 1A financial, market, legal, tax, cybersecurity, and general risks | inspected |
| W0016–W0020 | `[120000, 160000)` | End Item 1A; Items 1B–7 including all Item 1C governance occurrences and MD&A through operating cash flow | inspected |
| W0021–W0025 | `[160000, 200000)` | Item 7 capital spending and legal proceedings; Item 7A; Item 8 index, audit reports, statements, and Notes 1–2; includes `a20-e01` and `p20-e01` | inspected |
| W0026–W0030 | `[200000, 240000)` | Notes 2–11 covering policies, segments, revenue, receivables, inventory, cloud costs, PP&E, goodwill, investments, and accrued liabilities | inspected |
| W0031–W0035 | `[240000, 280000)` | Notes 12–22 and Items 9–9A; includes the Note 16 `p20-e02` occurrence | inspected |
| W0036–W0039 | `[280000, 311405)` | Items 9B–16, exhibit index, signatures, and power of attorney through filing page 81 | inspected |

Coverage checks: W0001 starts at 0, W0039 ends at 311,405, every window starts at the prior
window's end, overlap is zero, and the sum of window lengths is 311,405. The canonical text
contains the filing's final `POWER OF ATTORNEY AND SIGNATURES` section and no truncation marker.

After the sequential pass, full-text cross-checks covered EOFlow/award/appeal/ability to satisfy;
EVOLUTION 2/STRIVE/Omnipod 6/IDE; CGM/glucose/predict/adjust; capital expenditures/Costa
Rica/Malaysia; and cybersecurity/ERM/Board/NGR/CISO/CTO/committee/incident/remediation terms. No
additional distinct source occurrence independently satisfied the applicable question contract.

## Candidate findings

### `p20` — keep question; add Note 16 occurrence

- Candidate ID: `p20`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `o`
- Round 1 reviewer comment:
- Round 1 question: `What threatens collection of the EOFlow trade-secret award?`
- Proposed question change: none
- Proposed query type: `passage`
- Acceptable occurrence count: `2`

#### `p20-e01`

- Filing location: Item 7, Liquidity and Capital Resources → Legal Proceedings
- Window / canonical line / offsets: `W0021` / `839` / `[167285, 167453)`
- Character count / exact count: `168` / `1`
- Snippet SHA-256: `4f9cff35b9e6cc2556ad6034b3374741b54c0f1e42056b31dcd66730e4b44ad3`

> We have not recorded the damages awarded in our consolidated statements of income as EOFlow has appealed and EOFlow’s ability to satisfy the damages award is uncertain.

#### `p20-e02`

- Filing location: Item 8, Note 16 → Legal Proceedings
- Window / canonical line / offsets: `W0032` / `1790` / `[255412, 255599)`
- Character count / exact count: `187` / `1`
- Snippet SHA-256: `c361684f5103a87711dc2744b20944530d5117f75680794af0191b612b3f0f89`

> The Company has not recorded the damages awarded in the Company’s consolidated statements of income, as EOFlow has appealed and EOFlow’s ability to satisfy the damages award is uncertain.

Rejected near-matches include the jury verdict, injunction, reduced award, cross-appeal, and
partial-stay statements when they do not independently state both collection threats.

### `p35` — rewrite to one explicit EVOLUTION 2 timeline

- Candidate ID: `p35`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 reviewer comment: `milestone 應該要更多時間軸過去現在未來，需要多個 evidence 組合`
- Round 1 question: `Insulet next-generation insulin automation development milestones`
- Proposed revised question: `What milestone did Insulet reach for EVOLUTION 2 in 2025, and what did it plan for 2026?`
- Proposed query type: `factoid` (changed from `passage`)
- Proposed answer requirement: one occurrence must state both 2025 enrollment completion and the planned 2026 U.S. IDE pivotal study
- Acceptable occurrence count: `1`

#### `p35-e01`

- Filing location: Item 1, Business → Data Management
- Window / canonical line / offsets: `W0004` / `300` / `[24455, 24644)`
- Character count / exact count: `189` / `1`
- Snippet SHA-256: `e603f502b1c75ce2982586af9212e57ca730fdfa26e6fca430fe34db5ca5095c`

> In 2025, we completed enrollment for EVOLUTION 2, our safety and feasibility study for FCL (T2) and we plan to start the U.S. investigational device exemption (“IDE”) pivotal study in 2026.

The revision turns the broad Round 1 milestone label into the exact past-to-future timeline the
evidence supports. Item 7 repeats enrollment completion but omits the 2026 plan, so it is not an
independently sufficient alternative. STRIVE and Omnipod 6 describe different programs.

### `p36` — rewrite to the automated dosing response

- Candidate ID: `p36`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 reviewer comment: `evidence 只回答 receive 沒有回答 response, 這題不是分開的兩件事，但需要多個 evidence 才可以正確回答`
- Round 1 question: `How does Omnipod 5 receive glucose readings and respond?`
- Proposed revised question: `How does Omnipod 5 use glucose readings to adjust insulin dosing?`
- Proposed query type: `passage`
- Proposed answer requirement: one occurrence must explain prediction from glucose values and automatic dosing adjustment
- Acceptable occurrence count: `1`

#### `p36-e01`

- Filing location: Item 1, Business → Diabetes Management Challenges
- Window / canonical line / offsets: `W0002` / `204` / `[14411, 14546)`
- Character count / exact count: `135` / `1`
- Snippet SHA-256: `85e03317c323a1ce6e4fd6e89e45127ec47602aeee5d57c2e0c62f788c66d457`

> The embedded algorithm utilizes these glucose values to predict glucose levels into the future and automatically adjusts insulin dosing

The original question needs receipt plus response, but no 50–200-character occurrence
independently answers both. This revision keeps the automated-response mechanism. The Bluetooth
sentence answers only receipt; the continuation after the SEC-rendered page number adds intended
clinical effects, not another adjustment mechanism.

### `a20` — rewrite to the cause of the spending increase

- Candidate ID: `a20`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 reviewer comment: `query 問單一問題，看是資本增加原因，或是有哪些工廠擴建專案之類的`
- Round 1 question: `2025 capital spending increase and associated factory expansion projects`
- Proposed revised question: `What investments primarily drove Insulet’s $66.7 million increase in capital expenditures in 2025?`
- Proposed query type: `passage`
- Proposed answer requirement: one occurrence must identify both the Costa Rica plant investment and additional Malaysia machinery/equipment
- Acceptable occurrence count: `1`

#### `a20-e01`

- Filing location: Item 7, Liquidity and Capital Resources → Investing Activities → Capital Spending
- Window / canonical line / offsets: `W0021` / `791` / `[161437, 161637)`
- Character count / exact count: `200` / `1`
- Snippet SHA-256: `f33d2bf1570c3a7ed7a6c756bff8a18c913de5ec899f2b25c34a2ae6fc34bc56`

> $66.7 million increase primarily related to the investment in our third manufacturing plant in Costa Rica and the purchase of additional machinery and equipment for our Malaysia manufacturing facility

This is exactly 200 canonical characters and therefore does not relax the global limit. Amount-only
comparisons, 2026 expectations, and general facility descriptions do not independently answer why
2025 capital spending increased.

### `n09` — keep question; retain all independently sufficient responsibility spans

- Candidate ID: `n09`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1: not applicable (new intent-first candidate)
- Question: `How is responsibility for cybersecurity risk oversight allocated at Insulet?`
- Query type: `passage`
- Answer requirement: one occurrence must explain allocation of cybersecurity oversight or management responsibility; generic importance is partial
- Acceptable occurrence count: `11`

| ID | Responsibility allocation | Window / line / offsets | Chars | SHA-256 |
|---|---|---|---:|---|
| `n09-e01` | Cybersecurity team assesses, monitors, and manages risk | `W0016` / 571 / `[125510, 125658)` | 148 | `04afd6634b180586ece4d184a131a897e6f37d340e93533b3952611662c30b6c` |
| `n09-e02` | Cybersecurity team leaders maintain the risk register and prioritize threats | `W0016` / 571 / `[125932, 126066)` | 134 | `a818185b6886789c3e75a680cbbb9a643c1e5cbb19e80fe9553b2be2df758b5e` |
| `n09-e03` | Cross-functional team reviews and remediates vulnerability findings | `W0016` / 578 / `[127464, 127638)` | 174 | `af951611756542008c50c37b108166e6ffa4d07bfa2ade11ab3572043ac17f05` |
| `n09-e04` | Security operations team initially reviews and rates incidents | `W0017` / 584 / `[130771, 130876)` | 105 | `17f1a1ba95cc2fa4462c77aef2f60ff27116130e722c259969d6df6245d24a8e` |
| `n09-e05` | ERM function annually identifies and assesses enterprise cyber risk | `W0017` / 585 / `[131702, 131870)` | 168 | `9c7ec9ec8f76d75871c4416ee1441e9a2ff5d860c9bbb2221007db59513f8ecf` |
| `n09-e06` | Board oversees management's cyber-risk processes | `W0017` / 588 / `[132551, 132729)` | 178 | `aaa40df7aefc993d379e63a92cdca866c28037ecd2b72bdedae1f53dbeddc88d` |
| `n09-e07` | NGR Committee has primary cybersecurity oversight responsibility | `W0017` / 591 / `[132825, 132922)` | 97 | `b73b0842ad7db613e54bbf8848b1861eb31288015f608de205c8a6a085ac1ece` |
| `n09-e08` | CISO leads the cybersecurity organization | `W0017` / 592 / `[133414, 133586)` | 172 | `26c47fc167400e6f45401c708b9a2e8cd8f9da22663f4624faab457485957d5d` |
| `n09-e09` | CISO reports to CTO and develops/implements the program | `W0017` / 592 / `[133587, 133729)` | 142 | `e223d9cdb45c20855697565fa61a82972471df893bfb9f583d73c6693fb11631` |
| `n09-e10` | CTO prioritizes cybersecurity across technical functions | `W0017` / 593 / `[134200, 134351)` | 151 | `c6b10e6b236f39649eb9e3934a95d4a5d35b2a438d8b9a843305158c43f869d4` |
| `n09-e11` | CTO and CISO co-chair the Technology Risk Committee | `W0017` / 593 / `[134492, 134635)` | 143 | `0ced7684fa94ea9425a637d32a1b4ccca7114aff6c2a4ce765b5b67e124adb1d` |

Exact snippets and acceptance reasons are recorded in `T15_PODD.json`. They are non-overlapping
source spans, not alternate substring boundaries around the same statement. Reporting-only
sentences, generic controls/certifications/training/insurance, the non-self-contained embedded
product-team sentence, and the CIRT membership list that cannot fit completely under 200 characters
were not accepted.

## Round 2 assembly recommendation

This ticker result proposes questions and evidence only. It does not assign a human
`round2_decision` or reviewer comment. During final Round 2 assembly:

1. Preserve the Round 1 question, decision, and comment columns for comparison.
2. Put `candidate_id` immediately before `round2_decision`.
3. Keep the Round 2 decision and reviewer-comment columns empty.
4. For `p20`, retain both Item 7 and Note 16 occurrences as OR alternatives.
5. For `p35`, `p36`, and `a20`, use the proposed revised questions and requirements.
6. For `n09`, retain all 11 independently sufficient non-overlapping occurrences as OR alternatives.
7. Do not add `p04` or `a04`; they belong to the separate `multi_passage` dataset.

## Open human decisions

- Whether the `p35` EVOLUTION 2 past-to-future timeline is sufficiently rich after narrowing from
  the broader next-generation-program wording.
- Whether `p36` should keep the automated-response half, as proposed, or instead be rewritten to
  the Bluetooth receipt mechanism.
- Whether the causal wording for `a20` is preferable to a question that asks only which factory
  expansion projects were funded.
- Whether `n09` should count the operational vulnerability and incident-response allocations as
  acceptable answers to the broad oversight question, or narrow the question to Board and executive
  governance before Round 2 assembly.
