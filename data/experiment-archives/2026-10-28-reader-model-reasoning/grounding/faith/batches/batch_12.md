# Faithfulness batch 12 — 6 items

===== ITEM F0067 =====

QUESTION:
分析沃爾瑪跟好市多的現金流品質與資本配置韌性，哪家比較穩。

----- BEGIN EVIDENCE F0067 -----
[tool 0] finnhub_company_basic_financials {"ticker": "COST"}
{
 "ticker": "COST",
 "fiftyTwoWeekHigh": 1096.5,
 "fiftyTwoWeekLow": 844.06,
 "peTTM": 48.348,
 "forwardPE": 39.71763,
 "psTTM": 1.4714,
 "pb": 11.686,
 "marketCap": 446058.4,
 "enterpriseValue": 432013.4,
 "beta": 0.86917955,
 "epsTTM": 20.7597,
 "roeTTM": 28.02,
 "roaTTM": 10.79,
 "grossMarginTTM": 12.82,
 "netProfitMarginTTM": 3.04,
 "operatingMarginTTM": 3.85,
 "currentRatio": 1.0598,
 "quickRatio": 0.6202,
 "debtToEquity": 0.1721,
 "dividendYield": 0.68994,
 "revenueGrowthTTMYoy": 10.14,
 "epsGrowthTTMYoy": 14.01,
 "tenDayAvgVolume": 2.21746
}

[tool 1] finnhub_company_basic_financials {"ticker": "WMT"}
{
 "ticker": "WMT",
 "fiftyTwoWeekHigh": 135.16,
 "fiftyTwoWeekLow": 98.88,
 "peTTM": 42.9839,
 "forwardPE": 35.49995,
 "psTTM": 1.2896,
 "pb": 9.0081,
 "marketCap": 948912.4,
 "enterpriseValue": 994626.4,
 "beta": 0.5401133,
 "epsTTM": 2.76,
 "roeTTM": 22.74,
 "roaTTM": 7.630000000000001,
 "grossMarginTTM": 25.23,
 "netProfitMarginTTM": 3,
 "operatingMarginTTM": 4.39,
 "currentRatio": 0.7671,
 "quickRatio": 0.1955,
 "debtToEquity": 0.5827,
 "dividendYield": 0.7596102202102354,
 "revenueGrowthTTMYoy": 6.16,
 "epsGrowthTTMYoy": 4.13,
 "tenDayAvgVolume": 21.32036
}

[tool 2] sec_filing_search {"query": "cash flow quality operating cash flow free cash flow conversion capital expenditures working capital lease obligations debt maturities dividends share repurchases capital allocation", "ticker": "WMT", "fiscal_year": null}
{
 "fiscal_year": 2026,
 "fiscal_year_end": "2026-01-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "WMT",
   "fiscal_year": 2026,
   "item": "Item 7",
   "prelude": "Excerpts from WMT FY2026 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 9 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000104169-26-000055/7#107",
     "title": "WMT FY2026 10-K · Item 7 · Capital Allocation",
     "content": "### Capital Allocation\n\nOur strategy includes allocating the majority of our capital to higher-return areas focused on automation such as eCommerce, supply chain and store and club investments. The following table provides additional detail regarding our capital expenditures:\n\n|
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| (Amounts in millions) | | |  | | | Fiscal Years Ended January 31, | | | | | | | | |\n| Allocation of Capital Expenditures | | |  | | | 2026 | | |  | | | 2025 |
| |\n| Supply chain, customer-facing initiatives, technology and other | | |  | | | $ | 16,468 |  |  | | | $ | 14,603 |  |\n| Store and club remodels | | |  | | | 5,571 | |  |  | | | 5,552 | |  |\n| New stores and clubs, including expansions and relocations | | |  | | | 1,406 | |  |  | | | 450 | |
|\n| Total U.S. | | |  | | | $ | 23,445 |  |  | | | $ | 20,605 |  |\n| Walmart International | | |  | | | 3,197 | |  |  | | | 3,178 | |  |\n| Total Capital Expenditures | | |  | | | $ | 26,642 |  |  | | | $ | 23,783 |  |\n\n36\n\n\n\nFree Cash Flow",
     "score": 0.5,
     "subsection": "Capital Allocation"
    },
    {
     "source": "sec://0000104169-26-000055/7#108",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "36\n\n\n\nFree Cash Flow\n\nFree cash flow is considered a non-GAAP financial measure. Management believes, however, that free cash flow, which measures our ability to generate additional cash from our business operations, is an important financial measure for use in evaluating the
Company's financial performance. Free cash flow should be considered in addition to, rather than as a substitute for, consolidated net income as a measure of our performance and net cash provided by operating activities as a measure of our liquidity. See [Liquidity and Capital
Resources](#i6e16e33efce1499a82f13fd9f63b74c6_103) for discussions of GAAP metrics including net cash provided by operating activities, net cash used in investing activities and net cash used in financing activities.\n\nWe define free cash flow as net cash provided by operating activities in a
period minus payments for property and equipment made in that period. Walmart's definition of free cash flow is limited in that it does not represent residual cash flows available for discretionary expenditures due to the fact that the measure does not deduct the payments required for debt service
and other contractual obligations or payments made for business acquisitions. Therefore, we believe it is important to view free cash flow as a measure that provides supplemental information to our [Consolidated Statements of Cash Flows](#i6e16e33efce1499a82f13fd9f63b74c6_139).\n\nAlthough other
companies report their free cash flow, numerous methods may exist for calculating a company's free cash flow. As a result, the method used by management to calculate our free cash flow may differ from the methods used by other companies to calculate their free cash flow.\n\nThe following table sets
forth a reconciliation of free cash flow, a non-GAAP financial measure, to net cash provided by operating activities, which we believe to be the GAAP financial measure most directly comparable to free cash flow, as well as information regarding net cash used in investing activities and net cash used
in financing activities.",
     "score": 0.4921
    },
    {
     "source": "sec://0000104169-26-000055/7#109",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | |  | | | Fiscal Years Ended January 31, | | | | | | | | | | | | | | |\n| (Amounts
in millions) | | |  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net cash provided by operating activities | | |  | | | $ | 41,565 |  |  | | | $ | 36,443 |  |  | | | $ | 35,726 |  |\n| Payments for property and equipment | | |  | | | (26,642) | |  |  | | | (23,783) | |  |  | | | (20,606)
| |  |\n| Free cash flow | | |  | | | $ | 14,923 |  |  | | | $ | 12,660 |  |  | | | $ | 15,120 |  |\n|  | | |  | | |  | | |  | | |  | | |  | | |  | | |\n| Net cash used in investing activities(1) | | |  | | | $ | (26,350) |  |  | | | $ | (21,379) |  |  | | | $ | (21,287) |  |\n| Net cash used in
financing activities | | |  | | | (13,553) | |  |  | | | (14,822) | |  |  | | | (13,414) | |  |\n\n(1)\"Net cash used in investing activities\" includes payments for property and equipment, which is also included in our computation of free cash flow.",
     "score": 0.5332
    },
    {
     "source": "sec://0000104169-26-000055/7#110",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "(1)\"Net cash used in investing activities\" includes payments for property and equipment, which is also included in our computation of free cash flow.\n\n\nThe increase in net cash provided by operating activities in fiscal 2026 is primarily due to an increase in cash provided by
operating income, lower cash tax payments and the timing of certain payments. Free cash flow for fiscal 2026 increased when compared to fiscal 2025 due to an increase in cash provided by operating income, lower cash tax payments and timing of certain payments, partially offset by an increase of $2.9
billion in capital expenditures to support our omnichannel growth strategy. Net cash provided by operating activities for fiscal 2025 increased when compared to fiscal 2024 primarily due to an increase in cash provided by operating income and lapping the payment of accrued opioid legal charges in
the prior year, partially offset by increased inventory purchases. Free cash flow for fiscal 2025 decreased when compared to fiscal 2024 due to an increase of $3.2 billion in capital expenditures to support our omnichannel growth strategy, partially offset by the increase in net cash provided by
operating activities described above.\n\n37",
     "score": 0.5123
    },
    {
     "source": "sec://0000104169-26-000055/7#132",
     "title": "WMT FY2026 10-K · Item 7 · Liquidity and Capital Resources",
     "content": "### Liquidity and Capital Resources",
     "score": 0.4951,
     "subsection": "Liquidity and Capital Resources"
    },
    {
     "source": "sec://0000104169-26-000055/7#133",
     "title": "WMT FY2026 10-K · Item 7 · Liquidity",
     "content": "### Liquidity\n\nThe strength and stability of our operations have historically supplied us with a significant source of liquidity. Our cash flows provided by operating activities, supplemented with our long-term debt and short-term borrowings, have been sufficient to fund our
operations while allowing us to invest in activities that support the long-term growth of our operations. Generally, some or all of the remaining available cash flow has been used to fund dividends on our common stock and share repurchases. We believe our sources of liquidity will continue to be
sufficient to fund operations, finance our investment activities, pay dividends and fund our share repurchases for at least the next 12 months and for the foreseeable future.",
     "score": 0.5537,
     "subsection": "Liquidity"
    },
    {
     "source": "sec://0000104169-26-000055/7#134",
     "title": "WMT FY2026 10-K · Item 7 · Net Cash Provided by Operating Activities",
     "content": "### Net Cash Provided by Operating Activities\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | |  | | | Fiscal Years Ended
January 31, | | | | | | | | | | | | | | |\n| (Amounts in millions) | | |  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net cash provided by operating activities | | |  | | | $ | 41,565 |  |  | | | $ | 36,443 |  |  | | | $ | 35,726 |  |\n\nNet cash provided by operating activities
increased $5.1 billion for fiscal 2026 when compared to the previous fiscal year. The increase is primarily due to an increase in cash provided by operating income, lower cash tax payments and timing of certain payments. The increase in net cash provided by operating activities for fiscal 2025, when
compared to the previous fiscal year, was primarily due to an increase in cash provided by operating income and lapping the payment of accrued opioid legal charges in the prior year, partially offset by increased inventory purchases.\n\nCash Equivalents and Working Capital Deficit\n\nCash and cash
equivalents were $10.7 billion and $9.0 billion as of January 31, 2026 and 2025, respectively. Our working capital deficit, defined as total current assets less total current liabilities, was $22.6 billion and $17.1 billion as of January 31, 2026 and 2025, respectively. The increase in our working
capital deficit was primarily driven by timing of certain payments combined with an increase in short-term borrowings for general corporate purposes, partially offset by increased inventories and receivables related to higher sales growth as well as higher cash balances. We generally operate with a
working capital deficit due to our efficient use of cash in funding operations, consistent access to the capital markets and returns provided to our shareholders in the form of payments of cash dividends and share repurchases.",
     "score": 0.5287,
     "subsection": "Net Cash Provided by Operating Activities"
    },
    {
     "source": "sec://0000104169-26-000055/7#144",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "Material Cash Requirements\n\nMaterial cash requirements from operating activities primarily consist of inventory purchases, employee related costs, taxes, interest and other general operating expenses, which we expect to be primarily satisfied by our cash from operations. Other
material cash requirements from known contractual and other obligations include short-term borrowings, long-term debt and related interest payments, leases and purchase obligations. See [Note 4](#i6e16e33efce1499a82f13fd9f63b74c6_157), [Note 5](#i6e16e33efce1499a82f13fd9f63b74c6_160) and [Note
6](#i6e16e33efce1499a82f13fd9f63b74c6_163) to our Consolidated Financial Statements for information regarding accrued liabilities, outstanding short-term borrowings and long-term debt, and leases, respectively.\n\nAs of January 31, 2026, the Company has $41.4 billion of unrecorded purchase
obligations outstanding, of which $18.3 billion is due within one year. Purchase obligations include legally binding contracts, such as firm commitments for inventory and utility purchases, as well as commitments to make capital expenditures, software acquisition and license commitments and legally
binding service contracts. Contractual obligations for the purchase of goods or services are defined as agreements that are enforceable and legally binding and that specify all significant terms, including: fixed or minimum quantities to be purchased; fixed, minimum or variable price provisions; and
the approximate timing of the transaction. Contracts that specify the Company will purchase all or a portion of its requirements of a specific product or service from a supplier, but do not include a fixed or minimum quantity, are excluded from the obligations quantified above. Accordingly, purchase
orders for inventory are also excluded as purchase orders represent authorizations to purchase rather than binding agreements. Our purchase orders are based on our current inventory needs and are fulfilled by our suppliers within short time periods. We also enter into contracts for outsourced
services; however, the obligations under these contracts are not significant and the contracts generally contain clauses allowing for cancellation without significant penalty. Timing of payments and actual amounts paid may be different depending on the timing of receipt of goods or services or
changes to agreed-upon amounts for some obligations.\n\n44",
     "score": 0.5236
    },
    {
     "source": "sec://0000104169-26-000055/7#145",
     "title": "WMT FY2026 10-K · Item 7 · Capital Resources",
     "content": "### Capital Resources\n\nWe believe our cash flows from operations, current cash position, short-term borrowings and access to capital markets will continue to be sufficient to meet our anticipated cash requirements and contractual obligations, which includes funding seasonal
buildups in merchandise inventories and funding our capital expenditures, acquisitions, dividend payments and share repurchases.\n\nWe have strong commercial paper and long-term debt ratings that have enabled and should continue to enable us to refinance our debt as it becomes due at favorable rates
in capital markets. As of January 31, 2026, the ratings assigned to our commercial paper and rated series of our outstanding long-term debt were as follows:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
|\n| Rating agency | | |  | | | Commercial paper | | |  | | | Long-term debt | | |\n| Standard & Poor's | | |  | | | A-1+ | | |  | | | AA | | |\n| Moody's Investors Service | | |  | | | P-1 | | |  | | | Aa2 | | |\n| Fitch Ratings | | |  | | | F1+ | | |  | | | AA | | |",
     "score": 0.5157,
     "subsection": "Capital Resources"
    }
   ]
  },
  {
   "ticker": "WMT",
   "fiscal_year": 2026,
   "item": "Item 8",
   "prelude": "Excerpts from WMT FY2026 10-K, Item 8 (Financial Statements and Supplementary Data) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000104169-26-000055/8#196",
     "title": "WMT FY2026 10-K · Item 8",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | |  | | | Fiscal Years Ended January 31, | | | | | | | | | | | | | | |\n| (Amounts
in millions) | | |  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Cash flows from operating activities: | | |  | | |  | | |  | | |  | | |  | | |  | | |\n| Consolidated net income | | |  | | | $ | 22,270 |  |  | | | $ | 20,157 |  |  | | | $ | 16,270 |  |\n| Adjustments to reconcile
consolidated net income to net cash provided by operating activities: | | |  | | |  | | |  | | |  | | |  | | |  | | |\n| Depreciation and amortization | | |  | | | 14,203 | |  |  | | | 12,973 | |  |  | | | 11,853 | |  |\n| Investment (gains) and losses, net | | |  | | | (2,016) | |  |  | | | 878 | |
|  | | | 3,193 | |  |\n|\n| Deferred income taxes | | |  | | | 2,277 | |  |  | | | (635) | |  |  | | | (175) | |  |\n|\n| Other operating activities | | |  | | | 4,079 | |  |  | | | 2,889 | |  |  | | | 2,642 | |  |",
     "score": 0.5138
    }
   ]
  }
 ]
}

[tool 3] sec_filing_search {"query": "cash flow quality operating cash flow free cash flow conversion capital expenditures working capital lease obligations debt maturities dividends share repurchases capital allocation", "ticker": "COST", "fiscal_year": null}
{
 "fiscal_year": 2026,
 "fiscal_year_end": "2026-08-30",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "COST",
   "fiscal_year": 2026,
   "item": "_unknown",
   "prelude": "Excerpts from COST FY2026 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000909832-26-000093/unknown#57",
     "title": "COST FY2026 10-K",
     "content": "LIQUIDITY AND CAPITAL RESOURCES\n\nThe following table summarizes our significant sources and uses of cash and cash equivalents:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net cash provided by operating activities | | | $ | 15,817 |  |  | | | $ | 13,335 |  |  | | | $ | 11,339 |  |\n| Net cash used in investing activities | | | (6,378) | |  |  | | | (5,311) | |  |  | | | (4,409) | |  |\n| Net
cash used in financing activities | | | (3,355) | |  |  | | | (3,775) | |  |  | | | (10,764) | |  |\n|\n\nOur primary sources of liquidity are cash flows from operations, cash and cash equivalents, and short-term investments. Cash and cash equivalents and short-term investments were $21,301 and
$15,284 at August 30, 2026, and August 31, 2025. Of these balances, unsettled credit and debit card receivables represented $2,842 and $2,670. These receivables generally settle within four days.\n\nMaterial contractual obligations arising in the normal course of business primarily consist of
purchase obligations, long-term debt and related interest payments, leases, and construction and land purchase obligations. See [Notes 4](#iae87f9b9600946fdb18e1436ed6ec90c_121) and [5](#iae87f9b9600946fdb18e1436ed6ec90c_124) to the consolidated financial statements included in Item 8 of this Report
for amounts outstanding on August 30, 2026, related to debt and leases.",
     "score": 0.5224
    },
    {
     "source": "sec://0000909832-26-000093/unknown#58",
     "title": "COST FY2026 10-K",
     "content": "Purchase obligations consist of contracts primarily related to merchandise, equipment, and third-party services, the majority of which are due in the next 12 months. Construction and land-purchase obligations consist of contracts primarily related to the development and opening of
new and relocated warehouses, the majority of which (other than leases) are due in the next 12 months.\n\n28\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nWe believe that our cash and investment positions and operating cash flow, with capacity under existing and available
credit agreements, will be sufficient to meet our liquidity and capital requirements for the foreseeable future and that our U.S. current and projected asset position is sufficient to meet our U.S. liquidity requirements.\n\nCash Flows from Operating Activities\n\nOur cash flow provided by
operations is primarily from net sales and membership fees. Cash flow used in operations generally consists of payments to merchandise suppliers, warehouse operating costs, including wages and employee benefits, utilities, credit and debit card processing fees, and operating leases. Cash used in
operations also includes payments for income taxes. Changes in our net investment in merchandise inventories (the difference between merchandise inventories and accounts payable) is impacted by several factors, including inventory levels and turnover, payment terms with suppliers, and early payments
to obtain discounts. Net cash provided by operating activities totaled $15,817 in 2026, compared to $13,335 in 2025. The increase was primarily due to higher operating income, as well as reduced net investment in merchandise inventories. The latter was a result of faster inventory turns and improved
payment terms with suppliers.\n\nCash Flows from Investing Activities\n\nNet cash used in investing activities totaled $6,378 in 2026, compared to $5,311 in 2025, and is primarily related to capital expenditures. Net cash from investing activities also includes purchases and maturities of short-term
investments.\n\nCapital Expenditure Plans",
     "score": 0.5091
    },
    {
     "source": "sec://0000909832-26-000093/unknown#59",
     "title": "COST FY2026 10-K",
     "content": "Capital Expenditure Plans\n\nOur primary requirements for capital are acquiring land, buildings, and equipment for new and remodeled warehouses, information systems, and manufacturing and distribution facilities. In 2026, we spent $6,435 on capital expenditures, and it is our
current intention to spend approximately $7,500 during fiscal 2027. These expenditures are expected to be financed with cash from operations, cash and cash equivalents, and short-term investments. We opened 28 new warehouses, including three relocations, in 2026, and plan to open up to 33 new
warehouses, including five relocations, in 2027. There can be no assurance that current expectations will be realized, and plans are subject to change upon further review of our capital expenditure needs and the economic environment.\n\nCash Flows from Financing Activities\n\nNet cash used in
financing activities totaled $3,355 in 2026, compared to $3,775 in 2025. Cash flow used in financing activities primarily related to the payment of dividends, repurchases of common stock, repayments of short-term borrowings and long-term debt, and withholding taxes on stock-based awards. Cash flow
provided by financing activities included proceeds from short-term borrowings and issuance of long-term debt.\n\nLong-term Debt\n\nProceeds from long-term debt in 2026 included three series of Guaranteed Senior Notes totaling approximately $500, at fixed interest rates ranging from 2.620% to 3.680%,
issued by our Japan subsidiary, as compared to no proceeds in 2025. Repayments of long-term debt in 2026 totaled $69, as compared to $103 in 2025.\n\nDividends\n\nCash dividends declared in 2026 totaled $2,458, $5.54 per share, as compared to $2,183, $4.92 per share, in 2025. In April 2026, the
Board of Directors increased our quarterly cash dividend from $1.30 to $1.47 per share.\n\n29\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nShare Repurchase Program",
     "score": 0.5297
    },
    {
     "source": "sec://0000909832-26-000093/unknown#60",
     "title": "COST FY2026 10-K",
     "content": "29\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nShare Repurchase Program\n\nOn January 19, 2023, the Board of Directors authorized a share repurchase program in the amount of $4,000, which expires in January 2027. During 2026 and 2025, we repurchased 891,000
and 943,000 shares of common stock, at an average price per share of $950.90 and $957.66, totaling $847 and $903. These amounts may differ from the accompanying consolidated statements of cash flows due to changes in unsettled repurchases at the end of each fiscal year. Purchases are made from time
to time, as conditions warrant, in the open market or in block purchases, pursuant to plans under SEC Rule 10b5-1. Repurchased shares are retired, in accordance with the Washington Business Corporation Act. The remaining amount available to be purchased under our approved plan was $1,115 at the end
of 2026.\n\nBank Credit Facilities and Commercial Paper Programs\n\nWe maintain bank credit facilities for working capital and general corporate purposes. At August 30, 2026, we had borrowing capacity under these facilities of $2,118, compared to $1,220 at the end of 2025. This increase was
primarily driven by the renewal and expansion of our U.S. revolving credit facility in August 2026, which increased total borrowing capacity from $400 to $1,000 and extended the maturity date to August 2027, as well as credit facility expansions in our Japan and Mexico subsidiaries. Our Canadian and
Other International operations maintain $1,012 of this capacity under bank credit facilities, of which $333 is guaranteed by the Company. There were no short-term borrowings outstanding under the bank credit facilities at the end of 2026. Short-term borrowings were immaterial at the end of 2025 and
were included in other current liabilities on the consolidated balance sheets.",
     "score": 0.4543
    },
    {
     "source": "sec://0000909832-26-000093/unknown#81",
     "title": "COST FY2026 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 52 Weeks Ended | | | | | | | | | | | | | | |\n|  | | | August 30,   2026 | | |  | | | August 31,   2025 |
| |  | | | September 1,   2024 | | |\n| CASH FLOWS FROM OPERATING ACTIVITIES | | |  | | |  | | |  | | |  | | |  | | |\n| Net income | | | $ | 9,226 |  |  | | | $ | 8,099 |  |  | | | $ | 7,367 |  |\n| Adjustments to reconcile net income to net cash provided by operating activities: | | |  | | |  | |
|  | | |  | | |  | | |\n| Depreciation and amortization | | | 2,674 | |  |  | | | 2,426 | |  |  | | | 2,237 | |  |\n| Non-cash lease expense | | | 318 | |  |  | | | 303 | |  |  | | | 315 | |  |\n| Stock-based compensation | | | 924 | |  |  | | | 860 | |  |  | | | 818 | |  |\n| Deferred income taxes
| | | 306 | |  |  | | | (108) | |  |  | | | (60) | |  |\n| Other non-cash operating activities, net | | | 49 | |  |  | | | (9) | |  |  | | | 51 | |  |\n| Changes in operating assets and liabilities: | | |  | | |  | | |  | | |  | | |  | | |",
     "score": 0.5131
    },
    {
     "source": "sec://0000909832-26-000093/unknown#82",
     "title": "COST FY2026 10-K",
     "content": "| Changes in operating assets and liabilities: | | |  | | |  | | |  | | |  | | |  | | |\n| Merchandise inventories | | | (1,153) | |  |  | | | 559 | |  |  | | | (2,068) | |  |\n| Accounts payable | | | 2,755 | |  |  | | | 404 | |  |  | | | 1,938 | |  |\n| Other operating assets and
liabilities, net | | | 718 | |  |  | | | 801 | |  |  | | | 741 | |  |\n| Net cash provided by operating activities | | | 15,817 | |  |  | | | 13,335 | |  |  | | | 11,339 | |  |\n| CASH FLOWS FROM INVESTING ACTIVITIES | | |  | | |  | | |  | | |  | | |  | | |\n| Additions to property and equipment | |
| (6,435) | |  |  | | | (5,498) | |  |  | | | (4,710) | |  |\n| Purchases of short-term investments | | | (788) | |  |  | | | (1,028) | |  |  | | | (1,470) | |  |\n| Maturities of short-term investments | | | 811 | |  |  | | | 1,141 | |  |  | | | 1,790 | |  |\n| Other investing activities, net | | |
34 | |  |  | | | 74 | |  |  | | | (19) | |  |\n| Net cash used in investing activities | | | (6,378) | |  |  | | | (5,311) | |  |  | | | (4,409) | |  |\n| CASH FLOWS FROM FINANCING ACTIVITIES | | |  | | |  | | |  | | |  | | |  | | |",
     "score": 0.5005
    },
    {
     "source": "sec://0000909832-26-000093/unknown#83",
     "title": "COST FY2026 10-K",
     "content": "| CASH FLOWS FROM FINANCING ACTIVITIES | | |  | | |  | | |  | | |  | | |  | | |\n| Repayments of short-term borrowings | | | (577) | |  |  | | | (862) | |  |  | | | (920) | |  |\n| Proceeds from short-term borrowings | | | 553 | |  |  | | | 816 | |  |  | | | 928 | |  |\n| Repayments
of long-term debt | | | (69) | |  |  | | | (103) | |  |  | | | (1,077) | |  |\n| Proceeds from issuance of long-term debt | | | 496 | |  |  | | | — | |  |  | | | 498 | |  |\n| Tax withholdings on stock-based awards | | | (361) | |  |  | | | (393) | |  |  | | | (315) | |  |\n| Repurchases of common
stock | | | (848) | |  |  | | | (903) | |  |  | | | (700) | |  |\n| Cash dividend payments | | | (2,458) | |  |  | | | (2,183) | |  |  | | | (9,041) | |  |\n| Financing lease payments and other financing activities, net | | | (91) | |  |  | | | (147) | |  |  | | | (137) | |  |\n| Net cash used in
financing activities | | | (3,355) | |  |  | | | (3,775) | |  |  | | | (10,764) | |  |\n| EFFECT OF EXCHANGE RATE CHANGES ON CASH AND CASH EQUIVALENTS | | | (38) | |  |  | | | 6 | |  |  | | | 40 | |  |\n| Net change in cash and cash equivalents | | | 6,046 | |  |  | | | 4,255 | |  |  | | | (3,794) |
|  |",
     "score": 0.4779
    },
    {
     "source": "sec://0000909832-26-000093/unknown#84",
     "title": "COST FY2026 10-K",
     "content": "| Net change in cash and cash equivalents | | | 6,046 | |  |  | | | 4,255 | |  |  | | | (3,794) | |  |\n| CASH AND CASH EQUIVALENTS BEGINNING OF YEAR | | | 14,161 | |  |  | | | 9,906 | |  |  | | | 13,700 | |  |\n| CASH AND CASH EQUIVALENTS END OF YEAR | | | $ | 20,207 |  |  | | | $
| 14,161 |  |  | | | $ | 9,906 |  |\n|  | | |  | | |  | | |  | | |  | | |  | | |\n| SUPPLEMENTAL DISCLOSURE OF CASH FLOW INFORMATION: | | |  | | |  | | |  | | |  | | |  | | |\n| Cash paid during the year for: | | |  | | |  | | |  | | |  | | |  | | |\n| Interest | | | $ | 103 |  |  | | | $ | 106 |  |
| | | $ | 129 |  |\n| Income taxes, net | | | $ | 2,839 |  |  | | | $ | 2,917 |  |  | | | $ | 2,319 |  |\n| SUPPLEMENTAL DISCLOSURE OF NON-CASH ACTIVITIES: | | |  | | |  | | |  | | |  | | |  | | |\n|\n| Capital expenditures included in liabilities | | | $ | 220 |  |  | | | $ | 193 |  |  | | | $ |
203 |  |",
     "score": 0.4297
    },
    {
     "source": "sec://0000909832-26-000093/unknown#111",
     "title": "COST FY2026 10-K",
     "content": "(2)Included in interest expense and merchandise costs in the consolidated statements of income.\n\nSupplemental cash flow information related to leases were as follows:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | ---
| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Cash paid for amounts included in the measurement of lease liabilities: | | |  | | |  | | |  | | |  | | |  | | |\n| Operating cash flows — operating leases | | | $ | 312 |  |  | | |
$ | 255 |  |  | | | $ | 274 |  |\n| Operating cash flows — finance leases | | | 62 | |  |  | | | 58 | |  |  | | | 58 | |  |\n| Financing cash flows — finance leases | | | 89 | |  |  | | | 147 | |  |  | | | 136 | |  |\n| Operating lease assets obtained in exchange for new or modified leases | | | 238
| |  |  | | | 294 | |  |  | | | 125 | |  |\n| Finance lease assets obtained in exchange for new or modified leases | | | 122 | |  |  | | | 131 | |  |  | | | 200 | |  |\n\nAs of August 30, 2026, future minimum payments during the next five fiscal years and thereafter are as follows:",
     "score": 0.442
    },
    {
     "source": "sec://0000909832-26-000093/unknown#112",
     "title": "COST FY2026 10-K",
     "content": "As of August 30, 2026, future minimum payments during the next five fiscal years and thereafter are as follows:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | Operating Leases(1) | | |  | | | Finance
Leases | | |\n| 2027 | | | $ | 252 |  |  | | | $ | 146 |  |\n| 2028 | | | 258 | |  |  | | | 142 | |  |\n| 2029 | | | 226 | |  |  | | | 130 | |  |\n| 2030 | | | 204 | |  |  | | | 118 | |  |\n| 2031 | | | 186 | |  |  | | | 97 | |  |\n| Thereafter | | | 2,399 | |  |  | | | 1,657 | |  |\n| Total(2) | |
| 3,525 | |  |  | | | 2,290 | |  |\n| Less amount representing interest | | | 919 | |  |  | | | 877 | |  |\n| Present value of lease liabilities | | | $ | 2,606 |  |  | | | $ | 1,413 |  |\n\n_______________\n\n(1)Operating lease payments have not been reduced by expected future sublease income of
$90.\n\n(2)Excludes $1,667 of lease payments for leases that have been signed but not commenced.\n\n54\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nNote 6—Equity\n\nDividends\n\nCash dividends declared in 2026 totaled $2,458 or $5.54 per share, as compared to $2,183 or $4.92
per share in 2025. Dividends in 2024 included a special dividend of $15 per share, resulting in a payment of $6,655. The Company's current quarterly dividend rate is $1.47 per share.\n\nStock Repurchase Programs",
     "score": 0.4562
    }
   ]
  }
 ]
}

[tool 4] sec_filing_search {"query": "fiscal 2026 dividends paid share repurchases debt repayments total cash returned to shareholders debt outstanding interest rates liquidity", "ticker": "WMT", "fiscal_year": 2026}
{
 "fiscal_year": 2026,
 "fiscal_year_end": "2026-01-31",
 "fiscal_year_source": "requested",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "WMT",
   "fiscal_year": 2026,
   "item": "Item 7",
   "prelude": "Excerpts from WMT FY2026 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000104169-26-000055/7#133",
     "title": "WMT FY2026 10-K · Item 7 · Liquidity",
     "content": "### Liquidity\n\nThe strength and stability of our operations have historically supplied us with a significant source of liquidity. Our cash flows provided by operating activities, supplemented with our long-term debt and short-term borrowings, have been sufficient to fund our
operations while allowing us to invest in activities that support the long-term growth of our operations. Generally, some or all of the remaining available cash flow has been used to fund dividends on our common stock and share repurchases. We believe our sources of liquidity will continue to be
sufficient to fund operations, finance our investment activities, pay dividends and fund our share repurchases for at least the next 12 months and for the foreseeable future.",
     "score": 0.5969,
     "subsection": "Liquidity"
    },
    {
     "source": "sec://0000104169-26-000055/7#141",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "Our total outstanding long-term debt increased $2.2 billion during fiscal 2026, primarily due to issuances of long-term debt. Refer to [Note 5](#i6e16e33efce1499a82f13fd9f63b74c6_160) to our Consolidated Financial Statements for details on the issuances of long-term
debt.\n\nEstimated contractual interest payments associated with our long-term debt amount to $17.3 billion, with approximately $1.7 billion expected to be paid in fiscal 2027. Estimated interest payments are based on our principal amounts and expected maturities of all debt outstanding as of
January 31, 2026, and assumes interest rates remain at current levels for our variable rate instruments.\n\n43\n\n\n\nDividends\n\nOur total dividend payments were $7.5 billion, $6.7 billion and $6.1 billion for fiscal 2026, 2025 and 2024, respectively. Effective February 19, 2026, the Company
approved the fiscal 2027 annual dividend of $0.99 per share, an increase over the fiscal 2026 annual dividend of $0.94 per share. For fiscal 2027, the annual dividend will be paid in four quarterly installments of $0.2475 per share, according to the following record and payable dates:\n\n|  |  |  |
|  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| Record Date | | |  | | | Payable Date | | |\n| March 20, 2026 | | |  | | | April 6, 2026 | | |\n| May 8, 2026 | | |  | | | May 26, 2026 | | |\n| August 21, 2026 | | |  | | | September 8, 2026 | | |\n| December 11, 2026 | |
|  | | | January 4, 2027 | | |\n\nCompany Share Repurchase Program",
     "score": 0.6646
    },
    {
     "source": "sec://0000104169-26-000055/7#142",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "Company Share Repurchase Program\n\nFrom time to time, the Company repurchases shares of its common stock under share repurchase programs authorized by the Company's Board of Directors. Any repurchased shares are constructively retired and returned to an unissued status. All
repurchases during fiscal 2026 were made under the $20.0 billion share repurchase program approved in November 2022, of which authorization for $4.0 billion of share repurchases remained as of January 31, 2026. In February 2026, the Board of Directors approved a new $30.0 billion share repurchase
authorization, which has no expiration date or other restrictions limiting the period over which the Company can make repurchases, and beginning February 23, 2026, replaced the remaining capacity under the prior authorization.\n\nWe regularly review share repurchase activity and consider several
factors in determining when to execute share repurchases, including, among other things, current cash needs, capacity for leverage, cost of borrowings, our results of operations and the market price of our common stock. We anticipate that a majority of the ongoing share repurchase program will be
funded through the Company's free cash flow.\n\nThe following table provides, on a settlement date basis, the number of shares repurchased, average price paid per share and total amount paid for share repurchases for fiscal 2026, 2025 and 2024:",
     "score": 0.5715
    },
    {
     "source": "sec://0000104169-26-000055/7#143",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "The following table provides, on a settlement date basis, the number of shares repurchased, average price paid per share and total amount paid for share repurchases for fiscal 2026, 2025 and 2024:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | ---
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | |  | | | Fiscal Years Ended January 31, | | | | | | | | | | | | | | |\n| (Amounts in millions, except per share data) | | |  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n|
Total number of shares repurchased | | |  | | | 85.0 | | |  | | | 61.9 | | |  | | | 54.6 | | |\n| Average price paid per share | | |  | | | $ | 95.13 |  |  | | | $ | 72.72 |  |  | | | $ | 50.87 |  |\n| Total amount paid for share repurchases | | |  | | | $ | 8,088 |  |  | | | $ | 4,494 |  |  | | | $
| 2,779 |  |\n\nDuring fiscal 2026, the Company repurchased $8.1 billion in shares of its common stock, an increase of $3.6 billion as compared to the same period in the previous fiscal year. The increase was primarily driven by opportunistic prices during the first quarter of fiscal 2026 as part of
the Company's long-term strategy.\n\nMaterial Cash Requirements",
     "score": 0.5871
    }
   ]
  },
  {
   "ticker": "WMT",
   "fiscal_year": 2026,
   "item": "Item 8",
   "prelude": "Excerpts from WMT FY2026 10-K, Item 8 (Financial Statements and Supplementary Data) — 6 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000104169-26-000055/8#248",
     "title": "WMT FY2026 10-K · Item 8",
     "content": "As of January 31, 2026, the Company also has approximately $3 billion in unrecognized compensation cost (based on grant-date fair value) primarily associated with share-based compensation plans of certain subsidiaries which contain performance or other conditions including vesting
upon an initial public offering. If such conditions are ultimately satisfied, unrecognized compensation cost would be recognized in the applicable reporting period.\n\nShare Repurchase Program\n\nFrom time to time, the Company repurchases shares of its common stock under share repurchase programs
authorized by the Company's Board of Directors. All repurchases during fiscal 2026 were made under the current $20.0 billion share repurchase program approved in November 2022, which had no expiration date or other restrictions limiting the period over which the Company can make repurchases. As of
January 31, 2026 authorization for $4.0 billion of share repurchases remained under the share repurchase program. Any repurchased shares are constructively retired and returned to an unissued status. In February 2026, the Board of Directors approved a new $30.0 billion share repurchase
authorization, which has no expiration date or other restrictions limiting the period over which the Company can make repurchases, and beginning February 23, 2026, replaced the remaining capacity under the prior authorization.\n\n65\n\n\n\nThe Company regularly reviews share repurchase activity and
considers several factors in determining when to execute share repurchases, including, among other things, current cash needs, capacity for leverage, cost of borrowings, results of operations and the market price of the Company's common stock. The following table provides, on a settlement date
basis, the number of shares repurchased, average price paid per share and total amount paid for share repurchases for fiscal 2026, 2025 and 2024:",
     "score": 0.5749
    },
    {
     "source": "sec://0000104169-26-000055/8#249",
     "title": "WMT FY2026 10-K · Item 8",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | |  | | | Fiscal Years Ended January 31, | | | | | | | | | | | | | | |\n| (Amounts
in millions, except per share data) | | |  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Total number of shares repurchased | | |  | | | 85.0 | |  |  | | | 61.9 | |  |  | | | 54.6 | |  |\n| Average price paid per share | | |  | | | $ | 95.13 |  |  | | | $ | 72.72 |  |  | | | $ | 50.87 |
|\n| Total cash paid for share repurchases | | |  | | | $ | 8,088 |  |  | | | $ | 4,494 |  |  | | | $ | 2,779 |  |",
     "score": 0.5958
    },
    {
     "source": "sec://0000104169-26-000055/8#255",
     "title": "WMT FY2026 10-K · Item 8",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- |\n|  | | |  | | | January 31, 2026 | | | | | | | | | | | | | | |  | | | January 31, 2025 | | | | | | | | |\n| (Amounts in millions) | | |  | | | Maturity Dates   By Fiscal Year | | |  | | | Amount | | |  | | | Average Rate(1) | | |  | | | Amount | | |  | | | Average Rate(1) | | |\n|
Unsecured debt | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |\n| Fixed | | |  | | | 2027 - 2054 | | |  | | | $ | 32,032 |  |  | | | 3.9% | | |  | | | $ | 31,406 |  |  | | | 3.8% | | |\n| Variable | | |  | | | 2028 | | |  | | | 750 | |  |  | | | 4.1% | | |  | | | — | |  |
| | | —% | | |\n| Total U.S. dollar denominated | | |  | | |  | | |  | | | 32,782 | |  |  | | |  | | |  | | | 31,406 | |  |  | | |  | | |",
     "score": 0.5778
    },
    {
     "source": "sec://0000104169-26-000055/8#257",
     "title": "WMT FY2026 10-K · Item 8",
     "content": "(1)The average rate represents the weighted-average stated rate for each corresponding debt category, based on year-end balances and year-end interest rates.\n\n(2)Includes deferred loan costs, discounts, fair value hedges, foreign-held debt and secured debt.\n\nAnnual maturities of
long-term debt during the next five years and thereafter are as follows:\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| (Amounts in millions) | | |  | | | Annual | | |\n| Fiscal Year | | |  | | | Maturities | | |\n| 2027 | | |  | | | $ | 3,542 |  |\n|
2028 | | |  | | | 3,237 | |  |\n| 2029 | | |  | | | 3,389 | |  |\n| 2030 | | |  | | | 2,143 | |  |\n| 2031 | | |  | | | 2,600 | |  |\n| Thereafter | | |  | | | 23,255 | |  |\n| Total | | |  | | | $ | 38,166 |  |\n\nDebt Issuances\n\nInformation on significant issuances of long-term debt during
fiscal 2026, for general corporate purposes, is as follows:",
     "score": 0.5906
    },
    {
     "source": "sec://0000104169-26-000055/8#258",
     "title": "WMT FY2026 10-K · Item 8",
     "content": "Debt Issuances\n\nInformation on significant issuances of long-term debt during fiscal 2026, for general corporate purposes, is as follows:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| (Amounts in millions) | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |\n| Issue Date | | |  | | | Principal Amount | | |  | | | Maturity Date | | |  | | | Interest Rate | | |
| | | Net Proceeds | | |\n| April 28, 2025 | | |  | | | $750 | | |  | | | April 28, 2027 | | |  | | | Floating | | |  | | | $ | 749 |  |\n| April 28, 2025 | | |  | | | $750 | | |  | | | April 28, 2027 | | |  | | | 4.100% | | |  | | | 748 | |  |\n| April 28, 2025 | | |  | | | $1,000 | | |  | | |
April 28, 2030 | | |  | | | 4.350% | | |  | | | 993 | |  |\n| April 28, 2025 | | |  | | | $1,500 | | |  | | | April 28, 2035 | | |  | | | 4.900% | | |  | | | 1,493 | |  |\n| Total | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | | $ | 3,983 |  |",
     "score": 0.591
    },
    {
     "source": "sec://0000104169-26-000055/8#259",
     "title": "WMT FY2026 10-K · Item 8",
     "content": "These issuances are senior, unsecured notes which rank equally with all other senior, unsecured debt obligations of the Company, and are not convertible or exchangeable. These issuances do not contain any financial covenants which restrict the Company's ability to pay dividends or
repurchase Company stock.\n\nMaturities\n\nThe following tables provide details of significant long-term debt maturities during fiscal 2026 and 2025, respectively:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| (Amounts in millions) | | |  | | |  | | |  | | |  | | |  | | |  | | |\n| Maturity Date | | |  | | | Principal Amount | | |  | | | Interest Rate | | |  | | | Repayment | | |\n| June 26, 2025 | | |  | | | $875 | | |  | | | 3.550% | | |  |
| | $ | 875 |  |\n| September 9, 2025 | | |  | | | $1,750 | | |  | | | 3.900% | | |  | | | 1,750 | |  |\n|\n|\n| Total | | |  | | |  | | |  | | |  | | |  | | | $ | 2,625 |  |\n\n67",
     "score": 0.6185
    }
   ]
  }
 ]
}

[tool 5] sec_filing_search {"query": "fiscal 2026 total debt cash and cash equivalents short-term investments dividends share repurchases capital allocation liquidity", "ticker": "COST", "fiscal_year": 2026}
{
 "fiscal_year": 2026,
 "fiscal_year_end": "2026-08-30",
 "fiscal_year_source": "requested",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "COST",
   "fiscal_year": 2026,
   "item": "_unknown",
   "prelude": "Excerpts from COST FY2026 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000909832-26-000093/unknown#57",
     "title": "COST FY2026 10-K",
     "content": "LIQUIDITY AND CAPITAL RESOURCES\n\nThe following table summarizes our significant sources and uses of cash and cash equivalents:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net cash provided by operating activities | | | $ | 15,817 |  |  | | | $ | 13,335 |  |  | | | $ | 11,339 |  |\n| Net cash used in investing activities | | | (6,378) | |  |  | | | (5,311) | |  |  | | | (4,409) | |  |\n| Net
cash used in financing activities | | | (3,355) | |  |  | | | (3,775) | |  |  | | | (10,764) | |  |\n|\n\nOur primary sources of liquidity are cash flows from operations, cash and cash equivalents, and short-term investments. Cash and cash equivalents and short-term investments were $21,301 and
$15,284 at August 30, 2026, and August 31, 2025. Of these balances, unsettled credit and debit card receivables represented $2,842 and $2,670. These receivables generally settle within four days.\n\nMaterial contractual obligations arising in the normal course of business primarily consist of
purchase obligations, long-term debt and related interest payments, leases, and construction and land purchase obligations. See [Notes 4](#iae87f9b9600946fdb18e1436ed6ec90c_121) and [5](#iae87f9b9600946fdb18e1436ed6ec90c_124) to the consolidated financial statements included in Item 8 of this Report
for amounts outstanding on August 30, 2026, related to debt and leases.",
     "score": 0.6076
    },
    {
     "source": "sec://0000909832-26-000093/unknown#58",
     "title": "COST FY2026 10-K",
     "content": "Purchase obligations consist of contracts primarily related to merchandise, equipment, and third-party services, the majority of which are due in the next 12 months. Construction and land-purchase obligations consist of contracts primarily related to the development and opening of
new and relocated warehouses, the majority of which (other than leases) are due in the next 12 months.\n\n28\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nWe believe that our cash and investment positions and operating cash flow, with capacity under existing and available
credit agreements, will be sufficient to meet our liquidity and capital requirements for the foreseeable future and that our U.S. current and projected asset position is sufficient to meet our U.S. liquidity requirements.\n\nCash Flows from Operating Activities\n\nOur cash flow provided by
operations is primarily from net sales and membership fees. Cash flow used in operations generally consists of payments to merchandise suppliers, warehouse operating costs, including wages and employee benefits, utilities, credit and debit card processing fees, and operating leases. Cash used in
operations also includes payments for income taxes. Changes in our net investment in merchandise inventories (the difference between merchandise inventories and accounts payable) is impacted by several factors, including inventory levels and turnover, payment terms with suppliers, and early payments
to obtain discounts. Net cash provided by operating activities totaled $15,817 in 2026, compared to $13,335 in 2025. The increase was primarily due to higher operating income, as well as reduced net investment in merchandise inventories. The latter was a result of faster inventory turns and improved
payment terms with suppliers.\n\nCash Flows from Investing Activities\n\nNet cash used in investing activities totaled $6,378 in 2026, compared to $5,311 in 2025, and is primarily related to capital expenditures. Net cash from investing activities also includes purchases and maturities of short-term
investments.\n\nCapital Expenditure Plans",
     "score": 0.5645
    },
    {
     "source": "sec://0000909832-26-000093/unknown#59",
     "title": "COST FY2026 10-K",
     "content": "Capital Expenditure Plans\n\nOur primary requirements for capital are acquiring land, buildings, and equipment for new and remodeled warehouses, information systems, and manufacturing and distribution facilities. In 2026, we spent $6,435 on capital expenditures, and it is our
current intention to spend approximately $7,500 during fiscal 2027. These expenditures are expected to be financed with cash from operations, cash and cash equivalents, and short-term investments. We opened 28 new warehouses, including three relocations, in 2026, and plan to open up to 33 new
warehouses, including five relocations, in 2027. There can be no assurance that current expectations will be realized, and plans are subject to change upon further review of our capital expenditure needs and the economic environment.\n\nCash Flows from Financing Activities\n\nNet cash used in
financing activities totaled $3,355 in 2026, compared to $3,775 in 2025. Cash flow used in financing activities primarily related to the payment of dividends, repurchases of common stock, repayments of short-term borrowings and long-term debt, and withholding taxes on stock-based awards. Cash flow
provided by financing activities included proceeds from short-term borrowings and issuance of long-term debt.\n\nLong-term Debt\n\nProceeds from long-term debt in 2026 included three series of Guaranteed Senior Notes totaling approximately $500, at fixed interest rates ranging from 2.620% to 3.680%,
issued by our Japan subsidiary, as compared to no proceeds in 2025. Repayments of long-term debt in 2026 totaled $69, as compared to $103 in 2025.\n\nDividends\n\nCash dividends declared in 2026 totaled $2,458, $5.54 per share, as compared to $2,183, $4.92 per share, in 2025. In April 2026, the
Board of Directors increased our quarterly cash dividend from $1.30 to $1.47 per share.\n\n29\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nShare Repurchase Program",
     "score": 0.6159
    },
    {
     "source": "sec://0000909832-26-000093/unknown#60",
     "title": "COST FY2026 10-K",
     "content": "29\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nShare Repurchase Program\n\nOn January 19, 2023, the Board of Directors authorized a share repurchase program in the amount of $4,000, which expires in January 2027. During 2026 and 2025, we repurchased 891,000
and 943,000 shares of common stock, at an average price per share of $950.90 and $957.66, totaling $847 and $903. These amounts may differ from the accompanying consolidated statements of cash flows due to changes in unsettled repurchases at the end of each fiscal year. Purchases are made from time
to time, as conditions warrant, in the open market or in block purchases, pursuant to plans under SEC Rule 10b5-1. Repurchased shares are retired, in accordance with the Washington Business Corporation Act. The remaining amount available to be purchased under our approved plan was $1,115 at the end
of 2026.\n\nBank Credit Facilities and Commercial Paper Programs\n\nWe maintain bank credit facilities for working capital and general corporate purposes. At August 30, 2026, we had borrowing capacity under these facilities of $2,118, compared to $1,220 at the end of 2025. This increase was
primarily driven by the renewal and expansion of our U.S. revolving credit facility in August 2026, which increased total borrowing capacity from $400 to $1,000 and extended the maturity date to August 2027, as well as credit facility expansions in our Japan and Mexico subsidiaries. Our Canadian and
Other International operations maintain $1,012 of this capacity under bank credit facilities, of which $333 is guaranteed by the Company. There were no short-term borrowings outstanding under the bank credit facilities at the end of 2026. Short-term borrowings were immaterial at the end of 2025 and
were included in other current liabilities on the consolidated balance sheets.",
     "score": 0.599
    },
    {
     "source": "sec://0000909832-26-000093/unknown#74",
     "title": "COST FY2026 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | August 30,   2026 | | |  | | | August 31,   2025 | | |\n| ASSETS | | |  | | |  | | |  | | |\n| CURRENT ASSETS | | |  | | |  | | |  | | |\n| Cash and cash
equivalents | | | $ | 20,207 |  |  | | | $ | 14,161 |  |\n| Short-term investments | | | 1,094 | |  |  | | | 1,123 | |  |\n| Receivables, net | | | 3,959 | |  |  | | | 3,203 | |  |\n| Merchandise inventories | | | 19,324 | |  |  | | | 18,116 | |  |\n| Other current assets | | | 1,998 | |  |  | | |
1,777 | |  |\n| Total current assets | | | 46,582 | |  |  | | | 38,380 | |  |\n| OTHER ASSETS | | |  | | |  | | |  | | |\n| Property and equipment, net | | | 35,633 | |  |  | | | 31,909 | |  |\n| Operating lease right-of-use assets | | | 2,697 | |  |  | | | 2,725 | |  |\n| Other long-term assets | |
| 4,133 | |  |  | | | 4,085 | |  |\n| TOTAL ASSETS | | | $ | 89,045 |  |  | | | $ | 77,099 |  |\n| LIABILITIES AND EQUITY | | |  | | |  | | |  | | |\n| CURRENT LIABILITIES | | |  | | |  | | |  | | |\n| Accounts payable | | | $ | 22,591 |  |  | | | $ | 19,783 |  |",
     "score": 0.5623
    },
    {
     "source": "sec://0000909832-26-000093/unknown#79",
     "title": "COST FY2026 10-K",
     "content": "- Repurchases of common stock (891) — (20) — (827) (847)\n- Cash dividend declared — — — — (2,458) (2,458)\n- BALANCE AT AUGUST 30, 2026 443,266 $ 2 $ 8,830 $ (1,620) $ 28,591 $ 35,803",
     "score": 0.5523
    },
    {
     "source": "sec://0000909832-26-000093/unknown#81",
     "title": "COST FY2026 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 52 Weeks Ended | | | | | | | | | | | | | | |\n|  | | | August 30,   2026 | | |  | | | August 31,   2025 |
| |  | | | September 1,   2024 | | |\n| CASH FLOWS FROM OPERATING ACTIVITIES | | |  | | |  | | |  | | |  | | |  | | |\n| Net income | | | $ | 9,226 |  |  | | | $ | 8,099 |  |  | | | $ | 7,367 |  |\n| Adjustments to reconcile net income to net cash provided by operating activities: | | |  | | |  | |
|  | | |  | | |  | | |\n| Depreciation and amortization | | | 2,674 | |  |  | | | 2,426 | |  |  | | | 2,237 | |  |\n| Non-cash lease expense | | | 318 | |  |  | | | 303 | |  |  | | | 315 | |  |\n| Stock-based compensation | | | 924 | |  |  | | | 860 | |  |  | | | 818 | |  |\n| Deferred income taxes
| | | 306 | |  |  | | | (108) | |  |  | | | (60) | |  |\n| Other non-cash operating activities, net | | | 49 | |  |  | | | (9) | |  |  | | | 51 | |  |\n| Changes in operating assets and liabilities: | | |  | | |  | | |  | | |  | | |  | | |",
     "score": 0.5332
    },
    {
     "source": "sec://0000909832-26-000093/unknown#86",
     "title": "COST FY2026 10-K",
     "content": "Reclassification\n\nReclassifications were made to the 2025 consolidated balance sheet and the 2025 and 2024 consolidated statements of cash flows to conform with current year presentation.\n\nCash and Cash Equivalents\n\nThe Company considers as cash and cash equivalents all cash
on deposit, highly liquid investments with a maturity of three months or less at the date of purchase, and proceeds due from credit and debit card transactions with settlement terms of up to four days. Credit and debit card receivables were $2,842 and $2,670 at the end of 2026 and 2025.\n\nShort-
Term Investments\n\nShort-term investments generally consist of debt securities (U.S. government and agency securities), with maturities at the date of purchase of three months to ten years. Investments with maturities beyond five years may be classified, based on the Company’s determination, as
short-term based on their highly liquid nature and because they represent the investment of cash that is available for current operations.\n\n42\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nShort-term investments classified as available-for-sale are recorded at fair value
using the specific identification method with the unrealized gains and losses reflected in accumulated other comprehensive income (loss) until realized. Realized gains and losses from the sale of available-for-sale securities, if any, are determined on a specific identification basis and are
recorded in interest income and other, net in the consolidated statements of income. These available-for-sale investments have a low level of inherent credit risk given they are issued by the U.S. government and agencies. Changes in their fair value are primarily attributable to changes in interest
rates and market liquidity. Short-term investments classified as held-to-maturity are financial instruments that the Company has the intent and ability to hold to maturity and are reported net of any related amortization and are not remeasured to fair value on a recurring basis.\n\nThe Company
periodically evaluates unrealized losses in its investment securities for credit impairment, using both qualitative and quantitative criteria. In the event a security is deemed to be impaired as the result of a credit loss, the Company recognizes the loss in interest income and other, net in the
consolidated statements of income.\n\nFair Value of Financial Instruments",
     "score": 0.5422
    },
    {
     "source": "sec://0000909832-26-000093/unknown#106",
     "title": "COST FY2026 10-K",
     "content": "In 2024, the Company repaid the $1,000 outstanding principal balance on its 2.750% Senior Notes.\n\nAt the end of 2026 and 2025, the fair value of the Company's long-term debt, including the current portion, was $5,689 and $5,370. The carrying value of long-term debt consisted of
the following:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |\n| 3.000% Senior Notes due May 2027 | | | $ | 1,000 |  |  | | | $ | 1,000 |  |\n| 1.375% Senior Notes due June 2027 | | | 1,250 |
|  |  | | | 1,250 | |  |\n| 1.600% Senior Notes due April 2030 | | | 1,750 | |  |  | | | 1,750 | |  |\n| 1.750% Senior Notes due April 2032 | | | 1,000 | |  |  | | | 1,000 | |  |\n| Other long-term debt | | | 1,175 | |  |  | | | 805 | |  |\n| Total long-term debt | | | 6,175 | |  |  | | | 5,805 | |
|\n| Less unamortized debt discounts and issuance costs | | | 13 | |  |  | | | 17 | |  |\n| Less current portion(1) | | | 2,248 | |  |  | | | 75 | |  |\n| Long-term debt, excluding current portion | | | $ | 3,914 |  |  | | | $ | 5,713 |  |_____________\n\n(1)Net of unamortized debt discounts and
issuance costs.\n\n52\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nMaturities of long-term debt during the next five fiscal years and thereafter are as follows:",
     "score": 0.5341
    },
    {
     "source": "sec://0000909832-26-000093/unknown#112",
     "title": "COST FY2026 10-K",
     "content": "As of August 30, 2026, future minimum payments during the next five fiscal years and thereafter are as follows:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | Operating Leases(1) | | |  | | | Finance
Leases | | |\n| 2027 | | | $ | 252 |  |  | | | $ | 146 |  |\n| 2028 | | | 258 | |  |  | | | 142 | |  |\n| 2029 | | | 226 | |  |  | | | 130 | |  |\n| 2030 | | | 204 | |  |  | | | 118 | |  |\n| 2031 | | | 186 | |  |  | | | 97 | |  |\n| Thereafter | | | 2,399 | |  |  | | | 1,657 | |  |\n| Total(2) | |
| 3,525 | |  |  | | | 2,290 | |  |\n| Less amount representing interest | | | 919 | |  |  | | | 877 | |  |\n| Present value of lease liabilities | | | $ | 2,606 |  |  | | | $ | 1,413 |  |\n\n_______________\n\n(1)Operating lease payments have not been reduced by expected future sublease income of
$90.\n\n(2)Excludes $1,667 of lease payments for leases that have been signed but not commenced.\n\n54\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nNote 6—Equity\n\nDividends\n\nCash dividends declared in 2026 totaled $2,458 or $5.54 per share, as compared to $2,183 or $4.92
per share in 2025. Dividends in 2024 included a special dividend of $15 per share, resulting in a payment of $6,655. The Company's current quarterly dividend rate is $1.47 per share.\n\nStock Repurchase Programs",
     "score": 0.6235
    }
   ]
  }
 ]
}
----- END EVIDENCE F0067 -----

----- BEGIN ANSWER F0067 -----
## 結論：好市多（COST）較穩；沃爾瑪（WMT）規模與融資能力更強，但現金流對資本支出、營運資金與外部融資的依賴較高

以下以兩家公司最新 FY2026 10-K 為基礎：沃爾瑪財年截至 **2026-01-31**，好市多財年截至 **2026-08-30**。

### 一、現金流品質：好市多較佳

| 指標，FY2026 | 沃爾瑪 | 好市多 |
|---|---:|---:|
| 營業現金流 | $41.6B | $15.8B |
| 資本支出 | $26.6B | $6.4B |
| 自由現金流 | $14.9B | 約 $9.4B |
| 營業現金流／淨利 | 約 1.87 倍 | 約 1.71 倍 |
| 自由現金流／淨利 | 約 67% | 約 102% |

沃爾瑪的絕對營業現金流遠高於好市多，但其資本支出也非常龐大。FY2026 營業現金流為 **$41.565B**，扣除 **$26.642B** 資本支出後，自由現金流僅 **$14.923B**；公司也明確說明，資本支出增加主要是為了全通路成長策略。[1][2]

好市多的營業現金流為 **$15.817B**，資本支出為 **$6.435B**，因此粗略自由現金流約 **$9.382B**。換言之，好市多只需消耗約四成營業現金流進行資本投資，沃爾瑪則接近三分之二。這使好市多在景氣轉弱時，更容易保留現金、維持股東回饋或降低負債。[3][4]

**現金流來源的可重複性方面，好市多也略勝。** 好市多表示，FY2026 營業現金流增加，主要來自營業利益成長、存貨周轉加快及供應商付款條件改善；這些因素至少部分反映營運效率改善。[5] 沃爾瑪則提到，現金流增加除了營業利益成長，也受到較低現金稅款及付款時點影響；其中「付款時點」與稅款因素的持續性相對較弱。[6]

不過，兩家公司都有大型零售商常見的負營運資金特徵，不能單純把高營業現金流全部視為高品質。好市多 FY2026 應付帳款增加 **$2.755B**，而存貨增加造成 **$1.153B** 現金流出，表示供應商信用仍是現金流的重要支撐。[7] 沃爾瑪則明確表示其營運資金通常為赤字，依靠存貨週轉、資本市場及供應商付款安排來支持營運。[8]

### 二、資本配置：好市多的安全邊際較厚

#### 沃爾瑪

沃爾瑪 FY2026：

- 股利支付：**$7.5B**
- 股票回購：**$8.1B**
- 兩者合計約 **$15.6B**
- 自由現金流：約 **$14.9B**

也就是說，單看股利與回購，現金回饋已略高於當年自由現金流，尚未計入其他投資、債務償還及流動性需求。沃爾瑪仍有很強的融資能力，但在資本支出維持高檔時，股東回饋的韌性部分依賴現金餘額、發債或商業票據市場。[9][10]

沃爾瑪的優勢是規模、信用評等與融資管道。FY2026 10-K 顯示，其長期債務約 **$38.2B**，未來預估長期債務利息支付約 **$17.3B**；公司也表示，營業現金流、短期借款及資本市場融資足以支持營運、投資、股利及回購。[11][12] 因此，沃爾瑪不是「缺乏融資能力」，而是其資本配置對融資市場和高額資本支出的敏感度較高。

#### 好市多

好市多 FY2026：

- 股利支付：約 **$2.458B**
- 股票回購：約 **$0.847B**
- 兩者合計約 **$3.305B**
- 自由現金流：約 **$9.382B**

股利與回購只消耗自由現金流約三成五，仍留下約 **$6.1B** 的緩衝，可用於擴張、增加現金、償債或應對景氣波動。[13][14]

此外，好市多在 FY2026 年底持有現金及短期投資合計約 **$21.3B**，長期債務帳面金額約 **$6.2B**；公司亦表示，其現金、投資及營業現金流足以支應可預見的流動性和資本需求。[15][16] 這種「高現金、低負債、低股東回饋壓力」的組合，使其資本配置更有彈性。

需要注意的是，好市多 FY2027 計畫將資本支出提高至約 **$7.5B**，並計畫開設最多 33 家新倉庫；若擴張速度加快，資本支出仍會上升。[17] 但以目前自由現金流和資產負債表來看，這項擴張尚未明顯壓縮其財務安全邊際。

### 三、抗壓性比較

**好市多較穩的原因：**

1. 資本支出占營業現金流比例較低。
2. 自由現金流高於淨利，現金轉換較完整。
3. 股利加回購明顯低於自由現金流，資本配置有較大緩衝。
4. 現金及短期投資約為長期債務的數倍。
5. 現金流改善部分來自營運效率，如庫存週轉與付款條件。

**沃爾瑪仍然很強，但穩定性略低於好市多：**

1. 營業現金流絕對規模最大，且有很強的信用與融資能力。
2. 但資本支出巨大，未來仍需持續投入自動化、電商、供應鏈及門店。
3. 股利與回購金額已接近或略高於自由現金流。
4. 負營運資金、短期借款及長期債務使其對供應商信用與資本市場更敏感。
5. 最新現金流增長有部分來自付款時點與稅款因素，品質不如單純由營業利益和效率改善驅動。

## 最終判斷

若問題是「哪一家在不景氣、資本市場收緊或必須降低投資時，仍能維持股利、回購和擴張？」答案是：**好市多較穩，資本配置韌性較高。**

若問題是「哪一家擁有更大的絕對現金產生能力與融資能力？」答案則是：**沃爾瑪更強。**

因此可以概括為：

- **現金流規模：沃爾瑪勝**
- **自由現金流轉換品質：好市多勝**
- **資產負債表安全邊際：好市多勝**
- **融資能力與系統重要性：沃爾瑪勝**
- **整體現金流品質與資本配置韌性：好市多勝**

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt  
[8]: SEC 10-K excerpt  
[9]: SEC 10-K excerpt  
[10]: SEC 10-K excerpt  
[11]: SEC 10-K excerpt  
[12]: SEC 10-K excerpt  
[13]: SEC 10-K excerpt  
[14]: SEC 10-K excerpt  
[15]: SEC 10-K excerpt  
[16]: SEC 10-K excerpt  
[17]: SEC 10-K excerpt
----- END ANSWER F0067 -----

===== ITEM F0068 =====

QUESTION:
好市多真正的賺錢核心到底是什麼？會員費的重要性有多高？

----- BEGIN EVIDENCE F0068 -----
[tool 0] sec_filing_search {"query": "core profit engine membership model membership fees renewal rates gross margins merchandise sales operating income and why membership fees are important", "ticker": "COST", "fiscal_year": null}
{
 "fiscal_year": 2026,
 "fiscal_year_end": "2026-08-30",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "COST",
   "fiscal_year": 2026,
   "item": "_unknown",
   "prelude": "Excerpts from COST FY2026 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000909832-26-000093/unknown#3",
     "title": "COST FY2026 10-K",
     "content": "Certain financial information for our segments and geographic areas is included in [Note 11](#iae87f9b9600946fdb18e1436ed6ec90c_142) to the consolidated financial statements included in Item 8 of this Report.\n\nMembership\n\nOur members may utilize their memberships at all of our
warehouses and e-commerce sites. Our annual fee for memberships is $65 in the U.S., varies in other countries and includes a free household card.\n\nMembership at the end of 2026, 2025, and 2024 was made up of the following (in thousands):\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Paid members1 | | | 84,100 | |  |  | | | 81,000 | |  |  | | | 76,200 | |  |\n| Household cards | | | 66,300 | |  |  | | |
64,200 | |  |  | | | 60,600 | |  |\n| Total cardholders | | | 150,400 | |  |  | | | 145,200 | |  |  | | | 136,800 | |  |\n\n_______________\n\n(1)These membership counts include active memberships as well as memberships that have expired and not renewed within the 12 months prior to the reporting
date. These expired memberships make up a small percentage of membership counts, and many of them are subsequently renewed.\n\nPaid members, in most countries, are eligible to upgrade to an Executive membership for an additional annual fee. These members earn an Executive reward, generally 2% on
qualified purchases, subject to an annual maximum value, redeemable at Costco warehouses. Executive members represented 42,300, 38,700, and 35,400 of total paid members in 2026, 2025, and 2024. The penetration of sales to Executive members represented approximately 75.2% of worldwide net sales in
2026.",
     "score": 0.5295
    },
    {
     "source": "sec://0000909832-26-000093/unknown#4",
     "title": "COST FY2026 10-K",
     "content": "Our member renewal rate was 92.3% in the U.S. and Canada and 89.8% worldwide at the end of 2026. This rate is a trailing calculation that captures renewals during the period seven to eighteen months prior to the reporting date. Memberships that have an expiration date in the six
months prior to the end of our reporting period are excluded from this calculation, regardless of whether or not they have been renewed. Although most members renew prior to expiration, the vast majority of those who renew late do so within six months of expiration. The timing of renewal after
expiration is impacted by a variety of factors, such as warehouse openings and promotional activity.\n\n5\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nHuman Capital\n\n“Take Care of Our Employees,” is a key component of our code of ethics and is fundamental to our commitment
to “Take Care of Our Members.” Compensation and benefits for employees is our largest expense after the cost of merchandise and is carefully monitored.\n\nEmployee Base\n\nAt the end of 2026, we employed 355,000 employees worldwide. Approximately 95% are employed in our membership warehouses and
distribution channels. Around 5% are represented by unions. We also utilize seasonal employees.\n\nThe total number of employees by segment was:",
     "score": 0.4763
    },
    {
     "source": "sec://0000909832-26-000093/unknown#14",
     "title": "COST FY2026 10-K",
     "content": "Our failure to maintain membership growth, loyalty, brand recognition, and our culture could adversely affect our results of operations.\n\nMembership loyalty and growth are essential to our business. The extent to which we achieve growth in our membership base, increase the
penetration of Executive membership, and sustain high renewal rates materially influences our profitability. Achieving these metrics relies heavily on member trust and our long-standing culture focused on value, integrity, member service, and always striving to do what is right. Damage to our
brands, reputation, or culture may negatively impact comparable sales, diminish member trust, and reduce renewal rates and, accordingly, net sales and membership fee revenue, negatively impacting our results of operations.\n\nWe sell many products under our Kirkland Signature brand. Maintaining
consistent product quality, competitive pricing, and availability of these products is essential to developing and maintaining member loyalty. These products also generally carry higher margins than national brand products and represent a growing portion of our overall sales. If the Kirkland
Signature brand experiences a loss of member acceptance or confidence, our sales and gross margin results could be adversely affected.\n\nDisruptions in merchandise distribution or processing, packaging, manufacturing, and other facilities could adversely affect sales and member satisfaction.\n\nWe
depend on the orderly operation of the merchandise receiving and distribution process, primarily through our depots. We also rely upon processing, packaging, manufacturing and other facilities to support our business, which includes the production of certain private-label items. Although we believe
that our operations are efficient, disruptions due to extreme weather, pandemics or other catastrophic events, labor issues, work stoppage, or other shipping problems may result in delays in the production and delivery of merchandise to and the operation of our warehouses, which could adversely
affect sales and the satisfaction of our members. Our e-commerce operations depend heavily on logistics providers, both internal and external, and are negatively affected when services are unable to be provided in a timely fashion.\n\nWe may not timely identify or effectively respond to consumer
tastes and preferences, which could negatively affect our relationship with our members, the demand for our products and services, and our market share.",
     "score": 0.4847
    },
    {
     "source": "sec://0000909832-26-000093/unknown#43",
     "title": "COST FY2026 10-K",
     "content": "We believe that the most important driver of our profitability is increasing net sales, particularly comparable sales. Net sales includes our core merchandise categories (foods and sundries, non-foods, and fresh foods), warehouse ancillary (gasoline, pharmacy, food court, optical,
hearing aids, and tire installation), and other businesses (e-commerce, business centers, travel, and other). E-commerce and business center sales are allocated to the appropriate merchandise categories in the Net Sales discussion. The Executive reward earned by our Executive members reduces net
sales and is allocated to the category in which the reward is generated (core merchandise categories, warehouse ancillary, and other businesses). Comparable sales is defined as net sales from warehouses operating for more than one year, including remodels, relocations, and expansions. Digitally-
enabled comparable sales is defined as sales initiated through a digital device, whether fulfilled through a warehouse, distribution center, or Costco Travel, operating for more than one year. Comparable sales metrics are intended as supplemental information and are not a substitute for net sales
presented in accordance with U.S. generally accepted accounting principles (U.S. GAAP) and should be reviewed in conjunction with results reported in accordance with U.S. GAAP. Comparable sales growth is achieved through increasing shopping frequency from new and existing members and the amount they
spend on each visit (average ticket). Sales comparisons can also be particularly influenced by certain factors that are beyond our control: fluctuations in currency exchange rates (with respect to our international operations) and inflation or deflation in the cost of gasoline and associated
competitive conditions. The higher our comparable sales exclusive of these items, the more we can leverage our selling, general and administrative (SG&A) expenses, reducing them as a percentage of sales and enhancing profitability. Generating comparable sales growth is foremost a question of making
available the right merchandise at the right prices, a skill that we believe we have repeatedly demonstrated over the long-term. Another substantial factor in net sales growth is the health of the economies in which we do business, including the effects of inflation or deflation, especially the
United States. Net sales growth and gross margins are also impacted by competition, which is vigorous and widespread, across a wide range of global, national, and regional wholesalers and retailers, including those with e-commerce operations. While we cannot control or reliably predict general
economic health or changes in competition, we believe that we have been successful, historically, in adapting our business to these changes, such as through adjustments to our pricing and merchandise mix, including increasing the penetration of our private-label",
     "score": 0.5236
    },
    {
     "source": "sec://0000909832-26-000093/unknown#45",
     "title": "COST FY2026 10-K",
     "content": "Our philosophy is to provide our members with quality goods and services at competitive prices. We do not focus in the short-term on maximizing prices charged, but instead seek to maintain what we believe is a perception among our members of our “pricing authority” – consistently
providing the most competitive values. Our net sales and gross margin are influenced in part by our merchandising and pricing strategies in response to cost increases. Those strategies can include, but are not limited to, working with our suppliers to share in absorbing cost increases, earlier-than-
usual purchasing and in greater volumes, sourcing in the countries and regions where items are sold, as well as passing cost increases on to our members. Our investments in merchandise pricing may include reducing prices on merchandise to drive sales or meet competition and holding prices steady
despite cost increases instead of passing the increases on to our members, negatively impacting gross margin and gross margin as a percentage of\n\n23\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nnet sales (gross margin percentage) in the near term. Gross margin is also
impacted by our digitally-enabled businesses, domestically and internationally, some of which have a lower gross-margin percentage than our warehouse operations.\n\nGovernment actions in various countries relating to tariffs affect the costs of some of our merchandise. The degree of our exposure is
dependent on (among other things) the type of goods, rates imposed, and timing of the tariffs. Higher tariffs are more likely to adversely impact rather than improve our results.\n\nWe believe our gasoline business enhances traffic in our warehouses; it generally has a lower gross margin percentage
and lower SG&A expense relative to our non-gasoline businesses. A higher penetration of gasoline sales will generally lower our gross margin percentage. Generally, rising gasoline prices benefit net sales growth which, given the higher sales base, negatively impacts our gross margin percentage but
decreases our SG&A expenses as a percentage of net sales. A decline in gasoline prices has the inverse effect.\n\nWe also achieve net sales growth by opening new warehouses. As our warehouse base grows and available and desirable sites become more difficult to secure, square footage growth becomes a
comparatively less substantial component of growth. Negative aspects of such growth include lower initial operating profitability relative to existing warehouses and cannibalization of sales at existing warehouses when openings occur in existing markets. Our rate of square footage growth is
generally higher in many of our international markets, due to the smaller base in those markets, and we expect that to continue.",
     "score": 0.527
    },
    {
     "source": "sec://0000909832-26-000093/unknown#46",
     "title": "COST FY2026 10-K",
     "content": "The membership format is integral to our business and profitability. This format is designed to reinforce member loyalty and provide continuing fee revenue. The extent to which we achieve growth in our membership base, increase the penetration of Executive memberships, and sustain
high renewal rates materially influences our profitability. Our renewal rate, which excludes affiliates of Business members, is a trailing calculation that captures renewals during the period seven to eighteen months prior to the reporting date. Our paid-membership growth rate may be adversely
impacted when warehouse openings occur in existing markets as compared to new markets. Our worldwide renewal rate is adversely impacted by membership growth in certain international markets and a higher penetration of memberships sold online, including through digital membership promotions, which
renew at a slightly lower rate on average.\n\nOur financial performance depends heavily on controlling costs. While we believe that we have achieved successes in this area, some significant costs are partially outside our control, particularly health care and utility expenses. With respect to the
compensation of our employees, our philosophy is not to seek to minimize their wages and benefits. Rather, we believe that achieving our longer-term objectives of reducing employee turnover, increasing productivity, and enhancing employee satisfaction requires maintaining compensation levels that
are better than the industry average for much of our workforce. This may cause us, for example, to absorb costs that other employers might seek to pass through to their workforces. Because our business operates on very low margins, modest changes in various items in the consolidated statements of
income, particularly merchandise costs and SG&A expenses, can have substantial impacts on net income.\n\nOur operating models are generally the same across our U.S., Canadian, and Other International operating segments (see [Note 11](#iae87f9b9600946fdb18e1436ed6ec90c_142) to the consolidated
financial statements included in Item 8 of this Report). Certain operations in the Other International segment have relatively higher rates of square footage growth, lower wage and benefit costs as a percentage of sales, less or no direct membership warehouse competition, or lack business delivery
or Costco operated e-commerce sites.",
     "score": 0.6491
    },
    {
     "source": "sec://0000909832-26-000093/unknown#51",
     "title": "COST FY2026 10-K",
     "content": "(1)Comparable sales for 2024 were calculated using comparable retail weeks.\n\n\nNet sales increased $27,335 or 10% during 2026. The improvement was primarily attributable to an increase in comparable sales of $22,457 or 8%. Comparable sales were positively impacted by increases of
5% in average ticket and 3% in shopping frequency. The remaining increase in net sales was driven by sales at the 25 net new warehouses opened since the end of 2025.\n\nDigitally-enabled comparable sales increased 21% during 2026, both as reported and excluding the impact of changes in foreign
currencies.\n\nSales increased $17,136 or 8% in core merchandise categories, increasing in all categories. Sales in warehouse ancillary and other businesses increased $10,199, or 20%, led by gasoline and pharmacy.\n\nHigher gasoline prices positively impacted net sales by $3,501, or 130 basis
points, with a 12% increase in the average price per gallon. The volume of gasoline sold increased 7%, positively impacting net sales by $1,913, or 71 basis points.\n\nChanges in foreign currencies relative to the U.S. dollar positively impacted net sales by $1,332, or 49 basis points, attributable
to our Other International and Canadian operations.\n\nMembership Fees\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n|
Membership fees | | | $ | 5,907 | |  | | | $ | 5,323 | |  | | | $ | 4,828 | |\n\nMembership fee revenue increased 11% in 2026, driven by new member sign-ups, membership fee increases, and upgrades to Executive memberships. At the end of 2026, member renewal rates were 92.3% in the U.S. and Canada
and 89.8% worldwide.\n\n26\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)",
     "score": 0.5189
    },
    {
     "source": "sec://0000909832-26-000093/unknown#52",
     "title": "COST FY2026 10-K",
     "content": "26\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nAs previously reported, we increased annual membership fees in the U.S. and Canada, effective September 1, 2024. We account for membership fee revenue on a deferred basis, recognized ratably over the one-year
membership period. The fee income increase accounted for approximately 30% and 40% of membership income growth during 2026 and 2025.\n\nGross Margin\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net sales | | | $ | 297,247 | |  | | | $ | 269,912 | |  | | | $ | 249,625 | |\n| Less merchandise costs | | | 264,279 | | |  | | | 239,886 | | |  | | | 222,358 | | |\n| Gross margin | | | $ | 32,968 | |  | | | $ | 30,026 |
|  | | | $ | 27,267 | |\n| Gross margin percentage | | | 11.09 | | % |  | | | 11.12 | | % |  | | | 10.92 | | % |",
     "score": 0.6166
    },
    {
     "source": "sec://0000909832-26-000093/unknown#71",
     "title": "COST FY2026 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 52 Weeks Ended | | | | | | | | | | | | | | |\n|  | | | August 30,   2026 | | |  | | | August 31,   2025 |
| |  | | | September 1,   2024 | | |\n| REVENUE | | |  | | |  | | |  | | |  | | |  | | |\n| Net sales | | | $ | 297,247 |  |  | | | $ | 269,912 |  |  | | | $ | 249,625 |  |\n| Membership fees | | | 5,907 | |  |  | | | 5,323 | |  |  | | | 4,828 | |  |\n| Total revenue | | | 303,154 | |  |  | | |
275,235 | |  |  | | | 254,453 | |  |\n| OPERATING EXPENSES | | |  | | |  | | |  | | |  | | |  | | |\n| Merchandise costs | | | 264,279 | |  |  | | | 239,886 | |  |  | | | 222,358 | |  |\n| Selling, general and administrative | | | 27,190 | |  |  | | | 24,966 | |  |  | | | 22,810 | |  |\n| Operating
income | | | 11,685 | |  |  | | | 10,383 | |  |  | | | 9,285 | |  |\n| OTHER INCOME (EXPENSE) | | |  | | |  | | |  | | |  | | |  | | |",
     "score": 0.502
    },
    {
     "source": "sec://0000909832-26-000093/unknown#97",
     "title": "COST FY2026 10-K",
     "content": "47\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nThe Company offers merchandise in the following core merchandise categories: foods and sundries, non-foods, and fresh foods. The Company also provides expanded products and services through warehouse ancillary
and other businesses. The Company is the principal for the majority of its transactions and recognizes revenue on a gross basis. The Company is the principal when it has control of the merchandise or service before it is transferred to the member. The majority of revenue from merchandise sales is
recognized at the point of sale. Revenue generated through e-commerce or special orders is generally recognized upon shipment to the member. For merchandise shipped directly to the member, shipping and handling costs are expensed as incurred as fulfillment costs and included in merchandise costs in
the consolidated statements of income. In certain ancillary businesses, revenue is deferred until the member picks up merchandise at the warehouse. Deferred sales are included in other current liabilities in the consolidated balance sheets.\n\nThe Company accounts for membership fee revenue, net of
refunds, on a deferred basis, ratably over the one-year membership period. Deferred membership fees at the end of 2026 and 2025 were $3,006 and $2,854.\n\nIn most countries, the Company's Executive members qualify for an Executive reward, generally 2% on qualified purchases, subject to an annual
maximum value, which does not expire and is redeemable at Costco warehouses. The Company accounts for this reward as a reduction in sales, net of the estimated impact of non-redemptions (breakage), with the corresponding liability classified as accrued member rewards in the consolidated balance
sheets. Estimated breakage is computed based on redemption data. For 2026, 2025, and 2024, the net reduction in sales was $3,383, $3,007, and $2,804.\n\nThe Company sells and otherwise provides proprietary shop cards that do not expire and are redeemable at the warehouse or online for merchandise or
membership. Revenue from shop cards is recognized upon redemption, and estimated breakage is recognized based on redemption data. The Company accounts for outstanding shop card balances as a liability, net of estimated breakage. Shop card liabilities are included in other current liabilities in the
consolidated balance sheets.",
     "score": 0.5196
    }
   ]
  }
 ]
}
----- END EVIDENCE F0068 -----

----- BEGIN ANSWER F0068 -----
**結論：好市多（Costco）真正的賺錢核心，不是靠商品高毛利，而是「會員費支撐的低價、高周轉零售飛輪」。**  
商品銷售負責創造巨大規模與現金流；會員費則提供相對穩定、類似經常性收入的高價值收入，讓公司能長期維持低商品毛利、低價策略，進而提高會員忠誠度與續費率。

## 1. 會員費不是最大營收，但對獲利極其重要

根據好市多 FY2026 10-K（財政年度截至 2026-08-30）：

- 商品淨銷售額：**2,972.47 億美元**
- 會員費收入：**59.07 億美元**
- 商品毛利：**329.68 億美元**
- 營業利益：**116.85 億美元** [1]

因此：

- 會員費只約占總收入 **1.9%**
- 但會員費約相當於營業利益的 **50.5%**
- 會員費約相當於商品毛利的 **17.9%**

這說明一個關鍵：**會員費不是好市多的主要營收來源，卻是營業利潤中非常重要的一塊。** 如果沒有會員費，好市多要嘛提高商品價格、要嘛接受更低的營業利潤。

不過，不能簡單說「會員費就是一半淨利」。因為好市多的整體人工、物流、門市與管理成本，仍然要靠商品銷售的毛利來覆蓋。比較精確的說法是：**會員費大幅補貼了低價商品模式，並使商品毛利中有更多部分能轉化為營業利益。**

## 2. 商品本身是「規模引擎」，但不是靠高毛利賺錢

好市多 FY2026 商品毛利率只有 **11.09%**。這是非常薄的零售毛利，反映它刻意把價格壓低，以維持會員感受到的「划算」與定價可信度。[2]

它的盈利邏輯大致是：

1. 商品價格低，吸引會員頻繁購物；
2. 會員購買金額與購買頻率上升；
3. 銷售規模變大，固定成本被攤薄；
4. 會員持續續費，產生穩定會員費；
5. 會員費又讓公司更有空間維持低價。

好市多自己在 10-K 中表示，盈利能力最重要的驅動因素是增加淨銷售額，尤其是同店銷售；更高的同店銷售可以攤薄 SG&A 費用、提高獲利能力。[3]

所以，好市多不是典型的「賣一件賺很多」模式，而是：

> **每件商品少賺一點，但讓會員買得更多、更頻繁，再用會員費提高整體經濟效益。**

## 3. 會員費的重要性，還不只在這 59 億美元

會員費的價值包括三層：

### 第一層：直接收入

FY2026 會員費收入為 **59.07 億美元**，較 FY2025 的 **53.23 億美元**增加約 **11%**。增加來源包括新會員、會員費調漲，以及普通會員升級為 Executive 會員。[1]

這種收入的好處是：相較於每筆商品交易，會員費不需要重新採購、運輸和陳列商品，因此通常具有較高的增量經濟價值。

### 第二層：提高會員留存與消費

FY2026 末：

- 全球續費率：**89.8%**
- 美國與加拿大續費率：**92.3%**
- 付費會員：**8,410 萬**
- Executive 會員：**4,230 萬**
- Executive 會員貢獻約 **75.2% 的全球淨銷售額** [4]

換句話說，Executive 會員約占付費會員一半，卻貢獻約四分之三的銷售額。這表示會員制度不只是收年費，也是把客戶轉化為高頻、高消費客戶的機制。

### 第三層：改變公司與顧客的關係

一般零售商主要靠商品交易賺錢；好市多則先收會員費，讓顧客成為「付費會員」。顧客既然已經付了年費，就更有動機把購物集中到好市多，藉此把年費「買回來」。

因此會員費創造了一種心理與經濟上的黏著力：

- 會員希望多消費以攤平年費；
- 好市多希望維持低價，讓會員覺得續費值得；
- 會員越常購物，公司越能透過規模與周轉獲利。

## 4. 真正的核心是「會員費＋商品周轉」的飛輪

如果只看會員費，會低估好市多；如果只看商品銷售，也會誤解它。

比較完整的獲利公式是：

> **會員費提供獲利底盤；低價商品帶來流量；高銷售額攤薄成本；高續費率維持現金流；Executive 會員提高客單價。**

好市多在 10-K 中也明確表示，會員制是其業務與盈利能力不可或缺的一部分；會員數增長、Executive 會員滲透率與高續費率，會重大影響公司的獲利能力。[5]

## 5. Kirkland 與附屬業務是額外的利潤強化器

Kirkland Signature 私有品牌通常比全國性品牌有較高毛利，同時又能提供有競爭力的價格。這使好市多可以在不破壞低價形象的情況下改善毛利結構。[6]

汽油、藥房、美食廣場、眼鏡、輪胎等附屬業務則主要具有兩個作用：

- 增加會員到店頻率；
- 提高會員在好市多體系內的總消費。

其中汽油業務毛利率通常較低，但好市多表示汽油可以為倉庫帶來客流。[7] 因此，這些業務未必各自都是高利潤中心，卻能強化整個會員生態系。

## 最後的判斷

**會員費的重要性：非常高，但不能單獨理解。**

- 以收入看：會員費很小，約占總收入 2%；
- 以營業利益看：會員費約等於營業利益的一半；
- 以商業模式看：會員費是低價策略、會員忠誠度與高周轉模式的核心支柱；
- 以長期投資角度看：真正應觀察的是**會員數、續費率、Executive 滲透率、同店銷售與會員消費頻率**，而不只是會員費本身。

簡單說：

> **好市多不是靠會員費單獨賺錢，而是靠會員費讓它可以用低價賣大量商品；商品規模再反過來提高會員制度的價值。這個飛輪，才是好市多真正的賺錢核心。**

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt
----- END ANSWER F0068 -----

===== ITEM F0069 =====

QUESTION:
Google 現在碰到的反壟斷風險，到底哪些已經在發生，哪些還只是潛在壓力？

----- BEGIN EVIDENCE F0069 -----
[tool 0] sec_filing_search {"query": "current antitrust litigation investigations remedies and potential competition law risks affecting Google Alphabet", "ticker": "GOOGL", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "GOOGL",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from GOOGL FY2025 10-K, Item 1A (Risk Factors) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001652044-26-000018/1a#40",
     "title": "GOOGL FY2025 10-K · Item 1A · Risks Related to Laws, Regulations, and Policies",
     "content": "### Risks Related to Laws, Regulations, and Policies\n\nWe are subject to a variety of new, existing, and changing laws and regulations worldwide that could harm our business, and will likely be subject to an even broader scope of laws and regulations as we continue to expand our
business.\n\nWe are subject to numerous US federal and state as well as foreign laws and regulations covering a wide variety of subjects, and our introduction of new businesses, products, services, and technologies will likely continue to subject us to additional laws and regulations. In recent
years, governments around the world have proposed and adopted a large number of new laws and regulations relevant to the digital economy, particularly in the areas of data privacy and security, competition, AI, and online content. The costs of compliance with these measures are high and are likely
to increase in the future, including as a result of differing, and sometimes conflicting, laws and regulations.\n\nNew or changing laws and regulations, or interpretations or applications of existing laws and regulations in a manner inconsistent with our interpretations of such laws and regulations
or our practices, have resulted in, and may continue to result in, less useful products and services, altered business models and operations, limited ability to pursue certain business practices or offer certain products and services, substantial costs, and civil or criminal liability. Examples
include laws and regulations regarding:\n\n•Competition and technology platforms' business practices: Laws and regulations focused on large technology platforms, including the Digital Markets Act in the European Union (EU) and the Act on Promotion of Competition for Specified Smartphone Software in
Japan; regulations and legal settlements in the US, South Korea, and elsewhere that affect Google Play's billing policies, fees, and business model; as well as litigation and new and expected regulations in a range of jurisdictions.",
     "score": 0.6394,
     "subsection": "Risks Related to Laws, Regulations, and Policies"
    },
    {
     "source": "sec://0001652044-26-000018/1a#44",
     "title": "GOOGL FY2025 10-K · Item 1A",
     "content": "We are subject to claims, lawsuits, regulatory and government inquiries and investigations, other proceedings, and orders involving competition, intellectual property, data privacy and security, tax and related compliance, labor and employment, commercial disputes, content generated
by our users, goods and services offered by advertisers or publishers using our platforms, design of our products and services, personal injury and other tort and nuisance theories, consumer protection claims, including how we moderate content on our platforms, AI, and other matters.\n\nThe US
Department of Justice (DOJ), various states, and other plaintiffs have filed, and may continue to file in the future, several antitrust lawsuits about aspects of our business, including our advertising technologies and practices, the operation and distribution of Google Search, and the operation and
distribution of Android operating system and Play Store. If we are unsuccessful in these lawsuits, we could face significant expenses to implement the remedies, and such costs and alterations could harm our business, reputation, financial condition, and operating results.\n\n18.\n\n\n|  |  |  |  |
|  |\n| --- | --- | --- | --- | --- | --- |\n| [Table of Contents](#i6be430fe3ebf411481dcec8b0abe9149_7) | | | Alphabet Inc. | | |\n\nFor example, the DOJ and a number of state Attorneys General filed a lawsuit concerning our Search and Search advertising practices and our compliance with US
antitrust laws. In August 2024, the US District Court for the District of Columbia ruled against Google, and in December 2025, entered a final judgment requiring remedies, which, among other things, imposes restrictions on how we distribute our services and requires us to share certain search data
with and offer syndication services to certain competitors. In January 2026, we appealed the final judgment and moved to pause implementation of certain remedies. In February 2026, the DOJ and state Attorneys General also appealed.",
     "score": 0.671
    },
    {
     "source": "sec://0001652044-26-000018/1a#45",
     "title": "GOOGL FY2025 10-K · Item 1A",
     "content": "Furthermore, in December 2020, a number of state Attorneys General, led by the Texas Attorney General, filed a lawsuit in the US District Court for the Eastern District of Texas concerning our advertising technology and our compliance with US antitrust laws and other laws. In
January 2023, the DOJ and a number of state Attorneys General sued in the Eastern District of Virginia alleging similar antitrust violations relating to our advertising technology. In April 2025, the presiding judge issued a mixed decision in the DOJ case against us, ruling that neither our
advertiser tools nor the DoubleClick and AdMeld acquisitions were anticompetitive, but that our publisher tools unfairly excluded rivals. A separate proceeding to determine remedies, the range of which varies widely, took place in September 2025 with the parties presenting differing remedy
proposals. The DOJ's remedy proposal includes structural remedies that could harm our business. Closing arguments were held in November 2025, and we are awaiting a final judgment. After that judgment, we plan to appeal the adverse portion of the April 2025 decision and potentially aspects of the
remedies decision. A trial in the state Attorneys General case in the Eastern District of Texas will take place after a decision on remedies is issued in the DOJ advertising technology case, and could result in remedies that could harm our business, reputation, financial condition, and operating
results.\n\nIn addition to these regulatory proceedings, private individual and collective actions that overlap with claims pursued by regulators are pending in the US and in several other jurisdictions. Adverse results in these or similar future lawsuits may include awards of monetary damages and
remedies that could harm our business, reputation, financial condition, and operating results.\n\nOther regulatory agencies in the US and around the world, including competition enforcers, consumer protection agencies, and data protection authorities, have challenged and may continue to challenge
our business practices and compliance with laws and regulations. We are cooperating with these investigations and defending litigation or appealing decisions where appropriate.",
     "score": 0.6783
    },
    {
     "source": "sec://0001652044-26-000018/1a#49",
     "title": "GOOGL FY2025 10-K · Item 1A",
     "content": "We, like other internet, technology, and media companies, are frequently subject to litigation based on allegations of infringement or other violations of intellectual property rights, including patent, copyright, trade secrets, and trademarks. Parties have also sought broad
injunctive relief against us by filing claims in US and international courts and the US International Trade Commission (ITC) for exclusion and cease-and-desist orders. In addition, patent-holding companies may frequently seek to generate income from patents they have obtained by bringing claims
against us. As we continue to expand our business, intellectual property claims against us have increased and may continue to increase as we develop and acquire new products, services, and technologies, including AI technologies.\n\nAdverse results in any of these lawsuits may include awards of
monetary damages, costly royalty or licensing agreements (if licenses are available at all), or orders limiting our ability to sell our products and services in the US or elsewhere, including by preventing us from offering certain features, functionalities, products, or services in certain
jurisdictions. They may also cause us to change our business practices in ways that could result in a loss of revenues for us and otherwise harm our business.\n\nMany of our agreements with our customers and partners, including certain suppliers, require us to defend against certain intellectual
property infringement claims and in some cases indemnify them for certain intellectual property infringement claims against them, which could result in increased costs for defending such claims or significant damages if there were an adverse ruling in any such claims. Such customers and partners may
also discontinue the use of our products, services, and technologies, as a result of injunctions or otherwise, which could\n\n20.\n\n\n|  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- |\n| [Table of Contents](#i6be430fe3ebf411481dcec8b0abe9149_7) | | | Alphabet Inc. | | |",
     "score": 0.6025
    }
   ]
  },
  {
   "ticker": "GOOGL",
   "fiscal_year": 2025,
   "item": "Item 8",
   "prelude": "Excerpts from GOOGL FY2025 10-K, Item 8 (Financial Statements and Supplementary Data) — 5 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001652044-26-000018/8#300",
     "title": "GOOGL FY2025 10-K · Item 8 · Antitrust Matters",
     "content": "### Antitrust Matters\n\nWe are subject to formal and informal inquiries and investigations as well as litigation on various competition matters by regulatory authorities and private parties in the US, Europe, and other jurisdictions globally, including the following:
\n\n•Shopping: In June 2017, the EC announced its decision that certain actions taken by Google relating to its display and ranking of shopping search results and ads infringed European antitrust laws and imposed a €2.4 billion fine. In 2024, we made a cash payment of $3.0 billion for the
fine.\n\n•Android: In July 2018, the EC announced its decision that certain provisions in Google's Android-related distribution agreements infringed European antitrust laws, imposed a €4.3 billion fine, and directed the termination of the conduct at issue. We appealed the EC decision and implemented
changes to certain of our Android distribution practices. In September 2022, the General Court affirmed the EC decision but reduced the fine from €4.3 billion to €4.1 billion. We subsequently appealed the General Court's affirmation of the EC decision with the European Court of Justice, which
remains pending. In 2018, we recognized a charge of $5.1 billion for the fine, which we reduced by $217 million in 2022.\n\n•AdSense for Search: In March 2019, the EC announced its decision that certain provisions in Google's agreements with AdSense for Search partners infringed European antitrust
laws, imposed a €1.5 billion fine, and directed actions related to AdSense for Search partners' agreements, which we implemented prior to the decision. In 2019, we recognized a charge of $1.7 billion for the fine and appealed the EC decision. In September 2024, the General Court overturned the EC
decision and annulled the €1.5 billion fine. The EC has appealed the General Court's decision with the European Court of Justice.",
     "score": 0.6541,
     "subsection": "Antitrust Matters"
    },
    {
     "source": "sec://0001652044-26-000018/8#301",
     "title": "GOOGL FY2025 10-K · Item 8",
     "content": "•Search: In October 2020, the DOJ and a number of state Attorneys General filed a lawsuit in the US District Court for the District of Columbia concerning Google's Search and Search advertising practices and its compliance with US antitrust laws. In August 2024, the US District
Court for the District of Columbia ruled against Google. A final judgment was entered in December 2025, which, among other things, imposes restrictions on how Google distributes its services and requires Google to share certain search data with and offer syndication services to certain competitors.
In January 2026, we appealed the final judgment and moved to pause implementation of certain remedies. In February 2026, the DOJ and state Attorneys General also appealed.\n\nFurther, in June 2022, the Australian Competition and Consumer Commission (ACCC) opened an investigation into Search
distribution practices. In August 2025, we agreed to a settlement with the ACCC requiring, among other things, changes to our Android agreements. We recognized a charge in the second quarter of 2025, and the settlement was approved by the court in December 2025.\n\nIn October 2023, the Japanese Fair
Trade Commission (JFTC) opened an investigation into Search distribution practices. In April 2025, the JFTC issued a cease-and-desist order requiring us to make changes to our Android agreements to ensure they are consistent with Japanese antitrust law. The JFTC did not impose monetary penalties.",
     "score": 0.6337
    },
    {
     "source": "sec://0001652044-26-000018/8#302",
     "title": "GOOGL FY2025 10-K · Item 8",
     "content": "•Advertising Technology: In December 2020, a number of state Attorneys General filed a lawsuit in the US District Court for the Eastern District of Texas concerning Google's advertising technology and its compliance with US antitrust laws and state deceptive trade laws. In January
2023, the DOJ, along with a number of state Attorneys General, filed a lawsuit in the US District Court for the Eastern District of Virginia concerning Google's advertising technology and its compliance with US antitrust laws, and a number of additional state Attorneys General subsequently joined
the lawsuit. In April 2025, the US District Court for the Eastern District of Virginia issued a mixed decision in the DOJ case against Google, ruling that neither Google's advertiser tools nor the DoubleClick and AdMeld acquisitions were anticompetitive, but that Google's publisher tools unfairly
excluded rivals. A separate proceeding to determine remedies, the range of which vary widely, took place in September 2025, with the parties presenting differing remedy proposals. The DOJ's remedy proposal includes structural remedies that could have a material adverse effect on our business.
Closing arguments were held in November 2025, and we are awaiting a final judgment. After that judgment, we plan to appeal the adverse portion of the April 2025 decision and potentially aspects of the remedies decision. A trial in the state Attorneys General case in the Eastern District of Texas
will take place after a decision on remedies is issued in the DOJ case. Given the nature of these matters, we cannot estimate a possible loss.\n\nFurther, in September 2025, the EC announced its decision that Google had infringed European competition laws through \"self-preferencing\" practices on
the buy-side and the sell-side relating to Google's advertising technology business. The EC decision imposed a €3.0 billion fine and directed Google to cease and desist the alleged \"self-preferencing\" practices. We appealed the ruling in November 2025. We recognized a charge of\n\n76.\n\n\n|  |  |
|  |  |  |\n| --- | --- | --- | --- | --- | --- |\n| [Table of Contents](#i6be430fe3ebf411481dcec8b0abe9149_7) | | | Alphabet Inc. | | |\n\n$3.5 billion in the third quarter of 2025, and we placed bank guarantees in the fourth quarter of 2025 in lieu of cash payment.",
     "score": 0.6663
    },
    {
     "source": "sec://0001652044-26-000018/8#303",
     "title": "GOOGL FY2025 10-K · Item 8",
     "content": "$3.5 billion in the third quarter of 2025, and we placed bank guarantees in the fourth quarter of 2025 in lieu of cash payment.\n\nIn September 2024, the UK also issued a Statement of Objections concerning Google's advertising technology and its compliance with UK antitrust laws, to
which we responded.\n\n•Google Play: In July 2021, a number of state Attorneys General filed a lawsuit in the US District Court for the Northern District of California concerning Google’s operation of Android and Google Play and its compliance with US antitrust laws and state antitrust and consumer
protection laws. In September 2023, we reached a settlement in principle with 50 state Attorneys General and three territories and recognized a charge. The court preliminarily approved the settlement in November 2025, and final approval remains pending before the court. In May 2024, we funded the
settlement amount to an escrow agent.\n\nIn December 2023, a California jury delivered a verdict against Google in Epic Games v. Google related to Google Play's business. Epic did not seek monetary damages. The presiding judge issued a remedies decision in October 2024, ordering a variety of
alterations to our business models and operations and contractual agreements for Android and Google Play. We appealed the judgment, including the jury verdict and aspects of the remedies ordered, and in July 2025, the Court of Appeals denied our appeal. We are in the process of appealing that
decision to the US Supreme Court, and we implemented the ordered remedies in October 2025 while the appeal is pending. In October 2025, we reached a settlement with Epic to modify the remedies in this case and resolve certain other lawsuits Epic has filed regarding Google Play's business. The
settlement is contingent on the court approving a proposed modified injunction. Epic and Google filed a joint motion to modify the injunction in November 2025, which is currently pending before the court.\n\n•European Digital Markets Act: In March 2024, the EC opened two investigations regarding
Google's compliance with certain provisions of the EU's Digital Markets Act relating to Google Play and Search. In March 2025, the EC issued preliminary findings of non-compliance in both investigations, to which we responded. Given the nature of this matter, we cannot estimate a possible loss.",
     "score": 0.6247
    },
    {
     "source": "sec://0001652044-26-000018/8#306",
     "title": "GOOGL FY2025 10-K · Item 8 · Patent and Intellectual Property Claims",
     "content": "### Patent and Intellectual Property Claims\n\nWe have had patent, copyright, trade secret, and trademark infringement lawsuits filed against us claiming that certain of our products, services, and technologies infringe others' intellectual property rights. Adverse results in these
lawsuits may include awards of substantial monetary damages, costly royalty or licensing agreements, or orders preventing us from offering certain features, functionalities, products, or services. As a result, we may have to change our business practices and develop non-infringing products or
technologies, which could result in a loss of revenues for us and otherwise harm our business. In addition, the ITC has increasingly become an important forum to litigate intellectual property disputes because an ultimate loss in an ITC action can result in a prohibition on importing infringing
products into the US. Because the US is an important market, a prohibition on importation could have an adverse effect on us, including preventing us from importing many important products into the US or necessitating workarounds that may limit certain features of our products. Further, our
customers and partners may discontinue the use of our products, services, and technologies, as a result of injunctions or otherwise, which could result in loss of revenues and adversely affect our business.\n\nOther\n\nWe are subject to claims, lawsuits, regulatory and government inquiries and
investigations, other proceedings, and consent orders involving competition, intellectual property, data privacy and security, tax and related compliance, labor and employment, commercial disputes, content generated by our users, goods and services offered by advertisers or publishers using our
platforms, design of our products and services, personal injury and other tort and nuisance theories, consumer protection, including how we moderate content on our platforms, AI, and other matters.\n\n77.\n\n\n|  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- |\n| [Table of
Contents](#i6be430fe3ebf411481dcec8b0abe9149_7) | | | Alphabet Inc. | | |\n\nFor example, we periodically have data incidents that we report to relevant regulators as required by law. Such claims, consent orders, lawsuits, regulatory and government investigations, and other proceedings could result
in substantial fines and penalties, injunctive relief, ongoing monitoring and auditing obligations, changes to our products and services, alterations to our business models and operations, and collateral related civil litigation or other adverse consequences, all of which could harm our business,
reputation, financial condition, and operating results.",
     "score": 0.597,
     "subsection": "Patent and Intellectual Property Claims"
    }
   ]
  },
  {
   "ticker": "GOOGL",
   "fiscal_year": 2025,
   "item": "Item 1",
   "prelude": "Excerpts from GOOGL FY2025 10-K, Item 1 (Business) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001652044-26-000018/1#13",
     "title": "GOOGL FY2025 10-K · Item 1 · Competition",
     "content": "### Competition\n\nOur business is characterized by rapid change as well as new and disruptive technologies. We face formidable competition in every aspect of our business, including but not limited to, from:\n\n•general purpose search engines and information services;\n\n•vertical
search engines and e-commerce providers for queries on topics such as those related to travel, jobs, and health, which users may navigate directly to rather than go through Google;\n\n•online advertising platforms and networks, including online shopping and streaming services;\n\n•other forms of
advertising, such as billboards, magazines, newspapers, radio, and television, as our advertisers typically advertise in multiple media, both online and offline;\n\n•digital content and application platform providers;\n\n•providers of enterprise cloud services;\n\n•AI model developers and providers
of AI products and services;\n\n•companies that design, manufacture, and market consumer hardware products, including businesses that have developed proprietary platforms;\n\n•providers of digital video services;\n\n•social networks, which users may rely on for product or service referrals, rather
than seeking information through traditional search engines; and\n\n•providers of workspace communication and connectivity products.\n\n6.\n\n\n|  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- |\n| [Table of Contents](#i6be430fe3ebf411481dcec8b0abe9149_7) | | | Alphabet Inc. | |
|\n\nCompeting successfully depends heavily on our ability to continually develop and distribute innovative products and technologies to the marketplace across our businesses. For example, for advertising, competing successfully depends on attracting and retaining:\n\n•users, for whom other products
and services are literally one click away, on the basis of the relevance of our advertising, as well as the general usefulness, security, and availability of our products and services;\n\n•advertisers, primarily based on our ability to generate sales leads, and ultimately customers, and to deliver
their advertisements in an efficient and effective manner across a variety of distribution channels even as trends in advertising mediums and user preferences change; and\n\n•content providers, primarily based on the quality of our advertiser base, our ability to help these partners generate
revenues from advertising, and the terms of our agreements with them.\n\nFor additional information about competition, see Item 1A Risk Factors of this Annual Report on Form 10-K.",
     "score": 0.5814,
     "subsection": "Competition"
    }
   ]
  }
 ]
}

[tool 1] finnhub_stock_quote {"ticker": "GOOGL"}
{
 "ticker": "GOOGL",
 "currentPrice": 319.97,
 "open": 317.05,
 "previousClose": 316.8,
 "change": 3.17,
 "percentChange": 1.0006,
 "dayHigh": 320.77,
 "dayLow": 316.86
}

[tool 2] tavily_financial_search {"query": "Alphabet Google latest antitrust lawsuits remedies DOJ ad tech search 2025 2026", "ticker": "GOOGL"}
{
 "query": "GOOGL Alphabet Google latest antitrust lawsuits remedies DOJ ad tech search 2025 2026",
 "results": [
  {
   "title": "Google files to appeal search monopoly case",
   "url": "https://www.cnbc.com/2026/01/16/google-files-to-appeal-search-monopoly-case.html",
   "content": "Last Spring, the company and the DOJ participated in a remedies trial to determine the the consequences Google would implement. The trial included witnesses from Apple and Mozilla, as well as competitors from OpenAI and other companies. In September 2025, Mehta ruled against the most
severe consequences proposed by the Department of Justice, including a forced sale of Google's Chrome browser. The ruling was seen as a win for Google, with its stock jumping 8% following the news. [...] Mehta finalized the remedies in December. Mehta stipulated that Google must share some of its
raw search interaction data that it uses to train its ranking and AI systems, but he spared the company from having to share its actual algorithms. Mehta also wrote that Google cannot enter into any deals like the search agreement the company had with Apple \"unless the agreement terminates no more
than one year after the date it is entered.\" [...] Analysts at the time compared the lighter-than-expected remedies to a slap on the wrist.\n\nGoogle is asking to pause the implementation of the remedies, Mulholland wrote on Friday.\n\n\"These mandates would risk Americans' privacy and discourage
competitors from building their own products,\" Mulholland wrote. \"Ultimately stifling the innovation that keeps the U.S. at the forefront of global technology.\"\n\nWATCH: CNBC's full interview with Google DeepMind CEO Demis Hassabis",
   "published_date": null
  },
  {
   "title": "Google advertising antitrust remedies trial set for Sept. 22, judge says",
   "url": "https://www.cnbc.com/2025/05/02/google-advertising-antitrust-remedies-trial.html",
   "content": "Key Points\n\n The U.S. government's remedies trial in the Google antitrust case regarding its advertising technology is scheduled to begin on Sept. 22.\n Last month, U.S. District Judge Leonie Brinkema in Alexandria, Virginia, said Google was liable for “willfully acquiring and
maintaining monopoly power.”\n\nIn this article\n\n GOOGL\n\nSundar Pichai, chief executive officer of Alphabet Inc., during a visit to the Google for Startups campus in Warsaw, Poland, on Thursday, Feb. 13, 2025. [...] \"Today the DOJ conceded Google's proposed ad tech remedy fully addresses the
Court's decision on liability,\" Lee-Anne Mulholland, Google's vice president of regulatory affairs, said in a statement. \"The DOJ's additional proposals to force a divestiture of our ad tech tools go well beyond the Court's findings, have no basis in law, and would harm publishers and
advertisers.\"\n\nChoose CNBC as your preferred source on Google and never miss a moment from the most trusted name in business news. [...] That followed an August ruling that Google has held a monopoly in its core market of internet search, the most-significant antitrust ruling in the tech industry
since the case against Microsoftmore than 20 years ago. The remedies trial for that case began last month in Washington, D.C.",
   "published_date": null
  },
  {
   "title": "Google defeats U.S. bid to force ad tech sale",
   "url": "https://www.cnbc.com/2026/09/02/google-defeats-us-bid-to-force-ad-tech-sale.html",
   "content": "In April 2025, Brinkema ruled that Google holds illegal monopolies on servers that host publisher ads and ad exchanges which sit between buyers and sellers. Google unlawfully locked publishers on its ad server into using its AdX, the judge found.\n\nThe tech giant's anticompetitive
conduct \"substantially harmed Google's publisher customers, the competitive process, and, ultimately, consumers of information on the open web,\" Brinkema said at the time. [...] Likewise, another judge in Washington, who previously ruled that Google holds an illegal monopoly in online search,
rejected the DOJ's bid to make the company sell its Chrome browser, citing rising competition from generative artificial intelligence companies such as OpenAI's ChatGPT.\n\nU.S. antitrust cases against Amazon and Apple, which involve massive smartphone and online retail markets, will not go to trial
until 2027 at the earliest. [...] In this article\n\nAlphabet's Google escaped a breakup of its advertising technology business on Wednesday, when a judge in Virginia rejected U.S. antitrust enforcers' bid to force a sale of Google's online advertising exchange.\n\nWhile the ad exchange is a small
part of Google's business, the ruling is the second powerful symbolic victory against the U.S. Department of Justice in its efforts to force Google to sell assets to address illegal monopolies.",
   "published_date": null
  },
  {
   "title": "Google stock jumps as judge rules it can keep Chrome in antitrust case",
   "url": "https://www.cnbc.com/2025/09/02/google-antitrust-search-ruling.html",
   "content": "During the remedies trial in May, the DOJ asked the judge to force Google to share the data it uses for generating search results, such as data about what users click on.\n\nMehta ruled Tuesday that Google will have to make available certain search index data and user interaction
data, though \"not ads data.\"\n\nGoogle does not have to share or provide access to granular data with advertisers. [...] \"The court's ruling today recognizes the need for remedies that will pry open the market for general search services, which has been frozen in place for over a decade,\" the
DOJ said in a press release. \"The ruling also recognizes the need to prevent Google from using the same anticompetitive tactics for its GenAI products as it used to monopolize the search market, and the remedies will reach GenAI technologies and companies.\" [...] U.S. District Judge Amit Mehta
ruled against the most severe consequences that were proposed by the Department of Justice, including the forced sale of Google's Chrome browser, which provides data that helps its advertising business deliver targeted ads.",
   "published_date": null
  },
  {
   "title": "Google Partially Loses US Advertising Tech Antitrust Case (GOOGL) - Bloomberg",
   "url": "https://www.bloomberg.com/news/articles/2025-04-17/google-partially-loses-us-advertising-tech-antitrust-case",
   "content": "US District Judge Leonie Brinkema found on Thursday that the Alphabet Inc. unit violated antitrust law in the markets for advertising exchanges and tools used by websites to sell ad space, known as ad servers. But she said the company didn’t meet the definition of a monopoly for a
third market of tools used by advertisers to buy display ads. [...] # Google Illegally Monopolized Ad Tech Markets, Judge Says\n\nThis article is for subscribers only.\n\n## Takeaways by Bloomberg AI\n\nGoogle illegally monopolized some online advertising technology markets, according to a federal
judge, whose ruling marked the latest antitrust setback for the company and a challenge to its main source of revenue.",
   "published_date": null
  }
 ]
}
----- END EVIDENCE F0069 -----

----- BEGIN ANSWER F0069 -----
**結論：Google 的反壟斷風險已經不是單純「可能被調查」；搜尋、廣告科技、Google Play／Android 與歐盟監管等多條戰線都已經進入判決、補救措施、罰款或合規執行階段。** 真正仍屬「潛在壓力」的，主要是補救措施會不會進一步擴大、未決案件的最終處分，以及各國新規對商業模式的長期限制。

## 已經在發生的風險

### 1. 美國搜尋壟斷案：已敗訴，補救措施正在上訴中

美國司法部（DOJ）及多州檢察長針對 Google 搜尋與搜尋廣告提起的案件，Google 在 2024 年 8 月被法院判定敗訴；2025 年 12 月法院作出最終判決，要求 Google 限制部分服務分發方式、分享部分搜尋資料，並向特定競爭者提供搜尋結果 syndication 服務。Google 已於 2026 年 1 月上訴並要求暫停部分補救措施，DOJ 與州政府則於 2026 年 2 月提出上訴。[1]

這代表風險已經從「是否違法」轉為：

- Google 是否必須實際改變與 Apple 等平台的分發協議；
- 搜尋資料分享會不會削弱 Google 的資料與 AI 優勢；
- 上訴法院是否會擴大或縮小補救措施。

Alphabet FY2025 10-K（財政年度截至 2025-12-31）明確表示，這些補救措施可能造成重大執行成本，並傷害業務、聲譽、財務狀況與經營成果。[2]

### 2. 廣告科技案：部分責任已成立，結構性處分仍未完全落地

在美國 DOJ 的廣告科技案件中，法院於 2025 年 4 月認定 Google 的 publisher tools 不當排除競爭者；但法院同時認定 Google 的 advertiser tools，以及 DoubleClick 和 AdMeld 收購，並未構成反競爭行為。[3]

因此，已發生的部分是：

- Google 已被判定在部分廣告科技市場違法；
- 2025 年 9 月已進行補救措施審理；
- DOJ 提出的方案包含可能影響業務結構的措施；
- Google 預期會上訴不利部分。

但**最終補救判決仍是關鍵未決事項**。Alphabet 表示，德州州檢察長另案的審判也要等 DOJ 案的補救判決後進行，而且公司目前無法估計可能損失。[4]

歐洲方面，歐盟執委會在 2025 年 9 月認定 Google 在廣告科技業務中存在「自我偏好」行為，處以 30 億歐元罰款並要求停止相關行為；Google 已提出上訴，並以銀行保函取代立即現金支付。[5]

### 3. Google Play／Android：商業模式已被迫調整

Epic Games v. Google 案中，美國法院要求 Google 改變 Android 與 Google Play 的商業模式、營運方式及合約安排。Google 的上訴在 2025 年 7 月被駁回；公司已於 2025 年 10 月執行相關補救措施，目前正尋求美國最高法院審理。Google 之後與 Epic 達成和解，但修改禁制令仍待法院批准。[6]

此外，Google 與 50 個州及 3 個地區就 Google Play 案達成的和解，法院已初步批准，但最終批准仍待完成。[6]

這些不是抽象風險，而是已經可能影響：

- Google Play 的抽成與計費政策；
- 開發者使用第三方支付或其他分發渠道的自由度；
- Android 生態系的合約與分發安排。

### 4. 歐盟與其他國家的 Android／搜尋分發監管已經落地

Google 在歐盟 Android 案的罰款，經上訴後由 43 億歐元降至 41 億歐元，案件仍在歐洲法院審理中。[7]

澳洲競爭與消費者委員會的搜尋分發調查則已於 2025 年達成和解，要求 Google 修改 Android 協議；日本公平交易委員會也在 2025 年發布停止及改正命令，要求 Google 修改 Android 協議，且未處以金錢罰款。[8]

這表示 Google 面對的不是單一美國案件，而是各國逐步要求它降低預設地位、改變分發協議與平台規則。

## 仍屬潛在壓力、但不能忽略的部分

### 1. 美國廣告科技案的最終結構性補救

目前最具不確定性的，是 DOJ 是否能取得比行為限制更嚴格的結構性處分，例如要求出售或拆分部分廣告科技資產。Google 10-K 只確認 DOJ 提案包含可能重大傷害業務的結構性補救，但截至該申報時，最終判決仍未出爐。[4]

因此，**「Google 一定會被迫出售廣告科技業務」目前不能視為已發生事實**；比較準確的說法是，這是仍在審理中的高影響情境。

### 2. 搜尋補救措施是否會擴大，以及對 AI 搜尋的外溢影響

目前法院已要求分享部分搜尋資料並限制部分分發安排，但 Google 與政府雙方都在上訴。[1] 新聞報導指出，法院沒有採納最嚴厲的 Chrome 強制出售方案，但要求提供部分搜尋索引與使用者互動資料，且補救措施也涉及防止 Google 將類似策略延伸到生成式 AI。[9]

所以潛在壓力包括：

- 搜尋資料分享範圍可能在上訴中改變；
- Google 的預設搜尋交易可能受到更嚴格限制；
- 監管機構可能把傳統搜尋案件的原則延伸到 AI 搜尋與 Gemini 等產品。

### 3. 歐盟《數位市場法》可能帶來持續性合規成本

歐盟在 2024 年針對 Google Play 與搜尋是否符合《數位市場法》（DMA）展開調查，並於 2025 年提出兩項初步不合規結論；Alphabet 表示已回應，但該事項的可能損失仍無法估計。[10]

這類風險未必立即表現為一次性巨額罰款，更可能是持續要求 Google：

- 改變搜尋結果呈現與自家服務排序；
- 調整 Play 商店規則；
- 提供更多互通性或選擇權；
- 承擔長期監控、報告與產品修改成本。

Alphabet 自己也表示，全球競爭法、平台監管與數位市場規則正在增加，合規成本可能持續上升，並可能限制商業做法或改變產品與營運模式。[11]

## 簡單分級

| 風險 | 狀態 | 對 Google 的主要影響 |
|---|---|---|
| 美國搜尋案 | **已發生，補救措施與上訴中** | 分發協議、資料分享、搜尋與 AI 戰略 |
| 美國廣告科技案 | **部分敗訴，補救判決未完全確定** | publisher tools、可能的結構性處分 |
| 歐盟廣告科技案 | **已裁罰、已上訴** | 30 億歐元罰款與業務行為限制 |
| Google Play／Epic | **補救措施已執行，後續上訴／修改中** | 抽成、支付、第三方分發 |
| Android 澳洲／日本 | **已和解或已下令改正** | Android 預設與分發協議 |
| 歐盟 DMA | **調查及初步不合規已發生** | 持續合規、產品改造與潛在罰款 |
| 強制出售 Chrome 或廣告科技資產 | **目前仍屬潛在情境** | 高影響，但不能當成已確定結果 |

**投資上最重要的判斷是：Google 面對的核心風險不是單一罰款，而是「分發優勢、資料優勢與平台抽成模式」可能被逐步削弱。** 目前最確定的是搜尋與 Play 已有實質補救要求；最大的不確定性則在廣告科技案的最終補救，以及搜尋案上訴後是否出現更嚴格限制。根據 Finnhub 即時報價，GOOGL 目前為 319.97 美元，較前收盤上升 1.00%；這只是即時市場價格，不能單獨解讀為市場已完全消化上述法律風險。

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt  
[8]: SEC 10-K excerpt  
[9]: https://www.cnbc.com/2025/09/02/google-antitrust-search-ruling.html "Google stock jumps as judge rules it can keep Chrome in antitrust case"  
[10]: SEC 10-K excerpt  
[11]: SEC 10-K excerpt
----- END ANSWER F0069 -----

===== ITEM F0070 =====

QUESTION:
好市多會員費是不是快要調了？管理層有真的把時間點講明嗎？

----- BEGIN EVIDENCE F0070 -----
[tool 0] sec_filing_search {"query": "membership fee increase timing management statements next increase renewal fee", "ticker": "COST", "fiscal_year": null}
{
 "fiscal_year": 2026,
 "fiscal_year_end": "2026-08-30",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "COST",
   "fiscal_year": 2026,
   "item": "_unknown",
   "prelude": "Excerpts from COST FY2026 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000909832-26-000093/unknown#3",
     "title": "COST FY2026 10-K",
     "content": "Certain financial information for our segments and geographic areas is included in [Note 11](#iae87f9b9600946fdb18e1436ed6ec90c_142) to the consolidated financial statements included in Item 8 of this Report.\n\nMembership\n\nOur members may utilize their memberships at all of our
warehouses and e-commerce sites. Our annual fee for memberships is $65 in the U.S., varies in other countries and includes a free household card.\n\nMembership at the end of 2026, 2025, and 2024 was made up of the following (in thousands):\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Paid members1 | | | 84,100 | |  |  | | | 81,000 | |  |  | | | 76,200 | |  |\n| Household cards | | | 66,300 | |  |  | | |
64,200 | |  |  | | | 60,600 | |  |\n| Total cardholders | | | 150,400 | |  |  | | | 145,200 | |  |  | | | 136,800 | |  |\n\n_______________\n\n(1)These membership counts include active memberships as well as memberships that have expired and not renewed within the 12 months prior to the reporting
date. These expired memberships make up a small percentage of membership counts, and many of them are subsequently renewed.\n\nPaid members, in most countries, are eligible to upgrade to an Executive membership for an additional annual fee. These members earn an Executive reward, generally 2% on
qualified purchases, subject to an annual maximum value, redeemable at Costco warehouses. Executive members represented 42,300, 38,700, and 35,400 of total paid members in 2026, 2025, and 2024. The penetration of sales to Executive members represented approximately 75.2% of worldwide net sales in
2026.",
     "score": 0.3766
    },
    {
     "source": "sec://0000909832-26-000093/unknown#4",
     "title": "COST FY2026 10-K",
     "content": "Our member renewal rate was 92.3% in the U.S. and Canada and 89.8% worldwide at the end of 2026. This rate is a trailing calculation that captures renewals during the period seven to eighteen months prior to the reporting date. Memberships that have an expiration date in the six
months prior to the end of our reporting period are excluded from this calculation, regardless of whether or not they have been renewed. Although most members renew prior to expiration, the vast majority of those who renew late do so within six months of expiration. The timing of renewal after
expiration is impacted by a variety of factors, such as warehouse openings and promotional activity.\n\n5\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nHuman Capital\n\n“Take Care of Our Employees,” is a key component of our code of ethics and is fundamental to our commitment
to “Take Care of Our Members.” Compensation and benefits for employees is our largest expense after the cost of merchandise and is carefully monitored.\n\nEmployee Base\n\nAt the end of 2026, we employed 355,000 employees worldwide. Approximately 95% are employed in our membership warehouses and
distribution channels. Around 5% are represented by unions. We also utilize seasonal employees.\n\nThe total number of employees by segment was:",
     "score": 0.3431
    },
    {
     "source": "sec://0000909832-26-000093/unknown#46",
     "title": "COST FY2026 10-K",
     "content": "The membership format is integral to our business and profitability. This format is designed to reinforce member loyalty and provide continuing fee revenue. The extent to which we achieve growth in our membership base, increase the penetration of Executive memberships, and sustain
high renewal rates materially influences our profitability. Our renewal rate, which excludes affiliates of Business members, is a trailing calculation that captures renewals during the period seven to eighteen months prior to the reporting date. Our paid-membership growth rate may be adversely
impacted when warehouse openings occur in existing markets as compared to new markets. Our worldwide renewal rate is adversely impacted by membership growth in certain international markets and a higher penetration of memberships sold online, including through digital membership promotions, which
renew at a slightly lower rate on average.\n\nOur financial performance depends heavily on controlling costs. While we believe that we have achieved successes in this area, some significant costs are partially outside our control, particularly health care and utility expenses. With respect to the
compensation of our employees, our philosophy is not to seek to minimize their wages and benefits. Rather, we believe that achieving our longer-term objectives of reducing employee turnover, increasing productivity, and enhancing employee satisfaction requires maintaining compensation levels that
are better than the industry average for much of our workforce. This may cause us, for example, to absorb costs that other employers might seek to pass through to their workforces. Because our business operates on very low margins, modest changes in various items in the consolidated statements of
income, particularly merchandise costs and SG&A expenses, can have substantial impacts on net income.\n\nOur operating models are generally the same across our U.S., Canadian, and Other International operating segments (see [Note 11](#iae87f9b9600946fdb18e1436ed6ec90c_142) to the consolidated
financial statements included in Item 8 of this Report). Certain operations in the Other International segment have relatively higher rates of square footage growth, lower wage and benefit costs as a percentage of sales, less or no direct membership warehouse competition, or lack business delivery
or Costco operated e-commerce sites.",
     "score": 0.43
    },
    {
     "source": "sec://0000909832-26-000093/unknown#47",
     "title": "COST FY2026 10-K",
     "content": "In discussions of our consolidated operating results, we refer to the impact of changes in foreign currencies relative to the U.S. dollar, which are differences between the foreign-exchange rates we use to convert the financial results of our international operations from local
currencies into U.S. dollars. This impact is calculated based on the difference between the current and prior period's exchange rates. The impact of changes in gasoline prices on net sales is calculated based on the difference between the current and prior period's average price per gallon. Results
expressed excluding the impacts of foreign-\n\n24\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nexchange and gasoline prices are intended as supplemental information and are not a substitute for net sales presented in accordance with U.S. GAAP and should be reviewed in
conjunction with results reported in accordance with U.S. GAAP.\n\nOur fiscal year ends on the Sunday closest to August 31. References to 2026, 2025, and 2024 relate to the 52-week fiscal years ended August 30, 2026, August 31, 2025, and September 1, 2024. Certain percentages presented are
calculated using actual results prior to rounding.\n\nHighlights for 2026 include:\n\n•We opened 28 new warehouses, including three relocations, for a total of 25 net new warehouses: 18 in the U.S., five in our Canadian segment, and two in our Other International segment, compared to 27 new
warehouses, including three relocations, in 2025;\n\n•Net sales increased 10% to $297,247, driven by an increase in comparable sales and sales at new warehouses;\n\n•Higher gasoline prices positively impacted net sales by $3,501, or 130 basis points, and changes in foreign currencies positively
impacted net sales by $1,332, or 49 basis points;\n\n•Membership fee revenue increased 11% to $5,907, driven by new member sign-ups, membership fee increases, and upgrades to Executive membership;\n\n•Gross margin percentage decreased three basis points; it increased 10 basis points excluding the
impact of gasoline price inflation;\n\n•SG&A expenses as a percentage of net sales decreased 10 basis points; it increased one basis point excluding the impact of gasoline price inflation;",
     "score": 0.3328
    },
    {
     "source": "sec://0000909832-26-000093/unknown#48",
     "title": "COST FY2026 10-K",
     "content": "•SG&A expenses as a percentage of net sales decreased 10 basis points; it increased one basis point excluding the impact of gasoline price inflation;\n\n•The effective tax rate in 2026 was 24.7%, compared to 25.1% in 2025;\n\n•Net income increased 14% to $9,226, $20.76 per diluted
share, compared to $8,099, $18.21 per diluted share in 2025; and\n\n•In April, the Board of Directors approved a 13% increase in the quarterly cash dividend.\n\nTariff Impacts\n\nBeginning in February 2025, the United States imposed tariffs under the International Emergency Economic Powers Act
(IEEPA) on certain goods, materials, and products imported into the United States. We paid the government approximately $500 in IEEPA tariffs. In February 2026, the U.S. Supreme Court ruled that the IEEPA tariffs were unlawful. Following this ruling, the government launched a program to administer
IEEPA refunds.\n\nWe applied the gain contingency model, in accordance with Accounting Standards Codification (ASC) 450-30, “Gain Contingencies,” recognizing recoveries in our consolidated statements of operations only as they were realized. During 2026, we began filing for refunds and received
$184, made up of $174 in refunds, recorded as a reduction to merchandise costs, and $10 recorded as interest income. A portion of these refunds was invested in reducing prices for members. Subsequent to 2026, we received $155 in additional refunds and we intend to continue to invest the majority of
the refunds in increased value for the member. For a small percentage of transactions where corrections are required, refunds may be delayed as the government continues to implement the IEEPA refund process.\n\n25\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nRESULTS OF
OPERATIONS\n\nNet Sales",
     "score": 0.3301
    },
    {
     "source": "sec://0000909832-26-000093/unknown#51",
     "title": "COST FY2026 10-K",
     "content": "(1)Comparable sales for 2024 were calculated using comparable retail weeks.\n\n\nNet sales increased $27,335 or 10% during 2026. The improvement was primarily attributable to an increase in comparable sales of $22,457 or 8%. Comparable sales were positively impacted by increases of
5% in average ticket and 3% in shopping frequency. The remaining increase in net sales was driven by sales at the 25 net new warehouses opened since the end of 2025.\n\nDigitally-enabled comparable sales increased 21% during 2026, both as reported and excluding the impact of changes in foreign
currencies.\n\nSales increased $17,136 or 8% in core merchandise categories, increasing in all categories. Sales in warehouse ancillary and other businesses increased $10,199, or 20%, led by gasoline and pharmacy.\n\nHigher gasoline prices positively impacted net sales by $3,501, or 130 basis
points, with a 12% increase in the average price per gallon. The volume of gasoline sold increased 7%, positively impacting net sales by $1,913, or 71 basis points.\n\nChanges in foreign currencies relative to the U.S. dollar positively impacted net sales by $1,332, or 49 basis points, attributable
to our Other International and Canadian operations.\n\nMembership Fees\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n|
Membership fees | | | $ | 5,907 | |  | | | $ | 5,323 | |  | | | $ | 4,828 | |\n\nMembership fee revenue increased 11% in 2026, driven by new member sign-ups, membership fee increases, and upgrades to Executive memberships. At the end of 2026, member renewal rates were 92.3% in the U.S. and Canada
and 89.8% worldwide.\n\n26\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)",
     "score": 0.3763
    },
    {
     "source": "sec://0000909832-26-000093/unknown#52",
     "title": "COST FY2026 10-K",
     "content": "26\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nAs previously reported, we increased annual membership fees in the U.S. and Canada, effective September 1, 2024. We account for membership fee revenue on a deferred basis, recognized ratably over the one-year
membership period. The fee income increase accounted for approximately 30% and 40% of membership income growth during 2026 and 2025.\n\nGross Margin\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net sales | | | $ | 297,247 | |  | | | $ | 269,912 | |  | | | $ | 249,625 | |\n| Less merchandise costs | | | 264,279 | | |  | | | 239,886 | | |  | | | 222,358 | | |\n| Gross margin | | | $ | 32,968 | |  | | | $ | 30,026 |
|  | | | $ | 27,267 | |\n| Gross margin percentage | | | 11.09 | | % |  | | | 11.12 | | % |  | | | 10.92 | | % |",
     "score": 0.4461
    },
    {
     "source": "sec://0000909832-26-000093/unknown#58",
     "title": "COST FY2026 10-K",
     "content": "Purchase obligations consist of contracts primarily related to merchandise, equipment, and third-party services, the majority of which are due in the next 12 months. Construction and land-purchase obligations consist of contracts primarily related to the development and opening of
new and relocated warehouses, the majority of which (other than leases) are due in the next 12 months.\n\n28\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nWe believe that our cash and investment positions and operating cash flow, with capacity under existing and available
credit agreements, will be sufficient to meet our liquidity and capital requirements for the foreseeable future and that our U.S. current and projected asset position is sufficient to meet our U.S. liquidity requirements.\n\nCash Flows from Operating Activities\n\nOur cash flow provided by
operations is primarily from net sales and membership fees. Cash flow used in operations generally consists of payments to merchandise suppliers, warehouse operating costs, including wages and employee benefits, utilities, credit and debit card processing fees, and operating leases. Cash used in
operations also includes payments for income taxes. Changes in our net investment in merchandise inventories (the difference between merchandise inventories and accounts payable) is impacted by several factors, including inventory levels and turnover, payment terms with suppliers, and early payments
to obtain discounts. Net cash provided by operating activities totaled $15,817 in 2026, compared to $13,335 in 2025. The increase was primarily due to higher operating income, as well as reduced net investment in merchandise inventories. The latter was a result of faster inventory turns and improved
payment terms with suppliers.\n\nCash Flows from Investing Activities\n\nNet cash used in investing activities totaled $6,378 in 2026, compared to $5,311 in 2025, and is primarily related to capital expenditures. Net cash from investing activities also includes purchases and maturities of short-term
investments.\n\nCapital Expenditure Plans",
     "score": 0.2982
    },
    {
     "source": "sec://0000909832-26-000093/unknown#71",
     "title": "COST FY2026 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 52 Weeks Ended | | | | | | | | | | | | | | |\n|  | | | August 30,   2026 | | |  | | | August 31,   2025 |
| |  | | | September 1,   2024 | | |\n| REVENUE | | |  | | |  | | |  | | |  | | |  | | |\n| Net sales | | | $ | 297,247 |  |  | | | $ | 269,912 |  |  | | | $ | 249,625 |  |\n| Membership fees | | | 5,907 | |  |  | | | 5,323 | |  |  | | | 4,828 | |  |\n| Total revenue | | | 303,154 | |  |  | | |
275,235 | |  |  | | | 254,453 | |  |\n| OPERATING EXPENSES | | |  | | |  | | |  | | |  | | |  | | |\n| Merchandise costs | | | 264,279 | |  |  | | | 239,886 | |  |  | | | 222,358 | |  |\n| Selling, general and administrative | | | 27,190 | |  |  | | | 24,966 | |  |  | | | 22,810 | |  |\n| Operating
income | | | 11,685 | |  |  | | | 10,383 | |  |  | | | 9,285 | |  |\n| OTHER INCOME (EXPENSE) | | |  | | |  | | |  | | |  | | |  | | |",
     "score": 0.3962
    },
    {
     "source": "sec://0000909832-26-000093/unknown#75",
     "title": "COST FY2026 10-K",
     "content": "| CURRENT LIABILITIES | | |  | | |  | | |  | | |\n| Accounts payable | | | $ | 22,591 |  |  | | | $ | 19,783 |  |\n| Accrued salaries and benefits | | | 5,641 | |  |  | | | 5,205 | |  |\n| Accrued member rewards | | | 3,037 | |  |  | | | 2,677 | |  |\n| Deferred membership fees | |
| 3,006 | |  |  | | | 2,854 | |  |\n| Current portion of long-term debt | | | 2,248 | |  |  | | | 75 | |  |\n| Other current liabilities | | | 7,429 | |  |  | | | 6,514 | |  |\n| Total current liabilities | | | 43,952 | |  |  | | | 37,108 | |  |\n| OTHER LIABILITIES | | |  | | |  | | |  | | |\n|
Long-term debt, excluding current portion | | | 3,914 | |  |  | | | 5,713 | |  |\n| Long-term operating lease liabilities | | | 2,414 | |  |  | | | 2,460 | |  |\n| Other long-term liabilities | | | 2,962 | |  |  | | | 2,654 | |  |\n| TOTAL LIABILITIES | | | 53,242 | |  |  | | | 47,935 | |  |\n|
COMMITMENTS AND CONTINGENCIES | | |  | | |  | | |  | | |\n| EQUITY | | |  | | |  | | |  | | |\n| Preferred stock $0.005 par value; 100,000,000 shares authorized; no shares issued and outstanding | | | — | |  |  | | | — | |  |\n| Common stock $0.005 par value; 900,000,000 shares authorized;
443,266,000 and 443,237,000 shares issued and outstanding | | | 2 | |  |  | | | 2 | |  |",
     "score": 0.3129
    }
   ]
  }
 ]
}

[tool 1] tavily_financial_search {"query": "Costco membership fee increase timing management explicitly stated when next increase", "ticker": "COST"}
{
 "query": "COST Costco membership fee increase timing management explicitly stated when next increase",
 "results": [
  {
   "title": "Costco (COST) Raises Annual Membership Fee - Bloomberg",
   "url": "https://www.bloomberg.com/news/articles/2024-07-10/costco-raises-annual-membership-fee-for-first-time-since-2017",
   "content": "The 8% price increase for US and Canadian members will take effect Sept. 1, Costco said in a statement Wednesday. The price of the retailer’s premium membership will rise to $130 from $120. The move will affect about 52 million memberships. [...] Consumer\n\n# Costco Hikes Annual
Membership Fee for First Time Since 2017\n\n Basic membership will now cost $65 a year, up from $60\n Investors and analysts have long waited for the increase\n\nThis article is for subscribers only.\n\nCostco Wholesale Corp. is boosting its membership fees for the first time since 2017, raising the
charge for a basic membership to $65 a year from $60.",
   "published_date": null
  },
  {
   "title": "Costco hikes membership fee for the first time since 2017",
   "url": "https://www.cnbc.com/2024/07/10/costco-hikes-membership-fee-for-the-first-time-since-2017.html",
   "content": "Shares rose about 2% in extended trading Wednesday.\n\nIt marks Costco's first membership rate increase since June 2017. On average, the company has raised rates roughly every five and a half years, which would have put Costco on track to raise the fee in late 2022 or early 2023.
[...] In this article\n\nYou will soon have to pay more if you want to shop at Costco.\n\nThe membership-based warehouse club said Wednesday that it will increase its membership fee by $5 in the U.S. and Canada as of Sept. 1. That is an increase to $65 from $60 for annual memberships. Its higher-
tier plan, called \"Executive Membership,\" will increase to $130 a year from $120.\n\nCostco said the fee increases would affect about 52 million memberships, a little over half of which are executive memberships. [...] Costco relies on membership fees to drive most of its revenue and help keep
merchandise prices low. Its rival, Walmart-owned Sam's Club, hiked its own membership fee in 2022 for the first time in nine years. Yet, even after the fee bump, a Sam's Club membership was cheaper, at $50 for club members and $110 for members of its higher-tier level, \"Plus,\" on an annual basis.
At BJ's Wholesale, annual membership fees are $55 and $110, for club members and its own higher tier, respectively.",
   "published_date": null
  },
  {
   "title": "Costco membership price hike is 'a question of when, not if'",
   "url": "https://www.cnbc.com/2022/12/13/costco-membership-prices-are-going-up.html",
   "content": "Related Stories\n\nCostco's $60 annual membership fee is going up sooner or later.\n\nDuring the company's earnings report last week, chief financial officer Richard Galanti said that while \"there's no rush\" to raise prices, an eventual hike is \"a question of when, not if.\"\n\nThe
Seattle-based wholesaler's last price hike in June of 2017 saw it raise the price of its Standard Gold Star membership from $55 to $60, and increase the price of its Executive membership from $110 to $120. [...] Those prices have remained steady ever since. Rival Sam's Club, meanwhile, recently
increased its prices for the first time in nearly a decade.\n\nGalanti told analysts that on average Costco has increased its rates every five years and seven months, which would put Costco on track for another increase in January.\n\nStill, Galanti said, no decisions have been made about when the
fee increase will be implemented. [...] \"It's a question of when, not if,\" he said on the call. \"There's no analytical framework we use other than we feel very good about our member loyalty and our strength. And if we wanted to do it yesterday, we could. If we want to do it six months from now,
we can. So, we'll wait and see.\"\n\nOnly customers with memberships to Costco are permitted to shop in its warehouses, with the company boasting a 92.5% renewal rate in the U.S. and Canada.",
   "published_date": null
  },
  {
   "title": "Costco (COST) Won’t Raise Membership Fees as Renewals Surge - Bloomberg",
   "url": "https://www.bloomberg.com/news/articles/2022-09-22/costco-holds-off-on-membership-fee-hikes-amid-record-renewals",
   "content": "Inside A Costco Wholesale Location Ahead Of Earnings Figures\n\nCostco Wholesale chose not to raise its membership fees amid record renewal rates in the company’s fourth quarter.\n\n“There are no specific plans regarding a fee increase at this time,” said Chief Financial Officer
Richard Galanti on the earnings conference call. However, he continued, “it’s a question of when, not if.” [...] ### Products\n\n### Industry Products\n\n### Media\n\n### Media Services\n\n### Bloomberg\n\nConnecting decision makers to a dynamic network of information, people and ideas, Bloomberg
quickly and accurately delivers business and financial information, news and insight around the world\n\n### For Customers\n\n### Support\n\nAmericas+1 212 318 2000\n\nEMEA+44 20 7330 7500\n\nAsia Pacific+65 6212 1000\n\n# Costco Won’t Raise Membership Fees as Renewals Surge [...] ###
Bloomberg\n\nConnecting decision makers to a dynamic network of information, people and ideas, Bloomberg quickly and accurately delivers business and financial information, news and insight around the world\n\n### For Customers\n\n### Support\n\nAmericas+1 212 318 2000\n\nEMEA+44 20 7330
7500\n\nAsia Pacific+65 6212 1000\n\n### Company\n\n### Communications\n\n### Follow\n\n### Products\n\n### Industry Products\n\n### Media\n\n### Media Services\n\n### Company\n\n### Communications\n\n### Follow\n\n### Products",
   "published_date": null
  },
  {
   "title": "Costco price hike: Is the $130 Executive Membership worth the money?",
   "url": "https://www.cnbc.com/make-it/2024/07/11/costco-price-hike-is-the-130-executive-membership-worth-the-money.html",
   "content": "Related Stories\n\nCostco is increasing the price of admission to its warehouse stores for the first time since 2017.\n\nBeginning Sept. 1 the members-only chain will raise the price of its $60 Gold Star membership to $65. Its premium $120 Executive Membership will now cost $10
more.\n\nCostco on average raises its rates every five and a half years, meaning that customers likely won't see their bill go up again until at least 2030 if current patterns hold. [...] Calculating if the $130 Executive Membership is worth the upcharge is simple. Because you get 2%, you'll need to
spend $3,250 to receive $65 in cash back. At that point, your effective annual membership rate is back down to $65. [...] But if your annual spend regularly tops $3,250, you're better off with the Executive Membership. Every additional dollar you spend after $3,250 will bring your annual fee further
and further below $65 and end up saving you money in the long run.\n\nCostco's membership page includes a calculator where you can enter how much you spend at the store each month to see how much cash back you can expect to receive at the end of the year.",
   "published_date": null
  }
 ]
}
----- END EVIDENCE F0070 -----

----- BEGIN ANSWER F0070 -----
結論：**好市多下一次會員費調漲「可能會發生」，但目前沒有可靠證據顯示管理層已經公布明確時間點。**最近一次調漲其實已在 **2024 年 9 月 1 日**生效：美國、加拿大 Gold Star 會員年費由 60 美元升至 65 美元，Executive 會員由 120 美元升至 130 美元。[1]

管理層過去的說法比較像是「遲早會調」，而不是「某年某月會調」：

- 2022 年 CFO Richard Galanti 表示，調漲是 **“a question of when, not if”**，但同時說「沒有急迫性」，也沒有決定何時實施。[2]
- 2024 年調漲後，外界依照好市多過去平均約五年半調一次的節奏推估，下一次可能要等到約 2030 年左右；但這只是歷史週期推算，不是公司承諾的時間表。[3]
- 好市多最新可取得的 10-K 顯示，2024 年調漲後美國年費仍為 65 美元，且會員費收入成長部分來自該次調漲；該文件沒有給出下一次調漲的日期。[4]

所以，如果你問「是不是快要調了」：**不能說已經快要調，至少管理層沒有把時間點講明。**比較準確的解讀是：公司保留調漲空間，會員續約率和 Executive 會員滲透率仍然很高，因此未來調漲具備條件；但「近期一定調」目前仍屬市場推測，而非管理層正式指引。最新 10-K 顯示，美加續約率為 92.3%，Executive 會員約占付費會員的一半，這些都是公司可能考量的因素。[5]

[1]: https://www.cnbc.com/2024/07/10/costco-hikes-membership-fee-for-the-first-time-since-2017.html "Costco hikes membership fee for the first time since 2017"
[2]: https://www.cnbc.com/2022/12/13/costco-membership-prices-are-going-up.html "Costco membership price hike is 'a question of when, not if'"
[3]: https://www.cnbc.com/make-it/2024/07/11/costco-price-hike-is-the-130-executive-membership-worth-the-money.html "Costco price hike: Is the $130 Executive Membership worth the money?"
[4]: SEC 10-K excerpt
[5]: SEC 10-K excerpt
----- END ANSWER F0070 -----

===== ITEM F0071 =====

QUESTION:
Visa 為什麼常被看成比傳統放款銀行更穩的生意？

----- BEGIN EVIDENCE F0071 -----
[tool 0] sec_filing_search {"query": "business model payment network does not issue cards or extend credit, limited credit risk compared with banks; revenue sources transaction volume and payment processing", "ticker": "V", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-09-30",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "V",
   "fiscal_year": 2025,
   "item": "Item 1",
   "prelude": "Excerpts from V FY2025 10-K, Item 1 (Business) — 5 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001403161-25-000089/1#2",
     "title": "V FY2025 10-K · Item 1 · OVERVIEW",
     "content": "### OVERVIEW\n\nVisa is one of the world’s leaders in digital payments. Our purpose is to uplift everyone, everywhere by being the best way to pay and be paid. Since Visa’s early days in 1958, we have been in the business of facilitating secure, reliable and efficient global
commerce and money movement. We provide transaction processing services (primarily authorization, clearing and settlement) among consumers, issuing and acquiring financial institutions and sellers in a structure we call the “four-party” model. Please see Our Core Business discussion below. As the
payments ecosystem continues to evolve, we have broadened this model to include digital banks, digital wallets, a range of financial technology companies (fintechs), governments and non-governmental organizations (NGOs). We are focused on extending, enhancing and investing in our proprietary
advanced transaction processing network, VisaNet, to offer a single connection point for facilitating money movement to multiple endpoints through various form factors and innovative technologies across more than 200 countries and territories. Visa is committed to advancing innovation within the
payment technology sector. Building upon our track record of industry leadership, including early adoption and integration of artificial intelligence (AI) models in payment systems, Visa continues to invest in the development and deployment of next-generation technologies, such as generative AI
(GenAI), stablecoins and agentic commerce. During fiscal 2025, 329 billion payments and cash transactions with Visa’s brand were processed by Visa or other networks, equating to an average of 901 million transactions per day. Of the 329 billion total transactions, 258 billion were processed by
Visa.\n\n•We offer a wide range of Visa-branded payment products that our clients, including nearly 14,500 financial institutions, use to develop and offer payment solutions or services, including credit, debit, prepaid and cash access programs for individual, business and government account
holders. During fiscal 2025, Visa’s total payments and cash volume was $17 trillion, and we had nearly 5 billion payment credentials, which are issued Visa card accounts, that were available to be used at more than 175 million merchant locations worldwide.(1)",
     "score": 0.4669,
     "subsection": "OVERVIEW"
    },
    {
     "source": "sec://0001403161-25-000089/1#3",
     "title": "V FY2025 10-K · Item 1",
     "content": "•We take an open partnership approach and seek to provide value by enabling access to our global network through multiple integration methods, including programmatic access via application programming interfaces (APIs) and structured data exchange through our Model Context Protocol
(MCP) server. We partner with traditional financial institutions and emerging fintech and AI companies to innovate and expand the payments ecosystem, enabling them to leverage our platform infrastructure to accelerate their business growth and market expansion.\n\n•We are using our componentized
capabilities and global connectivity to power all types of payments and deliver services to all types of clients worldwide through our Visa as a Service stack, which has four layers: the foundation layer, the services layer, the solutions layer and the access layer. Our foundation layer comprises
the network infrastructure that enables connections to approximately 12 billion cards, bank accounts and digital wallets with more than 175 million merchant locations across more than 200 countries and territories. Our services layer organizes core capabilities, including authentication, risk
management and fraud detection, into discrete, reusable components that can be utilized individually or combined into solutions. These modular services are the building blocks of our comprehensive portfolio in our solutions layer, which are enhanced to create new features and capabilities for our
clients. Finally, the access layer provides clients the entry point to these solutions via on-demand APIs, our MCP server that enables AI systems to interface with our Visa Intelligent Commerce APIs, and fully managed solutions. The Visa as a Service stack enables organizations of any size to access
and scale Visa’s network capabilities globally.\n\n•We are accelerating the migration to digital payments through our network of networks strategy. We aim to provide a single connection point so that Visa clients can enable money movement for businesses, governments and consumers, regardless of
which network is used to start or complete the transaction. This model ultimately helps to unify a complex payments ecosystem. Visa’s network of networks approach creates opportunities by facilitating person-to-person (P2P), business-to-consumer (B2C), business-to-business (B2B) and government-to-
consumer (G2C) payments, in addition to consumer-to-business (C2B) payments.\n\n(1) Data provided to Visa by acquiring institutions and other third parties as of June 30, 2025.\n\n4\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)",
     "score": 0.474
    },
    {
     "source": "sec://0001403161-25-000089/1#6",
     "title": "V FY2025 10-K · Item 1 · OUR CORE BUSINESS",
     "content": "### OUR CORE BUSINESS\n\n![Picture1.jpg](v-20250930_g3.jpg)\n\nIn a typical Visa C2B payment transaction, the consumer purchases goods or services from a seller using a Visa card or payment product. The seller presents the transaction data to an acquirer, usually a bank or third-
party processing firm that supports acceptance of Visa cards or payment products, for verification and processing. Through VisaNet, the acquirer presents the transaction data to Visa, which in turn sends the transaction data to the issuer to check the account holder’s account balance or credit line
for authorization. After the transaction is authorized, the issuer posts the transaction to the consumer’s account and effectively pays the acquirer an amount equal to the value of the transaction, minus the interchange reimbursement fee (IRF). The acquirer pays the amount of the purchase, minus the
merchant discount rate (MDR), to the seller.\n\nVisa earns revenue by facilitating money movement across more than 200 countries and territories, among a global set of consumers, sellers, financial institutions and government entities, through innovative
technologies.\n\n5\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)\n\nOur net revenue in fiscal 2025 consisted of the following:\n\n![Visa-AR25_Business-section-stats_Revenue-details.jpg](v-20250930_g4.jpg)",
     "score": 0.5119,
     "subsection": "OUR CORE BUSINESS"
    },
    {
     "source": "sec://0001403161-25-000089/1#8",
     "title": "V FY2025 10-K · Item 1",
     "content": "Visa is not a financial institution. We do not issue cards, extend credit or set rates and fees for account holders of Visa products nor do we earn revenue from or bear credit risk with respect to any of these activities. Interchange reimbursement fees reflect the value sellers
receive from accepting our products and play a key role in balancing the costs and benefits that account holders and sellers derive from participating in our payments network. Generally, IRFs are paid by acquirers to issuers. We establish default IRFs that apply absent other established settlement
terms. These default IRFs are set independently from the revenue we receive from issuers and acquirers. Our acquiring clients are responsible for soliciting sellers and for setting the fees they charge to sellers for the MDR. Visa sets fees to acquirers independently from any fees that acquirers may
charge sellers. Therefore, the fees we receive from issuers and acquirers are not derived from IRFs or MDRs.\n\n6\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)\n\n![Visa-AR24_Business-section-stats_Our-Strategy-
header.jpg](v-20250930_g10.jpg)\n\nVisa’s strategy is to accelerate revenue growth through consumer payments (CP), commercial and money movement solutions (CMS) and value-added services (VAS), as well as fortify the key foundations of our business model. In CP, we are focused on strengthening our
impact in card-based consumer payments and expanding our reach in non-card-based payments. In CMS, formerly known as new flows, we are driving and enabling further penetration of commercial payments and money movement. Finally, in VAS, we are delivering innovative services to deepen our partnerships
with our clients.\n\n![Visa-AR25_Business-section-stats_Our-Strategy-icons.jpg](v-20250930_g11.jpg)\n\n![Visa-AR24_Business-section-stats_Revenue-growth-drivers-header.jpg](v-20250930_g12.jpg)\n\nWe seek to accelerate revenue growth through the following areas:\n\n![Visa-AR25_Business-section-
stats_Revenue-growth-drivers-icons.jpg](v-20250930_g13.jpg)",
     "score": 0.4926
    },
    {
     "source": "sec://0001403161-25-000089/1#42",
     "title": "V FY2025 10-K · Item 1",
     "content": "(1)American Express, Diners Club / Discover, JCB and Mastercard data sourced from The Nilson Report issue 1288 (June 2025). Includes all consumer, small business and commercial credit, debit and prepaid cards for Visa and Mastercard and includes all consumer, small business and
commercial credit cards, including business from third-party issuers, for American Express, Diners Club / Discover, and JCB. JCB figures include other payment-related products and some figures are estimates. Mastercard excludes Maestro and Cirrus figures.\n\n(2)Total volume is the sum of payments
volume and cash volume. Cash volume generally consists of cash access transactions, balance access transactions, balance transfers and convenience checks.\n\nLocal and Regional Networks: Operated in many countries, these networks often have the support of government influence or mandate. In some
cases, they are owned by financial institutions or payment processors.\n\n17\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)\n\nThese networks typically focus on debit payment products, and may have strong local acceptance and recognizable
brands. Examples include NYCE, Pulse and STAR in the U.S.; Interac in Canada; and eftpos in Australia.\n\nAlternative Payments Providers: These providers, such as closed commerce ecosystems, BNPL solutions and cryptocurrency platforms (including stablecoins), often have a primary focus of enabling
payments through ecommerce and mobile channels; however, they are expanding or may expand their offerings to the physical point of sale. These companies may process payments using in-house account transfers between parties, electronic funds transfer networks like the ACH, global or local networks
like Visa, or some combination of the foregoing. In some cases, these entities can be both a partner and a competitor to Visa.",
     "score": 0.5346
    }
   ]
  },
  {
   "ticker": "V",
   "fiscal_year": 2025,
   "item": "Item 8",
   "prelude": "Excerpts from V FY2025 10-K, Item 8 (Financial Statements and Supplementary Data) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001403161-25-000089/8#208",
     "title": "V FY2025 10-K · Item 8",
     "content": "Revenue recognition. The Company’s net revenue is comprised principally of the following categories: service revenue, data processing revenue, international transaction revenue, and other revenue, reduced by client incentives. As a payments network service provider, the Company’s
obligation to the customer is to stand ready to provide continuous access to Visa’s payments network over the contractual term, facilitate the processing of payment transactions, including authorization, clearing and settlement, and deliver related products and services. The Company delivers its
payments network services directly to issuers and acquirers, who, in turn, provide those services to others within the payments network: sellers and consumers. The Company considers all parties in Visa’s payments network as customers, and earns net revenue primarily from issuers and acquirers.
Consideration is variable, based primarily on the amount and type of transactions and payments volume on Visa’s products. The transaction price for each specific service is reported net of discounts attributable to individual services or fees. The Company recognizes revenue, net of sales and other
similar taxes, as the payments network services are performed, in an amount that reflects the consideration the Company expects to receive in exchange for those services. The Company has elected the optional exemption to not disclose the remaining performance obligations related to payments network
services and other performance obligations that are constrained by, and dependent upon, the future performance of its clients, which are variable in nature.\n\nThe Company’s value-added services consist of Issuing Solutions, Acceptance Solutions, Risk and Security Solutions, and Advisory and Other
Services. These services may be offered in combination with the Company’s payments network services or independently as standalone products. The Company earns revenue from its Value-added Services through fixed or transaction-based fees, and recognizes revenue, net of sales and other similar taxes,
as these value-added services are performed.\n\nFor revenue generated from arrangements that involve third parties, the Company assesses whether it is the principal, and recognizes revenue on a gross basis, or the agent, and recognizes revenue on a net basis. In making this assessment, the Company
considers whether it obtains the control of the specified services before they are transferred to the customer, or it is arranging for the services to be provided.\n\n69\n\n\n[Table of Contents](#i3e21d382a73642188017c034fc47d460_7)",
     "score": 0.4827
    }
   ]
  },
  {
   "ticker": "V",
   "fiscal_year": 2025,
   "item": "Item 7",
   "prelude": "Excerpts from V FY2025 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 2 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001403161-25-000089/7#105",
     "title": "V FY2025 10-K · Item 7 · Overview",
     "content": "### Overview\n\nVisa is a global payments technology company that facilitates secure, reliable and efficient global commerce and money movement. We provide transaction processing services (primarily authorization, clearing and settlement) among consumers, issuing and acquiring
financial institutions and sellers. We are focused on extending, enhancing and investing in our proprietary advanced transaction processing network, VisaNet, to offer a single connection point for facilitating money movement to multiple endpoints through various form factors and innovative
technologies across more than 200 countries and territories. Visa is not a financial institution. We do not issue cards, extend credit or set rates and fees for account holders of Visa products.\n\nFinancial overview. A summary of our GAAP and non-GAAP operating results is as follows:",
     "score": 0.4626,
     "subsection": "Overview"
    },
    {
     "source": "sec://0001403161-25-000089/7#133",
     "title": "V FY2025 10-K · Item 7",
     "content": "(1)Figures in the table may not recalculate exactly due to rounding. Percentage changes are calculated based on unrounded numbers.\n\n45\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)\n\nNet revenue increased in fiscal 2025 over
the prior year primarily due to the growth in processed transactions, nominal cross-border volume, and nominal payments volume, partially offset by higher client incentives.\n\nOur net revenue is impacted by the overall strengthening or weakening of the U.S. dollar as payments volume and related
revenue denominated in local currencies are converted to U.S. dollars. In fiscal 2025, exchange rate movements did not have a material impact on net revenue growth.\n\nThe following table presents the components of our net revenue:",
     "score": 0.4718
    }
   ]
  },
  {
   "ticker": "V",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from V FY2025 10-K, Item 1A (Risk Factors) — 2 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001403161-25-000089/1a#57",
     "title": "V FY2025 10-K · Item 1A",
     "content": "•As innovations in payment technology have enabled us to expand into new products and services, they have also expanded the potential scope of regulatory influence. For instance, new products and capabilities, including tokenization, push payments and cross-border money movement
solutions could bring increased licensing or authorization requirements in the countries where the product or capability is offered. Furthermore, certain portions of our business are regulated as payment institutions or as money transmitters, subjecting us to various licensing, supervisory and other
requirements. As we continue to expand our capabilities and offerings in furtherance of our multi-year growth strategy, we will need to obtain new types of licenses. These licenses could result in increased supervisory and compliance obligations that are distinct from the obligations we are subject
to in our capacity as a payment card network.\n\nRegulators around the world increasingly take note of each other’s approaches to regulating the payments industry. Consequently, development in one jurisdiction may influence regulatory approaches in another. The risks created by a new law, regulation
or regulatory outcome in one jurisdiction have the potential to be replicated and to negatively affect our business in another jurisdiction or in other product offerings. For example, our settlement with the European Commission on cross-border interchange rates has drawn attention from some
regulators in other parts of the world. Similarly, new regulations involving one product offering may prompt regulators to extend the regulations to other product offerings. For example, credit payments could become subject to similar regulation as debit payments (or vice versa). The RBA initially
capped credit interchange, but subsequently capped debit interchange as well.",
     "score": 0.4625
    },
    {
     "source": "sec://0001403161-25-000089/1a#69",
     "title": "V FY2025 10-K · Item 1A",
     "content": "Certain of our competitors operate with different business models, have different cost structures or participate in different market segments. Many of these competitors are also able to use existing payment networks without being subject to many of the associated costs. Moreover,
these competitors also occupy various roles in the payments ecosystem that enable them to influence payment choice of other participants. Some of our competitors, including American Express, Discover, private-label card networks, virtual currency providers, technology companies that enable the
exchange of digital assets, and certain alternative payments systems like Alipay and WeChat Pay, operate closed-loop payments systems, with direct connections to both sellers and consumers. Those business models may ultimately prove more successful or more adaptable to regulatory, technological and
other developments. In some cases, these competitors have the support of government mandates that prohibit, limit or otherwise hinder our ability to compete for transactions within certain countries and regions. For more information on government actions, initiatives or regulations that could impact
competition, please see Item 1—Government Regulation and Item 1A—Regulatory Risks above.\n\nWe expect the competitive landscape to continue to shift and evolve. For example:\n\n•We, along with our competitors, clients, network participants, and others are developing or participating in alternative
payments systems or products, such as mobile payment services, ecommerce payment services, P2P payment services, real-time and faster payment initiatives, and payment services that permit\n\n27\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of
Contents](#i3e21d382a73642188017c034fc47d460_7)\n\nACH or direct debits from or to consumer checking accounts, that could either reduce our role or otherwise disintermediate us from the transaction processing or the value-added services we provide to support such processing. Examples include
initiatives from The Clearing House, an association consisting of large financial institutions that has developed its own faster payments system; Early Warning Services, which operates Zelle, a bank-offered alternative network that provides another platform for faster funds or real-time payments
across a variety of payment types, including P2P, corporate and government disbursement, bill pay and deposit check transactions; and cryptocurrency, including stablecoin-based payments initiatives.",
     "score": 0.4636
    }
   ]
  }
 ]
}

[tool 1] sec_filing_search {"query": "risk factors payment volume transaction volume, fraud, cyberattacks, regulation, competition, economic conditions, and dependence on financial institutions", "ticker": "V", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-09-30",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "V",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from V FY2025 10-K, Item 1A (Risk Factors) — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001403161-25-000089/1a#51",
     "title": "V FY2025 10-K · Item 1A · Regulatory Risks",
     "content": "### Regulatory Risks\n\nWe are subject to complex and evolving global regulations that could harm our business and financial results.\n\nAs a global payments technology company, we are subject to complex and evolving regulations that govern our operations. Such regulations may
increase in quantity, complexity and scope in response to heightened geopolitical tensions. See Item 1—Government Regulation for more information on the most significant areas of regulation that affect our business. The impact of these regulations on us, our clients, and other third parties could
limit our ability to enforce our payments system rules; require us to adopt new rules or change existing rules; affect our existing contractual arrangements; and increase our compliance costs. As discussed in more detail below, we may face differing rules and regulations in matters like interchange
reimbursement rates, preferred routing, domestic processing and localization requirements, currency conversion, point-of-sale transaction rules and practices, privacy, data use and protection, licensing requirements and associated product technology. As a result, the Visa operating rules and our
other contractual commitments may differ from country to country, state to state, or product to product. Complying with these and other regulations increases our costs and operational complexity, and reduces our revenue opportunities.\n\nIf widely varying regulations come into existence worldwide,
we may have difficulty rapidly adjusting our products, services, fees and other important aspects of our business to comply with the regulations. Our compliance programs and policies are designed to support our compliance with a wide array of regulations and laws, such as regulations regarding anti-
money laundering, anti-corruption, competition, money transfer services, privacy and sanctions, and we continually adjust our compliance programs as regulations evolve. However, we cannot guarantee that our practices will be deemed compliant by all applicable regulatory authorities. In the event our
controls should fail or we are found to be out of compliance for other reasons, we could be subject to monetary damages, civil and criminal penalties, litigation, investigations and proceedings, and damage to our global brands and reputation.\n\nIncreased scrutiny and regulation of the global
payments industry, including with respect to interchange reimbursement fees, merchant discount rates, operating rules, risk management protocols and other related practices, could harm our business.",
     "score": 0.5689,
     "subsection": "Regulatory Risks"
    },
    {
     "source": "sec://0001403161-25-000089/1a#52",
     "title": "V FY2025 10-K · Item 1A",
     "content": "Increased scrutiny and regulation of the global payments industry, including with respect to interchange reimbursement fees, merchant discount rates, operating rules, risk management protocols and other related practices, could harm our business.\n\nRegulators around the world have
been establishing or increasing their authority to regulate various aspects of the payments industry. See Item 1—Government Regulation for more information. In the U.S. and many other jurisdictions, we have historically set default IRFs. Even though we generally do not receive any revenue related to
IRFs in a payment transaction (in the context of credit and debit transactions, those fees are paid by the acquirers to the issuers; the reverse is true for certain transactions like ATM transactions), IRFs are a factor on which we compete with other payments providers and are therefore an important
determinant of the volume of transactions we process. Consequently, changes to these fees, whether voluntarily or by mandate, can substantially affect our overall payments volume and net revenue.\n\nInterchange reimbursement fees, certain operating rules and related practices continue to be subject
to increased government regulation globally, and regulatory authorities and central banks in a number of jurisdictions have reviewed or are reviewing these fees, rules and practices. For example:",
     "score": 0.6049
    },
    {
     "source": "sec://0001403161-25-000089/1a#57",
     "title": "V FY2025 10-K · Item 1A",
     "content": "•As innovations in payment technology have enabled us to expand into new products and services, they have also expanded the potential scope of regulatory influence. For instance, new products and capabilities, including tokenization, push payments and cross-border money movement
solutions could bring increased licensing or authorization requirements in the countries where the product or capability is offered. Furthermore, certain portions of our business are regulated as payment institutions or as money transmitters, subjecting us to various licensing, supervisory and other
requirements. As we continue to expand our capabilities and offerings in furtherance of our multi-year growth strategy, we will need to obtain new types of licenses. These licenses could result in increased supervisory and compliance obligations that are distinct from the obligations we are subject
to in our capacity as a payment card network.\n\nRegulators around the world increasingly take note of each other’s approaches to regulating the payments industry. Consequently, development in one jurisdiction may influence regulatory approaches in another. The risks created by a new law, regulation
or regulatory outcome in one jurisdiction have the potential to be replicated and to negatively affect our business in another jurisdiction or in other product offerings. For example, our settlement with the European Commission on cross-border interchange rates has drawn attention from some
regulators in other parts of the world. Similarly, new regulations involving one product offering may prompt regulators to extend the regulations to other product offerings. For example, credit payments could become subject to similar regulation as debit payments (or vice versa). The RBA initially
capped credit interchange, but subsequently capped debit interchange as well.",
     "score": 0.578
    },
    {
     "source": "sec://0001403161-25-000089/1a#58",
     "title": "V FY2025 10-K · Item 1A",
     "content": "When we cannot set default interchange reimbursement rates at optimal levels, issuers and acquirers may find our payments system less attractive. This may increase the attractiveness of other payments systems, such as our competitors’ closed-loop payments systems with direct
connections to both sellers and consumers. We believe some issuers may react to such regulations by charging new or higher fees, or reducing certain benefits to consumers, which makes our products less appealing to consumers. Some acquirers may elect to charge higher MDR regardless of the Visa
interchange reimbursement rate, causing sellers not to accept our products or to steer consumers to alternative payments systems or forms of payment. In addition, in an effort to reduce the expense of their payment programs, some issuers and acquirers have obtained, and may continue to obtain,
incentives from us, including reductions in the fees that we charge, which directly impacts our net revenue. The evolving and increasing regulatory focus on the payments industry could negatively impact or reduce the number of Visa products our clients issue, the volume of payments we process, our
net revenue, our brands, our competitive positioning, our ability to use our intellectual property to differentiate our products and services, the quality and types of products and services we offer, the countries in which our products and services are used, and the types of consumers and sellers
who can obtain or accept our products and services, all of which could harm our business and financial results.\n\nFinally, policymakers and regulatory bodies in the U.S., Europe and other parts of the world are exploring ways to reform existing competition laws to meet the needs of the digital
economy, including restricting large technology companies from engaging in mergers and acquisitions, requiring them to interoperate with potential competitors, and prohibiting certain kinds of self-preferencing behaviors. While the focus of these efforts remains primarily on increasing regulation of
large technology, ecommerce and social media companies, they could also have implications for other types of companies including payments networks, which could constrain our ability to\n\n23\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of
Contents](#i3e21d382a73642188017c034fc47d460_7)\n\neffectively manage our business. Recent political developments around the world, including recent shifts in trade policy, have added additional uncertainty with respect to new laws and regulations or changes in the interpretations or enforcement of
existing laws and regulations, and increased risk of financial regulatory fragmentation.",
     "score": 0.5625
    },
    {
     "source": "sec://0001403161-25-000089/1a#68",
     "title": "V FY2025 10-K · Item 1A · Business Risks",
     "content": "### Business Risks\n\nWe face intense competition in our industry.\n\nThe global payments space is intensely competitive. As technology evolves and consumer expectations change, new competitors or methods of payment emerge, and existing clients and competitors assume different
roles. Our products compete with cash, checks, electronic payments, virtual currency payments, global or multi-regional networks, other domestic and closed-loop payments systems, digital wallets and alternative payments providers primarily focused on enabling payments through ecommerce and mobile
channels. As the global payments space becomes more complex, we face increasing competition from our clients, other emerging payment providers such as fintechs, other digital payments, technology companies that have developed payments systems enabled through online activity in ecommerce, social
media, and mobile channels, other providers of CMS and VAS offerings, as well as governments in a number of jurisdictions (e.g., U.S., Brazil and India), that are developing, supporting and/or operating national schemes, RTP networks and other payment platforms. For more information, please see Item
1—Competition above.\n\nOur competitors may acquire, develop or make better use of substantially better technology, have more widely adopted delivery channels, or have greater financial resources. They may offer more effective, innovative or a wider range of programs, products and services. They may
use more effective advertising and marketing strategies that result in broader brand recognition and greater use, including with respect to issuance and seller acceptance. They may also develop better solutions or offer more favorable pricing. Moreover, even if we successfully adapt to technological
change and the proliferation of alternative types of payment services by developing and offering our own services in these areas, such services may provide less favorable financial terms for us, which could hurt our financial results. We expect to face more competition as AI continues to advance and
GenAI and agentic AI capabilities become integrated into payments and related services in two main ways: first, by competitors successfully enhancing their products, services and external offerings with AI to achieve greater and faster product adoption; and second, by competitors providing internal
AI tools to upskill their employees for greater operational efficiencies and impact. In addition, our competitors may have, or in the future may obtain, proprietary rights that would prevent, limit or interfere with our ability to design, use or sell our own AI-based offerings or services to our
clients and other third parties. If we do not continue to invest in developing and supporting our AI-based initiatives, we may fall behind technological developments and evolving industry standards, which would likewise harm our reputation and ability to effectively compete, retain clients or grow
our business.",
     "score": 0.5965,
     "subsection": "Business Risks"
    },
    {
     "source": "sec://0001403161-25-000089/1a#72",
     "title": "V FY2025 10-K · Item 1A",
     "content": "[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)\n\nIn addition, we face intense competitive pressure on the prices we charge our financial institution clients. In certain regions, we are increasingly facing competition from RTP
networks, other payment facilitators offering lower pricing, and government involvement in domestic and cross-border payments. In order to stay competitive, we may need to adjust our pricing or offer incentives to our clients to grow payments volume, enter new market segments, adapt to regulatory
changes, and expand their use and acceptance of Visa products and services. These include up-front cash payments, fee discounts, rebates, credits, performance-based incentives, marketing and other support payments that impact our net revenue and profitability. In addition, we offer incentives to
certain sellers and acquirers to encourage them to route transactions to Visa. Pressures on pricing, incentives, fee discounts and rebates could moderate our growth. If we are not able to implement cost containment and productivity initiatives in other areas of our business or grow our volume in
other ways to offset or absorb the financial impact of these incentives, fee discounts and rebates, it may harm our net revenue and profits.\n\nSellers’ and processors’ continued push to lower acceptance costs and challenge industry practices could harm our business.",
     "score": 0.5657
    },
    {
     "source": "sec://0001403161-25-000089/1a#73",
     "title": "V FY2025 10-K · Item 1A",
     "content": "Sellers’ and processors’ continued push to lower acceptance costs and challenge industry practices could harm our business.\n\nWe rely in part on sellers and their relationships with our clients or their agents to maintain and expand the use and acceptance of Visa products. Certain
sellers and seller-affiliated groups have been exerting their influence in the global payments system in certain jurisdictions, such as the U.S., Australia, Canada and Europe, to attempt to lower acceptance costs paid by sellers to acquirers or their agents to accept payment products or services, by
lobbying for new legislation, seeking regulatory intervention, filing lawsuits and in some cases, surcharging or refusing to accept Visa products. If they are successful in their efforts, we may face increased compliance and litigation expenses, issuers may decrease their issuance of our products,
and consumer usage of our products could be adversely impacted. For example, in the U.S., certain stakeholders have raised concerns regarding how payment security standards and rules may impact debit routing choice and the cost of payment card acceptance. U.S. seller-affiliated groups and processors
have expressed concerns regarding the EMV certification process and the roles of industry bodies such as EMVCo and the Payment Card Industry Security Standards Council in the development of payment card standards. Moreover, many sellers have advocated for lower acceptance costs in the form of
reduced interchange rates, which could result in some issuers eliminating or reducing their promotion or use of Visa’s products and services, eliminating or reducing cardholder benefits such as rewards programs, or charging account holders increased or new fees for using Visa-branded products, all
of which could negatively impact Visa’s payments volume and related revenue. Finally, some sellers and processors have advocated for changes to industry practices and Visa acceptance requirements at the point of sale, including the ability for sellers to accept only certain types of Visa products,
to mandate only PIN authenticated transactions, to differentiate or steer among Visa product types issued by different financial institutions, and to impose surcharges on consumers presenting Visa products as their form of payment. A number of the issues flagged in this risk factor are subject to
pending litigation. For more information, please see Note 20—Legal Matters to our consolidated financial statements included in Item 8 of this report. If successful, these efforts could adversely impact consumers’ usage of our products and decrease our overall payments volume and net revenue, lead
to regulatory enforcement and/or litigation that increases our compliance and litigation expenses, and ultimately harm our business.",
     "score": 0.5659
    },
    {
     "source": "sec://0001403161-25-000089/1a#76",
     "title": "V FY2025 10-K · Item 1A",
     "content": "Global economic, political, market, health and social events or conditions may harm our business.\n\nMore than half of our net revenue is earned outside the U.S. In addition, international cross-border transaction revenue represents a significant part of our net revenue and is an
important part of our growth strategy. Our net revenue is dependent on the volume and number of payment transactions made by consumers, governments, and businesses whose spending patterns may be affected by economic, political, market, health and social events or conditions. Adverse macroeconomic
conditions within the U.S. or internationally, including but not limited to recessions, inflation, rising interest rates, increase in tariff rates, high unemployment, currency fluctuations, actual or anticipated large-scale defaults or failures, rising energy prices, a slowdown or disruption of
global trade, trade retaliation, government shutdowns, and reduced consumer, small business, government, and corporate spending, have a direct impact on international commerce. Our business depends on the smooth functioning of international financial systems and the free flow of commerce across
borders. Any restrictions on the activities of multinational businesses, disruptions to global trade, or deterioration in international relations could materially and adversely affect our payments volume, transactions, client relationships, and net revenue. Any events or conditions that impair the
functioning of the financial markets, tighten the credit market, or lead to a downgrade of our current credit rating could increase our future borrowing costs and impair our ability to access the capital and credit markets on favorable terms, which could affect our liquidity and capital resources,
or significantly increase our cost of capital. Furthermore, in efforts to deal with adverse macroeconomic conditions, governments may introduce new or additional initiatives or requests to reduce or eliminate payment fees or other costs. In an overall soft global economy, such pricing measures could
result in additional financial pressures on our business.",
     "score": 0.601
    },
    {
     "source": "sec://0001403161-25-000089/1a#81",
     "title": "V FY2025 10-K · Item 1A · Technology and Cybersecurity Risks",
     "content": "### Technology and Cybersecurity Risks\n\nFailure to anticipate, adapt to, or keep pace with, new technologies in the payments industry could harm our business and impact future growth.\n\nThe global payments industry is undergoing significant and rapid technological change,
including increased proliferation of mobile and other proximity and in-app payment technologies, ecommerce, tokenization, cryptocurrencies, distributed ledger and blockchain technologies, cloud-based encryption and authorization, and new authentication technologies such as biometrics, FIDO 2.0, 3D
Secure 2.0 and dynamic cardholder verification values or dCVV2. As a result, we expect new services and technologies to continue to emerge and evolve. For example, GenAI and agentic commerce solutions have emerged as an opportunity for Visa, its clients, suppliers, sellers and partners to innovate
more quickly and better serve consumers. Rapid adoption and novel uses of GenAI and agentic commerce across the marketplace may also introduce unique and unpredictable security risks to our systems, information, and the payments ecosystem. In addition to our own initiatives and innovations, we work
closely with third parties, including potential competitors, for the development of, and access to, new technologies. It is difficult, however, to predict which technological developments or innovations will become widely adopted and how those technologies may be regulated. Moreover, some of the new
technologies could be subject to intellectual property-related lawsuits or claims, potentially impacting our development efforts and/or requiring us to obtain licenses, implement design changes or discontinue our use. If we or our partners fail to adapt and keep pace with new technologies in the
payments space in a timely manner, it could harm our ability to compete, decrease the value of our products and services to our clients, impact our intellectual property or licensing rights, harm our business and impact our future growth.\n\nA disruption, failure or breach of our networks or
systems, including as a result of cyber incidents or attacks, could harm our business.",
     "score": 0.5407,
     "subsection": "Technology and Cybersecurity Risks"
    },
    {
     "source": "sec://0001403161-25-000089/1a#83",
     "title": "V FY2025 10-K · Item 1A",
     "content": "Our visibility and role in the global payments industry also puts our company at a greater risk of being targeted by hackers. In the normal course of our business, we have been the target of malicious cyber activity. We have been, and may continue to be, impacted by attacks and data
security breaches of financial institutions, sellers, and\n\n32\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)\n\nthird-party service providers. We are also aware of instances where governments have directed or sponsored attacks against some of
our financial institution clients, and other instances where sellers and issuers have encountered substantial data security breaches affecting their customers, some of whom were Visa account holders. Given the increase in payments through ecommerce, social media and mobile channels, we continue to
see increased cyber and payment fraud activity, as cybercriminals attempt phishing and social engineering scams, distributed denial of service attacks and other disruptive actions.\n\nThe security measures and procedures we, our financial institution and seller clients, other sellers and third-party
service providers in the payments ecosystem have in place to protect sensitive consumer data and other information may not be implemented effectively, may differ in scope and complexity across different ecosystem participants, or may not be successful or sufficient to counter all data security
breaches, cyber incidents and attacks or system failures. In some cases, the mitigation efforts may be dependent on third parties who may not follow the required contractual standards, who may not be able to timely patch vulnerabilities or fix security defects, or whose hardware, software or network
services may be subject to error, defect, delay, outage or lack appropriate security measures to prevent breaches or data exfiltration incidents. Cyber incidents and attacks can have cascading impacts that unfold with increasing speed across our internal networks and systems and those of our
partners and clients.",
     "score": 0.5692
    }
   ]
  }
 ]
}

[tool 2] finnhub_company_basic_financials {"ticker": "V"}
{
 "ticker": "V",
 "fiftyTwoWeekHigh": 414.6,
 "fiftyTwoWeekLow": 293.89,
 "peTTM": 33.5031,
 "forwardPE": 24.15752,
 "psTTM": 17.0136,
 "pb": 18.3758,
 "marketCap": 756901,
 "enterpriseValue": 768400,
 "beta": 0.8057082,
 "epsTTM": 11.752600000000001,
 "roeTTM": 61.260000000000005,
 "roaTTM": 23.41,
 "grossMarginTTM": 80.18,
 "netProfitMarginTTM": 50.78,
 "operatingMarginTTM": 60.68,
 "currentRatio": 0.9852,
 "quickRatio": 0.9105,
 "debtToEquity": 0.6782,
 "dividendYield": 0.81793,
 "revenueGrowthTTMYoy": 14.39,
 "epsGrowthTTMYoy": 14.72,
 "tenDayAvgVolume": 6.56901
}
----- END EVIDENCE F0071 -----

----- BEGIN ANSWER F0071 -----
**核心原因：Visa 更像「全球支付基礎設施與收費網路」，而不是靠資產負債表放款賺利差的銀行。**因此，它通常較少直接承擔借款人違約、壞帳與流動性錯配風險，但並不代表風險較低，只是風險類型不同。

以 Visa FY2025 10-K（截至 2025-09-30）來看，主要有幾個原因：

1. **不直接放款，也不承擔持卡人的信用風險**  
   Visa 明確表示自己不是金融機構，不發卡、不向持卡人提供信用，也不設定持卡人的利率與費用；這些活動所產生的信用風險也不是由 Visa 承擔。[1]  
   換言之，持卡人欠款、信用卡循環利息或貸款損失，主要落在發卡銀行，而不是 Visa。

2. **收入主要跟支付交易量連動，而非依賴單一批貸款資產**  
   Visa 的收入包括服務、資料處理、國際交易及其他收入，主要根據交易類型與支付量收費。[2] FY2025 Visa 處理了約 2580 億筆交易，總支付及現金交易量約 17 兆美元。[3]  
   只要經濟活動、消費和商業支付長期成長，Visa 就能從大量交易中收取小額費用；它不必像放款銀行一樣，先把大量資金借出去，再承擔本金收不回來的風險。

3. **商業模式相對「輕資產」且具規模效應**  
   Visa 提供的是授權、清算、結算及風險管理等網路服務，連接消費者、商戶、發卡行與收單行。FY2025 年，Visa 網路覆蓋超過 200 個國家和地區，連接近 14,500 家金融機構與超過 1.75 億個商戶地點。[3]  
   網路一旦形成規模，每增加一筆交易，通常不需要同比例增加一筆貸款資本，因此收入成長可能比傳統資產負債表型金融業更有營運槓桿。

4. **收入來源和交易場景較分散**  
   Visa 的網路涵蓋信用卡、簽帳金融卡、預付卡，以及消費支付、商業支付、跨境支付和匯款等場景。這種多方參與的網路，並非依賴少數大型借款人或單一產業的貸款組合。這是市場把 Visa 視為「收過路費」型公司的重要原因。

不過，**Visa 不是沒有風險，而是風險從「信用週期」轉向「支付量、監管、科技與網路營運」**：

- 經濟衰退、失業上升或消費下滑，會直接減少 Visa 的支付量和收入。[4]
- 交換費、支付路由、反壟斷及跨境支付等監管變化，可能壓低交易量或收入。[5]
- 網路中斷、資安攻擊、支付詐欺或第三方服務商故障，可能損害 Visa 的商譽與營運。[6]
- Visa 也面臨 Mastercard、銀行自有即時支付系統、數位錢包、BNPL 和政府支付網路的競爭。[7]

**所以更精確的說法是：**Visa 通常比傳統放款銀行更能避免「貸款本金損失與信用週期」風險，並享有全球支付網路的規模與網路效應；但它更依賴消費與商業交易持續成長，且承擔監管、競爭、資安和系統性營運風險。它是「信用風險較低的支付平台」，不是「所有風險都較低的金融公司」。

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt
----- END ANSWER F0071 -----

===== ITEM F0072 =====

QUESTION:
現在看迪士尼跟 Netflix，哪一邊的市場期待比較沒那麼滿？

----- BEGIN EVIDENCE F0072 -----
[tool 0] finnhub_stock_quote {"ticker": "NFLX"}
{
 "ticker": "NFLX",
 "currentPrice": 62.91,
 "open": 63.535,
 "previousClose": 63.9,
 "change": -0.99,
 "percentChange": -1.5493,
 "dayHigh": 63.879999999999995,
 "dayLow": 62.79
}

[tool 1] finnhub_stock_quote {"ticker": "DIS"}
{
 "ticker": "DIS",
 "currentPrice": 110.07,
 "open": 110.38,
 "previousClose": 110.4,
 "change": -0.33,
 "percentChange": -0.2989,
 "dayHigh": 110.38,
 "dayLow": 109.425
}

[tool 2] finnhub_company_basic_financials {"ticker": "NFLX"}
{
 "ticker": "NFLX",
 "fiftyTwoWeekHigh": 116.73,
 "fiftyTwoWeekLow": 64.1,
 "peTTM": 17.7735,
 "forwardPE": 19.21432,
 "psTTM": 5.2771,
 "pb": 9.8929,
 "marketCap": 262455.84,
 "enterpriseValue": 269393.959,
 "beta": 1.6119956,
 "epsTTM": 3.4608,
 "roeTTM": 50.41,
 "roaTTM": 25.27,
 "grossMarginTTM": 50.68,
 "netProfitMarginTTM": 29.69,
 "operatingMarginTTM": 36.93,
 "currentRatio": 1.0749,
 "quickRatio": 1.0267,
 "debtToEquity": 0.5167,
 "revenueGrowthTTMYoy": 14.65,
 "epsGrowthTTMYoy": 44.57,
 "tenDayAvgVolume": 47.55715
}

[tool 3] finnhub_company_basic_financials {"ticker": "DIS"}
{
 "ticker": "DIS",
 "fiftyTwoWeekHigh": 117.09,
 "fiftyTwoWeekLow": 92.19,
 "peTTM": 22.1799,
 "forwardPE": 13.90736,
 "psTTM": 1.9294,
 "pb": 1.5566,
 "marketCap": 190747.1,
 "enterpriseValue": 231603.1,
 "beta": 1.4469498,
 "epsTTM": 4.8475,
 "roeTTM": 7.870000000000001,
 "roaTTM": 4.25,
 "grossMarginTTM": 37.6,
 "netProfitMarginTTM": 8.7,
 "operatingMarginTTM": 13.66,
 "currentRatio": 0.7091,
 "quickRatio": 0.6498,
 "debtToEquity": 0.4184,
 "revenueGrowthTTMYoy": 4.58,
 "epsGrowthTTMYoy": -24,
 "tenDayAvgVolume": 7.92814
}

[tool 4] tavily_financial_search {"query": "NFLX Netflix recent analyst expectations valuation earnings outlook", "ticker": "NFLX"}
{
 "query": "NFLX NFLX Netflix recent analyst expectations valuation earnings outlook",
 "results": [
  {
   "title": "Netflix delivered a third-quarter earnings miss. Here’s how analysts reacted",
   "url": "https://www.cnbc.com/2025/10/22/netflix-delivered-a-third-quarter-earnings-miss-heres-how-analysts-reacted.html",
   "content": "NFLX did not provide a 2026 outlook, unlike in 3Q24 for 2025, which the company attributed to the unique circumstances of removing subscriber disclosure beginning in 2025. However, this does not appear to signal any noticeable change in underlying fundamentals as advertising is
expected to more than double in 2025, engagement growth picked up in 3Q and the pricing environment is constructive on the heels of several price increases from competitors.\" UBS keeps buy rating, lifts price forecast to [...] JPMorgan reiterates neutral rating, lowers price objective to $1,275
from $1,300 JPMorgan's forecast corresponds to upside of around 3%. \"NFLX 3Q results and 4Q outlook were solid overall, but did not include as much upside as recent quarters. … We believe the bigger focus on numbers is the lack of revenue upside in the back half. … The other key focus area coming
off the call is that NFLX seemed to keep the door open to M & A. NFLX has historically been more builder than buyer, and has never [...] and has never made a significant acquisition. But the media landscape is evolving, and NFLX indicated that selective M & A would have to grow its opportunity set,
strengthen its IP & entertainment offering, & accelerate its strategy.\" Citi keeps neutral rating and $1,280 price forecast Citi's target calls for 3% upside going forward. \"The firm raised its 2025 revenue guidance and modestly lowered margin guidance due to the recognition of an expense in
Brazil that was disputed by Netflix. Given",
   "published_date": null
  },
  {
   "title": "Wells Fargo downgrades Netflix on higher content investment and decelerating revenue",
   "url": "https://www.cnbc.com/2026/03/09/wells-fargo-downgrades-netflix-on-higher-content-investment-and-decelerating-revenue.html",
   "content": "period of higher content investment. \"We think competition is keeping investment elevated, and as a result, we expect NFLX to trade at slight discount to its [historical] P/E valuation as the market looks for clues of a verifiable engagement accel,\" he wrote. NFLX 1Y mountain NFLX
1Y chart Cahall expects Netflix to rebound from its saga with Warner Bros. Discovery, with Netflix ultimately choosing to walk away from the deal , by aiming to accelerate its engagement with more content. \"Now that [...] on both its annual rate of content growth and the forms of allocation,
especially putting more focus on sports. The analyst also suggested that going forward, Netflix concentrate on creating a hands-on development process such as Warner Bros. Discovery's HBO. \"If there's a lesson for NFLX, it's that it should build an internal HBO focused only on quality originals ( &
/or look for small indie studios w/ that kind of DNA),\" Cahall said. Shares of Netflix have added 6% this year and 11% over the [...] content. \"Now that the WBD saga has ended, we think the scars on NFLX's stock can begin to heal. Investors had wondered if mgmt's interest was sparked by a slowing
core biz, with fears exacerbated by 2h'25 engagement stats,\" he wrote. \"We think WBD was NFLX's opportunistic Plan B, and now it's back to Plan A: invest for growth.\" In a recent press release, Netflix also noted that it plans to invest around $20 billion on content this year. Cahall expects
Netflix to be more aggressive on both its",
   "published_date": null
  },
  {
   "title": "Netflix Tops Wall Street’s Lofty Expectations, Raises Forecast (NFLX) - Bloomberg",
   "url": "https://www.bloomberg.com/news/articles/2025-07-17/netflix-tops-wall-street-s-lofty-expectations-raises-forecast",
   "content": "The owner of the world’s most popular paid streaming service on Thursday reported revenue grew to $11.1 billion and earnings jumped to $7.19 a share. The company also raised its forecast for full-year sales and profit margins. [...] Entertainment\n\n# Netflix Tops Wall Street’s Lofty
Estimates, Raises Forecast\n\nThis article is for subscribers only.\n\n## Takeaways by Bloomberg AI\n\nNetflix Inc. beat expectations for second-quarter results and continues to trounce rival media companies, yet the shares slipped on Friday as investors took a pause after the stock has nearly
doubled over the past year.",
   "published_date": null
  },
  {
   "title": "Netflix slides as weak outlook deepens worries on viewership, revenue growth",
   "url": "https://www.reuters.com/business/media-telecom/netflix-slides-weak-profit-ad-outlook-intensify-investor-anxiety-2026-10-21",
   "content": "Analysts expect most of the challenges, including slowing engagement and revenue growth, to be addressable.\n\nBofA Global Research analysts said the leadership change and layoffs were \"a signal that management is focused ⁠on improving ​content output and creative hit
rates.\"\n\nNetflix trades at nearly 18.28 ​times expected earnings over the next 12 months, compared with 14.76 times for Walt Disney (DIS.N), opens new tab and 6.26 times for Comcast (CMCSA.O), opens new tab. [...] Skip to main content\n\nExclusive news, data and analytics for financial market
professionals Learn more about Refinitiv\n\n - Netflix (NFLX.O), opens new tab shares dropped 6% in premarket trading on Wednesday, ‌after the company's tepid profit and advertising outlook deepened investor concerns about slowing viewership and revenue growth amid stiff competition in the streaming
industry. [...] Netflix, ​which has stopped sharing subscriber numbers since 2025, reported an 11.8% rise in third-quarter revenue to $12.87 billion, in line with Wall Street forecasts but the slowest increase in nearly three years.\n\nThe company also reduced its advertising forecast for 2026 to
roughly $2.7 ​billion, down from about $3 billion.\n\n\"Growth has clearly slowed at Netflix,\" Evercore ISI analysts said in a note.",
   "published_date": null
  },
  {
   "title": "Wall Street ends lower on mixed earnings, revived US-China trade tensions | Reuters",
   "url": "https://www.reuters.com/world/africa/wall-st-futures-struggle-netflix-results-put-investors-guard-2025-10-22",
   "content": "On that front, Netflix (NFLX.O) slid 10.1% after the streaming company missed quarterly profit expectations, raising concerns about stretched valuation.\n\nTexas Instruments (TXN.O) posted lower-than-expected revenue and profit forecasts, dragging the chipmaker's shares down
5.6%.\n\nThe Philadelphia Semiconductor Index (.SOX), which has outperformed the broader market this year driven by artificial intelligence fervor, tumbled 2.4%. The chip index touched a record high on Monday. [...] NEW YORK, Oct 22 (Reuters) - Wall Street closed lower on Wednesday as a wave of
mixed earnings, including Netflix's disappointing results, dampened risk sentiment as investors assessed reports that the Trump administration is considering curbs on exports to China made with U.S. software.\n\nAll three major U.S. stock indexes extended their losses after the report, with weakness
in tech (.SPLRCT) and communication services stocks (.SPLRCL) weighing the Nasdaq down the most.\n\nSign up here. [...] \"You earn high valuations by achieving those expectations, and in general companies have so far been meeting or exceeding those expectations,\" Hainlin said. \"And those that
haven’t are not being rewarded by investors with patience.\"\n\nThe Dow Jones Industrial Average (.DJI) fell 334.33 points, or 0.71%, to 46,590.41, the S&P 500 (.SPX) lost 35.95 points, or 0.53%, to 6,699.40 and the Nasdaq Composite (.IXIC) lost 213.27 points, or 0.93%, to 22,740.40.",
   "published_date": null
  }
 ]
}

[tool 5] tavily_financial_search {"query": "DIS Disney recent analyst expectations valuation earnings outlook", "ticker": "DIS"}
{
 "query": "DIS DIS Disney recent analyst expectations valuation earnings outlook",
 "results": [
  {
   "title": "Disney (DIS) earnings Q1 2026",
   "url": "https://www.cnbc.com/2026/02/02/disney-dis-earnings-q1-26.html",
   "content": "In Disney's outlook for fiscal 2026 the company said it's on track to repurchase $7 billion in stock. It also expects double-digit growth in adjusted earnings per share and $19 billion in cash provided by operations.\n\nFor its fiscal second quarter, Disney said it projects its
streaming unit – which consists of Disney+ and Hulu – to notch about $500 million in operating income, or an increase of roughly $200 million compared with the same period last year. [...] Its experiences unit, however, is expected to see \"modest\" growth in operating income due to international
visitation headwinds at domestic parks, as well as prelaunch costs for a new Disney Cruise line and preopening costs for \"World of Frozen\" at Disneyland Paris. [...] Revenue for the sports segment was up 1% to $4.91 billion, while operating income decreased 23% to $191 million.\n\nThe sports
segment was weighed down by an increase in programming and production costs for new sports rights agreements, as well as the decline in subscription and affiliate fees due to the loss of traditional bundle subscribers. Advertising revenue grew, however, due to higher rates.",
   "published_date": null
  },
  {
   "title": "Disney (DIS) earnings Q1 2026",
   "url": "https://www.cnbc.com/amp/2026/02/02/disney-dis-earnings-q1-26.html",
   "content": "In Disney's outlook for fiscal 2026 the company said it's on track to repurchase $7 billion in stock. It also expects double-digit growth in adjusted earnings per share and $19 billion in cash provided by operations.\n\nFor its fiscal second quarter, Disney said it projects its
streaming unit – which consists of Disney+ and Hulu – to notch about $500 million in operating income, or an increase of roughly $200 million compared with the same period last year. [...] Its experiences unit, however, is expected to see \"modest\" growth in operating income due to international
visitation headwinds at domestic parks, as well as prelaunch costs for a new Disney Cruise line and preopening costs for \"World of Frozen\" at Disneyland Paris. [...] Revenue for the sports segment was up 1% to $4.91 billion, while operating income decreased 23% to $191 million.\n\nThe sports
segment was weighed down by an increase in programming and production costs for new sports rights agreements, as well as the decline in subscription and affiliate fees due to the loss of traditional bundle subscribers. Advertising revenue grew, however, due to higher rates.",
   "published_date": null
  },
  {
   "title": "Disney (DIS) earnings Q4 2022",
   "url": "https://www.cnbc.com/2022/11/08/disney-dis-earnings-q4-2022.html",
   "content": "Still, Wall Street had slightly higher hopes for the division: Analysts were expecting revenue of $7.5 billion, according to StreetAccount.\n\nOperating income for the division rose more than 66% to $1.5 billion as spending increased at its domestic and international parks and
consumers booked voyages on its new cruise ship, the Disney Wish. The parks unit, specifically, brought in $815 million in operating income, well shy of the $919 million expected by StreetAccount. [...] Fourth-quarter revenue in the media and entertainment division fell 3% year over year to $12.7
billion during the year-earlier period, as the company's direct-to-consumer and theatrical businesses struggled. Analysts had expected segment revenue of $13.9 billion, according to StreetAccount estimates.\n\nThe company also posted lower content sales because it had fewer theatrical films on the
calendar, and therefore fewer films to place into the home entertainment market.",
   "published_date": null
  },
  {
   "title": "Disney (DIS) earnings Q4 2022",
   "url": "https://www.cnbc.com/amp/2022/11/08/disney-dis-earnings-q4-2022.html",
   "content": "Still, Wall Street had slightly higher hopes for the division: Analysts were expecting revenue of $7.5 billion, according to StreetAccount.\n\nOperating income for the division rose more than 66% to $1.5 billion as spending increased at its domestic and international parks and
consumers booked voyages on its new cruise ship, the Disney Wish. The parks unit, specifically, brought in $815 million in operating income, well shy of the $919 million expected by StreetAccount. [...] Fourth-quarter revenue in the media and entertainment division fell 3% year over year to $12.7
billion during the year-earlier period, as the company's direct-to-consumer and theatrical businesses struggled. Analysts had expected segment revenue of $13.9 billion, according to StreetAccount estimates.\n\nThe company also posted lower content sales because it had fewer theatrical films on the
calendar, and therefore fewer films to place into the home entertainment market.",
   "published_date": null
  },
  {
   "title": "Disney (DIS) earnings Q2 2026",
   "url": "https://www.cnbc.com/2026/05/06/disney-dis-earnings-q2-2026.html",
   "content": "Disney provided additional details on its fiscal 2026 guidance, which includes full-year adjusted earnings growth of about 12%. The company also said it was targeting at least $8 billion in share repurchases for the fiscal year, up from the previously announced $7 billion. In
addition, Disney expects third-quarter total segment incoming of roughly $5.3 billion.\n\nFor its fiscal 2027 year, Disney said it expects double-digit growth in adjusted earnings. [...] Disney's entertainment segment – which includes its traditional TV, streaming and theatrical releases – saw
revenue increase 10% to $11.72 billion compared with the same period last year. Entertainment revenue got a 4% boost from the closed Fubo deal, Disney said.\n\nSubscription and affiliate fees climbed 14% to $7.8 billion, boosted by recent streaming price hikes. Advertising revenue was also up,
jumping 5%, in part due to higher impressions linked to streaming. [...] On Wednesday's earnings call with investors, Johnston said the company isn't anticipating any changes to adjusted earnings growth expectations for fiscal 2026 or 2027 in light of gas prices or consumer spending.",
   "published_date": null
  }
 ]
}
----- END EVIDENCE F0072 -----

----- BEGIN ANSWER F0072 -----
**結論：若問「市場期待比較沒那麼滿」，我會偏向迪士尼（DIS）；Netflix（NFLX）的基本面更強，但估值與成長期待也更高。**

- **估值角度：DIS 明顯較便宜。** Finnhub 顯示，DIS 的本益比約 **22.2 倍、預估本益比 13.9 倍**；NFLX 則約 **17.8 倍、預估本益比 19.2 倍**。更重要的是，NFLX 的本益比雖不一定高於 DIS，但其市銷率約 **5.3 倍**，遠高於 DIS 的 **1.9 倍**，市場對 Netflix 的營收品質與長期成長給予更高溢價。

- **基本面角度：Netflix 的市場期待較高。** NFLX 最近 TTM 營收年增約 **14.7%**、EPS 年增約 **44.6%**，淨利率約 **29.7%**；DIS 營收年增約 **4.6%**，EPS 反而年減 **24%**，淨利率約 **8.7%**。這表示 Netflix 已經交出較強的成長與獲利數字，因此股價更容易被要求「持續超預期」。

- **近期新聞也反映 Netflix 的門檻較高。** Bloomberg 報導 Netflix 即使營收與獲利優於預期、並上調全年展望，股價仍因先前大幅上漲而出現獲利了結壓力；另一則報導則指出，分析師開始關注內容投資增加與營收成長放緩。[1][2]

- **迪士尼則有較多「修復型」期待。** 近期公司展望包括 FY2026 調整後 EPS 雙位數成長、串流部門獲利改善與大額庫藏股；但 ESPN／傳統電視、主題樂園國際客流，以及串流轉型仍有不確定性。[3] 因此市場對 DIS 的期待比較像「持續改善、逐步修復」，而不是 Netflix 那種「高成長必須延續」。

**我的排序：**

1. **市場期待較不滿：DIS**
2. **基本面較強但期待較高：NFLX**
3. **若重視預期差與估值安全邊際：DIS 較有利**
4. **若重視成長品質與獲利動能：NFLX 較強，但失望風險也較集中**

不過要注意：Finnhub 的即時資料顯示 DIS 約 **110.07 美元**、NFLX 約 **62.91 美元**；NFLX 的股價資料可能涉及拆股或資料口徑差異，因此不宜直接用兩者的股價高低比較市場期待。  

[1]: https://www.bloomberg.com/news/articles/2025-07-17/netflix-tops-wall-street-s-lofty-expectations-raises-forecast "Netflix Tops Wall Street’s Lofty Expectations, Raises Forecast (NFLX)"
[2]: https://www.cnbc.com/2026/03/09/wells-fargo-downgrades-netflix-on-higher-content-investment-and-decelerating-revenue.html "Wells Fargo downgrades Netflix on higher content investment and decelerating revenue"
[3]: https://www.cnbc.com/2026/02/02/disney-dis-earnings-q1-26.html "Disney (DIS) earnings Q1 2026"
----- END ANSWER F0072 -----
