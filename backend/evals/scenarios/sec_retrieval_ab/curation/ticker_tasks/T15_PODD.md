# T15 PODD — pipeline-independent filing traversal

## Scope and result

- Ticker: `PODD`
- Fiscal year: `2025`
- Accession: `0001145197-26-000028`
- Active non-`multi_passage` candidates: `p20`, `p35`, `p36`, `a20`, `n09`
- Excluded `multi_passage` candidates: `p04`, `a04`
- Full traversal coverage: `39/39` fixed neutral windows; `311,405/311,405` canonical characters
- Acceptable distinct occurrences: `p20 = 2`, `p35 = 2`, `p36 = 1`, `a20 = 1`, `n09 = 1`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

The `p20` Item 7 and Note 16 sentences are retained separately because either location
independently answers the question. The corrected `p35` has two independently sufficient
enrollment-milestone occurrences in Items 1 and 7. The corrected `n09` has one historical-impact
disclosure in Item 1C; operational and governance statements do not answer that question.

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
| W0016–W0020 | `[120000, 160000)` | End Item 1A; Items 1B–7 including `n09-e01`, the Item 7 `p35-e02`, and MD&A through operating cash flow | inspected |
| W0021–W0025 | `[160000, 200000)` | Item 7 capital spending and legal proceedings; Item 7A; Item 8 index, audit reports, statements, and Notes 1–2; includes `a20-e01` and `p20-e01` | inspected |
| W0026–W0030 | `[200000, 240000)` | Notes 2–11 covering policies, segments, revenue, receivables, inventory, cloud costs, PP&E, goodwill, investments, and accrued liabilities | inspected |
| W0031–W0035 | `[240000, 280000)` | Notes 12–22 and Items 9–9A; includes the Note 16 `p20-e02` occurrence | inspected |
| W0036–W0039 | `[280000, 311405)` | Items 9B–16, exhibit index, signatures, and power of attorney through filing page 81 | inspected |

Coverage checks: W0001 starts at 0, W0039 ends at 311,405, every window starts at the prior
window's end, overlap is zero, and the sum of window lengths is 311,405. The canonical text
contains the filing's final `POWER OF ATTORNEY AND SIGNATURES` section and no truncation marker.

After the sequential pass, full-text cross-checks covered EOFlow/award/appeal/ability to satisfy;
EVOLUTION 2/STRIVE/Omnipod 6/IDE; CGM/glucose/predict/adjust; capital expenditures/Costa
Rica/Malaysia; and cybersecurity/incident/materially affected/internal-control terms. No
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

### `p35` — rewrite to one EVOLUTION 2 milestone

- Candidate ID: `p35`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `?`
- Round 1 reviewer comment: `milestone 應該要更多時間軸過去現在未來，需要多個 evidence 組合`
- Round 1 question: `Insulet next-generation insulin automation development milestones`
- Proposed revised question: `What milestone did Insulet reach for EVOLUTION 2 in 2025?`
- Proposed query type: `factoid` (changed from `passage`)
- Proposed answer requirement: one occurrence must state that Insulet completed or finished enrollment for EVOLUTION 2 in 2025
- Acceptable occurrence count: `2`

#### `p35-e01`

- Filing location: Item 1, Business → Data Management
- Window / canonical line / offsets: `W0004` / `300` / `[24455, 24537)`
- Character count / exact count: `82` / `1`
- Snippet SHA-256: `6b199169439f07346044f3a0364d488bb99791c272b1d8d940da004f94bca206`

> In 2025, we completed enrollment for EVOLUTION 2, our safety and feasibility study

This is the shortest self-contained semantic unit above the 50-character minimum. The following
2026 U.S. IDE pivotal-study plan is a separate intent and is excluded.

#### `p35-e02`

- Filing location: Item 7, Management's Discussion and Analysis → Overview
- Window / canonical line / offsets: `W0018` / `639` / `[140970, 141116)`
- Character count / exact count: `146` / `1`
- Snippet SHA-256: `d5ed75a05213698a94532c308029ecebe0bc8cf64310061c84fc2b69cbc50e22`

> In 2025, we also completed STRIVE, our pivotal study for the next generation hybrid closed loop system, and we finished enrollment for EVOLUTION 2

The preceding STRIVE clause is retained because this is the shortest contiguous source span that
keeps both the explicit 2025 time anchor and the EVOLUTION 2 enrollment milestone. STRIVE and
Omnipod 6 disclosures without the EVOLUTION 2 milestone are rejected.

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

### `n09` — replace governance question with incident-impact fact

- Candidate ID: `n09`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1: not applicable (new intent-first candidate)
- Proposed question: `Has Insulet experienced cybersecurity incidents that materially affected the company?`
- Proposed query type: `factoid`
- Proposed answer requirement: one occurrence must state whether previous cybersecurity incidents materially affected Insulet
- Acceptable occurrence count: `1`

#### `n09-e01`

- Filing location: Item 1C, Cybersecurity → Risk Management and Strategy
- Window / canonical line / offsets: `W0017` / `586` / `[132068, 132234)`
- Character count / exact count: `166` / `1`
- Snippet SHA-256: `62fc7ef5eff5b70569ea49b199cf2d38cee34bef0214447959098889f54a7e19`

> We currently do not believe that risks from cybersecurity threats, including as a result of any previous cybersecurity incidents, have materially affected the Company

The evidence supports the issuer-qualified answer: No—Insulet says it currently does not believe
so. The 234-character source sentence lists business strategy, results of operations, and financial
condition; the canonical snippet preserves the company-level conclusion within the global
200-character limit. Prospective risk warnings, incident-response procedures, governance
allocations, and Item 9A internal-control language are not acceptable occurrences.

## Round 2 assembly recommendation

This ticker result proposes questions and evidence only. It does not assign a human
`round2_decision` or reviewer comment. During final Round 2 assembly:

1. Preserve the Round 1 question, decision, and comment columns for comparison.
2. Put `candidate_id` immediately before `round2_decision`.
3. Keep the Round 2 decision and reviewer-comment columns empty.
4. For `p20`, retain both Item 7 and Note 16 occurrences as OR alternatives.
5. For `p35`, retain both Item 1 and Item 7 occurrences as OR alternatives; use the proposed revised question and requirement.
6. For `p36` and `a20`, use the proposed revised questions and requirements.
7. For `n09`, use the proposed factoid and retain only `n09-e01`; remove the 11 governance spans from the prior question.
8. Do not add `p04` or `a04`; they belong to the separate `multi_passage` dataset.

## Open human decisions

- Whether `p36` should keep the automated-response half, as proposed, or instead be rewritten to
  the Bluetooth receipt mechanism.
- Whether the causal wording for `a20` is preferable to a question that asks only which factory
  expansion projects were funded.
- Whether the issuer-qualified wording in `n09` should be carried explicitly into the reference
  answer so the dataset does not overstate the filing as an independent factual guarantee.
