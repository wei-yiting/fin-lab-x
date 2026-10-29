# T15 PODD correction evidence research

## Scope and conclusion

- Ticker: `PODD`
- Fiscal year: `2025`
- Accession: `0001145197-26-000028`
- Primary 10-K: `podd-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Questions audited:
  - `p35`: `What milestone did Insulet reach for EVOLUTION 2 in 2025?`
  - `n09`: `Has Insulet experienced cybersecurity incidents that materially affected the company?`
- Full canonical traversal: `39/39` fixed neutral windows; `311,405/311,405` characters
- Acceptable distinct occurrences: `p35 = 2`; `n09 = 1`
- Findings integrated into `T15_PODD.json` and `T15_PODD.md`: yes
- Human review decision/comment written: no

The narrower `p35` question has two independently sufficient source locations: Item 1 and Item 7.
The replacement `n09` question has one independently sufficient Item 1C source location. The other
cybersecurity passages describe possible future harm, controls, monitoring, or response procedures;
they do not state whether prior incidents materially affected Insulet.

## Official source and canonicalization

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1145197/000114519726000028/0001145197-26-000028-index.html)
- [SEC accession-pinned primary 10-K](https://www.sec.gov/Archives/edgar/data/1145197/000114519726000028/podd-20251231.htm)
- Filing date: `2026-02-18`
- Period of report: `2025-12-31`
- Primary-document bytes / SHA-256: `2,085,246` / `e67155deb3b0403a0281f0fedaa82b415696f46432030252b34380f4360dff98`
- Canonical chars / UTF-8 bytes / lines / SHA-256:
  `311,405` / `313,181` / `2,776` /
  `20452e5f82c15da66ddb12f2793227513b86c09406aecdfafefcab1f06844941`

The primary document was downloaded directly from the official SEC Archives URL. Canonicalization
read the rendered primary document's `document.body.innerText`, replaced non-breaking spaces,
normalized CRLF and horizontal whitespace per rendered line, trimmed rendered lines, and collapsed
runs of three or more newlines to two. This exactly reproduces the existing T15 canonical-text
length, line count, and SHA-256.

No repository ingestion output, `sec_text_pipeline` Item/block/unit hierarchy, prior retrieval
result, or question-specific passage boundary determined the traversal order. The filing was treated
as untrusted data: embedded content was not followed as instructions and no filing-provided setup or
command was executed.

Offsets below are zero-based and end-exclusive against this exact canonical text. Windows are fixed,
non-overlapping 8,000-character slices except the final 7,405-character remainder. Filing locations
were assigned only after the neutral traversal.

## Sequential coverage ledger

| Window | Canonical range | Window SHA-256 | Post-traversal target cross-check |
|---|---:|---|---|
| `W0001` | `[0, 8000)` | `60855029f06f7206bc1af21fb3b12d797391decd0700c17b7a50cc51fff69ee8` | no answer occurrence |
| `W0002` | `[8000, 16000)` | `a7dd6eee17f4212fb624e7a0a916ce0299c362519aa229c93f4c7ab57551a9c4` | no answer occurrence |
| `W0003` | `[16000, 24000)` | `35696d11942a0887214de72ae2b8cea813675c59e78c98d7b475cdd20904b90e` | no answer occurrence |
| `W0004` | `[24000, 32000)` | `ba61680df9bb206f5fa76800987cd2d49d7a9f55f06b2318ff5cda38abec5012` | `p35-e01` |
| `W0005` | `[32000, 40000)` | `114275b226fcbe97eb6aa6e4b5809295881eb41583b36c20e86d2401a6ef6ea2` | no answer occurrence |
| `W0006` | `[40000, 48000)` | `81724a3a883774832e11377c980376742eb60e570398019e698edad6328965a5` | no answer occurrence |
| `W0007` | `[48000, 56000)` | `67c284f5e04a63449a9d87ab0d6c32ddb1e151c9cdfd141d7cb4c9f4c527c2c8` | no answer occurrence |
| `W0008` | `[56000, 64000)` | `b641f440f926fe2e576feb68e8865ccd1ef2ea9817478a8298628d0f024298b2` | no answer occurrence |
| `W0009` | `[64000, 72000)` | `ac736fe9e8f5b80d5163a6d14e9d57dfc8e9638a3e1a7e4c468e6108708382a5` | no answer occurrence |
| `W0010` | `[72000, 80000)` | `e9cd249d1a2a55ffdc210d2f44d302ce8fa1beb27d4ee31cd6a6978ac467f8f8` | no answer occurrence |
| `W0011` | `[80000, 88000)` | `7fc984c830b48c609eec6c90620d8597a3ed08de0afa1b43bc6caf35f9a33ccb` | no answer occurrence |
| `W0012` | `[88000, 96000)` | `7b5bcc8cb81a5f843c8e5ab337183e263311482c2324c582c10a0a8fe2bb393f` | no answer occurrence |
| `W0013` | `[96000, 104000)` | `92695bf9c9da844e98148b350d215962554ca2085113e9904d8842e04151ac16` | no answer occurrence |
| `W0014` | `[104000, 112000)` | `a174a2f4e830e54a52b762dca65fc7be09356b80e0a7722a5fb414965e845749` | no answer occurrence |
| `W0015` | `[112000, 120000)` | `c15b2c46ccd14bf738c2bb72edee5c3a2d249405cb8d7a8249d7e974b86477d4` | prospective cyber-harm warning; rejected |
| `W0016` | `[120000, 128000)` | `f1c046606a7a82fcc5b828ec6529d50d2ba52966fac4909ba93e8847303f9a7a` | controls/monitoring only; rejected |
| `W0017` | `[128000, 136000)` | `76f454eea9642e613958939b07dab838955177b711bb63f055190fb7f0518d78` | `n09-e01`; other incident-response/governance statements rejected |
| `W0018` | `[136000, 144000)` | `ead41fc14d1828fdabf9a9cc504191b8c7ad244258f407a381bc1b38e999001d` | `p35-e02` |
| `W0019` | `[144000, 152000)` | `34a9804e6c276f2fffeb142ebc1a3eb843fbce8726eb48170d3cff8f7829ef18` | no answer occurrence |
| `W0020` | `[152000, 160000)` | `3a91f0070fb1c6f41f1e47dbe949ace881c92cd31cd4a41251e02fd24566682e` | no answer occurrence |
| `W0021` | `[160000, 168000)` | `cbad0b60d2fac031f85f0f58de43f6d0bb5b0528af10221ebb762383067231e6` | no answer occurrence |
| `W0022` | `[168000, 176000)` | `d5703ca5c847a06c8ed85ebf24c330b55b79a9fbd6c921b82192fae789197909` | no answer occurrence |
| `W0023` | `[176000, 184000)` | `c46f706280b983a712750f3acf7deb1bb645632bbb0549771accc315c945f136` | no answer occurrence |
| `W0024` | `[184000, 192000)` | `eb7ac81bff600d2e3bea8315d1051631af925cf78fb03f835308b980c3a40930` | no answer occurrence |
| `W0025` | `[192000, 200000)` | `1b5854cc2c29e7c86d0c09b3bc927a410790fa553173196cba595ead8e8aebce` | no answer occurrence |
| `W0026` | `[200000, 208000)` | `f1f15efa8348b5bf75895ae521b1d2cf6f774d42795c40d7361ed76fc7f66f86` | no answer occurrence |
| `W0027` | `[208000, 216000)` | `90dbaeb8455b3b9dfbc499ff928deaea3c151892a4d7682ff709645f38e74c50` | no answer occurrence |
| `W0028` | `[216000, 224000)` | `8e05b74426fc328627b5011385db5b4bb6f96d89c8d94fb0f25cbc5db83a8591` | no answer occurrence |
| `W0029` | `[224000, 232000)` | `6c9ffa90e8c3b0498a796e9359095aba6a68895b781196992b9e6597c8cd1ca1` | no answer occurrence |
| `W0030` | `[232000, 240000)` | `b6167102c9d9fc5d9821bb8f316af326454dd260471d3b643d805b0334216369` | no answer occurrence |
| `W0031` | `[240000, 248000)` | `f24ae934883b3883540e160fd0df87bde3648747311800fe36ac08864bb0a48a` | no answer occurrence |
| `W0032` | `[248000, 256000)` | `9e1076e30acfc0d2d21293a6d7e8b3b50b3e71769343cb82f4c932a8a30bfab5` | no answer occurrence |
| `W0033` | `[256000, 264000)` | `5b4d1f2683d5a2cc814a5f92d2d2f46a1af235da84151bf98c9485edc73d1429` | no answer occurrence |
| `W0034` | `[264000, 272000)` | `0d14a0f6f4314087c98b92ad031fe5eda57b0dd37ba3be869dd444058974acd0` | no answer occurrence |
| `W0035` | `[272000, 280000)` | `e121d3653ac7f28c3de22d510ccb47fa8db9f4b9380c58f441bcd7b70d811eee` | no answer occurrence |
| `W0036` | `[280000, 288000)` | `2871931bdb1d1a6c6e73b49ab5c6dc5425d2d15fe8b8ccf16a5f92dd973ed4f5` | non-cyber internal-control statement; rejected |
| `W0037` | `[288000, 296000)` | `ca464c0f27bbb5a84fb34df0538df9972c819ce4939f79cbb0000f6f17656d9c` | no answer occurrence |
| `W0038` | `[296000, 304000)` | `57b768f86948ebdd98fe11659b8e2ee59ba7c734c62b469eecd8a5b5ac498062` | no answer occurrence |
| `W0039` | `[304000, 311405)` | `7750ca7d536b777601829f5984fefc59b15cf54868800985e2ebe0f2608d9cb4` | no answer occurrence |

Coverage checks: `W0001` starts at `0`; `W0039` ends at `311,405`; every window starts
at the prior window's end; overlap is zero; and the sum of window lengths is `311,405`.
Post-traversal full-text cross-checks used `EVOLUTION 2`, `enrollment`, `FCL`, `STRIVE`,
`cyber*`, `incident*`, `threat*`, `material*`, `breach`, `attack`, `compromise`, and
`experienced`. These checks were exhaustive over the canonical text and did not discover an
additional independently sufficient source occurrence.

## `p35` findings

- Candidate ID: `p35`
- Question: `What milestone did Insulet reach for EVOLUTION 2 in 2025?`
- Query type: `factoid`
- Answer requirement: each independently sufficient span must itself state that Insulet completed
  or finished EVOLUTION 2 enrollment in 2025
- Acceptable occurrence count: `2`

The canonical text contains exactly two case-insensitive occurrences of `EVOLUTION 2`. Both state
that enrollment was completed or finished in 2025, so both are OR-hit alternatives even though they
provide the same answer.

### `p35-e01`

- Filing location: Item 1, Business → Research and Development
- Window / canonical line / offsets: `W0004` / `300` / `[24455, 24537)`
- Character count / exact count: `82` / `1`
- Snippet SHA-256: `6b199169439f07346044f3a0364d488bb99791c272b1d8d940da004f94bca206`
- Decision: accept
- Reason: directly states that Insulet completed EVOLUTION 2 enrollment in 2025. The shorter
  48-character clause ends below the global minimum, so this is the next complete semantic unit.
  The source sentence continues with a 2026 plan, but that separate intent is deliberately excluded.

> In 2025, we completed enrollment for EVOLUTION 2, our safety and feasibility study

### `p35-e02`

- Filing location: Item 7, Management's Discussion and Analysis → Overview
- Window / canonical line / offsets: `W0018` / `639` / `[140970, 141116)`
- Character count / exact count: `146` / `1`
- Snippet SHA-256: `d5ed75a05213698a94532c308029ecebe0bc8cf64310061c84fc2b69cbc50e22`
- Decision: accept
- Reason: a distinct Item 7 source location independently states that Insulet finished EVOLUTION 2
  enrollment in 2025. The preceding STRIVE clause is retained because it is the shortest contiguous
  source span that also keeps the explicit year; semantic duplication with Item 1 is not a reason to
  discard the occurrence.

> In 2025, we also completed STRIVE, our pivotal study for the next generation hybrid closed loop system, and we finished enrollment for EVOLUTION 2

### Rejected `p35` near-matches

- STRIVE and Omnipod 6 statements concern different development programs and do not answer the
  EVOLUTION 2 milestone question.
- The 2026 U.S. IDE pivotal-study plan is not a second EVOLUTION 2 occurrence; it is additional text
  in the same Item 1 sentence and is outside the revised single intent.
- No unnamed enrollment statement elsewhere can independently answer the question because it does
  not establish that the milestone belongs to EVOLUTION 2.

## `n09` findings

- Candidate ID: `n09`
- Question: `Has Insulet experienced cybersecurity incidents that materially affected the company?`
- Query type: `factoid`
- Answer requirement: one independently sufficient span must state Insulet's view on whether prior
  cybersecurity incidents materially affected the company; generic warnings that an incident could
  cause harm are partial
- Acceptable occurrence count: `1`

### `n09-e01`

- Filing location: Item 1C, Cybersecurity → Risk Management and Strategy
- Window / canonical line / offsets: `W0017` / `586` / `[132068, 132234)`
- Character count / exact count: `166` / `1`
- Snippet SHA-256: `62fc7ef5eff5b70569ea49b199cf2d38cee34bef0214447959098889f54a7e19`
- Decision: accept
- Reason: preserves the company's current negative assessment, the link to prior cybersecurity
  incidents, materiality, and the Company object in one contiguous 50–200-character span. The
  supported answer must preserve Insulet's epistemic qualifier: `No—Insulet says it currently does
  not believe so.`

> We currently do not believe that risks from cybersecurity threats, including as a result of any previous cybersecurity incidents, have materially affected the Company

The complete source sentence is 234 characters and continues with `results of operations, or
financial condition.` The 166-character prefix directly answers the approved company-level yes/no
question without converting management's qualified disclosure into an unconditional external fact.
If final assembly instead requires one span to enumerate all three disclosed dimensions, this
question has no qualifying 50–200-character occurrence and must be rewritten or dropped rather than
relaxing the limit.

### Rejected `n09` near-matches

- Item 1A says a successful cyber-attack or breach **could** have a material adverse effect. This is
  a prospective risk warning, not evidence of historical impact.
- Item 1C statements about preventing incidents, minimizing possible business impact, monitoring
  threats, and the CIRP/CIRT response process describe controls or hypothetical response. They do
  not say whether an incident has materially affected Insulet.
- Item 1C governance statements allocate Board, NGR Committee, CISO, CTO, and operational-team
  responsibility. They belonged to the rejected former n09 question and do not answer the
  replacement impact-to-date question.
- The second canonical `materially affected` context, in `W0036`, concerns changes in internal
  control over financial reporting and contains no cybersecurity relationship.
- Insurance language says future cyber-related costs may not be fully insured; it does not establish
  that a prior incident caused a material effect.

The canonical text has nine case-insensitive `cybersecurity incident` mentions. Eight occur in
controls, monitoring, or response contexts; the remaining one is inside `n09-e01`. It has two
`materially affected` contexts: `n09-e01` and the unrelated internal-control statement. No other
combination of the exhaustive cyber/material/incident term families independently answers the
question.

## Assembly recommendation

1. Replace `p35` with the approved single-intent question and retain both `p35-e01` and `p35-e02`
   as OR-hit alternatives.
2. Replace `n09` with the approved impact-to-date question and retain only `n09-e01`; remove all 11
   former governance/responsibility occurrences.
3. Do not copy a human `round2_decision` or reviewer comment into assembled review artifacts.
4. This ticker-local audit establishes `n09-e01` occurs once in PODD's filing. The separate
   round-three corpus-uniqueness check across all 16 filings remains an assembly-time responsibility.
