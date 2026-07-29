"""PROTOTYPE (DEV-121) — TTFT benchmark: blocking vs SSE vs reasoning streaming.

Throwaway measurement script. Answers one question: how much does end-to-end
streaming (and reasoning streaming from DEV-106) shorten user-perceived
time-to-first-token vs the blocking /chat/invoke path?

Usage (server must be running first):
    uv run uvicorn backend.api.main:app --port 8010
    uv run python backend/scripts/ttft_benchmark_prototype.py \
        --base-url http://127.0.0.1:8010 --runs 8 --warmup 2 --mode both

Delete or absorb after DEV-121 captures the numbers.
"""

import argparse
import asyncio
import json
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

QUERIES: dict[str, str] = {
    "quote": "What is NVIDIA's current stock price, and how has it moved today?",
    "financials": (
        "How has Apple's gross margin trended recently? "
        "Use its basic financials and interpret the trend."
    ),
    "sec": "Summarize the main risk factors in Tesla's latest 10-K filing.",
}

# Wire event types considered "user-visible content" for first_visible.
VISIBLE_EVENTS = ("reasoning-delta", "tool-input-available", "text-delta")

STREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=600.0, write=10.0, pool=10.0)


async def run_stream(client: httpx.AsyncClient, base_url: str, query: str) -> dict:
    """One streamed request; first-arrival time (s) per event type."""
    payload = {
        "id": uuid.uuid4().hex,
        "messages": [{"role": "user", "parts": [{"type": "text", "text": query}]}],
        "trigger": "submit-message",
    }
    first_seen: dict[str, float] = {}
    n_events = 0
    finish: float | None = None
    t0 = time.perf_counter()
    async with client.stream(
        "POST", f"{base_url}/api/v1/chat", json=payload, timeout=STREAM_TIMEOUT
    ) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            now = time.perf_counter() - t0
            n_events += 1
            event_type = json.loads(line[len("data:") :]).get("type", "?")
            first_seen.setdefault(event_type, now)
            if event_type == "finish":
                finish = now
    visible = [first_seen[e] for e in VISIBLE_EVENTS if e in first_seen]
    return {
        "first_seen": first_seen,
        "first_visible": min(visible) if visible else None,
        "finish": finish,
        "n_events": n_events,
    }


async def run_invoke(client: httpx.AsyncClient, base_url: str, query: str) -> dict:
    """One blocking request; total wall time == its user-perceived TTFT."""
    t0 = time.perf_counter()
    resp = await client.post(
        f"{base_url}/api/v1/chat/invoke",
        json={"message": query, "session_id": uuid.uuid4().hex},
        timeout=STREAM_TIMEOUT,
    )
    resp.raise_for_status()
    body = resp.json()
    return {
        "total": time.perf_counter() - t0,
        "response_chars": len(body.get("response", "")),
    }


def summarize(values: list[float]) -> dict[str, float] | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return {
        "n": len(present),
        "median": statistics.median(present),
        "mean": statistics.fmean(present),
        "min": min(present),
        "max": max(present),
    }


def summarize_stream_runs(runs: list[dict]) -> dict[str, Any]:
    metrics = {
        "ttfb_any_event": [min(r["first_seen"].values(), default=None) for r in runs],
        "first_reasoning": [r["first_seen"].get("reasoning-delta") for r in runs],
        "first_tool": [r["first_seen"].get("tool-input-available") for r in runs],
        "first_text": [r["first_seen"].get("text-delta") for r in runs],
        "first_visible": [r["first_visible"] for r in runs],
        "finish": [r["finish"] for r in runs],
    }
    return {name: summarize(vals) for name, vals in metrics.items()}


def fmt(stat: dict | None) -> str:
    if stat is None:
        return "-".rjust(22)
    return f"{stat['median']:7.2f}s (n={stat['n']}, {stat['min']:.2f}–{stat['max']:.2f})"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--runs", type=int, default=8)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--invoke-runs", type=int, default=3)
    parser.add_argument("--mode", choices=["stream", "invoke", "both"], default="both")
    parser.add_argument(
        "--queries", nargs="*", default=list(QUERIES), choices=list(QUERIES)
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Result JSON path (default: ttft_results/<timestamp>.json)",
    )
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc).isoformat()
    results: dict[str, Any] = {
        "started_at": started_at,
        "base_url": args.base_url,
        "args": vars(args),
        "queries": {k: QUERIES[k] for k in args.queries},
        "per_query": {},
    }

    async with httpx.AsyncClient() as client:
        for key in args.queries:
            query = QUERIES[key]
            entry: dict[str, Any] = {"stream_runs": [], "invoke_runs": []}
            print(f"\n=== query: {key} ===")

            if args.mode in ("stream", "both"):
                for i in range(args.warmup):
                    print(f"  warmup {i + 1}/{args.warmup} ...", flush=True)
                    await run_stream(client, args.base_url, query)
                for i in range(args.runs):
                    r = await run_stream(client, args.base_url, query)
                    entry["stream_runs"].append(r)
                    print(
                        f"  stream {i + 1}/{args.runs}: "
                        f"visible={r['first_visible']:.2f}s finish={r['finish']:.2f}s "
                        f"({r['n_events']} events)",
                        flush=True,
                    )

            if args.mode in ("invoke", "both"):
                for i in range(args.invoke_runs):
                    r = await run_invoke(client, args.base_url, query)
                    entry["invoke_runs"].append(r)
                    print(
                        f"  invoke {i + 1}/{args.invoke_runs}: total={r['total']:.2f}s",
                        flush=True,
                    )

            entry["stream_summary"] = summarize_stream_runs(entry["stream_runs"])
            entry["invoke_summary"] = summarize(
                [r["total"] for r in entry["invoke_runs"]]
            )
            results["per_query"][key] = entry

    out = Path(
        args.out
        or Path(__file__).parent
        / "ttft_results"
        / f"{started_at.replace(':', '-')}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))

    print("\n================ SUMMARY (median) ================")
    header = f"{'query':<12} {'invoke(blocking)':>24} {'finish':>24} {'first_visible':>24} {'first_reasoning':>24} {'first_text':>24}"
    print(header)
    for key, entry in results["per_query"].items():
        s = entry["stream_summary"]
        print(
            f"{key:<12} {fmt(entry['invoke_summary']):>24} {fmt(s['finish']):>24} "
            f"{fmt(s['first_visible']):>24} {fmt(s['first_reasoning']):>24} {fmt(s['first_text']):>24}"
        )
    print(f"\nRaw results written to {out}")


if __name__ == "__main__":
    asyncio.run(main())
