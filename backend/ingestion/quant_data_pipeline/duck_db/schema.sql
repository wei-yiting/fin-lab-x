-- ============================================================
-- Quant Data Pipeline — DuckDB Schema
-- ============================================================

-- 6.1 companies
CREATE TABLE IF NOT EXISTS companies (
    ticker VARCHAR PRIMARY KEY,
    company_name VARCHAR NOT NULL,
    sector VARCHAR,
    industry VARCHAR,
    fy_end_month INTEGER NOT NULL,
    fy_end_day INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN companies.ticker IS
  'Stock ticker symbol, uppercase. E.g. AAPL, MSFT, NVDA.';
COMMENT ON COLUMN companies.company_name IS
  'Full legal company name from yfinance.info longName.';
COMMENT ON COLUMN companies.sector IS
  'Broad industry classification. E.g. Technology, Financial Services.';
COMMENT ON COLUMN companies.industry IS
  'Fine-grained industry. E.g. Consumer Electronics, Software Application.';
COMMENT ON COLUMN companies.fy_end_month IS
  'Fiscal year end month (1-12). E.g. NVDA=1, WMT=1, MSFT=6, BRK.B=12, CAT=12.';
COMMENT ON COLUMN companies.fy_end_day IS
  'Fiscal year end day of month (1-31). Used only for display.';
COMMENT ON COLUMN companies.updated_at IS
  'Last time this row was upserted by ETL.';

-- 6.2 market_valuations
CREATE TABLE IF NOT EXISTS market_valuations (
    ticker VARCHAR NOT NULL,
    as_of_date DATE NOT NULL,
    market_cap_usd BIGINT,
    enterprise_value_usd BIGINT,
    trailing_price_to_earnings DOUBLE,
    forward_price_to_earnings DOUBLE,
    price_to_book_ratio DOUBLE,
    price_to_sales_trailing_12m DOUBLE,
    ev_to_ebitda_ratio DOUBLE,
    trailing_peg_ratio DOUBLE,
    dividend_yield_pct DOUBLE,
    beta DOUBLE,
    held_pct_institutions DOUBLE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, as_of_date)
);

COMMENT ON COLUMN market_valuations.ticker IS
  'Stock ticker symbol, uppercase. E.g. AAPL, MSFT, NVDA.';
COMMENT ON COLUMN market_valuations.as_of_date IS
  'Snapshot date of market data (typically today when ETL runs).';
COMMENT ON COLUMN market_valuations.market_cap_usd IS
  'Market capitalization in USD. = share_price * shares_outstanding.';
COMMENT ON COLUMN market_valuations.enterprise_value_usd IS
  'Enterprise value in USD. = market_cap + total_debt - cash.';
COMMENT ON COLUMN market_valuations.trailing_price_to_earnings IS
  'Trailing P/E ratio. = share_price / trailing 12-month EPS.';
COMMENT ON COLUMN market_valuations.forward_price_to_earnings IS
  'Forward P/E ratio. = share_price / forward 12-month EPS estimate.';
COMMENT ON COLUMN market_valuations.price_to_book_ratio IS
  'P/B ratio. = share_price / book_value_per_share.';
COMMENT ON COLUMN market_valuations.price_to_sales_trailing_12m IS
  'P/S TTM. = market_cap / trailing 12-month revenue.';
COMMENT ON COLUMN market_valuations.ev_to_ebitda_ratio IS
  'EV/EBITDA ratio. = enterprise_value / EBITDA.';
COMMENT ON COLUMN market_valuations.trailing_peg_ratio IS
  'PEG ratio. = trailing P/E / earnings growth rate.';
COMMENT ON COLUMN market_valuations.dividend_yield_pct IS
  'Dividend yield as percentage (already converted from decimal).';
COMMENT ON COLUMN market_valuations.beta IS
  'Beta. Volatility relative to broad market (S&P 500).';
COMMENT ON COLUMN market_valuations.held_pct_institutions IS
  'Institutional ownership as percentage.';
COMMENT ON COLUMN market_valuations.updated_at IS
  'Last time this row was upserted by ETL.';

-- 6.3 quarterly_financials
CREATE TABLE IF NOT EXISTS quarterly_financials (
    ticker VARCHAR NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    period_start DATE,
    period_end DATE NOT NULL,

    -- Income Statement (yfinance-sourced)
    total_revenue_usd BIGINT,
    cost_of_revenue_usd BIGINT,
    gross_profit_usd BIGINT,
    research_and_development_usd BIGINT,
    selling_general_admin_usd BIGINT,
    operating_income_usd BIGINT,
    ebit_usd BIGINT,
    net_income_usd BIGINT,
    interest_income_usd BIGINT,
    interest_expense_usd BIGINT,
    tax_provision_usd BIGINT,
    ebitda_usd BIGINT,
    diluted_eps DOUBLE,
    diluted_avg_shares BIGINT,

    -- Income Statement (SEC-sourced, revenue disaggregation per ASC 606)
    product_revenue_usd BIGINT,
    service_revenue_usd BIGINT,

    -- Balance Sheet (yfinance-sourced)
    total_assets_usd BIGINT,
    goodwill_usd BIGINT,
    net_ppe_usd BIGINT,
    total_debt_usd BIGINT,
    long_term_debt_usd BIGINT,
    net_debt_usd BIGINT,
    cash_and_equivalents_usd BIGINT,
    stockholders_equity_usd BIGINT,
    current_assets_usd BIGINT,
    current_liabilities_usd BIGINT,
    accounts_receivable_usd BIGINT,
    inventory_usd BIGINT,
    deferred_revenue_usd BIGINT,

    -- Balance Sheet (yf+sec: finance lease from yfinance, operating lease from SEC)
    total_lease_obligation_usd BIGINT,

    -- Cash Flow (yfinance-sourced)
    operating_cash_flow_usd BIGINT,
    capital_expenditure_usd BIGINT,
    free_cash_flow_usd BIGINT,
    depreciation_amortization_usd BIGINT,
    stock_buyback_usd BIGINT,
    dividends_paid_usd BIGINT,
    stock_based_compensation_usd BIGINT,

    -- Revenue Quality (SEC-sourced, RPO from ASC 606 disclosure)
    current_rpo_usd BIGINT,
    noncurrent_rpo_usd BIGINT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, fiscal_year, fiscal_quarter)
);

COMMENT ON COLUMN quarterly_financials.ticker IS
  'Stock ticker symbol, uppercase. E.g. AAPL, MSFT, NVDA.';
COMMENT ON COLUMN quarterly_financials.fiscal_year IS
  'Fiscal year (US SEC convention: year in which the fiscal year ENDS). AAPL FY2024 ends 2024-09-28.';
COMMENT ON COLUMN quarterly_financials.fiscal_quarter IS
  'Fiscal quarter 1-4. Q4 is the quarter ending on the fiscal year end.';
COMMENT ON COLUMN quarterly_financials.period_start IS
  'First calendar day of the reporting period. NULL when source does not disclose.';
COMMENT ON COLUMN quarterly_financials.period_end IS
  'Calendar date of fiscal period end (from data source, varies slightly year-to-year for 52/53-week calendars).';
COMMENT ON COLUMN quarterly_financials.total_revenue_usd IS
  'Total revenue in USD for the quarter.';
COMMENT ON COLUMN quarterly_financials.cost_of_revenue_usd IS
  'Cost of revenue (COGS) in USD for the quarter.';
COMMENT ON COLUMN quarterly_financials.gross_profit_usd IS
  'Gross profit = total_revenue - cost_of_revenue.';
COMMENT ON COLUMN quarterly_financials.research_and_development_usd IS
  'Research and development expense in USD.';
COMMENT ON COLUMN quarterly_financials.selling_general_admin_usd IS
  'Selling, general, and administrative expense in USD.';
COMMENT ON COLUMN quarterly_financials.operating_income_usd IS
  'Operating income = gross_profit - operating expenses (R&D + SG&A).';
COMMENT ON COLUMN quarterly_financials.ebit_usd IS
  'Earnings before interest and taxes.';
COMMENT ON COLUMN quarterly_financials.ebitda_usd IS
  'Earnings before interest, taxes, depreciation, and amortization.';
COMMENT ON COLUMN quarterly_financials.net_income_usd IS
  'Net income attributable to company shareholders.';
COMMENT ON COLUMN quarterly_financials.interest_income_usd IS
  'Non-operating interest income. Core revenue for financial services firms.';
COMMENT ON COLUMN quarterly_financials.interest_expense_usd IS
  'Non-operating interest expense. Used for interest coverage ratio.';
COMMENT ON COLUMN quarterly_financials.tax_provision_usd IS
  'Income tax provision. Used for effective tax rate.';
COMMENT ON COLUMN quarterly_financials.diluted_eps IS
  'Diluted earnings per share (EPS).';
COMMENT ON COLUMN quarterly_financials.diluted_avg_shares IS
  'Diluted weighted-average shares outstanding for the period.';
COMMENT ON COLUMN quarterly_financials.product_revenue_usd IS
  'Revenue from products (goods) per ASC 606 disaggregation. NULL if company does not disclose.';
COMMENT ON COLUMN quarterly_financials.service_revenue_usd IS
  'Revenue from services per ASC 606 disaggregation. NULL if company does not disclose.';
COMMENT ON COLUMN quarterly_financials.total_assets_usd IS
  'Total assets at period end.';
COMMENT ON COLUMN quarterly_financials.goodwill_usd IS
  'Goodwill from past acquisitions.';
COMMENT ON COLUMN quarterly_financials.net_ppe_usd IS
  'Net property, plant, and equipment.';
COMMENT ON COLUMN quarterly_financials.total_debt_usd IS
  'Total debt = long_term_debt + current_debt.';
COMMENT ON COLUMN quarterly_financials.long_term_debt_usd IS
  'Long-term debt (due > 1 year).';
COMMENT ON COLUMN quarterly_financials.net_debt_usd IS
  'Net debt = total_debt - cash_and_equivalents. Negative means cash exceeds debt.';
COMMENT ON COLUMN quarterly_financials.cash_and_equivalents_usd IS
  'Cash and cash equivalents (excludes short-term investments).';
COMMENT ON COLUMN quarterly_financials.stockholders_equity_usd IS
  'Total stockholders equity (book value).';
COMMENT ON COLUMN quarterly_financials.current_assets_usd IS
  'Current assets (expected to be realized within 1 year).';
COMMENT ON COLUMN quarterly_financials.current_liabilities_usd IS
  'Current liabilities (due within 1 year).';
COMMENT ON COLUMN quarterly_financials.accounts_receivable_usd IS
  'Accounts receivable at period end.';
COMMENT ON COLUMN quarterly_financials.inventory_usd IS
  'Inventory at period end.';
COMMENT ON COLUMN quarterly_financials.deferred_revenue_usd IS
  'Current deferred revenue (payments received but service not yet delivered).';
COMMENT ON COLUMN quarterly_financials.total_lease_obligation_usd IS
  'Total lease obligation (finance + operating). yfinance provides finance only; SEC 10-K/10-Q supplements operating.';
COMMENT ON COLUMN quarterly_financials.operating_cash_flow_usd IS
  'Cash flow from operating activities.';
COMMENT ON COLUMN quarterly_financials.capital_expenditure_usd IS
  'Capital expenditures. Stored with original sign (yfinance returns negative).';
COMMENT ON COLUMN quarterly_financials.free_cash_flow_usd IS
  'Free cash flow = operating_cash_flow - capital_expenditure (sign-normalized by yfinance).';
COMMENT ON COLUMN quarterly_financials.depreciation_amortization_usd IS
  'Depreciation and amortization from cash flow statement.';
COMMENT ON COLUMN quarterly_financials.stock_buyback_usd IS
  'Share repurchases. Original sign preserved (negative = cash outflow).';
COMMENT ON COLUMN quarterly_financials.dividends_paid_usd IS
  'Common stock dividends paid. Original sign preserved (negative = cash outflow).';
COMMENT ON COLUMN quarterly_financials.stock_based_compensation_usd IS
  'Stock-based compensation expense.';
COMMENT ON COLUMN quarterly_financials.current_rpo_usd IS
  'Remaining performance obligation expected to be recognized within 12 months. NULL if company does not disclose (typically SaaS/Cloud only).';
COMMENT ON COLUMN quarterly_financials.noncurrent_rpo_usd IS
  'Remaining performance obligation expected to be recognized beyond 12 months. NULL if company does not disclose.';
COMMENT ON COLUMN quarterly_financials.updated_at IS
  'Last time this row was upserted by ETL.';

-- 6.4 annual_financials
-- Same columns as quarterly_financials except fiscal_quarter; PK = (ticker, fiscal_year)
CREATE TABLE IF NOT EXISTS annual_financials (
    ticker VARCHAR NOT NULL,
    fiscal_year INTEGER NOT NULL,
    period_start DATE,
    period_end DATE NOT NULL,

    -- Income Statement (yfinance-sourced)
    total_revenue_usd BIGINT,
    cost_of_revenue_usd BIGINT,
    gross_profit_usd BIGINT,
    research_and_development_usd BIGINT,
    selling_general_admin_usd BIGINT,
    operating_income_usd BIGINT,
    ebit_usd BIGINT,
    net_income_usd BIGINT,
    interest_income_usd BIGINT,
    interest_expense_usd BIGINT,
    tax_provision_usd BIGINT,
    ebitda_usd BIGINT,
    diluted_eps DOUBLE,
    diluted_avg_shares BIGINT,

    -- Income Statement (SEC-sourced, revenue disaggregation per ASC 606)
    product_revenue_usd BIGINT,
    service_revenue_usd BIGINT,

    -- Balance Sheet (yfinance-sourced)
    total_assets_usd BIGINT,
    goodwill_usd BIGINT,
    net_ppe_usd BIGINT,
    total_debt_usd BIGINT,
    long_term_debt_usd BIGINT,
    net_debt_usd BIGINT,
    cash_and_equivalents_usd BIGINT,
    stockholders_equity_usd BIGINT,
    current_assets_usd BIGINT,
    current_liabilities_usd BIGINT,
    accounts_receivable_usd BIGINT,
    inventory_usd BIGINT,
    deferred_revenue_usd BIGINT,

    -- Balance Sheet (yf+sec: finance lease from yfinance, operating lease from SEC)
    total_lease_obligation_usd BIGINT,

    -- Cash Flow (yfinance-sourced)
    operating_cash_flow_usd BIGINT,
    capital_expenditure_usd BIGINT,
    free_cash_flow_usd BIGINT,
    depreciation_amortization_usd BIGINT,
    stock_buyback_usd BIGINT,
    dividends_paid_usd BIGINT,
    stock_based_compensation_usd BIGINT,

    -- Revenue Quality (SEC-sourced, RPO from ASC 606 disclosure)
    current_rpo_usd BIGINT,
    noncurrent_rpo_usd BIGINT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, fiscal_year)
);

COMMENT ON COLUMN annual_financials.ticker IS
  'Stock ticker symbol, uppercase. E.g. AAPL, MSFT, NVDA.';
COMMENT ON COLUMN annual_financials.fiscal_year IS
  'Fiscal year (US SEC convention: year in which the fiscal year ENDS). AAPL FY2024 ends 2024-09-28.';
COMMENT ON COLUMN annual_financials.period_start IS
  'First calendar day of the reporting period. NULL when source does not disclose.';
COMMENT ON COLUMN annual_financials.period_end IS
  'Calendar date of fiscal period end (from data source, varies slightly year-to-year for 52/53-week calendars).';
COMMENT ON COLUMN annual_financials.total_revenue_usd IS
  'Total revenue in USD for the quarter.';
COMMENT ON COLUMN annual_financials.cost_of_revenue_usd IS
  'Cost of revenue (COGS) in USD for the quarter.';
COMMENT ON COLUMN annual_financials.gross_profit_usd IS
  'Gross profit = total_revenue - cost_of_revenue.';
COMMENT ON COLUMN annual_financials.research_and_development_usd IS
  'Research and development expense in USD.';
COMMENT ON COLUMN annual_financials.selling_general_admin_usd IS
  'Selling, general, and administrative expense in USD.';
COMMENT ON COLUMN annual_financials.operating_income_usd IS
  'Operating income = gross_profit - operating expenses (R&D + SG&A).';
COMMENT ON COLUMN annual_financials.ebit_usd IS
  'Earnings before interest and taxes.';
COMMENT ON COLUMN annual_financials.ebitda_usd IS
  'Earnings before interest, taxes, depreciation, and amortization.';
COMMENT ON COLUMN annual_financials.net_income_usd IS
  'Net income attributable to company shareholders.';
COMMENT ON COLUMN annual_financials.interest_income_usd IS
  'Non-operating interest income. Core revenue for financial services firms.';
COMMENT ON COLUMN annual_financials.interest_expense_usd IS
  'Non-operating interest expense. Used for interest coverage ratio.';
COMMENT ON COLUMN annual_financials.tax_provision_usd IS
  'Income tax provision. Used for effective tax rate.';
COMMENT ON COLUMN annual_financials.diluted_eps IS
  'Diluted earnings per share (EPS).';
COMMENT ON COLUMN annual_financials.diluted_avg_shares IS
  'Diluted weighted-average shares outstanding for the period.';
COMMENT ON COLUMN annual_financials.product_revenue_usd IS
  'Revenue from products (goods) per ASC 606 disaggregation. NULL if company does not disclose.';
COMMENT ON COLUMN annual_financials.service_revenue_usd IS
  'Revenue from services per ASC 606 disaggregation. NULL if company does not disclose.';
COMMENT ON COLUMN annual_financials.total_assets_usd IS
  'Total assets at period end.';
COMMENT ON COLUMN annual_financials.goodwill_usd IS
  'Goodwill from past acquisitions.';
COMMENT ON COLUMN annual_financials.net_ppe_usd IS
  'Net property, plant, and equipment.';
COMMENT ON COLUMN annual_financials.total_debt_usd IS
  'Total debt = long_term_debt + current_debt.';
COMMENT ON COLUMN annual_financials.long_term_debt_usd IS
  'Long-term debt (due > 1 year).';
COMMENT ON COLUMN annual_financials.net_debt_usd IS
  'Net debt = total_debt - cash_and_equivalents. Negative means cash exceeds debt.';
COMMENT ON COLUMN annual_financials.cash_and_equivalents_usd IS
  'Cash and cash equivalents (excludes short-term investments).';
COMMENT ON COLUMN annual_financials.stockholders_equity_usd IS
  'Total stockholders equity (book value).';
COMMENT ON COLUMN annual_financials.current_assets_usd IS
  'Current assets (expected to be realized within 1 year).';
COMMENT ON COLUMN annual_financials.current_liabilities_usd IS
  'Current liabilities (due within 1 year).';
COMMENT ON COLUMN annual_financials.accounts_receivable_usd IS
  'Accounts receivable at period end.';
COMMENT ON COLUMN annual_financials.inventory_usd IS
  'Inventory at period end.';
COMMENT ON COLUMN annual_financials.deferred_revenue_usd IS
  'Current deferred revenue (payments received but service not yet delivered).';
COMMENT ON COLUMN annual_financials.total_lease_obligation_usd IS
  'Total lease obligation (finance + operating). yfinance provides finance only; SEC 10-K/10-Q supplements operating.';
COMMENT ON COLUMN annual_financials.operating_cash_flow_usd IS
  'Cash flow from operating activities.';
COMMENT ON COLUMN annual_financials.capital_expenditure_usd IS
  'Capital expenditures. Stored with original sign (yfinance returns negative).';
COMMENT ON COLUMN annual_financials.free_cash_flow_usd IS
  'Free cash flow = operating_cash_flow - capital_expenditure (sign-normalized by yfinance).';
COMMENT ON COLUMN annual_financials.depreciation_amortization_usd IS
  'Depreciation and amortization from cash flow statement.';
COMMENT ON COLUMN annual_financials.stock_buyback_usd IS
  'Share repurchases. Original sign preserved (negative = cash outflow).';
COMMENT ON COLUMN annual_financials.dividends_paid_usd IS
  'Common stock dividends paid. Original sign preserved (negative = cash outflow).';
COMMENT ON COLUMN annual_financials.stock_based_compensation_usd IS
  'Stock-based compensation expense.';
COMMENT ON COLUMN annual_financials.current_rpo_usd IS
  'Remaining performance obligation expected to be recognized within 12 months. NULL if company does not disclose (typically SaaS/Cloud only).';
COMMENT ON COLUMN annual_financials.noncurrent_rpo_usd IS
  'Remaining performance obligation expected to be recognized beyond 12 months. NULL if company does not disclose.';
COMMENT ON COLUMN annual_financials.updated_at IS
  'Last time this row was upserted by ETL.';

-- 6.5 segment_financials
CREATE TABLE IF NOT EXISTS segment_financials (
    ticker VARCHAR NOT NULL,
    fiscal_year INTEGER NOT NULL,
    period_type VARCHAR NOT NULL CHECK (period_type IN ('quarterly', 'annual')),
    fiscal_quarter INTEGER,                     -- NULL for annual
    period_start DATE,
    period_end DATE NOT NULL,
    segment_name VARCHAR NOT NULL,
    segment_revenue_usd BIGINT,
    segment_operating_income_usd BIGINT,
    segment_assets_usd BIGINT,
    segment_capex_usd BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (period_type = 'annual'    AND fiscal_quarter IS NULL) OR
        (period_type = 'quarterly' AND fiscal_quarter IS NOT NULL
                                   AND fiscal_quarter BETWEEN 1 AND 4)
    ),
    PRIMARY KEY (ticker, fiscal_year, period_type, period_end, segment_name)
);

COMMENT ON COLUMN segment_financials.ticker IS
  'Stock ticker symbol, uppercase. E.g. AAPL, MSFT, NVDA.';
COMMENT ON COLUMN segment_financials.fiscal_year IS
  'Fiscal year (e.g., MSFT FY2024 ends June 2024).';
COMMENT ON COLUMN segment_financials.period_type IS
  'Reporting granularity: ''quarterly'' (one calendar quarter) or ''annual'' (full fiscal year).';
COMMENT ON COLUMN segment_financials.fiscal_quarter IS
  'Fiscal quarter 1-4 when period_type=''quarterly''; NULL when period_type=''annual''.';
COMMENT ON COLUMN segment_financials.period_start IS
  'First calendar day of the reporting period. NULL when source does not disclose.';
COMMENT ON COLUMN segment_financials.period_end IS
  'Last calendar day of the reporting period (canonical identity date).';
COMMENT ON COLUMN segment_financials.segment_name IS
  'Company-defined business segment name. E.g. AWS, Reality Labs, Services.';
COMMENT ON COLUMN segment_financials.segment_revenue_usd IS
  'Segment revenue.';
COMMENT ON COLUMN segment_financials.segment_operating_income_usd IS
  'Segment operating income or loss (can be negative).';
COMMENT ON COLUMN segment_financials.segment_assets_usd IS
  'Segment assets. NULL if not disclosed at segment level.';
COMMENT ON COLUMN segment_financials.segment_capex_usd IS
  'Segment capital expenditure. NULL if not disclosed at segment level.';
COMMENT ON COLUMN segment_financials.updated_at IS
  'Last time this row was upserted by ETL.';

-- 6.6 geographic_revenue
CREATE TABLE IF NOT EXISTS geographic_revenue (
    ticker VARCHAR NOT NULL,
    fiscal_year INTEGER NOT NULL,
    period_type VARCHAR NOT NULL CHECK (period_type IN ('quarterly', 'annual')),
    fiscal_quarter INTEGER,                     -- NULL for annual
    period_start DATE,
    period_end DATE NOT NULL,
    region_name VARCHAR NOT NULL,
    revenue_usd BIGINT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (period_type = 'annual'    AND fiscal_quarter IS NULL) OR
        (period_type = 'quarterly' AND fiscal_quarter IS NOT NULL
                                   AND fiscal_quarter BETWEEN 1 AND 4)
    ),
    PRIMARY KEY (ticker, fiscal_year, period_type, period_end, region_name)
);

COMMENT ON COLUMN geographic_revenue.ticker IS
  'Stock ticker symbol, uppercase. E.g. AAPL, MSFT, NVDA.';
COMMENT ON COLUMN geographic_revenue.fiscal_year IS
  'Fiscal year (e.g., MSFT FY2024 ends June 2024).';
COMMENT ON COLUMN geographic_revenue.period_type IS
  'Reporting granularity: ''quarterly'' (one calendar quarter) or ''annual'' (full fiscal year).';
COMMENT ON COLUMN geographic_revenue.fiscal_quarter IS
  'Fiscal quarter 1-4 when period_type=''quarterly''; NULL when period_type=''annual''.';
COMMENT ON COLUMN geographic_revenue.period_start IS
  'First calendar day of the reporting period. NULL when source does not disclose.';
COMMENT ON COLUMN geographic_revenue.period_end IS
  'Last calendar day of the reporting period (canonical identity date).';
COMMENT ON COLUMN geographic_revenue.region_name IS
  'Company-defined geographic region name. E.g. Americas, Greater China, Europe.';
COMMENT ON COLUMN geographic_revenue.revenue_usd IS
  'Revenue attributed to this region for the period.';
COMMENT ON COLUMN geographic_revenue.updated_at IS
  'Last time this row was upserted by ETL.';

-- 6.7 customer_concentration
CREATE TABLE IF NOT EXISTS customer_concentration (
    ticker VARCHAR NOT NULL,
    fiscal_year INTEGER NOT NULL,
    customer_identifier VARCHAR NOT NULL,
    revenue_pct DOUBLE NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, fiscal_year, customer_identifier)
);

COMMENT ON COLUMN customer_concentration.ticker IS
  'Stock ticker symbol, uppercase. E.g. AAPL, MSFT, NVDA.';
COMMENT ON COLUMN customer_concentration.fiscal_year IS
  'Fiscal year (e.g., MSFT FY2024 ends June 2024).';
COMMENT ON COLUMN customer_concentration.customer_identifier IS
  'Customer name if disclosed (e.g. Apple Inc.), or anonymized label (e.g. Customer A) depending on filing.';
COMMENT ON COLUMN customer_concentration.revenue_pct IS
  'Percentage of total company revenue from this customer. Only disclosed when >10%.';
COMMENT ON COLUMN customer_concentration.updated_at IS
  'Last time this row was upserted by ETL.';

-- 6.8 ingestion_runs
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline VARCHAR NOT NULL,
    ticker VARCHAR NOT NULL,

    -- SEC-only: identifies the specific filing being processed
    target_filing_type VARCHAR,                 -- '10-K' | '10-Q' | NULL for yfinance
    target_fiscal_year INTEGER,
    target_fiscal_quarter INTEGER,
    target_accession_number VARCHAR,

    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,

    status VARCHAR NOT NULL,                    -- 'success' | 'error'
    error_class VARCHAR,
    error_message VARCHAR,

    rows_written_total INTEGER,
    metadata JSON
);

CREATE INDEX IF NOT EXISTS idx_runs_pipeline_ticker_started
    ON ingestion_runs(pipeline, ticker, started_at DESC);

COMMENT ON TABLE ingestion_runs IS
  'Audit log of every ETL invocation. Tracks WHO/WHEN/HOW data got in. For "WHAT data exists" query data tables directly (they carry fiscal_year/fiscal_quarter).';
COMMENT ON COLUMN ingestion_runs.run_id IS
  'Unique run identifier (UUID). Auto-generated when caller omits it.';
COMMENT ON COLUMN ingestion_runs.pipeline IS
  'Pipeline name: yfinance | sec_xbrl.';
COMMENT ON COLUMN ingestion_runs.ticker IS
  'Stock ticker symbol, uppercase. E.g. AAPL, MSFT, NVDA.';
COMMENT ON COLUMN ingestion_runs.target_filing_type IS
  'SEC filing type (''10-K'' or ''10-Q''). NULL for yfinance runs.';
COMMENT ON COLUMN ingestion_runs.target_fiscal_year IS
  'Fiscal year targeted by the run. NULL when pipeline processes all available years.';
COMMENT ON COLUMN ingestion_runs.target_fiscal_quarter IS
  'Fiscal quarter targeted by the run. NULL for 10-K (annual) or when processing all quarters.';
COMMENT ON COLUMN ingestion_runs.target_accession_number IS
  'SEC filing immutable identity. NULL for yfinance (no single-filing target).';
COMMENT ON COLUMN ingestion_runs.started_at IS
  'UTC timestamp when the run began.';
COMMENT ON COLUMN ingestion_runs.finished_at IS
  'UTC timestamp when the run ended (success or error). NULL if the row was pre-inserted before completion.';
COMMENT ON COLUMN ingestion_runs.status IS
  'Terminal outcome: ''success'' or ''error''.';
COMMENT ON COLUMN ingestion_runs.error_class IS
  'Exception class name when status=''error''. NULL on success.';
COMMENT ON COLUMN ingestion_runs.error_message IS
  'Exception message when status=''error''. NULL on success.';
COMMENT ON COLUMN ingestion_runs.rows_written_total IS
  'Total rows upserted across all target tables for this run. May be partial on error.';
COMMENT ON COLUMN ingestion_runs.metadata IS
  'Per-run summary. Free-form JSON: {periods_covered, rows_per_table, api_latency_ms, ...}.';
