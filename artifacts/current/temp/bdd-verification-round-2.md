# DEV-109 BDD Verification — Round 2（human 手動測試觸發的裁決與修復）

## 起點

Round 1 結果報告後,human 以 "Latest market news for NVDA" / "Summarize the latest 10-K of MSFT"
手動測試,回報 4 個現象;經 wire capture(`s-wire-02.sse`)與 code 交叉驗證,統一診斷為單一
root cause(deferred reasoning-end),詳見 `finding-deferred-reasoning-end.md`。

## Human 裁決

- **裁決 9**:選 Option A——mapper 收到 `tool_call_chunk` 即關閉 reasoning part,
  取代 DEV-106 §B keep-open 允許(其「偶發」成本假設實測失效:預設 provider 每輪必然)。
- **裁決 10**:tool-complete → next content 的 dead air 補 placeholder(window C,同 300ms grace)。

## 修復(one-fix-at-a-time,詳見 fix-history.json)

1. **close-on-tool-chunk**(backend `event_mapper`)——wire 實測改為每輪
   `reasoning-end → tool-input-available`(`fix1-wire-check.sse`)。
2. **placeholder window C**(frontend `useDeadAirPlaceholder`)——新 MSW fixture
   `tool-deadair-then-text` 端到端驗證:tool 完成後 2s dead air,placeholder 於 grace 後出現、
   `aria-live="polite"`、text 抵達即讓位。
3. **GeneratorExit abort path**(backend `astream_run`)——round-2 J-03 重跑時發現的真 bug:
   abort 落在 generator 懸停於 yield 時以 `GeneratorExit` 送達,原 cleanup 只掛
   `asyncio.CancelledError`,tail + `status:"aborted"` 靜默漏寫(時序 race;round 1 恰好都
   走 CancelledError 路徑所以通過)。已補分支 + 單元測試。

## Round 2 驗證結果

| Scenario | Round 1 | Round 2(修復後) |
|---|---|---|
| S-chip-02 | PASS | PASS(2.7m,slow-turn timeout 放寬) |
| S-chip-03 | FAIL(差 2.122s) | **PASS**(差 1.996s;免 code fix) |
| S-chip-04 | inconclusive(單 segment) | **PASS**(tail-only 規則驗證成功) |
| S-chip-06 / 08 / 09 | PASS | PASS |
| S-place-02 | FAIL(斷言對 wire shape 期望錯誤) | **PASS**(post-ruling MSW 版;真 backend invariants 兩輪取樣 0 違規) |
| S-place-04 / 05 | PASS | PASS |
| J-03 UI + Langfuse | PASS(round 1)→ round 2 初跑揭露 fix-3 | **PASS**(aborted turn tail+status 正確;resent turn 乾淨) |
| 全套 unit/integration | — | backend 924 綠、frontend 200 綠 |

## SSOT 同步

- `bdd-scenarios.md`:S-chip-05 Rule/And 改寫(裁決 9)、placeholder Context + S-place-02 改寫
  (裁決 10)、文末新增「DEV-109 執行期追加裁決」段(裁決 9/10 + fix-3 記錄);原裁決 4
  (opportunistic)作廢。
- `verification-plan.md`:S-place-02、S-chip-05 條目同步改寫。

## 殘留(非 blocker)

- S-chip-07(Gemini reasoning-off browser 案)round 1 兩次都是工具面 flake,尚未有乾淨驗證
  ——但其 wire 層等價條 S-wire-05 已 PASS,且 human 手動測試可低成本覆蓋。
- S-place-03 的 Browser-Use 回報語意模糊——post-ruling 的 S-place-02 invariants 取樣
  (placeholder 不與執行中 tool card 並存,兩輪 0 違規)已實質覆蓋同一斷言。
- Manual Behavior Test M-01~05 + UAT-01 尚未執行(bdd-e2e-loop 的 Manual Phase)。
