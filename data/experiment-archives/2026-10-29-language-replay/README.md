# 2026-10-29 — answer-language fixes, final-answer replay ablation

How much does each of #82's answer-language fixes contribute when every condition sees
byte-identical evidence? The 102 recorded arm-A runs of
[`2026-10-28-language-middleware`](../2026-10-28-language-middleware/) are replayed: the
question and every recorded tool call + result are frozen, and only the final model call
is regenerated under each condition.

Start with [`report.md`](report.md).

| File | What |
|---|---|
| `report.md` | Method, replay fidelity, ladder results, failure languages, cost, claim boundary, reproduce |
| `results.json` | Per-condition pass counts, Wilson 95% CIs, exact McNemar on paired replays, fidelity, cost (from `analyze.py`) |
| `results.csv` | One row per replay: condition, question, recorded run, rep, detected language, pass, recorded language |
| `raw.jsonl.gz` | One JSON line per replay (full regenerated answer, usage), 1020 replays |
| `replay_config.json` | Model config, condition definitions, old/new directive text, removed prompt rule, middleware instruction |

Code: `backend/evals/experiments/language_replay/` at tag
`experiment/2026-10-29-language-replay`.
