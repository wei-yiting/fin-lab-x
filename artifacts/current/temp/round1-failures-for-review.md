# DEV-136 bdd-e2e-loop — Round 1 Failures(待討論,尚未修正)

## 背景

這份文件是 `feat/text-fallback-detection` branch 上 DEV-136(Title-Case text fallback
detection path)的 behavior verification Round 1 結果,只摘錄**失敗的部分**,供另一個
agent/reviewer 接手討論或修正用。

- 完整 12 個 scenario 的驗收依據:[`artifacts/current/bdd-scenarios.md`](../bdd-scenarios.md)
- 每個 scenario 的驗證步驟:[`artifacts/current/verification-plan.md`](../verification-plan.md)
- Round 1 完整結果(含全部 10 個 PASS 的細節):
  [`artifacts/current/temp/bdd-verification-round-1.md`](./bdd-verification-round-1.md)
- 這兩個 scenario 都是透過 **design-only 的 Three Amigos 討論**(PO/Dev/QA 三個角色互相
  challenge,過程中完全沒有讀過 implementation code)推導出來的,不是先看 code 再回頭湊
  test case。這代表兩個 failure 都是**design 意圖與目前 implementation 之間的真實落差**,
  不是 test 寫錯或誤判。

**目前狀態:兩個 failure 都尚未修正,也還沒有人判斷該修 code 還是修 scenario/design——這是
接手者要做的第一個決定,不要預設任一邊是對的。**

**結果總表**:12 個 scenario(10 illustrative table-driven + 2 journey)、共約 34 個獨立案例,
10 個 scenario PASS、2 個 scenario 各自有 1 個 case FAIL、0 個 ERROR。跟既有測試套件
(`test_block_detection.py` 43 個、`test_detection_probes.py` 14 個)交叉執行,兩份既有
測試 100% 綠燈,新增的驗證程式碼沒有造成任何 regression。

程式碼位置:`backend/ingestion/sec_text_pipeline/block_detection.py`(核心偵測邏輯,兩個
failure 的根因都在這個檔案)。

---

## Failure 1 — S-fallback-03:Item 自引比對是前綴匹配,不是完整標題比對

**Scenario 出處**:`bdd-scenarios.md` Rule「候選 heading 行的 rejection 規則」→
S-fallback-03。這條 scenario 的 row 2 源自 QA 在 Three Amigos 討論 Round 2 提出的
「鏡像風險」——Dev 原本只擔心自引比對太嚴格會漏判格式不同的自引行(false negative),QA
反過來指出:如果比對邏輯被放寬到能容忍格式差異,可能會矯枉過正,誤傷「語意上不是自引、只是
恰好與 Item 編號共享前綴」的合法候選行(false positive)。

**失敗的 case**:

| 輸入 | Scenario 預期 | 實際結果 |
|---|---|---|
| `"Item 1A Compliance Program"`(獨立小節標題,語意上不是自引,只是碰巧用 Item 編號起頭)| 通過(可被選為候選 heading)| **被拒絕**(判定為自引,不能當候選)|

**根因**(`block_detection.py:106` 定義,`block_detection.py:138` 使用):

```python
_FALLBACK_ITEM_SELF_RE = re.compile(r"^item\s+\d+[a-c]?\.?", re.IGNORECASE)
...
if _FALLBACK_ITEM_SELF_RE.match(s):
    continue  # 視為自引,拒絕當候選
```

`re.match()` 只從字串開頭比對,沒有 `$` 結尾錨定,所以這條 regex 比對的是「這一行**開頭**是不是
長得像 `Item <數字><字母>`」,而不是「這一行**整體**是不是就是 Item 自己的標題」。任何合法標題
只要碰巧以 `Item <該 Item 編號>` 開頭,都會被這條規則當成自引擋下,不論後面接什麼內容。

**最小重現**:

```python
from backend.ingestion.sec_text_pipeline.block_detection import (
    detect_blocks, HeadingCandidates,
)

text = "\n\n".join([
    "Item 1A Compliance Program",
    "Sufficiently long body prose line for the block. " * 4,
    "Overview",
    "Sufficiently long body prose line for the block. " * 4,
])
d = detect_blocks(text, HeadingCandidates(h3=(), h4=()))
print([b.heading for b in d.blocks] if d else None)
# 實際: ['Overview']  —— "Item 1A Compliance Program" 沒有出現,被吃進 prelude
# Scenario 預期: ['Item 1A Compliance Program', 'Overview']
```

也可以直接對 regex 本身驗證,不需要整條偵測鏈:

```python
import re
r = re.compile(r"^item\s+\d+[a-c]?\.?", re.IGNORECASE)
print(r.match("Item 1A Compliance Program"))  # 有 match,span=(0, 7)
```

**待討論,不要假設答案**:這是否為需要修的 bug,取決於真實 10-K 裡「小節標題直接以
`Item <編號>` 開頭起名字」這個寫法出現的頻率——如果罕見,現行的寬鬆前綴比對影響面很小;如果
不罕見,現行規則會系統性漏掉這類標題。目前沒有證據判斷哪邊更接近真實情況。

---

## Failure 2 — S-fallback-04:空白分隔的短數字序列會繞過全部 digit 相關規則

**Scenario 出處**:`bdd-scenarios.md` Rule「候選 heading 行的 rejection 規則」→
S-fallback-04。源自 QA 在 Three Amigos 討論 Round 1 的觀察:財報表格被「壓扁」成純文字後,
殘留的數字行有可能繞過現行的 digit-cluster 判斷,誤判成候選標題——這跟已裁決接受的
Known Limitation #4(表格內容進 chunk 後、對結構化數字查詢語意較弱)是不同層次的問題:那條
講的是「表格內容已經正確落在某個 block 裡,只是檢索語意弱」;這裡是「表格殘留可能被誤判成一個
全新的假標題」,把本來連續的一段內容硬切成兩塊。

**失敗的 case**:

| 輸入 | Scenario 預期 | 實際結果 |
|---|---|---|
| `"12  34  56  78"`(4 組 2 位數字,空白分隔——攤平表格殘留的典型形狀)| 拒絕(不應被當作候選 heading)| **被接受**(成為候選 heading)|

（對照組:`"Approximately 1,000 Employees Worldwide"`〔千分位逗號數字〕**有**被正確擋下,
因為逗號後的 "000" 仍構成連續 3 碼數字——這個 case scenario 預期與實際一致,PASS。）

**根因**(`block_detection.py:109` 定義,`block_detection.py:136` 使用):

```python
_FALLBACK_DIGIT_CLUSTER_RE = re.compile(r"\d{3,}")
...
if s.isdigit() or _FALLBACK_DIGIT_CLUSTER_RE.search(s):
    continue  # 拒絕
```

兩個判準都繞得過去:
- `"12  34  56  78".isdigit()` → `False`(因為含空白字元,不是純數字行)
- `_FALLBACK_DIGIT_CLUSTER_RE.search("12  34  56  78")` → `None`(每一組數字只有 2 碼,
  被空白隔開,沒有任何一段連續數字達到 3 碼門檻)

**最小重現**:

```python
from backend.ingestion.sec_text_pipeline.block_detection import (
    detect_blocks, HeadingCandidates,
)

text = "\n\n".join([
    "Overview",
    "Sufficiently long body prose line for the block. " * 4,
    "12  34  56  78",
    "Sufficiently long body prose line for the block. " * 4,
    "Competition",
    "Sufficiently long body prose line for the block. " * 4,
])
d = detect_blocks(text, HeadingCandidates(h3=(), h4=()))
print([b.heading for b in d.blocks] if d else None)
# 實際: ['Overview', '12  34  56  78', 'Competition']
# Scenario 預期: ['Overview', 'Competition'](中間那行不該獨立成 block)
```

**待討論,不要假設答案**:這個誤判**不違反 zero-content-loss**(文字沒有不見,只是被錯誤地
切成獨立 block),所以不會被任何既有的 `assert_tiles` 類斷言意外抓到——換句話說,如果選擇不修,
這個 gap 會一直是「沒有任何回歸測試在盯」的狀態。

---

## 給接手 agent 的提醒

- 兩個 failure 都已經確認**不是既有測試套件的 regression**——`test_block_detection.py` /
  `test_detection_probes.py` 在這次驗證前後都是全綠。
- 這次驗證刻意遵守「如實回報,不要為了讓測試過而改測試」的原則(参見
  `verification-plan.md` S-fallback-04 的備註)。如果決定要修,請先跟 user 確認方向(改
  regex 邏輯,還是接受現況、把這兩個 case 記錄成新的 Known Limitation),不要單方面假設
  scenario 的預期值才是對的、直接改 code 去配合。
- 兩個 regex 都在同一個檔案、彼此獨立,理論上可以分開評估、分開決定,不需要綁在一起處理。
