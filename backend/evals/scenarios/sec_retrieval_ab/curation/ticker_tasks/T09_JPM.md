# T09 JPM — pipeline-independent filing traversal

## Scope and result

- Ticker / CIK: `JPM` / `0000019617`
- Fiscal year: `2025`
- Accession: `0001628280-26-008131`
- Active non-`multi_passage` candidate: `n10`
- Excluded `multi_passage` candidates: `a05`, `p05`
- Full traversal coverage: `100/100` fixed neutral windows; `1,199,025/1,199,025` canonical characters
- Acceptable source occurrences: `n10 = 1`; reachable filing-store locations after T3: `2`
- Human review fields changed: no
- Final Round 2 CSV/Markdown generated: no

The pipeline-independent traversal found one acceptable source-table occurrence. Round 3 T3 later
re-extracted it as a 151-character filing-store exact span and enumerated both reachable non-Item-8
store copies. The span keeps the `CIB trading VaR by risk type` heading and all four reported
categories in one contiguous interval.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/0001628280-26-008131-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/0001628280-26-008131.txt)
- [SEC primary 10-K](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm)
- Filing date: `2026-02-13`
- Period of report: `2025-12-31`
- Primary document: `jpm-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Complete-submission bytes / SHA-256: `64,896,112` / `e59055162f35a8ba24c2e8f1890a4eed7572db570116ba66d3a4ea184b650f95`
- Separately downloaded primary-document bytes / SHA-256: `12,927,325` / `4d9febdbc2038dcdca8726053286df4cbbfd48885051cbd781efcc3becb66a23`
- Extracted primary-document bytes / SHA-256: `12,927,324` / `5a9032f264f8c0b3473e75dc0c38ec1d725988ec1ca88ed62e9b7c05e3b7c978`
- Canonical visible-text bytes / chars / lines: `1,207,581` / `1,199,025` / `53,582`
- Canonical visible-text SHA-256: `4ecba188c3dfe4c89c1be21033ce3f017b6b68f9c950d3b56008717eb6902fd6`

The accession-pinned complete submission contains 269 `<DOCUMENT>` records and identifies
sequence 1 as the exact `TYPE=10-K` document. The submission wraps that document in one outer
`<XBRL>` element. After removing that wrapper, the extracted bytes match the separately
downloaded SEC primary document after removal of its single trailing newline.

Canonicalization parsed visible HTML in source order, removed non-visible transport content,
inserted separators at neutral HTML block boundaries, decoded entities, and normalized transport
whitespace. It did not construct or use Item, heading, block, sentence, candidate-evidence, or
repository-pipeline hierarchy. Offsets below are zero-based and end-exclusive in this canonical
text. Filing locations are descriptive provenance assigned after traversal.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 12,000-character slice except the final remainder.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W0001 | `[0, 12000)` | `42731e5c0871b5bcf4c84d63f8748927e44fa4185cf39d66886707cd09b6cd89` | inspected |
| W0002 | `[12000, 24000)` | `831b10dffbf263bd4d02d551af19ecf39294636e126d029c90d61c6b06a9234a` | inspected |
| W0003 | `[24000, 36000)` | `f253a69d96c60263cfe5ec765fb64df055189385908cffe85f78941204d51219` | inspected |
| W0004 | `[36000, 48000)` | `341d502daea862bfa609e3e302fac7fe7e9efd59ba72108f89ccf538f3278cb5` | inspected |
| W0005 | `[48000, 60000)` | `6caf44ecb0df8e0afec0b35e3cb7ee6266770cea90adeecb2febd98099d32d8a` | inspected |
| W0006 | `[60000, 72000)` | `ce192a9c3e7fadc8ff950b00081ddccfc452ce5ae59d4f77edccd3828e7d1573` | inspected |
| W0007 | `[72000, 84000)` | `3687918bc6fb82d7e9702d63f923bea81e58a390b7aeb97e709ff61407a1f78f` | inspected |
| W0008 | `[84000, 96000)` | `b2a8604ebdb25053b4019fa42b9d879ed1d3b369cc8e4a747490d7ed0d811d81` | inspected |
| W0009 | `[96000, 108000)` | `f082fe5cef995424f5f090f6720d742a36f1f433348e670edd92014e6e51dace` | inspected |
| W0010 | `[108000, 120000)` | `039eb523d28007a8dfac3a9c504f3003afec0eda9ebf77bdfe820c06d7c32df1` | inspected |
| W0011 | `[120000, 132000)` | `57467a52d695680d659e228c1be752c0d741e8686bde847a68b79a3c544c3584` | inspected |
| W0012 | `[132000, 144000)` | `a8e85a5f9adf07ffb55e773a9bfbb705607b6a119737bb979f6cbb7a36f02b90` | inspected |
| W0013 | `[144000, 156000)` | `96395db0972a5f8cde6d069c46fc22a9b155c3ab361ea75b5e7b17ecfb67ae0a` | inspected |
| W0014 | `[156000, 168000)` | `1685aa81fabad96a02565093fec9f2e3b7bfc782b0674fdabcc23b4a3ae58e1a` | inspected |
| W0015 | `[168000, 180000)` | `a7d98b0780ebedbd99ce2f84a0f025e4107bcea066ba138bf753fd4b39dec398` | inspected |
| W0016 | `[180000, 192000)` | `15b4fd3e7696ce338c40bcdceb43d72fd3bdf6dbfd8554c0e32dd55e0c8001d6` | inspected |
| W0017 | `[192000, 204000)` | `26971065acb657cec26cec4c675efdb24996ef273b47218084fbc7eebb9f3003` | inspected |
| W0018 | `[204000, 216000)` | `b4b28248d596f8b4a664c8b35a0581d45de57be55dbe96c5ee0dd72b9a39c30e` | inspected |
| W0019 | `[216000, 228000)` | `a0041f27fcff086df3932d28fa9492bc386918c0667b67c5b36b9251cbfaa446` | inspected |
| W0020 | `[228000, 240000)` | `6fdb1d25d717ae7a15114508b27c2a9fba9e9c796826130e8f8ffc411fbeee25` | inspected |
| W0021 | `[240000, 252000)` | `b1553b94b4ee9308747323513cc460a0d3118f62bfe2b763ad6aa6cd2505711b` | inspected |
| W0022 | `[252000, 264000)` | `9d92bece4b75b77d02e454bcb7dda36123e695f62862600153c179ec0376f9a7` | inspected |
| W0023 | `[264000, 276000)` | `255c99e92888694467fd85abffbadfebcf93de58965e58daeb4592fb18b7dc13` | inspected |
| W0024 | `[276000, 288000)` | `68297088030a4e7f3326e2713e2c7c91e9544950fe72a9dd55658431fb4b1758` | inspected |
| W0025 | `[288000, 300000)` | `3df7b6eb0297b959b14f7f1475e02eda6ec5f04bf7a6a5c299362f4acbfbec82` | inspected |
| W0026 | `[300000, 312000)` | `28aa9819febdea94a8c17b3b990107fba1a34c278486487b476a253710f48fd7` | inspected |
| W0027 | `[312000, 324000)` | `a74fb6d0c9b2450d81417b1dd7e25dc5bf7262827f8bbbc9513f4cd8229f2eae` | inspected |
| W0028 | `[324000, 336000)` | `4adfe4dd841d8e0bdd913d638f36b30daf29c4ff373eaeb5107f594aa3cbc18b` | inspected |
| W0029 | `[336000, 348000)` | `70d88c3b23a90fb12f043e69b72d516e0ab69c7f2d4674124d08fff89758a696` | inspected |
| W0030 | `[348000, 360000)` | `ab38f73fac5de4969d1a3055231162b15116a23ce55315e9e65301b2c01eb346` | inspected |
| W0031 | `[360000, 372000)` | `03ec87bb5d4745d55417b7ff3450f1910e4a6880af39b64620246157cec25e91` | inspected |
| W0032 | `[372000, 384000)` | `a9ffbafb74573e77442af51c2553a73b32dbacc01193668105ff55325ee9be8b` | inspected |
| W0033 | `[384000, 396000)` | `0c61837f0d68442e948aa387d0e1e604e9b4f3936407766e0647ecb148a9e65b` | inspected |
| W0034 | `[396000, 408000)` | `4528598f623ead75044a745b66da62dcb56a017a86a1abb12a2d659d0254c9a4` | inspected |
| W0035 | `[408000, 420000)` | `7ad8382bf1245e96a30cf06bc7ebb562cf74942da6e8021bc8240cfc50a0c5c0` | inspected |
| W0036 | `[420000, 432000)` | `16b74f78ca600c926caa7adec950d47bc374b1d292cf1702dc099cb6670af877` | inspected |
| W0037 | `[432000, 444000)` | `4d82423fb2aeaaaadf305168da7b17de542db873b1c824b89bfab94f3ce7a4d4` | inspected |
| W0038 | `[444000, 456000)` | `d1ed4dab2ae0c53ba49fc82401b09a9cc6ec27dc8b38bb0fd74743252819d459` | inspected |
| W0039 | `[456000, 468000)` | `37196de046820a9092ca1a49c2684f44cb6640b660e74425f7954d3866e79566` | inspected |
| W0040 | `[468000, 480000)` | `e3e0777a0925d9342ffbc26cbf6bf94f39e662f0e256112f8fee65ae88f64831` | inspected |
| W0041 | `[480000, 492000)` | `31417171f1da41d57e0bf65d0ece4d9bb88ae998a9dafe37eb9444c601140661` | inspected |
| W0042 | `[492000, 504000)` | `8a689b22aa56930b0edf5166da4946d1628469c8b49c6252cfaa0b5b69ea6e59` | inspected |
| W0043 | `[504000, 516000)` | `57cc4bda12fff8d75e9caca33a3bb9fe91698994b737abdb95faeaee643ba248` | inspected |
| W0044 | `[516000, 528000)` | `d226d7f51b75c02a8d79d098509425f06dea4a8fbf5910aa4b8697d922df82fb` | inspected |
| W0045 | `[528000, 540000)` | `1896b2c36a2ade9c9b223df0013dab1f87cc612bf513addbb22f3cb90f1c252b` | inspected |
| W0046 | `[540000, 552000)` | `d7b76d19cf0ccc771f15fd5bbe43b32e45b47f0c5e5a6530a0b26c2be9d79062` | inspected |
| W0047 | `[552000, 564000)` | `7bafe573088125398a6ef23c16b98651c4d44fe9a22969279064c7f526c59ddf` | inspected |
| W0048 | `[564000, 576000)` | `207a305b316f3ed8e82f256e907ddce705b9922496876fada9646ba5c48b3293` | inspected |
| W0049 | `[576000, 588000)` | `855978ea47cc1a2eede7e5d8f4d4700c40f5fa0230d511505c599480052fec03` | inspected |
| W0050 | `[588000, 600000)` | `c103be47b00a76053834bdfc975cf58adbb453cea2da41d78930edad60b5e2e6` | inspected |
| W0051 | `[600000, 612000)` | `2aa1b70de572ac7ae8ff592ef576b7b5f4fb4e2b81f62378a6e5a6bcb91efc92` | inspected |
| W0052 | `[612000, 624000)` | `b8147afd944212ad0bd05cbe4ed27c9953d0f84884610698a6ae13d124c9b621` | inspected |
| W0053 | `[624000, 636000)` | `674ca06b44ccff894c1cc174026100d8c2ba62d450c3bda08d9a89a16ea22b17` | inspected |
| W0054 | `[636000, 648000)` | `e321ba6a3fa12046a470a2acd41fb891b923df07bd45c97f7df1a46626327843` | inspected |
| W0055 | `[648000, 660000)` | `21a821c7d7f8f184cbbb75696fc3fcae1e22427032f39b85ecc84ea64b09e420` | inspected |
| W0056 | `[660000, 672000)` | `2b36f37fd5829248fbd6a41fe9228aecd4610aa1716ba708f449e2ca14d7ca15` | inspected |
| W0057 | `[672000, 684000)` | `bab2192432131f9ba6a1c5f493c0a43edd80f6c73477bed2295234d24366ae5f` | inspected |
| W0058 | `[684000, 696000)` | `c6b0f865a4c00530300d2f8c4f2eafbe985a431a062f105c17ac7bead1cca3b6` | inspected |
| W0059 | `[696000, 708000)` | `bebf9ed14eff241bc4e4e16ef4c5b8b4a7ab1bb1855f37c1745c80c7428da3d6` | inspected |
| W0060 | `[708000, 720000)` | `59647d2978244de3ee367be5078e63d47a6d4a41a4111b0d776af04e30fc82d9` | inspected |
| W0061 | `[720000, 732000)` | `4b180e83e18a1b0d198d0ee4ef0fb77ed7adc1b0300b136e49c0bab64bc19fc8` | inspected |
| W0062 | `[732000, 744000)` | `6d5b0d995e8b2494663769e1864277c5343be2ac30dc4b9058920fbfb80533b0` | inspected |
| W0063 | `[744000, 756000)` | `b62b782eebb40d5b2ee90a4d3e9efd50d4939ef2aadb93354bca4f711781606b` | inspected |
| W0064 | `[756000, 768000)` | `f1dc039fa1a6af9d1ceb54ac46133e06463fab984c4d5f0b0d0742af98cdd70e` | inspected |
| W0065 | `[768000, 780000)` | `765f28d78dcf726e768561c22ca24f9bf908fd3b3b45bbd2fe6a0c55b4c7382b` | inspected |
| W0066 | `[780000, 792000)` | `70c4add0810f3ac2f71322aa8efcf0b0161f8d74eb0436344d58d454cf3257f5` | inspected |
| W0067 | `[792000, 804000)` | `f97c3abeb933eaccc008ca30c1d1177df6eb872edefa380df29239423ea80d24` | inspected |
| W0068 | `[804000, 816000)` | `40f7825dd761c01aca41a696e2d81573ad6a5a335c2f38ec028c050bcf6f6d5d` | inspected |
| W0069 | `[816000, 828000)` | `2cff2fe1ee6e6b8f6e2e568bd8b95aedb67cb153fa052cd6a846936e9c3072b3` | inspected |
| W0070 | `[828000, 840000)` | `ee6e8264cba37db5631e383fcfabed4afd6786345856edf4aa3151b9b0b32ead` | inspected |
| W0071 | `[840000, 852000)` | `eaeeabd72812adeb5823e441adfb8313019a9c717703f602349df70e7036a6b9` | inspected |
| W0072 | `[852000, 864000)` | `edac822e794838f8ddd8d487c916439695fa40dbb573a7e7e1b8d3eb24dc5263` | inspected |
| W0073 | `[864000, 876000)` | `7667cf704077cf1500701850c5c2e062cea8570785d3ede76a79ed4532de363f` | inspected |
| W0074 | `[876000, 888000)` | `7347636eb752a375b427f1f15c6ce53dd5066548f2cff3df2f23b15e2bc91e3d` | inspected |
| W0075 | `[888000, 900000)` | `01c656a9a5e6e2634b3de33ad85c780546a143e246e4fb2a4ac18076ad75bef3` | inspected |
| W0076 | `[900000, 912000)` | `dcd07a0a79c49c97b892473aec72a7fbcdcdb16cd0999dea512e1e4cd5dc47cb` | inspected |
| W0077 | `[912000, 924000)` | `0b238fdb23f00ee4d061000dddce4d9697cda749d037bcf540aabfc4a4b0c3e0` | inspected |
| W0078 | `[924000, 936000)` | `fbb05535945d2874f43eb45d0ff5110a1c266cf592def83de602d5d15b4895db` | inspected |
| W0079 | `[936000, 948000)` | `5a379cbb70c8a0407630511f33a4dec89dd7b568f7c357767017ec7aa7055ddc` | inspected |
| W0080 | `[948000, 960000)` | `20571ba55cd2bba4f3201aaa5aeff645b83bc96c22ca3a18c854aac6f7519668` | inspected |
| W0081 | `[960000, 972000)` | `cf692f234e0d980dc0686fb6b16bb5551157e2747d0e8805715c945a2c54a9a3` | inspected |
| W0082 | `[972000, 984000)` | `cde9f95bcfe3b4937f2a74b70d6a3c4d1e4a1493916e37cfb432ae49e616e570` | inspected |
| W0083 | `[984000, 996000)` | `3a981b7a3b09fc72d2b6e15a8c747637ad74b8c04a3c4b1b80cce6c2ddac7c21` | inspected |
| W0084 | `[996000, 1008000)` | `c7410379780be40ddacebcc49a3e323c2c49b53c7fc62aea6074c772eb57da88` | inspected |
| W0085 | `[1008000, 1020000)` | `7ac94f546b33dab5d3f55aeda9af2c56ac71b45a38a951f650fcf00434443add` | inspected |
| W0086 | `[1020000, 1032000)` | `c0c81ea73a95d041406cb8e4b80d6201bb62b3ed122e386fa52591172938517b` | inspected |
| W0087 | `[1032000, 1044000)` | `503078b51d47c8fc8a81d5ce295a183a05fc1c25d8eaac7e61db399aed1141da` | inspected |
| W0088 | `[1044000, 1056000)` | `a6a7727a79e6bdeee69f10e83c1bb416b5891a92f2f07483c66303daacbc7cd4` | inspected |
| W0089 | `[1056000, 1068000)` | `5bf5a67077dde3ed36a96effcbb74dae9c92a0d7bfbd1456d00c2f42f4b6bb37` | inspected |
| W0090 | `[1068000, 1080000)` | `43cd7a471f87e51f7c11acf09cbaff100ca8d3e33d407b82c488877e02fcdc14` | inspected |
| W0091 | `[1080000, 1092000)` | `2876e3f44c59e6a1e8d2c606a87054bce7b8b5fb633dc391682e30a808b0d6d3` | inspected |
| W0092 | `[1092000, 1104000)` | `ea8d621b596a455f0a167ec5fda2262591503a6c7da9cfa6bd47c9ea447ea5cf` | inspected |
| W0093 | `[1104000, 1116000)` | `d13318e147cd5fae445afe152cb0e6adbc11602af0eb9ef818a831a645c67d00` | inspected |
| W0094 | `[1116000, 1128000)` | `bf26967b865ede312ead453465473d57890457a59b284afbf266be54de1eedff` | inspected |
| W0095 | `[1128000, 1140000)` | `97672d4fbd84b806c7fdfa2ae4b418b6c857766f573914283c11306352783eda` | inspected |
| W0096 | `[1140000, 1152000)` | `079e7433ae25e7ed4d7400e24f31d89068b5026182734ee4065be6f2b8dbe771` | inspected |
| W0097 | `[1152000, 1164000)` | `5d770551b316bb2356ea64a3a20b691d0bc30afb42d2a9bb592011c382c22dba` | inspected |
| W0098 | `[1164000, 1176000)` | `89fdf4fe6431b1d16cdc9da49073e5b379ba1da599be8e9daf6bb7315dcc9a66` | inspected |
| W0099 | `[1176000, 1188000)` | `f857a624cab5b60aaf75599080bfcf8473f4e5f63eb31e4ea6a97988f2ba07a9` | inspected |
| W0100 | `[1188000, 1199025)` | `a965c12fa9a7733019bb1093f6060388185a6a38985fa6cdb5fae52889fccdf1` | inspected |

The intervals are contiguous from `0` through `1,199,025`, with zero gaps and zero overlaps.

Traversal checkpoints:

- `W0001–W0016`: regulatory overview, risk factors, cybersecurity, properties, trading arrangements,
  exhibits and signatures. These windows contain market-risk language but no occurrence that
  identifies the requested VaR risk-type set.
- `W0017–W0031`: business and financial overview, segment results, capital planning and capital
  risk. `W0025` references positions in Risk Management VaR only to explain backtesting gains and
  losses; it does not identify the risk types.
- `W0032–W0041`: liquidity, funding, credit and counterparty risk, followed by the lead-in to
  Market Risk Management. No complete answer occurs in these windows.
- `W0042–W0044`: Market Risk Management, VaR, stress testing, interest-rate risk and other
  sensitivity measures. `W0043` contains the sole acceptable occurrence. A `W0042` business-
  activity list names the same four broad markets without establishing that they are VaR risk
  types. A later `W0043` narrative mentions all four types, but its shortest span that also retains
  the VaR relationship is 244 characters.
- `W0045–W0048`: country, model, operational, insurance, cybersecurity, compliance and conduct
  risk. No acceptable occurrence.
- `W0049–W0100`: critical accounting estimates, financial statements, Notes 1–32, legal matters,
  supplemental schedules and glossary. The glossary defines VaR but does not list its risk types;
  no second independently sufficient occurrence appears in this range.

After the sequential traversal, the full-text audit covered `VaR`, `value-at-risk`, `risk type`,
`market risk`, fixed income and interest-rate variants, foreign exchange, equity/equities,
commodity/commodities, credit, portfolio components, methodology, backtesting and glossary
definitions. It found no second 50–200 character occurrence satisfying the complete relation.

## Round 3 T3 filing-store correction

The canonical HTML table linearization below is historical traversal provenance only. It does not
exact-match the filing store because the store keeps each row's values on the same line. The exact
filing-store span/snippet is:

> CIB trading VaR by risk type
>
> Fixed income$35 $27 $51 $34 $26 $53 
>
> Foreign exchange9 6 15 15 7 23 
>
> Equities17 7 138 (e)8 4 15 
>
> Commodities and other

- Character count: `151`
- SHA-256: `6105d50fdeff67de89dd5a511baa42a28fcb253b6ee043225c47990d50a5e4cd`
- Answer span and answer snippet: identical
- Answer coverage: fixed income, foreign exchange, equities, and commodities and other
- Filing-store exact occurrences outside Item 8: `2`

The filing store exposes the same source table in two structured blocks, so both are retained as
OR alternatives:

1. Item 1 / block 1 / `Segment & Corporate Results – Managed Basis` / `[239167, 239318)`
2. Item 15 / block 2 / `Segment & Corporate Results – Managed Basis` / `[239167, 239318)`

The official filing context identifies the source as Item 7A. The mismatched store labels are
recorded rather than silently rewritten; cross-arm header-path reconciliation belongs to its
separate issue. Both new human-review fields remain blank.

## Round 2 canonical candidate finding (historical provenance)

### `n10` — keep question; one acceptable occurrence

- Candidate ID: `n10`
- Round 2 decision:
- Round 2 reviewer comment:
- Candidate type: new intent-first question
- Question: `Which types of market risk does JPMorganChase include in its Value-at-Risk measure?`
- Proposed question change: none
- Proposed query type: `factoid`

Occurrence 1:

- Filing location: Item 7A, Market Risk Management, Value-at-risk, Total VaR table
- Window and canonical offsets: `W0043`, `[504303, 504486)`
- Canonical line: `19017`
- Character count: `183`
- Snippet SHA-256: `1e3055b861ce78fc1e608e3a3d8ae10974287c568474ff99cf53c10d51fba828`
- Exact occurrences in canonical text: `1`

> CIB trading VaR by risk type
>
> Fixed income
>
> $
>
> 35
>
> $
>
> 27
>
> $
>
> 51
>
> $
>
> 34
>
> $
>
> 26
>
> $
>
> 53
>
> Foreign exchange
>
> 9
>
> 6
>
> 15
>
> 15
>
> 7
>
> 23
>
> Equities
>
> 17
>
> 7
>
> 138
>
> (e)
>
> 8
>
> 4
>
> 15
>
> Commodities and other

The table heading supplies the VaR relationship, while the four row labels supply the complete
answer: fixed income, foreign exchange, equities, and commodities and other. The numeric cells are
unnecessary to the semantic answer but cannot be removed from a contiguous exact source span.
They are filing content, not a `sec_text_pipeline` or `sec_filing_pipeline_html` artifact.

## Rejected near-matches and open human decision

1. The 98-character sentence `Makes markets and services clients across fixed income, foreign
   exchange, equities and commodities` names four markets but does not say they are VaR risk
   types, so it is not independently sufficient.
2. The 2025-versus-2024 Total VaR discussion also mentions all four types. Its shortest four-type
   fragment is 155 characters but omits any VaR relation; the shortest contiguous fragment that
   retains both VaR and all four types is 244 characters. It is therefore excluded without
   relaxing the global limit.
3. Credit Portfolio VaR, CCB VaR, AWM VaR and Corporate VaR are portfolio or organizational
   components in the Total VaR table, not additional entries under `CIB trading VaR by risk type`.
4. The current question is usable, but the evidence is specifically the CIB trading VaR risk-type
   table. If the reviewer interprets the wording as asking for every Firmwide VaR portfolio
   component, the precise rewrite would be `Which risk types does JPMorganChase report for CIB
   trading VaR?`; this task does not make that human decision.

No proposed occurrence violates the 50–200 character contract. Both Round 2 review fields remain
intentionally blank.
