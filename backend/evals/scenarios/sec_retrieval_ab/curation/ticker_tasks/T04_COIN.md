# T04 COIN — pipeline-independent filing traversal

## Scope and result

- Ticker: `COIN`
- Fiscal year: `2025`
- Accession: `0001679788-26-000015`
- Active non-`multi_passage` candidates: `p38`, `p21`, `a21`, `n06`
- Full traversal coverage: `109/109` fixed neutral windows; `649,618/649,618` canonical characters
- Acceptable distinct occurrences: `p38 = 1`, `p21 = 1`, `a21 = 3`, `n06 = 3`
- Human review fields changed: no
- Final Round 2 CSV/Markdown assembled: no

The three `a21` occurrences are distinct OR-hit alternatives even though they express the same policy. The three `n06` occurrences express different disclosed drivers; a retrieval hit on any one is relevant to the broad driver question and therefore counts under the unchanged metric.

## Official source and canonical text

- [SEC filing index](https://www.sec.gov/Archives/edgar/data/1679788/000167978826000015/0001679788-26-000015-index.html)
- [SEC complete submission](https://www.sec.gov/Archives/edgar/data/1679788/000167978826000015/0001679788-26-000015.txt)
- [Primary 10-K document](https://www.sec.gov/Archives/edgar/data/1679788/000167978826000015/coin-20251231.htm)
- Filing date: `2026-02-12`
- Period of report: `2025-12-31`
- Complete-submission SHA-256: `78459147056fb4343806105a8a20de62c7c6aaa16f1968563d877854be4537cd`
- Primary document: `coin-20251231.htm` (`TYPE=10-K`, `SEQUENCE=1`)
- Primary-HTML SHA-256: `cbe1e2c73bf6e9609afded3e95c338bcb1b92d0ea055fe3da5906e0c4c3805c9`
- Canonical visible-text SHA-256: `f6e46e1eed1c1176bbb11eb6e72f383b8ddcd594175c483a4b8d78e580c44519`
- Canonical character count: `649,618`

The complete submission's first document is `TYPE=10-K`, `SEQUENCE=1`, `FILENAME=coin-20251231.htm`. Removing the SGML `<TEXT>/<XBRL>` wrapper and outer whitespace produces the separately downloaded primary document byte-for-byte.

Canonicalization uses Python's standard `HTMLParser` and is independent of the repository SEC pipelines. It removes `script`, `style`, `noscript`, `ix:header`, `ix:hidden`, elements hidden by attributes, and elements whose inline style contains `display:none` or `visibility:hidden`. It adds separators at generic block tags, decodes entities, replaces NBSP, collapses horizontal whitespace, drops blank lines, and preserves source order. It does not construct or use Item, heading, block, sentence, or repository-pipeline hierarchy.

Offsets below are zero-based and end-exclusive against exactly that canonical text.

## Sequential coverage ledger

Every window is a fixed, non-overlapping 6,000-character slice except the final remainder. Every row was inspected in sequence before the full-text keyword audit.

| Window | Canonical range | SHA-256 | Status |
|---|---:|---|---|
| W001 | [0, 6000) | `4ac2b1a3182e5a65aac4bcec1337a6e98ce5bcb4bf5593303dfc56e1ab7e6d36` | inspected |
| W002 | [6000, 12000) | `f61cb8b11eb44d37e46a4b3b089637ac26d3dfd86301ab969176be9846a24ad7` | inspected |
| W003 | [12000, 18000) | `42062eb67217d04fa9fe17d5d084d618aaa7636832a869cec3a8a7a81d020e95` | inspected |
| W004 | [18000, 24000) | `33e31f55912fc5d42e8e2e1c2f9f2c3f688729e19942cbf870e334055aaab340` | inspected |
| W005 | [24000, 30000) | `3efa857f00b6fa8c2aeca720902fcc65853476c24d050eed8bc019fd28416027` | inspected |
| W006 | [30000, 36000) | `c6104a192e5fae1253c56b2aa0c26c71d150f8a9a0d0fda2311039e7635ce445` | inspected |
| W007 | [36000, 42000) | `1f9fd558c661ec89a79b0e20d2902067f050ab5d57703f64590da4bded1fc61b` | inspected (`p38`) |
| W008 | [42000, 48000) | `9f7536855d7fa23462c30b4225ce2c57e46b029eab8522153748cb63663b6fcb` | inspected |
| W009 | [48000, 54000) | `b132a2eb36667f5b0e4e871981ef08c56802052fda50d2fd43953748a49de03a` | inspected |
| W010 | [54000, 60000) | `9ac9c3805cec3802c8a0f0398db01a3b08afe1c245eb85eff18e7859ee70e12e` | inspected |
| W011 | [60000, 66000) | `a5f90f1d26db6b74318c4fa65910bd0e3d2a2b1dff71bb7996a823d9f82ea435` | inspected |
| W012 | [66000, 72000) | `477475726eb6ece37510322939a21c0ea0d34613ec75d6812f6e1a1671b76ade` | inspected |
| W013 | [72000, 78000) | `02d03af6ee2998a8bbff4e00deb6c9188478105080bb3ecbb5d6f9cddef11171` | inspected |
| W014 | [78000, 84000) | `4c3170cd5edcba205fe91dea6e128414f071d45b8dc207a7d9f7a124aa7d67aa` | inspected |
| W015 | [84000, 90000) | `3e32eed8f64aca5ea11aa4c8f146a106caf259ca6a9c11c82f77de5c79958aec` | inspected |
| W016 | [90000, 96000) | `531997aa9b2d1b386aa62a79fadfe1a7adf48fc5a9fbd8eb025b3e4a109f030b` | inspected |
| W017 | [96000, 102000) | `03ef024df7bce30617eab9f787d33238951ddc194df5e24602fc9385d8b14c18` | inspected |
| W018 | [102000, 108000) | `f84a502b403a75a0c3c756516e30044b3717b2dd22f813b3b3c55da4fedce3af` | inspected |
| W019 | [108000, 114000) | `a3f63fd7c12e34485e9d54e5122d0061e322c12c213db416c36bc92b90344d19` | inspected |
| W020 | [114000, 120000) | `d6a0a6d4caaa48d621c786ccab9c18e52dceee0aea7c871896c779f94de0c70b` | inspected |
| W021 | [120000, 126000) | `93625d090cf379c7ac9294b1b990dd0d24d77e1511fe060f10bcc4fe98c519e8` | inspected |
| W022 | [126000, 132000) | `6fe19ec3dac7a39119cdedd43ce4f2399db8fc3da4f172535c1b48529831becf` | inspected |
| W023 | [132000, 138000) | `1f8aa0aa50a216226b2e8dc2ec0f43a4fb495218066e584cb697ff39a170e110` | inspected |
| W024 | [138000, 144000) | `1f78dd73fd3a218032923e8fe20631fbd364c10d39ba9bc75d9dc241ebbe8ad3` | inspected |
| W025 | [144000, 150000) | `acde0c45eeccd445dca6ac51d37b75f515c1c5040a5675b6610edae099b9284b` | inspected |
| W026 | [150000, 156000) | `ed0e96506e1de088b5570ccc398f0eff6f67fa8e1cb610e0ac89070f6f44859f` | inspected |
| W027 | [156000, 162000) | `002a2f1ce75d5a31f30af3ec5793a7a77da8bd5a1571297ba541d78664524503` | inspected |
| W028 | [162000, 168000) | `84137209160296dc56f36f10affe9542c6a5ff7999056a434de8ac5f515deff5` | inspected |
| W029 | [168000, 174000) | `ec63f55bf4635e6681199f2568e108aedc7021350dc821d18458eda3094d77f6` | inspected |
| W030 | [174000, 180000) | `b40c4e817418238e794ab24292ff2ded9055a40d06a5986a28b46da784681627` | inspected |
| W031 | [180000, 186000) | `04c6ead95eb7e2f48c5847fd104f15c0a61c5bfdf861fc21991891894d6a5bee` | inspected |
| W032 | [186000, 192000) | `586bb6c800f39cf793a3d90416fc66db2693ea7b7e1bca7c8f990eacc2679502` | inspected |
| W033 | [192000, 198000) | `1741a464c75133aea150b34a83c7bb30f2d042ae8b15225fcc65bd1c0168a464` | inspected |
| W034 | [198000, 204000) | `6498851a4335db61c9d493326614f3733bd2eec169afc819d45985168cb76b78` | inspected |
| W035 | [204000, 210000) | `26ef580315348e0ce7cd48bd8ead385e79883d317c7f5ee53d75b088eb0eb99a` | inspected |
| W036 | [210000, 216000) | `cc01e91e96c6729244a37a9bc1a4b0b495f608e8efc0125f178e369714d991b2` | inspected |
| W037 | [216000, 222000) | `373be97b500f882161df4f2a4805925575f476f794b2ca0c045a9b1e6bb6ceda` | inspected |
| W038 | [222000, 228000) | `a236a47c9af03092c5f3a3d97b117d41bcd6b39e16ac382b57d5b7a9a7addf98` | inspected |
| W039 | [228000, 234000) | `5874392948050abb093f6b283f7e364ade27287be2ffa99e737771aafb7b43de` | inspected |
| W040 | [234000, 240000) | `032eca9eea13d52680e2b1cdb9fa4ee28da94d527a6a3952dc9b83f1facb6576` | inspected |
| W041 | [240000, 246000) | `35b1f91bd5a769a69a3f7d7325d7a5bae573e63ea6fc75b6cc9655f986da5d13` | inspected |
| W042 | [246000, 252000) | `83fd2b10958aa682e316efabed070e856e13b7c7dcee5ce55228f0312126ed45` | inspected |
| W043 | [252000, 258000) | `6d39353ec53e17b002e19e00d23086327d732b1f4fc013440d302f183ea3cc3e` | inspected |
| W044 | [258000, 264000) | `74e50b0d22c1070012c69d84338378cfcb15bd6300f84ad56cf7851e973f253d` | inspected |
| W045 | [264000, 270000) | `ab74397e6c5cc681041f96e7a22de753087ebe3b29369a3f30ea07cf2f3fdcb4` | inspected |
| W046 | [270000, 276000) | `4d02587a846861760b76f20951d121b519bf52eec99f6b46d212a7284a68afdc` | inspected |
| W047 | [276000, 282000) | `76704d5aa5b4709992c7e89ff405149e7ab40c7a139b6546be0fafabfeb613d1` | inspected |
| W048 | [282000, 288000) | `7e41a005726dc747c03c236735a169796c16841400ed9249b39e752d2ef48e2b` | inspected |
| W049 | [288000, 294000) | `fd802783e5ac14d521cdc4835e6edb266d0b43c83509a28c14da4d335d30d804` | inspected |
| W050 | [294000, 300000) | `11f4864bfaf6e5efa8e170c54c42d856abc78d35262bd7d04267d7844827359f` | inspected |
| W051 | [300000, 306000) | `c53bbb503f8c2a909694500c07ec984ec660cb10ec123629049d4a61d8d64bd8` | inspected |
| W052 | [306000, 312000) | `af0f83f5f7e709f20d8ca1da06d4e81a6af0db7bfac3ed719df5859a90d4b9d0` | inspected |
| W053 | [312000, 318000) | `69f7490ded6d14af7e9436b5e2c4a354e744ce91700e574111451c6df4167333` | inspected |
| W054 | [318000, 324000) | `c01f10f433db5c1e6c5d5810f95ff4603ca2a645079dc5cb74efd3a666660223` | inspected |
| W055 | [324000, 330000) | `86d72b265845c309b6f0c8e5c82fd6508eb9d2baf84eda11ff6a51f54bc3504e` | inspected |
| W056 | [330000, 336000) | `3246e98149ec914d7e03dc6700e917b57c85c0cfc0015905dcd8c6d59996c71a` | inspected |
| W057 | [336000, 342000) | `14bdda4db5dc4484eca83785426c3839be71e3de16640e8137ac21028a298ca2` | inspected |
| W058 | [342000, 348000) | `82eb5857d272461cf7020c526bc5840156cb287dd1d340f1e3cf7ec70d9d7803` | inspected |
| W059 | [348000, 354000) | `1e5f4642d87bb2c82834ebd831950faaa8cdf590a3be91e9e68a3e6634f90870` | inspected |
| W060 | [354000, 360000) | `f6ccfb912916263f430ed137fcb9c1aae25ca24c08364f6d39f9b34e89a98dcc` | inspected |
| W061 | [360000, 366000) | `b77f8071e9a7503edb8ab6837c3316be1ef103f823f14c1344c26fb9b8407234` | inspected |
| W062 | [366000, 372000) | `b343eb86e5a981b88f9da676ba8b24b850dd73f596fc01cdbc0033375dc385c8` | inspected |
| W063 | [372000, 378000) | `89b210a77e347724cd353a46d547089e1833c5180f0fc9b8c30b528d42b5d5e0` | inspected |
| W064 | [378000, 384000) | `b64f8c6ed2617ee62a4a87038917864466caaafebaee5714856246ef500d2b66` | inspected |
| W065 | [384000, 390000) | `155035c8e4a0b04e34a5fd65b8a4bc7d5a2d6bb0e2cb009a6c924a5deafac6a4` | inspected |
| W066 | [390000, 396000) | `f98b10efc0bf51365e9aab6a4dcd2d810fbee879953ec3981cab4c47d2b51894` | inspected |
| W067 | [396000, 402000) | `4a53bee51dc77e7dab320ee8bdc7fddbf178266cc80d4294196be44096605367` | inspected (`p21`, `n06`) |
| W068 | [402000, 408000) | `5b507bb1d1808a47ca48ff3a2445a861ebf5d33422a3460dcfe4347fe5084a51` | inspected |
| W069 | [408000, 414000) | `97e9e046fdb480121e0b9b0bd8c9b7600caf2d30a5fe968617e093bda39da5d1` | inspected (`a21`) |
| W070 | [414000, 420000) | `19e1923e12f15aab3a6b863e0175e6db2741f7901f0b01baac26ea3efbffa0de` | inspected (`a21`) |
| W071 | [420000, 426000) | `a98af0537025e04a0534c181731a6f2c5b6c500f18255dae18553e0f4a5b3eb2` | inspected |
| W072 | [426000, 432000) | `fbd678f35ef3ec4ff1f825a359c9468f068c931f9e52365177a7335d09594123` | inspected |
| W073 | [432000, 438000) | `7b08c3a23bcb84540d804f2c17563d2bb1d63c34d13e364ad47a1b7919b20fd8` | inspected |
| W074 | [438000, 444000) | `27b0cc3f4b76f6a7376b11a523a489540d8ab8980b2cf85dc12b75f684d21937` | inspected |
| W075 | [444000, 450000) | `357012051924cd3718a3fec6c22d630aadf1151d7f59121915ed75042d458601` | inspected |
| W076 | [450000, 456000) | `5e0fe26e99cb65074e77613aaccc111b88270fda2f894f0bdd078c7beb086fe3` | inspected |
| W077 | [456000, 462000) | `7a65d0f68357d5fa20f694e64e0eaaf84a1c5f7ebbaa469a3092b096903d7db8` | inspected |
| W078 | [462000, 468000) | `07238f3115aa86fb06732468176ff0864a2882a1f667796aa70a87d950368283` | inspected |
| W079 | [468000, 474000) | `5b5fc194873881886d1a2125d958345edf04415359404ba4b3f2007f5a5a28d6` | inspected |
| W080 | [474000, 480000) | `15ca437d9d09c4e25f515e8d15383f56bb377e40127415085aff718b5a0f746e` | inspected |
| W081 | [480000, 486000) | `ec77ec0966a78f4144f4864d2c9898b5e33e5e5231b0f38bcc1835f906b3f9ae` | inspected |
| W082 | [486000, 492000) | `c53d5f6e0ca3d698873fe8ac35852363cddcb45143f1a3e8af45d59a496d7f99` | inspected |
| W083 | [492000, 498000) | `c06cb6f8191207fcfdf54c5b9fe33ea9fe411fd9ea9a02d1f2724bbc76813006` | inspected |
| W084 | [498000, 504000) | `4ef9a8bf5a6528e34424fd6260766b248b0636689a7d3c0ff6ec16b01ed09bc5` | inspected |
| W085 | [504000, 510000) | `f9eb4bc4bd11fd42c27c92b01ca10615ad0694e6158b2f0e3b226b32cb0e5ea7` | inspected |
| W086 | [510000, 516000) | `0543a7d6b6a8048d35e092bb4ffbd4ac6a7f1e8f20890397b7d3f2a151c06c89` | inspected (`a21`) |
| W087 | [516000, 522000) | `38d3456f444ddd3bbafeb15e37303a4ac43b22c8449399a42e5f9f6afc1d2a52` | inspected |
| W088 | [522000, 528000) | `2c0d1a1998664c2c92a7af695bd92eef02118c5d664505bfb9474c486f7e9995` | inspected |
| W089 | [528000, 534000) | `0adb9fcb0cc2dbc3cf623bd7c948afc1b06e0d3464cda5c9d38fe7fb470dbab9` | inspected |
| W090 | [534000, 540000) | `0fd0398c64b15409c3d6a04f6e7e45c67da76d395c86ff9935635587cef09b15` | inspected |
| W091 | [540000, 546000) | `5de19017ab338c1a19cf966b00f5265d53c182aabd0bc079900c2bf68203d470` | inspected |
| W092 | [546000, 552000) | `3dd45140eeb704208e75c4a7e2d139ea9b738a1444f3a7e48688d0387d569d02` | inspected |
| W093 | [552000, 558000) | `71ff79a373a824054cf312f894f6c0575be2165a26784a3ff92244a6bfe6d15a` | inspected |
| W094 | [558000, 564000) | `d126cd36642ea1d5eb32522401b2003dd1d47746040b750a703615dd2842db16` | inspected |
| W095 | [564000, 570000) | `c4af887ead85e01643e301c974dbaf217aecd553475a313ddf0b6585e92f18f9` | inspected |
| W096 | [570000, 576000) | `77d593b5f091d7cad369109e059601a98d10205865c26ec0c5aa2b0b7c1ead78` | inspected |
| W097 | [576000, 582000) | `1cddd69e0493c5cc250de51e9059671fad8b90b3d7bed01b69961ef704aec571` | inspected |
| W098 | [582000, 588000) | `f17ba57fcbfcd4ea749e26f053041885b6d19ec5f42355dbc986823f8f7ae0ea` | inspected |
| W099 | [588000, 594000) | `c7ac3a39123ebdcc9dcc98da3d7169e6f5f2adcace652501730d90a2abd7b957` | inspected |
| W100 | [594000, 600000) | `cc605630da38f8bbb16e86e1f0c08a0d92dd365db8e8595f45cf2018592edec3` | inspected |
| W101 | [600000, 606000) | `636f1b91f8504d5e4bc21c160eb502341ca910f2597bee6762193ac7ad053955` | inspected |
| W102 | [606000, 612000) | `0bcb97ad77889bde4607d6d80eb2cfb86a5f2be44b50e08f06baec308d917354` | inspected |
| W103 | [612000, 618000) | `6e1c8bbfca6bea984faeb6457a14b071e93bfe18ba7abc95a29a1771d857a860` | inspected |
| W104 | [618000, 624000) | `00b22d21cd476e7237baf7f30bd3d99800ff3d63d5d2a21b776e3878701ee3f0` | inspected |
| W105 | [624000, 630000) | `f10febdb5d999bf72c1f08999f1656a5930bd2a8e1530a35b69b2bd2204f7659` | inspected |
| W106 | [630000, 636000) | `66749fac2144e9f8417b8d491270850030dfa953d00baed4ddfde6adaba11b6a` | inspected |
| W107 | [636000, 642000) | `d48fb4e415d9153092e9b7084bf31ed4f9842a11a8f39fa221318821c54b3822` | inspected |
| W108 | [642000, 648000) | `a46578db3bec90bdfddeeaceb8f9cd6282b300c0c98f7ca82824950742c695d8` | inspected |
| W109 | [648000, 649618) | `e329b14e2352a11c9a99b1f510af10da3b1f40d7188e0236881f16e27949a97b` | inspected |

Traversal checkpoints:

- `W001–W066`: cover, Parts I–II through the beginning of Item 7. `W007` contains the sole cbETH transfer-consequence occurrence. Other cbETH, international-market, crypto-investment and Deribit references do not independently answer the active questions.
- `W067`: Results of Operations. Contains the sole international-revenue-source occurrence and all three transaction-revenue driver spans.
- `W068–W075`: the rest of Item 7 and Item 7A. `W069` and `W070` contain two independent investment-policy occurrences; `W075` says investment assets are primarily held long term but does not state the regular-trading policy.
- `W076–W096`: financial statements and Notes. `W086` contains the third investment-policy occurrence. The Note 4 geographic table gives revenue amounts but not the main type of international revenue.
- `W097–W109`: remaining Notes, controls, Parts III–IV, exhibits and signatures; no acceptable occurrence.

After sequential traversal, full-text cross-checks covered direct terms and plausible alternatives: `cbETH`, `underlying staked ETH`, international/U.S./foreign revenue, geographic revenue, regular trading, long-term holdings, held-for-investment balances and policy, transaction revenue, fee rate, consumer Trading Volume, institutional revenue, derivatives trading and Deribit. No additional independently sufficient 50–200-character occurrence was found.

## Candidate findings

### `p38` — unchanged; one acceptable occurrence

- Round 1 decision: `o`
- Question: `What happens to underlying Ether when cbETH changes hands?`
- Occurrence: `W007`, `[38286, 38420)`, 134 chars
- Snippet: `Selling or otherwise transferring cbETH automatically transfers ownership of the underlying staked ETH, along with any rewards earned.`

Other cbETH references define or discuss the token but do not state the transfer consequence.

### `p21` — revise to one foreign-revenue-source intent; one acceptable occurrence

- Round 1 decision: `?`
- Round 1 comment: `沒涵蓋的海外營收來源，需要多個 evidence`
- Original question: `Coinbase domestic versus overseas revenue mix and foreign revenue source`
- Recommended revised question: `What mainly comprised Coinbase's international revenue in 2025?`
- Recommended query type: `factoid`
- Occurrence: `W067`, `[397600, 397659)`, 59 chars
- Snippet: `International revenue comprised mainly transaction revenue.`

The old query has two needs. The original evidence answered only geographic mix; making the mix sentence and source sentence separate OR alternatives would allow a partial answer to pass. The revision retains the missing foreign-source intent from the Round 1 comment as a single independently answerable need. The Note 4 table reports U.S. and international amounts but does not identify the revenue source, so it is not a second occurrence.

### `a21` — revise to policy only; three acceptable occurrences

- Round 1 decision: `?`
- Round 1 comment: `query 問單一問題，看是 policy 還是 liquidity constraints`
- Original question: `Coinbase policy and liquidity constraints for investment digital assets`
- Recommended revised question: `How does Coinbase approach regular trading of crypto assets it holds for investment?`
- Recommended query type: `passage`

Occurrences:

1. `W069`, `[410539, 410717)`, 178 chars: `We do not plan on engaging in regular trading of crypto assets, and, as an operating company, our investing activities in crypto are not part of our revenue generating activities`
2. `W070`, `[419843, 419994)`, 151 chars: `We do not plan to engage in regular trading of these crypto assets but may purchase additional crypto assets for investment as a buy and hold strategy.`
3. `W086`, `[515508, 515667)`, 159 chars: `Crypto assets held for investment are primarily held long term. The Company does not engage in regular trading of these assets but may lend them or stake them.`

The revised question removes liquidity stress, exceptional-sale and market-instability constraints. All three locations independently state the same non-regular-trading policy and must remain separate OR alternatives.

### `n06` — keep the broad driver question; three acceptable occurrences

- Round 1: new candidate
- Question: `What drove the change in Coinbase's transaction revenue in 2025?`
- Query type: `passage`

Occurrences:

1. `W067`, `[398200, 398367)`, 167 chars: `a lower average blended fee rate, primarily due to changes in the mix of Trading Volume from Simple users to Advanced and Coinbase One users who pay lower average fees`
2. `W067`, `[398388, 398472)`, 84 chars: `an increase of $277.0 million attributed to a 7% increase in consumer Trading Volume`
3. `W067`, `[398500, 398665)`, 165 chars: `an increase in institutional transaction revenue driven by an increase of $152.0 million attributed to derivatives trading, due mainly to the acquisition of Deribit.`

The filing discloses three distinct drivers. They do not need to increase answer diversity to be valid OR-hit alternatives. The original consumer fee clause is 210 characters, so it is not used; the 167-character causal subspan is the shortest self-contained compliant snippet. Other Deribit passages describe the business, risks or acquisition accounting but do not attribute the transaction-revenue change.

## Open human decisions

1. Confirm whether `p21` should retain the proposed international-revenue-source intent. Keeping both mix and source would require conjunctive/multi-passage grading, which is outside the current unchanged metric.
2. Confirm whether the three `n06` driver spans should each independently count as a hit. This task recommends yes because each is a company-disclosed causal answer to the broad question.
3. Human Round 2 decision and reviewer-comment fields remain blank; this task does not pre-approve its own proposals.

No recommended snippet violates the global 50–200 character limit.
