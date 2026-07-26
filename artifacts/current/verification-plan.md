# Verification Plan

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Generated: 2026-05-01 · **Revised: 2026-07-24 for DEV-106 (native reasoning parts + chips + placeholder + stall)**
- Scope: 本計畫詳列 DEV-106 slice 的 NEW scenarios(S-parts-* / S-chip-* / S-place-* / S-pres-*)驗法;preserved streaming(S-stream-*)給精簡 deterministic 條目;**F7 pre-F7 trace(S-trace-* / J-trace-01)僅列 ID + deferral 註記,實際驗法留待 DEV-107/108**。

### 共用前置與慣例

- **Endpoints**（`[POST-CODING: 由 frontend transport 設定 / backend router 確認]`,預設值取自既有 harness）:backend SSE `POST http://localhost:8000/api/v1/chat/stream`;frontend `http://localhost:5173`。
- **AI SDK v6 wire 格式**(Context7 `/vercel/ai` 已證):`data: {"type":"reasoning-start","id":"<id>"}` · `data: {"type":"reasoning-delta","id":"<id>","delta":"<text>"}` · `data: {"type":"reasoning-end","id":"<id>"}` · tool:`tool-input-start` / `tool-input-available` / `tool-output-available` · 終止 `data: [DONE]`。strict ordering(start 必先於 delta/end)由 SDK fatal 強制。
- **計時斷言用 tolerance band**(非逐 frame)因 `experimental_throttle` 可能合併更新。
- **Playwright** 慣例:`sync_playwright()` / headless chromium / `page.goto` 後 `wait_for_load_state('networkidle')` / `expect` from `playwright.sync_api`;video record 存 `frontend/tests/e2e/`。
- **D25 prompt** = `Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)`(觸發 `list_sec_sections` → `get_section` ×2 → synthesize)。
- **Selectors** `[POST-CODING]`:chip 容器、chip header、chip 展開/收合 toggle、placeholder、streaming/collapsed 狀態、`Stopped` header 皆待實作後確認 `data-testid`。下方以佔位命名(如 `[data-testid='reasoning-chip']`)標示預期,實作對齊後填入。

---

## Automated Verification — Deterministic (wire / API)

Backend / wire 行為以 curl 擷取 SSE、解析 part 序列驗證。多步驟間串接狀態。

### Feature A — Reasoning parts on the wire

#### S-parts-01: 一 block 一 part;multi-round 多 parts;id turn-unique
- **Method**: script (curl SSE + jq)
- **Steps**:
  1. 短 prompt:`curl -sN -X POST $URL -H 'Content-Type: application/json' -d '{"id":"'"$(uuidgen)"'","message":"What is a 10-K?"}' > /tmp/p1-short.txt`
  2. 解析 `reasoning-start`/`reasoning-end` 事件,依 `id` 分組;斷言恰好 1 組完整 start…end。
  3. D25 prompt 送新 session,存 `/tmp/p1-d25.txt`;抽出所有 `type` 為 `reasoning-*` 與 `tool-input-start` 的事件、保留到達順序。
  4. 斷言:出現 **3** 組獨立 `reasoning-start…end`,依序與 tool 事件交錯(reason→tool→reason→tool→reason)。
  5. 斷言:3 個 reasoning `id` **彼此相異**(`jq` 收集 reasoning-start 的 `.id`,`sort -u` 後 count == 3)。
- **Expected**: 單 block→1 part;D25→3 ordered parts,id turn-unique(無跨輪撞號)。

#### S-parts-02: raw passthrough(不切句、`\n\n` 逐字保留)
- **Method**: script
- **Steps**:
  1. 送 D25,擷取某 reasoning part 的所有 `reasoning-delta` `.delta`。
  2. 斷言:存在被切在字/詞中間的 delta(非每個 delta 都以句界/空白結尾)——即無 segmenter hold。
  3. `[POST-CODING: 用會產生多段 summary 的 prompt 或固定 fixture]` 斷言某 delta 序列 concat 後含逐字 `\n\n`(未被 strip / join)。
- **Expected**: delta 逐字直通,無句界緩衝、無 `\n` join、無 char-count re-chunk。

#### S-parts-03: abort → 無 reasoning-end
- **Method**: script (background curl + kill)
- **Steps**:
  1. 背景送 D25:`curl -sN ... > /tmp/p3.txt & PID=$!`
  2. `[POST-CODING: 等到 /tmp/p3.txt 出現第 2 個 reasoning-start(round-2)後]`(poll grep)。
  3. `kill $PID`(模擬 fetch abort / socket close)。
  4. 斷言:該 round-2 reasoning `id` 有 `reasoning-start` 與 `reasoning-delta`,但**無**對應 `reasoning-end`;檔尾無任何最終 SSE frame(非 `[DONE]`、非 error)。
- **Expected**: abort wire 靜默關閉,不補 `reasoning-end`。

#### S-parts-04: error → reasoning-end→error→finish;tool 中出錯不偽造 end
- **Method**: script
- **Steps**:
  1. `[POST-CODING: 用 FORCE_LLM_FAIL 或等效機制,令 provider 在 round-1 reasoning 串流中拋錯]`;擷取 `/tmp/p4-reason.txt`。
  2. 斷言 frame 順序:該 reasoning `id` 的 `reasoning-end` 出現在 `error` 之前,`error` 在 `finish` 之前。
  3. `[POST-CODING: 令錯誤發生於 get_section 執行中(無開著的 reasoning part)]`;擷取 `/tmp/p4-tool.txt`。
  4. 斷言:無任何 `reasoning-end`(不偽造),序列為 `error` → `finish`。
- **Expected**: error path 先補 reasoning-end 再 error;無開著 part 時不偽造。

#### S-parts-05: reasoning-off / 空 reasoning → 0 parts
- **Method**: script
- **Steps**:
  1. `[POST-CODING: 以 reasoning-off config 的 agent]` 送 D25,擷取。斷言 `reasoning-*` 事件數 == 0;仍有 tool 事件 + text-delta。
  2. (可選)reasoning-on 但短到不 emit reasoning 的 prompt,斷言同上 0 parts。
- **Expected**: 0 reasoning parts(→ 0 chips),tool + answer 照常。

#### J-parts-01: D25 wire trace 交錯順序 + id turn-unique
- **Method**: script
- **Steps**:
  1. 送 D25(reasoning-on Gemini),擷取完整 SSE。
  2. 抽出 part 序列,斷言 = reasoning₁ → tool(list_sec_sections) → reasoning₂ → tool(get_section) → reasoning₃ → text;每 reasoning part start/delta*/end 完整、id 唯一;無舊 `data-reasoning-status` 自訂事件殘留。
- **Expected**: F5 端到端 wire 契約成立。

### Feature (preserved) — Provider Streaming Pipeline

#### S-stream-01 / S-stream-02: default Gemini binding / version switch
- **Method**: script — 送 D25 到 `/chat/stream`,斷言串流完成含 `[DONE]`、有 text-delta;`[POST-CODING: 由 Langfuse 或 response metadata 確認 model == google_genai:gemini-2.5-flash]`。S-stream-02 於同 session 切 v5 後再送,斷言新 turn 完成且舊 turns 的 persisted parts 不變。
- **Expected**: 預設 / 切版皆走 Gemini,streaming 無 regression。

#### S-stream-03: 6-case matrix(native parts 斷言)
- **Method**: script(6 次 curl)+ 見 browser J-stream-01
- **Steps**: 對每 `<provider>×<mode>` 送 D25,解析 wire。`[POST-CODING: provider binding 切換機制]`。
- **Expected**: reasoning-on → ≥1 `reasoning-*` part;reasoning-off → 0 reasoning parts;皆串流完成。

#### S-stream-04: provider boot 失敗 surface
- **Method**: script — `[POST-CODING: 分別製造 API key 無效(pre-SSE)與第一個 LLM call 立即報錯(mid-stream)]`;斷言前者回 HTTP 5xx(fetch error)、後者回 SSE `error` event。Hung sub-case 移出 scope。

#### S-stream-05: `.invoke` Langfuse reasoning〔pre-F7〕
- **Method**: script — `Orchestrator.invoke(D25, v3)` 後查 Langfuse。**⚠ pre-F7 斷言,DEV-107/108 修訂。** 斷言每 chat_model span 有 `metadata.reasoning`,與 streaming path 語義等價。

#### S-stream-07: multi-tab per-tab chips 隔離
- **Method**: browser(見下 Browser 區)+ `[POST-CODING]` Langfuse 兩獨立 trace〔pre-F7〕。

#### S-stream-08: abort 後 resend 不污染
- **Method**: script — 送 D25 → 5s 後 kill → 立即新 curl 同 session;斷言新 turn 完成、`[POST-CODING: checkpointer 無半成品]`;〔pre-F7〕舊 trace `metadata.status=aborted`。前端面見 S-pres-02。

---

## Automated Verification — Browser Automation (Playwright)

前端 chip / placeholder / stall 行為只存在 UI 層,以 Playwright script 驗;關鍵狀態 screenshot / video。Selectors 為 `[POST-CODING]` 佔位。

### Feature B — Reasoning chips

#### S-chip-01: streaming chip 全文釘底、max-height 3–4 行
- **Steps**:
  ```python
  page.goto(f"{BASE}/chat"); page.wait_for_load_state("networkidle")
  page.get_by_role("textbox").fill(D25); page.get_by_role("button", name="Send").click()
  chip = page.locator("[data-testid='reasoning-chip']").first
  page.wait_for_selector("[data-testid='reasoning-chip'][data-state='streaming']")
  box = chip.bounding_box(); assert box["height"] <= FOUR_LINE_PX   # [POST-CODING: line-height 推 3–4 行上限]
  pinned = chip.evaluate("el => Math.abs(el.scrollHeight - el.clientHeight - el.scrollTop) < 4"); assert pinned
  page.screenshot(path="/tmp/s-chip-01-streaming.png")
  ```
- **Expected**: 展開、裁 3–4 行、最新文字釘底;短內容不出捲軸(另一 case)。

#### S-chip-02: 600 字無終止符 CJK wrap + 釘底
- **Steps**: `[POST-CODING: fixture 或 prompt 誘發長 CJK reasoning]`;斷言 chip `scrollWidth <= clientWidth`(無橫向溢出)、釘底成立;收合後點開斷言全文長度 ≥ 600 CJK 字。screenshot 供 visual。
- **Expected**: 字元換行、釘底穩定、可讀完整。

#### S-chip-03: 收合 Thought for Xs;X 凍結於第一個 tool-start;多輪獨立
- **Steps**:
  ```python
  page.wait_for_selector("[data-testid='reasoning-chip'][data-state='collapsed']")
  header = page.locator("[data-testid='reasoning-chip-header']").first.inner_text()
  assert re.match(r"Thought for \d+s", header)
  headers = page.locator("[data-testid='reasoning-chip-header']").all_inner_texts()
  assert len(headers) == 3
  ```
  X 的「凍結於 tool-start + 排除 tool 時間」語意由 hook 單元測試精確驗(見 Manual);browser 以 tolerance band 斷言 header 秒數合理。
- **Expected**: 收合 header 正確、三輪時長獨立(倚賴 id turn-unique)。

#### S-chip-04: 只有當前輪 chip 展開;無 chip 與 answer 並存 spinning
- **Steps**:
  ```python
  page.wait_for_selector("[data-testid='reasoning-chip'][data-round='2'][data-state='streaming']")
  assert page.locator("[data-testid='reasoning-chip'][data-state='streaming']").count() == 1
  assert page.locator("[data-testid='reasoning-chip'][data-round='1'][data-state='collapsed']").count() == 1
  page.wait_for_selector("[data-testid='assistant-text']")
  assert page.locator("[data-testid='reasoning-chip'][data-state='streaming']").count() == 0
  ```
- **Expected**: 當前輪唯一展開;答案串流時無 spinning chip(QA14)。

#### S-chip-05: 點開前一顆 chip 讀取,不被 derivation 收回
- **Steps**:
  ```python
  chip1 = page.locator("[data-testid='reasoning-chip'][data-round='1']")
  chip1.get_by_role("button").click()               # 手動展開
  page.wait_for_timeout(1500)                        # chip2 仍串流
  assert chip1.get_attribute("data-state") == "expanded"
  chip1.get_by_role("button").click(); assert chip1.get_attribute("data-state") == "collapsed"
  page.locator("[data-testid='reasoning-chip'][data-round='2']").get_by_role("button").click()
  assert page.locator("[data-testid='activity-placeholder']").is_visible() is False
  ```
- **Expected**: user override 勝過 derivation;收合 live chip 不喚出 placeholder。

#### S-chip-06: chip / tool card 到達順序;重疊時 tool card 在開著的 chip 下方
- **Steps**: 送 D25;蒐集 transcript 子元素順序(chip₁, list_sec_sections card, chip₂, get_section card, chip₃, text),斷言 DOM 順序相符。`[POST-CODING: 若能誘發 tool-input-start 早於 reasoning-end 的重疊,斷言該 tool card 的 DOM 位置在仍 streaming 的 chip 之後(下方)、且 chip 未立即收合]`。
- **Expected**: 到達順序渲染;重疊時 tool card 在開著 chip 下方(決策 4)。

#### S-chip-07: abort 半 chip 收合保留 header=Stopped;error 維持乾淨 header
- **Steps**:
  ```python
  page.get_by_role("button", name="Stop").click()   # chip1 已 collapsed、round-2 streaming 時
  aborted = page.locator("[data-testid='reasoning-chip'][data-round='2']")
  assert aborted.get_attribute("data-state") == "collapsed"
  assert "Stopped" in aborted.locator("[data-testid='reasoning-chip-header']").inner_text()
  assert "Thought for" in page.locator("[data-round='1'] [data-testid='reasoning-chip-header']").inner_text()
  ```
  對照 error case:`[POST-CODING: 令 round 以 error 收尾(reasoning-end 已送)]` 斷言該 chip header 為乾淨 `Thought for Xs`(無 `Stopped`)+ error 面出現。
- **Expected**: abort→`Stopped — thought for Xs`(保留);error(有 end)→乾淨 header + error 面。

#### S-chip-08: zero-delta 不出 chip;streamed-whitespace chip 保留
- **Steps**: `[POST-CODING: fixture — (a) reasoning-start 緊接 reasoning-end 零 delta;(b) 只送 whitespace delta 後 end]`。(a) 斷言 transcript 無新增 chip、placeholder 無 flash;(b) 斷言 chip 已出且收合為 header(未被事後移除)。
- **Expected**: zero-delta 抑制(無 ghost);已畫 whitespace chip 保留。

#### S-chip-09: 完成後 reload → 無 chips
- **Steps**:
  ```python
  page.reload(); page.wait_for_load_state("networkidle")   # D25 turn 完成後
  assert page.locator("[data-testid='reasoning-chip']").count() == 0
  assert page.locator("[data-testid='assistant-text']").count() >= 1
  assert page.locator("[data-testid='tool-card']").count() >= 1
  ```
- **Expected**: reload 後只剩 answer + tool cards,chips 全消。

#### S-chip-10: 串流中 reload → 進行中 turn 整個消失
- **Steps**:
  ```python
  page.get_by_role("textbox").fill(D25); page.get_by_role("button", name="Send").click()
  page.wait_for_selector("[data-testid='assistant-text']")   # 部分 answer 已串
  page.reload(); page.wait_for_load_state("networkidle")
  assert page.locator("[data-testid='assistant-message']").count() == 0
  assert page.locator("[data-testid='user-message']").count() == 1
  ```
- **Expected**: in-flight turn 丟棄(無 partial text/chips/error),user prompt 保留。

#### J-chip-01: 收合 chips 黃金路徑(§9)
- **Steps**: 送 D25,依序 screenshot:submit(placeholder「Thinking…」)→ chip streaming(釘底)→ collapsed「Thought for Xs」→ tool cards → 第二顆 chip → reply text 開始時 placeholder 消失。逐點斷言 selector 與文案;完成後點開任一 collapsed chip 斷言全文可讀;`page.reload()` 後斷言 chips 全消(接 S-chip-09)。錄 video。
- **Expected**: 黃金路徑逐階段可見且相符。

### Feature C — Placeholder & stall

#### S-place-01: submit(submitted)出 placeholder;tool / chip 串流中隱藏
- **Steps**:
  ```python
  page.get_by_role("textbox").fill(D25); page.get_by_role("button", name="Send").click()
  page.wait_for_selector("[data-testid='activity-placeholder']")
  assert "Thinking" in page.locator("[data-testid='activity-placeholder']").inner_text()
  page.wait_for_selector("[data-testid='tool-card'][data-state='running']")
  assert page.locator("[data-testid='activity-placeholder']").is_visible() is False
  ```
  `[POST-CODING: 確認 status==='submitted' 期間即顯示(非等 streaming)]`。
- **Expected**: submitted 空窗顯示;tool / chip 串流中隱藏。

#### S-place-02: chip 收合→reply text 空窗出 placeholder;chip→tool 空窗不出
- **Steps**: 於最後一顆 chip 收合後、reply text 前斷言 placeholder 可見;於某 chip 收合後緊接 tool card 的空窗斷言 placeholder **不**可見。`[POST-CODING: 時序捕捉,必要時用 CDP throttle 放慢]`。
- **Expected**: 符合決策 5 的空窗覆蓋。

#### S-place-03: placeholder 三態文案,無 reasoning token
- **Steps**: waiting < 10s 斷言「Thinking…」;強制 ≥10s stall(見 S-place-04)斷言「Still working…」;任一態斷言 placeholder 內文不含 reasoning 內容子串。
- **Expected**: 三態文案正確、無 reasoning 文字。

#### S-place-04: 10s 碼表;8s delta 歸零
- **Method**: browser(wiring,tolerance band)+ **hook 單元測試(fake timers)驗 10s 預設值**
- **Steps(browser wiring — F6 裁決:恰 1 個 ChatPanel 整合 case,mock 小 threshold + MSW 真實時間)**:
  ```python
  # [POST-CODING: MSW mock 一個延遲 > 小 threshold 的回應]
  page.wait_for_selector("text=Still working")     # 越過門檻降級
  ```
  再驗:於門檻前送達一個 part → 不出降級(碼表歸零)。10s 精確值由 stall hook fake-timer 單元測試負責。
- **Expected**: 越過門檻降級、任何 part 歸零;預設值由 hook test 鎖定。

#### S-place-05: 碼表新 turn 歸零、無跨 turn 滲入;長 tool 後 reasoning-start 先歸零
- **Steps**:
  1. 誘發 stall 使碼表高 → abort → 立即新 turn;斷言新 turn placeholder 顯示「Thinking…」(非「Still working…」)。
  2. `[POST-CODING: 誘發 >10s tool 後 round-2 reasoning-start]`;斷言 chip₂ 開場 header「Thinking…」而非「Still working…」。
- **Expected**: reset 邊界正確,無 stale 降級滲入。

#### S-place-06: 降級落在活躍面;長 tool 無降級面
- **Steps**: (a) dead-air stall ≥10s → placeholder 換「Still working…」;(b) chip 串流中 stall ≥10s → 該 chip header 換「Still working…」;(c) `[POST-CODING: 長 get_section >10s、placeholder 隱藏、無 chip]` → 斷言畫面無「Still working…」文字(決策 5 接受無面)。
- **Expected**: 降級落在正確 surface;長 tool 期間無降級面。

#### S-place-07: aria-live 播報(screen reader)
- **Steps**: 斷言存在 `[aria-live='polite']` 區;在 placeholder 出現 / chip 收合時,該區文字更新為高層級狀態(「Thinking…」/「Thought for Xs」);斷言 reasoning 逐字內容不進 aria-live。`[POST-CODING: accessibility snapshot 或 aria-live 節點文字監看]`。
- **Expected**: 高層級狀態被播報,逐字 reasoning 不灌 queue。

#### J-place-01: placeholder + stall 生命週期(慢 backend)
- **Steps**: `[POST-CODING: MSW 讓首 chunk > 門檻]`;依序斷言「Thinking…」→「Still working…」→ 首 delta 後 placeholder 讓位給 streaming chip、碼表歸零。錄 video。
- **Expected**: 空窗 → 降級 → 恢復 序列正確。

### Feature D — Preserved behaviors + stream browser

#### S-pres-01: tool cards running→done 與 chips 交錯
- **Steps**: 送 D25,等 `tool-card[data-state='running']` → `done`;斷言 DOM 內 tool cards 與 reasoning chips 依序交錯。screenshot 對照 main。
- **Expected**: 工具回饋不變(verify-unchanged)。

#### S-pres-02: abort→乾淨重送 + guards(wire + browser + integration)
- **Steps(browser)**:
  ```python
  page.get_by_role("button", name="Stop").click()
  page.get_by_role("textbox").fill(D25); page.get_by_role("button", name="Send").click()
  page.wait_for_selector("[data-status='ready']")
  assert page.get_by_role("textbox").is_disabled()   # [POST-CODING: 串流期斷言 composer/Stop 禁用]
  ```
  D19:`[POST-CODING: abort→ready 過渡窗連按第二次 Stop,斷言新重送未被中止]`(integration test 較穩)。決策 7 逃生:`[POST-CODING: 靜默 stall(MSW hang, status 仍 streaming)→ Stop 仍可見、click 後回 ready]`。wire 面見 S-stream-08。
- **Expected**: 乾淨重送、guards 成立、靜默 stall 可手動逃生。

#### S-pres-03: 可偵測 error → 面 + retry;error-after-chips 版面
- **Steps**: `[POST-CODING: 暫停 backend / 觸發 stream error]` → 斷言 error 面 + Retry;click Retry → 新回應成功、error 面消失。第二 case:chips 收合後 tool 中 error → 斷言 error 面渲染、收合 chips 仍可點開、errored-but-completed chip header 為乾淨「Thought for Xs」。
- **Expected**: 可偵測 error 有面 + retry;版面正確、chips 可展開。

#### S-pres-04: regenerate = 首次生成;舊 chips 先清;展開態不殘留
- **Steps**:
  ```python
  page.locator("[data-round='2'] button").click()          # 手動展開
  page.get_by_role("button", name="Regenerate").click()
  page.wait_for_selector("[data-testid='activity-placeholder']")
  assert page.locator("[data-testid='reasoning-chip']").first.get_attribute("data-state") != "expanded"
  ```
- **Expected**: 重生一致;舊 chips 清、override 不跨 turn。

#### S-pres-05: reply text 逐 token
- **Steps**: 送 D25,answer 階段連續兩次 screenshot,斷言後者文字比前者長。
- **Expected**: 逐 token 串流。

#### J-pres-01: abort 中段然後乾淨重送(journey)
- **Steps**:
  ```python
  page.get_by_role("textbox").fill(D25); page.get_by_role("button", name="Send").click()
  page.wait_for_selector("[data-testid='reasoning-chip'][data-round='2'][data-state='streaming']")
  page.get_by_role("button", name="Stop").click()
  # prior bubble:半 chip 收合為 Stopped、畫面安定
  assert "Stopped" in page.locator("[data-round='2'] [data-testid='reasoning-chip-header']").inner_text()
  page.get_by_role("textbox").fill(D25); page.get_by_role("button", name="Send").click()
  page.wait_for_selector("[data-status='ready']")   # 新 bubble 完整跑完
  # 兩 bubbles 並存;新 turn 無「Still working…」滲入(碼表歸零)
  assert page.locator("[data-testid='assistant-message']").count() == 2
  assert page.get_by_text("Still working").count() == 0
  ```
  錄 video。
- **Expected**: abort 半 chip 保留(Stopped)、畫面安定、乾淨重送、碼表歸零、兩 bubbles 並存。

#### S-stream-07: multi-tab per-tab chips 隔離
- **Steps**: 開兩個 page context 同 session,各送不同 query;斷言 Tab A 的 chips 只反映自己 turn、Tab B 不顯示 A 的 chips;`[POST-CODING: reload Tab B 於 A 串流中 → B 無 chips]`。〔pre-F7 Langfuse 兩 trace 留待 DEV-107/108〕。
- **Expected**: chips per-tab、無 cross-tab 洩漏。

#### J-stream-01: 6-case E2E(browser video)
- **Steps**: 對 6 case 各跑 D25,錄 video;斷言串流完成、reasoning-on 至少 1 顆 chip、reasoning-off 0 chip、無 console/network error。
- **Expected**: 6 家 streaming 行為可供 reviewer 親眼看。

### Feature (pre-F7) — Langfuse Reasoning Persistence 〔DEV-107/108 修訂〕

#### S-trace-01 … S-trace-09, J-trace-01
- **Method**: deterministic (Langfuse SDK/API polling) — **⚠ 反映 pre-F7 per-call 設計,DEV-106 不驗此終態。** 詳細步驟見 archive `artifacts/archive/2026-07-24-pre-dev106-ephemeral-indicator/verification-plan.md`;DEV-107 落地 trace-level 全文後,由 DEV-108 於本檔以「root trace 有全文 + per-call 分隔 marker」單一驗證項取代。
- **Expected**: 〔待 DEV-107/108〕。

---

## Manual Verification

### Manual Behavior Test

> Coding Agent 無法穩定自動化、或屬 hook/unit 層更適合的檢查。

#### 計時 / 排序精確度（S-chip-03 的 X 語意、S-place-04 的 10s、S-place-05 reset 排序）
- **Reason**: 逐 frame 精確度 + fake timers 屬 hook 單元測試層;browser 端只驗 wiring(tolerance band)。
- **Steps**:
  1. Run stall hook 單元測試(fake timers)驗 10s 預設門檻。
  2. Run「Thought for Xs 凍結於第一個 tool-start、排除 tool 時間」的 timer hook 單元測試(合成 reasoning+tool part 序列)。
  3. Run reset-before-derive 排序 hook 測試(reasoning-start 先歸零再 derive header)。
  4. Run override-map 每 turn 清空 + turn-unique-id keying 的 hook 測試。
- **Expected**: hook 層綠;browser 整合僅 1 個 ChatPanel case(mock 小 threshold + MSW 真實時間)。

#### Layout / scroll 穩定與 CJK 視覺（S-chip-01/02, 深迴圈 10+ chips）
- **Reason**: 收合 4→1 行的 scroll jitter、多顆 chip 累積位移、CJK wrap 視覺,自動斷言易 flaky,適合人工目視 + screenshot 比對。
- **Steps**: 跑 D25(含多輪)與長 CJK reasoning,肉眼確認收合時無跳動、深迴圈(10+ chips)仍可讀、CJK 不溢出。
- **Expected**: 版面穩定、CJK 可讀。

#### Grapheme flicker（cosmetic）
- **Reason**: wire 已 codepoint-safe(Context7 證);僅 emoji/ZWJ 家族跨 delta 一 frame 半字自癒抖動。
- **Steps**: 以含 emoji/繁中的 reasoning 目視;確認最終 collapsed 文字 byte-正確。
- **Expected**: 僅瞬時、自癒,終態正確。

### User Acceptance Test

> PO 視角驗收,PR review 時執行。

#### J-chip-01 黃金路徑體驗
- **Acceptance Question**: 多輪 agent 的「想→查→再想→答」節奏,在 transcript 上是否一眼可讀、乾淨、可事後點開回看?
- **Steps**:
  1. 送 D25,觀察 placeholder → 逐顆 chip 串流→收合 → tool cards → answer 的整體節奏是否流暢、無閃爍/跳動。
  2. 點開幾顆收合 chip 讀全文,確認可讀且有價值。
  3. reload,確認 reasoning 乾淨消失(可接受)。
- **Expected**: 節奏清楚、體驗流暢、符合 ADR-0006 legible multi-round 目標。

#### Abort / error 體驗(S-chip-07, S-pres-02/03)
- **Acceptance Question**: 中斷與出錯時,畫面是否安定、可預期、可重試,且能分辨「被中斷」與「正常完成」?
- **Steps**: 串流中 Stop,確認半 chip 標「Stopped」、可乾淨重送;製造 error,確認有明確 error 面 + retry;確認 aborted 與 completed chip 可肉眼區分。
- **Expected**: 中斷/出錯安定可預期、狀態可辨。
