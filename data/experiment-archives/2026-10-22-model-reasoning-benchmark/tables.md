## Arm summary (per-row means over repetitions; 95% CI = row-level bootstrap)

| Arm | Rows × reps | Task errors | Health mean [95% CI] | Median E2E s [95% CI] | Median TTFT s | Median tool calls | Median LLM calls | Median input tok | Median output tok | Median reasoning tok | Mean cost/run USD [95% CI] | Total cost USD | Hard tool errors/run | Runs at tool budget | Simplified-drift runs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luna_none | 30 × 3 | 0 | 0.91 [0.81, 0.99] | 27.3 [24.0, 31.4] | 2.2 | 6.0 | 3.0 | 38553 | 2022 | 0 | 0.0142 [0.0067, 0.0253] | 1.28 | 0.12 | 6 | 0 |
| luna_medium | 30 × 3 | 0 | 0.90 [0.79, 0.99] | 38.0 [35.1, 42.3] | 2.5 | 7.2 | 3.0 | 43749 | 2720 | 494 | 0.0161 [0.0091, 0.0260] | 1.45 | 0.14 | 9 | 1 |
| gemini_minimal | 30 × 3 | 0 | 0.97 [0.90, 1.00] | 15.1 [13.2, 16.8] | 1.4 | 3.7 | 2.8 | 12717 | 1421 | 0 | 0.0190 [0.0157, 0.0228] | 1.71 | 0.07 | 0 | 0 |
| gemini_medium | 30 × 3 | 0 | 0.99 [0.96, 1.00] | 31.5 [29.1, 33.8] | 2.0 | 4.5 | 3.0 | 15162 | 4345 | 2854 | 0.0303 [0.0275, 0.0336] | 2.73 | 0 | 2 | 1 |

## Run-to-run variability (same row, same arm, different repetition)

| Arm | Rows where health is identical across reps | Median within-row E2E CV | Median within-row SD of tool calls |
|---|---|---|---|
| luna_none | 93% | 0.14 | 0.58 |
| luna_medium | 93% | 0.13 | 0.58 |
| gemini_minimal | 100% | 0.14 | 0.58 |
| gemini_medium | 97% | 0.10 | 0.58 |

## Paired contrasts (mean per-row difference, treatment − control, 95% CI)

| Contrast | Treatment − control | Δ health | Δ E2E s | Δ cost/run USD | Δ tool calls |
|---|---|---|---|---|---|
| reasoning, Luna | luna_medium − luna_none | -0.01 [-0.07, +0.04] | +11.5 [+8.8, +14.2] | +0.0019 [-0.0002, +0.0037] | +0.5 [+0.0, +1.0] |
| reasoning, Gemini | gemini_medium − gemini_minimal | +0.02 [-0.03, +0.10] | +17.1 [+15.3, +19.4] | +0.0113 [+0.0077, +0.0152] | +0.9 [+0.5, +1.5] |
| family, low tier | gemini_minimal − luna_none | +0.06 [-0.03, +0.17] | -11.7 [-14.6, -8.9] | +0.0048 [-0.0071, +0.0132] | -2.2 [-2.8, -1.6] |
| family, medium tier | gemini_medium − luna_medium | +0.09 [-0.00, +0.20] | -6.0 [-9.2, -2.8] | +0.0142 [+0.0054, +0.0206] | -1.8 [-2.4, -1.1] |

## Health mean by expected best source

| Source | luna_none | luna_medium | gemini_minimal | gemini_medium |
|---|---|---|---|---|
| Finnhub | 1.00 | 0.93 | 1.00 | 1.00 |
| SEC | 1.00 | 1.00 | 1.00 | 1.00 |
| Tavily | 0.67 | 0.50 | 0.75 | 1.00 |
| mixed | 0.89 | 0.94 | 1.00 | 0.97 |
