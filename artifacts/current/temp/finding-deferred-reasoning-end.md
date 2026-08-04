# Finding: deferred reasoning-end — 單一 root cause 統一解釋 4 個觀察

Date: 2026-08-04 (DEV-109 round 1, human manual test + wire/code cross-check)

## Root cause

`StreamEventMapper` 只在三個時機關閉 open reasoning part
(`backend/agent_engine/streaming/event_mapper.py`):

1. 下一個 LLM call 的 chunk-id transition (`_handle_messages`, ~L96)
2. text block 出現 (`_handle_text_block`, ~L180)
3. `finalize()` (turn 結束 / error path)

`_handle_tool_call_chunk_block` (~L195) 明文**不**關閉 reasoning part — 引用 DEV-106 §B 裁決
(provider 可能在 reasoning-end 前送 tool args,chip 須保持開啟讓 tool card 排下方保序)。

Wire 證據 (`temp/s-wire-02.sse`, GPT-5-mini reasoning-on, canonical prompt):

```
reasoning-start → delta×180 → tool-input-available → tool-progress → tool-output-available
→ reasoning-end   ← 下一輪 LLM call 開始才補上
→ reasoning-start → tool-input … (每一輪都同樣 pattern)
→ reasoning-start → delta×521 → reasoning-end → text-start   ← 同一 flush,間隔 ~0ms
```

即:被 DEV-108 裁決為 opportunistic 邊角 case 的「tool card 排在開著的 chip 下方」,
在預設 provider (GPT-5-mini) 上是**每一輪必然發生的主線行為**,因為 mapper 結構上
沒有「tool chunk 到達 = reasoning block 結束」這個關閉訊號。

## 統一解釋的 4 個觀察

| # | 觀察 (human 手動測 / 自動化) | 機制 |
|---|---|---|
| 1 | chip 在 tool 執行全程保持展開,tool 做完(下一輪開始)才收合 | part 在 wire 上真的還開著 |
| 2 | 最後一顆 chip「瞬間收起」同時 answer text 立刻開始;S-place-02 自動化 FAIL(placeholder 永不出現) | `reasoning-end` 與 `text-start` 同 flush 抵達 → window B 寬度 ~0ms,< 300ms grace → placeholder 不出現**是 grace 設計下的正確行為**,但空窗結構上永遠是 0,window B 形同虛設 |
| 3 | tool 執行中 chip header 顯示 `Still working…`(screenshot) | chip 仍是 streaming 態 = live surface;tool 執行 >10s 且 progress 事件稀疏 → stall 碼表觸發,降級文案落在還開著的 chip header 上 |
| 4 | MSFT 案例:全部 tool call complete 後有無 placeholder 的 dead air | 等待下一輪 LLM call 的數秒間,last part 是 completed tool part → window B 條件不成立;且前一顆 chip 還開著(視覺上有「活」元素)→ placeholder 被抑制,但畫面實際無任何東西在動 |

附帶重分類:
- **S-place-02 自動化 FAIL** → 測試斷言對這種 wire shape 而言期望錯誤(空窗 0ms 時不出現
  placeholder 才是對的);真正的問題是上游 deferred reasoning-end 讓空窗永遠是 0。
- **S-chip-03 的 2.122s 邊界超差** → X 在 client 端第一個 tool-start 凍結,量測與 header 的
  誤差主要是渲染/取樣 skew;與本 finding 無直接因果,維持 borderline noise 分類。

## 與 ratified 裁決的張力

- DEV-106 §B / S-chip-05 And 句:裁決保護的是「**抵達序**」(tool card 排在開著的 chip 下方、
  不強制立即收合),當時假設 overlap 是 provider-timing dependent 的偶發 case。
- 現實:對 OpenAI(預設)是 100% 每輪發生;且「close-on-tool-chunk」其實**不破壞抵達序**
  (tool card 改排在已收合 chip 下方,順序不變)。
- 裁決本身沒有被違反,但其成本假設(偶發)已失效 → 屬 design 層問題,上呈裁決,
  不自行改規格(bdd-e2e-loop Level 3)。

## 選項(供裁決,尚未動任何 code)

**A. mapper 在收到 `tool_call_chunk` block 時關閉 open reasoning part**(比照 text block 的處理)
- 效果:chip 在 tool-start 收合(與 `Thought for Xs` 的 X 凍結時點一致);tool 執行中 live
  surface = tool card(stall 降級文案自然不再落在 chip header);觀察 1、3 直接消失。
- 殘留:觀察 4 的 dead air(tool-complete → 下一輪 reasoning-start)**不會**因此被 placeholder
  蓋住 — 該空窗不在 ratified 的兩個 window 定義內,需要追加裁決(新增 window C:
  「last part 是 completed tool part 且 status 仍 streaming」or 接受 completed tool card 視為
  畫面有內容、不補 placeholder)。
- 風險:若 provider 在同一 LLM call 內 tool args 之後**繼續** reasoning(理論上
  Anthropic interleaved;Gemini 罕見),單一 provider block 會被切成兩顆 chip,
  技術上違反「one provider block = one part」。Known gap 本來就不驗 Anthropic;
  Gemini 的 function_call 之後同 call 續 thought 未在本輪驗證中觀察到。

**B. wire 不動,frontend 在第一張 tool card 出現時「視覺收合」chip**
- 保留 wire 語意,但引入 non-derived 顯示狀態(ADR-0008 的 non-derived state budget 有上限),
  stall live-surface 判定也要跟著改;複雜度轉嫁到 frontend,且 wire 上 part 仍長時間開著,
  任何未來 consumer 都要重新處理同一問題。

**C. 全部維持現狀,把觀察 1/3/4 記為 ratified 行為**
- Human 已在手動測試中判定為 failure,此選項名存實亡,列出僅為完整性。

## 建議

A + 追加裁決「tool-complete → next content 空窗是否補 placeholder」。
S-place-02 的測試斷言同步修正(空窗 < grace 時不出現 placeholder = PASS 條件)。
