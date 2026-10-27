# Round 2 — two-reviewer reconciliation

## Decision record (user, 2026-10-27)

- Applied: **G1** (all 5 rows) and the mechanical **G3** fixes (p37, a20, a21,
  p21, p18 question rewrites; p33, a22, p36 span extensions — p36 question
  kept; p23, n08 snippet trims).
- Excluded: p50 (G3d), all of G2 (n07, n02, n03), G4 (p25, p28, p31, p27,
  n06) and G5 (p42, p40) — 11 rows. Result: **40 rows**.
- n08 assembly finding: the Item 7 copy of the brand sentence exists in the
  filing, but the store parses it as block headings, so it cannot be listed
  as a store-exact alternative (recorded in the row's `review_provenance` and
  the README's Known limitations).
- Encoded in `assemble_dataset.py`.

Inputs: `round2_llm_review_reviewer_a.csv` (reviewer A) and `round2_llm_review_codex.csv`
(reviewer B). Both reviewed the same 51 active candidates independently with the same
prompt. Rule: both `o` → include; both `x` → exclude; anything else → human decision below.

| outcome | rows |
|---|---:|
| both `o` → include | 25 |
| both `x` → exclude | 0 |
| needs a decision | 26 |

**Included without discussion (25):** p20, p38, p41, p43, p44, p48, p49, p16, p17, p22, p24,
p26, p29, p30, p32, p34, p35, a16, a17, a18, a23, n01, n04, n09, n10.

Every rewritten question proposed below was checked against the generator's anti-lexical
filter (`copies_trigram` on each span, `jaccard` ≤ 0.5 vs each snippet) and passes.

**How to answer:** reply per group, e.g. `G1 ok, G2 ok, G3 ok except p18, G4 rec, G5 drop both`.
"rec" = take the **Rec** column.

---

## G1 — both reviewers say `?` and agree on the fix (5 rows)

| id | issue (both) | fix | Rec |
|---|---|---|---|
| p45 DDOG | "Timing and size of … 2029 debt issuance" asks two attributes | Question → "How much debt principal did Datadog raise through its 2029 Notes issuance?"; keep both occurrences | apply |
| a24 GOOGL | "borrowing capacity and maturity schedule" asks two things; "unused" not in span | Question → "When do Alphabet's revolving credit lines expire?"; keep occurrence | apply |
| a25 CAT | "purchase price and closing schedule" asks two things | Question → "What purchase price did Caterpillar expect to pay for RPMGlobal?"; keep occurrence | apply |
| n05 COST | Alternatives 1–2 are evergreen statements, not FY2025 drivers | Drop COST-2025-083984 and COST-2025-084633; keep COST-2025-094148 | apply |
| a19 LLY | Alternatives 1–2 never mention capital spending | Drop LLY-2025-081769 and LLY-2025-202988; keep LLY-2025-214383 | apply (see note) |

Notes:
- p45/a24/a25: `compound_query()` in `generate_candidates.py` deliberately allows a bare noun
  "and" ("timing and size … is one fact cluster"). Both reviewers independently overrode that
  heuristic; a25's pairing was suggested by the Round-1 reviewer. Applying the fix makes the
  three rows consistent with the strict single-intent rule.
- a19: B additionally proposes moving the highlight to "These investments, and other capital
  investments …". That sentence **was the Round-1 snippet the human reviewer rejected**
  ("粗體字選錯句了"). Rec: keep the current highlight.

## G2 — both say `?`, fixes differ (3 rows)

| id | A | B | Rec |
|---|---|---|---|
| n07 AXON | Add the unlisted Item 1A subscription-model location **and** drop AXON-2025-012871 (revenue-source list, partial) | Add the same Item 1A location; keep AXON-2025-012871 | A (low stakes either way) |
| n02 LLY | Trim alternative 2's snippet to its first sentence (current snippet crosses a paragraph break); keep its span | Extend alternative 2's span back to the revenue-components table and re-anchor the snippet on the table | A — B's fix adds a third table-anchored snippet, which is format-fragile across arms |
| n03 PLD | Drop PLD-2025-030022 (rent-change metric, not a stated revenue driver) | Expand spans of PLD-2025-030022 and PLD-2025-130013 backward to include their causal sentences and re-pick snippets | A (simpler); B keeps more coverage at the cost of re-anchoring two spans |

## G3 — only A says `?`, B says `o` (14 rows)

**G3a — lexical give-away (question copies snippet wording)**

| id | copied phrase | proposed question | Rec |
|---|---|---|---|
| p37 AMZN | "manufacture and sell" (fails generator 3-gram rule) | "What consumer hardware products does Amazon make?" | apply |
| a20 PODD | "$66.7 million increase" (fails 3-gram rule) | "What investments drove Insulet's higher capital spending in 2025?" | apply |
| a21 COIN | "regular trading of crypto assets" (fails 3-gram rule) | "Does Coinbase actively trade the crypto it keeps on its balance sheet as an investment?" | apply |
| p21 COIN | "International revenue comprised mainly" reordered (passes 3-gram, same words) | "What kind of revenue does Coinbase mostly earn from non-US customers?" | apply |
| p18 DDOG | "export … authorization", "sales opportunities" | "Could U.S. export controls delay or cost Datadog customer deals?" | apply (judgment call) |

**G3b — span does not name its subject (antecedent outside the span)**

| id | problem | fix | Rec |
|---|---|---|---|
| p33 NVDA | Snippet says "it … 10x reduction in cost per token"; "Rubin" is in the previous sentence | `query_type` factoid → passage; span starts one sentence earlier (Rubin production-shipment sentence); snippet unchanged | apply |
| a22 AMZN | "We will capitalize certain of these costs …" without the satellite-network sentence | Span starts at "We currently expense the majority of the costs associated with the development of our satellite network …"; snippet unchanged | apply |
| p36 PODD | "these glucose values" without the CGM sentence; question copies "adjust insulin dosing" | Span starts one sentence earlier (Pod obtains glucose values from the CGM); snippet unchanged. Optional question rewrite: "How does Omnipod 5's algorithm automate insulin delivery from CGM data?" | apply span; question optional |

**G3c — snippet robustness / missing location**

| id | problem | fix | Rec |
|---|---|---|---|
| n08 DECK | Answer text also exists in **Item 7** (block start); T1's "no Item 7 copy" note is wrong → false negative. Item 1 snippet crosses a mid-sentence paragraph break | Snippet → "under three proprietary brands: HOKA, UGG, and Teva." (52 chars, exact in both); add the Item 7 location as alternative 2 | apply (factual) |
| p23 DECK | Snippet crosses a paragraph break ("74,100, ⏎⏎ compared to …") | Snippet → "We experienced an increase of 6.2% in the total volume of units sold to 78,700 from 74,100," | apply |

**G3d — p50 LIN (largest change)**

The Round-2 rewrite asks for generic exposed-data types ("confidential information or personal
data", boilerplate) and its snippet still contains the unresolved "such attempts" that caused the
Round-1 question to be abandoned. A: revert to the Round-1 intent — question "Have past
cyberattacks caused Linde meaningful damage?", snippet "To date, such attempts have not had any
significant impact on Linde's operations or financial results." (Item 1A), passage span starting
at the cyber-attack sentence so the span resolves "such attempts". B: approve as is.
**Rec: apply A** (alternative: drop the row).

## G4 — only B says `?`, A says `o` (5 rows)

| id | B's issue | B's fix | Rec |
|---|---|---|---|
| p25 CAT | Question omits Caterpillar and 2026; "how much" invites a dollar amount | "How much higher could Caterpillar's 2026 tariff burden be without its planned countermeasures?" | apply B |
| p28 NEE | "Retirement obligations" ambiguous (pension vs ARO); no company | "How sensitive were NextEra Energy's 2025 nuclear asset-retirement obligations to assumed decommissioning cost inflation?" | apply B |
| p31 XOM | Asks "how cultivate and retain"; snippet gives retention outcome only | B: "What does ExxonMobil report about employee retention under its career-oriented talent approach?" (reuses "career-oriented") | apply, with A's wording: "How well does ExxonMobil retain its career employees?" |
| p27 COST | Span "$6,000 to $6,500" lacks the "in millions" unit | Add "in millions of dollars" to the question | **no change** — the unit is a filing-wide convention; putting it in the query is unnatural and doesn't affect retrieval |
| n06 COIN | Each bullet is one component of the total change | Merge the three alternatives into one span over the bullet group | **no change** — all three bullets sit in one block, and one merged location with one snippet is stricter (a chunk boundary inside the group would cause misses) |

## G5 — A says `x`, B says `o` (2 rows)

| id | A's reason | Rec |
|---|---|---|
| p42 CAT | CIO's Audit Committee attendance frequency is governance trivia; the Round-1 reviewer approved but commented it has "沒什麼評估意義" | exclude |
| p40 DECK | Answer is a generic cybersecurity-program bullet ("periodically reviewing and updating our IRP, privacy policy …") and the question copies its wording | exclude |

---

## Size check

If every Rec is accepted: 51 − 2 (G5) = **49 rows**. `round3_assembly_instructions.md` T7 expects
the human's final selection to land around 40 but forbids inventing rows. 49 is acceptable as is;
to get closer to 40, name which additional rows to drop.

## Housekeeping applied at assembly (no decision needed)

Several rewritten rows (p16, p17, p21–p27, p29, p30, p33, p35, …) carry a stale `curation_note`
that still describes the Round-1 question. T7 regenerates these notes to match the final question.
