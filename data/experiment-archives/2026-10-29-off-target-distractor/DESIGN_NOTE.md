# Design note — off-target company controlled eval (MVP)

Linear: DEV-232 (parent DEV-96) · Branch `feat/off-target-controlled-eval` (stacked on #93)

Scope: **MVP run on 2026-10-29**. The formal `design.md` + spec review were
skipped for time; this note records the design as run.

## Question

Tracing showed answers about company X weaving in news about an unrelated
company Y that the news search happened to return. Does the answer-synthesis
step filter that content out when it is in the evidence?

Live news cannot be controlled, so the eval **replays recorded tool output**:
the variable is the evidence the agent sees, not the search.

## Design

```
14 zh diagnostic rows whose recorded reader_luna_medium runs called Tavily
  └─ per row, one recorded run (the one with most multi-company snippets)
       Tavily results, in recorded call order
         ├─ C1: unchanged (real snippets: target news with other-company passages)
         └─ C0: same snippets minus sentences labeled unrelated_other
  run: same question, same config, Tavily replaced by a replay tool
       (same name / description / args schema; sha256 identical to live)
  measure: the final answer
```

| Decision | Choice | Why |
|---|---|---|
| Unit of distraction | sentence/passage inside real snippets | real failures are mixed articles, not whole unrelated articles |
| Control | C0 = minimal edit of C1 | only the unrelated spans differ; separates "learned from evidence" from "model brings it in" |
| Labels | Gemini + Codex independently (κ = 0.81 on 1,067 sentences) | two model families other than the Claude judge |
| Disputed passages (7) | kept in C0 | conservative: C0 only loses consensus-unrelated content; under-states any C1–C0 gap |
| Systematic disputes | page chrome kept; passage continuations follow their passage | documented rules in `LABELING_GUIDE.md` |
| Replayed tools | Tavily only | the variable; SEC (Qdrant RAG) and Finnhub stay live |
| Repeated Tavily calls | k-th call → k-th recorded call, cycling | keeps per-call result size realistic |
| Rows run | 10 of 14 (rows where C0 ≠ C1) | rows 2, 9, 14, 23 have no consensus-unrelated sentence |
| Arms | `reader_luna_medium` (primary); `reader_luna_none` (exploratory sensitivity) | reader 2×2 saw more synthesis errors without reasoning |
| Question variant | exploratory: same fixtures, open recap question `"{targets} 最近有什麼新聞？"` (luna_medium) | the trace failure and the seed cases are recap-shaped |
| Reps / pairing | 3 reps; pairs = (row, rep) C0 vs C1; condition order alternates | paired exact McNemar |
| Primary score | deterministic: answer names a company present **only** in deleted sentences | cheap, exact, no judge variance |
| Secondary score | blinded fresh-subagent judge, functional rubric (other-company content passes only if it supports the answer to the aspect asked) | catches off-target content the string list misses |
| Judge validation | known-bad controls: C0 answer + one injected sentence translated from that row's deleted span | TPR on items whose correct verdict is known |

## Known limits

- n = 10 rows × 3 reps per condition per arm; fixtures selected for the most
  multi-company content (stress test, not a prevalence estimate).
- One annotator pipeline: two LLM labelers + rules; the 7 disputed passages
  were not human-adjudicated (kept).
- Article titles are not redacted; in row 26 two C0 results keep a title
  naming the removed company with empty content.
- Non-Tavily tools are live, so evidence beyond news can differ between runs.
- Fixture snippets are from 2024–2026 news; the agent may answer with dates
  that differ from today's.
