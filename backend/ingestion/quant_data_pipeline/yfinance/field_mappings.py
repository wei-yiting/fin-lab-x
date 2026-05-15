"""Pure structural lookup tables for yfinance ingestion.

Each table maps a yfinance API key (info dict key) or DataFrame line-item label
to a destination DDL column name. ``INFO_TO_*`` tables additionally carry an
optional converter callable for unit normalization (e.g. fraction → percent).

``YFINANCE_OWNED_COLUMNS`` is derived dynamically from ``YFinanceQuarterlyRow``
so a new column added to the DTO is automatically included in the
column-ownership boundary used by the cross-subsystem upsert isolation guard.
"""

from typing import Any, Callable

from backend.ingestion.quant_data_pipeline.duck_db.row_models import (
    YFinanceQuarterlyRow,
)

# ---------------------------------------------------------------------------
# info dict → CompanyRow / MarketValuationRow
# ---------------------------------------------------------------------------
# lastFiscalYearEnd is intentionally absent — dto_builder.build_company_row
# parses that single Unix timestamp into the two-output (fy_end_month, fy_end_day).

INFO_TO_COMPANY_FIELD: dict[str, tuple[str, Callable[[Any], Any] | None]] = {
    "longName": ("company_name", None),
    "sector": ("sector", None),
    "industry": ("industry", None),
}

# dividendYield has converter=None because yfinance 1.x already returns percent
# (e.g. 0.52 means 0.52%, not 52%). heldPercentInstitutions, in contrast, is
# still a 0..1 fraction in yfinance 1.x and must be scaled to percent.
INFO_TO_MARKET_VALUATION_FIELD: dict[str, tuple[str, Callable[[Any], Any] | None]] = {
    "marketCap": ("market_cap_usd", None),
    "enterpriseValue": ("enterprise_value_usd", None),
    "trailingPE": ("trailing_price_to_earnings", None),
    "forwardPE": ("forward_price_to_earnings", None),
    "priceToBook": ("price_to_book_ratio", None),
    "priceToSalesTrailing12Months": ("price_to_sales_trailing_12m", None),
    "enterpriseToEbitda": ("ev_to_ebitda_ratio", None),
    "trailingPegRatio": ("trailing_peg_ratio", None),
    "dividendYield": ("dividend_yield_pct", None),
    "beta": ("beta", None),
    "heldPercentInstitutions": ("held_pct_institutions", lambda v: v * 100),
}

# ---------------------------------------------------------------------------
# Statement DataFrame line item → YFinanceQuarterlyRow / YFinanceAnnualRow field
# ---------------------------------------------------------------------------
# Three independent dicts — each statement's line-item namespace is its own,
# and merging would obscure provenance when a label collides across statements.

INCOME_LINE_TO_FIELD: dict[str, str] = {
    "Total Revenue": "total_revenue_usd",
    "Cost Of Revenue": "cost_of_revenue_usd",
    "Gross Profit": "gross_profit_usd",
    "Research And Development": "research_and_development_usd",
    "Selling General And Administration": "selling_general_admin_usd",
    "Operating Income": "operating_income_usd",
    "EBIT": "ebit_usd",
    "Net Income": "net_income_usd",
    "Interest Income": "interest_income_usd",
    "Interest Expense": "interest_expense_usd",
    "Tax Provision": "tax_provision_usd",
    "EBITDA": "ebitda_usd",
    "Diluted EPS": "diluted_eps",
    "Diluted Average Shares": "diluted_avg_shares",
}

BALANCE_LINE_TO_FIELD: dict[str, str] = {
    "Total Assets": "total_assets_usd",
    "Goodwill": "goodwill_usd",
    "Net PPE": "net_ppe_usd",
    "Total Debt": "total_debt_usd",
    "Long Term Debt": "long_term_debt_usd",
    "Net Debt": "net_debt_usd",
    "Cash And Cash Equivalents": "cash_and_equivalents_usd",
    "Stockholders Equity": "stockholders_equity_usd",
    "Current Assets": "current_assets_usd",
    "Current Liabilities": "current_liabilities_usd",
    "Accounts Receivable": "accounts_receivable_usd",
    "Inventory": "inventory_usd",
    # deferred_revenue_usd resolved via DEFERRED_REVENUE_FALLBACK chain
}

# capex / stock_buyback / dividends_paid are sign-preserving (negative = cash
# outflow). dto_builder must NOT take abs() on these — downstream analytics
# rely on the sign to distinguish inflow vs outflow.
CASHFLOW_LINE_TO_FIELD: dict[str, str] = {
    "Operating Cash Flow": "operating_cash_flow_usd",
    "Capital Expenditure": "capital_expenditure_usd",
    "Free Cash Flow": "free_cash_flow_usd",
    "Depreciation Amortization Depletion": "depreciation_amortization_usd",
    "Repurchase Of Capital Stock": "stock_buyback_usd",
    "Common Stock Dividend Paid": "dividends_paid_usd",
    "Stock Based Compensation": "stock_based_compensation_usd",
}

# Order matters: try "Deferred Revenue" first, then "Current Deferred Revenue",
# then NULL. Some yfinance balance sheets only expose the current variant.
DEFERRED_REVENUE_FALLBACK: tuple[str, ...] = (
    "Deferred Revenue",
    "Current Deferred Revenue",
)

# ---------------------------------------------------------------------------
# Column-ownership boundary (cross-subsystem upsert isolation)
# ---------------------------------------------------------------------------

_PK_OR_PERIOD_COLUMNS = {
    "ticker",
    "fiscal_year",
    "fiscal_quarter",
    "period_start",
    "period_end",
}
YFINANCE_OWNED_COLUMNS: frozenset[str] = (
    frozenset(YFinanceQuarterlyRow.model_fields.keys()) - _PK_OR_PERIOD_COLUMNS
)
