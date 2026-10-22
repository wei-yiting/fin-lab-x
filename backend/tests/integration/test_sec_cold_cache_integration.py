"""SEC EDGAR integration tests that run against an empty edgartools cache.

edgartools keeps a persistent HTTP cache (``~/.edgar/_tcache``) that caches
``/Archives/edgar/data`` responses forever. A developer machine therefore
keeps serving filings it fetched long ago even after EDGAR stops answering
the request edgartools makes — which is how an EDGAR-side 403 on the
filing-index URL went unnoticed while every other sec_integration test
stayed green (DEV-219). These tests run each fetch in a subprocess whose
``EDGAR_LOCAL_DATA_DIR`` points at a fresh temp dir, so nothing can be
served from cache. A subprocess is needed because edgartools builds its
HTTP client and cache location once, at import time.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.sec_integration

_REPO_ROOT = Path(__file__).resolve().parents[3]

# A filing that is not special in any way: the bug this guards against hit
# every uncached filing, META's was simply one the benchmark needed.
_TICKER = "META"

_PROBE = textwrap.dedent(
    """
    import json, sys

    from backend.agent_engine.tools import setup_tools
    from backend.agent_engine.tools.registry import get_tool
    from backend.ingestion.sec_filing_pipeline_html.sec_downloader import SECDownloader

    ticker = sys.argv[1]
    setup_tools()
    list_sections = get_tool("sec_filing_list_sections")
    message = list_sections.invoke(
        {
            "args": {"ticker": ticker},
            "name": list_sections.name,
            "type": "tool_call",
            "id": "cold-cache-probe",
        }
    )
    raw = SECDownloader().download(ticker, "10-K", None)
    print(
        json.dumps(
            {
                "list_sections_status": message.status,
                "list_sections_content": message.content,
                "raw_html_chars": len(raw.raw_html or ""),
            }
        )
    )
    """
)


@pytest.fixture(autouse=True)
def _require_edgar_identity():
    if not os.getenv("EDGAR_IDENTITY"):
        pytest.skip("EDGAR_IDENTITY not set")


def _run_cold(tmp_path: Path) -> dict:
    env = {**os.environ, "EDGAR_LOCAL_DATA_DIR": str(tmp_path / "edgar")}
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE, _TICKER],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_both_sec_paths_read_an_uncached_10k(tmp_path: Path) -> None:
    result = _run_cold(tmp_path)

    # Whole-section path (sec_filing_list_sections / get_section).
    assert result["list_sections_status"] == "success", result["list_sections_content"][
        :500
    ]
    sections = json.loads(result["list_sections_content"])["sections"]
    assert any(section["key"] == "1a" for section in sections)

    # Retrieval path: JIT ingestion's download step (sec_filing_search).
    assert result["raw_html_chars"] > 100_000
