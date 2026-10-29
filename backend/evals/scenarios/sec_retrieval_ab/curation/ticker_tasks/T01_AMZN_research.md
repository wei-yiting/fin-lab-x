# T01 AMZN — pipeline-independent filing research

Research date: 2026-08-27

Scope: FY2025 Form 10-K, active non-`multi_passage` candidates only

Human review fields: not assigned in this note

## Filing identity and official sources

- Ticker / CIK: `AMZN` / `0001018724`
- Accession: `0001018724-26-000004`
- Period of report: `2025-12-31`
- Filing date: `2026-02-06`
- Primary document: `amzn-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/0001018724-26-000004-index.htm)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/0001018724-26-000004.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm)
- [SEC submissions metadata](https://data.sec.gov/submissions/CIK0001018724.json)

The complete submission was fetched directly from SEC Archives. Its first `<DOCUMENT>` has
`<TYPE>10-K`, `<SEQUENCE>1`, and `<FILENAME>amzn-20251231.htm`; only that document was used.

## Pipeline-independent traversal method

No `sec_text_pipeline`, repository Item/block/unit hierarchy, generated markdown, or existing
retrieval result was used to traverse the filing.

1. Extract the primary `<TYPE>10-K` document from the accession-pinned complete submission.
2. Remove non-visible `head`, `script`, `style`, `noscript`, `template`, `display:none`,
   `visibility:hidden`, and `ix:hidden` content.
3. Decode HTML entities, replace non-breaking spaces, remove zero-width spaces, and collapse
   whitespace. No Item, section, block, or semantic hierarchy was introduced.
4. Traverse the resulting canonical visible text sequentially in fixed, non-overlapping
   4,000-character windows. Only after completing that pass, audit occurrences relevant to the
   three questions.

Reproducibility hashes:

| Artifact | SHA-256 |
|---|---|
| Complete submission bytes | `9618be5f7d5c24dd98f262a06d8f38f487a008cee59fc771c98c8ecafd08f6bd` |
| Extracted primary 10-K HTML bytes | `279c3ecd3bb5e15bbc650175339738fd4fb93dd6975b7360a1131518a02f70c5` |
| Canonical visible-text bytes | `1959bbbce1fd4c1c7ebbc752ac5cb9f3f57ebfe7ca7ae0987949d09e969aee64` |

### Coverage ledger

- Canonical text: `283,477` Unicode characters (`284,884` UTF-8 bytes)
- Window size: `4,000` characters
- Window count: `71`
- Covered characters: `283,477`
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
| W51–W60 | `[200000, 240000)` | inspected |
| W61–W70 | `[240000, 280000)` | inspected |
| W71 | `[280000, 283477)` | inspected |

## Active candidate inventory

| Candidate | Round-1 question | Round-1 issue | Research disposition |
|---|---|---|---|
| `p22` | Factors behind Amazon's 2025 overseas retail and cloud revenue gains | Combines International and AWS drivers | Narrow to AWS only |
| `p37` | How do shoppers reach Amazon offerings, and which electronics does it make? | Combines access channels and devices | Narrow to devices only |
| `a22` | How does Amazon account for satellite broadband development before and after viability? | Existing snippet covers only the after-viability half | Original contract is not satisfiable within 50–200 characters; narrow to the capitalization trigger |

`p07` and `a07` are excluded because they are `multi_passage`; `p39` is excluded because its
round-1 decision is `x`.

## Candidate findings

### p22

Proposed revised question:

> What primarily drove AWS sales growth in 2025?

Why this revision: it removes the International-sales sub-question and keeps the original
intent-first revenue-growth intent. The wording also avoids the ambiguous word “overseas,” since
AWS is a global segment rather than an overseas retail segment.

Acceptable OR alternatives: **1**

#### p22-e01

- Document: `amzn-20251231.htm`
- Section context: Item 7 → Results of Operations → Net Sales
- Canonical offset: `[113141, 113262)`
- Length: `121` characters
- Window: W29
- Snippet SHA-256: `9f67ed8f44c9ceddff59fa176a28203379a920d0a557116d7ec365497abb2e1d`
- [SEC source](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm)

> AWS sales increased 20% in 2025, compared to the prior year. The sales growth primarily reflects increased customer usage

The snippet ends at a complete answer clause and retains the AWS subject; extending it through the
full source sentence would add the offsetting pricing detail and exceed 200 characters. Full-filing
occurrence audit found no other distinct disclosure that independently states the primary driver
of AWS's 2025 sales growth. Segment tables repeat the sales amount, not the driver.

### p37

Proposed revised question:

> Which electronic devices does Amazon manufacture and sell?

Why this revision: it removes the access-channel sub-question and follows the round-1 request to
retain only the electronics intent.

Acceptable OR alternatives: **1**

#### p37-e01

- Document: `amzn-20251231.htm`
- Section context: Item 1 → Business → Consumers
- Canonical offset: `[7599, 7715)`
- Length: `116` characters
- Window: W02
- Snippet SHA-256: `3816c81e7249031cf6bb4028ec956686eb67ff703001c0c3f00178244ff607ca`
- [SEC source](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm)

> We also manufacture and sell electronic devices, including Kindle, Fire tablet, Fire TV, Echo, Ring, Blink, and eero

Each named device occurs only in this source sentence in the canonical filing text. Note 1 has a
second, 48-character occurrence — “We also manufacture and sell electronic devices.” at
`[154057, 154105)` — but it neither names the devices nor reaches the 50-character minimum, so it
is not independently sufficient evidence for the revised question.

### a22

Original-contract finding: **question/evidence contract issue**.

The original question requires both accounting states. The source's before-viability sentence is
225 characters (`[119762, 119987)`), while the complete before-and-after pair is 345 characters
(`[119762, 120107)`). Therefore no independently sufficient canonical 50–200 character span can
answer the original question. Keeping the question would require `multi_passage`, truncation, or a
relaxed limit; all three are outside the active-pool contract.

Proposed revised question:

> When will Amazon begin capitalizing certain satellite broadband development costs?

Why this revision: it makes the existing after-viability disclosure independently answerable as a
single passage while preserving the investor-relevant accounting threshold.

Acceptable OR alternatives for the revised question: **1**

#### a22-e01

- Document: `amzn-20251231.htm`
- Section context: Item 7 → Results of Operations → Operating Expenses → Technology and Infrastructure
- Canonical offset: `[119988, 120107)`
- Length: `119` characters
- Windows: W30–W31 boundary
- Snippet SHA-256: `44e537dd3f5861836d078d5375b0b50010e8d1110a720a15a1fa7b0923b86029`
- [SEC source](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm)

> We will capitalize certain of these costs once the service achieves commercial viability, including sales to customers.

Related but inadmissible source occurrences:

| Offset | Length | Disclosure | Reason not an acceptable alternative |
|---:|---:|---|---|
| `[119762, 119987)` | 225 | Expenses most satellite-network development costs, including production, launch, payroll, and launch deposits | Exceeds 200 characters and answers only the original question's before-state |
| `[179968, 180079)` | 111 | Expenses satellite-network launch-service deposits upon launch to Technology and infrastructure | Does not answer the revised capitalization-trigger question |
| `[187808, 188058)` | 250 | Reclassifies launch-service deposits to construction-in-progress once commercially viable | Semantically supports the trigger but exceeds 200 characters; do not relax or create a fragment |

## Round-2 assembly recommendation

This note proposes revised questions and evidence, but does not assign `round2_decision` or a new
human review comment. When the Round-2 review artifacts are assembled, carry forward each
round-1 question, evidence, decision, and issue comment beside these proposed revisions, and leave
the new review fields blank.
