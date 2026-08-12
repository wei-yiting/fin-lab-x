# DEV-136 bdd-e2e-loop — Round 1 Failures 裁決紀錄

> 對應文件:`round1-failures-for-review.md`(Round 1 的兩個 FAIL)
> 裁決者:user(2026-08-12,經 orchestrator 分析後逐案討論定案)
> 落地 commit:見 branch `feat/text-fallback-detection` HEAD(本文件與 code 變更同一 commit)

## 裁決總表

| Failure | Scenario | 裁決 | Code 變更 | Scenario 端需要的動作(接手者執行) |
|---|---|---|---|---|
| F1 — Item 自引前綴匹配 | S-fallback-03 row 2 | **不修 code — scenario 預期值修訂 + 記 known limitation** | 無(僅新增 current-behavior pin 測試) | 把該 row 的預期從「通過」改為「被拒絕(fail-safe 方向,見下方理由)」;在 scenario 註記引用本文件 |
| F2 — 空白分隔短數字序列 | S-fallback-04 | **修 code — 已修** | `_FALLBACK_DIGITS_ONLY_RE = ^[\d\s]+$` rejection 已加入 | 無需改 scenario(原預期「拒絕」現在即為實際行為);重跑該 scenario 應 PASS |

兩案皆已有 unit test 釘住(見下),重跑 Round 2 前請先確認你的驗證程式碼與
`test_block_detection.py` 無重複斷言衝突。

---

## F1 — 為什麼不修 code(詳細理由)

**裁決:維持前綴匹配(`^item\s+\d+[a-c]?\.?` 無 `$` 錨定),S-fallback-03 row 2 的
scenario 預期值修訂為「被拒絕」。**

### 理由 1:Scenario 期待的「完整標題比對」在此架構下不可實作,且照做會破壞規則的核心目的

真實 10-K 的 Item 自引行的實際形狀是 **`Item 1A. Risk Factors`** — 編號後面接著該 Item 的
標題文字。若把 regex 加上 `$` 錨定(只擋「整行恰好是 `Item 1A.`」),則 `Item 1A. Risk
Factors` 這個規則存在的首要目標反而會通過、成為 block anchor — 規則直接失效。

要「語意上」區分:

- `Item 1A. Risk Factors` → 自引,必須擋
- `Item 1A Compliance Program` → 假想的合法小節標題,scenario 希望放行

偵測器必須知道「目前在處理哪個 Item、它的官方標題是什麼」。但 `detect_blocks(item_text,
candidates)` 的介面**刻意不接收 item key**(偵測是 item-agnostic 的純文字分析)。要實作
語意自引比對,需要:改 public API 把 item key 穿透進來 + 對官方標題做模糊比對。為一個
無實證的假想案例做這種介面變更,超出 design envelope 授權。

### 理由 2:現行方向是 fail-safe 的那一邊

本偵測鏈的設計哲學(DEV-133 起確立):**錯過比錯認便宜**。

- 前綴寬鬆比對的失敗模式 = **多擋**:合法標題掉進 prelude 或前一個 block。零內容流失
  (`assert_tiles` 不變量保證),損失僅是一個 block 邊界。
- 收緊比對的失敗模式 = **錯放**:自引行成為 anchor,Item 開頭被吞進錯誤結構,且這會發生在
  **每一個**走 fallback 的 Item 上(自引行幾乎每個 Item 都有)。

兩種風險不對稱,現行實作站在便宜的一邊。QA 在 Three Amigos Round 2 提出的鏡像風險
(放寬比對誤傷前綴巧合的合法行)方向正確,但其代價量級遠小於反向風險。

### 理由 3:零實證

14 檔實錄 filing、150+ 個真實 block heading 中,「以 `Item <編號>` 起頭命名的小節標題」
出現次數為 **0**。`Item 1A Compliance Program` 是合成輸入。依 design envelope §0
evidence gate(與 bullet-prefix 規則在 code review round 1 被駁回同一標準),不為無實證
的假想案例動 code。

### 理由 4(補充):與 72-probe 參考實作一致

此前綴 regex 逐字元等同 research 參考實作(`prelude_probe_v3_full_algo.py` 的
`ITEM_SELF_RE`)。AC 的 MSFT blocks 量級數字正是由含此規則的完整實作產出 — 改動它會使
實作偏離已 ratify 的參考行為。

### 落地物

- **Current-behavior pin**:`test_block_detection.py::TestTextFallback::`
  `test_item_prefixed_title_rejection_pinned_current_behavior` — 釘住「`Item 1A
  Compliance Program` 被拒、落入 prelude」的現行行為,docstring 記載完整理由。行為若漂移
  會大聲失敗。
- **重啟條件**:DEV-138 A/B failure mining 若浮現真實的「Item 前綴合法標題」案例,帶著
  實證回來重議(屆時的修法方向是 API 變更 + 標題比對,不是 `$` 錨定)。

### 附註:你的最小重現有一處與實際行為不符

`round1-failures-for-review.md` 中 F1 的最小重現宣稱輸出 `['Overview']`,但該輸入實際上
會得到 `None`:文字裡只有一個可通過的候選(`Overview`),而 plausibility gate 要求
**至少 2 個 anchor** — 單一 anchor 不可能組成 `DetectedBlocks`。這不影響 failure 本身的
成立(rejection 規則層級的行為你驗對了:該行確實被前綴規則拒絕),但表示這段重現碼未實際
執行或輸出被轉述錯誤。Round 2 時建議修正該重現(例:兩個合法候選 + 一個 Item 前綴行,
或直接對 `_fallback_heading_idxs` 斷言)。

---

## F2 — 修了什麼

**裁決:接受 scenario 的預期為正確,補上實作縫。**

裁決理由(與 F1 對比,為何這個修):

1. **不是新增推測性規則,是補既有裁決的實作漏洞**。「數字行不能當標題」的意圖在已 ratify
   的規則集中已表達三次(`isdigit()`、`\d{3,}` digit-cluster、markdown noise filter 的
   `^\d+$`)。`"12  34  56  78"` 繞過它們純粹是字元層的縫:空白使 `isdigit()` 回 False,
   又把數字切碎到不足 3 碼連續。
2. **結構上零誤殺**:新規則擋「整行僅由數字與空白組成」— 不含任何字母的行定義上不可能是
   section heading,規則不可能命中真標題。
3. **暴露位置已被實證**:「表格最後一行 + 緊接長 prose」正是 code review M-1.1 三個
   `(1)ppt` 實例的位置,只是語料裡尚未出現數字行版本。

### 變更內容

- `block_detection.py`:新增 `_FALLBACK_DIGITS_ONLY_RE = re.compile(r"^[\d\s]+$")`,
  在 digit-cluster 檢查之後套用(帶 S-fallback-04 出處註解)。
- `test_block_detection.py::TestTextFallback::test_digits_and_whitespace_line_rejected`:
  正反例(`"12  34  56  78"` 被拒;同文中 `Company Overview` / `Competition` 照常錨定)。

### 驗證

- **Recorded probes 零 delta**:13 個 (ticker, item) 全數重跑,heading list 與修改前
  byte-identical(MSFT 維持 27/14/38/5;WMT 7A = 5、DIS 7A = 2),且無任何現存 heading
  匹配 `^[\d\s]+$` — 證明規則對現有語料零影響。
- 全套 default suite:**1,049 passed**(net +2);ruff format/check 乾淨。
- S-fallback-04 原 scenario 預期(拒絕)現在即為實際行為 — **scenario 無需修改**,
  Round 2 重跑應轉 PASS。
