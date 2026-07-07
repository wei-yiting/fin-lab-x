"""Quick probe — check `filing.markdown()` output, comparing access via
``tenk.filing`` vs the original Filing object."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "backend" / ".env")
sys.path.insert(0, str(REPO_ROOT))

from edgar import Company, set_identity  # noqa: E402

set_identity(os.environ["EDGAR_IDENTITY"])


def probe(ticker: str) -> None:
    company = Company(ticker)
    filings = company.get_filings(form="10-K")
    filing = filings.latest()
    print(f"-- {ticker} --")
    print(f"  filing repr: {repr(filing)[:120]}")
    # via filing.obj() then .filing
    tenk = filing.obj()
    md_via_tenk = tenk.filing.markdown()
    md_via_direct = filing.markdown()
    print(f"  via tenk.filing.markdown(): {len(md_via_tenk)} chars")
    print(f"  via filing.markdown(): {len(md_via_direct)} chars")
    print(f"  same object? {tenk.filing is filing}")

    # Check first 5 lines of each
    for label, md in [("tenk.filing.md", md_via_tenk), ("filing.md", md_via_direct)]:
        if md:
            lines = md.splitlines()[:5]
            print(f"    {label} first 5 lines: {lines}")
        else:
            print(f"    {label}: EMPTY")


def main() -> int:
    for t in ["ADSK", "JPM", "JNJ", "WMT", "XOM", "CAT"]:
        try:
            probe(t)
        except Exception as exc:
            print(f"{t}: ERROR {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
