# T12 NEE — pipeline-independent filing traversal

## Scope and result

- Ticker: `NEE`
- Fiscal year: `2025`
- Accession: `0000753308-26-000015`
- Active non-`multi_passage` candidates: `p28`, `n01`
- Excluded `multi_passage` candidates: `p14`, `a14`
- Full traversal coverage: `46/46` fixed neutral windows; `545,546/545,546` canonical characters
- Acceptable distinct occurrences: `p28 = 1`, `n01 = 2`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

The two `n01` occurrences are retained separately. The Item 7 annual summary and the later FPL
results narrative are different source locations that each explain the earnings effect of FPL's
regulated-asset investment, even though they communicate overlapping conclusions.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/0000753308-26-000015-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/0000753308-26-000015.txt)
- [Primary 10-K document](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)
- Filing date: `2026-02-13`
- Period of report: `2025-12-31`
- Primary document: `nee-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Complete-submission bytes: `31,454,405`
- Complete-submission SHA-256: `43e4b5fca98319f5b2a53384b03fa8781a91cdd9099ede79d2824716c28010dc`
- Primary-document bytes: `4,642,182`
- Primary-document SHA-256: `c9acc48394834880be0f585f88826d7ed2747cc59c31a293e0664aac78192249`
- Canonical visible-text bytes: `547,779`
- Canonical character count: `545,546`
- Canonical line count: `16,628`
- Canonical visible-text SHA-256: `53127b72ba77b6e4597050aef4f62b92ab79461f8bb376c8b266907dc40a90e0`

The exact `TYPE=10-K` document extracted from the complete submission identifies
`nee-20251231.htm`; after removal of the SEC `<XBRL>` transport wrapper and trailing newline, it
matches the separately downloaded accession-pinned primary document.

Canonicalization removed only non-visible transport content, inserted separators at neutral HTML
block boundaries, decoded entities, converted NBSP to ordinary spaces, normalized line endings,
collapsed horizontal whitespace per line, trimmed lines and collapsed three or more newlines to
two. It did not produce or use an Item, heading, block, sentence or repository-pipeline hierarchy.

Offsets below are zero-based and end-exclusive against exactly that canonical text. Filing
locations were assigned only after occurrence discovery and did not determine traversal order.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | [0, 12000) | `a5cacdc3f834a4a0a039d371aa47f0a5974e311b6e4addabb5d47804f4f6ed55` | inspected |
| W0002 | [12000, 24000) | `303d500e4e12941cc91fee75aa40c66e54e843ddd42d9ead26503f5ae0d620c2` | inspected |
| W0003 | [24000, 36000) | `19f672d1eaeb5df16b0b04f6fcfa59eb9d8a856ee0484aaff59f1e96b8388253` | inspected |
| W0004 | [36000, 48000) | `13b82abbe8904d1cfe5f180452e3ab76a313f7dfb00375081a36d5e774c20109` | inspected |
| W0005 | [48000, 60000) | `d869257b46a514c511b5fe475f3348b54a41f99ff8a28d5c3a5f7866976b0f0b` | inspected |
| W0006 | [60000, 72000) | `d1b7ecf467a92a78d03eaaf737ff9b62d00732a6d3a68a4d99b10b0cf5c45bc3` | inspected |
| W0007 | [72000, 84000) | `d1b912f757ccfb3e90db28156ae7ae0fdf6a0d810d560ff5d5b4825345fb3ec8` | inspected |
| W0008 | [84000, 96000) | `1bf2f964f487940693549500c9bf0c0e1345d811c383a3f5e39a6f8dd44bd25e` | inspected |
| W0009 | [96000, 108000) | `dd30eadeaaa57754280d68c94c8e0d5934f66e211b874aeaa1e0f4798fac3bdd` | inspected |
| W0010 | [108000, 120000) | `7d6c4436422a70c90fd3a9a7ac4c1ce5ef9a2a0a46f8a1ee3858311fa7710e2f` | inspected |
| W0011 | [120000, 132000) | `840376831a41ce99d8e6c51f8b12478b8f75276509eb5460f208874a87152692` | inspected |
| W0012 | [132000, 144000) | `fcfa088082eccdd5e6c131eeaa82f06e1b02db7b7c3e7add9dc365842244c24c` | inspected |
| W0013 | [144000, 156000) | `df5031e5a1c819d51382d74557429be55e5c02170fa96b8be6fb0b76c560915e` | inspected |
| W0014 | [156000, 168000) | `5f919c8ac0433ef5a2ae0e2fb9fa5527eaacf3f7cd6b844ed1268c57dc3ebaf8` | inspected |
| W0015 | [168000, 180000) | `55039e250cf63f4b523b0b550608bee384ea335a8d8d2d1278c99abbbf5d07d5` | inspected |
| W0016 | [180000, 192000) | `1e2a2b5f1e7a08b697038d0d8aaa8c33b0d7d3d2f2a7259e87066d7ff1343b9f` | inspected |
| W0017 | [192000, 204000) | `33bbf288c571df2a405b8f6805c0850b54e94c33aa44a0569694bdbdf65863ff` | inspected |
| W0018 | [204000, 216000) | `14eb968e700e81220529fe5dc55bc38b6b07671c6403788a49e8f7a120beb436` | inspected |
| W0019 | [216000, 228000) | `72b79edb68e15ee78c24b2ec8c94b568d4d56e40d8c12900861a39178dcee62c` | inspected |
| W0020 | [228000, 240000) | `fb115fd936f273b285f9f1c9dd3e5984fbed4f540918e125f571832bfa21b988` | inspected |
| W0021 | [240000, 252000) | `ba9e6141f18be56e1f4ed4d9d5ea6c0e2dc44328b645a345a6f969c2376f151f` | inspected |
| W0022 | [252000, 264000) | `fa76a062e64dd43d0b8b49ad4d0d52d75c48896aa7b9a0795760bb445472b36c` | inspected |
| W0023 | [264000, 276000) | `edda55d0e7ca6dc7530718d201095e50fb8fad01e4e3b435eb591e9dc1001850` | inspected |
| W0024 | [276000, 288000) | `90ae9c2607e087105680694de4fd928605ffd58cc77df875bf1af09bc808082a` | inspected |
| W0025 | [288000, 300000) | `771a9c77f754097a5dc44e291629d042908d6d2f3715699a8c6b8d125cbbdadd` | inspected |
| W0026 | [300000, 312000) | `7cc153b6e1f1186b15b04f496fe6b68b50932bbdfee04a6712a28ee911a4bf8b` | inspected |
| W0027 | [312000, 324000) | `f5b4fe2adae783404d97a0904df0fcc46f8c3a6d2416fc40525e41da35c6041f` | inspected |
| W0028 | [324000, 336000) | `f7b8d0538de124156f0ee4cd345827059dc0ce99f5b236b2d84e75a25bda6880` | inspected |
| W0029 | [336000, 348000) | `c03fe2401606822e4de45b99acef572f11511a5064b9452026dc42136ce85544` | inspected |
| W0030 | [348000, 360000) | `204affa63d22a7fc4ccbbe4f785a4b2c449424e262a9ced855440490a25c3ca0` | inspected |
| W0031 | [360000, 372000) | `b0bceb61f2568c53aed9914f2f2c5eb7f6b50bbe21ec08728a365cafd61687e7` | inspected |
| W0032 | [372000, 384000) | `c581da0461b3f48d9e5e11c3fd6554fb6e0d6f9d42025f4305b3a49f1ae82869` | inspected |
| W0033 | [384000, 396000) | `47d73c07410d8f90b6a389c664152d6528bf712b0475ecddde1ecb3cbc6a04e2` | inspected |
| W0034 | [396000, 408000) | `895466257c99406455ca2cfe42ac4f983e2f1c7c4c9469f4a8d93fe8d45f2613` | inspected |
| W0035 | [408000, 420000) | `6d72a153195397eae5b90d9afb4ea356f38ae3bbb7439c46683fd2ffd906f78a` | inspected |
| W0036 | [420000, 432000) | `c9206b8beb23ad214b10451c63618cee6787fcece0afc585017eca27c172a0b1` | inspected |
| W0037 | [432000, 444000) | `c955480411bf8e3fd9f98eb80dec4e512e00189d4849a99ec1db506a47003565` | inspected |
| W0038 | [444000, 456000) | `96c6cb65e1440d99e804f0d9024e5fe2db6016721a9e7056212dc86550c3b2d0` | inspected |
| W0039 | [456000, 468000) | `01ba78d87b8c6285482e21168a04601990a94091cac2cd73a462f551910e09a5` | inspected |
| W0040 | [468000, 480000) | `89f765ce56d0bb5e28231d80e5f0388249d3fa6f9535fc9fce36137091f0dce7` | inspected |
| W0041 | [480000, 492000) | `9c36e0d14997be3dda7df45edeeb6be3fd37c96eb663a497d09615943964e770` | inspected |
| W0042 | [492000, 504000) | `3471fcbe6e61c2fcdf731b47560b86abc6eb5f5ad1c0d2c3e28fff83d9dcfa35` | inspected |
| W0043 | [504000, 516000) | `d00accbf3798bca8f969be883c53c2d67ba310db87c0e397136f0cff0ec0b9fb` | inspected |
| W0044 | [516000, 528000) | `3127a7902b73b341e583ce3bc94bfffab32b32bcbed9b9d20767e953d35a9b2d` | inspected |
| W0045 | [528000, 540000) | `e9fdb64c15f2552414b5ff56e4a28c53d6ea017f18ee9bfd66a5937f822076ce` | inspected |
| W0046 | [540000, 545546) | `6269357c5a6a8f28cc3ba2e6d70be5c1987bcc55758acd86edfdb227547a61c4` | inspected |

Traversal checkpoints:

- `W0001–W0007`: cover, definitions and business descriptions for FPL and NEER.
- `W0008–W0014`: complete Item 1A risk factors.
- `W0015`: Item 1C, Items 2–6 and the start of Item 7.
- `W0016–W0022`: complete Item 7 and Item 7A. `W0016` contains both `n01`
  occurrences; `W0021` contains the sole `p28` occurrence.
- `W0023–W0041`: audit reports, financial statements and all financial-statement notes.
- `W0042–W0046`: Items 9–16, exhibits and signatures.

After sequential traversal, full-text cross-checks covered direct terms and plausible alternatives
for rate base, plant in service, investments, net income, earnings, asset retirement obligations,
inflation, escalation rates and nuclear decommissioning. No additional independently sufficient
occurrence was found.

## Candidate findings

### `p28` — keep question and evidence; one acceptable occurrence

- Candidate ID: `p28`
- Round 2 decision:
- Round 2 reviewer comment:
- Round 1 decision: `o`
- Round 1 question: `How sensitive were retirement obligations to cost inflation assumptions?`
- Round 1 comment: none
- Proposed question change: none
- Proposed query type: `passage`

The original evidence is the filing's only quantitative escalation-rate sensitivity disclosure.

Occurrence 1:

- Filing location: Item 7, Critical Accounting Estimates / Decommissioning and Dismantlement /
  Nature of Accounting Estimates
- Window and canonical snippet offsets: `W0021`, `[240952, 241132)`
- Canonical line: `3513`
- Character count: `180`
- Snippet SHA-256: `abc96cb89843ae4fae6d0b0441dbc867e51f9177bf3d0157534f7c6aee57fb95`

> For example, an increase of 0.25% in the assumed escalation rates for nuclear decommissioning costs would increase NEE’s AROs as of December 31, 2025 by approximately $179 million.

Broader retirement-cost methodology explains inflation assumptions but provides no other numeric
sensitivity. Note 11 reports ARO balances and revisions, not the effect of changing the escalation
assumption.

### `n01` — keep question; two acceptable occurrences

- Candidate ID: `n01`
- Round 2 decision:
- Round 2 reviewer comment:
- Candidate type: new intent-first question
- Question: `How did growth in FPL's regulatory capital base affect its 2025 earnings?`
- Proposed question change: none
- Proposed query type: `passage`

Both locations explain that regulated-asset investment increased FPL earnings. The second source
also quantifies average-rate-base growth at approximately `$5.5 billion` in its surrounding answer
span. The concise snippet anchors the causal earnings statement and remains within the global
limit.

Occurrence 1:

- Filing location: Item 7, Overview / 2025 Summary
- Window and canonical snippet offsets: `W0016`, `[180298, 180457)`
- Canonical line: `2237`
- Character count: `159`
- Snippet SHA-256: `bfe5a80a782bda6fe380f077866ccaf8eb54de6b084bd6934e873c05e31ab94e`

> FPL's net income increased in 2025 primarily driven by continued investments in plant in service and other property and a higher earned regulatory ROE in 2025.

Occurrence 2:

- Filing location: Item 7, FPL Results of Operations
- Window and canonical snippet offsets: `W0016`, `[183888, 183997)`
- Canonical line: `2259`
- Character count: `109`
- Snippet SHA-256: `c094d4e062e8ad6531baac73afc497625e8451a55f2d43f9f20f462a5d4b9cfa`

> The increase was primarily driven by higher earnings from investments in plant in service and other property.

The occurrence's continuous answer span begins with the disclosed `$469 million` net-income
increase and continues through the statement that the same investments grew average rate base by
approximately `$5.5 billion`. The separate 196-character rate-base sentence is not accepted alone
because it does not state the effect on earnings. The reserve-amortization and regulatory-accounting
descriptions explain rate mechanics rather than another occurrence of the 2025 earnings result.

## Open human decisions

1. `p28` remains unchanged; its single quantitative sensitivity occurrence is within the global
   snippet contract.
2. `n01` remains unchanged and retains both source occurrences. The second occurrence uses the
   causal sentence as the canonical snippet while preserving the surrounding rate-base sentence in
   `answer_span`; human review should confirm that this is sufficiently self-contained for the
   intended retrieval contract.

All three snippets are unique exact substrings of the canonical text and contain 50–200 characters.
All Round 2 review fields are intentionally blank.
