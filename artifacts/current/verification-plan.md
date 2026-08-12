# Verification Plan

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Generated: 2026-08-12
- 本 feature 沒有 UI(純 backend 文字處理 pipeline),全部驗證方法皆為 Deterministic(script);
  無 Browser Automation 章節。

## 驗證方式說明

偵測鏈是一組純函式(輸入 Item 文字 + markdown heading candidates,輸出結構化結果),不是走
HTTP 的服務端點,所以驗證步驟採「直接呼叫函式 + 斷言回傳結構」的 script 形式,不是 curl。
遵循 `sec_text_pipeline` 既有測試慣例(module docstring 明講的「External behavior only」):
一律透過偵測鏈的**公開介面**呼叫並斷言回傳結構,不呼叫任何底線開頭的內部 helper——候選行是否
被接受,一律用「它有沒有出現在最終回傳的某個 block heading 裡」來觀察,不直接呼叫內部的候選
篩選函式。

真實 ticker 案例(MSFT/GE/WMT/DIS)一律從既有的錄製 fixture 讀取,不現場打 EDGAR。合成/邊界
值案例用最小的手工建構文字,避免每個案例都要準備一份完整假 filing。

---

## Automated Verification — Deterministic

### S-fallback-01:候選行需通過全部 7 條 rejection 規則,含精確邊界值

- **Method**: script
- **Steps**:
  1. 對表格中每一列候選行文字 `<候選內容>`,建構一段合成 Item 文字:兩個已知合法的 fallback
     heading(如 "Overview" / "Competition",各自前後有空行、內容足夠長)夾住待測的候選行,
     確保整體有 ≥2 個明確候選、滿足 plausibility,不會因為只測一行而讓整個結果變成 `None`。
  2. 呼叫偵測鏈的公開介面,傳入這段合成文字與空的 markdown candidates(強制走 fallback 路)。
  3. 檢查回傳結果的 blocks 標題列表。
  4. 斷言:若該列預期「通過」,候選行文字應該出現為某個 block 的 `heading`;若預期「拒絕」,
     候選行文字不應出現為任何 block 的 `heading`(而是被併入前一個 block 的 `text` 內容裡)。
- **Expected**: 每一列的通過/拒絕結果與 S-fallback-01 表格一致,尤其是邊界值列(5 vs 4 chars、
  120 vs 121 chars、80 vs 81 chars)——這兩側都要各自驗證,不能只測其中一側。

### S-fallback-02:候選行前後鄰接空白行或短行時的上下文判定

- **Method**: script
- **Steps**:
  1. 建構 4 段合成 Item 文字,分別對應表格 4 種排版形狀(標題前後皆夾空行 / 無空行直接鄰接
     句尾內文 / 下一行是空行再接長內文 / 下一行是含 `$` 的短財報註解再接長內文),候選行本身
     固定用同一個已知合格的標題文字(避免候選行自身屬性成為變因)。
  2. 每段文字都用另一個明確合格的第二個 heading(如 "Overview")滿足 plausibility 的候選數
     門檻。
  3. 呼叫偵測鏈公開介面,檢查候選行是否出現在回傳 blocks 的 heading 列表中。
- **Expected**: 通過/拒絕結果與 S-fallback-02 表格一致——尤其「空白行不算句尾標點結尾」與
  「下一行需跳過空白/短行找到真正內文」兩點要分別驗證到。

### S-fallback-03:Item 自引比對的格式容忍度

- **Method**: script
- **Steps**:
  1. 對表格 3 種候選行(全大寫格式自引 / 同編號開頭但非自引 / 自引行重複出現兩次),各自建構
     一段合成 Item 文字,並在偵測鏈呼叫時明確傳入該文字所屬的 Item key(例如 `"1a"`),讓
     「Item 自己的編號是什麼」有明確依據。
  2. 呼叫偵測鏈公開介面,檢查候選行(含重複出現的兩次)是否成為 block heading。
- **Expected**:格式不同的自引行仍被拒絕、非自引的同編號開頭候選被接受、重複出現的自引行
  兩次都被拒絕但文字仍完整出現在輸出中(交叉驗證 S-fallback-05)。

### S-fallback-04:攤平表格殘留行不應被誤判為候選標題

- **Method**: script
- **Steps**:
  1. 對錶格 2 種數字殘留樣式,各自建構合成 Item 文字(候選殘留行 + 兩個明確合格的 heading
     滿足 plausibility)。
  2. 呼叫偵測鏈公開介面,檢查殘留行是否成為 block heading。
- **Expected**: 兩種殘留樣式都不應出現為 block heading。**若 "12  34  56  78" 這個空白分隔
  短數字序列的案例實測結果是「被接受」,這是一個需要回報的發現,不要把測試改成配合現況通過**
  ——這個 scenario 的存在目的就是檢查現行 7 條規則組合是否真的擋得住這類殘留,不是預先假設
  答案。

### S-fallback-05:因任一規則被拒絕的候選行,文字仍完整保留在輸出中

- **Method**: script
- **Steps**:
  1. 建構一段合成 Item 文字,依序包含:(a) 一行 Item 自引標題、(b) 一行含 `\|` 字元的候選
     (如 "Revenue \| $1,234 \| $1,100")、(c) 一行過短候選("Tax"),中間穿插兩個明確合格
     的 heading("Overview"、"Competition")滿足 plausibility。
  2. 呼叫偵測鏈公開介面。
  3. 把回傳的 `prelude` 與全部 `blocks`(依序,heading + text)串接,依序在原始合成文字中
     做子字串比對(見 S-fallback-09 的統一比對邏輯,此處共用)。
- **Expected**: 三行被拒絕的候選文字,逐字(含 `\|` 字元本身)出現在串接後的輸出中;比對過程
  中的落差只能是空白字元。

### S-fallback-06:Plausibility 是兩個獨立子條件的 AND

- **Method**: script
- **Steps**:
  1. 「count 通過、position 失敗」案例:已查過 `fixtures_detection_probes.json` 涵蓋的
     CAT/WMT/JPM/DIS/MSFT/GE 六檔 ticker 全部既有 acceptance 案例(見 `test_detection_probes.py`
     的 `TestFlagshipTruePreludes`/`TestPseudoPreludeReclassification`/`TestNoPreludeMultiBlock`/
     `TestTextFallbackPath`/`TestKnownLimitations`),沒有任何一個案例是「候選數 ≥2 但第一個
     候選超出前 30%」——現有 recorded fixture 不包含這個分支,只能用合成文字構造:前 45% 塞入
     大量無候選特徵的填充內文,45% 之後放 ≥3 個明確合格的候選(可參考 `test_block_detection.py`
     的 `test_single_deep_heading_is_implausible` / `test_plausibility_gate_applies_to_fallback`
     的合成手法)。
  2. WMT Item 7A 案例:從 fixture 讀取 WMT Item 7A 原始文字與其 markdown candidates(僅 1 個
     淺層 anchor)。
  3. 分別呼叫偵測鏈公開介面。
- **Expected**: 案例 1 回傳 `None`(或該 Item 最終序列判定為 FlatItem,依實際 API 形狀而定);
  案例 2(WMT Item 7A)回傳 StructuredItem,`detection_source == "text_fallback"`。

### S-fallback-07:Anchor 數與 prelude 長度的精確邊界

- **Method**: script
- **Steps**:
  1. `anchor 數邊界`:建構一段合成文字,恰好 2 個候選、都落在前 30% 內,呼叫偵測鏈,斷言
     回傳非 `None`。
  2. `prelude 長度邊界`:已查得 Known Limitation #1(DIS Item 7)真實 prelude 長度為
     **2,610 chars**(`test_dis_7_false_valid_prelude_current_behavior` 斷言
     `2500 <= len(prelude) <= 3000`,docstring 明講精確數字)——離 3,000 邊界還有 390 chars,
     不夠貼近,不能取代精確邊界案例。維持合成兩段文字(prelude 前綴分別恰為 3,000 / 3,001
     chars),各自呼叫偵測鏈,斷言 `prelude` 欄位是否非空、`blocks[0].heading` 是否為空字串
     (重新分類案例)。DIS Item 7 的 2,610 chars 可作為「有效 prelude 但非邊界本身」的補充
     真實案例,與合成的精確邊界案例互補。
- **Expected**: 2 個候選、皆在前 30% → 可信;3,000 chars → `prelude` 為該段文字(非空、不
  截斷);3,001 chars → `prelude == ""`,`blocks[0].heading == ""` 且 `blocks[0].text` 含
  該段文字。

### S-fallback-08:偵測鏈依序嘗試,第一個可信路徑即停止

- **Method**: script
- **Steps**:
  1. 從 fixture 讀取 CAT Item 7(H3 直接成功代表案例)、WMT Item 1A(H4 案例)、WMT Item 7A、
     DIS Item 7A 的原始文字與各自的 markdown candidates。
  2. 對每個案例呼叫偵測鏈公開介面。
  3. 斷言回傳結果的 `detection_source` 與 blocks 數。
  4. 對 MSFT FY2026 全部 4 個 Item(1/1A/7/7A),同樣從 fixture 讀取並呼叫,斷言
     `detection_source == "text_fallback"` 且 blocks 數精確為 27/14/38/5(Item 7 原始
     72-probe 數字是 41,review round 1 的 footnote-label 規則修正為 38)。
- **Expected**(已從既有 `test_detection_probes.py` 驗證過的真實案例回填,不再是 [POST-CODING]):
  CAT Item 7 → `markdown_h3`,前兩個 block heading 為 "OVERVIEW"、"CONSOLIDATED SALES AND
  REVENUES";WMT Item 1A → `markdown_h4`,blocks 為 "Strategic Risks"、"Operational Risks";
  WMT Item 7A → `text_fallback`,5 blocks;DIS Item 7A → `text_fallback`,2 blocks;MSFT
  四個 Item → `text_fallback`,blocks 數精確吻合 27/14/38/5。

### S-fallback-09:StructuredItem 的 prelude 與 blocks 依序重建原始 Item 文字

- **Method**: script
- **Steps**:
  1. 從 fixture 讀取 MSFT FY2026 Item 1A 原始文字,呼叫偵測鏈公開介面取得 StructuredItem。
  2. 把 `prelude`(若非空)、每個 block 的 `heading`、每個 block 的 `text`,依序組成一個
     segment 序列。
  3. 從原始文字的位置 0 開始,依序對每個 segment 做 `str.find(segment, pos)`,每次都要求
     `find` 結果 `!= -1` 且 `>= pos`;取得結果後,檢查「前一個 segment 結束位置」到「這次
     find 到的起始位置」之間的字串,呼叫 `.strip()` 後必須是空字串。
  4. 對 DIS Item 7 重複同樣流程。
- **Expected**: 全部 segment 依序找得到,任何一段落差經 `.strip()` 後都是空字串;DIS Item 7
  的 prelude 也通過同樣檢查(驗證範圍就停在這裡,不再往下游檢索/citation 延伸)。

### S-fallback-10:FlatItem 的內容忠實重建原始 Item 文字

- **Method**: script
- **Steps**:
  1. 從 fixture 讀取 GE FY2025 Item 1A 原始文字(61,747 chars),呼叫偵測鏈公開介面,斷言
     回傳為表示「未偵測到結構」的結果(FlatItem 分支)。
  2. 取得 FlatItem 的 `text` 欄位,與原始輸入文字整體比對:去除兩者頭尾空白後是否相等
     (`text.strip() == original.strip()`),或至少「原始文字扣掉頭尾空白後,是 `text` 的
     子字串,且 `text` 沒有比原始文字多出任何非空白字元」。
- **Expected**: 61,747 chars 的內容完整保留,只有頭尾空白的差異被允許,中間任何位置都不能有
  非空白字元的落差。

---

## Automated Verification — Journey Scenarios (Deterministic)

### J-fallback-01:兩條 markdown 路徑降級後,fallback 完整跑完整條鏈路產出 StructuredItem

- **Method**: script
- **Steps**:
  1. 從 fixture 讀取 WMT Item 7A 原始文字與其 markdown candidates(僅 1 個淺層 anchor)。
  2. 呼叫偵測鏈公開介面(這一次呼叫內部會依序嘗試 H3 → H4 → fallback,不用分開呼叫三次)。
  3. 斷言回傳為 StructuredItem,`detection_source == "text_fallback"`。
  4. 對回傳的 `prelude`/`blocks` 執行與 S-fallback-09 相同的 segment 重建比對。
- **Expected**: 單一次呼叫的回傳結果同時滿足「detection_source 正確」與「zero content loss」
  兩個斷言——證明鏈路(降級 + plausibility + prelude validity + 組裝)是串起來一起動的,不是
  分開驗證卻沒證明能串接。

### J-fallback-02:三路偵測全數不可信,Item 優雅降級為 FlatItem 且零內容遺失

- **Method**: script
- **Steps**:
  1. 從 fixture 讀取 GE FY2025 Item 1A 原始文字與其 markdown candidates。
  2. 呼叫偵測鏈公開介面,斷言回傳結果為「未偵測到結構」。
  3. 呼叫上層的 filing 層級 parse 介面(而非只呼叫偵測鏈本身),確認這個 Item 在最終
     `ParsedFiling.items` 裡是以 FlatItem 形狀出現,且沒有拋出例外、沒有整個 filing parse
     失敗。
  4. 對 FlatItem 的 `text` 執行與 S-fallback-10 相同的內容比對。
- **Expected**: 沒有例外、沒有部分結果;FlatItem 內容完整;這證明「三路都失敗」是一個被
  正常處理的合法終點,不是意外路徑。

---

## Manual Verification

### Manual Behavior Test

> 本 feature 是純 backend 文字處理 pipeline,所有案例都能用錄製 fixture 資料自動化驗證,
> 不需要實體裝置、不涉及高併發情境。**無**需要人工介入才能完成的驗證項目。

### User Acceptance Test

> User 從 operator 角度驗證偵測結果是否「看起來合理」——這類判斷仰賴人眼比對 SEC 原文,無法
> 用斷言表達。依 DEV-127 parent spec,`inspect` view / CLI 是這類抽查的標準視圖。

#### UAT-01: MSFT 承重牆案例的 block 切分人工抽查

- **Acceptance Question**: MSFT FY2026 的 4 個 Item(1/1A/7/7A)透過 `inspect` 視圖看起來,
  block 邊界是否落在合理的段落分界上,而不是把一段完整論述切成語意不通的兩半?
- **Steps**:
  1. `inspect` CLI 尚未實作(獨立票 DEV-134「Inspect view + CLI」,不在 DEV-136 範圍內;
     repo 內確認過 `sec_text_pipeline/` 目前沒有任何 CLI 進入點)。此 UAT 項目**阻塞於
     DEV-134**,目前無法執行,先保留在報告的待辦清單中。
  2. 對照 SEC EDGAR 原始 10-K 全文(MSFT FY2026),抽查 Item 1A 的 14 個 block 邊界。
  3. 確認每個 block heading 是否對應原文裡真的有語意獨立性的小節,而不是誤切的表格殘留或
     其他雜訊行。
- **Expected**: Block 邊界在人工比對下是合理的、可理解的小節劃分;沒有明顯把單一論述硬切成
  兩個 block 的情況。

#### UAT-02: GE 大型 FlatItem 的降級行為人工確認

- **Acceptance Question**: GE FY2025 Item 1A(61,747 chars)在 `inspect` 視圖裡呈現為完整、
  未截斷的單一區塊,而不是看起來像出錯或被截斷的殘缺內容?
- **Steps**:
  1. 對 GE FY2025 執行 inspect,檢視 Item 1A。
  2. 確認顯示的文字長度與內容是否與 SEC EDGAR 原文的 Item 1A 完整對應。
- **Expected**: 呈現完整、可讀的整段文字,operator 能一眼看出「這是合理的降級結果」而不是
  「這裡東西不見了」。

---

## 待補事項(POST-CODING 總表 — bdd-e2e-loop Step 0 執行後更新)

- ~~S-fallback-06~~:已查證 recorded fixture 沒有「count 通過、position 失敗」的真實案例,
  維持用合成文字驗證(見 verification 步驟)。
- ~~S-fallback-07~~:已查得 DIS Item 7 真實 prelude 為 2,610 chars,離 3,000 邊界不夠近,
  維持合成的精確邊界案例,DIS Item 7 作為補充案例。
- ~~S-fallback-08~~:已從 `test_detection_probes.py` 回填全部真實 block 數與 detection_source
  (CAT 7/WMT 1A/WMT 7A/DIS 7A/MSFT 全部四項)。
- **UAT-01**:阻塞於 DEV-134(inspect CLI 尚未實作),無法執行,列入報告待辦清單。
