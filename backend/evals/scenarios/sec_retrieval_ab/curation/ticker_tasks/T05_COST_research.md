# T05 COST — pipeline-independent filing research

Research date: 2026-08-27

Scope: FY2025 Form 10-K, active non-`multi_passage` candidates only

Human review fields: not assigned in this note

## Filing identity and official sources

- Ticker / CIK: `COST` / `0000909832`
- Accession: `0000909832-25-000101`
- Period of report: `2025-08-31`
- Filing date: `2025-10-08`
- Primary document: `cost-20250831.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- [SEC filing index](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/0000909832-25-000101-index.htm)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/0000909832-25-000101.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/cost-20250831.htm)
- [SEC submissions metadata](https://data.sec.gov/submissions/CIK0000909832.json)

The complete submission was fetched directly from SEC Archives. Its first `<DOCUMENT>` has
`<TYPE>10-K`, `<SEQUENCE>1`, and `<FILENAME>cost-20250831.htm`; only that document was used.

## Pipeline-independent traversal method

No `sec_text_pipeline`, repository Item/block/unit hierarchy, generated markdown, or existing
retrieval result was used to traverse the filing.

1. Extract the primary `<TYPE>10-K` document from the accession-pinned complete submission.
2. Remove non-visible `head`, `script`, `style`, `noscript`, `template`, `display:none`, and
   `ix:hidden` content.
3. Decode HTML entities, replace non-breaking spaces, preserve neutral paragraph/table
   separators, and collapse transport whitespace. No Item, section, block, sentence, or semantic
   hierarchy was introduced.
4. Traverse the resulting canonical visible text sequentially in fixed, non-overlapping
   4,000-character windows. Only after completing that pass, audit occurrences relevant to the
   three questions.

An initial whitespace-only extraction inserted spaces at some inline-XBRL boundaries. Before
recording offsets, canonicalization was corrected to preserve inline text adjacency. Removing
whitespace, table separators, and the direct-document title produces the same visible character
sequence, so the correction changed neither traversal order nor semantic coverage.

Reproducibility hashes:

| Artifact | SHA-256 |
|---|---|
| Complete submission bytes | `0281da24f7cdf55c0a30258dd1c0046da4835802bcb03d41e1a7bd90b5009270` |
| Extracted primary 10-K HTML bytes | `104bf0ecfa41acb44fb81149c630bdd0e58336a425d3d294d0b48ed6adec2b29` |
| Canonical visible-text bytes | `b638124a26158007f5b23e8c749affa8761cf5dc7d51d7f718c9de5e3561df0d` |

### Coverage ledger

- Canonical text: `218,693` Unicode characters (`219,401` UTF-8 bytes)
- Window size: `4,000` characters
- Window count: `55`
- Covered characters: `218,693`
- Gap count: `0`
- Overlap count: `0`
- Offsets below are zero-based half-open intervals `[start, end)` in this canonical text.

| Windows | Offset coverage | Traversal result |
|---|---:|---|
| W01–W10 | `[0, 40000)` | inspected |
| W11–W20 | `[40000, 80000)` | inspected |
| W21–W30 | `[80000, 120000)` | inspected |
| W31–W40 | `[120000, 160000)` | inspected |
| W41–W50 | `[160000, 200000)` | inspected |
| W51–W54 | `[200000, 216000)` | inspected |
| W55 | `[216000, 218693)` | inspected |

## Active candidate inventory

| Candidate | Round-1 question | Round-1 issue | Research disposition |
|---|---|---|---|
| `p27` | Costco fiscal 2026 capital spending and warehouse expansion plans | `?` — asks for two information needs | Narrow to the fiscal 2026 capital-spending amount and change to `factoid` |
| `p44` | Impact of one-percentage-point rate shift on Costco investments | `o` — no issue recorded | Preserve the question and evidence contract |
| `n05` | What drove Costco's comparable-sales growth in fiscal 2025? | New intent-first candidate | Keep question; add every independently sufficient occurrence |

`p12` and `a12` are excluded because they are `multi_passage`; `a12` also has a round-1 decision
of `x`.

## Candidate findings

### p27

Round-1 reviewer comment:

> 題目應該只問單一產品，capital spending 或 warehouse expansion plans

Proposed revised question:

> How much does Costco intend to spend on capital expenditures in fiscal 2026?

Proposed query type: `factoid` (changed from `passage`)

Why this revision: the Round-1 query combined capital spending and warehouse expansion. The
revised query asks only for the disclosed fiscal 2026 capital-spending amount, which one sentence
answers independently.

Acceptable OR alternatives: **1**

#### p27-e01

- Document: `cost-20250831.htm`
- Section context: Item 7 → Liquidity and Capital Resources → Capital Expenditure Plans
- Canonical offset: `[103987, 104114)`
- Length: `127` characters
- Windows: W26–W27 boundary
- Snippet SHA-256: `ad674927521e72fb3f4d886bb9df53a68ab541b64db7228cc968e2043f11d212`
- [SEC source](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/cost-20250831.htm)

> In 2025, we spent $5,498 on capital expenditures, and it is our current intention to spend $6,000 to $6,500 during fiscal 2026.

Full-filing audit examined seven capital-expenditure-related occurrences. Generic risk statements,
historical investing cash flow, property-additions tables, capital-use context, and the
forward-looking disclaimer do not state the intended fiscal 2026 amount and therefore are not
acceptable alternatives.

### p44

Proposed revised question: unchanged from Round 1.

> Impact of one-percentage-point rate shift on Costco investments

Acceptable OR alternatives: **1**

#### p44-e01

- Document: `cost-20250831.htm`
- Section context: Item 7A → Interest Rate Risk
- Canonical offset: `[111712, 111846)`
- Length: `134` characters
- Window: W28
- Snippet SHA-256: `af2db2630c8895b9d501e9c96d12afbb50e4f4eb3d3cbe063d2faeaa017d2099`
- [SEC source](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/cost-20250831.htm)

> A 100 basis point change in interest rates as of the end of 2025 would have had an immaterial incremental change in fair market value.

This is the only distinct filing occurrence that independently states the one-percentage-point
interest-rate sensitivity result.

### n05

Proposed question: unchanged.

> What drove Costco's comparable-sales growth in fiscal 2025?

Acceptable OR alternatives: **3**

The first two occurrences explain Costco's disclosed operating mechanisms for comparable-sales
growth in the FY2025 MD&A; the third quantifies the observed 2025 changes. Under the agreed
inclusive OR-hit contract, all three independently answer the question and are retained even
though the first and third overlap semantically.

#### n05-e01

- Document: `cost-20250831.htm`
- Section context: Item 7 → Overview
- Canonical offset: `[83984, 84145)`
- Length: `161` characters
- Windows: W21–W22 boundary
- Snippet SHA-256: `6ab050e604d2c92800e65dc914e2ba9db6f4a13fd0c7e8100102f082a340fdc7`
- [SEC source](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/cost-20250831.htm)

> Comparable sales growth is achieved through increasing shopping frequency from new and existing members and the amount they spend on each visit (average ticket).

#### n05-e02

- Document: `cost-20250831.htm`
- Section context: Item 7 → Overview
- Canonical offset: `[84633, 84829)`
- Length: `196` characters
- Window: W22
- Snippet SHA-256: `cdfc17bb8479bb76c3dfadbb3e9dcc6c876844aef4139d5014b650b17c3683a9`
- [SEC source](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/cost-20250831.htm)

> Generating comparable sales growth is foremost a question of making available the right merchandise at the right prices, a skill that we believe we have repeatedly demonstrated over the long-term.

#### n05-e03

- Document: `cost-20250831.htm`
- Section context: Item 7 → Results of Operations → Net Sales
- Canonical offset: `[94148, 94270)`
- Length: `122` characters
- Window: W24
- Snippet SHA-256: `731f98f603d1d6efd969787d9d1e78a68d6f22b3133e9cd769ba586b7baed7cd`
- [SEC source](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/cost-20250831.htm)

> Comparable sales were positively impacted by increases of 5% in shopping frequency and approximately 1% in average ticket.

Full-filing audit examined fifteen comparable-sales-related occurrences. The remaining occurrences
are forward-looking boilerplate, risk-factor disclosures, a definition, profitability consequences,
or percentage-only tables/highlights; none independently explains the drivers.

## Round-2 assembly recommendation

This note proposes revised questions and evidence, but does not assign `round2_decision` or a new
human review comment. When the Round-2 review artifacts are assembled, carry forward each
round-1 question, evidence, decision, and issue comment beside these proposed revisions, and leave
the new review fields blank.
