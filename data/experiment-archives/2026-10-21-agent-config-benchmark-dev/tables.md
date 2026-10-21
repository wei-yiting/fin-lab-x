## E1 paired (A = luna_medium, no RAG / B = reader_luna_medium, RAG bundle)

Cells are `A / B`.

| Row | Expected source | SEC path | Tool calls | search calls | get_section calls | Hard tool errors | SEC evidence tokens | Input tokens | Output tokens | TTFT s | E2E s | Cost USD | Health | No-simplified | [N] bijective |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | mixed | neither / search_only | 6 / 5 | 0 / 1 | 0 / 0 | 0 / 0 | 0 / 4962 | 16939 / 25420 | 2006 / 1475 | 3.0 / 1.9 | 38.4 / 26.1 | 0.0040 / 0.0040 | 1.0 / 1.0 | 1.0 / 1.0 | ✓ / ✓ |
| 6 | SEC | get_section_only / search_only | 6 / 2 | 0 / 1 | 4 / 0 | 0 / 0 | 70998 / 5341 | 79330 / 12228 | 3313 / 2602 | 4.7 / 2.1 | 48.0 / 30.2 | 0.0186 / 0.0045 | 1.0 / 1.0 | 1.0 / 1.0 | ✓ / ✓ |
| 9 | mixed | get_section_only / search_only | 10 / 7 | 0 / 3 | 2 / 0 | 2 / 2 | 16331 / 5358 | 58831 / 28246 | 3819 / 2906 | 3.9 / 2.4 | 64.6 / 41.9 | 0.0102 / 0.0061 | 0.0 / 0.0 | 1.0 / 1.0 | ✓ / ✓ |
| 13 | SEC | neither / search_only | 11 / 12 | 0 / 2 | 0 / 0 | 5 / 4 | 0 / 28 | 21545 / 43245 | 2308 / 2830 | 2.8 / 1.8 | 49.3 / 47.6 | 0.0046 / 0.0063 | 0.0 / 0.0 | 1.0 / 1.0 | ✓ / ✓ |
| 17 | mixed | get_section_only / search_only | 7 / 4 | 0 / 4 | 3 / 0 | 0 / 0 | 41103 / 17582 | 52916 / 41350 | 4527 / 3143 | 4.0 / 3.4 | 64.7 / 33.0 | 0.0145 / 0.0079 | 1.0 / 1.0 | 1.0 / 1.0 | – / ✓ |
| 20 | Finnhub | get_section_only / search_only | 5 / 3 | 0 / 1 | 2 / 0 | 0 / 0 | 52695 / 4651 | 61093 / 11164 | 1830 / 1220 | 2.6 / 1.7 | 27.9 / 13.7 | 0.0132 / 0.0026 | 1.0 / 1.0 | 1.0 / 1.0 | ✓ / ✓ |
| 24 | Finnhub | neither / search_only | 6 / 8 | 0 / 2 | 0 / 0 | 0 / 0 | 0 / 9772 | 7473 / 27256 | 2333 / 2310 | 3.7 / 4.7 | 36.1 / 35.0 | 0.0037 / 0.0059 | 1.0 / 1.0 | 1.0 / 1.0 | – / ✓ |
| 29 | mixed | neither / search_only | 8 / 9 | 0 / 2 | 0 / 0 | 0 / 2 | 0 / 4426 | 13740 / 39261 | 3238 / 3393 | 3.1 / 2.3 | 52.1 / 51.6 | 0.0051 / 0.0070 | 1.0 / 0.0 | 1.0 / 1.0 | ✓ / ✓ |

## E1 aggregate (8 complete pairs)

| Metric | A (no RAG) | B (RAG bundle) |
|---|---|---|
| Median SEC evidence tokens | 8165.5 | 5151.5 |
| Median input tokens | 37230.5 | 27751.0 |
| Median output tokens | 2785.5 | 2716.0 |
| Median tool calls | 6.5 | 6.0 |
| Median TTFT s | 3.4 | 2.2 |
| Median E2E s | 48.7 | 34.0 |
| Hard tool errors (sum) | 7 | 8 |
| Total cost USD | 0.0739 | 0.0443 |
| Runs with health 1.0 | 6 | 5 |
| B's SEC path | – | search_only: 8 |

## E2 summary (dev 8 rows each, n=1)

| Arm | Runs | Health mean | Task errors | Hard tool errors | Runs at tool budget | Median tool calls | Median LLM calls | Median TTFT s | Median E2E s | Median input tok | Median output tok | Median reasoning tok | Total cost USD | Simplified-drift runs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luna_none | 8 | 0.62 | 0 | 7 | 1 | 6.0 | 2.5 | 4.7 | 28.8 | 14564 | 1818 | 0 | 0.0482 | 0 |
| luna_medium | 8 | 0.75 | 0 | 7 | 2 | 6.5 | 3.0 | 3.4 | 48.7 | 37230 | 2786 | 568 | 0.0739 | 0 |
| gemini_minimal | 8 | 0.75 | 0 | 5 | 0 | 4.0 | 3.0 | 1.6 | 16.6 | 17882 | 1436 | 0 | 0.1692 | 0 |
| gemini_medium | 8 | 0.88 | 0 | 4 | 1 | 6.5 | 4.0 | 2.0 | 33.9 | 18494 | 4397 | 2568 | 0.2706 | 0 |
