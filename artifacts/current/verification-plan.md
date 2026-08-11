# Verification Plan

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Generated: 2026-08-11

## 共用測試環境(所有 Deterministic 條目沿用)

- Qdrant:`QDRANT_URL`(預設 `http://localhost:6333`),collection 以
  `SEC_TEXT_QDRANT_COLLECTION=sec_dense_bdd_verify` 隔離,每條 scenario 開頭 wipe collection
- Embeddings:**不打真 API** — patch `backend.ingestion.sec_dense_pipeline.vectorizer._embed_texts`
  為決定性假向量(docstring 明示 patchable seam);失敗注入也在此 seam 與 Qdrant client 層
- 輸入:手工構造 toy `ParsedFiling`(`backend.ingestion.sec_text_pipeline.filing_models`),
  不打 EDGAR;canonical fixture 與 boundary fixtures 分離(不做 mega-fixture)
- 檢索側觀察介面:`check_commit_marker_complete(...)`(cache 判定)+
  `client.query_points(..., query_filter=Filter(must=[ticker, fiscal_year], must_not=[marker_status_condition()]))`
  (內容檢索,與 retriever 同一 filter 構型)
- Runner:python script(pytest 形式),多數 scenario 收斂為 parametrized cases(envelope §5)

---

## Automated Verification

### Deterministic

#### S-ingest-01: 大 block 切多 chunk,overlap 只存在同 block 相鄰 chunks 之間

- **Method**: script(pure — `build_chunk_payloads`,無需 Qdrant)
- **Steps**:
  1. 構造 fixture:Item 1A 含 4,800-token block(連續文字,弱 separator,使 overlap 決定性發生)
     + 300-token block + 40-token 尾端 block
  2. `payloads = build_chunk_payloads(filing)`;以 `cl100k_base` tokenizer 重算各 chunk token 數
  3. 斷言:每 chunk ≤512 tokens;同 `block_heading` 相鄰 chunks 的共同前後綴 ≤50 tokens;
     不同 `block_heading` 的 chunks 之間零重疊文字;40-token block 恰產出 1 chunk
- **Expected**: 不跨 block invariant 成立;overlap 僅同 block 內、有界;小 block 不合併不丟棄

#### S-ingest-02: valid prelude 產生自己的 heading-less leading chunk,進入可搜尋語料

- **Method**: script(Qdrant 可觀察狀態)
- **Steps**:
  1. canonical fixture ingest(patched embeddings)完成
  2. scroll 全部 content points,按 `item` + `chunk_index` 排序
  3. 斷言:prelude 文字對應的 point 存在且 `block_heading=None`;其 `chunk_index` 小於同 item
     全部 block chunks;FlatItem 與 reclassified leading block 的 points 同樣 `block_heading=None`;
     三型態 leading chunk 的 payload 欄位集合相同
  4. 以 prelude 假向量做 `query_points`(must_not marker)斷言可命中該 point
- **Expected**: 三型態 leading 內容皆可搜尋、payload 同形、prelude chunks 位於 item 最前

#### S-ingest-03: 長 prelude 是獨立的 chunking 單位,不跨進首 block

- **Method**: script(pure — `build_chunk_payloads`)
- **Steps**:
  1. 構造 fixture:prelude ~900 tokens(連續文字)+ 首 block「Overview」~600 tokens
  2. 斷言:`block_heading=None` 且非 FlatItem 的 payloads ≥2 個、chunk_index 連續、
     皆小於「Overview」chunks;無任何 chunk `text` 同時含 prelude 尾句與 Overview 首句;
     prelude chunks 彼此 overlap ≤50 tokens
- **Expected**: prelude 為 pseudo-block;邊界 = block 邊界;不被 prepend 進首 block

#### S-ingest-04: 空 block text 不中斷 chunk 流

- **Method**: script(pure + Qdrant 各驗一次)
- **Steps**:
  1. fixture:Item 7 = [block A(有內容)、block B(`text=""`)、block C(含標記句
     "UNIQUE_MARKER_C")]
  2. `build_chunk_payloads`:斷言含 "UNIQUE_MARKER_C" 的 chunk 存在;無 `text==""` 的 payload;
     chunk_index 為 0..N-1 連號
  3. ingest 後 scroll:斷言 C 的 point 存在、collection 無空 text point、marker `complete`
- **Expected**: 空 block 產出 0 chunks 且不中斷後續 blocks;無 silent data loss

#### S-ingest-05: payload 全欄位,單一 point 可組出 citation 素材

- **Method**: script(Qdrant 可觀察狀態)
- **Steps**:
  1. canonical fixture(NVDA FY2025、accession `0001045810-25-000023`、cik `0001045810`、
     primary_document `nvda-20250126.htm`)ingest 完成
  2. 各型態任取一 point,斷言欄位齊備:`ticker="NVDA"`、`fiscal_year==2025`(int)、
     `filing_date`、`filing_type`、`ingested_at`、`item`(如 `"7a"`,== `item.strip().lower()`)、
     `block_heading`、`prelude`、`header_path`、`chunk_index`、`text`、`accession_number`、
     `cik`、`primary_document`
  3. 以 payload 機械組出 `sec://0001045810-25-000023/7a#{chunk_index}` 與
     `https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashless}/{primary_document}`,
     斷言組裝所需欄位無一缺漏
  4. `header_path` 斷言:startswith `"NVDA / 2025 / Item "`;不含 `"Part"`;block chunk 以
     `" / {block_heading}"` 結尾;FlatItem / prelude / reclassified chunk 止於 item 層無懸空分隔符
- **Expected**: 單 point 自足;header_path 沿用 ticker/year 前綴慣例且 drop Part

#### S-ingest-06: prelude 欄位的三態語意

- **Method**: script(pure — `build_chunk_payloads`,parametrized)
- **Steps**:
  1. parametrized fixtures:valid prelude 1,200 chars / 2,900 chars(邊界值)、FlatItem、
     reclassified(`prelude=""` + heading-less 首 block)
  2. 斷言:有 prelude 的 item — **全部** `block_heading != None` 的 chunks `prelude` == 完整
    prelude 文字(含最後一個 block 的 chunks);prelude 自身 chunks `prelude is None`;
    FlatItem / reclassified 的全部 chunks `"prelude" in payload` 且值為 `None`
  3. 斷言 2,900-char 案例行為與 1,200-char 完全相同(ingest 無 size 分支)
- **Expected**: `None` 是明確值;附掛範圍 = block chunks;無條件附掛

#### S-ingest-07: citation 穩定性 — normalization 三端一致 + 跨 re-ingest ID 不變

- **Method**: script(Qdrant 可觀察狀態)
- **Steps**:
  1. fixture 的 item 原始標籤 `"1A"`、`"7"`;第一次 ingest 完成後記錄
     `{point.id: (payload.item, payload.chunk_index)}` 快照與 point 總數
  2. 斷言三端一致:`payload.item == "1a"`;以 `"1a"` 做 filter 檢索命中、以 `"1A"` 查不到;
     `sec://` 片段直接使用 payload 值無 escape(charset 驗證:全部 `item` 值 match `[a-z0-9]+`)
  3. 對同一 fixture 重新 ingest(觸發 wipe-before-rerun)
  4. 斷言:第二次快照與第一次逐項相等(相同 point ID、相同 chunk_index)、point 總數不變
- **Expected**: ID 決定性成立(same-version);citation 不因 re-ingest 斷鏈

#### S-ingest-08: ingest 中斷 → 檢索端視為不存在(含錯誤語意)

- **Method**: script(失敗注入,parametrized 中斷點)
- **Steps**:
  1. 中斷點 (a):patch `_embed_texts` 直接 raise → 呼叫 `ingest_filing`
  2. 中斷點 (b):patch `AsyncQdrantClient.upsert` 於第 2 個 content batch 時 raise
     (`_UPSERT_BATCH_SIZE=100`,fixture >100 chunks)
  3. 中斷點 (c):patch `upsert` 使 content batches 全部成功、**marker complete 那次呼叫** raise
  4. 各中斷點斷言:`pytest.raises` 收到**恰一個** exception 且非聚合容器
     (非 `ExceptionGroup` / retry-exhausted wrapper);`check_commit_marker_complete(...) is False`;
     content query(must_not marker)照 retriever 構型執行後,呼叫端 cache 判定與「從未 ingest」
     行為一致 — (c) 情境下即使 scroll 顯示全部 chunk points 實體存在,判定仍為 absent
- **Expected**: committed-or-absent 在三個中斷點全部成立;無外層重試放大

#### S-ingest-09: 失敗殘留重跑 → wipe 含 marker,無新舊混雜,鄰 key 完好

- **Method**: script(Qdrant 可觀察狀態)
- **Steps**:
  1. (NVDA, 2024) 完整 ingest → complete;記錄其 point IDs
  2. (NVDA, 2025) 以 S-ingest-08(b) 方式製造殘留(pending marker + 部分 chunks)
  3. (NVDA, 2025) 重跑成功
  4. 斷言:(NVDA, 2025) content point 數 == fixture 應有 chunk 數(無舊殘留混入)、marker
     `complete`;(NVDA, 2024) 的全部 point IDs 原封不動、marker 仍 `complete`
- **Expected**: wipe 範圍恰為 (ticker, fiscal_year),不越界、不 drop collection

#### S-ingest-10: complete 後重 ingest 中途失敗 → 舊資料不回來(destructive-first)

- **Method**: script(失敗注入)
- **Steps**:
  1. (NVDA, 2025) 完整 ingest → complete,檢索可命中
  2. 同 key 重 ingest,patch `upsert` 於第 1 個 content batch 後 raise
  3. 斷言:`check_commit_marker_complete is False`(marker 已被覆寫為 pending);
     content 檢索行為 = absent;舊 chunks 不完整存在(wipe 已執行)— 無 rollback
- **Expected**: 覆寫語意為 destructive-first;caller 的 recovery 是重跑,不是退回舊版

#### S-ingest-11: marker 與 chunk 的 key 序列化一致;檢索 filter 排除 marker

- **Method**: script(Qdrant 可觀察狀態)
- **Steps**:
  1. canonical fixture ingest 完成
  2. `client.retrieve(ids=[commit_marker_id(ticker, fiscal_year)])` 取 marker point,斷言
     payload `{ticker, fiscal_year, status="complete"}` 與任一 chunk 的 `ticker`/`fiscal_year`
     型別與值皆相等(int == int、str == str)
  3. 以 marker 假向量(全零)做 content query(must_not `marker_status_condition()`),
     斷言結果永不含 marker point — 排除靠 filter 不靠相似度
  4. 斷言 content chunks 全部不帶 `status` 欄位(discriminator 唯一性)
- **Expected**: 第三寫入端零漂移;wipe 與檢索共用同一 marker 判定

#### S-ingest-12: 零 chunk filing → 拋 EmptyIngestError,不留 marker、不動既有資料

- **Method**: script(parametrized)
- **Steps**:
  1. (a) `items=[]` fixture → `pytest.raises(EmptyIngestError)`;scroll 斷言該 (ticker,
     fiscal_year) 零 points(含 marker)
  2. (b) 先完整 ingest (NVDA, 2025) → complete;再以 `items=[]` 同 key 呼叫 →
     `pytest.raises(EmptyIngestError)`;斷言既有 chunks 與 `complete` marker 原封不動、
     檢索照常命中
- **Expected**: guard 先於任何 marker/wipe 動作;不產生 false cache-hit,也不誤傷已 commit 資料

#### J-ingest-01: 混合型 filing 完整 ingest → 檢索與 citation 全鏈路

- **Method**: script(Qdrant 可觀察狀態,單一 canonical journey fixture)
- **Steps**:
  1. journey fixture:StructuredItem(實質內容 valid prelude,文字含 "TOTAL_REVENUES_MARKER")
     + FlatItem + StructuredItem(reclassified leading block),中段夾一個 `text=""` block
  2. patch `upsert` 以攔截記錄呼叫順序(不改行為):斷言第一次 marker upsert 為 `pending`、
     最後一次為 `complete`(期間 marker 曾為 pending 的可觀察證據)
  3. ingest 完成後:scroll 全部 points 斷言 `chunk_index` == 0..N-1 全 filing 連號、跨 item
     型態不斷裂、prelude chunks 位於其 item 最前
  4. 以 "TOTAL_REVENUES_MARKER" 的假向量 query(must_not marker):斷言命中 prelude chunk,
     並由其 payload 組出合法 `sec://` ID 與 EDGAR URL 素材
  5. 斷言 point 總數 == 全部 chunks + 1(marker)— prelude metadata 副本不產生額外 point、
     不被 embed
  6. `check_commit_marker_complete` == True(cache hit)
- **Expected**: chunking、payload、marker、檢索可見性一條線全通;prelude 裁決的動機
  (財務內容可搜尋)被直接驗證

#### J-ingest-02: 失敗 → 重跑 → 恢復(可乾淨重試)

- **Method**: script(失敗注入 + 恢復)
- **Steps**:
  1. journey fixture 以 S-ingest-08(b) 方式中斷 → 斷言檢索端 absent
  2. 解除失敗注入,重跑 `ingest_filing` 成功
  3. 對照組:同 fixture 在乾淨 collection 一次成功 ingest 的
     `{point_id: (item, chunk_index, text)}` 快照
  4. 斷言:重跑後快照與對照組逐項相等;marker `complete`;檢索與 cache 判定恢復正常
- **Expected**: 失敗殘留對最終狀態零影響 — recovery path 是重跑,結果與從未失敗過相同

---

## Manual Verification

### Manual Behavior Test

無 — 本 feature 全部行為可在本機 Qdrant + patched embeddings 下決定性驗證,無實體裝置或
高併發需求(envelope §1 明文排除併發情境)。

### User Acceptance Test

#### J-ingest-01: 混合型 filing 完整 ingest → 檢索與 citation 全鏈路

- **Acceptance Question**: payload schema 與 citation 素材是否符合 DEV-125/137/138 下游的
  預期消費形態?(格式一旦被下游引用即成對外 contract)
- **Steps**:
  1. PR review 時抽查 J-ingest-01 的 fixture 輸出:一個 prelude chunk、一個 block chunk、
     一個 FlatItem chunk 的完整 payload dump
  2. 核對 `item` canonical 格式(`"7a"`)、`header_path` 格式(ticker/year 前綴 + drop Part)、
     `sec://` ID 組裝結果是否為你要交給 DEV-125 citation 鏈路與 DEV-138 scorer 的最終形態
- **Expected**: 三個下游票開工前,對外欄位格式無需再改
