# 2026-10-29 — off-target company, controlled replay eval (MVP)

Does answer synthesis keep unrelated-company news out of the answer when it is
in the evidence? Recorded Tavily outputs replayed through a mocked tool, C1
(original) vs C0 (unrelated sentences cut). Tag `experiment/2026-10-29-off-target-distractor`.

Start with [report.md](report.md). Then:

| Path | What |
|---|---|
| [DESIGN_NOTE.md](DESIGN_NOTE.md) | design as run, decisions, known limits |
| [slide_summary.md](slide_summary.md) | one-slide summary of method and numbers |
| `raw.tar.gz` | one JSON per run: `raw/<arm>/rep<K>/row<NN>__<C0/C1>.json` (answer, tool outputs, replay log) |
| `score_<arm>.json` | deterministic leak score per arm |
| `judge/`, `judge_recap/` | blinded batches, prompt, key, per-batch verdicts, `judge_scores.json` |
| `resolved_<arm>.json` | resolved config per arm (incl. tool-contract hashes) |
| `run_*.log` | run logs |

Fixtures: `backend/evals/experiments/off_target_distractor/fixtures.json`;
labels and labeling guide: `artifacts/current/off_target_labeling/`.
