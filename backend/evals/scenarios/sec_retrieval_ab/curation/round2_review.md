# sec_retrieval_ab dataset — Round 2 human review

This surface contains 51 active candidates and 4 reference-only Round-1 rows. Fill only `round2_decision` and `round2_reviewer_comment` in `round2_review.csv`; both fields are intentionally blank.

Every listed Round-2 evidence occurrence is an **OR alternative**: retrieving any one occurrence counts as a hit, and every occurrence must independently satisfy the answer requirement.

## Review order

| group | rows | review expectation |
|---|---:|---|
| Round-1 `o` | 13 | Re-review the current question and complete OR-set |
| Round-1 `?` | 28 | Compare the correction with the original issue |
| New `n01`–`n10` | 10 | First human review |
| Round-1 `!` / `x` | 4 | Reference only; excluded from active pool |

## Candidate p20 — PODD

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `intent_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | What threatens collection of the EOFlow trade-secret award? | What threatens collection of the EOFlow trade-secret award? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Legal Proceedings—In December 2024, a jury found that EOFlow Co., Ltd. (“EOFlow”) and several other defendants misappropriated certain of our trade secrets and awarded us $452 million in damages. The Court subsequently upheld the jury verdict and further entered a permanent worldwide injunction. In view of the scope of the permanent injunction, the Court reduced our monetary award to $59.4 million to avoid a double recovery. **We have not recorded the damages awarded in our consolidated statements of income as EOFlow has appealed and EOFlow’s ability to satisfy the damages award is uncertain.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must identify EOFlow's appeal and uncertain ability to satisfy the damages award as threats to collection.
- Curation note: This passage identifies a company-specific legal judgment and tests retrieval of appeal and collectability risks that could prevent Insulet from realizing the award.
- Change summary: The approved question remains unchanged. After the Item 8 exclusion, the Item 7 occurrence states both EOFlow's appeal and its uncertain ability to satisfy the award.

#### Acceptable OR alternatives

**OR alternative 1** — `PODD-2025-167285`

- Store Item: `Item 7`
- Location: Liquidity and Capital Resources / Legal Proceedings
- Acceptance reason: Directly identifies both threats to collection in Item 7: EOFlow's appeal and uncertain ability to pay.

> **We have not recorded the damages awarded in our consolidated statements of income as EOFlow has appealed and EOFlow’s ability to satisfy the damages award is uncertain.**

#### Evidence provenance

- T2: Item 8 is outside retrieval scope; the Item 7 occurrence remains.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p25 — CAT

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How much could tariffs cost without planned mitigation? | How much could tariffs cost without planned mitigation? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `CAT / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Based on the incremental tariffs announced in 2025 and in place by January 29, 2026, we expect the impact from tariffs to be around $2.6 billion in 2026, which is $800 million higher than incurred in 2025. **If we do not take the mitigating actions we plan to take in 2026, the impact from tariffs could be around 20 percent higher.** We remain confident that we will manage the impact of tariffs over time.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state the relative tariff impact if Caterpillar does not take its planned 2026 mitigation actions; an inferred dollar amount is not acceptable.
- Curation note: This passage quantifies Caterpillar’s 2026 tariff exposure and the additional downside if its countermeasures are not implemented.
- Change summary: Round 1 was approved, and full traversal found one independently sufficient occurrence expressing the no-mitigation impact as around 20 percent higher.

#### Acceptable OR alternatives

**OR alternative 1** — `CAT-2025-126153`

- Store Item: `Item 7`
- Location: OVERVIEW / Full-Year 2026 Company Trends and Expectations
- Acceptance reason: Directly states the relative tariff impact if Caterpillar does not take its planned 2026 mitigating actions.

> Based on the incremental tariffs announced in 2025 and in place by January 29, 2026, we expect the impact from tariffs to be around $2.6 billion in 2026, which is $800 million higher than incurred in 2025. **If we do not take the mitigating actions we plan to take in 2026, the impact from tariffs could be around 20 percent higher.** We remain confident that we will manage the impact of tariffs over time.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p28 — NEE

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How sensitive were retirement obligations to cost inflation assumptions? | How sensitive were retirement obligations to cost inflation assumptions? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `NEE / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Estimating the amount and timing of future expenditures includes, among other things, making projections of when assets will be retired and ultimately decommissioned and how costs will escalate with inflation. In addition, NEE also makes interest rate and rate of return projections on its investments in determining recommended funding requirements for nuclear decommissioning costs. Periodically, NEE is required to update these estimates and projections which can affect the annual expense amounts recognized, the liabilities recorded and the annual funding requirements for nuclear decommissioning costs. **For example, an increase of 0.25% in the assumed escalation rates for nuclear decommissioning costs would increase NEE’s AROs as of December 31, 2025 by approximately $179 million.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must quantify how a change in the nuclear-decommissioning cost-escalation assumption would affect NEE's retirement obligations.
- Curation note: This passage links NEE’s estimation methodology to a quantified $179 million sensitivity from a 0.25% escalation-rate increase.
- Change summary: Full traversal confirmed that the Round 1 question and evidence remain valid. The filing contains one quantitative occurrence linking a 0.25% increase in the nuclear-decommissioning cost escalation assumption to a $179 million increase in NEE's AROs.

#### Acceptable OR alternatives

**OR alternative 1** — `NEE-2025-240952`

- Store Item: `7`
- Location: Critical Accounting Estimates / Decommissioning and Dismantlement / Nature of Accounting Estimates
- Acceptance reason: Independently states both the change in the cost-inflation assumption and the resulting increase in retirement obligations.

> Estimating the amount and timing of future expenditures includes, among other things, making projections of when assets will be retired and ultimately decommissioned and how costs will escalate with inflation. In addition, NEE also makes interest rate and rate of return projections on its investments in determining recommended funding requirements for nuclear decommissioning costs. Periodically, NEE is required to update these estimates and projections which can affect the annual expense amounts recognized, the liabilities recorded and the annual funding requirements for nuclear decommissioning costs. **For example, an increase of 0.25% in the assumed escalation rates for nuclear decommissioning costs would increase NEE’s AROs as of December 31, 2025 by approximately $179 million.**

#### Evidence provenance

- T1: Re-extracted the filing-store non-breaking space in the date.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p31 — XOM

- Scope: `active`
- FY: `2025`
- Items: Item 1
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How does ExxonMobil cultivate and retain long-tenured career employees? | How does ExxonMobil cultivate and retain long-tenured career employees? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `XOM / 2025 / Item 1. Business`

> Talent development begins with recruiting exceptional candidates and continues with individually planned experiences and training designed to facilitate broad development and a deep understanding of our business across the business cycle. **Our career-oriented approach to talent development results in strong retention and an average length of service of about 30 years for our career employees.** Compensation, benefits, and workplace programs support the Corporation's talent management approach, and are designed to attract and retain employees for a career through compensation that is market competitive, long-term oriented, and highly differentiated by individual performance.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must connect ExxonMobil's career-oriented talent-development approach to employee retention or tenure.
- Curation note: This evidence links individualized development, roughly 30-year average tenure, and performance-based rewards, testing retrieval of ExxonMobil’s specific workforce strategy.
- Change summary: Round 1 approved this question and evidence. Full traversal found one independently sufficient occurrence of the approved retention and tenure answer, so the candidate remains unchanged.

#### Acceptable OR alternatives

**OR alternative 1** — `XOM-2025-009208`

- Store Item: `Item 1`
- Location: Business / talent development
- Acceptance reason: Independently states that the career-oriented talent-development approach produces strong retention and approximately 30 years of average service.

> **Our career-oriented approach to talent development results in strong retention and an average length of service of about 30 years for our career employees.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p38 — COIN

- Scope: `active`
- FY: `2025`
- Items: Item 1
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | What happens to underlying Ether when cbETH changes hands? | What happens to underlying Ether when cbETH changes hands? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `COIN / 2025 / Item 1. Business`

> cbETH is an Ethereum-based “wrapped staking token” that represents ownership of ETH staked through our platform. Eligible customers can obtain cbETH tokens by wrapping their staked ETH or by purchasing cbETH tokens on our exchange or on third-party exchanges. A cbETH holder can sell or transfer their cbETH within the Coinbase app or send cbETH to a self-custodial wallet or to other addresses on the Ethereum blockchain. **Selling or otherwise transferring cbETH automatically transfers ownership of the underlying staked ETH, along with any rewards earned.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must explain what happens to ownership of underlying staked Ether when cbETH is sold or transferred.
- Curation note: This evidence explains cbETH ownership and transfer mechanics, testing retrieval of a product-specific consequence of selling or transferring the token.
- Change summary: Round 1 was approved, and full traversal found one independently sufficient occurrence.

#### Acceptable OR alternatives

**OR alternative 1** — `COIN-2025-038286`

- Store Item: `Item 1`
- Location: Business / Staking
- Acceptance reason: Directly states that transferring cbETH transfers ownership of the underlying staked ETH and its earned rewards.

> **Selling or otherwise transferring cbETH automatically transfers ownership of the underlying staked ETH, along with any rewards earned.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p41 — GOOGL

- Scope: `active`
- FY: `2025`
- Items: Item 1C
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: 但是這個 query 是蠻罕見的問題，不會優先選這題

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Who independently evaluates Alphabet's cyber defenses? | Who independently evaluates Alphabet's cyber defenses? |
| Query type | factoid | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `GOOGL / 2025 / Item 1C. Cybersecurity`

> **Internal Audit maintains a dedicated cybersecurity auditing team that independently tests our cybersecurity controls.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must identify who independently tests Alphabet's cybersecurity controls.
- Curation note: This evidence identifies the specific internal function responsible for independent control testing and tests retrieval of Alphabet’s cybersecurity oversight structure.
- Change summary: Round 1 approved the evidence contract. Full traversal found one independently sufficient occurrence identifying Internal Audit; the Round 1 concern about query frequency remains a human filtering decision.

#### Acceptable OR alternatives

**OR alternative 1** — `GOOGL-2025-123761`

- Store Item: `Item 1C`
- Location: Cybersecurity / governance and oversight
- Acceptance reason: Directly identifies Internal Audit and its dedicated cybersecurity auditing team as the independent tester of Alphabet's cybersecurity controls.

> **Internal Audit maintains a dedicated cybersecurity auditing team that independently tests our cybersecurity controls.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p42 — CAT

- Scope: `active`
- FY: `2025`
- Items: Item 1C
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: 但是這個 query 是很罕見的問題，不會優先選這題，沒什麼評估意義

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How frequently does Caterpillar's IT chief attend Audit Committee meetings? | How frequently does Caterpillar's IT chief attend Audit Committee meetings? |
| Query type | factoid | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `CAT / 2025 / Item 1C. Cybersecurity`

> **The Company’s Chief Information Officer & Senior Vice President, Caterpillar IT (the “CIO”) attends all bimonthly AC meetings and provides cybersecurity updates to the AC and board.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state how frequently Caterpillar's CIO attends Audit Committee meetings.
- Curation note: This evidence provides a company-specific meeting cadence and tests retrieval of Caterpillar's cybersecurity governance practices.
- Change summary: The evidence contract is correct and full traversal found one independently sufficient occurrence. The Round 1 concern is candidate value and remains a human filtering decision.

#### Acceptable OR alternatives

**OR alternative 1** — `CAT-2025-105817`

- Store Item: `Item 1C`
- Location: Cybersecurity Governance
- Acceptance reason: Directly joins the CIO, attendance, Audit Committee meetings and their cadence.

> **The Company’s Chief Information Officer & Senior Vice President, Caterpillar IT (the “CIO”) attends all bimonthly AC meetings and provides cybersecurity updates to the AC and board.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p43 — AXON

- Scope: `active`
- FY: `2025`
- Items: Item 7 | Item 7A
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How much credit could Axon draw at year-end 2025? | How much credit could Axon draw at year-end 2025? |
| Query type | factoid | factoid |
| Evidence occurrences | 1 | 2 |

#### Round-1 evidence

**Original evidence 1** — `AXON / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk`

> **As of the year ended December 31, 2025, there was no amount outstanding under the line of credit, and the available borrowing under the line of credit was $291.1 million.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must state Axon's available borrowing under its line of credit at year-end 2025.
- Curation note: This evidence gives Axon’s exact unused borrowing capacity and tests retrieval of a dated liquidity fact.
- Change summary: The approved question remains unchanged. Two reachable non-Item-8 store occurrences independently report $291.1 million of available borrowing.

#### Acceptable OR alternatives

**OR alternative 1** — `AXON-2025-198921`

- Store Item: `7`
- Location: Liquidity and Capital Resources
- Acceptance reason: Independently states the year-end date and $291.1 million available borrowing.

> **As of December 31, 2025, we had letters of credit outstanding of approximately $8.9 million under the facility and available borrowing of $291.1 million.**

**OR alternative 2** — `AXON-2025-226300`

- Store Item: `7a`
- Location: Interest Rate Risk
- Acceptance reason: Independently states the year-end date and $291.1 million available borrowing.

> **As of the year ended December 31, 2025, there was no amount outstanding under the line of credit, and the available borrowing under the line of credit was $291.1 million.**

#### Evidence provenance

- T1: The canonical visible-text occurrence differed from the filing store only in whitespace; span and snippet were re-extracted as exact store substrings.
- T1: The canonical visible-text occurrence differed from the filing store only in whitespace; span and snippet were re-extracted as exact store substrings.
- T2: The source location is Item 8 and no same-text non-Item-8 label escape exists, so it is excluded from retrieval ground truth.
- T6: The two surviving non-Item-8 occurrences independently state $291.1 million of available borrowing at year-end 2025.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p44 — COST

- Scope: `active`
- FY: `2025`
- Items: Item 7A
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Impact of one-percentage-point rate shift on Costco investments | Impact of one-percentage-point rate shift on Costco investments |
| Query type | factoid | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `COST / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk`

> **A 100 basis point change in interest rates as of the end of 2025 would have had an immaterial incremental change in fair market value.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must state the fair-value effect of a 100-basis-point interest-rate change on Costco's investments at fiscal 2025 year-end.
- Curation note: This evidence quantifies a company-specific sensitivity scenario and tests retrieval of the resulting valuation impact.
- Change summary: The approved question and its sole independently sufficient occurrence remain unchanged.

#### Acceptable OR alternatives

**OR alternative 1** — `COST-2025-111712`

- Store Item: `Item 7A`
- Location: Interest Rate Risk
- Acceptance reason: Directly states that the incremental fair-market-value effect would have been immaterial.

> **A 100 basis point change in interest rates as of the end of 2025 would have had an immaterial incremental change in fair market value.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p45 — DDOG

- Scope: `active`
- FY: `2025`
- Items: Item 7 | Item 7A
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Timing and size of Datadog's 2029 debt issuance | Timing and size of Datadog's 2029 debt issuance |
| Query type | factoid | factoid |
| Evidence occurrences | 1 | 2 |

#### Round-1 evidence

**Original evidence 1** — `DDOG / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk`

> **In December 2024, we issued $1.0 billion aggregate principal amount of the 2029 Notes.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must state both when Datadog issued the 2029 Notes and their aggregate principal amount.
- Curation note: This sentence provides a company-specific issuance date and principal amount, testing retrieval of a precise financing fact.
- Change summary: The approved Round 1 question remains unchanged. After the Item 8 exclusion, the Item 7 and Item 7A filing-store occurrences each state both the issuance timing and principal amount.

#### Acceptable OR alternatives

**OR alternative 1** — `DDOG-2025-245545`

- Store Item: `Item 7`
- Location: —
- Acceptance reason: Independently states December 2024 and $1.0 billion for the 2029 Notes issuance.

> **In December 2024, we issued $1.0 billion aggregate principal amount of the 2029 Notes in a private placement to qualified institutional buyers pursuant to Rule 144A under the Securities Act.**

**OR alternative 2** — `DDOG-2025-259341`

- Store Item: `7a`
- Location: —
- Acceptance reason: Independently states December 2024 and $1.0 billion for the 2029 Notes issuance.

> **In December 2024, we issued $1.0 billion aggregate principal amount of the 2029 Notes.**

#### Evidence provenance

- T1: Re-extracted the Item 7A occurrence to preserve the filing-store non-breaking space after In.
- T2: Item 8 is outside retrieval scope.
- T2: Item 8 is outside retrieval scope.
- T6: Both non-Item-8 copies independently state December 2024 and $1.0 billion for the 2029 Notes issuance.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p48 — PLD

- Scope: `active`
- FY: `2025`
- Items: Item 5 | Item 16
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: 屬於 long-tail 的題目

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Prologis Series Q per-share dividend amount for 2025 | Prologis Series Q per-share dividend amount for 2025 |
| Query type | factoid | factoid |
| Evidence occurrences | 1 | 2 |

#### Round-1 evidence

**Original evidence 1** — `PLD / 2025 / Item 5. Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities`

> **Dividends payable per share were $4.27 for the year ended December 31, 2025.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must identify the Series Q total dividend of $4.27 per share for 2025; a dividend amount for another security is partial.
- Curation note: This evidence states a precise annual per-share dividend and tests retrieval of a company-specific preferred-stock payment.
- Change summary: The approved Round 1 question remains unchanged. The filing store labels the separate Series Q dividend table under Item 16, so the Item 5 sentence and Item 16 table remain OR-hit alternatives.

#### Acceptable OR alternatives

**OR alternative 1** — `PLD-2025-127107`

- Store Item: `Item 5`
- Location: Preferred Stock Dividends
- Acceptance reason: Directly reports the 2025 per-share dividend amount in the Item 5 Series Q paragraph.

> **Dividends payable per share were $4.27 for the year ended December 31, 2025.**

**OR alternative 2** — `PLD-2025-336753`

- Store Item: `16`
- Location: Dividends / Preferred Stock – Series Q
- Acceptance reason: The Item 16 answer span includes the 2025/2024/2023 column headings, identifies Series Q, and reports a total dividend of $4.27 in every displayed year; the shorter store-exact snippet anchors the total-dividend row within that independently sufficient span.

> The following summarizes the taxability of our common and preferred stock dividends for the years ended December 31:
>
>          2025
>
>          2024
>
>          2023
>
>          Common Stock:
>
>          Ordinary income
>
>          $
>
>          3.61
>
>          $
>
>          3.50
>
>          $
>
>          3.29
>
>          Qualified dividend
>
>          0.03
>
>          0.01
>
>          0.00
>
>          Capital gains
>
>          0.40
>
>          0.33
>
>          0.19
>
>          Total dividend
>
>          $
>
>          4.04
>
>          $
>
>          3.84
>
>          $
>
>          3.48
>
>          Preferred Stock – Series Q:
>
>          Ordinary income
>
>          $
>
>          3.85
>
>          $
>
>          3.90
>
>          $
>
>          4.05
>
>          Qualified dividend
>
>          0.02
>
>          0.02
>
>          0.00
>
>          Capital gains
>
>          0.40
>
>          0.35
>
>          0.22
>
>          **Total dividend
>
>          $
>
>          4.27
>
>          $
>
>          4.27
>
>          $
>
>          4.27**

#### Evidence provenance

- T2: The non-Item-8 store location remains in the OR-set. The 247-token answer span includes the table's year headings and Series Q rows; a 95-character exact anchor keeps the snippet within the global limit.
- T6: The Item 5 sentence directly states $4.27 per share; the Item 16 span labels Preferred Stock Series Q and shows total dividend of $4.27 in all displayed years, including 2025.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p49 — NVDA

- Scope: `active`
- FY: `2026`
- Items: Item 1A | Item 9A
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | What corporate software modernization initiative is NVIDIA continuing? | What corporate software modernization initiative is NVIDIA continuing? |
| Query type | factoid | factoid |
| Evidence occurrences | 1 | 2 |

#### Round-1 evidence

**Original evidence 1** — `NVDA / 2026 / Item 9A. Controls and Procedures`

> **We are continuing a phased upgrade of our enterprise resource planning, or ERP, system to update our existing core financial systems.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must identify the continuing ERP-system modernization initiative.
- Curation note: This evidence identifies NVIDIA’s phased ERP upgrade and tests retrieval of a specific ongoing financial-systems initiative.
- Change summary: The Round 1 question remains unchanged. Full traversal adds the Item 1A ERP implementation disclosure as a second independently sufficient OR alternative.

#### Acceptable OR alternatives

**OR alternative 1** — `NVDA-2026-121635`

- Store Item: `Item 1A`
- Location: Risks Related to Our Global Operating Business / business processes and information systems
- Acceptance reason: Independently identifies continued implementation of updated accounting functionality tied to a new ERP system.

> **We continue to design and implement updated accounting functionality related to a new enterprise resource planning, or ERP, system.**

**OR alternative 2** — `NVDA-2026-227546`

- Store Item: `Item 9A`
- Location: Changes in Internal Control Over Financial Reporting
- Acceptance reason: The distinct Item 9A occurrence directly identifies the continuing phased ERP upgrade and its modernization purpose.

> **We are continuing a phased upgrade of our enterprise resource planning, or ERP, system to update our existing core financial systems.**

#### Evidence provenance

- T6: Both disclosures independently identify an ongoing ERP modernization initiative, one through new accounting functionality and one through the phased core-financial-system upgrade.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a24 — GOOGL

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `o`
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | What borrowing capacity and maturity schedule did Alphabet's unused revolvers have? | What borrowing capacity and maturity schedule did Alphabet's unused revolvers have? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> **As of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring in April 2026 and $6.0 billion expiring in April 2030.** No amounts have been borrowed under the credit facilities.

### Round-2 proposal

- Answer requirement: One independently sufficient span must state the total revolving-credit capacity and how that capacity is split between the April 2026 and April 2030 expirations.
- Curation note: This evidence gives the company-specific size, expiration dates, and unused status of Alphabet’s revolving credit arrangements, testing retrieval of linked financing details.
- Change summary: The approved Round 1 question remains unchanged. The Item 7 filing-store occurrence states the full capacity and expiration split; the Item 8 copy is excluded.

#### Acceptable OR alternatives

**OR alternative 1** — `GOOGL-2025-172698`

- Store Item: `7`
- Location: Liquidity and Material Cash Requirements / Financing
- Acceptance reason: Independently states the $10.0 billion capacity and its $4.0 billion April 2026 / $6.0 billion April 2030 expiration schedule.

> **As of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring in April 2026 and $6.0 billion expiring in April 2030.**

#### Evidence provenance

- T1: Re-extracted the filing-store non-breaking space in the date.
- T2: Item 8 is outside retrieval scope; the Item 7 occurrence remains.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p16 — LIN

- Scope: `active`
- FY: `2025`
- Items: Item 7, Critical Accounting Estimates, Revenue Recognition
- Generation mode: `intent_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 我覺得整個 block 才能夠回答問題，光是粗體沒辦法回答

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Linde project exposure to materials, staffing, inflation, and scope changes | Which cost components does Linde include when accounting for equipment contracts? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `LIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> The cost incurred input method places considerable importance on accurate estimates of the extent of progress towards completion and may involve estimates on the scope of deliveries and services required to fulfill the contractually defined obligations. **The key source of estimation uncertainty is the total estimated costs at completion including material, labor and overhead costs and the resultant state of completion of the contracts.** There are inherent uncertainties associated with the estimation process, including technical complexity, duration of construction cycle, potential cost inflation (whether equipment or manpower), and scope considerations all of which may affect the total estimation process. Changes in these estimates may lead to a significant impact on future financial statements.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must identify the material, labor, and overhead cost components Linde includes when accounting for equipment contracts.
- Curation note: This passage captures Linde-specific engineering delivery risks involving input and labor estimates, construction duration, technical complexity, inflation, and changing scope.
- Change summary: The Round 1 question combines material and labor cost categories with technical complexity, construction duration, inflation, and scope. Those facts require multiple sentences and cannot fit in one independently sufficient 50-200 character occurrence. The revised question asks one thing; after the Item 8 exclusion, the Item 7 occurrence identifies material, labor, and overhead costs.

#### Acceptable OR alternatives

**OR alternative 1** — `LIN-2025-116578`

- Store Item: `Item 7, Critical Accounting Estimates, Revenue Recognition`
- Location: —
- Acceptance reason: Directly identifies material, labor, and overhead as the components of estimated costs at completion.

> **The key source of estimation uncertainty is the total estimated costs at completion including material, labor and overhead costs and the resultant state of completion of the contracts.**

#### Evidence provenance

- T2: Item 8 is outside retrieval scope.
- T2: Item 8 is outside retrieval scope; the Item 7 occurrence remains.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p17 — NVDA

- Scope: `active`
- FY: `2026`
- Items: Item 1A | Item 7 | Item 15
- Generation mode: `intent_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 我覺得題目可以簡化成對大型下游買家的依賴程度就好，然後 evidence 再找過，也可以不止一個 evidence

| field | Round 1 | Round 2 |
|---|---|---|
| Question | NVIDIA reliance on large downstream buyers and AI lab demand | What share of NVIDIA's fiscal 2026 revenue came from its largest direct customer? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 3 |

#### Round-1 evidence

**Original evidence 1** — `NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Indirect Customers – Indirect customer revenue is an estimation based upon multiple factors including customer purchase order information, product specifications, internal sales data, and other sources. Indirect customers primarily purchase our products through system integrators and distributors. We generate a significant amount of our revenue from a limited number of indirect customers, some individually representing 10% or more of our revenue. Certain companies purchase cloud and related services through various direct and indirect customers. **We estimate that one AI research and deployment company contributed to a meaningful amount of our revenue purchasing cloud services from our customers in fiscal year 2026.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must state the percentage of total fiscal 2026 revenue attributable to NVIDIA's largest direct customer; spans at distinct source offsets are OR-hit alternatives.
- Curation note: This passage identifies concentrated indirect-buyer exposure and a meaningful fiscal 2026 contribution linked to one AI company, testing retrieval beyond direct-customer percentages.
- Change summary: The corrected single-intent factoid asks for the largest direct-customer share. Full-filing traversal found three distinct source occurrences that each report one direct customer at 22% of fiscal 2026 revenue and the next direct customer at 14%, making 22% the largest disclosed share.

#### Acceptable OR alternatives

**OR alternative 1** — `NVDA-2026-116355`

- Store Item: `Item 1A`
- Location: Risks Related to Our Global Operating Business / customer concentration risk
- Acceptance reason: The Item 1A occurrence independently reports 22% for the largest disclosed direct-customer share and 14% for the next direct customer.

> **For fiscal year 2026, sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14% of total revenue**

**OR alternative 2** — `NVDA-2026-205958`

- Store Item: `Item 7`
- Location: Results of Operations / Concentration of Revenue / Direct Customers
- Acceptance reason: The distinct Item 7 occurrence independently repeats the 22% largest disclosed direct-customer share and the 14% comparison.

> **For fiscal year 2026, sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14% of total revenue**

**OR alternative 3** — `NVDA-2026-337687`

- Store Item: `15`
- Location: Note 16 - Segment Information / Direct Customers
- Acceptance reason: The filing store labels the Note 16 occurrence under Item 15; it independently repeats the 22% largest disclosed direct-customer share and the 14% comparison.

> **For fiscal year 2026, sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14% of total revenue**

#### Evidence provenance

- T2: The actual filing-store label is Item 15, so this distinct store location remains in the OR-set.
- T6: All three distinct store locations independently report that the largest direct customer represented 22% of fiscal 2026 revenue.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p18 — DDOG

- Scope: `active`
- FY: `2025`
- Items: Item 1A
- Generation mode: `intent_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 粗體字拿的不精準，應該比 markdown 更下面的內容才是重點

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How can trade barriers affect Datadog’s growth and results? | How can export-authorization requirements affect Datadog’s sales opportunities? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> **Unfavorable conditions in the economy both in the United States and abroad may negatively affect the growth of our business and our results of operations.** For example, macroeconomic events including changes in trade policies, such as trade wars, tariffs or other trade restrictions or the threat of such actions, fluctuating inflation and interest rates, and the conflicts in Ukraine and the Middle East have led to economic uncertainty.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state how export-authorization requirements can restrict or eliminate Datadog sales opportunities.
- Curation note: This passage links restrictive trade policies to economic uncertainty that may weaken Datadog’s growth and operating performance.
- Change summary: The Round 1 snippet states the business effect but omits the trade-barrier cause. The source sentence that joins both concepts is longer than 200 characters. The revised intent remains about a concrete trade-control impact and has one independently sufficient 50–200 character occurrence.

#### Acceptable OR alternatives

**OR alternative 1** — `DDOG-2025-147331`

- Store Item: `Item 1A`
- Location: —
- Acceptance reason: Directly states that obtaining required export authorization can delay or eliminate a sale opportunity.

> **Obtaining the necessary export license or other authorization for a particular sale may be time-consuming and may result in the delay or loss of sales opportunities.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p21 — COIN

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `intent_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 沒涵蓋的海外營收來源，需要多個 evidence

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Coinbase domestic versus overseas revenue mix and foreign revenue source | What mainly comprised Coinbase's international revenue in 2025? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Comparison of the years ended December 31, 2025 and 2024
>
> Revenue
>
> **For the years ended December 31, 2025 and 2024 we generated 84% and 83%, respectively, of total revenue in the U.S., with no other country contributing over 10%.** International revenue comprised mainly transaction revenue.

### Round-2 proposal

- Answer requirement: One independently sufficient span must identify the main type of Coinbase international revenue in 2025.
- Curation note: This passage quantifies Coinbase’s geographic revenue concentration and identifies the main type of revenue earned internationally.
- Change summary: The Round 1 query combined geographic mix with foreign-revenue source, while its only evidence covered the mix. Because the two adjacent disclosures cannot form separate OR alternatives for a compound question, the revision keeps the missing foreign-source intent as one independently answerable need.

#### Acceptable OR alternatives

**OR alternative 1** — `COIN-2025-397600`

- Store Item: `Item 7`
- Location: Results of Operations / Revenue
- Acceptance reason: Directly identifies transaction revenue as the main source of international revenue.

> For the years ended December 31, 2025 and 2024 we generated 84% and 83%, respectively, of total revenue in the U.S., with no other country contributing over 10%. **International revenue comprised mainly transaction revenue.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p22 — AMZN

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `intent_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 問題牽涉海外營收與雲端業務，簡化成單一問題，重找 evidence

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Factors behind Amazon's 2025 overseas retail and cloud revenue gains | What primarily drove AWS sales growth in 2025? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `AMZN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> International sales increased 13% in 2025, compared to the prior year. The sales growth primarily reflects increased unit sales, including sales by third-party sellers, advertising sales, and subscription services. Increased unit sales were driven largely
>
> 24
>
>
> by our continued focus on price, selection, and convenience for our customers, including from our fast shipping offers. Changes in foreign exchange rates increased International net sales by $4.9 billion in 2025.
>
> AWS sales increased 20% in 2025, compared to the prior year. **The sales growth primarily reflects increased customer usage, partially offset by pricing changes primarily driven by long-term customer contracts.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must explain the primary disclosed driver of AWS sales growth in 2025; a growth rate without the driver is partial.
- Curation note: This passage captures distinct growth drivers for Amazon’s International and AWS businesses, testing retrieval across adjacent segment discussions.
- Change summary: The Round-1 question combined International retail and AWS. The revision keeps only AWS and the single store-exact occurrence identifies increased customer usage as the primary driver.

#### Acceptable OR alternatives

**OR alternative 1** — `AMZN-2025-113141`

- Store Item: `Item 7`
- Location: Overview
- Acceptance reason: Independently states the AWS subject, comparison year, and primary customer-usage driver.

> **AWS sales increased 20% in 2025, compared to the prior year. The sales growth primarily reflects increased customer usage**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p23 — DECK

- Scope: `active`
- FY: `2026`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: query 同時問「sales growth」跟「unit-volume metrics」兩件事，但 snippet 只覆蓋「unit volume」這句，前兩個成長率 bullet 沒被凸顯

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Deckers fiscal 2026 supplemental sales growth and unit-volume metrics | How did Deckers' total unit volume change in fiscal 2026? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> •On a constant currency basis, net sales increased by 9.0%, compared to the prior period.
>
> •Comparable DTC channel net sales for the 52 weeks ended March 29, 2026, increased by 4.6%,
>
> compared to the prior period.
>
> **•We experienced an increase of 6.2% in the total volume of units sold to 78,700 from 74,100,
>
> compared to the prior period.** Units sold include all categories such as footwear, apparel,
>
> accessories, home goods, and care kits across all brands. Percentages may not calculate on
>
> rounded units.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state the fiscal 2026 percentage increase and resulting total unit volume for Deckers.
- Curation note: This passage consolidates constant-currency growth, comparable direct-channel performance, and unit-volume data, testing retrieval of related supplemental operating metrics.
- Change summary: The Round 1 query combined sales-growth rates with a unit-volume metric, while its evidence answered only unit volume. The revised question asks only for the disclosed unit-volume change and removes the pipeline-specific bullet artifact from the canonical snippet.

#### Acceptable OR alternatives

**OR alternative 1** — `DECK-2026-160539`

- Store Item: `7`
- Location: Results of Operations / Supplemental Disclosure
- Acceptance reason: Independently states the 6.2% increase and both disclosed unit counts for the current and prior periods.

> **We experienced an increase of 6.2% in the total volume of units sold to 78,700 from 74,100,
>
> compared to the prior period.**

#### Evidence provenance

- T1: Re-extracted the filing-store space before the paragraph break.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p24 — GOOGL

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `intent_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: query 問的是「如何在幣別跟票面利率結構上做出不同安排」——重點是「vary（不同）」，需要對比才能回答，選的粗體不對

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How did Alphabet vary debt by denomination and coupon structure? | What mix of floating- and fixed-rate U.S. dollar notes did Alphabet issue in November 2025? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> **We also issued €6.75 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.31%, and a weighted-average maturity of approximately 14 years.**
>
> •November 2025: We issued $500 million of US dollar-denominated floating-rate senior unsecured notes and $17.0 billion of US dollar-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 4.92% and a weighted-average maturity of approximately 20 years. We also issued €6.5 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.44% and a weighted-average maturity of approximately 16 years.

### Round-2 proposal

- Answer requirement: One independently sufficient span must state both the floating-rate and fixed-rate U.S. dollar note amounts issued in November 2025.
- Curation note: This passage details Alphabet’s mix of dollar and euro borrowings and fixed versus floating coupons, testing retrieval of concrete financing choices relevant to currency and interest-rate exposure.
- Change summary: The Round 1 question requires a cross-denomination and coupon-structure comparison, but no single independently sufficient 50-200 character occurrence contains that full comparison. The revision preserves the reviewer's required contrast by narrowing to the November U.S. dollar issuance: $500 million floating-rate versus $17.0 billion fixed-rate.

#### Acceptable OR alternatives

**OR alternative 1** — `GOOGL-2025-172245`

- Store Item: `Item 7`
- Location: Liquidity and Material Cash Requirements / Financing / November 2025 issuance
- Acceptance reason: This shortest self-contained clause directly contrasts the $500 million floating-rate and $17.0 billion fixed-rate U.S. dollar notes; the remaining maturity and coupon details are not needed for the revised question.

> **We issued $500 million of US dollar-denominated floating-rate senior unsecured notes and $17.0 billion of US dollar-denominated fixed-rate senior unsecured notes**

#### Evidence provenance

- T2: Item 8 is excluded and the non-Item-8 store copy is already present, so a duplicate OR alternative is not retained.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p26 — AXON

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 題目應該只問單一產品，不要一次問三個

| field | Round 1 | Round 2 |
|---|---|---|
| Question | What factors drove TASER, Personal Sensors, and Platform Solutions growth? | What drove the increase in Axon's Personal Sensors revenue in 2025? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `AXON / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> The increase of $163.7 million in TASER is primarily driven by higher TASER 10 handle and cartridge volume. **Personal Sensors increased $80.1 million, which was primarily driven by the continued adoption of our newest body camera, AB4, and higher warranty revenue from more devices in the field.** The $111.7 million increase in Platform Solutions is primarily driven by higher volume for counter-drone equipment, virtual reality training, and fleet systems.

### Round-2 proposal

- Answer requirement: One independently sufficient span must explain a principal disclosed driver of the 2025 increase in Personal Sensors revenue; an amount without a driver is partial.
- Curation note: This evidence captures product-specific growth drivers across all three Connected Devices lines and tests retrieval of a compact comparative operating explanation.
- Change summary: The Round-1 question combined three product lines. The revision retains only Personal Sensors and its disclosed drivers.

#### Acceptable OR alternatives

**OR alternative 1** — `AXON-2025-181724`

- Store Item: `Item 7`
- Location: Results of Operations
- Acceptance reason: Independently identifies AB4 adoption and higher warranty revenue as the principal drivers.

> **Personal Sensors increased $80.1 million, which was primarily driven by the continued adoption of our newest body camera, AB4, and higher warranty revenue from more devices in the field.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p27 — COST

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 題目應該只問單一產品，capital spending 或 warehouse expansion plans

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Costco fiscal 2026 capital spending and warehouse expansion plans | How much does Costco intend to spend on capital expenditures in fiscal 2026? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `COST / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Capital Expenditure Plans
>
> Our primary requirements for capital are acquiring land, buildings, and equipment for new and remodeled warehouses, information systems, and manufacturing and distribution facilities. **In 2025, we spent $5,498 on capital expenditures, and it is our current intention to spend $6,000 to $6,500 during fiscal 2026.** These expenditures are expected to be financed with cash from operations, cash and cash equivalents, and short-term investments. We opened 27 new warehouses, including three relocations, in 2025, and plan to open up to 35 new warehouses, including five relocations, in 2026. There can be no assurance that current expectations will be realized, and plans are subject to change upon further review of our capital expenditure needs and the economic environment.

### Round-2 proposal

- Answer requirement: One independently sufficient span must state Costco's intended fiscal 2026 capital-expenditure amount; historical spending or warehouse counts alone are partial.
- Curation note: This passage combines Costco’s projected fiscal 2026 investment range, funding sources, and planned openings, testing retrieval of a detailed forward capital plan.
- Change summary: The Round-1 question combined capital spending and warehouse expansion. The revision asks only for the disclosed fiscal 2026 spending range.

#### Acceptable OR alternatives

**OR alternative 1** — `COST-2025-103987`

- Store Item: `Item 7`
- Location: LIQUIDITY AND CAPITAL RESOURCES
- Acceptance reason: Independently states the intended fiscal 2026 capital-expenditure range.

> **In 2025, we spent $5,498 on capital expenditures, and it is our current intention to spend $6,000 to $6,500 during fiscal 2026.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p29 — PLD

- Scope: `active`
- FY: `2025`
- Items: Item 7 | Item 16
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 題目應該只問單一事，Employee allocation 或 timing for venture incentive fees

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Employee allocation and expense timing for venture incentive fees | What share of third-party promote earnings can Prologis allocate to employees under its Promote Plan? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 2 |

#### Round-1 evidence

**Original evidence 1** — `PLD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> **The Prologis Promote Plan ("PPP") awards up to 25% of the third-party portion of the promotes earned by us from the co-investment ventures to our employees.** This award is issued as a combination of cash and equity-based awards, pursuant to the terms of the PPP and expensed through Strategic Capital Expenses in the Consolidated Statements of Income, as vested. As a result, expenses recognized in the current period may relate to promote revenues recognized in prior periods.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state the maximum third-party promote share allocated to employees.
- Curation note: This passage captures Prologis’s specific 25% employee allocation, award mix, vesting treatment, and potential lag between incentive revenue and expense recognition.
- Change summary: The Round 1 query combined employee allocation with expense timing. The revision keeps the employee-allocation half already answered by the valid evidence. The filing store contains independently sufficient Item 7 and Item 16 locations.

#### Acceptable OR alternatives

**OR alternative 1** — `PLD-2025-142515`

- Store Item: `Item 7`
- Location: Results of Operations / Strategic Capital Segment
- Acceptance reason: Directly states the current PPP maximum allocation to employees.

> **The Prologis Promote Plan ("PPP") awards up to 25% of the third-party portion of the promotes earned by us from the co-investment ventures to our employees.**

**OR alternative 2** — `PLD-2025-348730`

- Store Item: `16`
- Location: Prologis Promote Plan (“PPP”)
- Acceptance reason: A separate Item 16 store occurrence states the same 25% current-plan allocation and independently answers the revised question.

> **Under the PPP, for promotes earned after January 2024, we award up to 25% of the third-party portion of promotes earned by Prologis from co-investment ventures to employees** through a compensation pool.

#### Evidence provenance

- T2: The actual filing-store label is non-Item-8, so the distinct occurrence remains in the OR-set.
- T6: Both occurrences independently state the current maximum allocation of 25% of third-party promotes to employees.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p30 — LIN

- Scope: `active`
- FY: `2025`
- Items: Item 7, Liquidity, Capital Resources and Other Financial Data, Investing
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 「驅動因素」跟「地區集中度」兩件事，問題應問單一一件事，以 evidence 來說應該問地區集中度

| field | Round 1 | Round 2 |
|---|---|---|
| Question | What drove Linde's 2025 investment spending and where was it concentrated? | Where were Linde's 2025 capital expenditures concentrated geographically? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `LIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Capital expenditures in 2025 were $5,261 million, an increase of $764 million from 2024. Capital expenditures during 2025 related primarily to investments in new plant and production equipment for backlog growth requirements.
>
> **30
>
>
> Approximately 60% of the capital expenditures were in the Americas segment with 21% in the APAC segment and the rest largely in the EMEA segment.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state where Linde's 2025 capital expenditures were concentrated geographically.
- Curation note: This evidence captures both the backlog-related purpose and geographic allocation of Linde's capital investment, testing retrieval across adjacent quantitative details.
- Change summary: The Round 1 question asks both why capital expenditures increased and where they were allocated, while its snippet answers only geographic concentration and contains a page-number artifact. The revision follows the Round 1 reviewer direction and removes that artifact.

#### Acceptable OR alternatives

**OR alternative 1** — `LIN-2025-108671`

- Store Item: `Item 7, Liquidity, Capital Resources and Other Financial Data, Investing`
- Location: —
- Acceptance reason: Independently gives the Americas, APAC, and remaining EMEA allocation of 2025 capital expenditures.

> **Approximately 60% of the capital expenditures were in the Americas segment with 21% in the APAC segment and the rest largely in the EMEA segment.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p32 — XOM

- Scope: `active`
- FY: `2025`
- Items: Item 1
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 題目應該只問單一事，size 或 financial importance

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Size and financial importance of ExxonMobil's intellectual property portfolio | How large was ExxonMobil's active patent portfolio at the end of 2025? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `XOM / 2025 / Item 1. Business`

> ExxonMobil has a long-standing commitment to the development of proprietary technology. We have a wide array of research programs designed to meet the needs identified in each of our businesses. **ExxonMobil held over 8 thousand active patents worldwide at the end of 2025.** Although technology is an important contributor to the overall operations and results of our Company, the profitability of each business segment is not dependent on any individual patent, trade secret, trademark, license, franchise, or concession.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state the size of ExxonMobil's active patent portfolio at the end of 2025.
- Curation note: This evidence gives a concrete worldwide patent count and clarifies that no single intellectual property right determines segment profitability.
- Change summary: The Round 1 query combined portfolio size and financial importance while its evidence answered size. The revised question selects only the supported size intent; the adjacent dependency statement answers the removed financial-importance half, not this revised question.

#### Acceptable OR alternatives

**OR alternative 1** — `XOM-2025-008365`

- Store Item: `1`
- Location: Business / proprietary technology
- Acceptance reason: Independently states the worldwide count and measurement date for ExxonMobil's active patent portfolio.

> **ExxonMobil held over 8 thousand active patents worldwide at the end of 2025.**

#### Evidence provenance

- T1: Re-extracted the filing-store non-breaking space between 8 and thousand.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p33 — NVDA

- Scope: `active`
- FY: `2026`
- Items: Item 1
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 題目應該只問單一事，production timeline 或 token-cost improvement over Blackwell

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Rubin production timeline and token-cost improvement over Blackwell | How does NVIDIA say Rubin improves cost per token compared with Blackwell? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `NVDA / 2026 / Item 1. Business`

> In fiscal year 2026, we unveiled the NVIDIA Rubin platform, which is expected to commence production shipments in the second half of fiscal year 2027. **Built for agentic AI and reasoning, it excels at processing multi-step problem-solving and massive long-context workflows, delivering up to a 10x reduction in cost per token compared to Blackwell.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must state Rubin's cost-per-token improvement relative to Blackwell.
- Curation note: This evidence pairs Rubin’s expected shipment schedule with its quantified efficiency advantage, testing retrieval of a product roadmap and performance claim.
- Change summary: Selects only the token-cost comparison already supported by the original snippet and drops the separate production-timeline intent.

#### Acceptable OR alternatives

**OR alternative 1** — `NVDA-2026-023747`

- Store Item: `Item 1`
- Location: Business / Our Markets / Data Center
- Acceptance reason: Directly states Rubin's up-to-10x cost-per-token reduction relative to Blackwell.

> **Built for agentic AI and reasoning, it excels at processing multi-step problem-solving and massive long-context workflows, delivering up to a 10x reduction in cost per token compared to Blackwell.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p34 — DDOG

- Scope: `active`
- FY: `2025`
- Items: Item 1
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 題目應該只問單一事，database bottlenecks 或 resource constraints

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How does Datadog identify database bottlenecks and resource constraints? | How does Datadog’s Database Monitoring identify database bottlenecks? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `DDOG / 2025 / Item 1. Business`

> Database Monitoring allows customers to view query metrics and explain plans from all of their databases in a single place. **With Database Monitoring, they can quickly pinpoint costly and slow queries and drill into precise execution details to address bottlenecks.** Additionally, query, host, and application metric correlation makes it easy to identify and understand the impact of resource constraints on database performance.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must explain how Datadog Database Monitoring identifies database bottlenecks.
- Curation note: This passage explains Datadog’s concrete methods for diagnosing slow queries, execution issues, and infrastructure-related database performance problems.
- Change summary: The Round 1 question combined bottlenecks and resource constraints, while its snippet answered only bottlenecks. The revised question asks one thing and is fully answered by the existing evidence.

#### Acceptable OR alternatives

**OR alternative 1** — `DDOG-2025-039147`

- Store Item: `Item 1`
- Location: —
- Acceptance reason: Directly explains the slow-query and execution-detail method used to identify bottlenecks.

> **With Database Monitoring, they can quickly pinpoint costly and slow queries and drill into precise execution details to address bottlenecks.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p35 — PODD

- Scope: `active`
- FY: `2025`
- Items: Item 1 | Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: milestone 應該要更多時間軸過去現在未來，需要多個 evidence 組合

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Insulet next-generation insulin automation development milestones | What milestone did Insulet reach for EVOLUTION 2 in 2025? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 2 |

#### Round-1 evidence

**Original evidence 1** — `PODD / 2025 / Item 1. Business`

> In addition, we are working to integrate Omnipod 5 with Libre 3 Plus and developing Omnipod 6, our next-generation AID product. In 2025, we completed STRIVE, our pivotal study for the next generation hybrid closed loop system. Further, we continue to develop a fully closed loop AID system for type 2 diabetes (“FCL (T2)”). **In 2025, we completed enrollment for EVOLUTION 2, our safety and feasibility study for FCL (T2) and we plan to start the U.S. investigational device exemption (“IDE”) pivotal study in 2026.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state that Insulet completed or finished enrollment for EVOLUTION 2 in 2025.
- Curation note: This evidence captures named pipeline programs, completed studies, enrollment progress, and a planned pivotal trial, testing retrieval of product-development status across a compact passage.
- Change summary: The prior rewrite still combined the completed 2025 enrollment milestone with a separate planned 2026 study. This revision keeps one factoid intent. Full-filing traversal found two distinct source occurrences that independently state the 2025 EVOLUTION 2 enrollment milestone.

#### Acceptable OR alternatives

**OR alternative 1** — `PODD-2025-024455`

- Store Item: `Item 1`
- Location: Business / Data Management
- Acceptance reason: The Item 1 occurrence independently states that enrollment for EVOLUTION 2 was completed in 2025. This is the shortest self-contained semantic unit that satisfies the 50-character minimum.

> **In 2025, we completed enrollment for EVOLUTION 2, our safety and feasibility study** for FCL (T2) and we plan to start the U.S. investigational device exemption (“IDE”) pivotal study in 2026.

**OR alternative 2** — `PODD-2025-140970`

- Store Item: `Item 7`
- Location: Management's Discussion and Analysis / Overview
- Acceptance reason: The separate Item 7 occurrence independently states that Insulet finished EVOLUTION 2 enrollment in 2025.

> **In 2025, we also completed STRIVE, our pivotal study for the next generation hybrid closed loop system, and we finished enrollment for EVOLUTION 2**, our safety and feasibility study for a fully closed loop AID system for type 2 diabetes.

#### Evidence provenance

- T6: Both Item 1 and Item 7 occurrences independently state that EVOLUTION 2 enrollment was completed in 2025.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p36 — PODD

- Scope: `active`
- FY: `2025`
- Items: Item 1
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: evidence 只回答 receive 沒有回答 response, 這題不是分開的兩件事，但需要多個 evidence 才可以正確回答

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How does Omnipod 5 receive glucose readings and respond? | How does Omnipod 5 use glucose readings to adjust insulin dosing? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `PODD / 2025 / Item 1. Business`

> Omnipod 5 includes a proprietary AID algorithm embedded in the Pod. **The Pod integrates with a third-party continuous glucose monitor (“CGM”) to obtain glucose values through secure wireless Bluetooth communication.** The embedded algorithm utilizes these glucose values to predict glucose levels into the future and automatically adjusts insulin dosing intended
>
> to improve time-in-range (a dynamic measure of the percentage of time spent in glucose range) and reduce the occurrence of blood glucose highs and lows. The user can also deliver additional insulin doses for snacks or meals or to correct high blood glucose through the system.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must explain how Omnipod 5 uses glucose values to predict future levels and automatically adjust insulin dosing.
- Curation note: This evidence explains the product-specific sensor connection and predictive algorithm, testing retrieval of how Omnipod 5 automates insulin adjustments.
- Change summary: The original question required both receipt and response, but no 50–200-character occurrence independently answers both. The revision retains the more investor-relevant automated-response mechanism and removes the unsupported Bluetooth-receipt subpart.

#### Acceptable OR alternatives

**OR alternative 1** — `PODD-2025-014411`

- Store Item: `Item 1`
- Location: Business / Diabetes Management Challenges
- Acceptance reason: Directly explains the prediction-and-adjustment response asked by the revised question without crossing the SEC page-number artifact.

> **The embedded algorithm utilizes these glucose values to predict glucose levels into the future and automatically adjusts insulin dosing**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p37 — AMZN

- Scope: `active`
- FY: `2025`
- Items: Item 1
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 題目應該只問單一事，which electronics does it make

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How do shoppers reach Amazon offerings, and which electronics does it make? | Which electronic devices does Amazon manufacture and sell? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `AMZN / 2025 / Item 1. Business`

> Customers access our offerings through our websites, mobile apps, Alexa, devices, streaming, and physically visiting our stores. **We also manufacture and sell electronic devices, including Kindle, Fire tablet, Fire TV, Echo, Ring, Blink, and eero, and we develop and produce media content.** We seek to offer our customers low prices, fast and free delivery, easy-to-use functionality, and timely customer service.

### Round-2 proposal

- Answer requirement: One independently sufficient span must identify the electronic devices Amazon states it manufactures and sells; a generic statement that it sells devices is partial.
- Curation note: This evidence combines Amazon-specific customer access channels with its named device portfolio, testing retrieval across two adjacent substantive facts.
- Change summary: The Round-1 question combined shopping access channels and devices. The revision keeps only the device-list intent.

#### Acceptable OR alternatives

**OR alternative 1** — `AMZN-2025-007599`

- Store Item: `Item 1`
- Location: Consumers
- Acceptance reason: Independently identifies every device named in Amazon's manufacturing-and-sales disclosure.

> **We also manufacture and sell electronic devices, including Kindle, Fire tablet, Fire TV, Echo, Ring, Blink, and eero**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p50 — LIN

- Scope: `active`
- FY: `2025`
- Items: Item 1A, information technology and cybersecurity risk
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 還要看更完整的整個 chunk, 現在看不出來這段是不是在想 cyber incidents

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Have cyber incidents materially affected Linde's performance so far? | What types of information could operational security failures or breaches expose at Linde? |
| Query type | factoid | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `LIN / 2025 / Item 1A. Risk Factors`

> **To date, such attempts have not had any significant impact on Linde's operations or financial results.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must identify the types of confidential, proprietary, or personal information that Linde security failures or breaches could expose.
- Curation note: This disclosure gives a company-specific historical outcome and tests retrieval of whether prior cyberattacks caused significant harm.
- Change summary: The Round 1 answer uses the unresolved antecedent 'such attempts'. Joining the cyber-attack antecedent to the historical-impact sentence requires more than 200 characters. The revised question stays within the cybersecurity intent and is directly answered by a 146-character Item 1A clause; the canonical Item 1C copy maps to that same filing-store location.

#### Acceptable OR alternatives

**OR alternative 1** — `LIN-2025-044684`

- Store Item: `Item 1A, information technology and cybersecurity risk`
- Location: —
- Acceptance reason: Directly identifies confidential information and personal data as the information types exposed by operational security failures or breaches.

> **Operational failures and breaches of security from such attempts could lead to the loss or disclosure of confidential information or personal data**

#### Evidence provenance

- T1: The canonical Item 1C copy has no Item 1C filing-store match and maps to the same store location as LIN-2025-044684.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p40 — DECK

- Scope: `active`
- FY: `2026`
- Items: Item 1C
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 從粗體答案中不確定是不是在講security documents, 而且題目出現了 and why, 需要多個 evidence 才能回答

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Which security documents undergo periodic refresh, and why? | Which cybersecurity policies and procedures does Deckers periodically review and update? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `DECK / 2026 / Item 1C. Cybersecurity`

> **•periodically reviewing and updating our IRP, privacy policy, and other relevant policies/procedures.**
>
> We continuously evaluate and enhance our cybersecurity risk management practices in response to evolving
>
> threats and business needs.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must identify the cybersecurity policies or procedures Deckers periodically reviews and updates.
- Curation note: This evidence identifies the specific policies Deckers updates and links those updates to changing threats and organizational needs.
- Change summary: The Round 1 wording called the evidence 'security documents' and added a separate why-clause. The revised question uses the filing's own policies/procedures terminology, asks one thing, and is fully answered by one canonical occurrence without the bullet artifact.

#### Acceptable OR alternatives

**OR alternative 1** — `DECK-2026-124910`

- Store Item: `Item 1C`
- Location: Cybersecurity Risk Management and Strategy / key components
- Acceptance reason: Directly identifies the IRP, privacy policy, and other relevant policies/procedures as the materials periodically reviewed and updated.

> **periodically reviewing and updating our IRP, privacy policy, and other relevant policies/procedures.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a16 — LIN

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 整個 block 有涵蓋 query 資訊，但粗體本身沒有

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Factors behind unchanged APAC revenue in 2025 | How did currency translation affect Linde's APAC sales in 2025? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 2 |

#### Round-1 evidence

**Original evidence 1** — `LIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Sales
>
> Sales for the APAC segment were flat in 2025 versus 2024. Acquisitions increased sales by 2%. Volumes decreased sales by 1%. **Currency translation decreased sales by 1% primarily due to the weakening of the Australian dollar and Korean won against the U.S. dollar.** Cost pass-through and pricing were flat.

### Round-2 proposal

- Answer requirement: One independently sufficient source occurrence must state the direction or magnitude of currency translation's effect on APAC sales in 2025. Consolidated or other-segment sales effects, APAC operating-profit effects, exchange-rate tables without a sales effect, and generic foreign-exchange disclosures are partial or non-responsive.
- Curation note: This passage decomposes flat APAC sales into acquisition gains offset by volume and currency declines, testing retrieval of segment-specific revenue drivers.
- Change summary: The earlier three-driver rewrite remained a compound request. This correction asks only for currency translation's effect on APAC sales. Full-filing re-audit found two distinct responsive source locations: the APAC sales bridge table and the APAC sales narrative.

#### Acceptable OR alternatives

**OR alternative 1** — `LIN-2025-100223`

- Store Item: `7`
- Location: —
- Acceptance reason: Within the filing store's APAC structured block, the exact answer span carries the APAC sales-change table through the Currency (1)% row, independently identifying the measure, comparison period, direction, and magnitude. The 126-character snippet is its corpus-unique retrieval anchor.

> (Dollar amounts in millions) Variance
>
> Year Ended December 31,202520242025 vs 2024
>
> Sales$6,661 $6,632 — %
>
> Operating profit$1,933 $1,918 1 %
>
> As a percent of sales29.0 %28.9 %
>
> **2025 vs 2024
>
>  % Change
>
> Factors Contributing to Changes - Sales
>
> Volume(1)%
>
> Price/Mix— %
>
> Cost pass-through— %
>
> Currency(1)%**

**OR alternative 2** — `LIN-2025-101099`

- Store Item: `7`
- Location: —
- Acceptance reason: Within the filing store's APAC structured block, this exact sentence directly states that currency translation reduced sales by 1% and identifies the weakening Australian dollar and Korean won as the primary cause. It is independently sufficient and corpus-unique.

> **Currency translation decreased sales by 1% primarily due to the weakening of the Australian dollar and Korean won against the U.S. dollar.**

#### Evidence provenance

- T3: The canonical pipe-table text did not exact-match the filing store. The replacement span and snippet are exact filing-store substrings while preserving the APAC sales bridge's Currency (1)% answer.
- T3: The narrative sentence already exact-matched the filing store, is corpus-unique, and independently states the direction and magnitude of currency translation's APAC sales effect.
- T6: The APAC sales bridge table states Currency (1)%, while the narrative independently states the 1% decrease and currency causes.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a17 — NVDA

- Scope: `active`
- FY: `2026`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: query 同時問資料中心運算與網路業務的成長，應該只問單一一個

| field | Round 1 | Round 2 |
|---|---|---|
| Question | What propelled NVIDIA's Data Center compute and networking expansion? | What drove the growth in NVIDIA's Data Center networking revenue in fiscal 2026? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Revenue from Data Center computing grew 59% driven by demand for our Blackwell computing platform. **Revenue from Data Center networking grew 142% driven by the introduction and continued ramp of NVLink compute fabric for GB200 and GB300 systems and the growth of Ethernet and InfiniBand platforms.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must explain the fiscal 2026 drivers of Data Center networking revenue growth; compute-only growth drivers are partial.
- Curation note: This evidence pairs distinct growth rates with named Blackwell, NVLink, Ethernet, and InfiniBand demand drivers, testing retrieval of segment-specific operating details.
- Change summary: Keeps only the networking-growth intent supported by the original snippet and removes the separate compute-growth intent.

#### Acceptable OR alternatives

**OR alternative 1** — `NVDA-2026-204588`

- Store Item: `Item 7`
- Location: Results of Operations / Reportable Segments
- Acceptance reason: Directly attributes Data Center networking growth to the NVLink ramp and growth of Ethernet and InfiniBand platforms.

> **Revenue from Data Center networking grew 142% driven by the introduction and continued ramp of NVLink compute fabric for GB200 and GB300 systems and the growth of Ethernet and InfiniBand platforms.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a18 — DDOG

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 粗體字不夠長，沒涵蓋到 net retention change 的數據

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Datadog net retention change and its cause in 2025 | How did Datadog’s trailing 12-month dollar-based net retention rate change from 2024 to 2025? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> A further indication of the propensity of our customer relationships to expand over time is our dollar-based net retention rate, which compares our ARR from the same set of customers in one period, relative to the year-ago period. As of December 31, 2025, our trailing 12-month dollar-based net retention rate was about 120%. As of December 31, 2024, our trailing 12-month dollar-based net retention rate was high-110%'s. **The increase in our trailing 12-month dollar-based net retention rate was attributable to increased usage growth from existing customers.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state Datadog's trailing 12-month dollar-based net-retention rates for both 2024 and 2025.
- Curation note: This evidence quantifies the year-over-year retention improvement and attributes it to greater usage by established customers, testing metric-and-driver retrieval.
- Change summary: The Round 1 question combined the numeric change and its cause, but no single 50–200 character source occurrence states both. The revised question keeps the change requested by the reviewer and the 190-character evidence contains both years' disclosed rates.

#### Acceptable OR alternatives

**OR alternative 1** — `DDOG-2025-225945`

- Store Item: `7`
- Location: —
- Acceptance reason: Independently supplies the 2025 and 2024 values needed to describe the year-over-year increase.

> **As of December 31, 2025, our trailing 12-month dollar-based net retention rate was about 120%. As of December 31, 2024, our trailing 12-month dollar-based net retention rate was high-110%'s.**

#### Evidence provenance

- T1: Re-extracted both dates from the filing store to preserve non-breaking spaces.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a19 — LLY

- Scope: `active`
- FY: `2025`
- Items: Item 1 | Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 粗體字選錯句了，但整個 block 是有涵蓋到的

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Why will Lilly's near-term capital spending remain elevated? | Why will Lilly's near-term capital spending remain elevated? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 3 |

#### Round-1 evidence

**Original evidence 1** — `LLY / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Capital expenditures were $7.8 billion during 2025, compared to $5.1 billion in 2024. We are making investments in global facilities to manufacture existing and future products. **These investments, and other capital investments that support our operations, have increased our capital expenditures and will result in meaningfully higher capital expenditures in the near term.**
>
> As we expand our manufacturing capacity in order to meet existing and expected demand of our medicines, we have entered, and expect to continue to enter, into various agreements for contract manufacturing and for supply of materials.

### Round-2 proposal

- Answer requirement: One independently sufficient span must identify demand-driven manufacturing expansion or global manufacturing-facility investment as a reason Lilly expects near-term capital spending to remain elevated.
- Curation note: This passage links rising capital expenditures to global manufacturing investments and tests retrieval of the specific operational driver behind Lilly's spending outlook.
- Change summary: The Round 1 question is answerable, but its pronoun-led snippet was not the canonical cause sentence. Full traversal found three distinct disclosures that independently attribute the spending outlook to manufacturing expansion or global-facility investment, including the preceding sentence identified by the Round 1 comment.

#### Acceptable OR alternatives

**OR alternative 1** — `LLY-2025-081769`

- Store Item: `Item 1`
- Location: Business / Raw Materials and Product Supply
- Acceptance reason: Independently explains that anticipated demand is driving significant manufacturing expansion, a direct reason for elevated capital spending.

> **To support anticipated demand for our current and prospective products, we have undertaken significant manufacturing expansion initiatives.** Investments to increase our manufacturing capacity include new sites in North Carolina, Wisconsin, Indiana, Virginia, Texas, Alabama, Pennsylvania, Ireland, Germany, and the Netherlands.

**OR alternative 2** — `LLY-2025-202988`

- Store Item: `Item 7`
- Location: Executive Overview / Other Matters / Incretin Medicines
- Acceptance reason: The distinct Item 7 occurrence independently links anticipated demand to manufacturing expansion; the adjacent timing sentence confirms that capacity comes online over several years.

> **To support anticipated demand for our current and prospective products, we have undertaken significant manufacturing expansion initiatives.** Additional capacity is expected to become operational over the next several years.

**OR alternative 3** — `LLY-2025-214383`

- Store Item: `Item 7`
- Location: Financial Condition and Liquidity
- Acceptance reason: This is the cause sentence immediately preceding the Round 1 snippet and directly identifies global manufacturing facilities as the investment driving the near-term spending outlook.

> Capital expenditures were $7.8 billion during 2025, compared to $5.1 billion in 2024. **We are making investments in global facilities to manufacture existing and future products.** These investments, and other capital investments that support our operations, have increased our capital expenditures and will result in meaningfully higher capital expenditures in the near term.

#### Evidence provenance

- T6: The first two spans identify demand-driven manufacturing expansion; the third directly ties global manufacturing-facility investment to meaningfully higher near-term capital expenditures.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a20 — PODD

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: query 問單一問題，看是資本增加原因，或是有哪些工廠擴建專案之類的

| field | Round 1 | Round 2 |
|---|---|---|
| Question | 2025 capital spending increase and associated factory expansion projects | What investments primarily drove Insulet’s $66.7 million increase in capital expenditures in 2025? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Investing Activities
>
> Net cash used in investing activities was $222.7 million in 2025, compared with $146.2 million in 2024.
>
> **Capital Spending—Capital expenditures were $191.6 million and $124.9 million in 2025 and 2024, respectively.** The $66.7 million increase primarily related to the investment in our third manufacturing plant in Costa Rica and the purchase of additional machinery and equipment for our Malaysia manufacturing facility to support continued business growth.

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must identify the Costa Rica plant investment and the additional Malaysia machinery and equipment as the primary causes of the 2025 increase.
- Curation note: This passage links the year-over-year increase in capital expenditures to specific manufacturing investments in Costa Rica and Malaysia.
- Change summary: The revision asks one causal question. It replaces the Round 1 amount-only snippet with the adjacent cause disclosure and preserves both company-stated primary investments.

#### Acceptable OR alternatives

**OR alternative 1** — `PODD-2025-161437`

- Store Item: `Item 7`
- Location: Liquidity and Capital Resources / Investing Activities / Capital Spending
- Acceptance reason: The canonical 200-character snippet states both company-disclosed primary investment causes without relaxing the global limit.

> The **$66.7 million increase primarily related to the investment in our third manufacturing plant in Costa Rica and the purchase of additional machinery and equipment for our Malaysia manufacturing facility** to support continued business growth.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a21 — COIN

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: query 問單一問題，看是 policy 還是 liquidity constraints

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Coinbase policy and liquidity constraints for investment digital assets | How does Coinbase approach regular trading of crypto assets it holds for investment? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 2 |

#### Round-1 evidence

**Original evidence 1** — `COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Crypto assets held for investment are primarily long-term holdings and in certain cases fulfill capital requirements set by regulators (see also Capital requirements below). **We do not plan to engage in regular trading of these crypto assets but may purchase additional crypto assets for investment as a buy and hold strategy.** In case of a liquidity stress event, or for other episodic purposes, which may necessitate the use of these assets, we may change our policy and sell crypto assets held for investment to generate liquidity. During times of instability in the crypto assets market, we may not be able to sell our crypto assets at reasonable prices or at all. Our crypto assets held are considered less liquid than our cash and cash equivalents and may not be able to serve as a source of liquidity for us to the same extent as cash and cash equivalents.

### Round-2 proposal

- Answer requirement: One independently sufficient span must state Coinbase's policy or practice concerning regular trading of investment crypto assets.
- Curation note: This passage explains Coinbase’s long-term holding approach, exceptional-sale policy, and potential difficulty monetizing investment crypto during market instability.
- Change summary: The revision follows the Round 1 request to ask one question by retaining the investment-policy intent and removing liquidity constraints. After the Item 8 exclusion, two filing-store locations independently state the long-term, non-regular-trading policy.

#### Acceptable OR alternatives

**OR alternative 1** — `COIN-2025-410539`

- Store Item: `Item 7`
- Location: Non-GAAP Financial Measure / Adjusted EBITDA
- Acceptance reason: Independently states that Coinbase does not plan regular crypto trading and treats crypto investing as outside revenue-generating operations.

> **We do not plan on engaging in regular trading of crypto assets, and, as an operating company, our investing activities in crypto are not part of our revenue generating activities**, which are primarily based on transactions on our platform and the sales of subscriptions and services.

**OR alternative 2** — `COIN-2025-419843`

- Store Item: `Item 7`
- Location: Liquidity and Capital Resources / Other resources and commitments / Crypto assets
- Acceptance reason: Directly states the buy-and-hold policy and lack of planned regular trading for investment crypto assets.

> Crypto assets held for investment are primarily long-term holdings and in certain cases fulfill capital requirements set by regulators (see also Capital requirements below). **We do not plan to engage in regular trading of these crypto assets but may purchase additional crypto assets for investment as a buy and hold strategy.**

#### Evidence provenance

- T2: Item 8 is outside retrieval scope; two non-Item-8 acceptable occurrences remain.
- T6: Both Item 7 disclosures independently state that investment crypto assets are not intended for regular trading; the second also states the buy-and-hold policy.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a22 — AMZN

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 粗體字太短，無法包含所有需要回答 query 的資訊

| field | Round 1 | Round 2 |
|---|---|---|
| Question | How does Amazon account for satellite broadband development before and after viability? | When will Amazon begin capitalizing certain satellite broadband development costs? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `AMZN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> We currently expense the majority of the costs associated with the development of our satellite network for global broadband service (including production, launch, and payroll costs, and launch services deposits upon launch). **We will capitalize certain of these costs once the service achieves commercial viability, including sales to customers.**

### Round-2 proposal

- Answer requirement: One independently sufficient span must state the trigger for Amazon to begin capitalizing the satellite broadband development costs; a before-viability expense description is partial.
- Curation note: This evidence captures Amazon-specific accounting treatment for its satellite network and tests retrieval of the capitalization threshold after commercial viability.
- Change summary: The original before-and-after accounting request cannot fit the evidence limits. The revision asks only for the independently answerable capitalization trigger.

#### Acceptable OR alternatives

**OR alternative 1** — `AMZN-2025-119988`

- Store Item: `Item 7`
- Location: Overview
- Acceptance reason: Directly states commercial viability, including customer sales, as the capitalization trigger.

> **We will capitalize certain of these costs once the service achieves commercial viability, including sales to customers.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a23 — DECK

- Scope: `active`
- FY: `2026`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 應該要只有單一問題，currency-neutral revenue 或 comparable direct-sales growth rates

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Deckers currency-neutral revenue and comparable direct-sales growth rates | How much did Deckers' net sales increase on a constant-currency basis in fiscal 2026? |
| Query type | passage | factoid |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> •On a constant currency basis, net sales increased by 9.0%, compared to the prior period.
>
> **•Comparable DTC channel net sales for the 52 weeks ended March 29, 2026, increased by 4.6%,
>
> compared to the prior period.**

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state Deckers' constant-currency net-sales increase in fiscal 2026.
- Curation note: This passage provides two related supplemental sales-growth measures, testing retrieval of adjusted revenue performance metrics.
- Change summary: The Round 1 query joined two non-GAAP growth measures. The revised question selects only constant-currency net-sales growth, leaving p23 to cover the separate unit-volume metric and avoiding another compound query.

#### Acceptable OR alternatives

**OR alternative 1** — `DECK-2026-160324`

- Store Item: `Item 7`
- Location: Results of Operations / Supplemental Disclosure
- Acceptance reason: Independently states the filing's fiscal 2026 constant-currency net-sales growth rate.

> **On a constant currency basis, net sales increased by 9.0%, compared to the prior period.**

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate a25 — CAT

- Scope: `active`
- FY: `2025`
- Items: Item 7
- Generation mode: `passage_first`

### Round-1 review

- Decision: `?`
- Round-1 reviewer comment: 題目應該簡化為 deal cost and completion schedule,  拿掉 mining software capabilities

| field | Round 1 | Round 2 |
|---|---|---|
| Question | RPMGlobal deal cost, completion schedule, and mining software capabilities | What were the expected purchase price and closing schedule for Caterpillar's RPMGlobal acquisition? |
| Query type | passage | passage |
| Evidence occurrences | 1 | 1 |

#### Round-1 evidence

**Original evidence 1** — `CAT / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> On February 3, 2026, the Federal Court of Australia approved Caterpillar's acquisition of RPMGlobal Holdings Limited, an Australian based software company. **The transaction is expected to close in the final two weeks of February with a purchase price of approximately $790 million, excluding cash acquired.** RPMGlobal is a leading provider of mining software solutions with deep domain expertise in mining technology enablement and data-driven software solutions at every stage of the mining lifecycle.

### Round-2 proposal

- Answer requirement: One independently sufficient span must state both the expected closing window and purchase price for the RPMGlobal acquisition.
- Curation note: This passage combines the acquisition’s expected closing window and consideration with RPMGlobal’s specialized mining technology expertise, testing transaction-detail retrieval.
- Change summary: Removes mining-software capabilities as requested in Round 1, leaving one transaction-detail intent that each 149-character occurrence answers independently.

#### Acceptable OR alternatives

**OR alternative 1** — `CAT-2025-171845`

- Store Item: `Item 7`
- Location: LIQUIDITY AND CAPITAL RESOURCES / Machinery, Power & Energy / resource allocation discussion
- Acceptance reason: Directly states both the expected closing window and purchase price in the Item 7 liquidity discussion.

> On February 3, 2026, the Federal Court of Australia approved Caterpillar's acquisition of RPMGlobal Holdings Limited, an Australian based software company. **The transaction is expected to close in the final two weeks of February with a purchase price of approximately $790 million, excluding cash acquired.** RPMGlobal is a leading provider of mining software solutions with deep domain expertise in mining technology enablement and data-driven software solutions at every stage of the mining lifecycle.

#### Evidence provenance

- T2: Item 8 is excluded and the non-Item-8 store copy is already present, so a duplicate OR alternative is not retained.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n01 — NEE

- Scope: `active_new`
- FY: `2025`
- Items: Item 7 | Item 6
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | How did growth in FPL's regulatory capital base affect its 2025 earnings? |
| Query type | — | passage |
| Evidence occurrences | 0 | 4 |

### Round-2 proposal

- Answer requirement: One independently sufficient span must explain how growth in FPL's regulatory capital base affected 2025 earnings; a span stating only capital spending or an earnings amount is partial.
- Curation note: Understand whether regulated capital deployment translated into earnings growth.
- Change summary: The question remains unchanged. The filing store contains two distinct answer texts under Item 7, and each has a second reachable copy under the store's Item 6 label. All four locations are enumerated as OR alternatives; the detailed answer text also states that the investments grew average rate base by approximately $5.5 billion.

#### Acceptable OR alternatives

**OR alternative 1** — `NEE-2025-180298`

- Store Item: `Item 7`
- Location: Overview / 2025 Summary
- Acceptance reason: Independently explains that continued regulated-asset investment was a primary driver of FPL's 2025 net-income increase.

> **FPL's net income increased in 2025 primarily driven by continued investments in plant in service and other property and a higher earned regulatory ROE in 2025.**

**OR alternative 2** — `NEE-2025-183888`

- Store Item: `7`
- Location: FPL Results of Operations
- Acceptance reason: The continuous answer span states the $469 million net-income increase, attributes it to higher earnings from plant and property investments, and states that those investments grew average rate base by approximately $5.5 billion.

> FPL’s net income for 2025 and 2024 was $5,012 million and $4,543 million, respectively, representing an increase of $469 million. **The increase was primarily driven by higher earnings from investments in plant in service and other property.** Such investments grew FPL's average rate base by approximately $5.5 billion in 2025 and reflect, among other things, solar generation additions and ongoing transmission and distribution additions.

**OR alternative 3** — `NEE-2025-store-item6-6732`

- Store Item: `6`
- Location: Flat Item 6 / [Reserved] / FPL and NEER earnings summary
- Acceptance reason: This second reachable store copy independently states that regulated-asset investment was a primary driver of FPL's 2025 net-income increase.

> **FPL's net income increased in 2025 primarily driven by continued investments in plant in service and other property and a higher earned regulatory ROE in 2025.**

**OR alternative 4** — `NEE-2025-store-item6-10171`

- Store Item: `6`
- Location: Flat Item 6 / [Reserved] / FPL earnings
- Acceptance reason: This second reachable store copy states the net-income increase, attributes it to plant and property investment, and connects those investments to average-rate-base growth.

> FPL’s net income for 2025 and 2024 was $5,012 million and $4,543 million, respectively, representing an increase of $469 million. **The increase was primarily driven by higher earnings from investments in plant in service and other property.** Such investments grew FPL's average rate base by approximately $5.5 billion in 2025 and reflect, among other things, solar generation additions and ongoing transmission and distribution additions.

#### Evidence provenance

- T1: Re-extracted the filing-store non-breaking space after $5.5; the selected snippet was already store-exact.
- T6: The two distinct answer texts each independently connect plant/property investment to higher FPL earnings. Both reachable store copies of each text are enumerated, and the detailed span additionally quantifies rate-base and net-income changes.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n02 — LLY

- Scope: `active_new`
- FY: `2025`
- Items: Item 7
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | What were the principal drivers of Lilly's 2025 revenue growth? |
| Query type | — | passage |
| Evidence occurrences | 0 | 2 |

### Round-2 proposal

- Answer requirement: One independently sufficient span must identify the principal company-disclosed drivers of Lilly's 2025 revenue growth; a span containing only the growth rate is partial.
- Curation note: Identify the operating drivers behind company-level revenue growth.
- Change summary: The question remains unchanged. Full traversal found one concise company-level driver sentence and one distinct geographic driver disclosure; both are valid OR alternatives.

#### Acceptable OR alternatives

**OR alternative 1** — `LLY-2025-188613`

- Store Item: `Item 7`
- Location: Executive Overview / Financial Results
- Acceptance reason: Explicitly identifies increased volume as the primary company-level growth driver and lower realized prices as a partial offset.

> **Revenue increased in 2025 driven primarily by increased volume, partially offset by lower realized prices.** The increased volume and lower realized prices in 2025 were primarily driven by Mounjaro and Zepbound.

**OR alternative 2** — `LLY-2025-208980`

- Store Item: `7`
- Location: Results of Operations / Operating Results—2025 / Revenue
- Acceptance reason: Independently supplies the geographic volume and realized-price drivers and attributes them to Mounjaro and Zepbound within the 200-character cap.

> **In the U.S., the volume increase and the lower realized prices in 2025 were primarily driven by Mounjaro and Zepbound.
>
> Outside the U.S., the volume increase in 2025 was primarily driven by Mounjaro.**

#### Evidence provenance

- T1: Re-extracted the filing-store space before the paragraph break; the exact snippet is 200 characters and remains within the global limit.
- T6: The first span states the consolidated volume/price drivers; the second independently identifies the U.S. and international product drivers behind those revenue components.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n03 — PLD

- Scope: `active_new`
- FY: `2025`
- Items: Item 7 | Item 1
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | What drove the change in Prologis's rental revenue in 2025? |
| Query type | — | passage |
| Evidence occurrences | 0 | 3 |

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must explain a principal company-disclosed driver of Prologis's 2025 rental-revenue change; an isolated revenue amount or percentage is partial.
- Curation note: Understand the operating causes of rental-revenue movement.
- Change summary: The intent-first question remains unchanged. Full traversal found three distinct locations that independently explain the 2025 lease mark-to-market and rollover-rent mechanism.

#### Acceptable OR alternatives

**OR alternative 1** — `PLD-2025-130013`

- Store Item: `Item 7`
- Location: Management's Overview / Summary of 2025
- Acceptance reason: Attributes 2025 results to favorable mark-to-market in existing leases created by earlier market-rent increases.

> **Our results during 2025 continued to reflect the favorable mark-to-market of our existing leases, reflecting increases in market rents over the past several years.**

**OR alternative 2** — `PLD-2025-030022`

- Store Item: `Item 1`
- Location: Future Growth / Rent Growth
- Acceptance reason: Identifies lease rollovers to higher market rents in 2025 and quantifies the resulting net-effective-rent increase.

> **For lease rollovers during 2025, the increases to market on our share of the O&M portfolio resulted in increases of approximately 50% on net effective rents.**

**OR alternative 3** — `PLD-2025-136602`

- Store Item: `Item 7`
- Location: Results of Operations / Real Estate Segment
- Acceptance reason: Explicitly identifies higher rental rates on lease rollover as a key driver of increasing rental income.

> **Significant rent change due to higher rental rates on the rollover of leases during both periods continues to be a key driver of increasing rental income.**

#### Evidence provenance

- T6: Each occurrence independently identifies a rental-revenue mechanism: favorable lease mark-to-market, rent increases on rollover, or higher rollover rental rates.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n04 — XOM

- Scope: `active_new`
- FY: `2025`
- Items: Item 16
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | How did lower crude prices affect ExxonMobil's 2025 Upstream earnings? |
| Query type | — | passage |
| Evidence occurrences | 0 | 1 |

### Round-2 proposal

- Answer requirement: One independently sufficient span must explain the effect of lower crude prices on ExxonMobil's 2025 Upstream earnings.
- Curation note: Connect commodity-price movements to the company's earnings performance.
- Change summary: The filing reports 2025 crude-oil and natural-gas price movements together, but the independently sufficient 2025 earnings-driver disclosure attributes a $6.1 billion earnings decrease primarily to lower crude prices and does not state a 2025 natural-gas earnings effect. The revised question preserves the causal earnings intent without relaxing the global 50–200-character span limit.

#### Acceptable OR alternatives

**OR alternative 1** — `XOM-2025-167393`

- Store Item: `16`
- Location: Upstream Financial Results
- Acceptance reason: Independently quantifies the 2025 Upstream earnings decrease from lower realizations and attributes it primarily to lower crude prices.

> **Price – Lower realizations decreased earnings by $6.1 billion, primarily driven by lower crude prices as record demand was more than offset by increased industry supply.**

#### Evidence provenance

- T1: The selected exact text has no Item 7 filing-store copy; the actual non-excluded filing-store label is Item 16.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n05 — COST

- Scope: `active_new`
- FY: `2025`
- Items: Item 7
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | What drove Costco's comparable-sales growth in fiscal 2025? |
| Query type | — | passage |
| Evidence occurrences | 0 | 3 |

### Round-2 proposal

- Answer requirement: One independently sufficient span must explain a principal disclosed driver of Costco's fiscal 2025 comparable-sales growth; a growth percentage without a driver is partial.
- Curation note: Understand the business drivers of comparable-sales performance.
- Change summary: The full-filing audit identified three distinct disclosures of the operating mechanisms and observed frequency/ticket drivers of comparable-sales growth.

#### Acceptable OR alternatives

**OR alternative 1** — `COST-2025-083984`

- Store Item: `Item 7`
- Location: Overview
- Acceptance reason: Identifies shopping frequency and average ticket as the two operating drivers of comparable-sales growth.

> **Comparable sales growth is achieved through increasing shopping frequency from new and existing members and the amount they spend on each visit (average ticket).**

**OR alternative 2** — `COST-2025-084633`

- Store Item: `Item 7`
- Location: Overview
- Acceptance reason: Identifies merchandise selection and pricing as Costco's disclosed mechanism for generating comparable-sales growth.

> **Generating comparable sales growth is foremost a question of making available the right merchandise at the right prices, a skill that we believe we have repeatedly demonstrated over the long-term.**

**OR alternative 3** — `COST-2025-094148`

- Store Item: `Item 7`
- Location: Overview
- Acceptance reason: Quantifies the observed shopping-frequency and average-ticket contributions to fiscal 2025 comparable sales.

> **Comparable sales were positively impacted by increases of 5% in shopping frequency and approximately 1% in average ticket.**

#### Evidence provenance

- T6: The three disclosures independently identify complementary comparable-sales drivers: shopping frequency/average ticket, merchandise/pricing, and the observed 2025 frequency/ticket increases.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n06 — COIN

- Scope: `active_new`
- FY: `2025`
- Items: Item 7
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | What drove the change in Coinbase's transaction revenue in 2025? |
| Query type | — | passage |
| Evidence occurrences | 0 | 3 |

### Round-2 proposal

- Answer requirement: One independently sufficient span must explain a principal company-disclosed driver of Coinbase's 2025 transaction-revenue change; an isolated revenue amount is partial.
- Curation note: Understand the operating drivers of transaction-revenue movement.
- Change summary: The question remains broad enough for multiple correct OR-hit answers. Full traversal found three distinct driver spans: consumer fee-rate and user-mix changes, higher consumer Trading Volume, and institutional derivatives growth associated with Deribit.

#### Acceptable OR alternatives

**OR alternative 1** — `COIN-2025-398200`

- Store Item: `7`
- Location: Results of Operations / Transaction revenue / consumer transaction revenue
- Acceptance reason: Identifies the lower blended fee rate and the shift toward lower-fee Advanced and Coinbase One volume as a disclosed transaction-revenue driver.

> a decrease of $384.4 million attributed to **a lower average blended fee rate, primarily due to changes in the mix of Trading Volume from Simple users to Advanced and Coinbase One users who pay lower average fees**

**OR alternative 2** — `COIN-2025-398388`

- Store Item: `Item 7`
- Location: Results of Operations / Transaction revenue / consumer transaction revenue
- Acceptance reason: Directly identifies higher consumer Trading Volume as a separate disclosed transaction-revenue driver.

> **an increase of $277.0 million attributed to a 7% increase in consumer Trading Volume**

**OR alternative 3** — `COIN-2025-398500`

- Store Item: `7`
- Location: Results of Operations / Transaction revenue / institutional transaction revenue
- Acceptance reason: Directly identifies derivatives trading, mainly from the Deribit acquisition, as an institutional transaction-revenue driver.

> **an increase in institutional transaction revenue driven by an increase of $152.0 million attributed to derivatives trading, due mainly to the acquisition of Deribit.**

#### Evidence provenance

- T1: Re-extracted the span from the filing store to preserve its non-breaking space after $384.4.
- T1: Re-extracted the span and snippet from the filing store to preserve its non-breaking space after $152.0.
- T6: Each bullet is an answer-bearing transaction-revenue driver in the same Results of Operations block: fee-rate mix, consumer trading volume, or institutional derivatives volume from Deribit.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n07 — AXON

- Scope: `active_new`
- FY: `2025`
- Items: Item 1
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | How do Axon's subscription offerings support its recurring-revenue model? |
| Query type | — | passage |
| Evidence occurrences | 0 | 2 |

### Round-2 proposal

- Answer requirement: One independently sufficient span must connect an Axon subscription or SaaS offering to recurring revenue; a product list without that business-model relationship is partial.
- Curation note: Understand how subscription offerings support recurring revenue.
- Change summary: The full-filing audit found two distinct Item 1 disclosures that independently connect subscription offerings to recurring revenue.

#### Acceptable OR alternatives

**OR alternative 1** — `AXON-2025-012871`

- Store Item: `Item 1`
- Location: Business Segments
- Acceptance reason: Identifies multi-year recurring software subscriptions as a direct revenue source.

> **Our revenue is derived from a combination of hardware sales, multi-year recurring software subscriptions, professional services, and extended warranties.**

**OR alternative 2** — `AXON-2025-013183`

- Store Item: `1`
- Location: Business Segments
- Acceptance reason: Directly connects Axon's SaaS suite to annual recurring revenue.

> **Axon has a suite of cloud-based, SaaS solutions that deeply integrate with our hardware to benefit customers and drive annual recurring revenue, which totaled $1.3 billion1 as of December 31, 2025.**

#### Evidence provenance

- T1: The canonical visible-text occurrence differed from the filing store only in whitespace; span and snippet were re-extracted as exact store substrings.
- T6: One occurrence identifies multi-year recurring software subscriptions as revenue; the other independently connects SaaS offerings to annual recurring revenue.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n08 — DECK

- Scope: `active_new`
- FY: `2026`
- Items: Item 1
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | Which brands does Deckers identify as its principal product brands? |
| Query type | — | factoid |
| Evidence occurrences | 0 | 1 |

### Round-2 proposal

- Answer requirement: One independently sufficient span must identify all brands Deckers presents as its principal product brands; a span naming only one brand is partial unless the filing states that it is the sole principal brand.
- Curation note: Identify the brands that define the company's product portfolio.
- Change summary: The question remains unchanged. Filing-store reconciliation retains one Item 1 occurrence identifying HOKA, UGG, and Teva; the canonical Item 7 copy maps to that same store location and the Item 8 copy is excluded.

#### Acceptable OR alternatives

**OR alternative 1** — `DECK-2026-014599`

- Store Item: `1`
- Location: Business / General
- Acceptance reason: The Item 1 occurrence independently identifies all three primarily marketed proprietary brands.

> **We market our products primarily
>
> under three proprietary brands: HOKA, UGG, and Teva.**

#### Evidence provenance

- T1: Re-extracted the filing-store space before the paragraph break.
- T1: The canonical Item 7 copy has no Item 7 filing-store match and maps to the same store location as DECK-2026-014599.
- T2: Item 8 is outside retrieval scope; the Item 1 occurrence remains.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n09 — PODD

- Scope: `active_new`
- FY: `2025`
- Items: Item 1C
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | Has Insulet experienced cybersecurity incidents that materially affected the company? |
| Query type | — | factoid |
| Evidence occurrences | 0 | 1 |

### Round-2 proposal

- Answer requirement: One independently sufficient occurrence must state whether previous cybersecurity incidents materially affected Insulet; hypothetical incident risks, response procedures, and governance allocations are not sufficient.
- Curation note: Understand how responsibility for cybersecurity risk is governed.
- Change summary: The revised question asks one binary incident-history fact instead of a broad allocation of governance responsibilities. Full-filing traversal found one distinct source occurrence stating that Insulet does not believe previous cybersecurity incidents materially affected the company.

#### Acceptable OR alternatives

**OR alternative 1** — `PODD-2025-132068`

- Store Item: `Item 1C`
- Location: Risk Management and Strategy / prior incident impact
- Acceptance reason: The filing's single historical-impact disclosure states that Insulet does not believe previous cybersecurity incidents materially affected the company; the full answer span preserves all three disclosed impact dimensions.

> **We currently do not believe that risks from cybersecurity threats, including as a result of any previous cybersecurity incidents, have materially affected the Company**’s business strategy, results of operations, or financial condition.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate n10 — JPM

- Scope: `active_new`
- FY: `2025`
- Items: Item 1 | Item 15
- Generation mode: `intent_first`

### Round-1 review

- Decision: — (new candidate)
- Round-1 reviewer comment: —

| field | Round 1 | Round 2 |
|---|---|---|
| Question | — | Which types of market risk does JPMorganChase include in its Value-at-Risk measure? |
| Query type | — | factoid |
| Evidence occurrences | 0 | 2 |

### Round-2 proposal

- Answer requirement: One independently sufficient span must identify all market risk types JPMorganChase states are included in its Value-at-Risk measure.
- Curation note: Understand which market-risk exposures JPMorganChase's Value-at-Risk measure covers.
- Change summary: The question remains unchanged. The filing-store table yields a 151-character exact span that joins the CIB trading VaR risk-type heading to all four reported categories: fixed income, foreign exchange, equities, and commodities and other. The store contains the same source table under Item 1 and Item 15, so both reachable copies are enumerated as OR alternatives.

#### Acceptable OR alternatives

**OR alternative 1** — `JPM-2025-504303`

- Store Item: `1`
- Location: Segment & Corporate Results – Managed Basis / Market Risk Management / Value-at-risk / Total VaR table
- Acceptance reason: The store-exact span preserves the table heading that establishes the VaR relationship and includes all four CIB trading VaR risk types within the 200-character limit.

> **CIB trading VaR by risk type
>
> Fixed income$35 $27 $51 $34 $26 $53 
>
> Foreign exchange9 6 15 15 7 23 
>
> Equities17 7 138 (e)8 4 15 
>
> Commodities and other**

**OR alternative 2** — `JPM-2025-store-item15-239167`

- Store Item: `15`
- Location: Segment & Corporate Results – Managed Basis / Market Risk Management / Value-at-risk / Total VaR table
- Acceptance reason: This second reachable filing-store copy contains the same independently sufficient table span under a distinct non-Item-8 store label, so it is enumerated as an OR alternative.

> **CIB trading VaR by risk type
>
> Fixed income$35 $27 $51 $34 $26 $53 
>
> Foreign exchange9 6 15 15 7 23 
>
> Equities17 7 138 (e)8 4 15 
>
> Commodities and other**

#### Evidence provenance

- T3: The canonical table linearization did not exact-match the filing store. The store has two non-Item-8 copies of the same source table, so both store-exact locations are enumerated; cross-arm header-path reconciliation remains outside this task.
- T6: Both reachable store copies contain the same VaR table heading and all four risk types; neither relies on another occurrence.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p46 — COIN

- Scope: `reference_only`
- FY: `2025`
- Items: Item 3
- Generation mode: `passage_first`

### Round-1 review

- Decision: `!`
- Round-1 reviewer comment: 這一題涉及整個 RAG retrieval 問題，另外討論

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Where does Coinbase cross-reference its significant litigation disclosures? | — |
| Query type | factoid | — |
| Evidence occurrences | 1 | 0 |

#### Round-1 evidence

**Original evidence 1** — `COIN / 2025 / Item 3. Legal Proceedings`

> **ITEM 3. LEGAL PROCEEDINGS
>
> For a description of material legal proceedings in which we are involved, see Note 21.**

### Round-2 disposition

This row is reference-only and was not carried into the 51-candidate active pool.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p19 — LLY

- Scope: `reference_only`
- FY: `2025`
- Items: Item 7
- Generation mode: `intent_first`

### Round-1 review

- Decision: `x`
- Round-1 reviewer comment: evidence 沒有回答到 query

| field | Round 1 | Round 2 |
|---|---|---|
| Question | competitive threats facing Lilly’s incretin franchise | — |
| Query type | passage | — |
| Evidence occurrences | 1 | 0 |

#### Round-1 evidence

**Original evidence 1** — `LLY / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> Longer term, the durability of our cardiometabolic health product offerings and sustainability of our growth and prospects will depend on our ability to maintain or strengthen our competitive position as the therapeutic landscape evolves and to deliver further innovations that provide sufficient value to sustain our growth momentum.
>
> **We continue to see the production, marketing, and sale of counterfeit, misbranded, adulterated, and mass-compounded incretins.** These practices may impact patient safety and undermine regulatory drug approval processes. While the FDA confirmed in late 2024 that the previous shortage of tirzepatide had ended and that compounding pharmacies are required to cease mass production, we cannot guarantee adequate regulation or compliance. Lilly will continue to consider all options, including filing lawsuits where appropriate, to address unlawful practices and the patient safety risks of unapproved, untested, and manipulated drugs.

### Round-2 disposition

This row is reference-only and was not carried into the 51-candidate active pool.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p47 — XOM

- Scope: `reference_only`
- FY: `2025`
- Items: Item 2
- Generation mode: `passage_first`

### Round-1 review

- Decision: `x`
- Round-1 reviewer comment: evidence 沒講 FPSO, 而且這題太冷門了

| field | Round 1 | Round 2 |
|---|---|---|
| Question | Which Brazilian development began producing via an FPSO? | — |
| Query type | factoid | — |
| Evidence occurrences | 1 | 0 |

#### Round-1 evidence

**Original evidence 1** — `XOM / 2025 / Item 2. Properties`

> **Brazil commenced operations in the Bacalhau Phase 1 development with the start-up of the floating production, storage and offloading vessel.**

### Round-2 disposition

This row is reference-only and was not carried into the 51-candidate active pool.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---

## Candidate p39 — AMZN

- Scope: `reference_only`
- FY: `2025`
- Items: Item 1
- Generation mode: `passage_first`

### Round-1 review

- Decision: `x`
- Round-1 reviewer comment: 這題不太是 user 會問的問題，沒有參考價值

| field | Round 1 | Round 2 |
|---|---|---|
| Question | What does Career Choice provide, and how many workers joined? | — |
| Query type | passage | — |
| Evidence occurrences | 1 | 0 |

#### Round-1 evidence

**Original evidence 1** — `AMZN / 2025 / Item 1. Business`

> We rely on numerous and evolving initiatives to implement this objective and invent mechanisms for talent development, including competitive pay and benefits, flexible work arrangements, and skills training and educational programs such as Amazon Career Choice (education funding for eligible employees). **Over 300,000 Amazon employees around the world have participated in Career Choice.**

### Round-2 disposition

This row is reference-only and was not carried into the 51-candidate active pool.

### Human review — Round 2

- `round2_decision`: _(blank)_
- `round2_reviewer_comment`: _(blank)_

---
