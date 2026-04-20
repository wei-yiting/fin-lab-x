"""Port gate for is_stub_section.

Manual run (not CI). Reads each fixture under
backend/tests/common/fixtures/stub_samples/ and prints the classification.
Exits 0 iff all fixtures match the expected classification.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow `uv run python backend/scripts/spotcheck_is_stub_section.py` to
# resolve the `backend` package even when the project root is not on
# sys.path (the default for a bare script invocation).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.common.sec_core import is_stub_section  # noqa: E402

FIXTURES_DIR = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "common"
    / "fixtures"
    / "stub_samples"
)

EXPECTED: dict[str, tuple[bool, str | None]] = {
    "aapl_item_11.txt": (True, "incorporated"),
    "aapl_item_1a.txt": (False, None),
    "item_1b_none.txt": (False, None),
    "item_6_reserved.txt": (True, "reserved"),
    "rare_part_stub.txt": (True, "incorporated"),
}


def main() -> int:
    failures: list[str] = []
    for name, (expected_stub, expected_substr) in EXPECTED.items():
        text = (FIXTURES_DIR / name).read_text()
        actual_stub, actual_reason = is_stub_section(text)
        status = "OK"
        if actual_stub != expected_stub:
            status = f"FAIL expected is_stub={expected_stub}, got {actual_stub}"
            failures.append(name)
        elif expected_stub and expected_substr not in (actual_reason or ""):
            status = f"FAIL expected reason substring {expected_substr!r} in {actual_reason!r}"
            failures.append(name)
        elif not expected_stub and actual_reason is not None:
            status = f"FAIL expected reason None, got {actual_reason!r}"
            failures.append(name)
        print(f"[{status}] {name}: is_stub={actual_stub}, reason={actual_reason!r}")
    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("All spot-checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
