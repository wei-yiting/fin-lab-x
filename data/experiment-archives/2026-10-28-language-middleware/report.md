# Does the answer-language middleware (#82) stop English questions drifting into other languages?

> **One-line takeaway:** On the reader profile (`gpt-5.6-luna`, default/medium reasoning),
> with a 10-K in context, English questions came back in another language in **7 of 78
> runs before #82** (Spanish, Russian, a Japanese phrase) and in **0 of 78 after**
> (Fisher p = 0.014). The new SEC-directive wording alone did **not** fix it (13 of 78
> drifted, p = 0.0001 vs. after); the middleware is the fix. Traditional Chinese
> controls were correct in every arm (24/24 each).

## Results

English questions, 13 questions × 6 reps per arm. "Pass" = the final answer is English
(see [Scorer](#scorer)).

| Arm | What changed | EN pass | Rate | Wilson 95% CI | Questions with ≥1 failure | Wrong languages |
|---|---|---|---|---|---|---|
| **A — before** | pre-#82 SEC directive, no middleware | 71 / 78 | 91.0% | 82.6–95.6% | 5 / 13 | es ×5, ru ×1, ja phrase ×1 |
| **C — wording only** | #82 SEC directive, no middleware | 65 / 78 | 83.3% | 73.5–90.0% | 8 / 13 | es ×9, ru ×3, ja ×1 |
| **B — after (#82)** | #82 SEC directive + `ResponseLanguageMiddleware` | **78 / 78** | **100%** | 95.3–100% | **0 / 13** | — |

Two-sided Fisher exact test on EN pass counts: A vs B p = 0.014; C vs B p = 0.0001;
A vs C p = 0.23 (no detectable difference between the two directive wordings).

Traditional Chinese controls (4 questions × 6 reps): A 24/24, B 24/24, C 24/24 in
Traditional Chinese.

In 77 of 78 arm-A EN runs, 78/78 arm-B runs and 78/78 arm-C runs, SEC tool output
(10-K text wrapped by the language directive) was in context when the answer was
written. The one exception (A, d07 rep 3, Tavily-only) passed.

### Failure examples (all 20 checked by hand)

| Run | Question (abridged) | Answer opens with |
|---|---|---|
| A d06 r2 | J&J's biggest litigation risk… | "**Conclusión:** el mayor riesgo litigioso actual de Johnson & Johnson es el litigio por talco…" |
| A d07 r1 | Google's antitrust risk… | "**Коротко:** антимонопольный риск Google уже перешёл…" (Russian) |
| A s1 r5 | NVIDIA export-control risks (starter prompt) | English, but with a Japanese phrase mid-sentence: "from "potential" to "実際に表面化"" |
| C d07 r2 | Google's antitrust risk… | "**結論：Google の反トラスト・リスクは…**" (Japanese) |
| C d17 r4 | Amazon advertising… | Starts "**Conclusión:**" then one English sentence, then the body switches to Spanish |

Drift clusters on certain questions: J&J litigation (d06) failed 2/6 in A and 3/6 in C.
Every failure was in an answer that had 10-K text in context.

## Setup

- **Agent:** production `reader` profile, unmodified: `openai:gpt-5.6-luna`, `reasoning: on`,
  no explicit effort (= API default, medium), 10-tool-call budget, tools: Finnhub ×2,
  Tavily, `sec_filing_list_sections`, `sec_filing_get_section`, `sec_filing_search`.
  System prompt is reader's, which already had the language policy before #82.
- **Arms** (one process per arm, because the directive text is a module global read at
  tool-call time; production code is untouched and arms A/C are monkeypatched inside the
  experiment process only; the resolved values are in `configs/arm_*_resolved.json`):
  - A: `_LANGUAGE_DIRECTIVE_PRE/POST` in `sec_filing_tools` and `sec_filing_search` restored
    to the pre-#82 text ("The following SEC filing content is in English… regardless of
    the language of this content"); `ResponseLanguageMiddleware` replaced by a no-op.
  - B: main at `22bff15` (includes #82), unpatched.
  - C: #82 directive text; middleware replaced by a no-op.
- **Questions (17):** 13 English: 10 SEC/mixed-source rows of
  `scenarios/baseline_behavior_diagnostic/dataset.csv` (ids 6, 7, 8, 11, 12, 13, 15, 16,
  17, 18; verbatim) + the three 10-K starter prompts added in #82. 4 Traditional Chinese
  controls: rows 6, 11, 15 of the zh diagnostic dataset + #82's UAT question. Full list in
  `backend/evals/experiments/language_middleware/questions.py`.
- **Reps / order:** 6 reps per question per arm, 306 runs. The three arms ran
  concurrently; within each arm, jobs were ordered row-major. Reps 1–3 ran at
  concurrency 5 per arm, reps 4–6 at concurrency 2 per arm (see
  [Set-aside batch](#set-aside-batch)). SEC caches were pre-warmed for all 14 tickers first.
- **Answer extracted:** the final AIMessage's text blocks only (`AIMessage.text`). The
  orchestrator's `_extract_result` `str()`s list content, which would include the
  (always-English) reasoning summaries and bias the scorer toward English.

### Scorer

Deterministic, no LLM (`scorer.py`). URLs and reference lines are stripped. Then:
kana ≥ 10 → ja; Hangul → ko; Cyrillic-dominant → ru; CJK-dominant (2 Latin letters per
CJK char) → zh, split into zh-Hant / zh-Hans with the `language_policy` scenario's
`response_no_simplified_chars`. Otherwise, function-word counts pick en / es / pt / fr /
de / it. An English question passes only if the answer is `en` with no kana or Hangul
and Han characters ≤ 2% of letters. A Chinese question passes only if the answer is
`zh-Hant` with Han share ≥ 30%. All 20 failures were read by hand: each is a real
non-English answer or a non-English phrase inside one.

## Cost

US$1.41 model spend for the 306 reported runs (A $0.47, B $0.48, C $0.47; median 19K
input tokens per run, max 57K). Including the set-aside batch ($0.58), the smoke run, and
a batch killed after a scorer bug, total spend was ≈ US$2.1 at list prices
($0.20 / $0.02 cached / $1.20 per 1M input/cached/output tokens, from the
2026-10-22 model benchmark). Tavily and Finnhub calls are excluded.

## Claim boundary

What this shows:
- On this question set and profile, the post-#82 system answered English questions in
  English in every run (78/78; with zero failures, the 95% upper bound on the residual
  drift rate is ~4.7%), and the pre-#82 system did not (7/78).
- The middleware is what fixes it. The directive rewording alone made no detectable
  difference (A vs C p = 0.23; C's point estimate is worse).

What it does not show:
- **The before rate is lower than the deck's "2 of 4 drifting per run".** That manual
  check ran on the baseline profile, which before #82 used `gpt-5-nano` and a Chinese
  example in its prompt. Here, arm A holds the model and prompt at reader's current
  values, so it isolates the directive and middleware and leaves out the model and
  prompt changes #82 also made to baseline. The ~9% here is a per-run rate on
  `gpt-5.6-luna`. Do not quote it as the rate users saw on the old baseline.
- Runs are not independent. Six reps of the same question are correlated (drift
  clusters on d06), so the Wilson intervals, which treat runs as independent, are
  somewhat too narrow. The question-level view (5/13 and 8/13 questions failed at least
  once in A and C, 0/13 in B) is the more conservative reading.
- Only one-turn questions, so no multi-turn language switches; only English and
  Traditional Chinese inputs; one model. Answer quality and correctness were not scored.
- Latency medians (A 18.2 s, B 21.2 s, C 18.2 s) are reported for completeness. This
  design does not attribute latency to the middleware: the arms share a process
  budget, and EDGAR and Tavily latency varies.

## Set-aside batch

The first attempt at reps 4–6 started right after a killed batch. SEC EDGAR
rate-limited nearly every SEC call ("Rate-limited by SEC EDGAR"), so most runs answered
without 10-K text, which is not the condition under test. All 153 records are kept in
`raw_batch2_edgar_ratelimited.jsonl.gz` and excluded from the tables. For what it's worth,
the same pattern held there: EN A 37/39, B 39/39, C 37/39. Reps 4–6 were then re-run at
lower concurrency. 18 of the 306 reported runs had at least one rate-limited SEC call
but still had 10-K text from another call.

## Reproduce

```bash
git checkout experiment/2026-10-28-language-middleware
uv sync --extra dev
set -a; source backend/.env; set +a        # OPENAI, TAVILY, FINNHUB, EDGAR_IDENTITY; Qdrant on :6333
python -m backend.evals.experiments.language_middleware.run --prewarm
for a in A B C; do
  python -m backend.evals.experiments.language_middleware.run --arm $a --reps 6 --concurrency 2 \
    --out data/experiment-archives/2026-10-28-language-middleware/raw &
done; wait
python -m backend.evals.experiments.language_middleware.analyze data/experiment-archives/2026-10-28-language-middleware
```

`analyze.py` reads `raw/*.json` if present, else `raw.jsonl.gz` (this archive). Re-running
it on the archive reproduces `results.json` exactly.
