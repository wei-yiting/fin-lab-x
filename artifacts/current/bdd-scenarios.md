# BDD Scenarios

## Meta
- Design Reference: `artifacts/current/design.md`(DEV-135 spec + 2026-08-11 prelude 檢索可見性裁決)
- Generated: 2026-08-11
- Discovery Method: Three Amigos(PO / Dev / QA subagent teammates,3 challenge rounds + delta round)

---

## Feature: sec_dense_pipeline 結構化 ingest(DEV-135)

### Context
`ingest_filing(filing: ParsedFiling)` 把結構化 filing 切 chunk、embed、寫入新 Qdrant collection,
以 per-(ticker, fiscal_year) commit marker 保證 committed-or-absent invariant。
消費者:retriever(DEV-137)、citation 鏈路(DEV-125)、A/B eval(DEV-138)。

### Scenario Assumptions(discovery 收斂的裁決紀錄,斷言以此為準)

1. **Key 粒度**:(ticker, fiscal_year) 一 key 一份 filing;同 key 重 ingest = destructive 覆寫;
   10-K/A amendment 不自動處理(操作者手動重跑)。本專案只 ingest 10-K。
2. **Marker lifecycle 順序**(對齊實作,invariant 等價):marker 先覆寫為 `pending`(rerun 立即
   對檢索端隱形)→ wipe content(filter 以 `must_not status` 排除 marker)→ upsert chunks →
   最後 flip `complete`。任何時點中斷,檢索端皆為 absent。
3. **Marker payload**:`{ticker, fiscal_year, status}`;discriminator = `status` 欄位
   (content chunks 永不帶 `status`);wipe 與檢索共用同一 `marker_status_condition`。
4. **Canonical item key** = `item.strip().lower()`(如 `"1a"`、`"7a"`),三端共用:payload `item`、
   `sec://{accession_number}/{item}#{chunk_index}`、retriever filter。
5. **header_path** = string `"{TICKER} / {fiscal_year} / Item {KEY}. {title}[ / {block_heading}]"`
   — 沿用舊 collection 的 ticker/year 前綴慣例(production eval dataset startswith 比對依賴它),
   新舊唯一差異 = drop Part。FlatItem / reclassified / prelude chunk 止於 item 層,無懸空分隔符。
6. **fiscal_year 型別 = int**,ingest / marker / retriever filter 同一序列化路徑。
7. **Prelude 附掛無條件**:ingest 不量 size(`prelude or None`);3,000-char validity 語意完全屬
   上游 DEV-133;「>3,000 → None」在 ingest 層為 dead branch,不在本層測。
8. **共存組合不可達**:valid prelude 與 reclassified leading block 為同段 leading text 的互斥
   結果,同 item 不並存(依 DEV-133 語意 Reject,不出 scenario)。
9. **錯誤語意**:ingest_filing 不含 retry;失敗拋單一明確錯誤(非聚合重試容器);
   pending 狀態對 retriever 的觀察值與「從未 ingest」同型。
10. **穩定性界線**:sec:// ID / chunk_index 穩定性 = 同 pipeline 版本內 + producer 保證 items
    ordering 跨 run 穩定(DEV-132 frozen schema 承擔);tokenizer/splitter 升級不在承諾內。

### Rule: chunk 邊界不跨 block;三種 heading-less leading 內容(FlatItem / reclassified / valid prelude)走同一條 chunk 流

#### S-ingest-01: 大 block 切多 chunk,overlap 只存在同 block 相鄰 chunks 之間
> 驗證 per-block chunking 的核心 invariant:不跨 block、overlap 有界。

- **Given** toy ParsedFiling:NVDA FY2025,Item 1A 含 block「Risks Related to Our Industry」
  (約 4,800 tokens)與 block「Risks Related to Regulation」(約 300 tokens)
- **When** `ingest_filing` 完成
- **Then** 第一個 block 產出多個 chunks 且任一 chunk ≤512 tokens;相鄰 chunks 的重疊 ≤50 tokens
  且僅出現在同 block 內;第二個 block 獨立成 1 chunk;無任何 chunk 同時含兩個 block 的文字;
  40-token 的尾端 block 仍產出自己的 chunk(不合併、不丟棄)

Category: Illustrative
Origin: Multiple(PO seed + Dev overlap-invariant 修正)

#### S-ingest-02: valid prelude 產生自己的 heading-less leading chunk,進入可搜尋語料
> 驗證 2026-08-11 裁決:threshold 不再決定可搜尋性,三型態 leading 內容同路徑。

- **Given** toy ParsedFiling 依序含:StructuredItem(valid prelude 1,200 chars + 3 blocks)、
  FlatItem(約 2,000 tokens)、StructuredItem(首 block 為 reclassified 無標題 leading block)
- **When** `ingest_filing` 完成
- **Then** 三者各自產出 heading-less chunk(s)(`block_heading=None`),文字完整可被檢回;
  prelude chunks 位於該 item 所有 block chunks 之前;三型態 leading chunk 的 payload 同形

Category: Illustrative
Origin: Multiple(PO A4 反轉 + delta round)

#### S-ingest-03: 長 prelude 是獨立的 chunking 單位,不跨進首 block
> 驗證動機案例(DIS 2,610 chars 損益表)的多 chunk 行為與 prelude/block 邊界。

- **Given** StructuredItem:valid prelude 約 900 tokens + 首 block「Overview」約 600 tokens
- **When** `ingest_filing` 完成
- **Then** prelude 產出 ≥2 個 chunks,overlap 只存在 prelude chunks 彼此之間;無任何 chunk
  同時含 prelude 尾端與「Overview」開頭;prelude chunks 的 chunk_index 連續且小於首 block
  第一個 chunk 的 index

Category: Illustrative
Origin: Multiple(Dev + QA delta round)

#### S-ingest-04: 空 block text 不中斷 chunk 流
> 凍結 schema 允許 `text=""`;防「迴圈提早中斷 → 後續 blocks 靜默消失 + complete marker 永久化」。

- **Given** StructuredItem:block A(有內容)、block B(`text=""`)、block C(含關鍵財務數字)
- **When** `ingest_filing` 完成
- **Then** A 與 C 的 chunks 全部進 Qdrant 且內容可檢回;B 產出 0 chunks;不存在空 `text` 的
  point;chunk_index 連號無跳號

Category: Illustrative
Origin: QA(Q-5,schema 查證後依升級條款轉正)

### Rule: 每個 chunk payload 自足承載 citation 與 filter 欄位;prelude metadata 只附掛 block chunks

#### S-ingest-05: payload 全欄位,單一 point 可組出 citation 素材
> 驗證 acceptance criteria 1:全欄位含 citation 三欄,以及 header_path / item 格式。

- **Given** canonical toy ParsedFiling(NVDA FY2025,accession `0001045810-25-000023`、
  cik `0001045810`、primary_document `nvda-20250126.htm`;三種 item 型態交錯)
- **When** `ingest_filing` 完成後任取各型態的 chunk point
- **Then** payload 同時含 `ticker="NVDA"`、`fiscal_year=2025`(int)、`filing_date`、
  `filing_type`、`ingested_at`、`item`(canonical 如 `"7a"`)、`block_heading`、`prelude`、
  `header_path`(assumption 5 格式,drop Part)、`chunk_index`、`text`、citation 三欄 —
  單靠此 point 可組 `sec://0001045810-25-000023/7a#{chunk_index}` 與 EDGAR URL 素材

Category: Illustrative
Origin: PO

#### S-ingest-06: prelude 欄位的三態語意
> `None` 是明確值非缺欄位;附掛範圍 = 該 item 的 block chunks(含後段 block),prelude chunk 自身為 None。

- **Given** canonical fixture:含 valid prelude(參數化含 2,900 chars 邊界值)的 StructuredItem、
  FlatItem、含 reclassified leading block 的 StructuredItem
- **When** `ingest_filing` 完成
- **Then** 有 prelude 的 item:其**全部** block chunks(含最後一個 block)`prelude` = 完整
  prelude 文字,prelude 自身的 chunks `prelude=None`;FlatItem 與 reclassified 的 chunks
  `prelude` 欄位存在且為 `None`、`block_heading=None` — 讀取端可區分「無 prelude」與「欄位遺漏」

Category: Illustrative
Origin: Multiple(PO B2/B3 + Dev D-3 + delta round)

#### S-ingest-07: citation 穩定性 — normalization 三端一致 + 跨 re-ingest ID 不變
> citation 鏈路(DEV-125)的根 invariant:ID 漂移 = 下游存下的 citation 全斷鏈。

- **Given** toy filing 內兩個 item 的原始標籤為 `"1A"` 與 `"7"`;完成一次 complete ingest,
  記下各 chunk 的 sec:// ID 與 Qdrant point ID
- **When** 對同一份 filing 執行 wipe-before-rerun 後重新 ingest
- **Then** payload `item` 值 === sec:// URI item 片段 === retriever filter 接受值(同一
  canonical 字串,無 escape 轉換);相同內容的 chunk 得到相同 sec:// ID 與相同 point ID;
  point 總數不變

Category: Illustrative
Origin: Multiple(Dev D-5 + QA Q-2)

### Rule: commit marker 生命週期 — committed or absent

#### S-ingest-08: ingest 中斷 → 檢索端視為不存在(含錯誤語意)
> acceptance criteria「中斷模擬」;參數化中斷點,最鋒利的邊界是「資料 100% 在但 marker 未 flip」。

- **Given** (NVDA, 2025) 開始 ingest;中斷點參數化:(a) embedding 失敗、(b) chunks upsert 60%
  後失敗、(c) 全部 chunks upsert 完成但 complete flip 前中斷
- **When** ingest 以該中斷點失敗後,以 retriever 的判定介面查 (NVDA, 2025)
- **Then** 判定 = 不存在(cache miss),與從未 ingest 無異 — 即使 (c) 情境下全部 chunk points
  實體存在;caller 收到恰一個明確錯誤(非聚合多次嘗試的容器型錯誤),ingest 不在外層重試

Category: Illustrative
Origin: Multiple(PO C2 + Dev D-7 + Rule D 合併)

#### S-ingest-09: 失敗殘留重跑 → wipe 含 marker,無新舊混雜,鄰 key 完好
> wipe 的正向行為 + 作用範圍隔離(防 drop-collection 式偷懶實作)。

- **Given** (NVDA, 2024) 已 complete(chunks 可檢索);(NVDA, 2025) 前次失敗殘留
  pending marker + 部分 chunks
- **When** 重跑 (NVDA, 2025) ingest 且成功
- **Then** (NVDA, 2025) 的 chunk 數量 = 新 ParsedFiling 應有數量(無新舊混雜)、marker
  `complete`;(NVDA, 2024) 的全部 chunks 與 `complete` marker 完好不受影響

Category: Illustrative
Origin: Multiple(PO C3/C4 + QA Q-1)

#### S-ingest-10: complete 後重 ingest 中途失敗 → 舊資料不回來(destructive-first)
> 把覆寫語意釘成契約:absent 包含「吃掉先前已 commit 的資料」,無 rollback。

- **Given** (NVDA, 2025) 已 complete 且可檢索
- **When** 對 (NVDA, 2025) 重新 ingest,於 upsert 40% 時中斷
- **Then** 檢索端對 (NVDA, 2025) 的判定 = 不存在;舊的 complete 資料不會回來;marker 為
  `pending`(重跑成功後才恢復 complete)

Category: Illustrative
Origin: Dev(D-8;PO 判定為 envelope §2 legibility 的明文化)

#### S-ingest-11: marker 與 chunk 的 key 序列化一致;檢索 filter 排除 marker
> 第三寫入端(marker)漂移 = cache 永遠 miss 或 wipe 漏刪;排除靠 discriminator 機制不靠相似度。

- **Given** canonical fixture ingest 完成 complete
- **When** 以與 retriever 相同的 filter 介面查詢:(a) chunk 內容檢索、(b) marker cache-hit 判定
- **Then** (a) 命中且結果**永不含** marker point(`must_not status` 機制);(b) 回報 complete;
  marker payload 的 `ticker` / `fiscal_year` 與任一 chunk 對應欄位型別與值皆相等

Category: Illustrative
Origin: Multiple(QA Q-4 + Dev D-10 + PO C5)

#### S-ingest-12: 零 chunk filing → 拋 EmptyIngestError,不留 marker、不動既有資料
> 防「complete + 0 chunks」的 false cache-hit 永久化(U-2 決策,對齊實作語意)。

- **Given** (a) `items=[]` 的 ParsedFiling;(b) (NVDA, 2025) 已 complete,收到同 key 的
  零 chunk ParsedFiling
- **When** 呼叫 `ingest_filing`
- **Then** 拋出 `EmptyIngestError`;(a) Qdrant 無任何 (NVDA, 2025) point 含 marker;
  (b) 既有 complete 資料與 marker 完好、檢索照常 — guard 發生在任何 marker/wipe 動作之前

Category: Illustrative
Origin: Dev(D-9;實作已定案,scenario 對齊)

---

### Journey Scenarios

#### J-ingest-01: 混合型 filing 完整 ingest → 檢索與 citation 全鏈路
> 一條線走完 chunking、payload、marker、檢索可見性 — 含 prelude 裁決的動機驗證。

- **Given** canonical toy ParsedFiling(NVDA FY2025):StructuredItem(實質內容 valid prelude,
  如損益表文字)+ FlatItem + StructuredItem(reclassified leading block),中段夾一個空 block
- **When** 完整執行 `ingest_filing`,期間觀察 marker,完成後以 retriever 介面執行內容檢索與
  cache 判定
- **Then** ingest 期間 marker 曾為 `pending`、結束為 `complete`;全部 chunks 的 chunk_index
  為 0..N-1 全 filing 連號且跨 item 型態不斷裂(prelude chunks 佔 index 且位於其 item 最前);
  以 prelude 內容(損益表語意)query 可命中 prelude chunk 並組出合法 sec:// ID 與 EDGAR URL
  素材;point 總數 = 全部 chunks + 1 個 marker(prelude metadata 副本不產生額外 point);
  檢索結果永不含 marker;cache 判定 = hit

Category: Journey
Origin: Multiple

#### J-ingest-02: 失敗 → 重跑 → 恢復(可乾淨重試)
> Rule C/D 交界:caller 收到失敗後的 recovery path 是重跑,且重跑後狀態完整。

- **Given** (NVDA, 2025) ingest 於 upsert 中途失敗(殘留 pending + 部分 chunks),檢索端視為
  不存在
- **When** caller 重新執行同一份 filing 的 `ingest_filing` 且成功
- **Then** marker `complete`;chunk 數量與 chunk_index 序列與一次成功的 ingest 完全相同;
  檢索與 citation 行為恢復正常 — 失敗殘留對最終狀態零影響

Category: Journey
Origin: Multiple(PO D3 + Dev)

---

## Demoted(unit-test backlog,非 behavior scenarios)

- **恰 512-token block → 恰 1 chunk**(Dev D-2):防 char-based splitter 誤設,單呼叫 contract
  → chunking unit test。已 feedback 給 implement agent。
- 空 block text 的 unit 深度(S-ingest-04 的行為版之外的細節)由 implement agent 的
  parametrized unit case 承擔。
