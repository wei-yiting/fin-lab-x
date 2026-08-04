"""Dump the raw Langfuse trace JSON for inspection."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / "backend" / ".env")

import base64
import urllib.request


def main(trace_id: str) -> int:
    base = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    pk = os.environ["LANGFUSE_PUBLIC_KEY"]
    sk = os.environ["LANGFUSE_SECRET_KEY"]
    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/api/public/traces/{trace_id}",
        headers={"Authorization": f"Basic {auth}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    summary = {
        "trace_id": data.get("id"),
        "trace_metadata_keys": sorted((data.get("metadata") or {}).keys()),
        "trace_session_id": data.get("sessionId"),
        "trace_status": (data.get("metadata") or {}).get("status"),
        "observations": [],
    }
    for obs in data.get("observations") or []:
        summary["observations"].append({
            "id": obs.get("id"),
            "type": obs.get("type"),
            "name": obs.get("name"),
            "parent": obs.get("parentObservationId"),
            "metadata_keys": sorted((obs.get("metadata") or {}).keys()),
            "reasoning_present": "reasoning" in (obs.get("metadata") or {}),
            "reasoning_value_excerpt": (
                ((obs.get("metadata") or {}).get("reasoning") or "")[:80]
                if isinstance((obs.get("metadata") or {}).get("reasoning"), str)
                else (obs.get("metadata") or {}).get("reasoning")
            ),
            "reasoning_tail_aborted": (obs.get("metadata") or {}).get(
                "reasoning_tail_aborted"
            ),
            "model": (obs.get("metadata") or {}).get("ls_model_name")
            or obs.get("model"),
        })
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
