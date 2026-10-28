from datetime import date

import pytest

from backend.ingestion.fundamentals_pipeline.calendar_to_fiscal_period import (
    normalize_fiscal_period,
    snap_period_end,
)


# fmt: off
@pytest.mark.parametrize(
    "fye_month, period_end, expected",
    [
        pytest.param(9,  date(2024, 6, 30), (2024, 3), id="AAPL-Q3-FY24"),
        pytest.param(9,  date(2024, 9, 28), (2024, 4), id="AAPL-Q4-FY24"),
        pytest.param(9,  date(2024, 12, 31),(2025, 1), id="AAPL-Q1-FY25"),
        pytest.param(12, date(2024, 3, 31), (2024, 1), id="AMZN-Q1-FY24"),
        pytest.param(12, date(2024, 12, 31),(2024, 4), id="AMZN-Q4-FY24"),
        pytest.param(6,  date(2024, 6, 30), (2024, 4), id="MSFT-Q4-FY24"),
        pytest.param(6,  date(2024, 9, 30), (2025, 1), id="MSFT-Q1-FY25"),
        pytest.param(1,  date(2024, 1, 28), (2024, 4), id="NVDA-Q4-FY24"),
        pytest.param(1,  date(2024, 4, 30), (2025, 1), id="NVDA-Q1-FY25"),
        pytest.param(1,  date(2025, 1, 31), (2025, 4), id="CRM-Q4-FY25"),
        pytest.param(1,  date(2026, 2, 1),  (2026, 4), id="5253wk-FYE-drifts-to-Feb-1"),
        pytest.param(8,  date(2024, 9, 1),  (2024, 4), id="COST-FY24-ends-Sep-1"),
        pytest.param(9,  date(2022, 10, 1), (2022, 4), id="DIS-FY22-ends-Oct-1"),
    ],
)
# fmt: on
def test_normalize_fiscal_period_golden(
    fye_month: int, period_end: date, expected: tuple[int, int]
) -> None:
    assert normalize_fiscal_period(period_end, fye_month) == expected


@pytest.mark.parametrize(
    "fye_month, period_end, match_fragment",
    [
        pytest.param(
            9,
            date(2024, 7, 15),
            "delta=",
            id="misaligned-2mo",
        ),
        pytest.param(
            9,
            date(2024, 11, 30),
            "delta=",
            id="misaligned-10mo",
        ),
    ],
)
def test_normalize_fiscal_period_raises(
    fye_month: int, period_end: date, match_fragment: str
) -> None:
    with pytest.raises(ValueError, match=match_fragment):
        normalize_fiscal_period(period_end, fye_month)
    with pytest.raises(ValueError, match=str(period_end)):
        normalize_fiscal_period(period_end, fye_month)


@pytest.mark.parametrize(
    "raw, expected",
    [
        pytest.param(date(2026, 2, 1), date(2026, 1, 31), id="day1-snaps-back"),
        pytest.param(date(2026, 3, 7), date(2026, 2, 28), id="day7-snaps-back"),
        pytest.param(date(2026, 3, 8), date(2026, 3, 8), id="day8-unchanged"),
        pytest.param(date(2026, 9, 27), date(2026, 9, 27), id="month-end-drift"),
    ],
)
def test_snap_period_end(raw: date, expected: date) -> None:
    assert snap_period_end(raw) == expected


@pytest.mark.parametrize("bad_month", [0, 13, -1, 100])
def test_normalize_fiscal_period_rejects_out_of_range_month(bad_month):
    with pytest.raises(ValueError, match="must be 1-12"):
        normalize_fiscal_period(date(2024, 6, 30), bad_month)
