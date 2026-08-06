# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-06

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 8 |
| Blocking | 0 |
| Major | 5 |
| Minor | 3 |
| Suggestion | 0 |
| Library checks | 2 |

## Issues

### [Major] M-1.1: Section bleed corrupts item boundaries and stub classification
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` L92
- **Problem:** `section.text()` is classified and persisted without isolating the current Item. The repository already documents that edgartools returns bleeding sections for AAPL FY2025 Items 9C and 11. The committed fixture contains exactly this shape: Item 11 includes Items 12–15, making the substantive tail push it above the stub threshold. Consequently, the test at `test_parser.py` L31 incorrectly requires Item 11 to survive even though its actual body is only an incorporated-by-reference stub. Item 9C likewise contains later Items. This leaks duplicated text into downstream chunks and defeats the stated "drop all stubs" behavior.
- **Fix:** Cut each body at the first subsequent standard Item heading before stub classification and persistence. Reuse `trim_text_to_item_boundary()` where applicable, but handle headings glued to Part markers such as `PART IIIItem 10.`. Change the recorded-fixture regression to assert that Item 11 is dropped and that emitted text never contains a later Item heading.

### [Major] M-1.2: `force=True` does not refetch from EDGAR
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` L60
- **Problem:** `force` bypasses the filing-store lookups but still calls `fetch_filing_obj()`, whose underlying `_fetch_filing_obj_cached()` is decorated with `@lru_cache` at `backend/common/sec_core.py` L369. In a long-lived process, `force=True` reparses the cached `TenK`; it does not refetch EDGAR. The test at `test_parser.py` L122 only counts calls to a monkeypatched function and therefore proves the wrong behavior.
- **Fix:** Provide an explicit uncached fetch or exact-key invalidation path in `sec_core` and invoke it when `force=True`. Test with the real cached fetch seam so the second call proves the underlying EDGAR acquisition executes again.

### [Major] M-1.3: Metadata extraction depends on an undocumented private edgartools attribute
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` L107
- **Problem:** `tenk._filing` is private and is not part of edgartools' documented `CompanyReport` API. The comment acknowledges the unsupported dependency but does not make it stable. An edgartools upgrade can break citation metadata extraction despite all documented APIs remaining compatible.
- **Fix:** Preserve the public `Filing` object at acquisition time and pass a small domain result containing both the report and required metadata into this pipeline. Because `sec_core` is only-add during A/B coexistence, add a new acquisition entry point rather than changing the existing `fetch_filing_obj()` contract.
- **Context7:** `CompanyReport` exposes `filing_date`, `form`, `company`, and `period_of_report`, but no public accessor for its underlying `Filing`. Obtain citation fields from a retained `Filing` using its public `cik`, `company`, `accession_no`/`accession_number`, and `document` properties.

### [Major] M-1.4: An empty parse is silently cached and returned as success
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` L68
- **Problem:** `_parse_items()` may return an empty list, after which `parse_filing()` saves and returns it as a successful filing. The test at `test_filing_models.py` L85 explicitly says failure legibility belongs to the parser, but the parser implements no such guard. This violates Design Envelope §2 and §4: silent empty ingestion is a bug in the JIT path.
- **Fix:** After parsing, reject an empty item list with a structured `SECError` subclass containing actionable ticker/year/accession context, and do not save the result. Add a parser test where every source section is empty or a stub.

### [Major] M-1.5: Future-only schema branch violates the reachability rule
- **File:** `backend/ingestion/sec_text_pipeline/filing_models.py` L42
- **Problem:** Possible **Speculative Generality**: `StructuredItem`, `Block`, `prelude`, and all three `detection_source` variants are exported as production API, but no production path emits or consumes them. The parser deliberately creates only `FlatItem`; the structured branch is instantiated only by tests and is described as support for later tickets. That is unreachable API surface under Design Envelope §0, and new speculative API surface is Major under §7.
- **Fix:** Either land the first structured-item detector and its consumer in this slice, or keep the current contract flat and add the structured union when that behavior becomes reachable. Do not freeze future variants solely through tests.

### [Minor] m-1.1: Persisted models silently discard unknown JSON fields
- **File:** `backend/ingestion/sec_text_pipeline/filing_models.py` L15
- **Problem:** Every model inherits Pydantic's default `extra="ignore"`. A cache produced with unexpected or newer fields will validate successfully while silently deleting those fields from the in-memory object and potentially from the next save. That weakens the claimed frozen, schema-validated contract.
- **Fix:** Set `ConfigDict(extra="forbid")` on every persisted model and add a round-trip test proving unknown top-level and nested fields raise `ValidationError`.

### [Minor] m-1.2: Corrupt-cache test accepts unrelated failures
- **File:** `backend/tests/ingestion/sec_text_pipeline/test_filing_store.py` L67
- **Problem:** `pytest.raises(Exception)` passes for any unrelated filesystem or implementation error, so it does not verify that corrupt JSON is rejected through Pydantic validation.
- **Fix:** Assert `pydantic.ValidationError` for schema-invalid JSON, and add a separate `json.JSONDecodeError` assertion only if malformed JSON behavior is part of the contract.

### [Minor] m-1.3: New pipeline lacks durable architectural documentation
- **File:** `backend/ingestion/sec_text_pipeline/filing_models.py` L3
- **Problem:** This folder has several non-obvious responsibilities—A/B coexistence, two cache stages, a frozen schema, private vendor-boundary handling, and versioned stub detection—but no README. Multiple docstrings cite bare `design.md` sections that do not exist in the reviewed tree, leaving contributors unable to resolve the stated decisions.
- **Fix:** Add a focused README covering scope, module map, parse/cache flow, A/B boundary, and extension rules. Replace unresolved `design.md §…` references with links to a committed durable document or the new README.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/ingestion/sec_text_pipeline/` | Scope, structure map, parse/cache data flow, A/B coexistence boundary, extension guidelines, and resolvable sources for the current `design.md §…` references |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| pydantic | `>=2.0` | Discriminated union, `Field(min_length=1)`, JSON round trip, `model_copy()` | ✅ Current | Union discrimination and list validation follow official patterns. `model_copy()` is safely used with already-normalized data, but the default `extra="ignore"` silently weakens cache validation. |
| edgartools | `5.17.1` | `TenK.sections`, `Section.item`, `Section.text()`, `TenK._filing`, `Filing` metadata | ❌ Wrong | Structured-section calls and public `Filing` fields are current. `TenK._filing` is undocumented private API; retain the public `Filing` during acquisition instead. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-06

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 3 |
| Missing | 0 |
| Scope creep | 1 |
| Misimplemented | 2 |

## Findings

### [Major] SP-1.1: `parse_filing` 不接受 spec 定義的 `year` keyword
- **Type:** Misimplemented
- **Spec:** "單一 public method parse_filing(ticker, year, force) -> ParsedFiling;edgartools internal types 不 leak 給 caller。" (DEV-127 parent-spec constraint)
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` L35
- **Problem:** Public method 將參數命名為 `fiscal_year`,因此依 spec 使用 `parse_filing(ticker=..., year=..., force=...)` 會得到 unexpected-keyword error,沒有忠實實作指定 API contract。
- **Fix:** 將 public 參數改為 `year`,並在內部需要時映射成 `fiscal_year`。

### [Major] SP-1.2: 未先切除跨 Item bleed,導致 stub Item 被保留
- **Type:** Misimplemented
- **Spec:** "ParsedFiling = metadata + list[StructuredItem | FlatItem](discriminated union, kind 欄位);StructuredItem = prelude + blocks(至少一個 block,schema 層 enforce);FlatItem = 整段 text;stub items 在 parse 階段直接 drop。" (DEV-127 parent-spec constraint)
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` L92
- **Problem:** `_parse_items` 直接對未切界的 `section.text()` 執行 stub detection。錄製的 AAPL Item 11 本身是 incorporated-by-reference stub,但 edgartools 回傳內容一路夾帶 Item 12–15;後續 Item 15 文字超過 remaining-content threshold,使 Item 11 被錯判為 substantive 並輸出成含 Item 15 內容的 `FlatItem`。既有 `trim_text_to_item_boundary` 完全未被使用。
- **Fix:** 在 stub detection 與 `FlatItem` 建立前,先以 `trim_text_to_item_boundary(text, key)` 切到下一個 Item boundary;增加 fixture-backed parser assertion,確認 AAPL Item 11 被 drop,且保留的 Item 不含下一個 Item heading。

### [Major] SP-1.3: Public API 新增未要求的 latest-year 與 custom-store 模式
- **Type:** Scope creep
- **Spec:** "單一 public method parse_filing(ticker, year, force) -> ParsedFiling;edgartools internal types 不 leak 給 caller。" (DEV-127 parent-spec constraint)
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` L35
- **Problem:** Public method 額外提供 `fiscal_year=None` 的 latest-filing 模式與 `store=` injection,並為後者新增 `FilingStore` abstraction。這兩者都是 spec 未要求的新 option/API surface,不是完成固定 JSON filing store 所必需的 caller capability。
- **Fix:** Public method 應維持 `parse_filing(ticker, year, force)`;在內部建立 `LocalFilingStore`。若測試需要 injection,使用 private helper 或 monkeypatch constructor,避免擴張 public contract。

## Covered Requirements

✅ `ParsedFiling` 定義為 `metadata + list[StructuredItem | FlatItem]` discriminated union,使用 `kind` discriminator — `backend/ingestion/sec_text_pipeline/filing_models.py`
✅ `StructuredItem` 包含 `prelude`、`blocks` 與指定的 `detection_source` literals — `backend/ingestion/sec_text_pipeline/filing_models.py`
✅ `StructuredItem.blocks` 至少一個的 invariant 在 Pydantic schema 層 enforce — `backend/ingestion/sec_text_pipeline/filing_models.py`
✅ `FlatItem` 僅保存整段 `text`,且不定義 `detection_source` — `backend/ingestion/sec_text_pipeline/filing_models.py`
✅ `FilingMetadata` 包含 `accession_number`、`cik`、`primary_document`,並由 edgartools filing object 取得 — `backend/ingestion/sec_text_pipeline/parser.py`
✅ Detection 的 degenerate 版本會將所有保留的 Item 建為 `FlatItem`,未實作 DEV-133 的 markdown detection — `backend/ingestion/sec_text_pipeline/parser.py`
✅ JSON filing store 使用 `data/sec_text/{TICKER}/10-K/{YEAR}.json`,讀回時執行 `ParsedFiling` validation — `backend/ingestion/sec_text_pipeline/filing_store.py`
✅ Fetch、建立 `ParsedFiling`、JSON save 與 validated round-trip 已串接 — `backend/ingestion/sec_text_pipeline/parser.py`
✅ Stub v2 透過 `sec_core` 的參數化 remaining-content helper 加入既有與 pseudo-stub patterns — `backend/common/sec_core.py`
✅ 舊 `is_stub_section` 仍以空 extra-pattern set 呼叫共用 helper,v1 判定行為不增加 pseudo-stub patterns — `backend/common/sec_core.py`
✅ JPM 7/7A 與 XOM 7/7A pseudo-stub cases 均有對應測試 — `backend/tests/ingestion/sec_text_pipeline/test_stub_detection.py`
✅ 60k 字 substantive MD&A 含 `"Reference is made to"` 時不會被判定為 stub — `backend/tests/ingestion/sec_text_pipeline/test_stub_detection.py`
✅ 第三個 pseudo-stub regex 對 spec 自相矛盾處採 bounded multi-word 修正,並在程式內明確記錄偏差理由 — `backend/ingestion/sec_text_pipeline/stub_detection.py`
✅ Seam-1 parser tests 使用錄製的 AAPL filing fixture,並 monkeypatch EDGAR fetch seam — `backend/tests/ingestion/sec_text_pipeline/conftest.py`
✅ 未加入 markdown H3/H4 detection、inspect/CLI、dense ingest、Qdrant、observability 或 migration 等後續 ticket scope — `backend/ingestion/sec_text_pipeline/`
