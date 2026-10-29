# Slide: Replaying recorded tool outputs to test one failure in isolation

**Failure from traces:** asked about company X, the agent wove in news about an unrelated company Y that the news search returned alongside X's news.

**Method — freeze the evidence, vary one thing**

```
recorded Tavily results (real snippets, X news mixed with other companies)
   ├─ C1: unchanged
   └─ C0: same text, unrelated-company sentences cut   ← only difference
replay tool = same name / description / args schema as live Tavily (sha256 match)
same question · same config · SEC + Finnhub live → grade the final answer
```

- 1,067 snippet sentences labeled by two LLM labelers (κ = 0.81); 62 consensus-unrelated sentences cut
- 10 questions × {C0, C1} × 3 reps, paired; raw JSON per run
- Scored two ways: string check for cut-only companies + blinded LLM judge (functional rubric)

**Results**

| | C1 off-target | C0 off-target |
|---|---|---|
| Reader · Luna medium (primary) | **0 / 30** | 0 / 30 |
| Reader · Luna none (exploratory) | 0 / 30 | 0 / 30 |
| News-recap questions · Luna medium (exploratory) | 0 / 30 | 0 / 30 |

- Distractors reached the model: 29 / 30 primary runs were served the cut content
- Judge is sensitive: **7 / 7** injected off-target sentences caught
- String check over-counts (3 hits, all legitimate context, e.g. TSMC's customers) → judge layer needed

**Takeaway:** the current reader config filters this distractor type; the failure did not reproduce under controlled evidence (C1 rate < 12 %, 95 % bound). Next: harder distractors and the question types seen in traces.

*MVP, n = 10 questions; LLM labels, no human spot check yet; only Tavily replayed.*
