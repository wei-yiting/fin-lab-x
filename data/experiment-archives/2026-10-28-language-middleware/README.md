# 2026-10-28 — answer-language middleware (#82) before/after

Does #82's `ResponseLanguageMiddleware` stop English questions from being answered in
another language once a 10-K is in context, and does it need the new SEC-directive
wording to do it?

Start with [`report.md`](report.md).

| File | What |
|---|---|
| `report.md` | Setup, results, failure examples, cost, claim boundary, reproduce |
| `results.json` | Per-arm pass counts, Wilson 95% CIs, Fisher tests, cost (from `analyze.py`) |
| `results.csv` | One row per run: arm, question, rep, detected language, pass, SEC-in-context, cost |
| `raw.jsonl.gz` | One JSON line per run (full answer, tool outputs, token usage), 306 runs |
| `configs/` | Each arm's resolved directive text, middleware and model config |
| `raw_batch2_edgar_ratelimited.jsonl.gz` | First attempt at reps 4–6, set aside: SEC EDGAR rate-limited most SEC calls, so the 10-K condition wasn't met (see report) |

Code: `backend/evals/experiments/language_middleware/` at tag
`experiment/2026-10-28-language-middleware`.
