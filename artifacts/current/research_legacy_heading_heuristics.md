# Research — 舊 HTML pipeline heading detection 對純文字新設計的可借鑑性

## Scope

Audit 即將 archive 的 v2 markdown pipeline (5 modules) 的 heading 邏輯，提取對純文字 sub-heading 偵測仍 actionable 的 insight。Title Case body 句首是新 design 最大風險。

---

## 1. 舊 pipeline heading detection flow

```
RawFiling.raw_html
    │
    ▼
HTMLPreprocessor.preprocess()                           # html_preprocessor.py
    ├─ _strip_xbrl_tags                                 # ix:* unwrap
    ├─ _remove_hidden_elements                          # display:none decompose
    ├─ _unwrap_font_tags                                # legacy <font>
    ├─ _normalize_text_whitespace                       # 內嵌 \n → space
    ├─ _promote_headings                                # 核心 — 把 div/p 改成 <h1>/<h2>/<h3+>
    │   ├─ detect_item_regions() (sec_heading_promoter)   # body Item 邊界
    │   ├─ detect_part_anchors(is_eligible=_has_bold_signal)
    │   ├─ _estimate_body_font_size                       # 字符加權眾數
    │   └─ for each block: PART_RE/ITEM_RE × bold/isolation/strong-size 三條 fallback path
    │       └─ promote_subsections() — 在每個 ItemRegion 內 rank font-size → h3/h4/h5
    └─ _strip_decorative_styles                         # 在 promote 之後執行（跑 size 邏輯需要 style）
    │
    ▼
HTMLToMarkdownAdapter.convert()                         # html_to_md_converter.py — 純包裝 lib，無 heading 邏輯
    │
    ▼
MarkdownCleaner.clean()                                 # markdown_cleaner.py — 純後處理 (text-only)
    ├─ _strip_cover_page                                # # Part I / ## Item 1 為 anchor
    ├─ _strip_page_separators                           # bare `---` 行
    ├─ _strip_part_iii_stubs                            # incorporated-by-reference + remainder<100ch
    └─ _normalize_headings
        ├─ _merge_split_titles                          # AMZN / AMT 雙行 heading 合併
        ├─ _PART_HEADING_RE replace                     # # Part I
        └─ _ITEM_HEADING_RE replace + _title_case
```

分工：HTML 階段做 **樣式 → 結構** 提升 (signals = font-size/bold/sibling)，Markdown 階段做 **文字 normalization + 雙行合併**（純 text-only，已和新 design 同維度，可直接抄）。

---

## 2. Heuristics inventory

| # | Signal | Where | What it does | Edge case covered |
|---|--------|-------|--------------|-------------------|
| H1 | Item regex `^Item\s+\d+[A-Z]?\.` | sec_heading_promoter.py:16 | Body Item 邊界 anchor | TOC 重複 |
| H2 | Part regex `^PART\s+(I{1,3}V?|IV)\b` | sec_heading_promoter.py:17 | h1 anchor | Roman numeral |
| H3 | **Last-occurrence dedup** by item_num | sec_heading_promoter.py:67-76 | TOC 出現的 Item < body 出現 ⇒ 留 body | TOC pollution（所有公司） |
| H4 | **Token normalization** `" ".join(tag.get_text().split())` | sec_heading_promoter.py:70, html_preprocessor.py:268 | 跨 span heading 不被 strip 折疊 | MSFT 2025 `<span>PART</span><span> I</span>` → `PART I` 而非 `PARTI` |
| H5 | **Table-ancestor drop pass** | sec_heading_promoter.py:88-97 | TOC 完全在 `<table>` 裡 ⇒ drop | BRK.A/B 把 Items 10-14 全部留在 TOC 表格 |
| H6 | font-weight 700 / `bold` / `<b>` / `<strong>` | sec_heading_promoter.py:14, 250-262, html_preprocessor.py:140-155 | 第一條 promote signal | 多數 modern filings |
| H7 | `is_isolated_item_block` — sibling 不是 div/td/th/table/ul/ol/li | html_preprocessor.py:84-116 | Bold 失敗時的 fallback | INTC、JPM 非 bold body Item |
| H8 | **Empty-spacer skip** — 跳過空文字 Tag siblings | html_preprocessor.py:96-107 | Workiva margin 用空 div 做 spacer | JPM body Item 旁邊是空 `<div style="margin-bottom:6pt">` |
| H9 | `_has_item_strong_size_signal` — size > body × 1.1, len < 150 | html_preprocessor.py:119-137 | 純大 font-size 旁路 sibling check | JPM 12pt over 10pt body，相鄰 div 是真 body |
| H10 | char-weighted dominant font-size | sec_heading_promoter.py:168-192 | 找 tag 主要字級（避免 footnote `1`@6pt 蓋過 heading@10pt） | NVDA 9pt heading + 6pt footnote marker |
| H11 | `_estimate_body_font_size` — 全 doc span 字符加權眾數 | html_preprocessor.py:63-81 | Body baseline，給 H7/H9 用 | INTC 14pt heading vs 10pt body |
| H12 | `is_bold_only_block` — 全部 text 後代都 bold | sec_heading_promoter.py:195-237 | sub-heading candidate | NVDA 純 bold sub-heading |
| H13 | min_len=3, max_len=200, sentence-end guard >30 | sec_heading_promoter.py:9, 220-226 | 排 prose | 句末有 .!? 且 >30 ⇒ reject |
| H14 | **Numeric-only reject** | sec_heading_promoter.py:223 | page number guard | `42`、頁碼 |
| H15 | `build_noise_tokens` — block 文字出現 ≥4 次 | sec_heading_promoter.py:25-33 | 排重複頁眉 | BAC `Bank of America`、`Part I` 每頁出現 |
| H16 | `is_self_reference` — `^Item \d+[A-Z]?` | sec_heading_promoter.py:22, 36-38 | Item 7 內部不要把 `Item 7A. Quantitative` 升 h3 | 跨 Item 引用 |
| H17 | font-size rank ⇒ h3/h4/h5 (cap) | sec_heading_promoter.py:279-289 | sub-section hierarchy | 多層 sub-heading |
| H18 | `_NEXT_LINE_TITLE_MAX_LEN = 100` + ALL CAPS / Title Case 過濾 | markdown_cleaner.py:130, 332-365 | AMZN/AMT 雙行 heading 合併安全 | `## Item 1.\n\nBusiness` |
| H19 | `_looks_like_title_case` — 第一字大寫 + 後續字大寫（小詞除外） | markdown_cleaner.py:526-542 | 雙行 merge 時拒絕 body 句首 | 防 "The company operates..." 被當 title |
| H20 | Part III stub detector — `incorporated.*by.*reference` + remainder<100 chars | markdown_cleaner.py:69-72, 478-504 | 移除 Items 10-14 stub | 多數公司 |
| H21 | Pseudo-stub adverb 注入 (`incorporated\s+(?:\w+\s+)?(?:in|into|to|by)\s+(?:\w+\s+)?reference`) | markdown_cleaner.py:69-72 | "incorporated herein by reference" 等變體 | 大部分真 10-K 用變體 |
| H22 | Markdown link 剝除再算字數 | markdown_cleaner.py:91, 501 | trailing image/URL 不撐起 stub | XOM 等公司 |

---

## 3. Company-specific workarounds

| Company | Quirk | Workaround | 本質 |
|---------|-------|------------|------|
| **MSFT 2025** | XBRL exporter 把 heading 切到相鄰 span：`<span>PART</span><span> I</span>` 或 `<span>PAR</span><span>T II</span>` | H4: `" ".join(tag.get_text().split())` 取代 `get_text(strip=True)` | **HTML artifact only** — 純文字裡 heading 已是連續字元 |
| **JPM (Workiva)** | Body Item 非 bold；相鄰 sibling 是空 `<div style="margin-bottom:6pt">` spacer | H8 empty-spacer skip + H9 strong-size signal | **HTML artifact only** — text 裡空 div 不存在 |
| **JNJ / MSFT / BAC** | Body PART divider 非 bold（只有 TOC bold） | `detect_part_anchors(is_eligible=_has_bold_signal)` 退回 TOC anchor | **HTML artifact** — text-only 沒有 bold 概念 |
| **JNJ Item 1/1A** | Sub-heading 是 sentence case (`Risk factors`) 而非 ALL CAPS | `_title_case` 的 `_needs_recasing` 對 sentence-case 也 trigger（markdown_cleaner.py:455-467） | **真 SEC convention** — 純 text 仍存在 |
| **BAC** | 沒有 `# Part I` heading；page header `Bank of America` 重複 | H15 noise-token + cover-page anchor fallback `## Item 1` (markdown_cleaner.py:210-212) | **真 convention** — 純 text 仍存在 |
| **BRK.A/B** | Items 10-14 全在 TOC `<table>` 裡，body 沒有重新 anchor | H5 table-ancestor drop pass | **真 SEC convention**（cross-reference proxy） — text-only 也會碰到，但 BRK 這種把 Items 整段 cross-ref 出去的，新 design 應走 Path III stub 移除 |
| **Donnelley/Workiva** | 跨 span text + nbsp + 中間 text node：`<span>Item</span><span>&nbsp;7.</span><span> MD&A</span>` | H4 normalization 同上 | **HTML artifact only** |
| **AAPL** | `Item 1.\xa0\xa0\xa0\xa0Business` non-breaking spaces | `_normalize_text_whitespace` (`\s+` → ` `) | **HTML artifact**，但 `\xa0` 在 `section.text()` 也會出現（已在 research_filing_markdown_quality.md 證實） |
| **AMZN** | `## Item 1.\n\nBusiness Description` heading 跟 title 跨兩行 | H18 `_merge_split_titles` | **真 convention** — text-only 仍存在（Markdown 後處理已是純 text 邏輯） |
| **AMT** | `## ITEM 10.\n\n- DIRECTORS, ...` dash bullet 起 title | H18 dash-prefix branch + ALL CAPS / Title Case 守門 | **真 convention** — text-only 仍存在 |
| **INTC** | 非 bold Item heading + 14pt over 10pt body | Class C fallback (H9 strong-size signal) | **HTML artifact only** — text 裡 bold/size 都沒有 |
| **WMT/XOM** | Pseudo-stub "Reference is made to…" / "appears on pages…" 不含 "incorporated by reference" | （未實作）— 現有 H20 抓不到 | **真 convention** — text-only 仍存在 |
| **NVDA** | Footnote `1`@6pt 同 div 蓋過 heading text@10pt | H10 char-weighted dominant size | **HTML artifact only**（純 text 沒有 size） |

---

## 4. Transferable to new design (純 text + edgartools native API)

| 借鑑項 | 原來自 | 新 design 怎麼用 |
|---|---|---|
| **Last-occurrence dedup** (H3) | sec_heading_promoter.py:67-76 | `section.text()` 已被 edgartools 切到單一 section，但 `Item 7A. Quantitative` 等 cross-Item reference 仍會出現在 Item 7 內。新 sub-heading 偵測要排除 self/cross-Item reference (`^Item \d+[A-Z]?` regex，借 H16 邏輯) |
| **Numeric-only / page-number reject** (H14) | sec_heading_promoter.py:223 | edgartools 文字仍會夾雜頁碼。`stripped.isdigit()` reject 是現有 ALL CAPS rule 已有的 |
| **Length window 3-200 + sentence-end guard** (H13) | sec_heading_promoter.py:220-226 | 對 Title Case heading 偵測**極度有用**：Title Case body 句首通常是完整句（>30 chars 且以 .!? 結尾），用「length≤120 + 不以 .!? 結尾」可以剔除大部分 false positive |
| **Self-reference reject** (H16) | sec_heading_promoter.py:22, 36-38 | 同上，`^Item \d+[A-Z]?` 在新 sub-heading 偵測也要 skip |
| **Noise token (≥4 次重複)** (H15) | sec_heading_promoter.py:25-33 | edgartools `section.text()` 裡仍可能殘留重複的 page header / footer (`Bank of America` 每頁)。對 sub-heading 偵測：在偵測前先掃整個 filing text 找出重複短串，當 noise blacklist。**關鍵**：必須 cross-section 統計，不能只在單一 section 內 |
| **Title Case 守門邏輯** (H19) | markdown_cleaner.py:526-542 | 新 Title Case sub-heading detector 直接搬：第一字大寫 + 每個非小詞起首大寫 + 整體不以 .!? 結尾 + length 短。這是純 text，已 archive 也能直接抄 |
| **Pseudo-stub adverb 注入** (H21) | markdown_cleaner.py:69-72 | `is_stub_section()` 移到 sec_core，**直接保留這條 regex** — design 已決定要保留 stub 邏輯 |
| **Pseudo-stub second match group**（未實作但研究指出） | research_prelude_block_relationship.md:138 | 加 "Reference is made to … section"、"Refer to … on pages N"、"appears on pages N–M" 三種 |
| **AMZN/AMT 雙行 heading 合併** (H18) | markdown_cleaner.py:288-329 | 雖然 edgartools section text 第一行通常是 `ITEM N. TITLE`，但 sub-heading 也可能跨行（`OVERVIEW\n\nWe operate...` vs `OVERVIEW\nOf Operations`）— 借鑑「合併下一非空行如果它符合 ALL CAPS / Title Case 守門」的策略 |
| **Cover page anchor fallback** (markdown_cleaner.py:210-212) | `# Part I` 找不到 ⇒ fallback `## Item 1` | 新 design 已用 edgartools 結構化 access，section 邊界由 library 給，這條是 anchor 邏輯不再需要，但**保守通過原則** (markdown_cleaner.py:8-12) 應該繼承到 sub-heading 偵測：**留下 noise 沒關係，絕不能誤刪有意義的內容** |

---

## 5. Anti-patterns (HTML-specific，新 design 不該重新發明)

| 別碰 | 原 heuristic | 為什麼不行 |
|---|---|---|
| Font size signals (H10, H11, H17) | `extract_dominant_font_size`、`_estimate_body_font_size`、size→h3/h4/h5 rank | edgartools `section.text()` 是純文字，零 style 資訊；MSFT 整個 filing.markdown() 也丟掉 style |
| Bold signals (H6) | `_has_bold_signal`、`<b>`/`<strong>` 偵測 | 同上，純文字無 bold |
| Sibling isolation (H7, H8) | `is_isolated_item_block` + spacer skip | 純文字沒有 sibling Tag 概念，"前後是 div/td" 失去意義；改成「前後是空行」是不一樣的 signal |
| Strong size signal (H9) | size > body × 1.1 | 同上，沒 size |
| Token normalization (H4) | `" ".join(tag.get_text().split())` | 純文字裡 heading 已連續，不會被 span 切開 |
| TOC `<table>` drop pass (H5) | table ancestor 偵測 | edgartools 已負責 section 邊界，TOC 已被 library 排除 |
| `is_bold_only_block` (H12) | 全部文字後代都 bold | 純文字無 bold |
| HTML→Markdown round-trip 本身 | html_to_md_converter.py | research_filing_markdown_quality.md 證明 `filing.markdown()` 在 MSFT 嚴重損壞，重建是無謂 round-trip |

---

## 6. Recommendations for new ALL-CAPS + Title Case mixed rule

### 6.1 統一守門（兩種 case 共用）

```
def is_block_heading_candidate(line):
    s = line.strip()
    if not s: return False
    if not (5 <= len(s) <= 120): return False        # 借 H13
    if s.isdigit(): return False                     # 借 H14
    if any(c in s for c in {'|', '$', '%'}): return False
    # 借 H16：跨 Item 引用不算 sub-heading
    if re.match(r'^Item\s+\d+[A-Z]?\b', s, re.I): return False
    # 借 H13：>30 chars 且以 .!? 結尾 ⇒ 是句子，不是 heading
    if len(s) > 30 and s[-1] in '.!?': return False
    # 借 prelude research finding：digit-adjacent-to-alphabetic 的 table cell
    if re.search(r'[A-Za-z]\d{3,}|\d{3,}[A-Za-z]', s): return False
    return True
```

### 6.2 Case 分流

```
def classify(line):
    s = line.strip()
    if s.isupper(): return 'all_caps'
    # 借 H19：第一字大寫 + 每個非 stop-word 起首大寫
    if looks_like_title_case(s): return 'title_case'
    return None
```

### 6.3 Title Case 額外守門（最關鍵 — body 句首也是 Title Case）

加上**位置 / 上下文** signals，不要只看單一行：

| Signal | 借鑑來源 | 應用 |
|---|---|---|
| **前後空行** | （新 — 純 text 唯一可靠 signal） | sub-heading 通常獨立成行，前後至少一個空行；body 段落首句通常黏在前文後 |
| **不接續上一行** | 同上 | 上一行非空且不以 .!? 結尾 ⇒ 大概率是 body 接續，**不是** heading |
| **後接 paragraph** | 推自 H18 | 下一非空行是長 prose（>80 chars 且不像 heading）⇒ 強化 heading 判定 |
| **noise token blacklist** | H15 | 對整個 filing 統計重複短串（≥4 次、≤50 chars），candidate 在 blacklist 內 ⇒ 拒絕 |
| **cross-section consistency** | （新） | 若同一 ticker 同一 Item 多年都用同一組 sub-heading（"Overview"、"Liquidity"），增加置信度。短期可不做，先實現單行邏輯 |

### 6.4 可借的雙行合併 (H18)

`OVERVIEW\n\nOf Operations` → `OVERVIEW Of Operations` 的合併規則直接抄 markdown_cleaner.py:288-329，但守門用 6.1 + 6.2 的 candidate gate。

### 6.5 Stub 偵測延伸 (H20, H21)

新 `is_stub_section()` 在 sec_core 至少要包含：

1. 現有 `_INCORP_BY_REF_RE` (markdown_cleaner.py:69-72)
2. 加 prelude research 提的：`Reference is made to`、`Refer to .* (?:section|on pages)`、`appears on pages \d+`（涵蓋 JPM/XOM 4 個 pseudo-stub）
3. Remainder threshold 100 chars 維持（H22 strip markdown link 在純文字環境不需要）

### 6.6 不該採納

- 不要重做 font-size / bold / sibling isolation — 純文字環境信號不存在，硬模擬只會引入 FP
- 不要寫公司專屬 workaround — 95% quirk 是 HTML artifact，換到 edgartools 後消失；剩下 (BAC 沒 Part、JNJ sentence-case) 用通用 heuristic，不要 hardcode ticker

---

## 一句話總結

純文字環境**保留**：last-occurrence、length window、sentence-end guard、numeric/digit-cluster reject、self-reference reject、noise-token blacklist、`_looks_like_title_case`、pseudo-stub regex 擴張。Title Case body 句首風險靠「前後空行 + 上一行不以 .!? 結尾 + 長度 ≤120 + 不以 .!? 結尾」四 AND 壓制 — **位置 signals 是純文字唯一新信號來源**。
