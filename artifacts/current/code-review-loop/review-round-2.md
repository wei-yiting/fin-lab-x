# Code Review Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-06
> Orchestrator verification notes appended at the bottom.

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 7 |
| Blocking | 0 |
| Major | 5 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 2 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Fixed | Recorded AAPL Item 9C/11 bleed 已在分類前裁切;新的 over-trimming regression 另列為 SP-2.1。 |
| 2 | M-1.2 | ✅ Accepted | Won't Fix 理由為明確 user ruling:`force=True` 代表重新 parse,不重新下載。 |
| 3 | M-1.3 | ✅ Fixed | `tenk._filing` 已移除並改用 public `Filing` API;其 refactor 引入的 legacy regression 另列為 M-2.1/M-2.2。 |
| 4 | M-1.4 | ✅ Fixed | 零 substantive item 時會在 save 前拋出 `EmptyFilingError`。 |
| 5 | M-1.5 | ✅ Accepted | Won't Fix 理由為明確 user-ratified schema contract。 |
| 6 | m-1.1 | ✅ Fixed | 五個 persisted models 均使用 `extra="forbid"`。 |
| 7 | m-1.2 | ✅ Fixed | Corrupt-cache test 已限定 `pydantic.ValidationError`。 |
| 8 | m-1.3 | ⚠️ Partially Fixed | README 已新增,但 `test_sec_core.py:284` 仍引用無法解析的 `design.md §8.3`。 |
| 9 | SP-1.1 | ✅ Accepted | user ruling:保留 repo convention `fiscal_year`。 |
| 10 | SP-1.2 | ✅ Fixed | Recorded AAPL stub/bleed case 已正確處理;新的 regex false positive 另列為 SP-2.1。 |
| 11 | SP-1.3 | ✅ Fixed | Latest-year mode 已移除,`fiscal_year` 必填;`store=` 依 ruling 保留為 keyword-only seam。 |

## Issues

### [Major] SP-2.1: Inline Item cross-reference 被誤判為下一個 section boundary
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` (_trim_section_text / _ITEM_HEADING_RE), `test_parser.py` no-foreign-heading test
- **Problem:** trim 沒有 structural anchor,任何後續 `Item N.` 都被視為 bleed boundary。合法 prose 如 "We discuss cyber risk under Item 1A. Risk Factors..." 也會匹配,導致 substantive text 被靜默刪除。測試還把「不得包含其他 Item heading」當 invariant,但 inline cross-reference 是合法內容。
- **Fix:** local trimmer 只認 structural context(行首 heading、觀察到的 glued 形態);加 inline cross-ref 保留 regression。

### [Major] M-2.1: Bundle refactor 改變 frozen `fetch_filing_obj()` 的行為
- **File:** `backend/common/sec_core.py`
- **Problem:** `_fetch_filing_obj_cached` 委派給 bundle fetch,後者對每次 fetch 都讀 `filing.document.document`(SGML/homepage lookup)— 所有既有 legacy caller 多了一次 network I/O 與 failure mode,違反 only-add/frozen baseline。
- **Fix:** legacy path 恢復原始 acquisition 行為;只有 bundle path 讀 citation metadata;加 regression test 證明 `fetch_filing_obj()` 不觸碰 `filing.document`。

### [Major] M-2.2: Metadata fetch failures 不會轉成 documented `SECError`
- **File:** `backend/common/sec_core.py`
- **Problem:** accession/cik/company、尤其 network-backed `filing.document` 的讀取在 error-classification try 之外;429/5xx/SDK error 直接洩漏 raw exception,違反 fetch 契約與 envelope §2/§4。
- **Fix:** metadata acquisition 放入 external-boundary error mapping;測 429/5xx/missing-document。

### [Major] M-2.3: Ticker validation 接受 path-special `"."` 與 `".."`
- **File:** `backend/ingestion/sec_text_pipeline/filing_store.py`
- **Problem:** `^[A-Z0-9.\-]+$` 接受 dot-only 值;`".."` 使路徑跳出 base_dir(envelope §4 boundary validation 缺口)。
- **Fix:** 要求 alphanumeric 起首/含量,禁止 path-special;加 `"."`/`".."` 測試。

### [Major] M-2.4: Non-obvious architecture decisions 沒有 ADR
- **File:** `docs/adr/`(缺)
- **Problem:** frozen structured schema exception、A/B only-add boundary、兩段 cache、非典型 force 語意都是長期決策,只存在於 README 與(預計的)PR body;envelope §4 要求 docs/adr/ 記錄。
- **Fix:** 新增聚焦 ADR(不反對 user-ratified 決策本身,只要求 durable record)。

### [Minor] m-2.1: Documentation sweep 仍有 unresolved 與 future-only claims
- **File:** `backend/tests/common/test_sec_core.py:284`(design.md §8.3 殘留)、`filing_store.py` 開頭、`README.md`(inspect helper 以現在式描述但不存在)
- **Fix:** 換成可解析 reference 或 self-contained rationale;inspect helper 改 future extension。

### [Minor] m-2.2: Force test 名稱與 ratified semantics 相反
- **File:** `test_parser.py` `test_force_refetches_and_overwrites`
- **Fix:** 改名 `test_force_bypasses_store_and_reparses` 並直接驗證 store 被略過、新結果被保存。

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| pydantic | 2.12.5 | ConfigDict(extra="forbid"), discriminated union, Field(min_length=1), JSON round trip, model_copy() | ✅ Current | |
| edgartools | 5.17.1 | Filing.accession_number/cik/company/document, Attachment.document | ⚠️ API valid, integration wrong | `Filing.document` 走 sgml()/homepage;目前 placement 改變 legacy fetch 行為且 failure 未映射為 SECError |

---

# Spec Conformance Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-06

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 1 |
| Missing | 0 |
| Scope creep | 1 |
| Misimplemented | 0 |

## Previous Findings Status

| Issue ID | Status | Notes |
|----------|--------|-------|
| SP-1.1 | Accepted | `fiscal_year` 為 repo-wide convention(final ruling)。 |
| SP-1.2 | ✅ Fixed | Item boundary 先裁切再 stub classification;AAPL Item 11 drop、9C 乾淨。 |
| SP-1.3 | ✅ Fixed / Accepted | Latest mode 移除;keyword-only `store=` 依 ruling 接受。 |

## Findings

### [Major] SP-2.1(spec 軸): 新增未規範的 zero-item failure contract
- **Type:** Scope creep
- **Spec:** 「parse_filing(ticker, year, force) -> ParsedFiling」
- **File:** `parser.py`(EmptyFilingError)、`__init__.py`(public export)
- **Problem:** DEV-132 沒有要求 zero-item filing 成為失敗;schema 允許 `items=[]`。實作新增公開 exception contract。
- **Fix:** 移除,或取得明確 spec ruling 納入 contract。
- **[Orchestrator note]** 該 exception 正是 quality 軸 M-1.4 的 user-ratified 修法(envelope §2 legible-failure)。處置:declined by prior ruling;裁決將回寫 DEV-132 description 與 PR body 使其 durable。

## Covered Requirements

(15 項全數確認,含:簽名定案、bleed 修正生效、degenerate detection、FetchedFiling 走 public API 不洩漏 edgartools types、union/invariant、stub v2 helper 委派、JPM/XOM cases、60k MD&A 存活、JSON store 路徑、Seam-1 fixture 不打 EDGAR)

---

# Orchestrator verification(round 2)

- **SP-2.1(over-trim)證實**:synthetic "under Item 1A. Risk Factors" 令 `_trim_section_text` 截斷 Item 7 其餘全部內文。真實 AAPL FY2025 落地資料未受害(僅 9C 2581→94、4 2979→81,皆為正當 bleed 裁切;其餘 17 items 位元不變),但 hazard 對其他 filings 真實存在(10-K prose 常見 "See Item 1A." 句式)。
- **M-2.1/M-2.2 證實(code inspection)**:`_fetch_filing_obj_cached` 委派 bundle → 每次 legacy fetch 都執行 `filing.document.document`(network);metadata 四讀全部在 error-classification try 之外。
