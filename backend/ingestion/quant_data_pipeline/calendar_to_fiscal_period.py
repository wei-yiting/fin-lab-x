from datetime import date


def normalize_fiscal_period(
    period_end: date,
    fiscal_year_end_month: int,  # 1-12
) -> tuple[int, int]:
    """Convert a calendar period_end date to (fiscal_year, fiscal_quarter).

    Month-precision (day is ignored) to tolerate 52/53-week calendar drift.
    Raises ValueError if period_end is not on a quarter boundary relative to FYE.
    """
    fye_month = fiscal_year_end_month
    if period_end.month <= fye_month:
        fy = period_end.year
    else:
        fy = period_end.year + 1
        fye_month += 12
    months_before = fye_month - period_end.month
    if months_before % 3 != 0:
        raise ValueError(
            f"period_end {period_end} not quarter-aligned to FYE month "
            f"{fiscal_year_end_month}: delta={months_before} months"
        )
    quarter = 4 - months_before // 3
    return (fy, quarter)
