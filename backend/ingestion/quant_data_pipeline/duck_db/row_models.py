from datetime import date

from pydantic import BaseModel


class CompanyRow(BaseModel):
    """yfinance owner — table: companies — excludes: updated_at."""

    ticker: str
    company_name: str
    sector: str | None = None
    industry: str | None = None
    fy_end_month: int
    fy_end_day: int


class MarketValuationRow(BaseModel):
    """yfinance owner — table: market_valuations — excludes: updated_at."""

    ticker: str
    as_of_date: date
    market_cap_usd: int | None = None
    enterprise_value_usd: int | None = None
    trailing_price_to_earnings: float | None = None
    forward_price_to_earnings: float | None = None
    price_to_book_ratio: float | None = None
    price_to_sales_trailing_12m: float | None = None
    ev_to_ebitda_ratio: float | None = None
    trailing_peg_ratio: float | None = None
    dividend_yield_pct: float | None = None
    beta: float | None = None
    held_pct_institutions: float | None = None


class YFinanceQuarterlyRow(BaseModel):
    """yfinance owner — table: quarterly_financials — excludes: product_revenue_usd, service_revenue_usd, current_rpo_usd, noncurrent_rpo_usd, total_lease_obligation_usd, updated_at."""

    ticker: str
    fiscal_year: int
    fiscal_quarter: int
    period_start: date | None = None
    period_end: date

    # Income Statement (yfinance-sourced)
    total_revenue_usd: int | None = None
    cost_of_revenue_usd: int | None = None
    gross_profit_usd: int | None = None
    research_and_development_usd: int | None = None
    selling_general_admin_usd: int | None = None
    operating_income_usd: int | None = None
    ebit_usd: int | None = None
    net_income_usd: int | None = None
    interest_income_usd: int | None = None
    interest_expense_usd: int | None = None
    tax_provision_usd: int | None = None
    ebitda_usd: int | None = None
    diluted_eps: float | None = None
    diluted_avg_shares: int | None = None

    # Balance Sheet (yfinance-sourced)
    total_assets_usd: int | None = None
    goodwill_usd: int | None = None
    net_ppe_usd: int | None = None
    total_debt_usd: int | None = None
    long_term_debt_usd: int | None = None
    net_debt_usd: int | None = None
    cash_and_equivalents_usd: int | None = None
    stockholders_equity_usd: int | None = None
    current_assets_usd: int | None = None
    current_liabilities_usd: int | None = None
    accounts_receivable_usd: int | None = None
    inventory_usd: int | None = None
    deferred_revenue_usd: int | None = None

    # Cash Flow (yfinance-sourced)
    operating_cash_flow_usd: int | None = None
    capital_expenditure_usd: int | None = None
    free_cash_flow_usd: int | None = None
    depreciation_amortization_usd: int | None = None
    stock_buyback_usd: int | None = None
    dividends_paid_usd: int | None = None
    stock_based_compensation_usd: int | None = None


class YFinanceAnnualRow(BaseModel):
    """yfinance owner — table: annual_financials — excludes: product_revenue_usd, service_revenue_usd, current_rpo_usd, noncurrent_rpo_usd, total_lease_obligation_usd, updated_at."""

    ticker: str
    fiscal_year: int
    period_start: date | None = None
    period_end: date

    # Income Statement (yfinance-sourced)
    total_revenue_usd: int | None = None
    cost_of_revenue_usd: int | None = None
    gross_profit_usd: int | None = None
    research_and_development_usd: int | None = None
    selling_general_admin_usd: int | None = None
    operating_income_usd: int | None = None
    ebit_usd: int | None = None
    net_income_usd: int | None = None
    interest_income_usd: int | None = None
    interest_expense_usd: int | None = None
    tax_provision_usd: int | None = None
    ebitda_usd: int | None = None
    diluted_eps: float | None = None
    diluted_avg_shares: int | None = None

    # Balance Sheet (yfinance-sourced)
    total_assets_usd: int | None = None
    goodwill_usd: int | None = None
    net_ppe_usd: int | None = None
    total_debt_usd: int | None = None
    long_term_debt_usd: int | None = None
    net_debt_usd: int | None = None
    cash_and_equivalents_usd: int | None = None
    stockholders_equity_usd: int | None = None
    current_assets_usd: int | None = None
    current_liabilities_usd: int | None = None
    accounts_receivable_usd: int | None = None
    inventory_usd: int | None = None
    deferred_revenue_usd: int | None = None

    # Cash Flow (yfinance-sourced)
    operating_cash_flow_usd: int | None = None
    capital_expenditure_usd: int | None = None
    free_cash_flow_usd: int | None = None
    depreciation_amortization_usd: int | None = None
    stock_buyback_usd: int | None = None
    dividends_paid_usd: int | None = None
    stock_based_compensation_usd: int | None = None


