## Arm summary (per-row means over repetitions; 95% CI = row-level bootstrap)

| Arm | Rows × reps | Task errors | Health mean [95% CI] | Median E2E s [95% CI] | Median TTFT s | Median tool calls | Median LLM calls | Median input tok | Median output tok | Median reasoning tok | Mean cost/run USD [95% CI] | Total cost USD | Hard tool errors/run | Runs at tool budget | Simplified-drift runs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reader_luna_none | 30 × 3 | 0 | 0.97 [0.90, 1.00] | 18.5 [17.1, 21.4] | 2.6 | 4.0 | 2.0 | 13564 | 1558 | 0 | 0.0038 [0.0034, 0.0043] | 0.35 | 0.07 | 0 | 2 |
| reader_luna_medium | 30 × 3 | 0 | 0.92 [0.82, 1.00] | 24.5 [21.5, 27.5] | 2.2 | 4.8 | 2.7 | 22489 | 2153 | 487 | 0.0053 [0.0047, 0.0060] | 0.48 | 0.14 | 4 | 0 |
| reader_gemini_minimal | 30 × 3 | 0 | 0.97 [0.90, 1.00] | 15.0 [13.9, 15.9] | 1.7 | 3.0 | 2.0 | 17447 | 1637 | 0 | 0.0192 [0.0178, 0.0205] | 1.72 | 0.07 | 0 | 2 |
| reader_gemini_medium | 30 × 3 | 0 | 0.97 [0.90, 1.00] | 34.6 [31.6, 37.0] | 2.1 | 4.0 | 2.3 | 20441 | 5291 | 3605 | 0.0337 [0.0315, 0.0361] | 3.03 | 0.09 | 0 | 0 |

## Run-to-run variability (same row, same arm, different repetition)

| Arm | Rows where health is identical across reps | Median within-row E2E CV | Median within-row SD of tool calls |
|---|---|---|---|
| reader_luna_none | 100% | 0.10 | 0.29 |
| reader_luna_medium | 97% | 0.12 | 0.58 |
| reader_gemini_minimal | 100% | 0.12 | 0.58 |
| reader_gemini_medium | 100% | 0.14 | 0.58 |

## Paired contrasts (mean per-row difference, treatment − control, 95% CI)

| Contrast | Treatment − control | Δ health | Δ E2E s | Δ cost/run USD | Δ tool calls |
|---|---|---|---|---|---|
| vs control: Luna, no reasoning | reader_luna_none − reader_luna_medium | +0.04 [+0.00, +0.12] | -5.9 [-8.1, -3.7] | -0.0015 [-0.0020, -0.0010] | -0.9 [-1.4, -0.3] |
| vs control: Gemini minimal | reader_gemini_minimal − reader_luna_medium | +0.04 [+0.00, +0.12] | -10.3 [-12.8, -8.0] | +0.0138 [+0.0127, +0.0150] | -1.5 [-2.0, -1.1] |
| vs control: Gemini medium | reader_gemini_medium − reader_luna_medium | +0.04 [+0.00, +0.12] | +8.6 [+6.3, +10.7] | +0.0283 [+0.0266, +0.0303] | -0.8 [-1.2, -0.3] |
| reasoning, Gemini | reader_gemini_medium − reader_gemini_minimal | +0.00 [+0.00, +0.00] | +18.9 [+17.0, +21.0] | +0.0145 [+0.0127, +0.0163] | +0.7 [+0.5, +1.0] |
| family, low tier | reader_gemini_minimal − reader_luna_none | +0.00 [+0.00, +0.00] | -4.5 [-6.4, -2.8] | +0.0153 [+0.0141, +0.0165] | -0.7 [-1.1, -0.3] |

## Health mean by expected best source

| Source | reader_luna_none | reader_luna_medium | reader_gemini_minimal | reader_gemini_medium |
|---|---|---|---|---|
| Finnhub | 1.00 | 1.00 | 1.00 | 1.00 |
| SEC | 1.00 | 1.00 | 1.00 | 1.00 |
| Tavily | 0.75 | 0.75 | 0.75 | 0.75 |
| mixed | 1.00 | 0.89 | 1.00 | 1.00 |

## Citations and SEC path

| Arm | Runs | Runs with [N] citations | Bijective (inline ↔ defs) | SEC path (runs) |
|---|---|---|---|---|
| reader_luna_none | 90 | 90 | 90 | neither 3, search_only 87 |
| reader_luna_medium | 90 | 87 | 87 | both 2, neither 5, search_only 83 |
| reader_gemini_minimal | 90 | 89 | 86 | both 1, neither 6, search_only 83 |
| reader_gemini_medium | 90 | 90 | 89 | both 2, neither 9, search_only 79 |
