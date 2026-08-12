# BDD Scenarios

## Meta

- Design Reference: `artifacts/current/design.md`
- Generated: 2026-08-12
- Discovery Method: Three Amigos(Agent Teams)— PO/Dev/QA 三個角色,Phase 1 example seeding
  → Round 1/2 challenge(含 cross-talk)→ Round 3 judgment(含 1 次 user escalation、1 次
  contest)→ Phase 2.5 assumption check,共收斂 25 項 challenge。

## 給後續讀者的重要提醒

**不要撰寫斷言「三路偵測鏈中哪一條規則/哪一路造成了某個結果」的驗證**(例如「GE Item 1A
是因為 Rule 1 零候選、還是 Rule 3 plausibility 擋下才變成 FlatItem」)。`ParsedFiling` 的
schema(`prelude`/`blocks`/`detection_source`,FlatItem 不帶 `detection_source`)在三路皆
失敗時完全不記錄失敗原因,這類區分在黑箱層級不可觀察,只能在 unit test 層級斷言(呼叫內部
候選偵測函式),不屬於本文件的 declarative scenario 範圍。（Phase 2.5 assumption check
發現,對應 #18/#22 的 Demote to unit test 判決。）

---

## Feature: Title-Case Text Fallback Detection Path

### Context

當 markdown H3、H4 兩路對某個 Item 都拿不到可信結果時,系統降級到用「看起來像 Title-Case
heading 的獨立行」偵測 heading。這不是邊角備援——72-probe 研究驗證中,8/63 個 Item 完全靠
這條路徑才有結構(MSFT FY2026 全部 4 個 Item 皆是)。Fallback 結果套用與 markdown 路徑相同的
plausibility 與 prelude validity 關卡,任何情況下都不能有文字被靜默丟棄(zero content loss)。

### Rule: 候選 heading 行的 rejection 規則

一行文字只要符合 7 條 rejection 條件中的任一條,就不能成為 fallback heading 候選:長度窗、
digit cluster、Item 自引、上下文訊號(AND 條件)、特殊字元、結尾標點、footnote 標籤形狀。

#### S-fallback-01: 候選行需通過全部 7 條 rejection 規則,含精確邊界值

> 驗證每一條 rejection 規則各自的判斷邊界,包含 design.md 明文寫出的數值門檻(5、120、80 chars)

- **Given** Item 文字中一行候選行,屬性為 `<屬性>`
- **When** fallback 偵測鏈掃描這一行
- **Then** 該行 `<結果>`

| 屬性 | 結果 |
|---|---|
| 長度恰為 5 chars(下限) | 通過長度檢查(仍須通過其餘規則) |
| 長度恰為 4 chars | 拒絕(長度不足) |
| 長度恰為 120 chars(上限) | 通過長度檢查 |
| 長度恰為 121 chars | 拒絕(超出上限) |
| 內容為 "Fiscal Year 2026 Highlights"(含連續 4 碼數字) | 拒絕(digit cluster) |
| 內容為 "Item 1A"(Item 自己的標題) | 拒絕(自引;文字仍完整保留在輸出中,見 S-fallback-05) |
| 內容為 "(1)ppt"(財報表格 footnote 標記形狀) | 拒絕(footnote 標籤) |
| 內容為 "Revenue Growth %"(含 `%`) | 拒絕(特殊字元) |
| 內容為 "Key Risks:"(以 `:` 結尾) | 拒絕(結尾標點) |
| 前一行以句號結尾,下一行為 95 chars 的內文段落 | 拒絕(上一行是句尾標點結尾) |
| 前一行非句尾標點結尾,下一行恰為 80 chars | 拒絕(下一行未達 long prose 門檻) |
| 前一行非句尾標點結尾,下一行恰為 81 chars | 通過上下文檢查 |

Category: Illustrative (table-driven)
Origin: Multiple(PO 提出 Rule 1 完整規則的代表案例,Dev/QA 補上精確邊界值)

#### S-fallback-02: 候選行前後鄰接空白行或短行時的上下文判定

> 驗證 condition 4(上下文訊號)在真實排版(標題前後夾空白行,10-K 常見樣式)下正確運作,不會
> 被相鄰的空白行或短非內文行拖累合法候選的判定

- **Given** 候選行前後的排版是 `<排版形狀>`
- **When** fallback 判斷此行的上下文訊號
- **Then** 此行 `<結果>`

| 排版形狀 | 結果 |
|---|---|
| 前一行是空白行,空白行之前的段落以句號結尾(標題前後皆夾空行,標準排版) | 通過(空白行本身不算「句尾標點結尾」) |
| 前一行直接是內文句子、以句號結尾,兩者之間沒有空白行分隔 | 拒絕(上一行是句尾標點結尾) |
| 下一行是空白行,再往下第一個非空白行是 96 chars 的內文段落 | 通過(正確跳過空白行找到內文) |
| 下一行是含 `$` 符號的 42 chars 簡短財報註解(本身會被特殊字元規則拒絕),再往下才是長內文段落 | 拒絕(緊鄰的下一行不足 80 chars,即使它自己也會被別的規則擋下) |

Category: Illustrative (table-driven)
Origin: Multiple(Dev 發現空白行方向性誤拒風險,QA 發現鏡像的誤放風險與短鄰居行耦合風險)

#### S-fallback-03: Item 自引比對的格式容忍度

> 驗證 condition 3(Item 自引)能正確辨識格式有落差的自引行,同時不會誤傷語意上不是自引、只是
> 恰好與 Item 編號共享前綴的候選行

- **Given** Item 文字中出現一行 `<候選行內容>`
- **When** fallback 判斷此行是否為 Item 自引
- **Then** 此行 `<結果>`

| 候選行內容 | 結果 |
|---|---|
| "ITEM 1A—RISK FACTORS"(全大寫、em dash,格式與 canonical 的句點分隔不同) | 拒絕(視為自引) |
| "Item 1A Compliance Program"(與 Item 編號開頭相同,但語意上是獨立小節標題,不是自引) | 通過(不因編號前綴相同而被誤判) |
| "Item 1A"(因分頁殘留在 Item 文字中重複出現兩次) | 兩次出現都拒絕 |

Category: Illustrative (table-driven)
Origin: Multiple(Dev 發現格式容忍度的 false negative 風險,QA 發現鏡像的 false positive 風險)

#### S-fallback-04: 攤平表格殘留行不應被誤判為候選標題

> 驗證來自攤平表格的短數字序列殘留,即使不含連續 3 碼數字、不含特殊字元,仍不應被當成候選
> 標題——這跟 Known Limitation #4(表格內容進 chunk 後語意較弱)是不同階段的問題:這裡是
> 偵測階段的誤判風險,不是已裁決的限制

- **Given** Item 文字中有一行攤平表格殘留,內容為 `<內容>`
- **When** fallback 掃描這一行
- **Then** 此行 `<結果>`

| 內容 | 結果 |
|---|---|
| "Approximately 1,000 Employees Worldwide"(千分位逗號數字) | 拒絕(逗號後的 "000" 滿足連續 3 碼數字) |
| "12  34  56  78"(空白分隔、每段僅 2 碼的短數字序列) | 拒絕(不應被誤判為候選標題,即使不含連續 3 碼數字) |

Category: Illustrative (table-driven)
Origin: Multiple(QA 發現主要案例,Dev 補充千分位變體)

---

### Rule: Assembly 是逐字重現(不做 prelude carve-out)

Fallback 的 prelude/blocks 組裝沿用與 markdown 路徑相同的邏輯——不管一行文字因為哪一條
rejection 規則被拒絕,它的文字內容都不會從 assembled 輸出中被排除。

#### S-fallback-05: 因任一規則被拒絕的候選行,文字仍完整保留在輸出中

> 驗證逐字重現原則涵蓋全部 7 條 rejection 規則(不只自引一種),且特殊字元不會在組裝過程中被
> 意外轉義或清洗掉

- **Given** Item 文字中有一行因 `<拒絕理由>` 被判定拒絕,內容為 `<內容>`
- **When** fallback 組裝 prelude 與 blocks
- **Then** 這一行的文字 `<結果>`

| 拒絕理由 | 內容 | 結果 |
|---|---|---|
| Item 自引 | "Item 1A" | 完整保留在 prelude 或所屬 block 的內容中 |
| 特殊字元(以 `\|` 為代表——同時是 markdown 表格語法字元,風險高於 `$`/`%`) | "Revenue \| $1,234 \| $1,100" | 完整保留,`\|` 字元本身不被轉義或移除 |
| 長度不足 | "Tax" | 完整保留 |

Category: Illustrative (table-driven)
Origin: Multiple(PO 以 design.md「任何情況下都零 content loss」的無條件敘述解出範圍,QA 提出
特殊字元清洗風險,Dev 指出 `\|` 因架構重疊風險最高)

---

### Rule: Fallback 結果要通過與 markdown 路徑相同的關卡

Fallback 找到候選標題後,結果要通過與 markdown 路徑完全相同的 plausibility check(候選數 ≥2
且第一個候選位置在 Item 文字前 30% 內)與 prelude validity threshold(≤3,000 chars)。

#### S-fallback-06: Plausibility 是兩個獨立子條件的 AND,任一失敗都不可信

> 驗證「候選數 ≥2」與「第一個候選位置在前 30%」是兩個各自能單獨導致不可信的條件——WMT/DIS
> Item 7A 這類「僅 1 個 anchor」的案例只測到候選數不足這一個分支,候選數足夠、但位置超出前
> 30% 的分支需要獨立驗證

- **Given** fallback 在 Item 文字中找到候選標題,情況為 `<候選狀況>`
- **When** 系統評估 plausibility
- **Then** 系統判定 `<結果>`

| 候選狀況 | 結果 |
|---|---|
| 找到 3 個候選,但第一個候選落在 Item 文字 45% 的位置(候選數足夠,位置超出前 30%) | 不可信 |
| WMT Item 7A:markdown 僅 1 個淺層 anchor(候選數不足)→ 不可信 → 降級到 fallback → fallback 找到 ≥2 個候選且第一個落在前 30% 內 | 可信,產出 StructuredItem,`detection_source = "text_fallback"` |

[POST-CODING: 「45% 位置」目前是合成案例;優先確認 72-probe 原始 fixture 資料裡有無現成、
貼近 30% 邊界的真實案例可直接取用]

Category: Illustrative (table-driven)
Origin: Multiple(PO 對 WMT/DIS「淺層/深層」用詞提出原始 Question,QA 指出這其實只測了 count
子條件,Dev 的 anchor-offset 疑慮收斂進同一個代表案例)

#### S-fallback-07: Anchor 數與 prelude 長度的精確邊界

> 驗證 plausibility 與 prelude validity 兩個門檻在剛好卡在邊界值時的行為(通過側與拒絕側各一)

- **Given** `<情境>`
- **When** 系統評估對應門檻
- **Then** `<結果>`

| 情境 | 結果 |
|---|---|
| 候選數恰好為 2,且都落在前 30% 內 | 可信(達到最低通過門檻) |
| 第一個候選前的文字恰好為 3,000 chars | 視為有效 prelude,整段附加,不截斷 |
| 第一個候選前的文字恰好為 3,001 chars | 不算 prelude,重新分類為無標題 leading block |

[POST-CODING: 優先確認 Known Limitation #1(DIS Item 7)的真實 prelude 長度是否已貼近
3,000 chars——若貼近,直接用這個具名真實案例取代合成的 3,000/3,001 邊界值]

Category: Illustrative (table-driven)
Origin: QA(對 design.md 明文數值門檻的邊界值分析)

---

### Rule: Fallback 不會搶在可信的 markdown 結果之前

偵測鏈依序嘗試 markdown H3 → H4 → text fallback,在第一個產出可信結果的路徑就停止。

#### S-fallback-08: 偵測鏈依序嘗試,第一個可信路徑即停止

> 驗證 H3→H4→fallback 三段式 fallthrough 的每一段停止條件,不只是「markdown(不分哪路)vs
> fallback」的二分——並且非 MSFT 案例也要有精確的 block 數斷言,不能只斷言「產出某個
> StructuredItem」

- **Given** 某 Item 的 markdown 偵測狀況為 `<狀況>`
- **When** 偵測鏈依序執行
- **Then** 產出 `<結果>`,`detection_source = <值>`,blocks 數為 `<block 數>`

| item | 狀況 | 結果 | detection_source | block 數 |
|---|---|---|---|---|
| WMT Item 1 | H3 直接找到 ≥2 個可信 anchor | StructuredItem,H4 與 fallback 皆不執行 | markdown_h3 | [POST-CODING] |
| WMT Item 1A | H3 不可信,H4 找到 ≥2 個可信 anchor | StructuredItem,fallback 不執行 | markdown_h4 | [POST-CODING] |
| WMT Item 7A | H3、H4 皆不可信(僅 1 個淺層 anchor)→ fallback 接手且通過 plausibility | StructuredItem | text_fallback | [POST-CODING] |
| DIS Item 7A | H3、H4 皆不可信(僅 1 個深層 anchor)→ fallback 接手且通過 plausibility | StructuredItem | text_fallback | [POST-CODING] |
| MSFT Item 1 / 1A / 7 / 7A | H3、H4 皆對此 filing 全面劣化/不可信(承重牆案例) | StructuredItem | text_fallback | 27 / 14 / 38 / 5(Item 7 原始 72-probe 數字為 41,review round 1 的 footnote-label 規則修正為 38) |

Category: Illustrative (table-driven)
Origin: Multiple(PO 對 H3/H4 未區分提出原始 Question,Dev 指出三段式 fallthrough 的中間分支
未被驗證,QA 指出非 MSFT 案例的斷言強度不足)

---

### Rule: Zero Content Loss(貫穿全部路徑的不變量)

無論 Item 最終走哪一條路徑、產出 StructuredItem 還是 FlatItem,原始 Item 文字的每一個
非空白字元都必須被保留。驗證標準(取代原本偏弱的長度總和比對):把輸出攤平成一個 segment
序列,每個 segment 依序在原始文字中都要找得到,segment 之間(以及最前/最後)容許的落差只能
是純空白字元,不能是任何實際文字內容。此標準已涵蓋現行「prelude/blocks 頭尾空白正規化允許、
FlatItem 不額外正規化」的實作行為——這是使用者在檢視實際程式碼與 fixture 資料後確認的既有
行為,不是待決的設計問題。

#### S-fallback-09: StructuredItem 的 prelude 與 blocks 依序重建原始 Item 文字

> 驗證這是整個 fallback feature 存在的核心保證——切錯位置可以接受,遺失文字不行

- **Given** `<Item 案例>` 經偵測鏈產出 StructuredItem
- **When** 依序比對 prelude、每個 block 的 heading 與 text 在原始 Item 文字中的位置
- **Then** 每個 segment 都依序找得到,segment 之間的落差只能是空白字元

| Item 案例 | 備註 |
|---|---|
| MSFT FY2026 Item 1A(經 text_fallback,14 blocks) | 一般案例,含 Item 自引行(見 S-fallback-05) |
| DIS Item 7(Known Limitation #1:短 prelude 實際上是本文內容,被誤判附加) | 驗證範圍收在「這段文字確實逐字出現在 prelude 欄位裡」,不延伸到下游 LLM 可見性(Out of Scope) |

Category: Illustrative (table-driven)
Origin: Multiple(PO 提出核心案例,Dev 定義了取代長度總和比對的驗證方法,QA 錨定 DIS Item 7
這個已知限制的具名案例)

#### S-fallback-10: FlatItem 的內容忠實重建原始 Item 文字

> 驗證三路偵測皆不可信、Item 維持 FlatItem 時,zero content loss 保證同樣成立——這是目前
> 驗證計畫裡唯一專屬於 FlatItem 的內容保真度案例(現行測試對 StructuredItem 的 prelude/blocks
> 有專門的驗證機制,FlatItem 目前沒有對應機制,屬於驗證缺口而非設計問題)

- **Given** GE FY2025 Item 1A(61,747 chars,三路偵測皆不可信)
- **When** 偵測鏈判定該 Item 維持 FlatItem
- **Then** FlatItem 的文字內容與原始 Item 文字比對,落差只能是頭尾空白字元,不能有任何內容遺失

Category: Illustrative
Origin: Multiple(Dev 最早提出 FlatItem 組裝可能改變格式的疑慮,QA 併入同一個「空白算不算
內容」缺口,PO 在最終定案時標記為 formulation 階段需要補上的驗證缺口)

---

### Journey Scenarios

#### J-fallback-01: 兩條 markdown 路徑降級後,fallback 完整跑完整條鏈路產出 StructuredItem

> 證明「markdown 不可信 → fallback 接手 → 通過 plausibility → 通過 prelude validity →
> 組裝」這條完整降級路徑真的串得起來,不是每條規則分別驗證卻沒證明串起來能動

- **Given** WMT Item 7A 的原始文字(markdown anchor 存在但只有 1 個,不可信)
- **When** 偵測鏈依序嘗試 markdown H3、H4(皆不可信),然後 text fallback
- **Then** fallback 找到候選標題、通過 plausibility check、通過 prelude validity threshold,
  最終產出 StructuredItem(`detection_source = "text_fallback"`),且 prelude/blocks 零
  內容遺失

Category: Journey
Origin: Multiple

#### J-fallback-02: 三路偵測全數不可信,Item 優雅降級為 FlatItem 且零內容遺失

> 證明「三路都失敗」這個最終退路的完整鏈路——三路依序都跑過且都不可信,最終合理地整段保留
> 原文,不捏造假結構、不遺失任何內容

- **Given** GE FY2025 Item 1A 的原始文字(61,747 chars)
- **When** 偵測鏈依序嘗試 markdown H3、H4、text fallback,三路皆不可信
- **Then** 該 Item 維持 FlatItem,原始文字零遺失地保留在 `text` 欄位中,不拋出錯誤、不產生
  部分結果

Category: Journey
Origin: Multiple

---

## 明確不驗證的項目(Demote to unit test / 已裁決不測)

以下項目在 Three Amigos 討論中被提出,但判定不適合寫成本文件的 declarative scenario:

- **GE Item 1A 究竟命中 Rule 1「零候選」還是 Rule 3「plausibility 擋下」**(以及 H3/H4 各自
  為何不可信):`ParsedFiling` schema 不記錄降級原因,黑箱不可觀察,需要 unit test 層級斷言
  內部候選清單。
- **Item 自引比對用單次字串查找還是逐行掃描實作**:純實作策略選擇,只要 observable outcome
  一致,黑箱測不出差異。
- **候選行是否為 Title-Case(字首大寫)**:程式碼的 7 條 rejection 規則實際上沒有任何一條
  檢查大小寫格式;「Title-Case」只是描述典型輸入樣態,不是被驗證的規則。使用者已確認這屬於
  design-envelope §5「everything else」層級的規則調參細節,不需要專門的 scenario 記錄這個
  寬鬆行為。
