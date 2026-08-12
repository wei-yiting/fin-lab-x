# BDD Scenarios

## Meta
- Design Reference: `artifacts/current/design.md`
- Generated: 2026-08-12
- Discovery Method: Three Amigos (Agent Teams) + 對照已審查完成的 implementation 交叉驗證

> 本輪 discovery 除了標準 Three Amigos 三輪 challenge 之外，另外對照了同分支上一個平行
> session（`code-review-loop`，2 輪 quality + spec conformance review，reviewer 為
> Codex gpt-5.6-sol）已經產出的審查結論，以及 user 對兩個未定案項目的最終裁決。標為
> **「由 code review 發現」**的 Rule 不是本次 Three Amigos 挖出來的，是交叉比對時發現
> Three Amigos 完全沒觸及的缺口，補在這裡以確保 verification-plan.md 涵蓋完整的 CLI
> 行為面。Stub-dropped items 可視化（原 CQ1）已裁決另開 [DEV-149](https://linear.app/dongwyt-dev-projects/issue/DEV-149)（凍結 schema 擴充，DEV-134 完成後的後續票），本輪明確排除，見文末說明。

---

## Feature: Inspect View + CLI

### Context

`sec_text_pipeline` 用 edgartools 結構化 API 重寫 SEC 10-K parsing，detection（block 切分、
prelude 判定）本身可能出錯，出錯後果是內容從檢索索引消失。Inspect 是給 operator 手動抽查
detection/prelude 判定品質、對照 SEC 原文確認「retrieval 問題不出在 chunking 之前」的工具
——三個 CLI 入口（`--verbose` 摘要表、`--section <key>` 單 Item 純文字、`inspect` subcommand
完整 markdown）都是同一份 render 邏輯（`inspect_view.py`）在不同 CLI mode 上的呈現，不改變
凍結的 `filing_models.py` schema。

依 [design-envelope](../../docs/design-envelope.md) §5 校準：這是 operator 內部工具，非
Production-Grade Zone，標準是「happy path + 每個 behavior 一個 legible-failure case」，
以下 Rule 刻意不做窮舉性 edge case 排列組合。

---

### Rule: StructuredItem 完整攤開 render，不截斷、不做 chunk 切分

#### S-inspect-01: StructuredItem 的 detection_source 與所有 block 內容完整顯示
> 驗證完整 markdown render 對 StructuredItem 攤開所有必要欄位，且 block 內容不因長度被截斷

- **Given** NVDA FY2025 的 Item 7（MD&A）是一個 StructuredItem，`detection_source` 為
  `markdown_h3`，有兩個 block（「Results of Operations」約 4,500 字、「Liquidity and
  Capital Resources」約 1,200 字）
- **When** operator 執行 `inspect` 產出完整 markdown
- **Then** 輸出明確顯示 `detection_source: markdown_h3`，依序列出兩個 block 各自的
  heading 與完整內容（4,500 字的 block 整段照原文顯示，不被截斷、不被切成多個
  chunk——`ParsedFiling` 本身沒有 chunk 邊界的概念，「blocks 邊界」與 embedding
  chunk 是不同層次）

Category: Illustrative
Origin: PO

---

### Rule: Prelude 判定依三態規則推斷（schema 本身不存判定結果）

#### S-inspect-02: Prelude 依 `prelude` 與 `blocks[0].heading` 的組合推斷成三種判定之一
> 驗證 render 邏輯正確推斷 valid / reclassified leading block / no prelude 三種狀態，而非讀取一個不存在的判定欄位

- **Given** 一個 StructuredItem 的 `prelude`、`blocks[0].heading` 依下表變化
- **When** operator 執行 `inspect` 或 `--verbose`
- **Then** render 出的 prelude 判定是 `<判定>`

| prelude | blocks[0].heading | 判定 | 附加資訊 |
|---|---|---|---|
| 非空字串（如 CAT 1A 的 2,532 字前言） | （不影響判定） | valid | 附 chars 數，如「valid (2,532 chars)」 |
| `""` | `""`（無標題） | reclassified leading block | 附該 block 的 chars 數（原本 >3,000 字的偽 prelude 被轉正文） |
| `""` | 非空（如「Quantitative and Qualitative Disclosures」） | no prelude / absent | 不附 chars 數（沒有東西可數） |

Category: Illustrative (table-driven)
Origin: PO

---

### Rule: FlatItem 顯示 kind、完整字數，以及有長度上限的內容 preview

> **2026-08-12 使用者裁決**：design 原文「字數（或 preview）」在 Three Amigos 討論中一度被
> 誤記為「只顯示字數」（討論過程中的 paraphrase 失真，非設計本意），且與此同時，平行進行的
> `code-review-loop` 兩輪 review 都把「顯示完整未截斷內容」判定為 spec-conformant。使用者
> 最終明確裁決：**字數 + preview**（有長度上限的截斷內容），既非只顯示字數、也非顯示完整
> 未截斷全文。截斷長度本身 implementation 階段再定案。

#### S-inspect-03: 短文字 FlatItem 在 preview 長度限制內，完整顯示不截斷
> 驗證內容短於 preview 上限時不會被誤截斷

- **Given** Item 4（Mine Safety Disclosures）是一個 FlatItem，`text` 為
  `"Not applicable."`（短於 preview 長度上限）
- **When** operator 執行 `inspect`
- **Then** 輸出顯示 `kind: flat`、完整字數（16 chars），且 preview 內容與 `text` 完全相同
  （沒有截斷標記）

Category: Illustrative
Origin: PO

#### S-inspect-04: 長文字 FlatItem 的 preview 被截斷，但完整字數仍照實顯示
> 驗證超過 preview 上限的內容會被截斷並標記，但字數統計仍反映原始完整長度

- **Given** Item 9B（Other Information）是一個 FlatItem，`text` 長度遠超過 preview 字數
  上限（如 2,000 字的說明文字）
- **When** operator 執行 `inspect`
- **Then** 輸出的字數欄位仍顯示完整的 2,000 字（不是截斷後的長度），但 preview 內容本身
  在上限處被截斷並附上截斷標記（如「…」），截斷點之後的原文不會出現在輸出裡

Category: Illustrative
Origin: PO（ratified by user，覆蓋先前 code review 已核准的「完整內容」判定）

---

### Rule: `detection_source` 直接顯示欄位值，不假設固定的字面值集合

#### S-inspect-05: 三種 detection_source 值（含尚未由其他票產出的第三種）都能正確顯示
> 驗證 render 邏輯是「顯示欄位值」而非「hardcode 兩個 if/elif 分支」，對未來新增的偵測路徑天然相容

- **Given** 一個 StructuredItem 的 `detection_source` 依下表變化
- **When** operator 執行 `inspect` 或 `--verbose`
- **Then** 輸出正確顯示對應的 `detection_source` 值

| detection_source | 說明 |
|---|---|
| `markdown_h3` | 目前 real data 中最常見的偵測路徑 |
| `markdown_h4` | 目前 real data 中會出現的第二種路徑 |
| `text_fallback` | producer 是尚未 merge 的 DEV-136；本 Item 用手造 fixture 模擬，證明 render 邏輯不會因為只認得兩個字面值而漏顯示或報錯 |

Category: Illustrative (table-driven)
Origin: PO

---

### Rule: `--verbose` 產出一畫面內看完的摘要表，不含任何內文

#### S-inspect-06: 摘要表對混合 kind 的 filing 給出一致的欄位配置
> 驗證 StructuredItem 與 FlatItem 混合出現時，表格仍能一致呈現、缺值有明確 placeholder

- **Given** 一份 filing 的 `ParsedFiling.items` 同時包含 StructuredItem（Item 7，
  `markdown_h3`，2 個 block）與 FlatItem（Item 1A，`"Not applicable."`）
- **When** operator 執行 `--verbose`
- **Then** 摘要表恰好兩行（表格行數等於 `items` 長度，stub 已在 parse 階段被丟棄不會
  出現），structured 列顯示 detection_source / prelude 判定 / block 數，flat 列的
  這些欄位以固定 placeholder（如「—」）表示不適用，兩者都顯示各自的完整字數

Category: Illustrative
Origin: Dev

#### S-inspect-07: `--verbose` 摘要表不洩漏任何內文
> 驗證摘要表符合 AC「不含內文」的明文要求

- **Given** 同上一份混合 filing
- **When** operator 執行 `--verbose`
- **Then** 輸出裡不出現任何 block 的完整內容、prelude 全文，或 FlatItem 的內容 preview
  ——只有欄位層級的判定與計數

Category: Illustrative
Origin: PO

---

### Rule: `--section <key>` 輸出單一 Item 的純文字，不含 markdown 標記

#### S-inspect-08: StructuredItem 的 prelude 與多個 block 串接，保留 heading 當區隔
> 驗證多 block 串接時有清楚的邊界，不會讓不同 block 的內文黏在一起

- **Given** Item 7 是一個 StructuredItem，`prelude` 非空，有兩個 block：block 1（heading
  「Results of Operations」，內容以「…continuing operations.」結尾）、block 2（heading
  「Liquidity」，內容以「Legal proceedings include…」開頭）
- **When** operator 執行 `--section 7`
- **Then** 輸出依序是 prelude、block 1 的 heading 與內容、block 2 的 heading 與內容，
  彼此有清楚分隔（不是「…continuing operations.Legal proceedings include…」這種黏在
  一起的輸出），且不含任何 markdown 標記符號（如 `##`）

Category: Illustrative
Origin: Dev

#### S-inspect-09: `--section` 查詢 FlatItem 時直接輸出原始文字，不誤入 block-join 邏輯
> 驗證 FlatItem 這條分支走的是「直接印 text 欄位」的簡單路徑，不會因為程式碼誤套用 StructuredItem 的 block 串接邏輯而出錯或印出空白

- **Given** Item 1A 是一個 FlatItem，`text` 為完整一段文字
- **When** operator 執行 `--section 1a`
- **Then** 輸出恰好等於該 FlatItem 的 `text` 內容，不多不少（沒有 heading 前綴、沒有
  block 分隔符號，因為 FlatItem 本來就沒有 blocks 可分隔）

Category: Illustrative
Origin: QA

#### S-inspect-10: `--section` 的 key 比對大小寫不敏感
> 驗證 operator 打大寫或小寫 key 都能查到同一個 Item

- **Given** Item 1A 是一個 FlatItem
- **When** operator 分別執行 `--section 1A` 與 `--section 1a`
- **Then** 兩次輸出完全相同

Category: Illustrative
Origin: PO

#### S-inspect-11: 查詢一個這份 filing 沒有的 key，列出可用的 key 清單
> 驗證這是本 Rule 的 legible-failure case——filer 常見的省略某個 Item（如小型申報公司省略 9B）不會讓 operator 撞見一團看不懂的 traceback

- **Given** 一份 filing 的 items 只有 `7`、`1a`、`8` 三個 key（這份 filer 沒有揭露其他
  標準 Item）
- **When** operator 執行 `--section 9b`
- **Then** CLI 印出清楚訊息，明確列出這份 filing 實際可用的 key（`7, 1a, 8`），並以非零
  exit code 結束——不會是一段 Python traceback

Category: Illustrative
Origin: QA

---

### Rule: `inspect` subcommand 產出完整 markdown 檔案，路徑可直接開啟

#### S-inspect-12: 對同一 ticker/fiscal_year 重複執行 `inspect`，覆蓋既有檔案而非累積新檔
> 驗證 operator 反覆核對同一份 filing 時，打開的永遠是最新一次 parse 的結果，不會因為累積多個同名不同版本的檔案而搞混

- **Given** operator 先前已對 NVDA FY2025 執行過 `inspect`，輸出目錄下已存在對應的
  markdown 檔案
- **When** operator 再次對 NVDA FY2025 執行 `inspect`
- **Then** 同一個路徑的檔案被覆寫（新內容取代舊內容），不會在輸出目錄下產生第二個
  同 ticker/年度的檔案

Category: Illustrative
Origin: QA

---

### Rule: Filing-level header 出現在 Journey 與 `--verbose` 輸出，`--section` 不含 header

#### S-inspect-13: 三種輸出模式對 filing header 的顯示行為
> 驗證「這是哪一份 filing」在需要對照 SEC 原文核對的模式下可見，但不污染 `--section` 的單 Item 純文字契約

- **Given** 同一份已解析的 filing（ticker、fiscal year、accession_number、cik、
  primary_document 皆已知）
- **When** operator 分別用 `inspect`、`--verbose`、`--section <key>` 三種模式查詢
- **Then** `inspect` 與 `--verbose` 的輸出最上方都能看到 ticker / fiscal year /
  accession_number 等 filing 層級識別資訊；`--section` 的輸出完全不含這些資訊
  ——維持「單 Item 純文字」的單純契約

Category: Illustrative
Origin: PO

---

### Rule: Cache miss 時自動觸發 fetch + parse，operator 不用手動介入

#### S-inspect-14: 未快取過的 ticker 直接查詢即可，不需要額外指令
> 驗證 operator 不需要先手動下一個「抓資料」的指令

- **Given** MSFT FY2024 從未被 inspect 過（filing store 沒有對應的 JSON）
- **When** operator 對 MSFT FY2024 執行任一種 CLI 模式
- **Then** CLI 自動完成 fetch + parse + 落地 filing store，然後才渲染輸出——過程中
  operator 不需要下任何額外指令

Category: Illustrative
Origin: PO

---

### Rule: 輸出目錄透過 `data_paths` resolver 解析，可用環境變數覆寫，且被 gitignore

#### S-inspect-15: 預設輸出路徑與環境變數覆寫路徑
> 驗證 CLI 不 hardcode 路徑字串，且輸出不會意外進入 git 版本控制

- **Given** operator 未設定任何環境變數
- **When** operator 執行 `inspect`
- **Then** 輸出檔案落在 resolver 提供的預設路徑下，且 `git status` 不會把這個檔案列為
  untracked（已被 gitignore）
- **Given** operator 改設定 resolver 支援的 override 環境變數
- **When** operator 再次執行 `inspect`
- **Then** 輸出目錄改為環境變數指定的路徑

Category: Illustrative
Origin: PO

---

### Rule: `--verbose` 與 `--section` 互斥；`inspect` 不接受另外兩者的 mode flag——衝突在參數解析階段就報錯

#### S-inspect-16: 同時給兩個互斥的 mode flag，CLI 立即拒絕，不觸發任何 fetch/parse
> 驗證衝突的組合在最早的階段就被擋下，operator 不會誤以為拿到了某個模式的結果，實際上卻被悄悄忽略

- **Given** operator 準備查詢一個 ticker
- **When** operator 在同一次呼叫裡同時給 `--verbose` 與 `--section <key>`，或同時給
  `inspect` subcommand 與 `--verbose`/`--section`
- **Then** CLI 在參數解析階段就以清楚的 usage 錯誤拒絕，不會觸發任何 EDGAR fetch 或
  parse 動作（不會有「其中一個 flag 被悄悄忽略、operator 誤以為拿到另一個模式結果」的
  情況）

Category: Illustrative
Origin: Multiple（QA 發現 `--verbose`+`--section` 衝突，Dev 發現 `inspect`+`--verbose`
衝突，Dev 進一步證明「兩者合併輸出」在邏輯上與 Rule 1（不截斷）+ `--verbose`（一畫面）
兩條既有 Rule 互相矛盾，因此排除「合併」選項，只剩「二選一」或「拒絕」）

---

### Rule: `--force` 略過 filing store 快取，強制重新 parse

> **由 code review 發現**：本 Rule 不是這次 Three Amigos 討論找出來的——`--force` 是比照
> `_html` pipeline CLI 既有慣例而存在的 flag，Three Amigos 進行時可用的 design 內容裡沒有
> 提到它。平行的 `code-review-loop` 一度把它標成「未在 spec 明列的 scope creep」，使用者
> 裁決保留並正式寫入 DEV-134 spec：這是「抽查活躍變動中的 detection（DEV-136 開發期間）」
> 的必要工作流程——沒有 `--force` 就得手動刪 filing store 的 JSON 才能重新 parse。

#### S-inspect-17: 已有快取的 ticker 加上 `--force`，略過快取重新 parse
> 驗證 operator 在 detection 邏輯變動期間，能不必手動清快取就重新驗證同一份 filing

- **Given** NVDA FY2025 先前已被 inspect 過，filing store 已有對應的快取 JSON
- **When** operator 帶著 `--force` 對 NVDA FY2025 執行任一種 CLI 模式
- **Then** CLI 略過快取直接重新 parse（不是直接讀快取），並用新的 parse 結果覆寫 filing
  store，輸出反映的是這次重新 parse 的結果，不是舊的快取內容

Category: Illustrative
Origin: Dev（由 code review 補充發現，非原始 Three Amigos 產出）

---

### Rule: 例外狀況要有清楚可讀的失敗訊息，不能是原始 Python traceback

#### S-inspect-18: Filing 全部 section 皆空或 stub，CLI 印出含 ticker/年度/accession 的清楚錯誤
> 驗證這是本 Feature 明文點名的唯一失敗模式——operator 能立刻知道是哪一份 filing 出問題

- **Given** 一份 filing 的每個 section 都被判定為空或 stub（`parse_filing` 會拋出
  `EmptyFilingError`），filing store 完全沒有寫入任何東西
- **When** operator 對這個 ticker/年度執行任一種 CLI 模式
- **Then** CLI 印出的錯誤訊息裡能清楚看到 ticker、年度、accession number 三項資訊，並以
  非零 exit code 結束

Category: Illustrative
Origin: Multiple（PO 原始提出這是本 Feature 唯一該覆蓋的失敗模式，Dev 補充「訊息必須明確
包含三個值，不能只靠 `str(exception)` 的預設格式」）

#### S-inspect-19: 格式不正確的 ticker，CLI 印出清楚訊息而非洩漏 traceback
> **由 code review 發現**：本場景不是 Three Amigos 討論產出——是平行的 `code-review-loop`
> 實際測試 CLI 行為時發現的落地缺口（一開始只 catch 了一種例外類型，格式錯誤的 ticker
> 會讓 operator 看到整段 Python traceback），修好後補了對應的行為測試，本 Rule 補在這裡
> 確保 verification-plan.md 有涵蓋到

> 驗證 CLI 邊界能攔住 filing store 對 ticker 格式的驗證錯誤，而不只是 `EmptyFilingError`

- **Given** operator 打錯了一個格式不合法的 ticker（例如帶有路徑字元）
- **When** operator 對這個格式不正確的 ticker 執行任一種 CLI 模式
- **Then** CLI 印出一行簡潔的錯誤訊息並以非零 exit code 結束，不會出現原始 Python
  traceback

Category: Illustrative
Origin: Dev（由 code review 補充發現，非原始 Three Amigos 產出）

---

### 明確排除：Stub-dropped items 的可視化

Three Amigos 討論中原本浮現一個問題（design.md 原 CQ1）：一個 Item 被 `is_stub_section_v2`
判定為 stub 而整個丟棄後，inspect 完全看不到任何痕跡——連「這裡曾經有內容」都不知道。這觸及
DEV-127 user story #12 的核心動機（catch content-loss），但要做到「看見被丟棄的內容」，必須
先讓內容在 parse 階段被保留下來，這會直接修改凍結的 `filing_models.py`，與 DEV-134 自己的
明文限制（不修改凍結 schema）衝突。

**2026-08-12 使用者裁決**：確認這件事值得做，但不在 DEV-134 範圍內——另開
[DEV-149](https://linear.app/dongwyt-dev-projects/issue/DEV-149)（blocked by DEV-134，
明文的凍結 schema 例外，比照 DEV-132 對 `StructuredItem` 分支開過的先例）。本輪
bdd-scenarios.md 及對應的 verification-plan.md **不含**這塊行為；DEV-149 完成後應該重新
跑一次 behavior-validation-plan（或至少針對 DEV-149 的新 Rule 做一次增量更新，見本
skill 的 Incremental update 流程）。

---

### Journey Scenarios

> **2026-08-13 使用者裁決（bdd-e2e-loop Round 1 發現後）**：兩條 Journey 原本都指向
> MSFT FY2024，Round 1 對它真的跑了一次 `inspect`，結果 `EmptyFilingError`——
> edgartools 5.17.1 對 MSFT FY2024 的所有 24 個 section 都回傳 `section.item is None`，
> `_parse_items` 因此整份跳過。使用者確認：**MSFT FY2024 要等 DEV-136（text fallback）
> merge 後才能走通，在那之前這是已知限制，不是 DEV-134 的 bug**——與 DEV-127 spec 的
> Known Limitation #3（「Source-level missing...上游邊界，不在我們 detection 可修範圍
> → ParsedFiling 缺項 + legible failure」）吻合。兩條 Journey 改用 AAPL：
> J-inspect-01 換成 **AAPL FY2024**（尚未快取過，保留「cache miss」語意）；
> J-inspect-02 換成 **AAPL FY2025**（bdd-e2e-loop Round 1 用真實資料驗證過，確實有
> reclassified 的 Item，`--section` 輸出乾淨——比原本 NVDA FY2025 這個未經驗證的例子
>更紮實）。

#### J-inspect-01: 首次對未快取的 ticker 執行完整 inspect，並對照 SEC 原文核對
> 證明從「從未查過的 ticker」到「operator 能拿著檔案對照 SEC 原文核對」這條完整路徑走得通——這是 DEV-127 user story #12 的核心動機，也是 PO 提出的必要 Journey

- **Given** operator 想要核對 AAPL FY2024 的 detection/prelude 判定品質，這份 filing
  從未被 inspect 過
- **When** operator 執行 `inspect --ticker AAPL --fiscal-year 2024`，CLI 自動完成
  fetch + parse（cache miss），把完整 markdown 寫入輸出目錄並印出檔案路徑；operator
  打開這個檔案，依序核對每個 Item 的 detection_source、prelude 判定、block 邊界
- **Then** operator 能用這份檔案的內容，逐項對照 SEC EDGAR 原文，判斷 detection 是否
  正確、有沒有內容被誤判遺漏——檔案路徑可以直接開啟，不受 operator 執行指令時所在的
  工作目錄影響

Category: Journey
Origin: PO

#### J-inspect-02: Operator 標準抽查工作流程——先用 `--verbose` 掃視全貌，再用 `--section` 深入單一 Item
> 證明三個 CLI 入口不是三個互不相干的功能，而是同一套 render 邏輯支撐的一套完整工作流程——這正是 DEV-134 票面明講的「prelude 判定人工抽查與四象限 failure 分析的標準工具」

- **Given** operator 想快速掃過 AAPL FY2025 所有 Item 的 detection 狀態，找出看起來
  可疑的項目（例如某個 Item 的 prelude 被判定為「reclassified」，代表原本可能是超過
  3,000 字的偽 prelude）
- **When** operator 先執行 `--verbose` 看過一畫面的摘要表，注意到某個 Item 的 prelude
  判定是 reclassified；接著執行 `--section <該 item key>` 深入看這個 Item 的完整純
  文字內容，判斷這次 reclassify 是否合理
- **Then** operator 能在不重新解析 filing 的情況下（同一份已快取的 parse 結果），從
  「全貌掃視」自然銜接到「單點深入」，完成一次完整的人工抽查

Category: Journey
Origin: Multiple（PO 的原始 Journey 只涵蓋 `inspect` 一個入口；QA/Dev 在 Round 1-2 對
`--verbose`/`--section` 的細節挑戰，讓這個「三入口其實是一套工作流程」的洞察浮現出來）
