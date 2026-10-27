from datetime import date, timedelta

# 52/53-week fiscal calendars end on a weekday nearest a month end, so a period
# can end up to a week into the next month (e.g. FYE "Jan 31" landing on Feb 1).
_DRIFT_DAYS = 7


def snap_period_end(period_end: date) -> date:
    """Map a period end that drifted into the first days of a month back to the
    previous month end; any other date is returned unchanged."""
    if period_end.day <= _DRIFT_DAYS:
        return period_end.replace(day=1) - timedelta(days=1)
    return period_end


def normalize_fiscal_period(
    period_end: date,
    fiscal_year_end_month: int,  # 1-12
) -> tuple[int, int]:
    """Convert a calendar period_end date to (fiscal_year, fiscal_quarter).

    Month-precision after ``snap_period_end``, so 52/53-week drift — within the
    month or up to a week into the next one — resolves to the intended quarter.
    Raises ValueError if period_end is not on a quarter boundary relative to FYE.
    """
    if not 1 <= fiscal_year_end_month <= 12:
        raise ValueError(
            f"fiscal_year_end_month must be 1-12, got {fiscal_year_end_month}"
        )
    snapped = snap_period_end(period_end)
    fye_month = fiscal_year_end_month
    if snapped.month <= fye_month:
        fy = snapped.year
    else:
        fy = snapped.year + 1
        fye_month += 12
    months_before = fye_month - snapped.month
    if months_before % 3 != 0:
        raise ValueError(
            f"period_end {period_end} not quarter-aligned to FYE month "
            f"{fiscal_year_end_month}: delta={months_before} months"
        )
    quarter = 4 - months_before // 3
    return (fy, quarter)
