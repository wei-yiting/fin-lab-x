# RAG Filter Eval — Experiment Results

> **One-line takeaway**: 在 SEC 10-K 中文 query 場景,沒做 metadata + tenant 三層契約的 naive collection 平均 ticker-precision@10 為 **0.62**,但 per-query 變異極大(**0.00 → 1.00**);加上三層契約並以 ticker filter 查詢後,所有 18 題的 precision 都是 **1.00**(filter mechanism 的 tautology)。**Naive 模式的低點與變異才是這個實驗的 finding。**

---

## 1. 實驗設定

| 參數 | 值 |
|---|---|
| Embedding model | `text-embedding-3-large` (3072 dims, deterministic) |
| Vector DB | Qdrant v1.17.1 |
| Distance | Cosine |
| Top-k | 10 |
| Total chunks | 1,844 (sentinels excluded) |
| Tickers | GOOGL (397) · INTC (402) · MSFT (371) · NVDA (338) · AAPL (253) · AMD (83) |
| Fiscal years | 2025 except NVDA 2026 |
| Dataset | 18 中文 query,6 tickers × 3 題 |
| Query language | 中文 query;沒有任何 query 直接出現 ticker code |

兩個 collection 共用**完全相同**的 embedding vectors —— naive 是用 Qdrant `scroll + upsert` 從三層契約 collection 拷貝過去,只在 build-time 差別:

```
Collection A (naive)             vs   Collection B (three-layer)
─────────────────────                  ────────────────────────────
▪ Vectors only                         ▪ Vectors + payload
▪ No payload index                     ▪ KeywordIndex on ticker/year/item
▪ No is_tenant                         ▪ is_tenant=True on ticker
▪ HNSW built blind                     ▪ HNSW built tenant-aware
Query: search(q, top_k=10)             Query: search(q, must=[ticker=X], top_k=10)
```

---

## 2. Aggregate Summary

| Metric | Naive(無契約、無 filter) | Three-layer(有契約、帶 filter) |
|---|---:|---:|
| **Mean p@5** | **0.644** | **1.000** |
| **Mean p@10** | **0.622** | **1.000** |
| Std dev p@5 | 0.326 | 0.000 |
| Std dev p@10 | 0.312 | 0.000 |
| Min p@10 | **0.00** | 1.00 |
| Max p@10 | 1.00 | 1.00 |
| Queries scored | 18 | 18 |

> 三層契約的 1.000 是 filter mechanism 的數學 tautology(`must=[ticker=X]` 強制保證 Top-k 全屬 X)—— 本身不是 finding。**真正值得寫進文章的數字是 naive 那一欄的 0.622 平均 + 0.00 最低 + 0.312 標準差,以及下面的 per-query variance 表。**

---

## 3. Per-Ticker Breakdown(Naive)

| Ticker | n | p@5 mean | p@5 range | p@10 mean | p@10 range |
|---|---:|---:|---|---:|---|
| AAPL | 3 | 0.93 | 0.8 – 1.0 | 0.73 | 0.4 – 0.9 |
| AMD | 3 | **0.27** | **0.0 – 0.4** | **0.13** | **0.0 – 0.2** |
| GOOGL | 3 | 0.40 | 0.2 – 0.6 | 0.47 | 0.4 – 0.6 |
| INTC | 3 | 0.67 | 0.2 – 1.0 | 0.80 | 0.6 – 1.0 |
| MSFT | 3 | 0.93 | 0.8 – 1.0 | 0.87 | 0.7 – 1.0 |
| NVDA | 3 | 0.67 | 0.4 – 0.8 | 0.73 | 0.4 – 0.9 |

**觀察**:
- **AMD 是最大受害者**(僅 83 chunks,佔比 4.5%) —— naive 模式下三題平均 p@10 只有 **0.13**。語意上 AMD 跟 INTC / NVDA 同為 fabless 半導體,容易被搶到語意鄰居。
- **MSFT 表現最好** —— 「微軟」這個中文詞在語料中專屬性高,即使沒 filter 也能精準命中。
- **GOOGL** 雖然 chunks 數(397)最多,但「Google / 雲端」等概念在 AAPL / MSFT 的 10-K 也大量出現,語意相似度導致 contamination。

---

## 4. Per-Query Full Table

> `**TICKER:N**` 標示目標公司 chunks 數;其他 ticker 代表 cross-ticker contamination。

| Ticker | Query | Naive p@5 | Naive p@10 | Three p@5 | Three p@10 | Naive Top-10 ticker mix |
|---|---|---:|---:|---:|---:|---|
| AAPL | 蘋果在中國市場面臨什麼風險? | 1.0 | 0.9 | 1.0 | 1.0 | **AAPL:9**  GOOGL:1 |
| AAPL | 蘋果服務業務最新的成長趨勢是什麼? | 1.0 | 0.9 | 1.0 | 1.0 | **AAPL:9**  NVDA:1 |
| AAPL | 蘋果硬體產品的供應鏈集中度問題? | 0.8 | **0.4** | 1.0 | 1.0 | **AAPL:4**  NVDA:3  INTC:2  GOOGL:1 |
| AMD | AMD 在資料中心市場跟 Intel 競爭的進度? | 0.4 | **0.2** | 1.0 | 1.0 | **AMD:2**  INTC:7  NVDA:1 |
| AMD | AMD 的 AI 加速器產品有什麼策略? | 0.4 | **0.2** | 1.0 | 1.0 | **AMD:2**  NVDA:4  INTC:4 |
| AMD | AMD 面臨的供應鏈與製程依賴風險? | **0.0** | **0.0** | 1.0 | 1.0 | INTC:7  NVDA:3 |
| GOOGL | Google 在 AI 監管方面揭露了哪些挑戰? | 0.6 | 0.6 | 1.0 | 1.0 | **GOOGL:6**  NVDA:2  MSFT:2 |
| GOOGL | Google 最新財報提到哪些供應鏈風險? | 0.2 | **0.4** | 1.0 | 1.0 | **GOOGL:4**  AAPL:4  INTC:1  NVDA:1 |
| GOOGL | Google 雲端業務面臨什麼競爭壓力? | 0.4 | **0.4** | 1.0 | 1.0 | **GOOGL:4**  MSFT:5  AAPL:1 |
| INTC | 英特爾代工業務的策略與風險? | 0.2 | 0.6 | 1.0 | 1.0 | **INTC:6**  AAPL:2  NVDA:2 |
| INTC | 英特爾在 AI 晶片市場的競爭定位? | 0.8 | 0.8 | 1.0 | 1.0 | **INTC:8**  NVDA:2 |
| INTC | 英特爾製程技術轉型遇到哪些挑戰? | 1.0 | 1.0 | 1.0 | 1.0 | **INTC:10** |
| MSFT | 微軟在生成式 AI 方面有什麼競爭優勢? | 0.8 | 0.7 | 1.0 | 1.0 | **MSFT:7**  NVDA:2  GOOGL:1 |
| MSFT | 微軟跟 OpenAI 的合作對營運帶來什麼風險? | 1.0 | 0.9 | 1.0 | 1.0 | **MSFT:9**  NVDA:1 |
| MSFT | 微軟雲端事業的營收成長動能來自哪裡? | 1.0 | 1.0 | 1.0 | 1.0 | **MSFT:10** |
| NVDA | 輝達受美國出口管制影響的程度? | 0.8 | 0.9 | 1.0 | 1.0 | **NVDA:9**  INTC:1 |
| NVDA | 輝達在資料中心 GPU 的競爭優勢來源? | 0.8 | 0.9 | 1.0 | 1.0 | **NVDA:9**  INTC:1 |
| NVDA | 輝達面臨哪些客戶集中度風險? | 0.4 | **0.4** | 1.0 | 1.0 | **NVDA:4**  INTC:3  AAPL:2  GOOGL:1 |

---

## 5. 🔥 Per-Query Variance Highlights —— 文章可直接引用

### Tier 1: Catastrophic failure(naive p@10 ≤ 0.2)

| 排名 | Query | Naive p@10 | What went wrong |
|:---:|---|:---:|---|
| 1 | **AMD 面臨的供應鏈與製程依賴風險?** | **0.0** | Top-10 = 7 × INTC + 3 × NVDA + **0 × AMD**。整個 result set 沒有任何一個目標公司的 chunk —— 系統完美地誤導了下游 LLM,讓它用 Intel 和 NVIDIA 的供應鏈描述去「回答」AMD 的問題。 |
| 2 | **AMD 在資料中心市場跟 Intel 競爭的進度?** | **0.2** | Top-10 = 7 × INTC + 1 × NVDA + 2 × AMD。「跟 Intel 競爭」這個措詞觸發 INTC 的 data center 章節,但實際上問的是 AMD 自己的策略。 |
| 3 | **AMD 的 AI 加速器產品有什麼策略?** | **0.2** | Top-10 = 4 × NVDA + 4 × INTC + 2 × AMD。AI 加速器 + 策略在三家公司語料裡分布均勻,語意相似度無法區分。 |

> AMD 全軍覆沒 —— 3 題平均 **p@10 = 0.13**。
> AMD 在語料中只佔 4.5% chunks 比例,在沒有 filter 的純向量搜尋下,被語意鄰居完全淹沒。

### Tier 2: Half-poisoned(0.2 < naive p@10 ≤ 0.5)

| Query | Naive p@10 | 主要污染源 |
|---|:---:|---|
| **Google 最新財報提到哪些供應鏈風險?** | 0.4 | AAPL:4(蘋果亞洲代工供應鏈描述太經典) |
| **Google 雲端業務面臨什麼競爭壓力?** | 0.4 | MSFT:5(Azure 章節壓過 Google Cloud) |
| **輝達面臨哪些客戶集中度風險?** | 0.4 | INTC:3 + AAPL:2 + GOOGL:1(customer concentration 是通用財報語言) |
| **蘋果硬體產品的供應鏈集中度問題?** | 0.4 | NVDA:3 + INTC:2(hardware supply chain 在三家都很相似) |

### Tier 3: Clean baseline(naive p@10 = 1.0)—— 文章的「為何不是每題都壞」

| Query | Naive p@10 | 為何 entity 信號夠強 |
|---|:---:|---|
| **微軟雲端事業的營收成長動能來自哪裡?** | 1.0 | 「微軟」+「雲端」+「營收成長」三層 disambiguator 都在 MSFT 自己語料裡集中度極高 |
| **英特爾製程技術轉型遇到哪些挑戰?** | 1.0 | 「英特爾」+「製程技術轉型」是 INTC 的 unique narrative(其他公司是 fabless,不會講自己的 fab 轉型) |

> **這個觀察支撐文章 Section 6 的論點** —— pre-filter 不是萬靈丹,有些 query 的 entity scope 在 embedding space 已經夠 disambiguated,filter 帶來的邊際效益很小。但對 AMD 那類語意上會被淹沒的 query,filter 是從 0% 變 100% 的差別。

---

## 6. Cross-Ticker Contamination Patterns

> 統計 naive 模式下,每個目標 ticker 被哪些其他 ticker 污染最多。

| Target | Most common contaminants(across all 3 queries × top-10) |
|---|---|
| AMD | INTC(主要對手) > NVDA(同為 fabless GPU/AI 廠) |
| GOOGL | AAPL(蘋果供應鏈)+ MSFT(雲端競爭)|
| NVDA | INTC(同晶片產業)|
| AAPL | NVDA, INTC(硬體類比)|
| INTC | NVDA, AAPL(科技廠通用財報語言)|
| MSFT | NVDA, GOOGL(AI 與雲端競爭)|

**觀察**:污染來源高度符合產業競爭關係 —— 這也是 entity-mismatch 的本質:**語意相似度在「同產業競爭對手」之間最強,而這正是讀者最不希望搞混的兩家公司**。

---

## 7. 數據怎麼讀

| 數字 | 是 finding 嗎? | 文章該怎麼用 |
|---|---|---|
| Three-layer p@10 = **1.000** | ❌ Tautology(`must=[ticker=X]` 數學保證) | 當「fix 達成」的對照,不要單獨炫耀這個數字 |
| Naive mean p@10 = **0.622** | ✅ Finding | 「平均六成的 retrieval 拿到正確公司,意味著 LLM 拿到的脈絡有近四成是錯實體的雜訊」 |
| Naive **std = 0.312** | ✅ Finding | 「不只是平均偏低,**變異還很大**(0% → 100%)—— 系統的可靠度從根本上不可預測」 |
| AMD 全軍覆沒(0.13 mean) | ✅ Finding | 「**小語料 ticker 在純向量搜尋下會被語意鄰居淹沒**,即使整個語料庫有它的資料」 |
| MSFT / INTC 部分 query 已達 1.0 | ✅ Finding | 「Pre-filter 不是每題都有戲 —— 對 entity 信號強的 query,加 filter 的邊際效益小」 |

---

## 8. 重現步驟

```bash
docker compose up -d qdrant
uv run python -m backend.scripts.embed_sec_filings GOOGL MSFT AAPL NVDA AMD INTC
uv run python -m backend.scripts.setup_naive_collection
uv run python -m backend.evals.eval_runner rag_filter_naive --local-only
uv run python -m backend.evals.eval_runner rag_filter_three_layer --local-only
```

Raw CSVs:
- `backend/evals/results/rag_filter_naive_<ts>.csv`
- `backend/evals/results/rag_filter_three_layer_<ts>.csv`

質性 Top-5 對照表(5 個 highlight query):
- `artifacts/retrieval_diff_<ts>.md`(由 `backend/scripts/dump_retrieval_diff.py` 產生)

---

## 9. Caveats

- **資料量小**:1,844 chunks 跨 6 公司。HNSW graph traversal 在這個規模下幾乎不會退化,所以 **latency / within-ticker recall 的差異無法被測量到**(這部分文章結語的「-30% latency / +25% recall」需要更大語料量才能實證,本實驗不涵蓋)。
- **Oracle ticker**:三層 scenario 假設 LLM router 完美地從 query 抽出 ticker(因 dataset 預先標好 `target_ticker`)。這個假設把 router accuracy 從實驗中 isolate 掉 —— 真實 production 中 router 抽錯 ticker 的成本是另一條獨立的議題。
- **n=3 per ticker**:per-ticker 平均的統計力有限,本實驗的數字呈現的是 *方向性* 而非精確 effect size。
- **語言不對稱**:中文 query → 英文 chunks。`text-embedding-3-large` 對跨語言對齊普遍良好,但這也是 entity-mismatch 容易發生的條件之一(中文「Google」跟英文 chunks 裡的 "Google / search engine / advertising" 的距離可能比英文「supply chain」跟「Google supply chain」更近)。
