# Issue 2 / Issue 3 Research Findings

研究方法：直接解析 `.artifacts/current/temp/edgar_cache/` 下的 raw HTML，用 BeautifulSoup 模擬 `html_preprocessor._promote_headings`、`sec_heading_promoter.detect_item_regions`、`_has_bold_signal`、`_is_isolated_item_block` 的行為，找出每個 ticker 被錯過或被過度促進的 Item tag。**未執行任何 pytest、未修改任何 production／test code。**

## Group A — Item Detection Failure

### JPM

- **Markup observed**: body Item 都是單獨 `<div>` 包一個 `<span>`，`font-weight:400`（**明確非粗體**），用 `font-family:'Sons',sans-serif` 12pt 搭配 body 10pt 做階層區分。例如：
  `<div style="margin-bottom:6pt"><span style="...font-size:12pt;font-weight:400;...">Item 1. Business.</span></div>`
  全部 22 個 unique Item 都是這個樣子。
- **Why detection fails**: `_has_bold_signal` 回傳 False（沒有 `<b>/<strong>`、沒有 `font-weight:700|bold`）。`_is_isolated_item_block` 也回傳 False ——雖然 12pt ≥ body 10pt，但 Item `<div>` 的 prev sibling 是一個空的 `<div>`（Workiva 常見的 spacer），被 `_BLOCK_SIBLING_NAMES` 判定為「非孤立」。`bold_ok=0, iso_ok=0, both_fail=22`。
- **Suggested fix shape**: `_is_isolated_item_block` 的 sibling 掃描應該忽略「空 sibling」（text stripped == ''），繼續往前／往後找下一個有內容的 sibling。JPM 的 Item 其實就是乾淨的孤立 heading，只是 Workiva 在前面多塞了一個空 div 排版。
- **Estimated complexity**: small

### PG

- **Markup observed**: 23 個 unique Item 的 body 版本也是 `font-weight:400`（非粗體），font-size 10pt 等於 body。heading 的視覺信號是 **title 後半段** `<span style="...text-decoration:underline">Business.</span>`——底線不是粗體。整串 text 因為 `&nbsp;` 會 strip 成 `'Item\xa01.Business.'`。
- **Why detection fails**: `_has_bold_signal=False`。`_is_isolated_item_block` 也 False ——Item `<div>` 的 next sibling 是另一個包含段落文字的 `<div>`（不是 `<p>`），被 `_BLOCK_SIBLING_NAMES` 擋掉。此外即使修掉 sibling 檢查，isolation 還會要求 `tag_font_size ≥ body_font_size`，PG Item 剛好等於 10pt 所以這關可過；真正卡關的只是 sibling 判定。
- **Suggested fix shape**: 同 JPM 的 sibling 修正可以救一半——但 PG 的 next sibling 是「真正的」body 段落 `<div>`，並非空 spacer。更根本的做法是在 `_promote_headings` 的 Item 分支加一個 fallback：當 bold 與 isolation 都失敗，但 `<span>` 子元素帶有 `text-decoration:underline` 且 text matches Item regex，視為 underline-title 變體 heading。或者接受「non-bold Item heading」為 Class C（commit `daee3ab` 已經引入 Class C 概念），把 non-bold Item 寬鬆納入。
- **Estimated complexity**: medium（需要決策要不要承認 underline-title 為新訊號，或把 non-bold items 統一劃入 Class C）

### INTC

- **Markup observed**: 整份 10-K 用 `color:#0068b5`（Intel 藍）+ 9pt Arial + `font-weight:400` 區分 PART/Item heading，與 body `color:#262626` 區分，**完全沒有任何 bold、沒有 font-size 變化**。PART 是 `<div>` 或 `<td>` 包藍色 span；Item 則是 **兩欄結構**：cell 1 `<td>` 是 `"Item 1."`（標籤欄），cell 2 `<td>` 是 `"Business:"`（標題欄），兩個 cell 都在同一個 `<tr>` 裡，外層 `<table>` 的 parent 是 `<div>`。
- **Why detection fails**: 三層都失敗。(1) `_has_bold_signal` 全部 False → PART 促進失效，h1=0。(2) Item text 本身因為是 `<td>`，`_is_isolated_item_block` 直接回傳 False（`tag.name in ('td','th')`）。(3) 就算通過檢查，Item cell 的 text 只有 `'Item 1.'`，沒有標題，需要 cross-cell merge 才能得到 `'Item 1. Business'`。
- **Suggested fix shape**: INTC 只能以 Class C-style fallback 處理：(a) 允許 `color` 當作 heading signal——但 `color` 差異要跟 body 比對才能判斷；成本較高且 ticker-specific。(b) 更務實：在已知 Class C degraded 狀態下，接受 h1=0/h2=0，只依靠 font-size / visual clue 退化到 Class D（不保證），或乾脆把 INTC 標記為 vendor-specific exception。task spec 已經在 line 328 記錄 `INTC 用 color 區分階層`——建議本回合直接承認 INTC 為 CLASS_C_OR_DEGRADED 並放過 gate。
- **Estimated complexity**: large（若要自動處理）／ small（若只是加白名單或調寬 Class C gate）

## Group B — h2 Inflation

**共同根因（所有 4 個 ticker 相同）**：`detect_item_regions` 用 last-occurrence dedup 只影響「哪個 tag 成為 region anchor」，但 `_promote_headings` 的主迴圈另外**從頭再掃一次所有 `_BLOCK_TAGS`**，凡符合 `_ITEM_RE` + bold 的 tag 都會被 rewrite 成 `<h2>`，**dedup 結果並沒有用來 filter 這個迴圈**。結果 TOC 表格裡的 `<td>Item 1.</td>` 與 body 裡的 `<div>Item 1. Business</div>` 都會被促進成 h2，每個 Item 重複兩次。

### CRM

- **h2 sample headings (from discovery JSON)**: `["Item 1.", "Item 1A.", "Item 1B."]`（短形式 = TOC copy）
- **Inflation source**: 每個 item_num 剛好出現 2 次 bold 可促進 block —— 一個在 `<td>` TOC 裡（`Item 1.`），一個在 body 裡（`ITEM 1. BUSINESS`）。24 個 unique item × 2 = **48**，與 discovery JSON 的 h2_count=48 完全吻合。
- **Suggested fix shape**: 在 `_promote_headings` 的 Item 分支加上 `has_table_ancestor(tag)` 過濾；或讓 Item 促進只處理 `detect_item_regions` 回傳的 anchor tag 集合。
- **Estimated complexity**: small

### BAC

- **h2 sample headings (from discovery JSON)**: `["Item 1.", "Item 1A.", "Item 1B."]`
- **Inflation source**: 同 CRM。我模擬到 `bold+no-block-child` 的 Item 共 47 個（22 outside table + 25 inside table）；與 discovery h2_count=45 相差 2，差額應來自 `_BLOCK_SIBLING_NAMES` 判定或 child-block guard 的邊角情況，但 pattern 一致。TOC 表格裡每個 item 被促進一次，body 每個 item 也被促進一次，BAC 甚至有 Item 7／8 在 body 出現 3 次（多一個 sub-anchor）。
- **Suggested fix shape**: 同 CRM。加 `has_table_ancestor` 過濾後模擬得 **22 h2（outside-table only）**，落在合理區間 [18, 30]。
- **Estimated complexity**: small

### BRK.A and BRK.B（同一檔案）

- **確認點**: `BRK_A_*.html` 與 `BRK_B_*.html` 的 md5 完全相同，是 Berkshire 合併申報的同一份 10-K。只要處理 BRK.A 就同時修好 BRK.B。
- **h2 sample headings (from discovery JSON)**: `["Item 1.", "Item 1A.", "Item 1B."]`
- **Inflation source**: 同 CRM／BAC。TOC 版 Item 在 `<p>` 內（parent `<table>`），body 版 Item 在 `<p>` 外（parent `<div>`），兩者都 bold。模擬顯示 outside-table 18 items + inside-table 22 items = 40；discovery 紀錄 39（差 1 可能來自 Item 1C 重複三次中的 child-block guard）。
- **Suggested fix shape**: 同 CRM／BAC；加 table-ancestor 過濾後 outside-table = **18**，剛好對上預期 18 個 Item。
- **Estimated complexity**: small

## Cross-cutting observations

1. **`detect_item_regions` 的 dedup 對 h2 count 是 dead code**：dedup 結果只被 `promote_subsections` 用來切 region，但 `_promote_headings` 的 h2 促進迴圈並沒有讀 `regions`。Group B 就是這個 gap 的直接後果。最根本的修法是：讓 h2 促進迴圈只對 `regions[i].start_tag` 的 id 做促進，其他符合 regex 的 tag 一律跳過；或在 dedup 階段就只保留「非 table-ancestor」候選。

2. **JPM 的 h1 ordering bug 與 Group B 同源**：JPM discovery JSON 的 `h1_first3 = [Part II, Part III, Part I]`——Part II／Part III 都來自 TOC `<table>` 內（`in_table=True`），body 裡只剩 Part I、Part IV。若把 `has_table_ancestor` filter 同時套用在 PART 分支（`detect_part_anchors`），JPM h1 可能直接掉到 2，需要額外的處理（fallback 到 TOC 內的 bold anchor）。**這意味著單純「過濾 table-ancestor」會順便打破 JPM h1=4。** 修法需要針對 Item 與 Part 分開決策。

3. **JPM／PG／INTC 的共通特徵**：三者都是 `font-weight:400` 的 Item heading，視覺靠 color／font-family／font-size 區分而非 bold。Class C fallback（commit `daee3ab`）目前只處理 non-bold Item 的 `_is_isolated_item_block` 路徑，對「sibling 被空 div 擋住」與「Item 在 `<td>` 裡」兩種情境都無效。

4. **空 sibling spacer 是 Workiva 常見 pattern**：`_is_isolated_item_block` 的 sibling 掃描只看第一個 Tag sibling，不理會其是否空白。這對 Workiva 導出的 `<div style="margin-bottom:6pt">` spacer 尤其致命；單是修這一點就能救 JPM。

## Recommended next steps

1. **Group B fix（最高 ROI）**：在 `_promote_headings` 的 Item 分支加上 `if has_table_ancestor(tag): continue`，或改為「僅促進 `regions` 的 anchor」。需同時確認 NVDA／AAPL／MSFT 等 sane ticker 不受影響（它們的 body Item 都在 table 外，應無 regression）。不要對 PART 分支套同樣 filter，否則打破 JPM h1。
2. **JPM fix**：修 `_is_isolated_item_block` 的 sibling 掃描，讓 prev/next sibling 跳過 text stripped == '' 的 Tag。預期 JPM h2 從 0 → 22。
3. **PG fix**：單靠 sibling 修正不夠（PG 的 next sibling 是真 body `<div>`）。需要決定是否接受 underline-title 作為新 heading 訊號，或擴大 Class C 的 non-bold 路徑涵蓋更多情境。
4. **INTC**：建議本回合不為 INTC 做專屬偵測；只要把 hard gate 放寬讓 `CLASS_C_OR_DEGRADED` flag 通過，或把 INTC 標註為 vendor-specific exception。長期再考慮 color-based heading detector。
5. **Cross-cutting**：考慮讓 `detect_item_regions` 成為 h2 促進的唯一真相來源（single source of truth），消除「dedup 與促進分家」的 dead-code gap。這能一次解決 Group B 並為未來 refactor 打基礎。
