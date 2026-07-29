# TTFT Benchmark Notes (DEV-121, prototype)

**Question**: How much does end-to-end SSE streaming (and DEV-106 reasoning
streaming) shorten user-perceived time-to-first-token vs the blocking
`/chat/invoke` path?

## Method

- Branch: `metric/streaming-ttft-benchmark` (based on DEV-106
  `feat/multi-provider-streaming-reasoning`), model `openai:gpt-5-mini`,
  `reasoning: on`, localhost server (`uvicorn`, port 8010).
- Script: `../ttft_benchmark_prototype.py`. Per streamed request it records
  first-arrival time of every SSE event type plus `finish`; blocking baseline
  measured against the still-live legacy `/api/v1/chat/invoke` endpoint.
- 3 queries (quote / financials / SEC 10-K) × 2 warmup + 8 stream runs
  + 3 invoke runs, sequential, fresh session id per run.
- "main-equivalent first visible" is derived from the same runs as
  `min(tool-input-available, text-delta)` — i.e. what the user would first see
  without reasoning forwarding (main drops reasoning chunks entirely).

## Results (medians, full-run-1.json, 2026-07-29)

| query      | blocking `/chat/invoke` (X) | stream `finish` | main 1st-visible | DEV-106 1st-visible (Y) |
|------------|----------------------------:|----------------:|-----------------:|------------------------:|
| quote      | 20.7s | 21.1s | 6.6s | 5.7s |
| financials | 36.3s | 37.4s | 6.4s | 4.9s |
| sec        | 98.1s | 60.9s | 5.0s | 3.4s |
| **pooled** | **36.3s** | **37.1s** | **6.1s** | **3.9s** |

## Verdict

- Blocking → streaming: user-perceived TTFT drops from ~21–98s (query-
  dependent; pooled median ~36s) to ~5–7s first visible content (~6×).
- Streaming → reasoning streaming (DEV-106): first visible improves further
  to ~3–6s (pooled median 3.9s, ~1.5× over main) and is far more stable
  across query complexity (sec: 3.4s vs 98s blocking, ~29×).
- Cross-validation: blocking total ≈ stream `finish` (quote 20.7 vs 21.1,
  financials 36.3 vs 37.4) — both measurement paths agree. The sec mismatch
  (98.1 vs 60.9) is n=3 variance on the invoke side (67–170s spread), not a
  measurement artifact.

## Caveats

- Y is seconds, not milliseconds: gpt-5-mini reasons before emitting its first
  reasoning-summary chunk; `MessageStart` is only emitted on the first LLM
  chunk, so ~3–6s is genuine model-side latency, not pipeline buffering.
- Model did not always emit a reasoning summary before its first tool call, so
  per-run first-visible sometimes comes from `tool-input-available`.
- DEV-106 was unmerged at measurement time; re-run after merge for final
  resume numbers.
- Trace coverage verification (Langfuse/Braintrust span completeness for these
  ~40 requests) is still pending — see DEV-121.
