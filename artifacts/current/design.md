# Design: sec_dense_pipeline 新 contract — 結構化 ingest + Qdrant payload schema + commit marker(DEV-135)

> 來源:Linear DEV-135 spec + 母 spec DEV-127(ingest 相關章節)。本文件為 behavior-validation-plan 的輸入,
> 僅整併 spec 層資訊 — 不含任何 implementation code 細節。

## 1. Feature 概述

`sec_dense_pipeline`(沿用名)改 contract:`ingest_filing(filing: ParsedFiling)` 直接吃結構化輸入,
把一份 10-K filing 的 chunks + metadata 寫入新 Qdrant collection,並以 commit marker 保證
「committed or absent」invariant(envelope §2)。

上游輸入 `ParsedFiling`(DEV-132 凍結 schema):

- metadata:ticker、fiscal_year、filing_date、filing_type、accession_number、cik、primary_document
- items:`list[StructuredItem | FlatItem]`(discriminated union,`kind` 欄位)
  - `StructuredItem` = prelude(可為 None)+ blocks(至少一個 block;block = heading + text)
  - `FlatItem` = 整段 text,無 block 結構、無 prelude
  - reclassified leading block:偽 prelude(>3,000 chars)在上游 detection 已轉為無標題 leading block,
    該 Item 的 prelude = None(DEV-133 裁決;ingest 信任 producer 的 gate,不重複驗證)

下游消費者:retriever(JIT 檢索,DEV-137 接線)、citation 鏈路(DEV-125)、A/B eval(DEV-138)。

## 2. Rules(spec 定案)

### Rule A — Per-block chunking(2026-08-11 prelude 檢索可見性裁決後版本)

- RecursiveCharacterTextSplitter,token-based 512/50
- chunk 邊界不跨 block:overlap 只發生在同一 block 內的相鄰 chunks 之間
- **三種 heading-less leading 內容走同一條路徑、處理方式一致**:FlatItem 整段、reclassified
  leading block(>3,000 chars 偽 prelude)、**valid prelude(≤3,000 chars)** — 三者都視為
  該 item 最前面的 heading-less leading chunk 進 chunk 流(可搜尋)
- valid prelude 因此身兼兩態:(1) 產生自己的 heading-less chunk 進可搜尋語料;
  (2) 同 item 其餘 block chunks 的 `prelude` payload metadata 維持原行為
  (≤3,000 附、>3,000 為 None)— threshold 只決定 metadata 附掛,不再決定可搜尋性
- 裁決動機:DIS Item 7(2,610 字完整損益表)、CAT Item 7(2,522 字全年 Highlights)等
  valid prelude 含正解內容,舊 contract 下不可搜尋 — 可見性與內容價值倒掛

### Rule B — Qdrant payload schema(新 collection,與舊 baseline 並存)

每個 chunk point 的 payload 欄位:

| 欄位 | 說明 |
|---|---|
| `item` | normalized item key |
| `block_heading` | chunk 所屬 block 的 heading(FlatItem / reclassified leading block 無 heading) |
| `prelude` | 該 Item 的有效 prelude;FlatItem 或 reclassified → `None`(必須正確表達,非缺欄位) |
| `header_path` | drop Part 之後的 heading 路徑 |
| `chunk_index` | 全 filing 範圍的連續索引(非 per-item) |
| `text` | chunk 純文字 |
| `ticker` / `fiscal_year` / `filing_date` / `filing_type` / `ingested_at` | filing metadata(採 `fiscal_year`,不沿用舊 collection 的 `year`) |
| `accession_number` / `cik` / `primary_document` | citation 三欄(DEV-125 定案,denormalized 每 chunk 直接帶) |

- citation 用途:`sec://{accession_number}/{item}#{chunk_index}` stable ID;`cik` + `primary_document`
  供 API/frontend 機械組出 EDGAR 直達 URL — URL 本身不存
- payload indexes 建立(檢索 filter 用),與 commit marker payload 同步採用 `fiscal_year` 命名

### Rule C — Commit marker 生命週期

- ingest 起點:寫入 per-(ticker, fiscal_year) marker point,`status: "pending"`
- 全部 chunks upsert 完成後,最後一步把 marker 改為 `status: "complete"`
- retriever 只認 `complete`(兼任 JIT cache 命中判斷)
- wipe-before-rerun:重跑前清掉該 (ticker, fiscal_year) 的所有 points,**含 marker**
- 檢索 query 必須排除 marker point(marker 與 chunk 同 collection)
- 中斷語意(envelope §2 committed-or-absent):ingest 中途失敗 → 檢索端視為該 filing 不存在;
  絕不讓檢索看到 partial 或 stale-mixed 資料

### Rule D — 錯誤與重試邊界(裁決紀錄)

- `ingest_filing` 內**不包** `retry_transient`:embedding client(pinned llama-index OpenAIEmbedding 0.6.0)
  自帶 tenacity retry;外層再包即 DEV-141 點名的疊加重試反模式
- ingest 失敗語意完全由 commit marker invariant 承擔;重試決策留給上層(DEV-137 JIT)
- prelude 無 size cap 驗證:信任上游 detection 的 3,000-char validity gate,ingest 不重複驗證(M-1.1 裁決)

## 3. 邊界與 Out of Scope(本票不驗)

- 同 ticker 並行 ingest 的 resolution(B-1.1)與 tracing span(M-1.3)→ DEV-137 wiring 時處理;
  本票時點無 caller,技術上無觸發路徑
- `ingest_filing` 零 production caller — ratified 例外(tracer-bullet 分片,首發 caller = DEV-137)
- parse 端行為(detection、prelude validity、stub drop)→ DEV-133/132 範圍
- A/B eval 流程、retriever 完整行為 → DEV-138/137 範圍(但「retriever 只認 complete / 排除 marker」
  的檢索側 invariant 屬本票 acceptance criteria)
- LLM 決策品質 → agent evaluation,非 behavior test

## 4. Envelope 約束(校準用)

- §1:corpus < 50k chunks、單一 Qdrant collection、payload indexing only;≤3 concurrent users、
  無 locking / queueing;concurrent same-ticker JIT 的 resolution 屬 DEV-137
- §2:committed-or-absent 是本票承擔的核心 invariant;失敗須 legible
- §5:測試斷言外部可觀察行為(Qdrant 狀態),不測內部 helper;不測 pinned dependency 行為;
  scenario 收斂為 parametrized cases;toy ParsedFiling 手工構造,不打 EDGAR、不打真 embedding API

## 5. Acceptance criteria(DEV-135 原文)

1. Seam-2 tests(toy ParsedFiling 輸入,斷言 Qdrant 可觀察狀態):payload 全欄位含 citation 三欄;
   block-chunk payload 的 `prelude` metadata 欄位在無 valid prelude 時(FlatItem / reclassified)為 `None`
2. valid prelude(≤3,000 chars)產生自己的 heading-less chunk,進入可搜尋語料 — 與 FlatItem、
   reclassified leading block 同一路徑;該 chunk 之後,同 item 其餘 block chunk 的 `prelude`
   payload metadata 欄位維持原行為不變(≤3,000 才附,>3,000 為 `None`)
3. Chunk 邊界不跨 block;同 block 內相鄰 chunk 有 overlap
4. Commit marker:pending → complete;retriever 只認 complete;wipe 含 marker;檢索排除 marker point
5. 中斷模擬:ingest 中途失敗 → 檢索端視為不存在(committed or absent invariant)
