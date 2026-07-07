"""Companion probe — for selected (ticker, item) cases, dump:
- the FULL prelude
- the first 2 actual block-heading-bordered subsections
So we can judge whether the prelude is genuinely cross-cutting vs just
"the start of the first block".
"""

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


def is_block_heading(line: str) -> bool:
    s = line.strip()
    return (
        s.isupper()
        and 5 <= len(s) <= 120
        and not s.isdigit()
        and not any(c in s for c in {"|", "$", "%"})
    )


def inspect(ticker: str, item: str, label: str) -> None:
    tenk = Company(ticker).get_filings(form="10-K").latest().obj()
    text = tenk[item.lower()]
    lines = text.splitlines()

    # find first non-empty line
    first_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_idx = i
            break

    headings_found: list[tuple[int, str]] = []
    for i in range(first_idx + 1, len(lines)):
        if is_block_heading(lines[i]):
            headings_found.append((i, lines[i].strip()))

    out = []
    out.append(f"=== {ticker} item {item} ===\n")
    out.append(f"first line idx={first_idx}: {lines[first_idx].strip()!r}\n")
    out.append(f"detected block headings (n={len(headings_found)}):\n")
    for i, (idx, h) in enumerate(headings_found[:8]):
        out.append(f"  [{i}] line {idx}: {h!r}\n")
    out.append("\n--- PRELUDE (first heading -> first block heading) ---\n")
    if headings_found:
        prelude = "\n".join(lines[first_idx + 1 : headings_found[0][0]]).strip()
    else:
        prelude = "\n".join(lines[first_idx + 1 :]).strip()
    out.append(prelude[:2500])
    if len(prelude) > 2500:
        out.append(f"\n[... +{len(prelude) - 2500} chars elided ...]\n")
    out.append("\n\n--- FIRST BLOCK (first heading -> second heading) ---\n")
    if len(headings_found) >= 2:
        block1 = "\n".join(
            lines[headings_found[0][0] : headings_found[1][0]]
        ).strip()
        out.append(block1[:1500])
        if len(block1) > 1500:
            out.append(f"\n[... +{len(block1) - 1500} chars elided ...]\n")
    elif len(headings_found) == 1:
        out.append("(only one block heading detected — block extends to end)\n")

    path = f"/tmp/prelude_inspect_{label}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(out))
    print(f"wrote {path}", file=sys.stderr)


def main() -> int:
    # The cases where the algorithm DID find ALL CAPS headings
    inspect("WMT", "7", "WMT_item_7")
    inspect("CAT", "7", "CAT_item_7")
    inspect("CAT", "1A", "CAT_item_1A")
    inspect("ADSK", "1", "ADSK_item_1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
