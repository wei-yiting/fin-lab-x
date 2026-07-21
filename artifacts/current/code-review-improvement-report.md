# Code Review Improvement Report

> **Task:** PR #18 — ratified domain glossary + agent-skills config + commit-marker vocabulary adoption（branch `docs/agent-skills-setup`）
> **Date:** 2026-07-21
> **Rounds:** 3（2 輪 review+fix、1 輪確認）
> **Reviewer model:** gpt-5.5（Codex CLI 0.143.0,Quality 軸,read-only sandbox)+ claude-fable-5(Spec 軸)
> **Fixer model:** claude-opus(subagent)

## 架構影響摘要

本次 review 無架構層面的變更,所有修正皆為 documentation correctness。但有兩點需要知道:

- **CONTEXT.md 的 Commit marker 條目改寫為兩段式狀態機**:marker 在 ingest 開始時以 `status: "pending"` 寫入、結尾覆寫為 `"complete"`;檢索只認 `complete`。原條目「只在最後寫入」的說法與 `vectorizer.py` 實作不符。
- **發現一個既有的行為破口(非本 diff 引入)**:unfiltered vector search 不驗 commit marker,在 ingest 窗口期可見 partial chunks,違反 committed-or-absent(envelope §2)。已依裁決 defer 至 **DEV-92**(relatedTo DEV-73),不在本 PR 修。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 3 |
| 發現 issues 總數 | 5(Quality 軸 4 + Spec 軸 1) |
| Blocking | 0/0 |
| Major | 4/5 fixed(M-2.2 依裁決 deferred → DEV-92) |
| Minor | 0/0 |
| Suggestion | 0/0 |
| Spec findings (SP-) | 1/1 fixed |
| 文件修正 | 4 檔(CONTEXT.md、docs/agent_architecture.md、docs/file_structure.md、sec_dense_pipeline/README.md) |

## Spec Conformance(Spec 軸)

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented | R1「commit marker 取代 sentinel point,code identifiers 已於本 changeset 改名」vs R2「_Avoid_ 註記須如實反映 rename 狀態」 | Fixed(Round 2 確認) |

Spec 軸覆蓋:24 項 ratified 要求(R1–R7)全數確認實作正確——含 uuid5 seed byte-identical、payload `status` 值不變、兩處無關 sentinel 未被誤改、四項 deferred rename 未混入。無 Missing、無 Scope creep。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `CONTEXT.md` | 本 PR 的核心交付:36 詞條 ratified glossary(五節);review 修正集中於 Commit marker 與 Production-Grade Zone 兩條 | |
| 2 | `docs/agents/issue-tracker.md` | Linear 慣例的 agent-facing 設定(parent/sub-issue、PR cap、`Linear: DEV-XX`) | |
| 3 | `docs/agents/domain.md` | domain-doc 消費規則(single CONTEXT.md + docs/adr/) | |
| 4 | `AGENTS.md` | 新增 `## Agent skills` 節,指向上兩檔 | |
| 5 | `backend/ingestion/sec_dense_pipeline/common.py` | Rename 核心:`commit_marker_id` / `check_commit_marker_complete`;uuid5 seed 字串是 Qdrant point-ID 相容性契約,**不可變** | ⚠️ |
| 6 | `backend/ingestion/sec_dense_pipeline/vectorizer.py` | Marker 兩段式寫入的實作(pending → complete);僅局部變數改名 | |
| 7 | `backend/ingestion/sec_dense_pipeline/retriever.py` | 呼叫點改名 + docstring;M-2.2 的破口位於此檔但依裁決不動 | |
| 8 | `backend/ingestion/sec_filing_pipeline/pipeline.py`、`backend/evals/eval_tasks.py` | docstring / comment 詞彙更新 | |
| 9 | `docs/agent_architecture.md`、`docs/file_structure.md`、`sec_dense_pipeline/README.md` | Round 2 prose 清掃(sentinel → commit marker,9 處) | |
| 10 | `backend/tests/.../unit/test_retriever.py`、`.../integration/test_ingest.py` | 測試改名(`marker_complete`、`test_partial_failure_marker_pending` 等) | |
| 11 | `.gitignore` | 忽略 `.ua/` | |

## 所有修正問題詳解

### M-1.1(Major)
- **問題:** CONTEXT.md 的 Commit marker 條目寫「completion record 在最後一步寫入」,但 `vectorizer.py` 實際是兩段式:ingest 開始即寫入 `status: "pending"` 的 marker point,結尾才覆寫成 `"complete"`。條目漏掉 pending 態,未來 agent 可能誤刪 pending marker 或誤解 invariant。
- **修法:** 條目改寫為完整狀態機:「written as `pending` at ingest start, then overwritten as `complete` as the final commit step;檢索只認 `complete`;write-`complete`-last 紀律是 committed-or-absent 成立的原因」。
- **影響:** 詞彙表與實作一致;pending 態(DEV-73 wipe-timing bug 的相關機制)不再被文件遮蔽。
- **驗證:** Spec 軸 Round 2 逐行對照 `vectorizer.py` L111–126 / L229–242 與 `common.py` L39–42 確認忠實;Codex Round 2 確認定義部分已修。

### SP-1.1(Major,Spec 軸;與 M-1.1 後半為同一事實)
- **問題:** 同條目的 `_Avoid_` 註記寫「sentinel point 是 RAG-path code 現行 identifier 名,該 code 下次被動到時再改名」——但同一個 diff 已完成 rename。條目寫於 rename 指令之前,rename 後未回頭更新,一個 diff 內自我矛盾。
- **修法:** 註記改為反映交付現實(Round 1),最終於 Round 2 簡化為 `_Avoid_: sentinel point (legacy term)`。
- **影響:** 讀者不再被誤導以為 code 尚待改名。
- **驗證:** Spec 軸 Round 2 獨立重跑 grep 確認;Codex Round 3 repo-wide 搜尋最終確認。

### M-1.2(Major)
- **問題:** Production-Grade Zone 條目 inline 列舉六個 zones,其中 "retrieval correctness" **不存在**於 SSOT(`docs/design-envelope.md` §4 只有五項)。清單存了第二個家且已漂移,會讓 agent 在 envelope 之外過度要求 robustness。
- **修法:** 使用者裁決採 de-duplication(非鏡像同步):刪除列舉,條目只定義概念並指回 §4——「The authoritative zone list and per-zone standards live in design-envelope §4 — never enumerate them elsewhere.」
- **影響:** 清單只剩一個家;§4 未來增刪 zone 時 glossary 零維護、漂移不可能再發生。
- **驗證:** Spec 軸 Round 2 逐字比對核可措辭與 §4 指標有效性;Codex Round 2 確認 ✅。

### M-2.1(Major;M-1.1 註記修復的完成)
- **問題:** Round 1 修復後的註記聲明「舊詞只剩 `sec_dense_pipeline/README.md`」——但 repo-wide 搜尋顯示 `docs/agent_architecture.md`(4 處)與 `docs/file_structure.md`(1 處)仍以 sentinel 描述 RAG-path 機制。Round 1 的驗證 grep 被 orchestrator 的 fixer prompt 限縮在 `backend/ingestion/`,fixer 與 spec reviewer 在同一範圍互相印證了過窄的結論;cross-model 的 Codex 用 repo-wide `rg` 戳破。
- **修法:** 使用者裁決:三檔 9 處 RAG-path sentinel prose 全數改為 commit-marker 詞彙(僅換詞,語義/格式/mermaid 語法不動),註記簡化為 `_Avoid_: sentinel point (legacy term)`(不再維護位置清單)。
- **影響:** 全 repo prose 與 canonical 詞彙一致;殘留的 "sentinel" 僅剩五個無關概念檔案(frontend streaming sentinel、RunBudgetMiddleware sentinel、`sec_core.py` `[Reserved]` sentinel 及其測試)與註記本身的刻意提及。
- **驗證:** Fixer repo-wide grep(輸出存於 `fix-round-2.md`);Codex Round 3 獨立 repo-wide 搜尋確認 ✅ Fixed。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `CONTEXT.md` | Commit marker 條目狀態機化 + 註記簡化;Production-Grade Zone 條目 de-dup 指回 §4 |
| `docs/agent_architecture.md` | 4 處 sentinel prose → commit-marker 詞彙(含 mermaid node) |
| `docs/file_structure.md` | 1 處 sentinel prose → commit markers |
| `backend/ingestion/sec_dense_pipeline/README.md` | 4 處 sentinel prose → commit-marker 詞彙 |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Design issue | M-2.2:unfiltered search 不驗 commit marker,ingest 窗口期可見 partial chunks(committed-or-absent 破口) | 既有行為、非本 diff 引入;修復需 retrieval gating 設計裁決 + regression tests,屬獨立行為 slice;使用者裁決 defer | **DEV-92**(Later P2,relatedTo DEV-73)已認領:behavioral contract、三個候選方向(post-filter / commit flag / API 限縮)、驗收清單皆已寫入;DEV-73 已留分工註記 |

## Final Verification Results

### Code Level

- [x] Lint:`uv run --extra dev ruff check backend/` — All checks passed(最終 HEAD `78b401c`)
- [x] Unit Tests:`uv run --extra dev pytest backend/tests/ -q` — **822 passed**,13.02s(最終 HEAD `78b401c`)
- [x] Integration Tests:26 passed(live Qdrant,含 `test_partial_failure_marker_pending` 與 rerun-recovery,於 PR 建立時的 `7bdae8d` 執行;此後 delta 僅 markdown 4 檔 ±12 行,backend code byte-identical — `git diff 7bdae8d..78b401c --stat` 確認)
- [ ] Type Check:未配置(repo 無 mypy/pyright 強制)— 略過

### Behavior Level

- [x] Commit-marker 生命週期(partial failure → marker 停 `pending`;rerun → 恢復且無幽靈資料):由 integration scenarios 對 live Qdrant 驗證(見上)
- [x] 詞彙一致性(repo-wide 無 RAG-path sentinel prose 殘留):fixer + Codex Round 3 兩次獨立 repo-wide 搜尋

### Runtime / Observable Level

- [x] 資料相容性契約:uuid5 seed `f"{ticker}:{year}:_status"` 與 payload `status` 值 byte-identical(Spec 軸逐字確認)— 既有 Qdrant 資料無需遷移

註:`bdd-scenarios.md` / `verification-plan.md` 不存在(本 slice 為 docs+rename,無新行為),Step 5.5 BDD 驗證依 skill 規則跳過;行為證據以上述 integration scenarios 為準。

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `CONTEXT.md` | M-1.1 / SP-1.1 / M-1.2 / M-2.1 四項修正的主場 |
| `docs/agent_architecture.md` | M-2.1 prose 清掃 |
| `docs/file_structure.md` | M-2.1 prose 清掃 |
| `backend/ingestion/sec_dense_pipeline/README.md` | M-2.1 prose 清掃 |
| `docs/agents/issue-tracker.md`、`docs/agents/domain.md`、`AGENTS.md`、`.gitignore` | Review 無發現,未修改 |
| `backend/evals/eval_tasks.py`、`backend/ingestion/sec_dense_pipeline/{common,retriever,vectorizer}.py`、`backend/ingestion/sec_filing_pipeline/pipeline.py`、兩個 test 檔 | Rename 本體:Quality 軸零 issue、Spec 軸全項 ✅;review 未修改 |

## Learning Notes

### 採用的工程策略

- **清單只能有一個家**(M-1.2、M-2.1):glossary 定義概念、SSOT 擁有清單——這個原則在同一輪 review 裡兩次應驗(zone 列舉漂移、`_Avoid_` 位置清單失真),最終兩處都收斂為「指回單一權威來源、不複製」。
- **詞彙 rename 的資料相容邊界**(Spec R1a/R1b):identifier 改名與 wire/storage 契約(uuid5 seed、payload 值)分層處理——名字全換、bytes 不動,既有 Qdrant 資料零遷移。Spec 軸的逐字節驗證證明此策略完整存活。

### 權衡取捨

- **預期「README 之後再改」vs 實際「全部現在改」**(M-2.1):原裁決基於「舊詞只剩一處」的前提;repo-wide 驗證證偽前提後,維護位置清單的成本反超一次清掃,裁決反轉。前提變了,裁決要跟著重估,不是硬守。
- **預期「docs PR 只看 docs」vs 實際挖出行為 bug**(M-2.2):把 invariant 寫成明確詞條,給了 reviewer 一把對照實作的尺——文件化本身成為 bug-finding 工具。代價是 review 範圍溢出 slice,以 defer-to-issue(DEV-92)守住 slice 邊界。

### 關鍵收穫

- **聲明多大,驗證就要多大**(M-2.1):fixer 對 repo-wide 的聲明只做了 `backend/ingestion/` 範圍的驗證,spec reviewer 用同一範圍「獨立」印證——範圍相同的兩次驗證不是獨立證據。Cross-model reviewer 因為不共享預設才戳破。驗證範圍必須匹配聲明範圍,而非匹配修改範圍。
- **同一 diff 內的時序自我矛盾是真實的 failure mode**(SP-1.1):條目寫於 rename 之前、rename 完成後沒有回頭掃描受影響的描述。多步驟 session 的後步驟會讓前步驟的產物過時——收尾時要用「交付狀態」重讀一次自己的聲明。
- **Invariant 詞條要寫「機制全貌」而非「理想面」**(M-1.1):只寫 happy-path 結論(「最後寫入」)會遮蔽中間態(pending);而中間態正是 bug(DEV-73)與破口(DEV-92)寄生的地方。
