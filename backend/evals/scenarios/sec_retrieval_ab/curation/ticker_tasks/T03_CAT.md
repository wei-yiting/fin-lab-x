# T03 CAT — pipeline-independent filing traversal

## Scope and result

- Ticker: `CAT`
- Fiscal year: `2025`
- Accession: `0000018230-26-000008`
- Active non-`multi_passage` candidates: `p25`, `p42`, `a25`
- Full traversal coverage: `56/56` fixed neutral windows; `442,003/442,003` canonical characters
- Acceptable distinct occurrences: `p25 = 1`, `p42 = 1`, `a25 = 2`
- Human review fields changed: no

The second `a25` occurrence is not redundant for retrieval grading. The same disclosure appears once in Item 7 and once in Note 25; both independently answer the revised question and therefore must be separate OR-hit alternatives.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/0000018230-26-000008-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/0000018230-26-000008.txt)
- [Primary 10-K document](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)
- Filing date: `2026-02-13`
- Period of report: `2025-12-31`
- Complete-submission SHA-256: `1aade6920a2dcda891c91c4ff774d311be6d98963e497e305c0f729a00f8d972`
- Primary document: `cat-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Primary-HTML SHA-256: `ada3cc5dace5a2b16c4e05b5c888f33b2eae69a9d6076aff5e0b27825e5f9bbe`
- Canonical visible-text SHA-256: `546ce9a5401f9dea2a3ee8c9236452262bc1ff7e65bd1ecd686ee519bb7a6f5a`
- Canonical character count: `442,003` (including the final newline)

Canonicalization is independent of the repository's SEC pipelines. Python 3 and `lxml.html.fromstring` select the SGML `<DOCUMENT>` whose type is `10-K` and sequence is `1`, then take its `<TEXT>` body. The traversal drops `script`, `style`, `noscript`, `svg`, `input`, tags whose names end in `hidden`, elements with a `hidden` attribute, and elements whose normalized inline style contains `display:none` or `visibility:hidden`; `drop_tree()` preserves tail text. It inserts line breaks at `br` and common block elements, serializes with `etree.tostring(method="text")`, unescapes HTML entities, converts NBSP to spaces, removes zero-width spaces, normalizes line endings and horizontal whitespace, strips each line, collapses three or more newlines to two, and ends with one newline.

Offsets below are zero-based and end-exclusive against exactly that canonical text. No Item/block/unit hierarchy or prior retrieval output determined traversal order or coverage.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 8,000-character slice except the final remainder. Window SHA-256 values make the reviewed boundaries reproducible.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W001 | [0, 8000) | `ced277f8927795549cb2107589aa7ccdee58f8cd333fb06a453cc1c526e6ccb8` | inspected |
| W002 | [8000, 16000) | `225325f26d16544eb138d02969555b5889c14725f116ddae204744cba83b84d4` | inspected |
| W003 | [16000, 24000) | `29c39b15d63d5f2cf4c0506b960fa13aa708b0bd81e6a779ddb476909410cf8a` | inspected |
| W004 | [24000, 32000) | `b1e1166f763ba59ef5c6ef338281114700b69fbb2bd67c3222247ac6e908c848` | inspected |
| W005 | [32000, 40000) | `a44ed93524819fad955a8656f72a209b0712bed74779b38a37b4d3e0130a9ec0` | inspected |
| W006 | [40000, 48000) | `cd194cb20090a8336467dd3e4b59e63ca09c14a64c0efc7cf1fd76e1445ed656` | inspected |
| W007 | [48000, 56000) | `7f8357857f3fa9dfb9477b61eed58bfbf98b44f2f8f362a85c42a47b94ecdab8` | inspected |
| W008 | [56000, 64000) | `873e3c04aea2e306587c2c2c7a163ba43768cebfb2e2a1ab00ca648df076fcb3` | inspected |
| W009 | [64000, 72000) | `5acf76b2e6fa624a701aca8dcaa6e1ac081afbf152edd0c07e52422d47009e8d` | inspected |
| W010 | [72000, 80000) | `a1395c6122316f3cd5505c18baf1c951dbd53fd30e8522bceba3bb160656c75d` | inspected |
| W011 | [80000, 88000) | `b795ff6a371198ef72d5783950756f654bccbb540860e4b16d050544442404c5` | inspected |
| W012 | [88000, 96000) | `37f5f514b02404bd43cfed70ae2048a1067140ff4fd2916f535e895ec7075d9c` | inspected |
| W013 | [96000, 104000) | `7c929780a69a27619374cd7976ad639bc0f0cb58495f5271d140fab910529414` | inspected |
| W014 | [104000, 112000) | `71209895a6605033552c1f5064151af275108e8ef91113f9c4e3d23a899ad69e` | inspected |
| W015 | [112000, 120000) | `c47992a247bd9adbabbbcd248b05e084433d8922958d35c1ac08450c13fbf407` | inspected |
| W016 | [120000, 128000) | `cb71708a360eae9240029625c7ec6509342a9ede9556b268a342c809d76ef52f` | inspected |
| W017 | [128000, 136000) | `dc580046a67b6be3fc69855e8ef7d58256914d62aadad092dce8cf021d0092e4` | inspected |
| W018 | [136000, 144000) | `767f7114e0097bd0975b2c508b5bdab5c12fe5ae02a2a8fb571aa21384cc5eca` | inspected |
| W019 | [144000, 152000) | `f0f357f200565b4683a83b8625e27416a7b370f4c3af5d91504a5350f69a9ebb` | inspected |
| W020 | [152000, 160000) | `a3881f28b4c91ec0a710e3f03ad99cd6122303590e41bea3efda72d9b986d0da` | inspected |
| W021 | [160000, 168000) | `e9c419d92022b3720b0686e7e60ff22a8842f2b2612a0be37a774a1c2dc50033` | inspected |
| W022 | [168000, 176000) | `b3d5d6d9cc30fa9247eaadd4d9a171e2bf4da461871262d86b48db9476d4a8eb` | inspected |
| W023 | [176000, 184000) | `f4a5a9dc5f228dc62039e579b77b9aa380ca8557299f0abcb6c8267931100dd2` | inspected |
| W024 | [184000, 192000) | `04659b0fd2072a05fba2fb301e817e577128edc591dc7cc3b0891d39df0c7f13` | inspected |
| W025 | [192000, 200000) | `cee3a6817c76b3731e5da8da455a22d75487326deacc23e25f11d03dff8c18e5` | inspected |
| W026 | [200000, 208000) | `973e89db7311752119cc40ababfb15e9a44a6f3669e67f936428b62a67690e48` | inspected |
| W027 | [208000, 216000) | `86cb6e0cfe6ea5d97f32d838599604b54ac361e666c34e7b546a7d26a323f4bf` | inspected |
| W028 | [216000, 224000) | `0d70505a6b739e21814d11717d29b6fd928541e26aecce1d7c80d9c16f353a08` | inspected |
| W029 | [224000, 232000) | `81c1d0989313aacbf407c1c8a236ed252f1b54c01c0c72512fda2d25e2ce787e` | inspected |
| W030 | [232000, 240000) | `156dc590ce5e74dc33773856dbeb00ae9a241a8af8816218ce42ec81f3a98f3e` | inspected |
| W031 | [240000, 248000) | `492ad78409007ca3ae82e45fad4540884b9c0e201e558fe3431b55d55d999e5f` | inspected |
| W032 | [248000, 256000) | `896454121009bbc695b813459bf1b21fc1c4eec71c2a5fbb68a0f4fe27361cad` | inspected |
| W033 | [256000, 264000) | `a12f4d7fbd2f700bc1e4521198ba5fd3d200300d715e80747e0a6698d915d2ce` | inspected |
| W034 | [264000, 272000) | `419868c030fb3a7890adf273bbc1e1b255fd8895ca85fd0bb72a3b9610df1f93` | inspected |
| W035 | [272000, 280000) | `aa2229c8cf396064e59dc6d38ddfef105e65df7f297c910b93cf5da5887177b2` | inspected |
| W036 | [280000, 288000) | `d746e8378675398c345f3bf346eb4f2fd38722d9cd897e9e8d9112c0dfcd7369` | inspected |
| W037 | [288000, 296000) | `c1a9bfe6dbe98e4393a0f79ceea263cc6615d0db4996ba77ff748878a72ae893` | inspected |
| W038 | [296000, 304000) | `94cecce42018a61ada32d99089e2ceb1933a1693f912f0e9a2462e41fa1ca55e` | inspected |
| W039 | [304000, 312000) | `08cd88631c206ce330e2f514cc11d574cb026ad0f674361630c02acc4e96920a` | inspected |
| W040 | [312000, 320000) | `8109bf490872a4faaf5356db2c8b1281c8930726ab4c934ab559c59cdb8cf354` | inspected |
| W041 | [320000, 328000) | `bd2b284841e3a3e5988d50d524e4260b36f4806d94e709e4bd4c6e8876151416` | inspected |
| W042 | [328000, 336000) | `e253b78f41bfc17284ba2779fd3f92020d8e07c0ec6a1c8ad8cd57fd10ff8dbe` | inspected |
| W043 | [336000, 344000) | `84425e63c22169affa9c0b8d21d2f467a95079d59ffbdb1d3749eaec9e3355c3` | inspected |
| W044 | [344000, 352000) | `81d3bbd834a0799ecc1b658ad2efd05ce430bcb77097541235c9e90f2dd6158b` | inspected |
| W045 | [352000, 360000) | `8d720ee5b14e21739bca71c654f465093be07e8a96e0027c1e57908ecb433c2a` | inspected |
| W046 | [360000, 368000) | `721254e7db56621f61c1a8892b2b4254efc3da2a754fb9f11446e50f335929d4` | inspected |
| W047 | [368000, 376000) | `bbdaa3ab02d4e295454439510658b146dcc5ce6962bac642a8a5add3091c25d5` | inspected |
| W048 | [376000, 384000) | `32f21dccaadde148baa2962fa3d901d1908e7b2870bea11c18f3fbd463c01a19` | inspected |
| W049 | [384000, 392000) | `4533514f25533f3d422cf39e0908288da28491472850618aa28d6cd40eece922` | inspected |
| W050 | [392000, 400000) | `00285030f315b0da3a78bbd3ff2e609550eef97c12bfe60d1ca873e9eaa2ffb9` | inspected |
| W051 | [400000, 408000) | `c2bea758d2231ee7800a28334154a454a312aa9a2f396fe188d021096c652e72` | inspected |
| W052 | [408000, 416000) | `9d834fa0deedb4ebb149609ae3d113cc0065cb1c191ec0633b50b8d87c914802` | inspected |
| W053 | [416000, 424000) | `852c5610e9b5ccd7a813958009bd4a77f325ba0fa6433c4206ba63f586fdfce7` | inspected |
| W054 | [424000, 432000) | `7c50c5aaa63b9f74cba147e6d7dd9b802bb4e62431366aec5fa3578995a874bc` | inspected |
| W055 | [432000, 440000) | `f90b6c8ca7289b213a82782cfb33b9b8765d19a13db1b2ed15c6929cb34d876f` | inspected |
| W056 | [440000, 442003) | `a6080a92595bc661a03a49225d4e2112b32ac6741e29aeb7eb6767637441af2b` | inspected |

Traversal checkpoints:

- `W001–W006`: cover, Item 1, businesses, products, dealer network, human capital and environmental matters; no acceptable occurrence.
- `W007–W012`: risk factors. Generic tariff/trade references do not state the no-mitigation amount; generic acquisition and cyber risks do not answer `a25` or `p42`.
- `W013–W014`: Item 1C. `W014` contains the only CIO attendance-frequency occurrence.
- `W015–W022`: Item 7. `W016` contains the only no-mitigation tariff occurrence; `W022` contains the first RPMGlobal occurrence.
- `W023–W028`: critical accounting estimates, sensitivities, non-GAAP reconciliations and supplemental financial data. Audit Committee references concern accounting-assumption review rather than CIO attendance.
- `W029–W032`: Item 7A, financial statements and Notes 1–2; no acceptable occurrence.
- `W033–W048`: Notes 2–21. `W036` says derivatives risk practices are presented to the Audit Committee at least annually, but does not involve the CIO and cannot answer `p42`.
- `W049–W052`: legal matters, segment information, restructuring and Note 25. `W052` contains the second RPMGlobal occurrence.
- `W053–W056`: Parts III–IV, exhibit index and signatures; no acceptable occurrence.

After sequential traversal, full-text cross-checks covered direct terms and plausible alternatives: tariffs/import duties/customs/levies/mitigation; CIO/Chief Information Officer/Audit Committee/meeting cadence; and RPMGlobal/acquisition/closing/completion/purchase price. These checks found no additional independently sufficient occurrence.

## Candidate findings

### `p25` — keep question; one acceptable occurrence

- Round 1 decision: `o`
- Current question: `How much could tariffs cost without planned mitigation?`
- Recommended question change: none
- Acceptable occurrence count: `1`

Occurrence 1:

- Filing location: Item 7, `OVERVIEW` → `Full-Year 2026 Company Trends and Expectations`
- Window and canonical offsets: `W016`, `[126153, 126277)`
- Character count: `124`
- Canonical snippet: `If we do not take the mitigating actions we plan to take in 2026, the impact from tariffs could be around 20 percent higher.`

The sentence directly supplies the relative no-mitigation impact. The nearby `$2.6 billion` is the expected 2026 tariff impact under the company's stated plan, while `W017`'s `$800 million` is the expected first-quarter impact; neither is a second answer to the no-mitigation condition. The wording “how much could tariffs cost” can be read as asking for an absolute dollar amount, but the accepted evidence and filing express the no-mitigation delta as “around 20 percent higher.” This is a wording ambiguity to preserve for human comparison, not a span-bound violation or a reason to calculate an unstated dollar answer.

### `p42` — evidence is valid; selection value remains a human decision

- Round 1 decision: `o`
- Current question: `How frequently does Caterpillar's IT chief attend Audit Committee meetings?`
- Round 1 comment: `但是這個 query 是很罕見的問題，不會優先選這題，沒什麼評估意義`
- Recommended question change: none
- Acceptable occurrence count: `1`

Occurrence 1:

- Filing location: Item 1C, `Cybersecurity Governance`
- Window and canonical offsets: `W014`, `[105817, 105998)`
- Character count: `181`
- Canonical snippet: `The Company’s Chief Information Officer & Senior Vice President, Caterpillar IT (the “CIO”) attends all bimonthly AC meetings and provides cybersecurity updates to the AC and board.`

This is the sole occurrence that joins the CIO, attendance and meeting cadence. Other CIO references describe background or responsibility. Other Audit Committee cadence references concern accounting estimates or derivatives risk and are not acceptable alternatives. The Round 1 comment concerns usefulness/distribution, not evidence correctness; whether to remove it while filtering 51 candidates to 40 remains for human review.

### `a25` — revise the question; two acceptable occurrences

- Round 1 decision: `?`
- Current question: `RPMGlobal deal cost, completion schedule, and mining software capabilities`
- Round 1 comment: `題目應該簡化為 deal cost and completion schedule,  拿掉 mining software capabilities`
- Recommended revised question: `What were the expected purchase price and closing schedule for Caterpillar's RPMGlobal acquisition?`
- Recommended answer requirement: one span must state both the expected closing window and purchase price for the RPMGlobal acquisition
- Acceptable occurrence count after revision: `2`

Occurrence 1:

- Filing location: Item 7, `LIQUIDITY AND CAPITAL RESOURCES` → `Machinery, Power & Energy` → resource allocation discussion
- Window and canonical offsets: `W022`, `[171845, 171994)`
- Character count: `149`
- Canonical snippet: `The transaction is expected to close in the final two weeks of February with a purchase price of approximately $790 million, excluding cash acquired.`

Occurrence 2:

- Filing location: Item 8, Note 25, `Subsequent event`
- Window and canonical offsets: `W052`, `[409946, 410095)`
- Character count: `149`
- Canonical snippet: `The transaction is expected to close in the final two weeks of February with a purchase price of approximately $790 million, excluding cash acquired.`

The two normalized snippets are textually identical but come from distinct source locations, so both count as correct OR alternatives. Paired with the revised question, “the transaction” has an unambiguous referent and the single sentence supplies both required facts without surrounding text. Removing “mining software capabilities” makes each 149-character occurrence independently sufficient and avoids requiring a longer compound answer. The old pipeline label `Financial Products Segment` is not the filing location for the Item 7 occurrence and should not be carried into Round 2 provenance.

## Open human decisions and uncertainties

1. `p42` has a sound evidence contract but the Round 1 comment questions its eval value. Full traversal cannot resolve whether it deserves one of the final 40 slots.
2. `p25` is answerable as a relative increase. If the intended answer is instead an absolute unmitigated dollar cost, the question should be rewritten because the filing does not state that computed amount in a 50–200 character self-contained span; this task does not infer `$3.12 billion`.
3. `a25` should use both source occurrences even though their text is identical. Deduplicating on snippet text would incorrectly turn a valid retrieval at one filing location into a miss.
4. The filing says the RPMGlobal transaction was “expected” to close in the final two weeks of February. No external post-filing completion status was introduced; the dataset should preserve the accession-pinned statement.

No candidate has a confirmed 50–200 character span contract failure under the recommended handling above.
