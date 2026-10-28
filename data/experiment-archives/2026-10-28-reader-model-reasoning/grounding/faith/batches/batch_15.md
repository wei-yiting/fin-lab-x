# Faithfulness batch 15 — 4 items

===== ITEM F0085 =====

QUESTION:
波克夏現在的財務體質看起來算保守嗎？

----- BEGIN EVIDENCE F0085 -----
[tool 0] finnhub_company_basic_financials {"ticker": "BRK.B"}
{
 "ticker": "BRK.B",
 "fiftyTwoWeekHigh": 824765.2,
 "fiftyTwoWeekLow": 698000,
 "peTTM": 13.6493,
 "forwardPE": 24.52946517808715,
 "psTTM": 3.0432,
 "pb": 1.4419,
 "marketCap": 1170675,
 "enterpriseValue": 1258665,
 "beta": 0.08230131,
 "epsTTM": 59668.8094,
 "roeTTM": 11.87,
 "roaTTM": 6.909999999999999,
 "grossMarginTTM": 24.61,
 "netProfitMarginTTM": 22.3,
 "operatingMarginTTM": 13.87,
 "currentRatio": 1.228,
 "quickRatio": 0.9569,
 "debtToEquity": 0.1719,
 "revenueGrowthTTMYoy": 3.93,
 "epsGrowthTTMYoy": 36.33,
 "tenDayAvgVolume": 0.00023
}

[tool 1] sec_filing_search {"query": "financial condition liquidity cash and cash equivalents debt leverage insurance float capital allocation conservative balance sheet", "ticker": "BRK.B", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "BRK.B",
   "fiscal_year": 2025,
   "item": "Item 7",
   "prelude": "Excerpts from BRK.B FY2025 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001193125-26-083899/7#118",
     "title": "BRK.B FY2025 10-K · Item 7 · Insurance—Investment Income",
     "content": "### Insurance—Investment Income\n\nInvested assets of our insurance businesses derive from shareholder capital and net liabilities assumed under insurance contracts or “float.” The major components of float are unpaid losses and loss adjustment expenses, including liabilities under
retroactive reinsurance contracts, life, annuity and health benefit liabilities, unearned premiums and certain other liabilities, which are reduced by insurance premiums receivable, reinsurance receivables, deferred charges assumed under retroactive reinsurance contracts and deferred policy
acquisition costs. The effect of discount rate changes on long-duration insurance contracts, which are recorded in accumulated other comprehensive income, are excluded from float, as such amounts are not included in earnings in the Consolidated Statements of Earnings.\n\nFloat was approximately $176
billion at December 31, 2025, $171 billion at December 31, 2024 and $169 billion at December 31, 2023. The cost of float is measured as the ratio of pre-tax underwriting earnings to float balances. Our combined insurance operations generated pre-tax underwriting gains in each of the three years
ending December 31, 2025 and the average cost of float was negative in each year.\n\nA summary of cash and investments held in our insurance businesses follows (in millions).\n\n\n\n\n\n|  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n|  | December 31, | | | | | |  |\n|
| 2025 | |  |  | 2024 | |  |\n| Cash, cash equivalents and U.S. Treasury Bills | $ | 212,651 |  |  | $ | 212,591 |  |\n| Equity securities |  | 294,144 |  |  |  | 263,366 |  |\n| Fixed maturity securities |  | 17,466 |  |  |  | 15,137 |  |\n| Other, includes loans to affiliates |  | 4,702 |  |  |  |
5,980 |  |\n|  | $ | 528,963 |  |  | $ | 497,074 |  |\n\n\n\n\nFixed maturity investments as of December 31, 2025 were as follows (in millions).",
     "score": 0.526,
     "subsection": "Insurance—Investment Income"
    },
    {
     "source": "sec://0001193125-26-083899/7#161",
     "title": "BRK.B FY2025 10-K · Item 7 · Financial Condition",
     "content": "### Financial Condition\n\nOur Consolidated Balance Sheet continues to reflect significant liquidity and a very strong capital base. Berkshire’s shareholders’ equity at December 31, 2025 was $717.4 billion, an increase of $68.1 billion since December 31, 2024. Net earnings
attributable to Berkshire shareholders were $67.0 billion for 2025 and included after-tax investment gains of approximately $30.7 billion and after-tax impairment losses of $8.3 billion on our equity method investments. Investment gains and losses from changes in the market prices of our investments
in equity securities usually produce significant volatility in our earnings.\n\nBerkshire’s common stock repurchase program permits Berkshire to repurchase its Class A and Class B shares at prices below Berkshire’s intrinsic value, as conservatively determined by Berkshire’s Chief Executive Officer
after consultation with the Chairman of the Board. We are not committed to a minimum or subject to a maximum repurchase amount. We will not repurchase our stock if it reduces our consolidated cash, cash equivalents and U.S. Treasury Bills holdings to below $30 billion. Financial strength and
redundant liquidity will always be of paramount importance at Berkshire. There were no share repurchases in 2025.\n\nAt December 31, 2025, our insurance and other businesses held cash, cash equivalents and U.S. Treasury Bills (net of payables for unsettled purchases) of $369.0 billion. Investments
in equity and fixed maturity securities, excluding our equity method investments, were $315.6 billion. During 2025, we paid $16.9 billion to acquire equity securities and we received $30.7 billion from sales of equity securities.",
     "score": 0.5437,
     "subsection": "Financial Condition"
    },
    {
     "source": "sec://0001193125-26-083899/7#182",
     "title": "BRK.B FY2025 10-K · Item 7",
     "content": "| Liabilities: |  |  | |  |  |  | |  |  |  | |  |  |  | |  |  |  | |  |\n| Notes payable and other borrowings: |  |  | |  |  |  | |  |  |  | |  |  |  | |  |  |  | |  |\n| Insurance and other |  |  | 40,924 |  |  |  | 43,981 |  |  |  | 38,285 |  |  |  | 35,994 |  |  |  | 33,991 |
|\n| Railroad, utilities and energy |  |  | 76,803 |  |  |  | 84,025 |  |  |  | 68,744 |  |  |  | 62,816 |  |  |  | 57,751 |  |\n|  |  |  | |  |  |  | |  |  |  | |  |  |  | |  |  |  | |  |\n| December 31, 2024 |  |  | |  |  |  | |  |  |  | |  |  |  | |  |  |  | |  |\n| Assets: |  |  | |  |  |  | |
|  |  | |  |  |  | |  |  |  | |  |\n| Investments in fixed maturity securities |  | $ | 15,364 |  |  | $ | 15,503 |  |  | $ | 15,220 |  |  | $ | 15,086 |  |  | $ | 14,958 |  |\n| Investments in equity securities* |  |  | 8,429 |  |  |  | 8,743 |  |  |  | 8,142 |  |  |  | 7,864 |  |  |  | 7,597 |
|",
     "score": 0.4576
    },
    {
     "source": "sec://0001193125-26-083899/7#183",
     "title": "BRK.B FY2025 10-K · Item 7",
     "content": "| Loans and finance receivables |  |  | 27,579 |  |  |  | 28,774 |  |  |  | 26,476 |  |  |  | 25,455 |  |  |  | 24,508 |  |\n| Liabilities: |  |  | |  |  |  | |  |  |  | |  |  |  | |  |  |  | |  |\n| Notes payable and other borrowings: |  |  | |  |  |  | |  |  |  | |  |  |  | |  |
|  | |  |\n| Insurance and other |  |  | 40,181 |  |  |  | 43,345 |  |  |  | 37,467 |  |  |  | 35,122 |  |  |  | 33,082 |  |\n| Railroad, utilities and energy |  |  | 72,506 |  |  |  | 80,339 |  |  |  | 65,916 |  |  |  | 60,332 |  |  |  | 55,565 |  |",
     "score": 0.4407
    }
   ]
  },
  {
   "ticker": "BRK.B",
   "fiscal_year": 2025,
   "item": "Item 1",
   "prelude": "Excerpts from BRK.B FY2025 10-K, Item 1 (Business) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001193125-26-083899/1#12",
     "title": "BRK.B FY2025 10-K · Item 1",
     "content": "Investments of insurance businesses—Berkshire’s insurance subsidiaries hold significant levels of invested assets. Investments include a very large portfolio of publicly traded equity securities, which are unusually concentrated in relatively few companies, as well as in short-term
investments and fixed maturity securities. Generally, there are no target allocations by investment type or attempts to match investment asset and insurance liability durations. However, investment portfolios have historically included a much greater proportion of equity securities than is customary
in the insurance industry.\n\nInvested assets derive from shareholder capital as well as funds provided from policyholders through insurance and reinsurance businesses (“float”). Float represents the approximate net policyholder funds generated through underwriting activities that are held for
investment. The major components of float are unpaid losses and loss adjustment expenses, life, annuity and health benefit insurance liabilities (excluding the effects of discount rate changes that are recorded in accumulated other comprehensive income), unearned insurance premiums and other
insurance policyholder liabilities less premium and reinsurance receivables, deferred policy acquisition costs and deferred charges on assumed retroactive reinsurance contracts. On a consolidated basis, float has increased from approximately $138 billion at the end of 2020 to approximately $176
billion at the end of 2025. The cost of float can be measured as the net pre-tax underwriting earnings (or loss) as a percentage of the average float balance.",
     "score": 0.4967
    }
   ]
  },
  {
   "ticker": "BRK.B",
   "fiscal_year": 2025,
   "item": "Item 8",
   "prelude": "Excerpts from BRK.B FY2025 10-K, Item 8 (Financial Statements and Supplementary Data) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001193125-26-083899/8#201",
     "title": "BRK.B FY2025 10-K · Item 8",
     "content": "|  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n|  | December 31, | | | | | |  |\n|  | 2025 | |  |  | 2024 | |  |\n| Assets: |  | |  |  |  | |  |\n| Insurance and Other: |  | |  |  |  | |  |\n| Cash and cash equivalents* | $ | 47,719 |  |  | $ | 44,333
|  |\n| Short-term investments in U.S. Treasury Bills** |  | 321,434 |  |  |  | 286,472 |  |\n| Investments in fixed maturity securities |  | 17,816 |  |  |  | 15,364 |  |\n| Investments in equity securities |  | 297,778 |  |  |  | 271,588 |  |\n| Equity method investments |  | 19,978 |  |  |  |
31,134 |  |\n| Loans and finance receivables |  | 29,836 |  |  |  | 27,798 |  |\n| Other receivables |  | 44,331 |  |  |  | 43,887 |  |\n| Inventories |  | 24,424 |  |  |  | 24,008 |  |\n| Property, plant and equipment |  | 31,885 |  |  |  | 30,071 |  |\n| Equipment held for lease |  | 18,535 |  |
|  | 17,828 |  |\n| Goodwill |  | 55,945 |  |  |  | 56,860 |  |\n| Other intangible assets |  | 33,802 |  |  |  | 34,638 |  |\n| Deferred charges - retroactive reinsurance |  | 8,104 |  |  |  | 8,797 |  |\n| Other |  | 24,413 |  |  |  | 24,994 |  |",
     "score": 0.4802
    },
    {
     "source": "sec://0001193125-26-083899/8#224",
     "title": "BRK.B FY2025 10-K · Item 8",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  |  | Year Ended December 31, | | | | | | | | | |  |\n|  |  | 2025 | |  |  | 2024 | |  |  | 2023 | |  |\n| Cash flows from operating activities: |  |  | |  |
|  | |  |  |  | |  |\n| Net earnings |  | $ | 67,260 |  |  | $ | 89,561 |  |  | $ | 97,147 |  |\n| Adjustments to reconcile net earnings to operating cash flows: |  |  | |  |  |  | |  |  |  | |  |\n| Investment (gains) losses |  |  | (39,078 | ) |  |  | (52,799 | ) |  |  | (74,855 | ) |\n|
Depreciation and amortization |  |  | 13,476 |  |  |  | 12,855 |  |  |  | 12,486 |  |\n| Discount accretion on investments, principally U.S. Treasury Bills |  |  | (11,964 | ) |  |  | (11,349 | ) |  |  | (5,510 | ) |\n| Equity method investment impairment losses |  |  | 10,681 |  |  |  | — |  |  |
| — |  |\n| Other |  |  | 3,239 |  |  |  | (892 | ) |  |  | (513 | ) |\n| Changes in operating assets and liabilities: |  |  | |  |  |  | |  |  |  | |  |\n| Unpaid losses and loss adjustment expenses |  |  | 3,088 |  |  |  | 2,173 |  |  |  | 2,628 |  |",
     "score": 0.443
    },
    {
     "source": "sec://0001193125-26-083899/8#225",
     "title": "BRK.B FY2025 10-K · Item 8",
     "content": "| Unpaid losses and loss adjustment expenses |  |  | 3,088 |  |  |  | 2,173 |  |  |  | 2,628 |  |\n| Deferred charges - retroactive reinsurance |  |  | 693 |  |  |  | 698 |  |  |  | 375 |  |\n| Unearned insurance premiums |  |  | 432 |  |  |  | 376 |  |  |  | 1,854 |  |\n|
Receivables and originated loans |  |  | (2,426 | ) |  |  | 626 |  |  |  | (1,949 | ) |\n| Other assets |  |  | (861 | ) |  |  | (206 | ) |  |  | 98 |  |\n| Other liabilities |  |  | 429 |  |  |  | (2,288 | ) |  |  | 2,570 |  |\n| Income taxes |  |  | 1,000 |  |  |  | (8,163 | ) |  |  | 14,865 |
|\n| Net cash flows from operating activities |  |  | 45,969 |  |  |  | 30,592 |  |  |  | 49,196 |  |\n| Cash flows from investing activities: |  |  | |  |  |  | |  |  |  | |  |\n| Purchases of equity securities |  |  | (16,923 | ) |  |  | (9,237 | ) |  |  | (16,462 | ) |\n| Sales of equity
securities |  |  | 30,686 |  |  |  | 143,359 |  |  |  | 40,631 |  |\n| Purchases of U.S. Treasury Bills and fixed maturity securities |  |  | (586,129 | ) |  |  | (526,842 | ) |  |  | (235,007 | ) |\n| Sales of U.S. Treasury Bills and fixed maturity securities |  |  | 44,769 |  |  |  | 48,462 |  |
|  | 52,302 |  |",
     "score": 0.4796
    },
    {
     "source": "sec://0001193125-26-083899/8#376",
     "title": "BRK.B FY2025 10-K · Item 8",
     "content": "| December 31, 2024 |  |  | |  |  |  | |  |  |  | |  |  |  | |  |  |  | |  |\n| Cash and short-term investments |  | $ | 600 |  |  | $ | 556 |  |  | $ | 44 |  |  | $ | — |  |  | $ | — |  |\n| Equity securities |  |  | 9,757 |  |  |  | 9,036 |  |  |  | 581 |  |  |  | 140 |  |  |  | —
|  |\n| Fixed maturity securities |  |  | 1,747 |  |  |  | 953 |  |  |  | 794 |  |  |  | — |  |  |  | — |  |\n| Investment funds and other |  |  | 2,076 |  |  |  | 385 |  |  |  | 144 |  |  |  | 23 |  |  |  | 1,524 |  |\n|  |  | $ | 14,180 |  |  | $ | 10,930 |  |  | $ | 1,563 |  |  | $ | 163 |  |  |
$ | 1,524 |  |",
     "score": 0.4502
    }
   ]
  },
  {
   "ticker": "BRK.B",
   "fiscal_year": 2025,
   "item": "Item 15",
   "prelude": "Excerpts from BRK.B FY2025 10-K, Item 15 (Exhibits, Financial Statement Schedules) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001193125-26-083899/15#434",
     "title": "BRK.B FY2025 10-K · Item 15 · Balance Sheets",
     "content": "### Balance Sheets\n\n\n\n\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  |  | December 31, | | | | | |  |\n|  |  | 2025 | |  |  | 2024 | |  |\n| Assets: |  |  | |  |  |  | |  |\n| Cash and cash equivalents |  | $ | 14,627 |  |  | $ |
6,337 |  |\n| Short-term investments in U.S. Treasury Bills |  |  | 112,811 |  |  |  | 89,705 |  |\n| Investments in and advances to consolidated subsidiaries |  |  | 604,100 |  |  |  | 568,987 |  |\n| Investment in Kraft Heinz and other assets |  |  | 8,871 |  |  |  | 13,417 |  |\n|  |  | $ |
740,409 |  |  | $ | 678,446 |  |\n| Liabilities and Shareholders’ equity: |  |  | |  |  |  | |  |\n| Payable for purchase of U.S. Treasury Bills and other liabilities |  | $ | 150 |  |  | $ | 6,510 |  |\n| Income taxes, principally deferred |  |  | 178 |  |  |  | 1,477 |  |\n| Notes payable and
other borrowings |  |  | 22,662 |  |  |  | 21,091 |  |\n|  |  |  | 22,990 |  |  |  | 29,078 |  |\n| Berkshire shareholders’ equity |  |  | 717,419 |  |  |  | 649,368 |  |\n|  |  | $ | 740,409 |  |  | $ | 678,446 |  |",
     "score": 0.4443,
     "subsection": "Balance Sheets"
    }
   ]
  }
 ]
}

[tool 2] tavily_financial_search {"query": "Berkshire Hathaway BRK.B recent financial condition cash debt liquidity balance sheet", "ticker": "BRK.B"}
{
 "query": "BRK.B Berkshire Hathaway BRK.B recent financial condition cash debt liquidity balance sheet",
 "results": [
  {
   "title": "Berkshire CEO Greg Abel vows to keep Buffett's culture of disciplined investing in first annual letter",
   "url": "https://www.cnbc.com/2026/02/28/berkshire-ceo-abel-vows-to-keep-buffetts-culture-of-disciplined-investing-in-first-annual-letter.html",
   "content": "\"We maintain a fortress-like balance sheet, ensuring Berkshire's foundation is never compromised,\" he wrote. \"We preserve this financial strength by using debt sparingly and prudently. Our substantial liquidity enables us to meet our obligations even under the most adverse
conditions and to respond swiftly when opportunities arise.\"\n\nOther values he highlighted included a decentralized management model and \"reputation for integrity.\" [...] Berkshire's cash pile stood at $373.3 billion at the end of 2025. Abel described the mountain of cash as strategic dry
powder, which allows the company to act decisively when opportunities surface without jeopardizing resilience. Abel also used the letter to push back on any notion that the sizable cash position signified that Berkshire was retreating from investing.\n\nBut Abel noted he will continue Berkshire's
long-standing resistance to paying a dividend. [...] \"Our approach to cash dividends continues to be that Berkshire will not pay dividends so long as more than one dollar of market value for shareholders is reasonably likely to be created by each dollar of retained earnings,\" Abel wrote, adding
that the board reviews the policy annually.\n\nAbel emphasized that Berkshire applies the same disciplined framework whether it is acquiring an entire business, buying shares of a public company or repurchasing its own stock.",
   "published_date": null
  },
  {
   "title": "Warren Buffett: Cash is necessary 'like oxygen'—but it's 'not a good asset'",
   "url": "https://www.cnbc.com/make-it/2026/03/12/warren-buffett-cash-not-a-good-asset.html",
   "content": "Related Stories\n\nWhen Warren Buffett stepped down as CEO of Berkshire Hathaway at the end of 2025, the company held an enormous stash of cash. Berkshire reported more than $370 billion in cash equivalents on the books at year-end, largely held in Treasury bills. [...] \"Berkshire
shareholders can rest assured that we will forever deploy a substantial majority of their money in equities — mostly American equities although many of these will have international operations of significance,\" Buffett wrote in his 2024 shareholder letter. \"Berkshire will never prefer ownership of
cash-equivalent assets over the ownership of good businesses, whether controlled or only partially owned.\"",
   "published_date": null
  },
  {
   "title": "Morning Session - 2019 Berkshire Hathaway Annual Meeting",
   "url": "https://buffett.cnbc.com/video/2019/05/06/morning-session---2019-berkshire-hathaway-annual-meeting.html",
   "content": "WARREN BUFFETT: There will be a time when  I mean, I probably won't be around then  but there will be a time occasionally, just like in financial markets, when things are happening in the insurance world, and basically, Berkshire will be the only one  virtually the only one 
people turn to.\n\nCHARLIE MUNGER: But in the past, Ajit, talking to you, has added more than $50 billion to the balance sheet at Berkshire, by making these oddball calls. [...] And it's not  current sales can make some difference. Current profit margins can make some difference. Tangible assets,
excess cash, excess debt, all of those things go into making a calculation as to whether they should buy A versus B versus C.\n\nAnd they are absolutely following value principles. They don't necessarily agree with each other or agree with me. But they are very smart. They are totally committed to
Berkshire. And they're very good human beings, on top of it. [...] So, it's a very valuable asset. I don't want to give you a figure on it. But we would not sell it. We certainly wouldn't want to sell it for its float value. And that float is shown on the balance sheet as a liability. So, it's
extraordinary.\n\nAnd it's taken a long time to build. It'd be very, very, very hard for anybody to  I don't think they could build anything like it. It just takes so long.",
   "published_date": null
  },
  {
   "title": "Live Updates: Warren Buffett at Berkshire Hathaway Annual Meeting 2023",
   "url": "https://www.cnbc.com/2023/05/06/berkshire-hathaway-annual-meeting-live-updates.html",
   "content": "\"Those things are all on the balance sheet at zero,\" Nygren said. \"If you aren't making adjustments for that as a value investor, you're unnecessarily restricting your universe.\"\n\nAlthough Oakmark Funds does not own shares of Berkshire Hathaway, Nygren called it an attractive
investment opportunity for many. [...] Profit from insurance underwriting came in at $911 million, up sharply from $167 million a year prior. Insurance investment income also jumped 68% to $1.969 billion from $1.170 billion.\n\nBerkshire's cash hoard also swelled to $130.616 billion from $128
billion in the fourth quarter of 2022.\n\n— Fred Imbert\n\nWarren Buffett's successor Greg Abel will be joining the Oracle of Omaha and Charlie Munger on stage Saturday, answering questions about non-insurance operations. [...] — Sarah Min\n\nBuffett is watching currency in circulation, calling it
\"one of the most interesting figures\" to consider and calling out those who previously said \"cash is trash\" back in 2007 and 2008.\n\n\"The Federal Reserve balance sheet has gone from $800 billion to $2.2 trillion and most of that's in $100 bills overwhelmingly. … I would really like to know
where all of that is,\" he said.",
   "published_date": null
  },
  {
   "title": "Afternoon Session - 2001 Berkshire Hathaway Annual Meeting",
   "url": "https://buffett.cnbc.com/video/2001/04/28/afternoon-session---2001-berkshire-hathaway-annual-meeting.html",
   "content": "Actually, in financial products, what you see on that one line of income on that, and also what you see in the balance sheet items, is a combination of several things. It's General Re Securities, which used to be GRFP, General Re Financial Products. Its  and it's a couple of other
operations.\n\nIt actually had our  it has our  structured settlement business in it, which is quite predictable and a very easy business to understand. [...] And we bought  we publicly announced it. We bought $1,428,000,000 face amount of bonds or bank debt. So we, out of 11 billion of
aggregate debt at Finova, we own $1,428,000,000 face value. And we bought those at prices that looked attractive then and look attractive now. [...] So there's a greater capacity to carry debt as earning power increases and assets held increases. I dont  I can't give you a useful answer, in
terms of the world as a whole.\n\nBut I constantly give advice to young people, and those are the only people I talk to, aside from our shareholder group: just don't start out behind the eight ball.",
   "published_date": null
  }
 ]
}
----- END EVIDENCE F0085 -----

----- BEGIN ANSWER F0085 -----
結論：**算，而且是非常保守、流動性極強的財務體質**。不過「保守」主要體現在現金、短期美國國庫券與低槓桿；投資組合本身仍有相當大的股票集中與市場波動風險。

重點如下：

- **流動性非常充裕**：截至 FY2025、財年結束日為 **2025-12-31**，波克夏持有約 **3,690 億美元**的現金、現金等價物與美國國庫券；公司也明確表示，除非回購後仍保留至少 **300 億美元**，否則不會回購股票。[1]
- **資本基礎厚實**：股東權益約 **7,174 億美元**，且 2025 年營業活動產生的現金流約 **459.7 億美元**。[1][2]
- **負債相對低**：母公司層面的現金與國庫券約 **1,274 億美元**，而票據及其他借款約 **318 億美元**；單看母公司層面，現金資產明顯高於借款。[3] Finnhub 的最新基本面資料也顯示，BRK.B 的 debt-to-equity 約 **0.17**，current ratio 約 **1.23**。
- **保險業務提供大型「浮存金」**：2025 年底浮存金約 **1,760 億美元**，且保險業務連續三年產生承保利益，代表這項資金來源在近年並非高成本融資。[4]
- **但不是完全沒有風險**：波克夏的保險投資組合持有大量股票，而且集中在相對少數公司；公司也指出，其股票配置比例通常高於保險業慣例。[5] 因此，資產負債表保守，不代表淨利或股東權益不會因股市下跌而波動。

整體判斷是：**波克夏屬於「高流動性、低財務槓桿、保留大量安全墊」的保守型財務結構**。需要區分的是，這種保守性是對償債能力與危機應變能力而言；若從投資組合分散度來看，則不能說完全保守，因為股票部位集中度仍偏高。近期報導也引述管理層將其形容為「堡壘式」資產負債表，並強調審慎使用債務與維持大量流動性。[6]

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: https://www.cnbc.com/2026/02/28/berkshire-ceo-abel-vows-to-keep-buffetts-culture-of-disciplined-investing-in-first-annual-letter.html "Berkshire CEO Greg Abel vows to keep Buffett's culture of disciplined investing in first annual letter"
----- END ANSWER F0085 -----

===== ITEM F0086 =====

QUESTION:
分析 Visa 跟 Mastercard 的官方揭露，有沒有直接支持「監管會壓縮刷卡網路生意的獲利能力」這個說法。

----- BEGIN EVIDENCE F0086 -----
[tool 0] sec_filing_search {"query": "regulatory changes including interchange fee caps, routing requirements, assessment fees, and other regulation reducing transaction revenue, margins, profitability, or earnings", "ticker": "MA", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "MA",
   "fiscal_year": 2025,
   "item": "_unknown",
   "prelude": "Excerpts from MA FY2025 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001141391-26-000013/unknown#51",
     "title": "MA FY2025 10-K",
     "content": "- Payments Oversight and Regulation. Central banks and other regulators around the world either have established, or are seeking to establish, formal oversight over participants in the payments industry, as well as authority to regulate payments systems in their countries. Such
authority has resulted in certain of these entities regulating Mastercard as financial market infrastructure, as well as establishing oversight related to various aspects of our business (including areas such as consumer protections and cybersecurity). In the European Union (the “EU”), Mastercard
has been designated as a systemically important payment system (SIPS) and is subject to systemic importance regulation, which includes various requirements we must meet, including obligations related to governance and risk management. In the U.K., the Bank of England designated Vocalink™, our real-
time account-based payments network platform, as a “specified service provider”, and Mastercard as a “recognized payment system”, which includes supervisions and examination requirements. We have also been designated by certain jurisdictions as “critical infrastructure”, which includes cyber and
physical security resilience requirements and related reporting obligations. In addition, EU legislation requires us to separate our scheme activities (brand, products, franchise and licensing) from our switching activities and other processing in terms of how we go to market, make decisions and
organize our structure. Examples of other markets where Mastercard is formally overseen include Australia, Brazil, India, Mexico, South Africa and Canada. Additionally, certain of our subsidiaries are also regulated as payments institutions and payment service providers, including as money
transmitters. This regulation subjects us to licensing obligations, regulatory supervision and examinations, as well as various business conduct and risk management requirements.Interchange Fees. Interchange fees that support the function and value of four-party payments systems like ours are
subject to regulation in some jurisdictions. Examples include statutes in the U.S. that cap debit interchange for certain regulated activities, proposed legislation in the U.S. to extend routing mandates to credit and the EU regulation capping consumer credit and debit interchange fees. Interchange
fees are also periodically subject to litigation. For more detail, see “Risk Factors - Other Regulation” in Part I, Item 1A and Note 19 (Legal and Regulatory Proceedings) to the consolidated financial statements included in Part II, Item 8. Key 2025 Developments",
     "score": 0.6188
    },
    {
     "source": "sec://0001141391-26-000013/unknown#52",
     "title": "MA FY2025 10-K",
     "content": "- •In July 2025, the EU introduced its revised systemic importance regulation, covering companies such as ours that have been designated as systemically important. The revision introduces a framework for cyber resilience and detailed rules for managing outsourcing risks. It also
amended the definition of a SIPS operator in such a way as to extend to more companies in the payments ecosystem. •In November 2025, the Central Bank of Brazil established a new regulation for all Payment Scheme Operators (PSOs) in Brazil (including Mastercard and Visa), enhancing governance, risk
management and transparency standards across the payments ecosystem. The new regulation reinforces the PSOs’ accountability for the financial and settlement integrity of payments to merchants (including in cases of default, operational failure or insolvency of any of their scheme participants) and,
in particular, requires payment networks to extend their settlement guarantees to previously non-guaranteed transactions (such as merchant installment transactions). Although the regulation has already been enacted, its full implementation remains subject to the development and formal submission by
PSOs of their corresponding governance and risk management frameworks, as well as to the Central Bank’s review and approval of these frameworks. The conclusion of this process is expected to occur by November 2026. •In August and September of 2025, two separate Federal district courts issued
conflicting decisions regarding the validity of the interchange cap set by the Federal Reserve in Regulation II (related to the Durbin Amendment to the Dodd-Frank Wall Street Reform and Consumer Protection Act). One court vacated the interchange cap while the other upheld it. The interchange cap
remains in effect while the litigation continues. •The New Zealand Commerce Commission approved the implementation of caps on cross-border interchange for most types of card transactions, effective May 2026.",
     "score": 0.6219
    },
    {
     "source": "sec://0001141391-26-000013/unknown#55",
     "title": "MA FY2025 10-K",
     "content": "Issuer and Acquirer Practices Legislation and Regulation. Our issuers and acquirers are subject to numerous regulations and investigations applicable to banks, financial institutions and other licensed entities, which can indirectly impact us. Additionally, regulations such as the
EU’s Payment Services Directive in the EEA require financial institutions to provide third-party payment processors access to consumer payment accounts, enabling them to route transactions away from Mastercard products and provide payment initiation and account information services directly to
consumers who use our products.\n\nRegulation of Internet and High-Risk Merchant Categories. Various jurisdictions have enacted regulation related to internet transactions (such as laws surrounding gambling, including fantasy sports), which impacts both us and our customers. We are also impacted by
evolving laws surrounding certain legally permissible but high-risk merchant categories, such as adult content, firearms, alcohol and tobacco.",
     "score": 0.5856
    },
    {
     "source": "sec://0001141391-26-000013/unknown#59",
     "title": "MA FY2025 10-K",
     "content": "### Payments Industry Regulation\n\nGlobal regulatory and legislative activity related to the payments industry may have a material adverse impact on our overall business and results of operations.\n\nCentral banks and similar regulatory bodies have increasingly established or
further expanded their authority over certain aspects of payments systems such as ours, including obligations or restrictions with respect to the types of products and services that we may offer, the countries in which our products and services may be used, the way we structure and operate our
business and the types of consumers and merchants who can obtain or accept our products or services. Similarly, jurisdictions that regulate a particular product may consider extending their jurisdiction to other products. For example, debit regulations could lead to regulation of credit products.
Moreover, several jurisdictions are demonstrating increased interest about the network fees we charge to our customers (in some cases as part of broader market reviews of retail payments), which could in the future lead to regulation relating to our network fees. In several jurisdictions, we have
been designated as a “systemically important payment system”, with other regulators considering similar designations. This type of regulation and oversight is related to switching activities, and includes policies, procedures and requirements related to risk management, collateral, participant
default, timely switching of financial transactions, and capital and financial resources. Parts of our business have also been deemed as a “specified service provider” or considered “critical infrastructure”. The impact to our business created by any new law, regulation or designation is magnified
by the potential it has to be replicated in, or conflict with, other jurisdictions, or involve other products within any particular jurisdiction.\n\nOur strategic expansion of our products and services has also created the need for us to obtain new types and increasing numbers of regulatory
licenses, resulting in increased supervision and additional compliance burdens distinct from those imposed on our payment network activities. For example, certain of our subsidiaries maintain money transfer licenses that typically impose supervisory and examination requirements, as well as capital,
safeguarding, risk management and other business obligations.",
     "score": 0.6275
    },
    {
     "source": "sec://0001141391-26-000013/unknown#60",
     "title": "MA FY2025 10-K",
     "content": "Increased regulation and oversight of payments systems, as well as increased exposure to regulation resulting from changes to our products and services, have resulted and may continue to result in significant compliance and governance burdens or otherwise increase our costs. As a
result, customers could be less willing to participate in our payments system and/or use our other products or services, reduce the benefits offered in connection with the use of our products (making our products less desirable to consumers), reduce the volume of domestic and cross-border
transactions or other operational metrics, disintermediate us, impact our profitability and/or limit our ability to innovate or offer differentiated products and services, all of which could materially and adversely impact our financial performance. In addition, any regulation that is enacted
related to the type and level of network fees we charge our customers could also materially and adversely impact our results of operations. Regulators could also require us to obtain prior approval for changes to our system rules, procedures or operations, or could require customization with regard
to such\n\nMASTERCARD 2025 FORM 10-K 27\n\n\n\nPART I\n\nITEM 1A. RISK FACTORS\n\nchanges, which could negatively impact us. Moreover, failure to comply with the laws and regulations to which we are subject could result in fines, sanctions, civil damages or other penalties, which could materially
and adversely affect our overall business and results of operations, as well as have an impact on our brand and reputation.\n\nIncreased activity with respect to interchange rates could have an adverse impact on our business.\n\nInterchange rates are a significant component of the costs that
merchants pay in connection with the acceptance of products associated with our payment network. Although we do not earn revenues from interchange, interchange rates can impact the volume of transactions we see on our payment products. If interchange rates are too high, merchants may stop accepting
our products or route transactions away from our network. If interchange rates are too low, issuers may stop promoting our products and services, eliminate or reduce loyalty rewards programs or other account holder benefits (e.g., free checking or low interest rates on balances), or charge fees to
account holders (e.g., annual fees or late payment fees).\n\nGovernments and merchant groups in a number of countries have implemented or are seeking interchange rate reductions through legislation, regulation and litigation. See “Business - Government Regulation” in Part I, Item 1 and Note 19
(Legal and Regulatory Proceedings) to the consolidated financial statements included in Part II, Item 8 for more details.",
     "score": 0.686
    },
    {
     "source": "sec://0001141391-26-000013/unknown#61",
     "title": "MA FY2025 10-K",
     "content": "If issuers cannot collect or we are required to reduce interchange rates, issuers may be less willing to participate in our four-party payments system. Alternatively, they may reduce the benefits associated with our products, choose to charge higher fees to consumers to attempt to
recoup a portion of the costs incurred for their services, or seek a fee reduction from us to decrease the expense of their payment programs (particularly if regulation has a disproportionate impact on us as compared to our competitors in terms of the fees we can charge). These and other impacts
could make our products less desirable to consumers, limit our ability to innovate or offer differentiated products, and/or make proprietary three-party networks or other forms of payment more attractive, ultimately reducing the volume of transactions over our network and our profitability.\n\nWe
are devoting substantial resources to defending our right to establish interchange rates in regulatory proceedings, litigation and legislative activity. The potential outcome of any of these activities could have a more positive or negative impact on us relative to our competitors. If we are
ultimately unsuccessful in defending our ability to establish interchange rates, any resulting legislation, regulation and/or litigation may have a material adverse impact on our overall business and results of operations. In addition, regulatory proceedings and litigation could result (and in some
cases has resulted) in us being fined and/or having to pay civil damages, the amount of which could be material.\n\nLimitations on our ability to restrict merchant surcharging could materially and adversely impact our results of operations.\n\nWe have historically implemented policies, referred to
as no-surcharge rules, in certain jurisdictions, including the U.S. and Canada, that prohibit merchants from charging higher prices to consumers who pay using our products instead of other means. Authorities in several jurisdictions have acted to end or limit the application of these no-surcharge
rules (or indicated interest in doing so). Additionally, our no-surcharge rules now permit U.S. and Canadian merchants to surcharge credit cards (subject to certain limitations). If, over time, an increased number of merchants choose to surcharge as permitted, this could result in consumers viewing
our products less favorably and/or using alternative means of payment. These responses could result in a decrease in our overall transaction volumes, which in turn could materially and adversely impact our results of operations.",
     "score": 0.6673
    },
    {
     "source": "sec://0001141391-26-000013/unknown#67",
     "title": "MA FY2025 10-K",
     "content": "### Other Regulation\n\nRegulations that directly or indirectly apply to Mastercard as a result of our participation in the global payments industry may materially and adversely affect our overall business and results of operations.\n\nWe are subject to regulations that affect the
payments industry in the many jurisdictions in which our products and services are used. Many of our customers are also subject to regulations applicable to banks and other financial institutions that, at times, consequently affect us. Such regulation has increased significantly in the last several
years (as described in “Business - Government Regulation” in Part I, Item 1). Examples include:\n\n•Anti-Money Laundering, Countering the Financing of Terrorism, Economic Sanctions and Anti-Corruption. We are subject to AML and CFT laws and regulations globally. Economic sanctions programs
administered by OFAC restrict financial transactions and other dealings with certain countries and geographies, and persons and entities. We are also subject to anti-corruption laws and regulations globally, which, among other things, generally prohibit giving or offering payments or anything of
value for the purpose of improperly influencing a business decision or to gain an unfair business advantage.\n\n•Account-based Payments Systems. In the U.K., aspects of our Vocalink business are subject to the U.K. payment system oversight regime and are directly overseen by the Bank of
England.\n\n•Issuer and Acquirer Practices Legislation and Regulation. Certain regulations or legislation that do or could impact our issuers and acquirers (such as caps on issuer interest rates) may impact various aspects of our business. Additionally, strong authentication requirements within the
EU’s Payment Services Directive in the EEA could increase the number of transactions consumers abandon if we are unable to secure a frictionless authentication experience under these standards. Such an increase could adversely impact our volumes or other operational metrics.",
     "score": 0.5965
    },
    {
     "source": "sec://0001141391-26-000013/unknown#68",
     "title": "MA FY2025 10-K",
     "content": "Increased regulatory focus on us has resulted and may continue to result in significant compliance and governance burdens or otherwise increase our costs. Similarly, increased regulatory focus on our customers and other stakeholders may cause them to reduce the volume of
transactions processed through our systems, or may otherwise impact the competitiveness of our products. Actions by regulators could influence other organizations around the world to enact or consider adopting similar measures, amplifying any potential compliance burden. Additionally, our compliance
with new economic sanctions and related laws with respect to particular jurisdictions or customers could result in a loss of business, which could be significant. Moreover, while our risk-based compliance program obligates issuers and acquirers to comply with U.S., EU and local sanctions programs
(among other obligations), the failure of those issuers and acquirers to identify potential non-compliance issues either during or after their customer onboarding processes could ultimately impact our compliance with economic sanctions and related laws. Finally, failure to comply with the laws and
regulations discussed above to which we are subject could result in fines, sanctions or other penalties. In particular, a violation and subsequent judgment or settlement against us, or those with whom we may be associated, under economic sanctions and AML, CFT, and anti-corruption laws could subject
us to substantial monetary penalties, damages, and/or have a significant reputational impact. Each instance may individually or collectively materially and adversely affect our financial performance and/or our overall business and results of operations, as well as have an impact on our
reputation.\n\nWe could be subject to adverse changes in tax laws, regulations and interpretations or challenges to our tax positions.\n\nWe are subject to tax laws and regulations of the U.S. federal, state and local governments as well as various non-U.S. jurisdictions. Current and potential
future changes in existing tax laws, including regulatory guidance, are continuously being considered and have been or may be enacted (such as guidelines issued by the Organization for Economic Co-operation and Development (OECD) which impact how multinational enterprises are taxed on their global
profits). These changes have and in the future may continue to have an impact on our effective income tax rate and tax payments. Similarly, changes in tax laws and regulations that impact our customers and counterparties, or the economy generally, have impacted and may continue to impact us.",
     "score": 0.5745
    },
    {
     "source": "sec://0001141391-26-000013/unknown#73",
     "title": "MA FY2025 10-K",
     "content": "•Payments industry participants may merge, create joint ventures or form other business combinations that may strengthen their existing business services, leverage other business models to create a competitive edge over us or create new payment products and services that compete
with our products and services.\n\n•Regulation may disintermediate issuers by enabling third-party providers opportunities to route payment transactions toward their own forms of payment by offering account information or payment initiation services directly to our product users. Such regulation may
also provide these processors with the opportunity to commoditize the data that are included in the transactions they are servicing. Disintermediation of our customers’ business could diminish demand for our products and services.\n\nOur failure to compete effectively against any of the foregoing
competitive threats could materially and adversely affect our overall business and results of operations.\n\nContinued intense pricing pressure may materially and adversely affect our overall business and results of operations.\n\nIn order to increase transaction volumes, enter new markets and
expand our products and services, we seek to enter into business agreements with customers through which we offer incentives, pricing discounts and other support that promote our products. In order to stay competitive, we may have to increase the amount of these incentives and pricing discounts so
as to meet customer demand for better pricing arrangements and greater rebates and incentives. As a result, we may not be able to grow our volume and/or services to the extent necessary to compensate for the additional costs related to these increased incentives and pricing discounts. In addition,
increased pressure on prices increases the importance of cost containment and productivity initiatives in areas other than those relating to customer incentives.\n\nIn the future, we may not be able to enter into agreements with our customers if they require terms that we are unable or unwilling to
offer, and we may be required to modify existing agreements in order to maintain relationships and compete with others in the industry. Some of our competitors are larger with greater financial resources and accordingly may be able to charge lower prices. In addition, to the extent that we offer
discounts or incentives under such agreements, we will need to further increase transaction volumes or the amount of services provided in order to benefit from such agreements and to increase revenue and profit, and we may not be successful in doing so, particularly in the current regulatory
environment. Our customers also may implement cost reduction initiatives that reduce or eliminate payment product marketing or increase requests for greater incentives or greater cost stability. In addition to decisions made by competitors and customers, we also face pressure from pricing regulation
and litigation.",
     "score": 0.5771
    },
    {
     "source": "sec://0001141391-26-000013/unknown#89",
     "title": "MA FY2025 10-K",
     "content": "•Current and potential future geopolitical conflicts, as well as expansion into regional or global conflicts, and the resulting impacts to our business\n\n•The threat of terrorism and major environmental and extreme weather events (including those related to climate change)\n\nThe
impact of and uncertainty that could result from any of these events or factors could ultimately decrease cross-border activity. Additionally, any regulation of interregional interchange fees could also negatively impact our cross-border activity (for example, the targets announced by the G20
Financial Stability Board related to cross-border payments). In each case, decreased cross-border activity could decrease the revenue we receive.\n\nRussia’s invasion of Ukraine. In addition to the cross-border impacts described above, our compliance with sanctions and our decision to suspend our
business operations in Russia has led, and could further lead, to other legal ramifications and operational challenges, including fines, the nationalization of our subsidiary and any resulting impacts, and/or lawsuits.\n\nStandards. Our operations as a global payments network rely in part on global
interoperable standards to help facilitate payments. To the extent geopolitical events or government intervention result in jurisdictions no longer participating in the creation or adoption of these standards, or the creation of competing standards, our products and services could be negatively
impacted.\n\nAny of these developments potentially could have a material adverse impact on our overall business and results of operations.\n\nAdverse currency fluctuations and foreign exchange controls could negatively impact our results of operations.\n\nDuring 2025, approximately 71% of our
revenue was generated from activities outside the U.S., which could be transacted in a non-functional currency. Impacts from currency fluctuations are included in our net income. Our risk management activities provide protection with respect to adverse changes in the value of only a limited number
of currencies and are based on estimates of exposures to these currencies.\n\nIn addition, the revenue we generate in entities with non-U.S. dollar functional currencies is subject to unpredictable currency fluctuations, including where the values of other currencies change relative to the U.S.
dollar. If the U.S. dollar strengthens compared to currencies in which we generate revenue, this revenue may be translated at a materially lower amount than expected.\n\nFurthermore, we may become subject to exchange control regulations that might restrict or prohibit the conversion into U.S.
dollars of our other revenue currencies and financial assets.\n\nThe occurrence of currency fluctuations or exchange controls could have a material adverse impact on our results of operations.",
     "score": 0.5928
    }
   ]
  }
 ]
}

[tool 1] sec_filing_search {"query": "regulatory changes including interchange fee caps, routing requirements, assessment fees, and other regulation reducing transaction revenue, margins, profitability, or earnings", "ticker": "V", "fiscal_year": null}
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
   "prelude": "Excerpts from V FY2025 10-K, Item 1A (Risk Factors) — 9 passage(s) in document order.",
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
     "score": 0.6244,
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
     "score": 0.7008
    },
    {
     "source": "sec://0001403161-25-000089/1a#53",
     "title": "V FY2025 10-K · Item 1A",
     "content": "Interchange reimbursement fees, certain operating rules and related practices continue to be subject to increased government regulation globally, and regulatory authorities and central banks in a number of jurisdictions have reviewed or are reviewing these fees, rules and practices.
For example:\n\n•Regulations adopted by the U.S. Federal Reserve cap the maximum U.S. debit interchange reimbursement rate received by large financial institutions at 21 cents plus 5 basis points per transaction, plus a possible fraud adjustment of 1 cent. Additionally, the Dodd-Frank Act limits
issuers’ and payment networks’ ability to adopt network exclusivity and preferred routing in the debit and prepaid area, which also impacts our business. In response to seller requests, the Federal Reserve has recently taken actions to revisit its regulations that implement these aspects of the
Dodd-Frank Act. For example, in October 2022, the Federal Reserve published a final rule effectively requiring issuers to ensure that at least two unaffiliated networks are available for routing ecommerce debit transactions by July 1, 2023. In October 2023, the Federal Reserve issued a proposal for
comment that further lowers debit interchange rates, with a mechanism for automatic adjustment every two years. Finally, in August 2025, the District Court for the District of North Dakota ruled that the Federal Reserve exceeded its authority in implementing Regulation II, which sets debit card
interchange fees. The court found the Federal Reserve improperly included various costs beyond what the Durbin Amendment allows, such as fraud losses, network fees and other fixed costs, when setting the debit interchange fee standard. As a result, the court vacated Regulation II’s debit interchange
fee\n\n21\n\n\n[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)",
     "score": 0.7029
    },
    {
     "source": "sec://0001403161-25-000089/1a#54",
     "title": "V FY2025 10-K · Item 1A",
     "content": "[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)\n\nstandard. Subsequently, however, the District Court in Kentucky ruled that the Federal Reserve acted within its discretion in setting the debit interchange cap. If the District Court
of North Dakota’s decision is affirmed on appeal and ultimately prevails, it could potentially result in the Federal Reserve setting a significantly lower interchange cap for relevant debit transactions in the U.S. Separately, there continues to be interest in regulation of credit interchange fees
and routing practices by members of Congress and state legislators. It is possible that the Credit Card Competition Act may be reintroduced in Congress or attempted to be offered as an amendment to unrelated legislation. Previous versions of the legislation were introduced in 2022 and 2023, and
required among other things, that large issuing banks offer a choice of at least two unaffiliated networks over which electronic credit transactions may be processed. Finally, some states have passed or are considering passing laws that regulate how interchange can be set and assessed. For example,
in May 2024, Illinois passed a law that restricts the assessment of interchange on the state tax and gratuity portions of a transaction, and restricts financial institutions and payment networks, among others, from using payment transaction data for any purpose other than facilitating or processing
a transaction. While the Illinois law remains subject to legal challenge, if such laws are allowed to go into effect, they may also impose significant technical and compliance burdens on our business.\n\n•In Europe, the EU’s IFR places an effective cap on consumer credit and consumer debit
interchange fees for both domestic and cross-border transactions within the European Economic Area of 30 basis points and 20 basis points, respectively. EU member states have the ability to further reduce these interchange levels within their territories. The European Commission has announced its
intention to conduct another impact assessment of the IFR, which could result in even lower caps on interchange rates and the expansion of regulation to other types of products, services and fees.",
     "score": 0.6953
    },
    {
     "source": "sec://0001403161-25-000089/1a#55",
     "title": "V FY2025 10-K · Item 1A",
     "content": "•Several countries in Latin America continue to explore regulatory measures against payments networks and have either adopted or are exploring interchange caps, including Argentina, Brazil, Chile and Costa Rica. In Asia Pacific, the Reserve Bank of Australia (RBA) which already
regulates interchange, recently proposed reducing existing interchange caps on domestic credit and debit transactions and not allowing differential interchange treatment for consumer and commercial transactions. Similarly, in New Zealand, the Commerce Commission recently lowered existing caps on
domestic credit transactions. Interchange is also regulated in certain countries in the Central and Eastern Europe, Middle East and Africa region, including the United Arab Emirates. Finally, many governments, including but not limited to governments in India, Costa Rica, and Turkey, are using
regulation to further drive down MDR, which could negatively affect the economics of our transactions.\n\n•While the focus of interchange and MDR regulation has primarily been on domestic rates, interest on cross-border rates has been growing. For example, we agreed to limit certain cross-border
interchange rates in a settlement with the European Commission in 2019, which was extended through 2029. In 2020, Costa Rica became the first country to formally regulate cross-border interchange rates by regulation. In June 2022, the UK’s PSR initiated a market review focusing on post-Brexit
increases in interchange rates for e-commerce transactions between the UK and Europe and is proposing to cap cross-border interchange on certain transactions in that geographic corridor. Most recently, in July 2025, New Zealand adopted interchange caps on cross-border transactions including
commercial credit transactions. Australia has also proposed adopting caps for cross-border transactions. Cross-border MDR is also regulated in Costa Rica and Turkey.\n\n•With increased lobbying by sellers and other industry participants, we are also beginning to see regulatory interest in network
fees. For example, the UK’s PSR is conducting a market review into scheme and processing fees. In its interim report, the PSR indicated that it is reviewing possible remedies in the areas of governance, reporting and transparency, any of which, if adopted, could impose additional complexity and
burdens on our business in the UK. Other regulators, for example, those in Australia, the EU, Chile and New Zealand have expressed an interest in network fees, including issues related to transparency. Finally, in 2024, the Greek Parliament limited acquirer fees for certain small ticket transactions
in some seller categories for a period of three years.",
     "score": 0.658
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
     "score": 0.6511
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
     "score": 0.6624
    },
    {
     "source": "sec://0001403161-25-000089/1a#72",
     "title": "V FY2025 10-K · Item 1A",
     "content": "[Table](#i3e21d382a73642188017c034fc47d460_7)[of Contents](#i3e21d382a73642188017c034fc47d460_7)\n\nIn addition, we face intense competitive pressure on the prices we charge our financial institution clients. In certain regions, we are increasingly facing competition from RTP
networks, other payment facilitators offering lower pricing, and government involvement in domestic and cross-border payments. In order to stay competitive, we may need to adjust our pricing or offer incentives to our clients to grow payments volume, enter new market segments, adapt to regulatory
changes, and expand their use and acceptance of Visa products and services. These include up-front cash payments, fee discounts, rebates, credits, performance-based incentives, marketing and other support payments that impact our net revenue and profitability. In addition, we offer incentives to
certain sellers and acquirers to encourage them to route transactions to Visa. Pressures on pricing, incentives, fee discounts and rebates could moderate our growth. If we are not able to implement cost containment and productivity initiatives in other areas of our business or grow our volume in
other ways to offset or absorb the financial impact of these incentives, fee discounts and rebates, it may harm our net revenue and profits.\n\nSellers’ and processors’ continued push to lower acceptance costs and challenge industry practices could harm our business.",
     "score": 0.5839
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
     "score": 0.589
    }
   ]
  },
  {
   "ticker": "V",
   "fiscal_year": 2025,
   "item": "Item 1",
   "prelude": "Excerpts from V FY2025 10-K, Item 1 (Business) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001403161-25-000089/1#46",
     "title": "V FY2025 10-K · Item 1",
     "content": "Interchange Rates and Fees: An increasing number of jurisdictions around the world regulate or influence debit and credit interchange reimbursement rates in their regions. For example, the U.S. Dodd-Frank Wall Street Reform and Consumer Act (Dodd-Frank Act) limits interchange
reimbursement rates for certain debit card transactions in the U.S.; the European Union (EU) Interchange Fee Regulation (IFR) limits interchange rates in the European Economic Area (EEA) (as discussed below); and the Reserve Bank of Australia (RBA) regulates average permissible levels of
interchange.\n\nInternet Transactions: Many jurisdictions have adopted regulations that require payments system participants to monitor, identify, filter, restrict or take other actions with regard to certain types of payment transactions on the Internet, such as gambling, digital currencies, the
purchase of cigarettes or alcohol and other controversial transaction types.\n\nNetwork Exclusivity and Routing: In the U.S., the Dodd-Frank Act limits network exclusivity and restrictions on seller routing choice for the debit and prepaid market segments. Other jurisdictions impose similar
limitations, such as the IFR’s prohibition in Europe on restrictions that prevent multiple payment brands or functionality on the same card.\n\nNo-surcharge Rules: We have historically enforced rules that prohibit sellers from charging higher prices to consumers who pay using Visa products instead
of other means. However, sellers’ ability to surcharge varies by geographic market as well as Visa product type, and continues to be impacted by litigation, regulation and legislation.\n\nPrivacy, Data Use, AI and Cybersecurity: Aspects of our operations or business are subject to increasingly
complex and fragmented data-related regulations, including with respect to privacy, data use, AI and cybersecurity, which impact the way we collect, use and handle data, operate our products and services and even impact our ability to offer a product or service. In addition, legislatures and
regulators globally are proposing new laws or regulations on these topics that could require Visa to adopt more restrictive data collection and processing practices; expand cybersecurity requirements; limit cross-border data flows; impact the adoption of advanced AI systems; and impose increased
obligations on companies handling personal data.",
     "score": 0.655
    }
   ]
  }
 ]
}
----- END EVIDENCE F0086 -----

----- BEGIN ANSWER F0086 -----
**結論：有，而且 Mastercard 的表述比 Visa 更直接。** 兩家公司最新 FY2025 10-K 都明確把監管與「收入、交易量、成本及獲利能力」連結起來；但它們揭露的是**重大不利影響的風險機制**，不是宣稱監管必然、或已經全面壓縮了獲利率。

### 1. Visa：直接支持，但主要是「間接壓縮」

根據 Visa FY2025 10-K（財政年度截至 **2025-09-30**），Visa 明確表示監管會：

- 增加合規成本與營運複雜度；
- 減少收入機會；
- 影響交易量、淨收入及財務結果。[1]

Visa 特別說明，** interchange reimbursement fee 並非 Visa 通常直接收取的收入**，而是收單行支付給發卡行；但 interchange 水準會影響發卡行、收單行及商戶對 Visa 網路的參與和使用，因此變動仍可能「substantially affect」Visa 的整體支付量與淨收入。[2]

Visa 揭露的傳導機制是：

1. 監管壓低 interchange 或限制路由；
2. 發卡行可能降低卡片福利，收單行可能提高商戶折扣率或轉向其他網路；
3. Visa 為維持交易量，可能提供更多折扣、回饋與客戶激勵；
4. 這些優惠會直接影響 Visa 的淨收入與獲利能力。[3]

Visa 也明確指出，監管壓力可能降低其支付量及相關收入；如果無法以成本控制或其他交易量成長抵銷折扣、回饋及激勵，就可能傷害淨收入與利潤。[4]

**因此，Visa 的官方揭露支持「監管會壓縮刷卡網路的獲利能力」這個說法，但更精確的表述是：監管先透過交易量、定價、客戶激勵與合規成本影響獲利，而不一定是直接砍 Visa 的 interchange 收入。**

### 2. Mastercard：支持更直接，明文寫到 profitability

Mastercard FY2025 10-K 的財政年度截至 **2025-12-31**，措辭更明確。Mastercard 表示，監管及監督可能造成重大合規與治理負擔、增加成本，並可能：

- 降低客戶參與其支付系統的意願；
- 減少國內及跨境交易量；
- 影響產品競爭力；
- **impact our profitability**；
- 限制創新或差異化產品的能力。[5]

Mastercard 也明確指出，若未來監管其向客戶收取的 **network fees**，可能對營運結果產生重大不利影響。[5] 這一點比單純討論 interchange 更接近「網路本身的收入與獲利能力」，因為 network fees 是 Mastercard 向客戶收取的費用。

對 interchange 的部分，Mastercard 同樣承認自己通常**不直接賺取 interchange revenue**；但 interchange 會影響商戶是否接受 Mastercard、交易是否被路由到 Mastercard，以及發卡行是否繼續推廣其產品。[6] Mastercard 更進一步寫明，若 interchange 被迫降低，發卡行可能要求 Mastercard 降低費用；最終可能減少網路交易量及 **profitability**。[7]

### 3. 這個說法成立，但要避免一個常見誤解

「監管壓縮刷卡網路生意的獲利能力」如果理解為：

> 監管直接拿走 Visa 或 Mastercard 的 interchange 收入

那麼這個表述不夠精確，因為兩家公司都說，四方支付模式下 interchange 通常是發卡行與收單行之間的費用，並非 Visa 或 Mastercard 的直接收入。[2][6]

如果理解為：

> 監管透過 interchange 上限、路由要求、network-fee 監管、價格限制及合規義務，降低交易量或網路定價能力，增加成本，並迫使網路提供更多折扣和激勵，從而壓縮淨收入和利潤

那麼這個說法受到兩家公司官方揭露的**直接支持**，其中 Mastercard 甚至直接使用「impact our profitability」及「reduce ... our profitability」的措辭。[5][7]

### 判斷

| 命題 | Visa | Mastercard |
|---|---|---|
| 監管增加成本 | 直接支持 | 直接支持 |
| 監管降低交易量 | 直接支持 | 直接支持 |
| 監管降低淨收入 | 直接支持 | 直接支持 |
| 監管壓縮獲利能力 | 支持，透過激勵、折扣及成本機制 | **明確直接支持** |
| 監管直接削減 interchange 收入 | 不精確；兩者通常不直接收取 interchange | 不精確；兩者通常不直接收取 interchange |
| network fees 受監管而受壓 | 有相關監管風險揭露 | **明確直接支持** |

所以，最嚴謹的結論是：**官方揭露支持「監管可能壓縮 Visa 與 Mastercard 的網路經濟性及獲利能力」，但主要傳導渠道是交易量、客戶定價、network fees、折扣／激勵與合規成本，而不是簡單等同於 interchange 收入被直接拿走。**

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt
----- END ANSWER F0086 -----

===== ITEM F0087 =====

QUESTION:
英特爾最近這些負面新聞，已經足夠代表基本面真的惡化了嗎？

----- BEGIN EVIDENCE F0087 -----
[tool 0] finnhub_stock_quote {"ticker": "INTC"}
{
 "ticker": "INTC",
 "currentPrice": 92.9,
 "open": 90.8475,
 "previousClose": 90.47,
 "change": 2.43,
 "percentChange": 2.686,
 "dayHigh": 94.10000000000001,
 "dayLow": 90.8475
}

[tool 1] finnhub_company_basic_financials {"ticker": "INTC"}
{
 "ticker": "INTC",
 "fiftyTwoWeekHigh": 142.35,
 "fiftyTwoWeekLow": 32.89,
 "forwardPE": 63.01586,
 "psTTM": 8.4345,
 "pb": 7.5624,
 "marketCap": 481035.6,
 "enterpriseValue": 518698.6,
 "beta": 2.3829305,
 "epsTTM": -2.1202,
 "roeTTM": -10.76,
 "roaTTM": -5.48,
 "grossMarginTTM": 38.6,
 "netProfitMarginTTM": -19.79,
 "operatingMarginTTM": 9.36,
 "currentRatio": 1.604,
 "quickRatio": 1.2537,
 "debtToEquity": 0.5773,
 "dividendYield": 1.1374,
 "revenueGrowthTTMYoy": 7.47,
 "tenDayAvgVolume": 100.46334
}

[tool 2] sec_filing_search {"query": "recent business performance deterioration revenue gross margin operating loss cash flow foundry manufacturing restructuring risks", "ticker": "INTC", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-27",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "INTC",
   "fiscal_year": 2025,
   "item": "_unknown",
   "prelude": "Excerpts from INTC FY2025 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000050863-26-000011/unknown#55",
     "title": "INTC FY2025 10-K",
     "content": "Our 2025 consolidated results of operations were also affected by accelerated depreciation and impairment charges recognized for certain manufacturing assets that were determined to have no remaining operational use. This determination was based on an evaluation of our current
process technology node capacities relative to projected market demand for our products and services. These non-cash charges of $950 million, net of certain items, were recorded to cost of sales in 2025, impacting the results for our Intel Foundry segment.\n\n2024\n\nIn 2024, we announced and
initiated the 2024 Restructuring Plan, which reduced headcount, consolidated and reduced our global real estate footprint, and reduced our overall operating expenses. As a result of initiating and deploying our 2024 Restructuring Plan, we recognized restructuring charges of $2.8 billion in 2024 and
$348 million in 2025.\n\nOur 2024 consolidated results of operations were also materially impacted by the following:\n\n▪$3.3 billion of charges, substantially all of which were recorded to cost of sales, related to non-cash impairments and the acceleration of depreciation for certain manufacturing
assets, a substantial majority of which related to our Intel 7 process node;\n\n▪$3.1 billion of non-cash charges associated with the impairment of goodwill for certain of our reporting units as well as certain acquired intangible assets (see \"Note 7: Restructuring and Other Charges\" within Notes
to Consolidated Financial Statements); and\n\n▪$9.9 billion of non-cash charges recorded to provision for income taxes that substantially related to valuation allowances recorded to our net deferred tax assets (see \"Provision for (Benefit from) Taxes\" within this MD&A below).\n\nNon-Controlling
Interests",
     "score": 0.551
    },
    {
     "source": "sec://0000050863-26-000011/unknown#68",
     "title": "INTC FY2025 10-K",
     "content": "Intel Foundry Financial Performance1\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|\n| Years Ended ($ In Millions) | | |  | | |
Dec 27, 2025 | | |  | | | Dec 28, 2024 | | |  | | | Dec 30, 2023 | | |\n| Revenue | | |  | | | $ | 17,826 |  |  | | | $ | 17,317 |  |  | | | $ | 18,504 |  |\n| Cost of sales and operating expenses | | |  | | | 28,144 | |  |  | | | 30,608 | |  |  | | | 25,587 | |  |\n| Operating loss | | |  | | | $ |
(10,318) |  |  | | | $ | (13,291) |  |  | | | $ | (7,083) |  |\n|\n| Operating loss % | | |  | | | (58)% | | |  | | | (77)% | | |  | | | (38)% | | |\n\n1 Operating segment results include intersegment financial activity; refer to \"Note 3: Operating Segments\" within Notes to Consolidated Financial
Statements for a reconciliation between our operating segment and consolidated financial results for the periods presented.\n\n|  |  |  |\n| --- | --- | --- |\n| Operating Segment Revenue Summary | | |\n\n2025 vs. 2024",
     "score": 0.5637
    },
    {
     "source": "sec://0000050863-26-000011/unknown#102",
     "title": "INTC FY2025 10-K",
     "content": "▪market and economic factors, including cyclical changes in market conditions, the introduction of new or alternative products in the marketplace and the associated pricing environment; and\n\n▪other factors, including tariff and export controls.\n\nEach reporting period, we compare
our demand forecast estimate to work-in-process and finished goods inventory levels to determine the amount, if any, of obsolete or excess inventory, which would be reflected in cost of sales and result in a negative impact to our gross profit in that period. If our assumptions and estimates for our
demand forecast materially fluctuate and we fail to adjust manufacturing output accordingly or such assumptions and estimates are materially inaccurate, the related obsolete and excess inventory reserves can be materially impacted and result in reduced inventory values for products that we estimate
have substantial sales risk. Our estimates for obsolete and excess inventory reserves were materially consistent with actual results in 2025, 2024 and 2023; however, our assumptions and estimates are inherently uncertain, and our gross profit would be adversely affected if future demand is less
favorable than forecasted.\n\nProperty, Plant and Equipment\n\nAt least annually, we evaluate the period over which we expect to recover the economic value of our property, plant and equipment, considering factors such as the process technology cadence between node transitions, changes in machinery
and equipment technology, and re-use of machinery and tools across each generation of process technology. As we make manufacturing process conversions and other factory planning decisions, we use assumptions involving the use of management judgments regarding the remaining useful lives of assets,
primarily process-specific semiconductor manufacturing tools and building improvements. When we determine that the useful lives of assets are shorter or longer than we had originally estimated, we adjust the rate of depreciation to reflect the assets' revised useful lives. In 2025 and 2024, we
evaluated our current process technology node capacities relative to projected market demand for our products and services, and concluded that our manufacturing asset portfolio exceeded manufacturing capacity requirements, which resulted in us shortening the useful lives of certain placed-in-service
equipment and recording accelerated depreciation charges of $456 million and $992 million, respectively. These amounts exclude charges associated with certain business exits that we incurred in connection with our 2025 Restructuring Plan and 2024 Restructuring Plan.",
     "score": 0.5554
    },
    {
     "source": "sec://0000050863-26-000011/unknown#109",
     "title": "INTC FY2025 10-K",
     "content": "|  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- |\n| Risk Factors | | |  | | |\n|  | | |  | | |\n\nThe following summarizes what we believe to be the material factors that make an investment in our securities speculative or risky. When any one or more of the following risks
materialize from time to time, our business, reputation, financial condition, cash flows and results of operations may be materially and adversely affected, and the trading price of our common stock could decline. These risk factors do not identify all risks that we face; we may also be affected by
factors that are not presently known to us or that we currently consider to be immaterial, or by various risks that are generally applicable to most companies. Due to risks and uncertainties, known and unknown, our past financial results may not be a reliable indicator of future performance, and
historical trends should not be used to anticipate results or trends in future periods. Some of the factors, events and contingencies discussed below may have occurred in the past, and while we highlight certain noteworthy examples from recent years where occurrences of such factors, events or
contingencies had a material adverse effect on our business, such examples do not represent all of the instances where the factors, events or contingencies have occurred. Refer also to the other information set forth in this Form 10-K, including in the MD&A and Financial Statements and Supplemental
Details sections.\n\nWe are in a highly competitive and rapidly changing industry.\n\nThe industry in which we operate is highly competitive and subject to rapid technological, geopolitical and market developments; changes in industry standards; changes in customer and end-user needs, expectations
and preferences; and frequent product introductions and improvements. When we do not anticipate or respond to these developments, our competitive position can weaken and our products or technologies can become uncompetitive or obsolete. Our competitive environment has intensified in recent years,
and we expect it to continue to do so in the future, including as a result of the proliferation of AI and high demand for AI-related products and services. In addition, many of our competitors have substantially greater financial resources than us. If we are not able to compete effectively, or if
our external foundry strategy is unsuccessful, our financial results will be adversely affected, including through reduced revenue and gross margin, and we may be required to accelerate the write-down of the value of certain assets.",
     "score": 0.5449
    },
    {
     "source": "sec://0000050863-26-000011/unknown#112",
     "title": "INTC FY2025 10-K",
     "content": "We have limited experience in the highly competitive and capital-intensive third-party foundry business. As we pursue our strategy to establish Intel Foundry as a major provider of foundry capacity to manufacture semiconductors for others, we face intense competition from well-
established competitors such as TSMC, Samsung, Global Foundries, UMC and SMIC. To succeed, we need to compete effectively across factors such as availability and time-to-market of manufacturing technology; advances in manufacturing processes in areas such as performance, performance per watt and
density; multi-chip packaging; system integration; manufacturing capacity; price; margin; ease of use; quality; yields; customer satisfaction; and ecosystem support. Building and maintaining a competitive foundry business requires significant ongoing investments to maintain leading-edge process
technology and manufacturing capacity, which investments in many instances must be made ahead of customer commitments and may not be recouped. As we have reassessed demand and our \"shell ahead\" strategy, and our financial results in the last few years have constrained our ability to make capital
investments, we have delayed or cancelled manufacturing facility construction or expansion projects in Ohio, Germany, Poland, Malaysia and Israel and initiated the consolidation of our assembly and test facility in Costa Rica into our other facilities, and we may have additional project delays or
project cancellations in the future. Moreover, many of the largest potential foundry customers are fabless semiconductor companies whose products compete with our own. As a result, our strategy requires us to overcome customer concerns regarding protection of confidentiality information,
intellectual property, and foundry capacity, among other competitive concerns, to attract and retain such customers. Our limited third-party foundry experience also means we must continue to hire and retain talented employees with relevant foundry experience with respect to both leading-edge and
legacy nodes. Our efforts may be hindered by the higher costs of, regulatory and environmental restrictions imposed upon, and time it takes to build fabrication and assembly and test facilities in the jurisdictions in which we operate and plan to build new or upgrade existing foundry facilities as
compared to the jurisdictions in which our competitors predominantly operate their foundry facilities. Our construction projects to expand capacity require available sources of labor, materials and equipment. Increasing demand for such sources, including from other foundries; supply constraints,
labor shortages and other adverse market conditions; issues with permits or approvals; on-site incidents; and other construction issues arise from time to time and can result in significant delays and increased costs for our projects, as well as legal and reputational harm. These significant hurdles
to our foundry",
     "score": 0.5474
    },
    {
     "source": "sec://0000050863-26-000011/unknown#113",
     "title": "INTC FY2025 10-K",
     "content": "conditions; issues with permits or approvals; on-site incidents; and other construction issues arise from time to time and can result in significant delays and increased costs for our projects, as well as legal and reputational harm. These significant hurdles to our foundry strategy
make it highly risky and our success highly uncertain.",
     "score": 0.5819
    },
    {
     "source": "sec://0000050863-26-000011/unknown#119",
     "title": "INTC FY2025 10-K",
     "content": "The investments required for our leading-edge process technology development and our worldwide manufacturing and assembly and test require capital expenditures above our historical levels. In recent years, the semiconductor manufacturing industry has seen very significant increases
in the capital investments required for manufacturing facilities utilizing leading-edge process technologies, including as a result of the use of EUV and high-NA EUV lithography tools. Our ownership and operation of such high-tech fabrication facilities, and our need to build new and expand or
upgrade existing facilities in anticipation of future products and demand, has resulted and will continue to result in our incurring large capital outlays and high costs that are fixed or difficult to reduce in the short term. Such capital outlays and costs include those related to utilization of
existing facilities, facility construction and equipment, R&D, and the employment and training of a highly skilled workforce. To the extent customers are unwilling to pay prices to access the features that our process and product investments are expected to deliver, or if demand for our products,
foundry capacity and assembly and test capacity decreases or we fail to forecast demand accurately, our gross margin and operating income can be disproportionately affected due to our high fixed cost structure, which is difficult to reduce quickly in response to lower demand and other unfavorable
market factors. As we have reassessed demand and our \"shell ahead\" strategy, and our financial results in the last few years have constrained our ability to make capital investments, we have delayed or cancelled manufacturing facility construction or expansion projects in Ohio, Germany, Poland,
Malaysia and Israel and initiated the consolidation of our assembly and test facility in Costa Rica into our other facilities. We could also be required to write off inventory or record excess manufacturing capacity charges, which would also lower our gross margin and operating income. To the extent
the demand decrease is prolonged, our manufacturing or assembly and test capacity could be underutilized, and we may be required to write down our long-lived assets, which would increase our expenses. We may also be required to shorten the useful lives of under-used facilities and equipment and
accelerate depreciation. For example, in 2025 and 2024 we recorded $950 million and $3.3 billion, respectively, of charges related to non-cash impairments and the accelerated depreciation for certain manufacturing assets that were determined to have no remaining or reduced operational use.\n\nIf we
are unable to secure a significant external foundry customer for Intel 14A, our next generation semiconductor manufacturing process technology, we may pause or discontinue our pursuit of next generation leading-edge process technologies.",
     "score": 0.5507
    },
    {
     "source": "sec://0000050863-26-000011/unknown#120",
     "title": "INTC FY2025 10-K",
     "content": "If we are unable to secure a significant external foundry customer for Intel 14A, our next generation semiconductor manufacturing process technology, we may pause or discontinue our pursuit of next generation leading-edge process technologies.\n\nAs an integrated design manufacturer
(IDM) with a products business that depends on access to leading-edge semiconductor manufacturing process technologies, or nodes, to produce competitive products, we have historically invested significant capital resources to continually develop new generations of leading-edge nodes and foundry
capacity to produce such nodes. However, as described above, the design, development and manufacturing of leading-edge nodes is risky and capital-intensive, and it takes years for capital investments to yield a return. If we are unable to secure a significant external customer for our Intel 14A
node, we may pause or discontinue development of Intel 14A and subsequent next generation leading-edge nodes. While we remain focused on continued development of Intel 14A and securing such a significant external customer, we have taken steps to reduce our overall investment and have further slowed
down the construction of the new leading-edge fabrication facilities we are building in Ohio. In addition, while we continue to evaluate Intel 14A for use in future Intel products and our plan includes an initial product designed to utilize Intel 14A, at present we are maintaining the option to
design future Intel products requiring nodes with performance beyond Intel 18A and Intel 18A-P to be produced internally or by an external foundry. We have been unsuccessful to date in securing any significant external foundry customers for any of our nodes and our prospects for securing a
significant external foundry customer for Intel 14A are uncertain.\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| ![intel-logo-footer.jpg](intc-20251227_g2.jpg) | | | Risk Factors | | | 39 | | |\n\n\n\nIf we were to pause or discontinue the design,
development and manufacturing of Intel 14A and other next generation leading-edge nodes, we would be subject to a number of significant strategic business, financial, operational and reputational risks and repercussions including, but not limited to:",
     "score": 0.5506
    },
    {
     "source": "sec://0000050863-26-000011/unknown#121",
     "title": "INTC FY2025 10-K",
     "content": "▪Dependence on Third-Party Foundries. Our products business would, over time, become dependent on third-party foundries, particularly TSMC, as we develop products for nodes beyond Intel 18A and Intel 18A-P. We have no long-term contract with TSMC, and if we are unable to secure and
maintain sufficient capacity on favorable pricing terms, we may be unable to manufacture our products in sufficient volume and at a cost that supports the continued success of our products business. Further, most of our competitors have longer and more established relationships with TSMC and other
third-party foundries than we do, which may put us at a competitive disadvantage. There are few foundries capable of producing the leading-edge and near-leading-edge nodes needed for our products – currently only TSMC and Samsung. To the extent our competitors are more successful than us in securing
capacity with those foundries than we are, our product roadmap, market position and customer relationships would be materially adversely impacted.\n\n▪Losses with Respect to our Investments in R&D and Manufacturing Facilities and Equipment: We had over $100 billion of property, plant and equipment,
net on our balance sheet as of December 27, 2025, the substantial majority of which we estimate relate to our foundry business. While the significant majority of this relates to our existing and in-development nodes, including Intel 18A and Intel 18A-P, with each transition to a new node we continue
to utilize some R&D and manufacturing assets from prior nodes. If we were to pause or discontinue the design, development and manufacturing of Intel 14A and other next generation leading-edge nodes, we would expect to incur significant material impairments with respect to foundry assets that may
impact our results of operations. For example, we would likely discontinue the new leading-edge fabrication facilities we are building in Ohio. We also would expect to incur additional costs and expenses as we wind down other projects and facilities and reduce headcount.\n\n▪Loss of Eligibility for
Government Incentives. We have also entered into government incentive arrangements with local, regional and national governments, both U.S. and non-U.S. If we were to pause or discontinue the design, development and manufacturing of Intel 14A, we may lose eligibility for various incentives
contemplated by these arrangements, and we may be required to repay amounts already received under these arrangements.",
     "score": 0.5808
    },
    {
     "source": "sec://0000050863-26-000011/unknown#123",
     "title": "INTC FY2025 10-K",
     "content": "▪Other Significant Financial, Operational and Reputational Risks. If we pause or discontinue the design, development and manufacture of Intel 14A and future leading-edge nodes, it may give rise to additional material risks that we are not able to foresee or that are more significant
than we anticipate, including, but not limited to, adverse impacts to our relationships and the terms of our engagements with customers, suppliers and strategic partners, potential credit rating risk, and diminished investor confidence and increased stock price volatility. It is also uncertain what
actions, if any, may be taken by the U.S. and other governments to the extent they view a potential discontinuation of our leading-edge process technology design, development and manufacturing as a strategic risk from a national economic or defense perspective.\n\nAny of the foregoing could have a
material adverse impact on our revenue, operations, financial position, cash flows, access to financing, cost structure, competitiveness, reputation, profitability and prospects and could exacerbate other risks discussed in this Form 10-K. Further, given the decades of significant continuous
investments in R&D, talent accumulation, intellectual property, state-of-the-art facilities and technical know-how needed to compete in leading-edge node design, development and manufacturing, any decision to pause or discontinue our pursuit of Intel 14A and successor leading-edge process
technologies may be effectively irreversible.\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| ![intel-logo-footer.jpg](intc-20251227_g2.jpg) | | | Risk Factors | | | 40 | | |\n\n\n\nOur alternative financing arrangements and pursuit of government grants
involve risks and may not be successful.",
     "score": 0.5479
    }
   ]
  }
 ]
}

[tool 3] tavily_financial_search {"query": "Intel INTC recent negative news fundamentals deterioration earnings outlook foundry restructuring", "ticker": "INTC"}
{
 "query": "INTC Intel INTC recent negative news fundamentals deterioration earnings outlook foundry restructuring",
 "results": [
  {
   "title": "Intel (INTC) earnings report Q2 2026",
   "url": "https://www.cnbc.com/2026/07/23/intel-intc-earnings-report-q2-2026.html?taid=6a6274f310d75400018f0789",
   "content": "Despite the recent downturn, the company is getting a boost from the artificial intelligence infrastructure boom, which is helping sales of its server processors. Intel's 25% revenue growth was the fastest for any period in almost 15 years.\n\n\"AI is driving unprecedented demand for
compute,\" CEO Lip-Bu Tan said in the statement. \"As we continue to execute, Intel is well-positioned to capture sustainable growth across our CPU franchise.\" [...] For the current quarter, Intel said it expects adjusted earnings per share of 38 cents on revenue between $15.8 billion and $16.8
billion. Analysts were expecting revenue of $15.1 billion and EPS of 27 cents, according to LSEG.\n\nIntel also said it's starting to craft long-term agreements with customers for its server CPUs, some with pricing locked in and others focused on chip volume. [...] Intel is boosting its capital
expenditures, targeting a \"meaningful increase\" next year, as it aggressively tries to morph into a manufacturer of chips for other companies. Zinsner told CNBC's Kristina Partsinevelos that the company's latest manufacturing process, called 14A, is ahead of where older technologies were at the
same point in the cycle. Intel said its foundry reported $5.8 billion in sales, up 31% on an annual basis.",
   "published_date": null
  },
  {
   "title": "Intel (INTC) earnings report Q2 2026",
   "url": "https://cnbc.com/2026/07/23/intel-intc-earnings-report-q2-2026.html",
   "content": "Despite the recent downturn, the company is getting a boost from the artificial intelligence infrastructure boom, which is helping sales of its server processors. Intel's 25% revenue growth was the fastest for any period in almost 15 years.\n\n\"AI is driving unprecedented demand for
compute,\" CEO Lip-Bu Tan said in the statement. \"As we continue to execute, Intel is well-positioned to capture sustainable growth across our CPU franchise.\" [...] For the current quarter, Intel said it expects adjusted earnings per share of 38 cents on revenue between $15.8 billion and $16.8
billion. Analysts were expecting revenue of $15.1 billion and EPS of 27 cents, according to LSEG.\n\nIntel also said it's starting to craft long-term agreements with customers for its server CPUs, some with pricing locked in and others focused on chip volume. [...] Intel is boosting its capital
expenditures, targeting a \"meaningful increase\" next year, as it aggressively tries to morph into a manufacturer of chips for other companies. Zinsner told CNBC's Kristina Partsinevelos that the company's latest manufacturing process, called 14A, is ahead of where older technologies were at the
same point in the cycle. Intel said its foundry reported $5.8 billion in sales, up 31% on an annual basis.",
   "published_date": null
  },
  {
   "title": "Intel (INTC) earnings report Q2 2026",
   "url": "https://www.cnbc.com/2026/07/23/intel-intc-earnings-report-q2-2026.html?stream=top",
   "content": "Despite the recent downturn, the company is getting a boost from the artificial intelligence infrastructure boom, which is helping sales of its server processors. Intel's 25% revenue growth was the fastest for any period in almost 15 years.\n\n\"AI is driving unprecedented demand for
compute,\" CEO Lip-Bu Tan said in the statement. \"As we continue to execute, Intel is well-positioned to capture sustainable growth across our CPU franchise.\" [...] For the current quarter, Intel said it expects adjusted earnings per share of 38 cents on revenue between $15.8 billion and $16.8
billion. Analysts were expecting revenue of $15.1 billion and EPS of 27 cents, according to LSEG.\n\nIntel also said it's starting to craft long-term agreements with customers for its server CPUs, some with pricing locked in and others focused on chip volume. [...] Intel is boosting its capital
expenditures, targeting a \"meaningful increase\" next year, as it aggressively tries to morph into a manufacturer of chips for other companies. Zinsner told CNBC's Kristina Partsinevelos that the company's latest manufacturing process, called 14A, is ahead of where older technologies were at the
same point in the cycle. Intel said its foundry reported $5.8 billion in sales, up 31% on an annual basis.",
   "published_date": null
  },
  {
   "title": "Intel (INTC) earnings report Q2 2026",
   "url": "https://www.cnbc.com/2026/07/23/intel-intc-earnings-report-q2-2026.html",
   "content": "Despite the recent downturn, the company is getting a boost from the artificial intelligence infrastructure boom, which is helping sales of its server processors. Intel's 25% revenue growth was the fastest for any period in almost 15 years.\n\n\"AI is driving unprecedented demand for
compute,\" CEO Lip-Bu Tan said in the statement. \"As we continue to execute, Intel is well-positioned to capture sustainable growth across our CPU franchise.\" [...] For the current quarter, Intel said it expects adjusted earnings per share of 38 cents on revenue between $15.8 billion and $16.8
billion. Analysts were expecting revenue of $15.1 billion and EPS of 27 cents, according to LSEG.\n\nIntel also said it's starting to craft long-term agreements with customers for its server CPUs, some with pricing locked in and others focused on chip volume. [...] Intel is boosting its capital
expenditures, targeting a \"meaningful increase\" next year, as it aggressively tries to morph into a manufacturer of chips for other companies. Zinsner told CNBC's Kristina Partsinevelos that the company's latest manufacturing process, called 14A, is ahead of where older technologies were at the
same point in the cycle. Intel said its foundry reported $5.8 billion in sales, up 31% on an annual basis.",
   "published_date": null
  },
  {
   "title": "Intel (INTC) earnings report Q2 2026",
   "url": "https://www.cnbc.com/amp/2026/07/23/intel-intc-earnings-report-q2-2026.html",
   "content": "Despite the recent downturn, the company is getting a boost from the artificial intelligence infrastructure boom, which is helping sales of its server processors. Intel's 25% revenue growth was the fastest for any period in almost 15 years.\n\n\"AI is driving unprecedented demand for
compute,\" CEO Lip-Bu Tan said in the statement. \"As we continue to execute, Intel is well-positioned to capture sustainable growth across our CPU franchise.\" [...] For the current quarter, Intel said it expects adjusted earnings per share of 38 cents on revenue between $15.8 billion and $16.8
billion. Analysts were expecting revenue of $15.1 billion and EPS of 27 cents, according to LSEG.\n\nIntel also said it's starting to craft long-term agreements with customers for its server CPUs, some with pricing locked in and others focused on chip volume. [...] Intel is boosting its capital
expenditures, targeting a \"meaningful increase\" next year, as it aggressively tries to morph into a manufacturer of chips for other companies. Zinsner told CNBC's Kristina Partsinevelos that the company's latest manufacturing process, called 14A, is ahead of where older technologies were at the
same point in the cycle. Intel said its foundry reported $5.8 billion in sales, up 31% on an annual basis.",
   "published_date": null
  }
 ]
}

[tool 4] tavily_financial_search {"query": "Intel INTC latest 2025 2026 restructuring foundry losses 14A external customer negative news", "ticker": "INTC"}
{
 "query": "INTC Intel INTC latest 2025 2026 restructuring foundry losses 14A external customer negative news",
 "results": [
  {
   "title": "Intel (INTC) earnings report Q4 2025",
   "url": "https://www.cnbc.com/2026/01/22/intel-intc-earnings-report-q4-2025-.html?msockid=28de8eef69646cb83901980268946de1",
   "content": "Zinsner told CNBC that customers for Intel's next-generation 14A technology would show up in the second half of the year. Zinsner added that the company was unlikely to announce customers in general.\n\n\"Once we get them, we're gonna need to start really spending capital on the 14A
front, and that's how you'll know,\" Zinsner said.\n\nIntel said its foundry had $4.5 billion in revenue, although some of that is accounting for making the company's own chips. [...] On a call with analysts, CEO Lip-Bu Tan said that the company was looking to improve its production efficiency,
called yield, in order to improve supply of the company's products.\n\n\"Our yields are in line with our internal plans,\" Tan said. \"They are still below what I want them to be.\"\n\nThe company said it had a net loss of $600 million, or 12 cents per diluted share. In the year-ago period, Intel
reported a net loss of $100 million, or 3 cents per share. [...] Investor expectations were high for Intel heading into the report, with the stock up 147% in the past year. The rally has been driven by optimism that Intel may be on the cusp of securing its first major anchor customer for its foundry
business, which manufactures chips for other companies.",
   "published_date": null
  },
  {
   "title": "Intel (INTC) earnings report Q4 2025",
   "url": "https://www.cnbc.com/2026/01/22/intel-intc-earnings-report-q4-2025-.html?msockid=0d59194b98db6b0804550fa699026aab",
   "content": "Zinsner told CNBC that customers for Intel's next-generation 14A technology would show up in the second half of the year. Zinsner added that the company was unlikely to announce customers in general.\n\n\"Once we get them, we're gonna need to start really spending capital on the 14A
front, and that's how you'll know,\" Zinsner said.\n\nIntel said its foundry had $4.5 billion in revenue, although some of that is accounting for making the company's own chips. [...] On a call with analysts, CEO Lip-Bu Tan said that the company was looking to improve its production efficiency,
called yield, in order to improve supply of the company's products.\n\n\"Our yields are in line with our internal plans,\" Tan said. \"They are still below what I want them to be.\"\n\nThe company said it had a net loss of $600 million, or 12 cents per diluted share. In the year-ago period, Intel
reported a net loss of $100 million, or 3 cents per share.",
   "published_date": null
  },
  {
   "title": "Intel (INTC) earnings report Q4 2025",
   "url": "https://www.cnbc.com/2026/01/22/intel-intc-earnings-report-q4-2025-.html",
   "content": "Zinsner told CNBC that customers for Intel's next-generation 14A technology would show up in the second half of the year. Zinsner added that the company was unlikely to announce customers in general.\n\n\"Once we get them, we're gonna need to start really spending capital on the 14A
front, and that's how you'll know,\" Zinsner said.\n\nIntel said its foundry had $4.5 billion in revenue, although some of that is accounting for making the company's own chips. [...] On a call with analysts, CEO Lip-Bu Tan said that the company was looking to improve its production efficiency,
called yield, in order to improve supply of the company's products.\n\n\"Our yields are in line with our internal plans,\" Tan said. \"They are still below what I want them to be.\"\n\nThe company said it had a net loss of $600 million, or 12 cents per diluted share. In the year-ago period, Intel
reported a net loss of $100 million, or 3 cents per share.",
   "published_date": null
  },
  {
   "title": "Intel (INTC) earnings report Q4 2025",
   "url": "https://www.cnbc.com/2026/01/22/intel-intc-earnings-report-q4-2025-.html?msockid=2eacd6ad832a6e3800b8c19f82246f73",
   "content": "Zinsner told CNBC that customers for Intel's next-generation 14A technology would show up in the second half of the year. Zinsner added that the company was unlikely to announce customers in general.\n\n\"Once we get them, we're gonna need to start really spending capital on the 14A
front, and that's how you'll know,\" Zinsner said.\n\nIntel said its foundry had $4.5 billion in revenue, although some of that is accounting for making the company's own chips. [...] On a call with analysts, CEO Lip-Bu Tan said that the company was looking to improve its production efficiency,
called yield, in order to improve supply of the company's products.\n\n\"Our yields are in line with our internal plans,\" Tan said. \"They are still below what I want them to be.\"\n\nThe company said it had a net loss of $600 million, or 12 cents per diluted share. In the year-ago period, Intel
reported a net loss of $100 million, or 3 cents per share.",
   "published_date": null
  },
  {
   "title": "Intel (INTC) earnings report Q4 2025",
   "url": "https://www.cnbc.com/2026/01/22/intel-intc-earnings-report-q4-2025-.html?msockid=2c1c0190788c69063520168179176860",
   "content": "Zinsner told CNBC that customers for Intel's next-generation 14A technology would show up in the second half of the year. Zinsner added that the company was unlikely to announce customers in general.\n\n\"Once we get them, we're gonna need to start really spending capital on the 14A
front, and that's how you'll know,\" Zinsner said.\n\nIntel said its foundry had $4.5 billion in revenue, although some of that is accounting for making the company's own chips. [...] On a call with analysts, CEO Lip-Bu Tan said that the company was looking to improve its production efficiency,
called yield, in order to improve supply of the company's products.\n\n\"Our yields are in line with our internal plans,\" Tan said. \"They are still below what I want them to be.\"\n\nThe company said it had a net loss of $600 million, or 12 cents per diluted share. In the year-ago period, Intel
reported a net loss of $100 million, or 3 cents per share.",
   "published_date": null
  }
 ]
}
----- END EVIDENCE F0087 -----

----- BEGIN ANSWER F0087 -----
**結論：是，英特爾的負面新聞已經有相當部分被財報與 10-K 的硬數據印證；但更準確的說法是「基本面仍在修復與轉型危機中」，而不是已經證明公司將不可逆崩潰。**

### 已被基本面印證的惡化

1. **晶圓代工業務仍是主要拖累。**  
   Intel FY2025 10-K（截至 2025-12-27）顯示，Intel Foundry 營收為 **178.26 億美元**，但營運虧損仍高達 **103.18 億美元**，營業利益率為 **-58%**。[1] 這不是單一季度新聞，而是結構性的商業模式問題。

2. **公司持續為產能過剩與製程資產減值付出代價。**  
   2025 年因部分製造資產被認定沒有剩餘營運用途，Intel 認列約 **9.5 億美元**相關費用；2024 年則有約 **33 億美元**的製造資產減值及加速折舊。[2] 公司也表示，現有製造資產組合超過預期需求，因此縮短部分設備的使用年限並加速折舊。[3]

3. **14A 與外部晶圓代工客戶仍是關鍵未解風險。**  
   Intel 在 10-K 中明確表示，截至申報時，尚未為其任何製程取得具重大規模的外部晶圓代工客戶；若無法為 14A 找到重要客戶，可能暫停或終止下一代先進製程的追求。[4] 這代表市場最關注的「Intel 能否成為真正的第三方晶圓代工廠」，目前仍是高度不確定的選擇權，而非已證實的成長引擎。

4. **高固定成本讓下行風險被放大。**  
   Intel 表示，先進製程與晶圓廠需要大量、且短期難以削減的資本支出與固定成本；若需求不足或客戶不願支付相應價格，毛利率與營業利益可能受到不成比例的打擊。[5]

### 但也不能把所有負面新聞解讀成「全面崩壞」

- Finnhub 的即時基本面資料顯示，Intel TTM 營收仍有 **7.47% 年增**，流動比率約 **1.60**、速動比率約 **1.25**，因此目前不能只憑負面新聞就判定公司已出現立即性的流動性危機。  
- 不過，同一份資料也顯示 TTM **EPS 為 -2.12 美元**、淨利率 **-19.79%**、ROE **-10.76%**、ROA **-5.48%**。換言之，營收有回升，不代表盈利能力已經恢復。  
- 根據 Finnhub 即時報價，INTC 目前約為 **92.90 美元**，當日上漲約 **2.69%**；股價短期上漲本身不能證明基本面改善，可能反映市場對轉型、政策支持或未來客戶落地的預期。

### 負面新聞中最值得重視的部分

近期 CNBC 對 Intel 2025 年第四季的報導指出，Intel Foundry 當季營收約 **45 億美元**，但其中部分來自替 Intel 自己生產晶片；管理層也表示製造良率雖符合內部計畫，仍低於理想水準。報導同時提到，市場仍在等待 Intel 是否能取得 14A 的主要外部客戶。[6]

這說明市場目前交易的不是「已經證明的代工成功」，而是：

- 18A／14A 良率能否持續改善；
- 是否能取得具規模的外部代工客戶；
- Foundry 虧損何時能明顯收斂；
- 資本支出與產能是否會再次造成大額減值；
- CPU 業務能否抵消 AI 加速器與伺服器市場的競爭壓力。

### 我的判斷

**基本面惡化已經足夠被確認，尤其是在獲利能力、晶圓代工經濟性、製造資產利用率與資本配置方面。** 但目前證據比較支持「高風險轉型股」的判斷，而不是「已經失去翻身可能」。

對投資判斷而言，接下來最重要的不是單看新聞數量，而是觀察三項可驗證指標：

1. Foundry 營業虧損是否連續收窄；  
2. Intel 14A 是否取得真正具規模的外部客戶；  
3. 減值、加速折舊與重組費用是否再次大幅增加。

如果這三項沒有改善，即使營收暫時成長或股價反彈，仍較像是市場在提前交易希望，而不是基本面已完成反轉。

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: https://www.cnbc.com/2026/01/22/intel-intc-earnings-report-q4-2025-.html "Intel (INTC) earnings report Q4 2025"
----- END ANSWER F0087 -----

===== ITEM F0088 =====

QUESTION:
分析在歐盟和美國對大型平台管得更嚴的新局下，蘋果跟 Meta 哪家的直接商業衝擊比較大。

----- BEGIN EVIDENCE F0088 -----
[tool 0] sec_filing_search {"query": "EU Digital Markets Act DMA US antitrust regulation platform regulation direct business impact fines advertising privacy compliance", "ticker": "META", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "META",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from META FY2025 10-K, Item 1A (Risk Factors) — 8 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-003942/1a#23",
     "title": "META FY2025 10-K · Item 1A · Risks Related to Government Regulation and Enforcement",
     "content": "### Risks Related to Government Regulation and Enforcement\n\n•government restrictions on access to Facebook or our other products, or other actions that impair our ability to sell or deliver advertising, in their countries;\n\n•complex and evolving U.S. and foreign privacy, data
use, data combination, data protection, content and content moderation, competition, youth, safety, consumer protection, advertising, and other laws and regulations, including the General Data Protection Regulation (GDPR), Digital Markets Act (DMA), Digital Services Act (DSA), UK Online Safety Act
(OSA), Artificial Intelligence Act (EU AI Act), and the UK Digital Markets, Competition and Consumer Act (DMCC);\n\n•the impact of government investigations, enforcement actions, and settlements, including litigation and investigations by privacy, consumer protection, and competition authorities,
among others;\n\n12\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)\n\n•our ability to comply with regulatory and legislative privacy requirements, including our consent order with the Federal Trade Commission (FTC);",
     "score": 0.6052,
     "subsection": "Risks Related to Government Regulation and Enforcement"
    },
    {
     "source": "sec://0001628280-26-003942/1a#34",
     "title": "META FY2025 10-K · Item 1A",
     "content": "Our ad targeting and measurement tools rely on data signals from user activity on websites and services that we do not control, as well as signals generated within our products, in order to deliver relevant and effective ads to our users, and any changes in our ability to use such
signals will adversely affect our business. For example, legislative and regulatory developments, such as the GDPR, ePrivacy Directive, DMA, and U.S. state privacy laws, have impacted, and we expect will continue to impact, our ability to use such signals in our ad products. In particular, we have
seen increases in the number of users opting to control certain types of ad targeting in Europe following product changes implemented in connection with our GDPR and ePrivacy Directive compliance, and we have introduced product changes that limit data signal use for users in certain U.S. states
following adoption of state privacy laws. A number of U.S. state privacy laws have introduced additional rights for users and could result in restrictions on our use of signals from third-party apps and websites through certain browser- and device-based universal opt-out mechanisms. Judicial and
regulatory guidance, decisions, or enforcement actions, or new legislation in these or other jurisdictions may require us to make additional changes to our products in the future that further reduce our ability to use these signals, which has occurred in the past. For example, in response to
regulatory developments in Europe, we announced plans to change the legal basis for behavioral advertising on Facebook and Instagram in the European Union, European Economic Area, and Switzerland from \"legitimate interests\" to \"consent,\" and in November 2023 we began offering users in the region
a \"subscription for no ads\" alternative. We are engaging with regulators on our consent model, including regarding compliance with requirements under the GDPR, DMA, and EU consumer laws. For example, in March 2024, the European Commission opened formal proceedings regarding the compliance of our
\"subscription for no ads\" model with requirements under the DMA, and it issued preliminary findings in July 2024. In addition, the European Data Protection Board has published an opinion on the operation of such models under GDPR and European consumer protection organizations have raised concerns
regarding our compliance with consumer protection laws. In response to these developments, in November 2024, we began offering users in the European Union, European Economic Area, and Switzerland who elect to continue using our services free-of-charge, supported by ads, an option to see less
personalized ads (LPA), which are less relevant and effective than our premium ad offerings. In April",
     "score": 0.5905
    },
    {
     "source": "sec://0001628280-26-003942/1a#89",
     "title": "META FY2025 10-K · Item 1A",
     "content": "We have been subject to other significant legislative and regulatory developments, which together with proposed or new legislation and regulations could significantly affect our business in the future. For example, we have implemented a number of product changes and controls as a
result of requirements under the European General Data Protection Regulation (GDPR), and may implement additional changes in the future. The GDPR also requires submission of personal data breach notifications to our lead European Union privacy regulator, the IDPC, and includes significant penalties
for non-compliance with the notification obligation as well as other requirements of the regulation. The interpretation of the GDPR is still evolving, including through decisions of the CJEU, and draft decisions in investigations by the IDPC are subject to review by other European privacy regulators
as part of the GDPR's consistency mechanism, which may lead to significant changes in the final outcome of such investigations. We also face potential enforcement from European privacy regulators other than the IDPC, including where those regulators consider they must act urgently or where they
believe their concerns relate only to data processing undertaken in their individual jurisdiction. As a result, the interpretation and enforcement of the GDPR, as well as the imposition and amount of penalties for non-compliance, are subject to significant uncertainty, and as it evolves, could
potentially have a negative impact on our business and/or our operations. In addition, Brazil, the United Kingdom, and other countries have enacted similar data protection regulations imposing data privacy-related requirements on products and services offered to users in their respective
jurisdictions. The California Consumer Privacy Act, as amended by the California Privacy Rights Act, also establishes certain transparency rules and creates certain data privacy rights for users, including limitations on our use of certain sensitive personal information and more ability for users to
control the purposes for which their data is shared with third parties. Other states have proposed or enacted similar comprehensive privacy laws that afford users with similar data privacy rights and controls. These laws and regulations are evolving and subject to interpretation, and resulting
limitations on our advertising services, or reductions of advertising by marketers, have to some extent adversely affected, and will continue to adversely affect, our advertising business. Some states have also proposed or enacted laws specifically focused on whether and how a company can moderate
content on its services, and/or on the privacy rights and controls for users under 18 years old and their parents or guardians. Like comprehensive privacy laws, these laws are evolving and subject to interpretation, and may restrict our ability to offer certain products and services provided to all
or certain cohorts of users in those states, adversely affecting our advertising business. In Europe, evolving interpretation",
     "score": 0.5796
    },
    {
     "source": "sec://0001628280-26-003942/1a#90",
     "title": "META FY2025 10-K · Item 1A",
     "content": "guardians. Like comprehensive privacy laws, these laws are evolving and subject to interpretation, and may restrict our ability to offer certain products and services provided to all or certain cohorts of users in those states, adversely affecting our advertising business. In
Europe, evolving interpretation of the ePrivacy Directive's requirements regarding the use of cookies and similar technologies may lead to regulators imposing specific measures in the future which could directly impact our use of such technologies. In addition, the ePrivacy Directive and national
implementation laws impose additional limitations on the use of data across messaging products and include significant penalties for non-compliance. Changes to our products or business practices as a result of these or similar developments have adversely affected, and may in the future adversely
affect, our advertising business. For example, in response to regulatory developments in Europe, we announced plans to change the legal basis for behavioral advertising on Facebook and Instagram in the European Union, European Economic Area, and Switzerland from \"legitimate interests\" to
\"consent,\" and in November 2023 we began offering users in the region a \"subscription for no ads\" alternative. We are engaging with regulators on our consent model, including regarding compliance with requirements under the GDPR, DMA, and EU consumer laws. For example, in March 2024, the
European Commission opened formal proceedings regarding the compliance of our \"subscription for no ads\" model with requirements under the DMA, and it issued preliminary findings in July 2024. In addition, the European Data Protection Board has published an opinion on the operation of such models
under GDPR and European consumer protection organizations have raised concerns regarding our compliance with consumer protection laws. In response to these developments, in November 2024, we began offering users in the European Union, European Economic Area, and Switzerland who elect to continue
using our services free-of-charge, supported by ads, an option to see less personalized ads (LPA), which are less relevant and effective than our premium ad offerings. In April 2025, the European Commission issued a final decision that our \"subscription for no ads\" model does not comply with such
requirements. We made significant modifications to LPA since the European Commission issued its final decision. We have appealed the European Commission's decision but further modifications to our model may be imposed during the appeal process, which could result in a materially worse user
experience for European users and a significant impact to our European business and revenue. These or any similar developments in the future may negatively impact our user growth and engagement, revenue, and financial results.",
     "score": 0.6061
    },
    {
     "source": "sec://0001628280-26-003942/1a#91",
     "title": "META FY2025 10-K · Item 1A",
     "content": "Similarly, there are a number of legislative proposals or recently enacted laws in the European Union, the United States, at both the federal and state level, as well as other jurisdictions that could impose new obligations or limitations in areas affecting our business. For
example, the DMA in the European Union imposes restrictions and requirements on companies like ours, including in areas such as the combination of data across services, mergers and acquisitions, and product design. The DMA also includes significant penalties for non-compliance, and its key
requirements are enforceable against designated gatekeeper companies as of March 2024. The DMA has caused, and may in the future cause, us to incur significant compliance costs and make changes to our products or business practices. The requirements under the DMA will likely be subject to further
interpretation and regulatory engagement. Pending or future proposals to modify competition laws\n\n38\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)",
     "score": 0.7109
    },
    {
     "source": "sec://0001628280-26-003942/1a#92",
     "title": "META FY2025 10-K · Item 1A",
     "content": "in a number of jurisdictions could have similar effects. Further, the DSA, which started to apply to our business as of August 2023, imposes certain restrictions and requirements for our products and services, subjects us to increased compliance costs, and includes significant
penalties for non-compliance. In the UK, the OSA establishes similar types of obligations. The interpretation and enforcement of the DMA, DSA, and OSA, as well as the imposition and amount of penalties for non-compliance, are subject to significant uncertainty. In addition, some countries, such as
the UK, India, and Turkey, are considering or have passed legislation implementing data protection requirements, new competition requirements, or requiring local storage and processing of data or similar requirements that could require substantial changes to our products, increase the cost and
complexity of delivering our services, cause us to cease the offering of our products and services in certain countries, and/or result in fines or other penalties. We are also subject to new legislation or regulatory decisions that restrict our ability to collect and use information about minors or
also limit our advertising services or our ability to offer products and services to minors in certain jurisdictions. For example, several U.S. states, including Arkansas, California, Colorado, Florida, New York, Texas, and Utah, among others, have passed laws restricting our ability to offer
services to minors without parental consent or otherwise limiting the services that we can provide to minors. While enforcement of a number of these statutes (or parts of them) has been enjoined or stayed as a result of legal challenges to them, it is possible that the decisions to enjoin these
statutes may be overturned, the injunctive orders may expire, and certain statutes are coming into effect that may not be subject to injunctions. Should enforcement of one or more of these statutes not be enjoined, we may not be able to comply with certain of these statutes by their respective
effective dates. We are facing similar challenges in other jurisdictions, including Europe, Latin America, and Asia-Pacific. For example, various EU member states are currently considering a range of legislation from mandatory age verification requirements to banning minor access to social media
services. In addition, recent legislation in Australia imposes a social media ban for users under 16 years old, requiring certain social media companies to take reasonable steps to ensure under 16 year olds do not hold user accounts. As a result of legislative proposals, new laws, and evolving
interpretation of existing laws in Europe, Asia-Pacific, Latin America, and other jurisdictions, we are also, and expect to",
     "score": 0.598
    },
    {
     "source": "sec://0001628280-26-003942/1a#98",
     "title": "META FY2025 10-K · Item 1A",
     "content": "We are also subject to various litigation and formal and informal inquiries and investigations by competition authorities in the United States, Europe, and other jurisdictions, which relate to many aspects of our business, including with respect to users and advertisers. Such
inquiries, investigations, and lawsuits concern, among other things, our business practices in the areas of social networking or social media services, messaging services, digital advertising, and/or mobile or online applications, as well as our acquisitions. For example, beginning in 2019, we
became the subject of antitrust inquiries and investigations by the FTC and the U.S. Department of Justice. Beginning in 2020, we became subject to a lawsuit by the FTC alleging that we violated antitrust laws, including by acquiring Instagram in 2012 and WhatsApp in 2014. The complaint seeks a
permanent injunction against our company's alleged violations of the antitrust laws, and other equitable relief, including divestiture or reconstruction of Instagram and WhatsApp. In addition, in November 2024, the European Commission issued a fine as a result of its finding that we tied Facebook
Marketplace to Facebook and use data in a manner that infringes European Union competition rules. We are also subject to other government inquiries and investigations relating to our business activities and disclosure practices. For example, beginning in September 2021, we became subject to
government investigations and requests relating to allegations and the release of internal company documents by a former employee.\n\n\nOrders issued by, or inquiries or enforcement actions initiated by, government or regulatory authorities could cause us to incur substantial costs, expose us to
civil and criminal liability (including liability for our personnel) or penalties (including substantial monetary remedies), interrupt or require us to change our business practices in a manner materially adverse to our business (including changes to our products or user data practices), result in
negative publicity and reputational harm, divert resources and the time and attention of management from our business, or subject us to other structural or behavioral remedies that adversely affect our business, and we have experienced some of these adverse effects to varying degrees from time to
time.\n\nCompliance with our FTC consent order, the GDPR, U.S. state privacy laws, youth social media laws, the ePrivacy Directive, the DMA, the DSA, the OSA, and other regulatory and legislative privacy requirements require significant operational resources and modifications to our business
practices, and any compliance failures may have a material adverse effect on our business, reputation, and financial results.",
     "score": 0.5624
    },
    {
     "source": "sec://0001628280-26-003942/1a#99",
     "title": "META FY2025 10-K · Item 1A",
     "content": "We are engaged in ongoing privacy compliance and oversight efforts, including in connection with our modified consent order with the FTC, requirements of the GDPR and UK GDPR, and other current and anticipated regulatory and legislative requirements around the world, such as U.S.
state privacy laws, youth social media laws, the ePrivacy Directive,\n\n40\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)\n\nDMA, DSA, OSA, EU AI Act, the Korean Personal Information Protection Act, and the Indian Digital Personal Data Protection Act. In particular, we are
maintaining a comprehensive privacy program in connection with the FTC consent order that includes substantial management and board of directors oversight, stringent operational requirements and reporting obligations, prohibitions against making misrepresentations relating to user data, a process to
regularly certify our compliance with the privacy program to the FTC, and regular assessments of our privacy program by an independent third-party assessor, which has been and will continue to be challenging and costly to maintain and enhance. These compliance and oversight efforts are increasing
demand on our systems and resources, and require significant new and ongoing investments, including investments in compliance processes, personnel, and technical infrastructure. We continually reallocate resources internally to assist with these efforts, and this has had, and will continue to have,
an adverse impact on our other business initiatives. In addition, these efforts require substantial modifications to our business practices and make some practices such as product and ads development more difficult, time-consuming, and costly. As a result, we believe our ability to develop and
launch new features, products, and services in a timely manner has been and will continue to be adversely affected. Further, our privacy compliance and oversight efforts have required, and we expect will continue to require, significant time and attention from our management and board of directors.
The requirements of the FTC consent order and other privacy-related laws and regulations are complex and apply broadly to our business, and from time to time we notify relevant authorities of instances where we are not in full compliance with these requirements or otherwise discover privacy issues,
and we expect to continue to do so as any such issues arise in the future. In addition, regulatory and legislative privacy requirements are constantly evolving and can be subject to significant change and uncertain interpretation. For example, we are subject to restrictions and requirements under
the DMA, including in areas such as the combination of data across services and product design, which will likely be subject to further interpretation and regulatory engagement.",
     "score": 0.5924
    }
   ]
  },
  {
   "ticker": "META",
   "fiscal_year": 2025,
   "item": "Item 8",
   "prelude": "Excerpts from META FY2025 10-K, Item 8 (Financial Statements and Supplementary Data) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-003942/8#362",
     "title": "META FY2025 10-K · Item 8",
     "content": "In March 2024, the European Commission opened an investigation into the compliance of our \"subscription for no ads\" consent model with requirements under Article 5(2) of the Digital Markets Act (DMA). The European Commission issued preliminary findings on July 1, 2024 reflecting
its preliminary view that our model does not comply with such requirements. In April 2025, the European Commission issued a final decision that our \"subscription for no ads\" model does not comply with such requirements and imposed a fine of EUR €200 million. Based on feedback from the European
Commission in connection with the DMA, we launched less personalized ads (LPA) in November 2024 and made significant modifications to LPA since the European Commission issued its final decision. We appealed the European Commission's decision on July 4, 2025, but further modifications to our model
may be imposed during the appeal process, which could result in a materially worse user experience for European users and a significant impact to our European business and revenue.\n\n\n115\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)\n\nSecurities and Other Actions",
     "score": 0.6664
    }
   ]
  },
  {
   "ticker": "META",
   "fiscal_year": 2025,
   "item": "Item 3",
   "prelude": "Excerpts from META FY2025 10-K, Item 3 (Legal Proceedings) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-003942/3#142",
     "title": "META FY2025 10-K · Item 3",
     "content": "54\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)\n\nIn March 2024, the European Commission opened an investigation into the compliance of our \"subscription for no ads\" consent model with requirements under Article 5(2) of the Digital Markets Act (DMA). The
European Commission issued preliminary findings on July 1, 2024 reflecting its preliminary view that our model does not comply with such requirements. In April 2025, the European Commission issued a final decision that our \"subscription for no ads\" model does not comply with such requirements and
imposed a fine of EUR €200 million. Based on feedback from the European Commission in connection with the DMA, we launched less personalized ads (LPA) in November 2024 and made significant modifications to LPA since the European Commission issued its final decision. We appealed the European
Commission's decision on July 4, 2025, but further modifications to our model may be imposed during the appeal process, which could result in a materially worse user experience for European users and a significant impact to our European business and revenue.\n\n\nThe result of such litigation,
investigations or inquiries could subject us to substantial monetary remedies and costs, interrupt or require us to change our business practices, divert resources and the attention of management from our business, or subject us to other structural or behavioral remedies that adversely affect our
business.",
     "score": 0.6532
    }
   ]
  }
 ]
}

[tool 1] sec_filing_search {"query": "EU Digital Markets Act DMA US antitrust regulation platform regulation direct business impact fines app store advertising privacy compliance", "ticker": "AAPL", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-09-27",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 1A (Risk Factors) — 8 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/1a#31",
     "title": "AAPL FY2025 10-K · Item 1A · Legal and Regulatory Compliance Risks",
     "content": "### Legal and Regulatory Compliance Risks\n\nThe Company’s business, results of operations and financial condition could be adversely impacted by unfavorable results of legal proceedings or government investigations.\n\nThe Company is subject to various claims, legal proceedings and
government investigations that have arisen in the ordinary course of business and have not yet been fully resolved, and new matters may arise in the future. In addition, the Company enters into agreements that include indemnification provisions that can subject the Company to costs and damages in
the event of a claim against an indemnified third party. The number of claims, legal proceedings and government investigations involving the Company, and the alleged magnitude of such claims, proceedings and government investigations, has generally increased over time and may continue to
increase.\n\nThe Company has faced and continues to face a significant number of patent claims relating to its standards-enabled products, and new claims may arise in the future, including as a result of new legal or regulatory frameworks. For example, technology, data and other intellectual
property asset–holding companies frequently assert their intellectual property rights and seek royalties and often enter into litigation based on allegations of infringement or other violations of intellectual property rights. These risks, and the risks of novel claims being attempted, may be
exacerbated as new and emerging technologies, including machine learning and artificial intelligence, are further integrated into the Company’s products and services. The Company is vigorously defending infringement actions in courts in several U.S. jurisdictions, as well as internationally in
various countries. The plaintiffs in these actions frequently seek broad injunctive relief and substantial damages.\n\nRegardless of the merit of particular claims, defending against litigation or responding to government investigations can be expensive, time-consuming and disruptive to the
Company’s operations. In recognition of these considerations, the Company may enter into agreements or other arrangements to settle litigation and resolve such challenges. However, such agreements may not always be available on acceptable terms, and litigation may still arise. Such agreements can
also significantly reduce the Company’s revenue and increase the Company’s cost of sales and operating expenses, materially adversely affecting the Company’s business, results of operations, financial condition and stock price. Additionally, such agreements may require the Company to change its
business practices and limit the Company’s ability to offer certain products and services.\n\nApple Inc. | 2025 Form 10-K | 12",
     "score": 0.4773,
     "subsection": "Legal and Regulatory Compliance Risks"
    },
    {
     "source": "sec://0000320193-25-000079/1a#32",
     "title": "AAPL FY2025 10-K · Item 1A",
     "content": "Apple Inc. | 2025 Form 10-K | 12\n\n\n\nThe outcome of litigation or government investigations is inherently uncertain. If one or more legal matters were resolved against the Company or an indemnified third party in a reporting period for amounts above management’s expectations, the
Company’s results of operations, financial condition and stock price for that reporting period could be materially adversely affected. Further, such an outcome can result in significant monetary damages, disgorgement of revenue or profits, remedial corporate measures or injunctive relief against the
Company. Adverse resolution of legal matters has from time to time required, and can in the future require, the Company to change its business practices. It can also limit the Company’s ability to enjoin others from using, or to derive value from, its intellectual property rights, and to develop,
manufacture, use, import or offer for sale certain products and services, all of which could materially adversely affect the Company’s business, reputation, results of operations, financial condition and stock price.\n\nWhile the Company maintains insurance coverage for certain types of claims, such
insurance coverage may be insufficient to cover all losses or all types of claims that may arise.\n\nThe Company is subject to complex and changing laws and regulations worldwide, which exposes the Company to potential liabilities, increased costs and other adverse effects on the Company’s
business.\n\nThe Company’s global operations are subject to complex and changing laws and regulations worldwide on subjects including antitrust; privacy, data security and data localization; online safety; age verification; consumer protection; advertising, sales, billing and e-commerce; financial
services and technology; product liability; intellectual property ownership and infringement; digital platforms; machine learning and artificial intelligence; internet, telecommunications and mobile communications; media, television, film and digital content; availability of third-party software
applications and services; labor and employment; anticorruption; import, export and trade; foreign exchange controls and cash repatriation restrictions; anti–money laundering; foreign ownership and investment; national security; tax; and environmental, health and safety, including electronic waste,
recycling, product design and climate change.",
     "score": 0.4621
    },
    {
     "source": "sec://0000320193-25-000079/1a#33",
     "title": "AAPL FY2025 10-K · Item 1A",
     "content": "Compliance with these laws and regulations is onerous and expensive. New and changing laws, regulations, executive orders, directives, and enforcement priorities can adversely affect the Company’s business by increasing the Company’s costs, limiting the Company’s ability to offer a
product, service or feature to customers, imposing changes to the design of the Company’s products and services, impacting customer demand for the Company’s products and services, and requiring changes to the Company’s business or supply chain. New and changing laws, regulations, executive orders,
directives, and enforcement priorities can also create uncertainty about how such laws and regulations will be interpreted and applied. If the Company is found to have violated such laws and regulations, it could materially adversely affect the Company’s business, reputation, results of operations,
financial condition and stock price.\n\nRisks and costs related to new and changing laws, regulations, executive orders, directives, and enforcement priorities increase as the Company’s products and services are introduced into specialized applications, including health and financial services, or as
the Company expands the use of technologies, such as machine learning and artificial intelligence features, and must navigate new legal, regulatory and ethical considerations relating to such technologies.\n\nRegulatory changes and other actions that materially adversely affect the Company’s
business may be announced with little or no advance notice and the Company may not be able to effectively mitigate all adverse impacts from such measures. For example, the Company is subject to changing regulations relating to the export and import of its products. The Company’s programs, policies
and procedures may not be effective in preventing a violation or a claim of a violation. As a result, the Company’s products could be banned, delayed or prohibited from importation, which could materially adversely affect the Company’s business, reputation, results of operations, financial condition
and stock price.\n\nVaried stakeholder expectations about social and other issues expose the Company to potential liabilities, increased costs, reputational harm, and other adverse effects on the Company’s business.",
     "score": 0.5021
    },
    {
     "source": "sec://0000320193-25-000079/1a#34",
     "title": "AAPL FY2025 10-K · Item 1A",
     "content": "Varied stakeholder expectations about social and other issues expose the Company to potential liabilities, increased costs, reputational harm, and other adverse effects on the Company’s business.\n\nVarious stakeholders, including governments, regulators, investors, employees,
customers and others, have differing expectations about a wide range of social and other issues related to the Company’s business. The Company makes statements about its values, including the environmental and societal impact of its business, through various reports, information provided on the
Company’s website, and in press statements and other communications. The Company also pursues environmental and other goals and initiatives that involve risks and uncertainties, require investments, and depend in part on third-party performance or data that is outside the Company’s control, and the
Company may not be able to fully achieve all of its goals and initiatives. Efforts by the Company to advance its business and values, or achieve its goals and further its initiatives, or to align with stakeholders’ expectations, or comply with evolving, varied and at times conflicting federal, state
and international laws, executive orders, regulations and standards, or any failure or perceived failure to do so, can result in adverse reactions by consumers and other stakeholders, including the commencement of legal and regulatory proceedings against the Company, and can materially adversely
affect the Company’s business, reputation, results of operations, financial condition and stock price.\n\nApple Inc. | 2025 Form 10-K | 13\n\n\n\nThe technology industry, including, in some instances, the Company, is subject to intense media, political and regulatory scrutiny, which exposes the
Company to increasing regulation, government investigations, legal actions and penalties.\n\nFrom time to time, the Company has made changes to its business, including actions taken in response to litigation, competition, market conditions and legal and regulatory requirements. The Company expects
to make further business changes in the future. For example, in the U.S., the Company has implemented changes to how developers communicate with consumers within apps on the U.S. storefront of the iOS and iPadOS App Store regarding alternative purchasing mechanisms and is currently subject to a
court order preventing it from imposing any commission or fee on certain purchases that consumers make.",
     "score": 0.4976
    },
    {
     "source": "sec://0000320193-25-000079/1a#35",
     "title": "AAPL FY2025 10-K · Item 1A",
     "content": "Globally, several jurisdictions have adopted, or may in the future adopt, competition-related laws and regulations imposing wide-ranging obligations on technology companies and significant limitations on businesses, including the Company. For example, the Company has implemented
changes to iOS, iPadOS, the App Store and Safari® in the EU as it seeks to comply with the Digital Markets Act (“DMA”), including new business terms and alternative fee structures for iOS and iPadOS apps, alternative methods of distribution for iOS and iPadOS apps, alternative payment processing for
apps across the Company’s operating systems, and additional tools and application programming interfaces for developers. The Company has also continued to make changes to its compliance plan in response to feedback and engagement with the Commission. Although the Company’s compliance plan is
intended to address the DMA’s obligations, it has been challenged by the Commission and may be challenged further by private litigants. The DMA provides for significant fines and penalties for noncompliance. While the changes introduced by the Company in the EU are intended to reduce new privacy and
security risks that the DMA poses to EU users, many risks will remain. Changes to the Company’s business in response to the DMA or other laws and regulations could materially adversely affect the Company’s business, reputation, results of operations, financial condition and stock price.\n\nThe
Company is also currently subject to antitrust investigations and litigation in various jurisdictions around the world, which can result in legal proceedings and claims against the Company that could, individually or in the aggregate, have a material adverse impact on the Company’s business, results
of operations, financial condition and stock price. For example, the Company is subject to civil antitrust lawsuits in the U.S. alleging monopolization or attempted monopolization in the markets for “performance smartphones” and “smartphones” generally in violation of U.S. antitrust laws. In
addition, the Company is the subject of investigations in Europe and other jurisdictions relating to App Store terms and conditions. If such investigations or litigation are resolved against the Company, the Company can be exposed to significant fines and may be required to make further changes to
its business practices, all of which could materially adversely affect the Company’s business, reputation, results of operations, financial condition and stock price.",
     "score": 0.6712
    },
    {
     "source": "sec://0000320193-25-000079/1a#36",
     "title": "AAPL FY2025 10-K · Item 1A",
     "content": "Further, the Company has commercial relationships with other companies in the technology industry that are or may become subject to investigations and litigation that, if resolved against those other companies, could materially adversely affect the Company’s commercial relationships
with those business partners and materially adversely affect the Company’s business, results of operations, financial condition and stock price. For example, the Company earns revenue from licensing arrangements with Google LLC (“Google”) and other companies to offer their search services on the
Company’s platforms and applications, and certain of these arrangements are currently subject to government investigations and legal proceedings. On August 5, 2024, Google was found to have violated U.S. antitrust laws. In connection with this finding, on September 2, 2025, the U.S. District Court
for the District of Columbia (“D.C. District Court”) ordered certain remedies. The court’s order is subject to further proceedings before the D.C. District Court, which may result in changes to the interpretation or application of the remedies ordered by the court, as well as new or changed remedies
being ordered. The court’s order is also subject to appeal by both the U.S. Department of Justice (“DOJ”) and Google. A reversal of the order on appeal could result in imposition of certain remedies initially proposed by the DOJ, such as those prohibiting Google from offering the Company commercial
terms for search distribution. If implemented, these remedies could materially adversely affect the Company’s ability to earn revenue from such licensing arrangements.\n\nThe Company’s business, results of operations, financial condition and stock price can be materially adversely affected,
individually or in the aggregate, by the outcomes of such investigations, litigation or changes to laws and regulations in the future. Changes to the Company’s business practices to comply with new laws and regulations or in connection with legal proceedings can negatively impact the reputation of
the Company’s products for privacy and security. Such changes in business practices can also otherwise adversely affect the experience for users of the Company’s products and services, and result in harm to the Company’s reputation, loss of competitive advantage, poor market acceptance, reduced
demand for products and services, lost sales, and lower profit margins.\n\nApple Inc. | 2025 Form 10-K | 14\n\n\n\nThe Company’s business is subject to a variety of U.S. and international laws, rules, policies and other obligations regarding the collection, use, protection and transfer of personal
data.",
     "score": 0.5778
    },
    {
     "source": "sec://0000320193-25-000079/1a#37",
     "title": "AAPL FY2025 10-K · Item 1A",
     "content": "The Company’s business is subject to a variety of U.S. and international laws, rules, policies and other obligations regarding the collection, use, protection and transfer of personal data.\n\nThe Company is subject to an increasing number of federal, state and international laws
relating to the collection, use, retention, protection and transfer of various types of personal data. In many cases, these laws apply not only to third-party transactions, but also restrict transfers of personal data among the Company and its international subsidiaries. Several jurisdictions have
passed laws in this area, and additional jurisdictions are considering imposing additional restrictions or have laws that are pending. These laws continue to develop and may be inconsistent from jurisdiction to jurisdiction. Complying with emerging and changing requirements causes the Company to
incur substantial costs and has required and may in the future require the Company to change its business practices. Noncompliance could result in significant penalties or legal liability.\n\nThe Company makes statements about its use and disclosure of personal data through its privacy policy,
information provided on its website, press statements and other privacy notices provided to customers. Any failure or perceived failure by the Company to comply with these public statements or with federal, state or international privacy or data protection laws and regulations could result in
inquiries, proceedings and penalties from governmental entities or others. Such a failure or perceived failure could also result in reputational impacts, ongoing audit requirements and significant legal liability. The risks of inadvertent disclosure of personal data can increase with the
introduction of new and complex technologies, such as artificial intelligence features, further exacerbating such risks.\n\nIn addition to the risks generally relating to the collection, use, retention, protection and transfer of personal data, the Company is also subject to specific obligations
relating to the collection and processing of data associated with minors, as well as information considered sensitive under applicable laws, such as health, biometric, financial and payment card data. Health, biometric, financial and payment card data are subject to additional privacy, security and
breach notification requirements, and the Company is subject to audit by governmental authorities regarding the Company’s compliance with these obligations. If the Company fails to adequately comply with these rules and requirements, the Company can be subject to litigation or government
investigations, can be liable for associated investigatory expenses, and can incur significant fees or fines.",
     "score": 0.4687
    },
    {
     "source": "sec://0000320193-25-000079/1a#38",
     "title": "AAPL FY2025 10-K · Item 1A",
     "content": "The Company is also subject to new and changing laws and regulations regarding online safety, including enhanced protections for minors and mandatory age verification requirements. These laws and regulations can increase regulatory risks by requiring complex compliance measures and
significant modifications to the Company’s products, services and operations, and may lead to operational disruptions, heightened privacy and data security risks, increased costs and potential liability and fines, all of which can have a material adverse impact on the Company’s business, financial
condition, results of operations and stock price.",
     "score": 0.4893
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 3",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 3 (Legal Proceedings) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/3#47",
     "title": "AAPL FY2025 10-K · Item 3",
     "content": "## Item 3. Legal Proceedings\n\nDigital Markets Act Investigations\n\nOn March 25, 2024, the Commission announced that it had opened a formal noncompliance investigation against the Company under Article 5(4) of the EU DMA (“Article 5(4) Investigation”). The Article 5(4)
Investigation relates to how developers may communicate and promote offers to end users for apps distributed through the App Store, as well as how developers may conclude contracts with those end users. On June 24, 2024, the Commission announced that it had opened an additional formal investigation
against the Company regarding whether the Company’s new contractual requirements for third-party app developers and app marketplaces may violate the DMA (“Article 6(4) Investigation”). On April 23, 2025, the Commission fined the Company €500 million in the Article 5(4) Investigation and issued a
cease and desist order requiring the Company to remove technical and commercial restrictions that prevent developers from steering users to alternative distribution channels outside the App Store. The Company has appealed the Commission’s Article 5(4) decision. Also on April 23, 2025, the Commission
issued preliminary findings in the Article 6(4) Investigation. If the Commission makes a final determination in the Article 6(4) Investigation that there has been a violation, it can issue a cease and desist order and may impose fines up to 10% of the Company’s annual worldwide net sales. The
Commission may also seek to impose additional fines if it deems that the Company has violated a cease and desist order. The Company believes that it complies with the DMA and has continued to make changes to its compliance plan in response to feedback and engagement with the
Commission.\n\nDepartment of Justice Lawsuit\n\nOn March 21, 2024, the DOJ and a number of state and district attorneys general filed a civil antitrust lawsuit in the U.S. District Court for the District of New Jersey against the Company alleging monopolization or attempted monopolization in the
markets for “performance smartphones” and “smartphones” in violation of U.S. antitrust laws. The DOJ is seeking equitable relief to redress the alleged anticompetitive behavior. In addition, various civil litigation matters have been filed in state and federal courts in the U.S. alleging similar
violations of U.S. antitrust laws and seeking monetary damages and other nonmonetary relief. The Company believes it has substantial defenses and intends to vigorously defend itself.\n\nEpic Games",
     "score": 0.5822
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "_unknown",
   "prelude": "Excerpts from AAPL FY2025 10-K, _unknown — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/unknown#48",
     "title": "AAPL FY2025 10-K",
     "content": "Epic Games\n\nEpic Games, Inc. filed a lawsuit in the U.S. District Court for the Northern District of California (“California District Court”) against the Company alleging violations of federal and state antitrust laws and California’s unfair competition law based upon the
Company’s operation of its App Store. The California District Court found that certain provisions of the Company’s App Review Guidelines violate California’s unfair competition law and issued an injunction (the “2021 Injunction”) enjoining the Company from prohibiting developers from including in
their apps buttons, external links, or other calls to action that direct customers to purchasing mechanisms other than the Company’s in-app purchase system. The 2021 Injunction applies to apps on the U.S. storefronts of the iOS and iPadOS App Stores. On January 16, 2024, the Company implemented a
plan to comply with the 2021 Injunction and filed a statement of compliance with the California District Court. On September 30, 2024, the Company filed a motion with the California District Court to narrow or vacate the 2021 Injunction. On April 30, 2025, the California District Court found the
Company to be in violation of the 2021 Injunction and enjoined the Company from imposing any commission or any fee on purchases that consumers make outside an app; restricting, conditioning, limiting, or prohibiting how developers guide consumers to purchases outside an app; or otherwise interfering
with a consumer’s choice to proceed in or out of an app. The California District Court also denied the Company’s motion to narrow or vacate the 2021 Injunction and referred the Company to the U.S. Attorney for the Northern District of California for a determination whether criminal contempt
proceedings are appropriate. The Company will continue to vigorously defend its actions and employees, and has appealed the California District Court’s most recent decision to the U.S. Court of Appeals for the Ninth Circuit (“Ninth Circuit Court”). Although the Company’s request to stay the decision
pending appeal was denied, the Ninth Circuit Court has agreed to consider the Company’s appeal on an expedited basis, with oral arguments heard in October 2025.\n\nOther Legal Proceedings",
     "score": 0.4751
    }
   ]
  }
 ]
}

[tool 2] tavily_financial_search {"query": "Meta latest EU US big tech platform regulation DMA antitrust direct business impact 2025 2026", "ticker": "META"}
{
 "query": "META Meta latest EU US big tech platform regulation DMA antitrust direct business impact 2025 2026",
 "results": [
  {
   "title": "EU hits Meta with antitrust probe over plans to block AI ...",
   "url": "https://www.reuters.com/sustainability/boards-policy-regulation/eu-launch-antitrust-probe-into-meta-over-use-ai-whatsapp-ft-reports-2025-12-04",
   "content": "Dec 3, 2025 — EU regulators launched an antitrust investigation into Meta Platforms on Thursday and may even temporarily halt its rollout of artificial",
   "published_date": null
  },
  {
   "title": "Major European regulatory probes into Big Tech",
   "url": "https://www.reuters.com/technology/european-regulators-crack-down-big-tech-2026-07-23",
   "content": "Jul 23, 2026 — Meta Platforms was fined nearly 800 million euros in 2024 over practices benefiting Facebook Marketplace.",
   "published_date": null
  },
  {
   "title": "Meta may face daily fines over pay-or-consent model, EU warns",
   "url": "https://www.reuters.com/sustainability/boards-policy-regulation/meta-may-face-daily-fines-over-pay-or-consent-model-eu-warns-2025-06-27",
   "content": "Report AdImage 4\n\nThe move shows the Commission's continuing crackdown against Big Tech and its push to create a level playing field for smaller rivals despite U.S. criticism about the bloc's rules mainly targeting its companies.\n\nDaily fines for not complying with the DMA can be
as much as 5% of a company's average daily worldwide turnover. [...] The warning from the European Commission, which acts as the EU competition enforcer, came two months after it slapped a 200-million-euro ($234 million) fine on the U.S. social media giant for breaching the Digital Markets Act (DMA)
aiming at curbing the power of Big Tech.\n\nMake sense of the latest ESG trends affecting companies and governments with the Reuters Sustainable Switch newsletter. Sign up here.\n\nAdvertisement · Scroll to continue\n\nReport AdImage 4 [...] Video 7\n\nVideo 8\n\n\"We are confident that the range of
choices we offer people in the EU doesn't just comply with what the EU's rules require - it goes well beyond them.\"\n\nThe EU watchdog dismissed Meta's discrimination charges, saying the DMA applies equally to all large digital companies doing business in the EU regardless of where they are
incorporated or who their controlling shareholders are.",
   "published_date": null
  },
  {
   "title": "US demands EU antitrust chief clarify rules reining in Big Tech | Reuters",
   "url": "https://www.reuters.com/technology/us-demands-eu-antitrust-chief-clarify-rules-reining-big-tech-2025-02-23",
   "content": "Sign up here.\n\nThe Digital Markets Act sets out a list of dos and don'ts for Alphabet (GOOGL.O), Amazon (AMZN.O), Apple (AAPL.O), Booking.com (BKNG.O), ByteDance, Meta Platforms (META.O), Microsoft (MSFT.O), aimed at securing a level playing field and giving consumers more choices.
[...] \"We write to express our concerns that the DMA may target American companies,\" Jordan wrote in a letter sent to Ribera on Sunday and seen by Reuters, saying that the rules subject companies to burdensome regulations and give European companies an advantage.\n\nScott Fitzgerald, chairman of
the subcommittee on the administrative state, regulatory reform and antitrust, was a co-signatory to the letter.\n\nThe letter criticised fines up to 10% of global annual revenues for DMA violations. [...] \"These severe fines appear to have two goals: to compel businesses to follow European
standards worldwide, and as a European tax on American companies,\" Jordan and Fitzgerald said.\n\nThey also took a swipe at the DMA requirements, saying some of them could benefit China.\n\n\"These, along with other provisions of the DMA, stifle innovation, disincentivize research and development,
and hand vast amounts of highly valuable proprietary data to companies and adversarial nations,\" the letter said.",
   "published_date": null
  },
  {
   "title": "Apple, Meta fined as EU presses ahead with tech probes",
   "url": "https://www.reuters.com/sustainability/boards-policy-regulation/apple-fined-570-million-meta-228-million-breaching-eu-law-2025-04-23",
   "content": "Apr 23, 2025 — It said Meta's pay-or-consent model introduced in November 2023 breached the DMA in the period up to November 2024, when it tweaked it to use ...Read more",
   "published_date": null
  }
 ]
}

[tool 3] tavily_financial_search {"query": "Apple Meta latest EU US big tech platform regulation DMA antitrust direct business impact 2025 2026", "ticker": "AAPL"}
{
 "query": "AAPL Apple Meta latest EU US big tech platform regulation DMA antitrust direct business impact 2025 2026",
 "results": [
  {
   "title": "Apple loses challenges against EU rules to curb Big Tech",
   "url": "https://www.reuters.com/world/eu-court-rejects-apples-challenge-against-eu-rules-reining-big-tech-2026-07-08",
   "content": "Apple lost its challenge on ​Wednesday against landmark EU rules that designate its app stores and operating system iOS as gatekeepers",
   "published_date": null
  }
 ]
}

[tool 4] sec_filing_search {"query": "App Store Services revenue commission alternative payments EU DMA impact revenue gross margin search licensing revenue", "ticker": "AAPL", "fiscal_year": 2025}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-09-27",
 "fiscal_year_source": "requested",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 1A (Risk Factors) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/1a#35",
     "title": "AAPL FY2025 10-K · Item 1A",
     "content": "Globally, several jurisdictions have adopted, or may in the future adopt, competition-related laws and regulations imposing wide-ranging obligations on technology companies and significant limitations on businesses, including the Company. For example, the Company has implemented
changes to iOS, iPadOS, the App Store and Safari® in the EU as it seeks to comply with the Digital Markets Act (“DMA”), including new business terms and alternative fee structures for iOS and iPadOS apps, alternative methods of distribution for iOS and iPadOS apps, alternative payment processing for
apps across the Company’s operating systems, and additional tools and application programming interfaces for developers. The Company has also continued to make changes to its compliance plan in response to feedback and engagement with the Commission. Although the Company’s compliance plan is
intended to address the DMA’s obligations, it has been challenged by the Commission and may be challenged further by private litigants. The DMA provides for significant fines and penalties for noncompliance. While the changes introduced by the Company in the EU are intended to reduce new privacy and
security risks that the DMA poses to EU users, many risks will remain. Changes to the Company’s business in response to the DMA or other laws and regulations could materially adversely affect the Company’s business, reputation, results of operations, financial condition and stock price.\n\nThe
Company is also currently subject to antitrust investigations and litigation in various jurisdictions around the world, which can result in legal proceedings and claims against the Company that could, individually or in the aggregate, have a material adverse impact on the Company’s business, results
of operations, financial condition and stock price. For example, the Company is subject to civil antitrust lawsuits in the U.S. alleging monopolization or attempted monopolization in the markets for “performance smartphones” and “smartphones” generally in violation of U.S. antitrust laws. In
addition, the Company is the subject of investigations in Europe and other jurisdictions relating to App Store terms and conditions. If such investigations or litigation are resolved against the Company, the Company can be exposed to significant fines and may be required to make further changes to
its business practices, all of which could materially adversely affect the Company’s business, reputation, results of operations, financial condition and stock price.",
     "score": 0.5305
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 3",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 3 (Legal Proceedings) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/3#47",
     "title": "AAPL FY2025 10-K · Item 3",
     "content": "## Item 3. Legal Proceedings\n\nDigital Markets Act Investigations\n\nOn March 25, 2024, the Commission announced that it had opened a formal noncompliance investigation against the Company under Article 5(4) of the EU DMA (“Article 5(4) Investigation”). The Article 5(4)
Investigation relates to how developers may communicate and promote offers to end users for apps distributed through the App Store, as well as how developers may conclude contracts with those end users. On June 24, 2024, the Commission announced that it had opened an additional formal investigation
against the Company regarding whether the Company’s new contractual requirements for third-party app developers and app marketplaces may violate the DMA (“Article 6(4) Investigation”). On April 23, 2025, the Commission fined the Company €500 million in the Article 5(4) Investigation and issued a
cease and desist order requiring the Company to remove technical and commercial restrictions that prevent developers from steering users to alternative distribution channels outside the App Store. The Company has appealed the Commission’s Article 5(4) decision. Also on April 23, 2025, the Commission
issued preliminary findings in the Article 6(4) Investigation. If the Commission makes a final determination in the Article 6(4) Investigation that there has been a violation, it can issue a cease and desist order and may impose fines up to 10% of the Company’s annual worldwide net sales. The
Commission may also seek to impose additional fines if it deems that the Company has violated a cease and desist order. The Company believes that it complies with the DMA and has continued to make changes to its compliance plan in response to feedback and engagement with the
Commission.\n\nDepartment of Justice Lawsuit\n\nOn March 21, 2024, the DOJ and a number of state and district attorneys general filed a civil antitrust lawsuit in the U.S. District Court for the District of New Jersey against the Company alleging monopolization or attempted monopolization in the
markets for “performance smartphones” and “smartphones” in violation of U.S. antitrust laws. The DOJ is seeking equitable relief to redress the alleged anticompetitive behavior. In addition, various civil litigation matters have been filed in state and federal courts in the U.S. alleging similar
violations of U.S. antitrust laws and seeking monetary damages and other nonmonetary relief. The Company believes it has substantial defenses and intends to vigorously defend itself.\n\nEpic Games",
     "score": 0.5061
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 7",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 3 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/7#69",
     "title": "AAPL FY2025 10-K · Item 7",
     "content": "Americas\n\nAmericas net sales increased during 2025 compared to 2024 primarily due to higher net sales of iPhone and Services. The weakness in foreign currencies relative to the U.S. dollar had an unfavorable year-over-year impact on Americas net sales during
2025.\n\nEurope\n\nEurope net sales increased during 2025 compared to 2024 primarily due to higher net sales of Services, iPhone and Mac.\n\nGreater China\n\nGreater China net sales decreased during 2025 compared to 2024 primarily due to lower net sales of iPhone, partially offset by higher net
sales of Mac.\n\nJapan\n\nJapan net sales increased during 2025 compared to 2024 primarily due to higher net sales of iPhone, Services and iPad.\n\nRest of Asia Pacific\n\nRest of Asia Pacific net sales increased during 2025 compared to 2024 primarily due to higher net sales of iPhone, Services and
Mac.\n\nApple Inc. | 2025 Form 10-K | 22",
     "score": 0.4979
    },
    {
     "source": "sec://0000320193-25-000079/7#71",
     "title": "AAPL FY2025 10-K · Item 7",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | |
| 2025 | | |  | | | Change | | |  | | | 2024 | | |  | | | Change | | |  | | | 2023 | | |\n| iPhone | | | $ | 209,586 |  |  | | | 4 | | % |  | | | $ | 201,183 |  |  | | | — | | % |  | | | $ | 200,583 |  |\n| Mac | | | 33,708 | |  |  | | | 12 | | % |  | | | 29,984 | |  |  | | | 2 | | % |  | | | 29,357
| |  |\n| iPad | | | 28,023 | |  |  | | | 5 | | % |  | | | 26,694 | |  |  | | | (6) | | % |  | | | 28,300 | |  |\n| Wearables, Home and Accessories | | | 35,686 | |  |  | | | (4) | | % |  | | | 37,005 | |  |  | | | (7) | | % |  | | | 39,845 | |  |\n| Services (1) | | | 109,158 | |  |  | | | 14 | | %
|  | | | 96,169 | |  |  | | | 13 | | % |  | | | 85,200 | |  |",
     "score": 0.4755
    },
    {
     "source": "sec://0000320193-25-000079/7#73",
     "title": "AAPL FY2025 10-K · Item 7",
     "content": "(1)Services net sales include amortization of the deferred value of services bundled in the sales price of certain products.\n\niPhone\n\niPhone net sales increased during 2025 compared to 2024 due to higher net sales of Pro models.\n\nMac\n\nMac net sales increased during 2025
compared to 2024 primarily due to higher net sales of laptops and desktops.\n\niPad\n\niPad net sales increased during 2025 compared to 2024 primarily due to higher net sales of iPad Air, iPad mini and iPad, partially offset by lower net sales of iPad Pro.\n\nWearables, Home and
Accessories\n\nWearables, Home and Accessories net sales decreased during 2025 compared to 2024 primarily due to lower net sales of Accessories and Wearables.\n\nServices\n\nServices net sales increased during 2025 compared to 2024 primarily due to higher net sales from advertising, the App Store
and cloud services.\n\nApple Inc. | 2025 Form 10-K | 23",
     "score": 0.4969
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 8",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 8 (Financial Statements and Supplementary Data) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/8#130",
     "title": "AAPL FY2025 10-K · Item 8 · Note 2 –Revenue",
     "content": "### Note 2 –Revenue\n\nThe Company recognizes revenue at the amount to which it expects to be entitled when control of products or services is transferred to its customers. Control is generally transferred when the Company has a present right to payment and title and the significant
risks and rewards of ownership of products or services are transferred to its customers. For most of the Company’s Products net sales, control transfers when products are shipped. For the Company’s Services net sales, control transfers over time as services are delivered. Payment for Products and
Services net sales is collected within a short period following transfer of control or commencement of delivery of services, as applicable.\n\nThe Company records reductions to Products net sales related to future product returns, price protection and other customer incentive programs based on the
Company’s expectations and historical experience.\n\nFor arrangements with multiple performance obligations, which represent promises within an arrangement that are distinct, the Company allocates revenue to all distinct performance obligations based on their relative stand-alone selling prices
(“SSPs”). When available, the Company uses observable prices to determine SSPs. When observable prices are not available, SSPs are established that reflect the Company’s best estimates of what the selling prices of the performance obligations would be if they were sold regularly on a stand-alone
basis. The Company’s process for estimating SSPs without observable prices considers multiple factors that may vary depending upon the unique facts and circumstances related to each performance obligation including, where applicable, prices charged by the Company for similar offerings, market trends
in the pricing for similar offerings, product-specific business objectives and the estimated cost to provide the performance obligation.\n\nThe Company has identified the performance obligations regularly included in arrangements involving the sale of iPhone, Mac and iPad. The first material
performance obligation, which represents the substantial portion of the allocated sales price, is the hardware and bundled software delivered at the time of sale. The second material performance obligation is the right to receive certain product-related bundled services, which include iCloud®, Siri®
and Maps. The Company allocates revenue and any related discounts to all of its performance obligations based on their relative SSPs. Because the Company lacks observable prices for product-related bundled services, the allocation of revenue is based on the Company’s estimated SSPs. Revenue
allocated to the delivered hardware and bundled software is recognized when control has transferred to the customer, which generally occurs when the product is shipped. Revenue allocated to product-related bundled services is deferred and recognized on a straight-line basis over the estimated period
they are expected to be provided.",
     "score": 0.4672,
     "subsection": "Note 2 –Revenue"
    },
    {
     "source": "sec://0000320193-25-000079/8#131",
     "title": "AAPL FY2025 10-K · Item 8",
     "content": "For certain long-term service arrangements, the Company has performance obligations for services it has not yet delivered. For these arrangements, the Company does not have a right to bill for the undelivered services. The Company has determined that any unbilled consideration
relates entirely to the value of the undelivered services. Accordingly, the Company has not recognized revenue, and does not disclose amounts, related to these undelivered services.\n\nFor the sale of third-party products where the Company obtains control of the product before transferring it to the
customer, the Company recognizes revenue based on the gross amount billed to customers. The Company considers multiple factors when determining whether it obtains control of third-party products, including evaluating if it can establish the price of the product, retains inventory risk for tangible
products or has the responsibility for ensuring acceptability of the product. For third-party applications sold through the App Store, the Company does not obtain control of the product before transferring it to the customer. Therefore, the Company accounts for all third-party application–related
sales on a net basis by recognizing in Services net sales only the commission it retains.\n\nApple Inc. | 2025 Form 10-K | 35\n\n\n\nThe following table shows disaggregated net sales, as well as the portion of total net sales that was previously deferred, for 2025, 2024 and 2023 (in millions):",
     "score": 0.4938
    },
    {
     "source": "sec://0000320193-25-000079/8#132",
     "title": "AAPL FY2025 10-K · Item 8",
     "content": "The following table shows disaggregated net sales, as well as the portion of total net sales that was previously deferred, for 2025, 2024 and 2023 (in millions):\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 2025 | | |  | | | 2024 | | |  | | | 2023 | | |\n| iPhone | | | $ | 209,586 |  |  | | | $ | 201,183 |  |  | | | $ | 200,583 |  |\n| Mac | | | 33,708 | |  |  | | | 29,984 | |  |  | | | 29,357 | |  |\n| iPad | | | 28,023 | |  |  | | | 26,694 | |
|  | | | 28,300 | |  |\n| Wearables, Home and Accessories | | | 35,686 | |  |  | | | 37,005 | |  |  | | | 39,845 | |  |\n| Services (1) | | | 109,158 | |  |  | | | 96,169 | |  |  | | | 85,200 | |  |\n| Total net sales | | | $ | 416,161 |  |  | | | $ | 391,035 |  |  | | | $ | 383,285 |  |\n|  | | |
| | |  | | |  | | |  | | |  | | |\n| Portion of total net sales that was included in deferred revenue as of the beginning of the period | | | $ | 8,229 |  |  | | | $ | 7,728 |  |  | | | $ | 8,169 |  |\n\n(1)Services net sales include amortization of the deferred value of services bundled in the
sales price of certain products.",
     "score": 0.4755
    },
    {
     "source": "sec://0000320193-25-000079/8#133",
     "title": "AAPL FY2025 10-K · Item 8",
     "content": "(1)Services net sales include amortization of the deferred value of services bundled in the sales price of certain products.\n\nThe Company’s proportion of net sales by disaggregated revenue source was generally consistent for each reportable segment in Note 13, “Segment Information
and Geographic Data” for 2025, 2024 and 2023, except in Greater China, where iPhone revenue represented a moderately higher proportion of net sales.\n\nAs of September 27, 2025 and September 28, 2024, the Company had total deferred revenue of $13.7 billion and $12.8 billion, respectively. As of
September 27, 2025, the Company expects 66% of total deferred revenue to be realized in less than a year, 23% within one-to-two years, 9% within two-to-three years and 2% in greater than three years.",
     "score": 0.4975
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 1",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 1 (Business) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/1#2",
     "title": "AAPL FY2025 10-K · Item 1 · Company Background",
     "content": "### Company Background\n\nThe Company designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories, and sells a variety of related services. The Company’s fiscal year is the 52- or 53-week period that ends on the last Saturday of
September.\n\nProducts\n\niPhone\n\niPhone® is the Company’s line of smartphones based on its iOS operating system. The iPhone line includes iPhone 17 Pro, iPhone Air™, iPhone 17, iPhone 16 and iPhone 16e.\n\nMac\n\nMac® is the Company’s line of personal computers based on its macOS® operating
system. The Mac line includes laptops MacBook Air® and MacBook Pro®, as well as desktops iMac®, Mac mini®, Mac Studio® and Mac Pro®.\n\niPad\n\niPad® is the Company’s line of multipurpose tablets based on its iPadOS® operating system. The iPad line includes iPad Pro®, iPad Air®, iPad and iPad
mini®.\n\nWearables, Home and Accessories\n\nWearables includes smartwatches, wireless headphones and spatial computers. The Company’s line of smartwatches, based on its watchOS® operating system, includes Apple Watch® Series 11, Apple Watch SE® 3 and Apple Watch Ultra® 3. The Company’s line of
wireless headphones includes AirPods®, AirPods Pro®, AirPods Max® and Beats® products. Apple Vision Pro™ is the Company’s spatial computer based on its visionOS® operating system.\n\nHome includes Apple TV 4K®, the Company’s media streaming and gaming device based on its tvOS® operating system, and
HomePod® and HomePod mini®, high-fidelity wireless smart speakers.\n\nAccessories includes Apple-branded and third-party accessories.\n\nApple Inc. | 2025 Form 10-K | 1\n\n\n\nServices\n\nAdvertising\n\nThe Company’s advertising services include third-party licensing arrangements and the Company’s
own advertising platforms.\n\nAppleCare\n\nThe Company offers a portfolio of fee-based service and support products under the AppleCare® brand. The offerings provide priority access to Apple technical support, access to the global Apple authorized service network for repair and replacement services,
and in many cases additional coverage for instances of accidental damage or theft and loss, depending on the country and type of product.\n\nCloud Services\n\nThe Company’s cloud services store and keep customers’ content up-to-date and available across multiple Apple devices and Windows personal
computers.\n\nDigital Content",
     "score": 0.4714,
     "subsection": "Company Background"
    }
   ]
  }
 ]
}

[tool 5] sec_filing_search {"query": "advertising revenue Europe share user geography regulatory privacy DMA consent personalized ads revenue impact", "ticker": "META", "fiscal_year": 2025}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "requested",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "META",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from META FY2025 10-K, Item 1A (Risk Factors) — 5 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-003942/1a#32",
     "title": "META FY2025 10-K · Item 1A",
     "content": "•reductions of advertising by marketers due to illegal, illicit, or otherwise objectionable content made available on our products by third parties, questions about our user data practices or the security of our platform, concerns about brand safety or potential legal liability, or
uncertainty regarding regulatory developments or their own legal and compliance obligations, including with respect to artificial intelligence;\n\n•the effectiveness of our ad targeting or degree to which users consent to, opt out of, or reduce the use of data for ads, including as a result of
product changes and controls that we have implemented or may implement in the future in connection with the GDPR, ePrivacy Directive, DMA, DMCC, U.S. state privacy laws, and other laws, regulations, regulatory actions, or litigation, or otherwise, that impact our ability to use data for advertising
purposes (for example, in response to regulatory developments in Europe, we began offering our users a \"subscription for no ads\" alternative in the European Union, European Economic Area, and Switzerland, and subsequently in November 2024 provided users in those regions who elect to continue
receiving our services free-of-charge, supported by ads, an option to see less personalized ads);\n\n•the degree to which users cease or reduce the number of times they engage with our ads;\n\n•changes in the way advertising on mobile devices or on personal computers is measured or priced;\n\n•the
success of technologies designed to block the display of ads or ad measurement tools;\n\n•changes in the composition of our marketer base or our inability to maintain or grow our marketer base; and\n\n•the impact of macroeconomic and geopolitical conditions, whether in the advertising industry in
general, or among specific types of marketers or within particular geographies, which in turn can have broader effects in other regions (for example, the war in Ukraine and service restrictions imposed by the Russian government have adversely affected our advertising business in Europe and other
regions, and advertiser spending also is subject to adverse effects from conflicts in the Middle East and the implementation of tariffs or other existing or future trade policies by the United States, China, and other governments).",
     "score": 0.5524
    },
    {
     "source": "sec://0001628280-26-003942/1a#34",
     "title": "META FY2025 10-K · Item 1A",
     "content": "Our ad targeting and measurement tools rely on data signals from user activity on websites and services that we do not control, as well as signals generated within our products, in order to deliver relevant and effective ads to our users, and any changes in our ability to use such
signals will adversely affect our business. For example, legislative and regulatory developments, such as the GDPR, ePrivacy Directive, DMA, and U.S. state privacy laws, have impacted, and we expect will continue to impact, our ability to use such signals in our ad products. In particular, we have
seen increases in the number of users opting to control certain types of ad targeting in Europe following product changes implemented in connection with our GDPR and ePrivacy Directive compliance, and we have introduced product changes that limit data signal use for users in certain U.S. states
following adoption of state privacy laws. A number of U.S. state privacy laws have introduced additional rights for users and could result in restrictions on our use of signals from third-party apps and websites through certain browser- and device-based universal opt-out mechanisms. Judicial and
regulatory guidance, decisions, or enforcement actions, or new legislation in these or other jurisdictions may require us to make additional changes to our products in the future that further reduce our ability to use these signals, which has occurred in the past. For example, in response to
regulatory developments in Europe, we announced plans to change the legal basis for behavioral advertising on Facebook and Instagram in the European Union, European Economic Area, and Switzerland from \"legitimate interests\" to \"consent,\" and in November 2023 we began offering users in the region
a \"subscription for no ads\" alternative. We are engaging with regulators on our consent model, including regarding compliance with requirements under the GDPR, DMA, and EU consumer laws. For example, in March 2024, the European Commission opened formal proceedings regarding the compliance of our
\"subscription for no ads\" model with requirements under the DMA, and it issued preliminary findings in July 2024. In addition, the European Data Protection Board has published an opinion on the operation of such models under GDPR and European consumer protection organizations have raised concerns
regarding our compliance with consumer protection laws. In response to these developments, in November 2024, we began offering users in the European Union, European Economic Area, and Switzerland who elect to continue using our services free-of-charge, supported by ads, an option to see less
personalized ads (LPA), which are less relevant and effective than our premium ad offerings. In April",
     "score": 0.5874
    },
    {
     "source": "sec://0001628280-26-003942/1a#35",
     "title": "META FY2025 10-K · Item 1A",
     "content": "European Union, European Economic Area, and Switzerland who elect to continue using our services free-of-charge, supported by ads, an option to see less personalized ads (LPA), which are less relevant and effective than our premium ad offerings. In April 2025, the European
Commission issued a final decision that our \"subscription for no ads\" model does not comply with such requirements. We made significant modifications to LPA since the European Commission issued its final decision. We have appealed the European Commission's decision but further modifications to our
model may be imposed during the appeal process, which could result in a materially worse user experience for European users and a significant impact to our European business and revenue.",
     "score": 0.6223
    },
    {
     "source": "sec://0001628280-26-003942/1a#90",
     "title": "META FY2025 10-K · Item 1A",
     "content": "guardians. Like comprehensive privacy laws, these laws are evolving and subject to interpretation, and may restrict our ability to offer certain products and services provided to all or certain cohorts of users in those states, adversely affecting our advertising business. In
Europe, evolving interpretation of the ePrivacy Directive's requirements regarding the use of cookies and similar technologies may lead to regulators imposing specific measures in the future which could directly impact our use of such technologies. In addition, the ePrivacy Directive and national
implementation laws impose additional limitations on the use of data across messaging products and include significant penalties for non-compliance. Changes to our products or business practices as a result of these or similar developments have adversely affected, and may in the future adversely
affect, our advertising business. For example, in response to regulatory developments in Europe, we announced plans to change the legal basis for behavioral advertising on Facebook and Instagram in the European Union, European Economic Area, and Switzerland from \"legitimate interests\" to
\"consent,\" and in November 2023 we began offering users in the region a \"subscription for no ads\" alternative. We are engaging with regulators on our consent model, including regarding compliance with requirements under the GDPR, DMA, and EU consumer laws. For example, in March 2024, the
European Commission opened formal proceedings regarding the compliance of our \"subscription for no ads\" model with requirements under the DMA, and it issued preliminary findings in July 2024. In addition, the European Data Protection Board has published an opinion on the operation of such models
under GDPR and European consumer protection organizations have raised concerns regarding our compliance with consumer protection laws. In response to these developments, in November 2024, we began offering users in the European Union, European Economic Area, and Switzerland who elect to continue
using our services free-of-charge, supported by ads, an option to see less personalized ads (LPA), which are less relevant and effective than our premium ad offerings. In April 2025, the European Commission issued a final decision that our \"subscription for no ads\" model does not comply with such
requirements. We made significant modifications to LPA since the European Commission issued its final decision. We have appealed the European Commission's decision but further modifications to our model may be imposed during the appeal process, which could result in a materially worse user
experience for European users and a significant impact to our European business and revenue. These or any similar developments in the future may negatively impact our user growth and engagement, revenue, and financial results.",
     "score": 0.6058
    },
    {
     "source": "sec://0001628280-26-003942/1a#91",
     "title": "META FY2025 10-K · Item 1A",
     "content": "Similarly, there are a number of legislative proposals or recently enacted laws in the European Union, the United States, at both the federal and state level, as well as other jurisdictions that could impose new obligations or limitations in areas affecting our business. For
example, the DMA in the European Union imposes restrictions and requirements on companies like ours, including in areas such as the combination of data across services, mergers and acquisitions, and product design. The DMA also includes significant penalties for non-compliance, and its key
requirements are enforceable against designated gatekeeper companies as of March 2024. The DMA has caused, and may in the future cause, us to incur significant compliance costs and make changes to our products or business practices. The requirements under the DMA will likely be subject to further
interpretation and regulatory engagement. Pending or future proposals to modify competition laws\n\n38\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)",
     "score": 0.5142
    }
   ]
  },
  {
   "ticker": "META",
   "fiscal_year": 2025,
   "item": "Item 7",
   "prelude": "Excerpts from META FY2025 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 3 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-003942/7#171",
     "title": "META FY2025 10-K · Item 7 · Developments in Advertising",
     "content": "### Developments in Advertising\n\n\nSubstantially all of our revenue is currently generated from advertising on Facebook and Instagram. We rely on targeting and measurement tools that incorporate data signals from user activity on websites and services that we do not control, as
well as signals generated within our products, in order to deliver relevant and effective ads to our users. Our advertising revenue has been, and we expect will continue to be, adversely affected by reduced marketer spending as a result of limitations on our ad targeting and measurement tools
arising from changes to the regulatory environment and third-party mobile operating systems and browsers.\n\n\nIn particular, legislative and regulatory developments such as the General Data Protection Regulation, including its evolving interpretation through decisions of the Court of Justice of the
European Union, ePrivacy Directive, European Digital Services Act, Digital Markets Act, and U.S. state privacy laws have impacted our ability to use data signals in our ad products, and an increasing number of laws have been introduced limiting or prohibiting the provision of our services to younger
users. We expect these and other developments will have further impact in the future. As a result, we have implemented, and we will continue to implement, whether voluntarily or otherwise, changes to our products and user data practices, which reduce our ability to effectively target and measure ads
and may negatively impact our advertising revenue and user engagement. For example, in response to regulatory developments in Europe, we announced our plans to change the legal basis for behavioral advertising on Facebook and Instagram in the European Union, European Economic Area,
and\n\n61\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)",
     "score": 0.5847,
     "subsection": "Developments in Advertising"
    },
    {
     "source": "sec://0001628280-26-003942/7#172",
     "title": "META FY2025 10-K · Item 7",
     "content": "61\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)\n\nSwitzerland from \"legitimate interests\" to \"consent,\" and began offering users in the region a \"subscription for no ads\" alternative. We subsequently began offering users in the region who elect to
continue using our services free-of-charge, supported by ads, an option to see less personalized ads, which are less relevant and effective than our premium ad offerings. We are engaging with regulators on our consent model. In addition, mobile operating system and browser providers, such as Apple
and Google, have implemented product changes and/or announced plans to limit the ability of websites and application developers to collect and use these signals to target and measure advertising. For example, in 2021, Apple made certain changes to its products and data use policies in connection
with changes to its iOS operating system that reduce our and other iOS developers' ability to target and measure advertising, which has negatively impacted, and we expect will continue to negatively impact, the size of the budgets marketers are willing to commit to us and other advertising
platforms.\n\n\nTo mitigate these developments, we are continually working to evolve our advertising systems to improve the performance of our ad products. We are developing privacy enhancing technologies to deliver relevant ads and measurement capabilities while reducing the amount of personal
information we process, including by relying more on anonymized or aggregated third-party data. In addition, we are developing tools that enable marketers to share their data into our systems, as well as ad products that generate more valuable signals within our apps. More broadly, we also continue
to innovate our advertising tools to help marketers prepare campaigns and connect with consumers, including developing growing formats such as Reels ads and our business messaging ad products. Across all of these efforts, we are making significant investments in artificial intelligence (AI),
including generative AI, to improve our delivery, targeting, and measurement capabilities. Further, we are focused on driving onsite conversions in our business messaging ad products by developing new features and scaling existing features.\n\n\nWe are also engaging with others across our industry
to explore the possibility of new open standards for the private and secure processing of data for advertising purposes. We believe our ongoing improvements to ad targeting and measurement are continuing to drive improved results for advertisers. However, we expect that some of these efforts will be
long-term initiatives, and that the legislative, regulatory and platform developments described above will continue to adversely impact our advertising revenue for the foreseeable future.",
     "score": 0.6101
    },
    {
     "source": "sec://0001628280-26-003942/7#176",
     "title": "META FY2025 10-K · Item 7 · Trends in Our Revenue by User Geography",
     "content": "### Trends in Our Revenue by User Geography\n\n\nWe calculate our revenue by user geography based on our estimate of the geography in which ad impressions are delivered, virtual and digital goods are purchased, or consumer hardware products are shipped. The geography of our users
affects our revenue and financial results. Our revenue in regions such as United States & Canada and Europe is relatively higher primarily due to the size and maturity of those online and mobile advertising markets, and ad impression growth is primarily in geographies that monetize at lower rates,
such as Asia-Pacific. In 2025, revenue increased by 21% in United States & Canada, 24% in Europe, 20% in Asia-Pacific, and 27% in Rest of World, in each case relative to
2024.\n\n\n![764](meta-20251231_g3.jpg)\n\n\n![767](meta-20251231_g4.jpg)-![769](meta-20251231_g5.jpg)\n\n\n![772](meta-20251231_g6.jpg) ![774](meta-20251231_g7.jpg)",
     "score": 0.5774,
     "subsection": "Trends in Our Revenue by User Geography"
    }
   ]
  },
  {
   "ticker": "META",
   "fiscal_year": 2025,
   "item": "Item 8",
   "prelude": "Excerpts from META FY2025 10-K, Item 8 (Financial Statements and Supplementary Data) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-003942/8#362",
     "title": "META FY2025 10-K · Item 8",
     "content": "In March 2024, the European Commission opened an investigation into the compliance of our \"subscription for no ads\" consent model with requirements under Article 5(2) of the Digital Markets Act (DMA). The European Commission issued preliminary findings on July 1, 2024 reflecting
its preliminary view that our model does not comply with such requirements. In April 2025, the European Commission issued a final decision that our \"subscription for no ads\" model does not comply with such requirements and imposed a fine of EUR €200 million. Based on feedback from the European
Commission in connection with the DMA, we launched less personalized ads (LPA) in November 2024 and made significant modifications to LPA since the European Commission issued its final decision. We appealed the European Commission's decision on July 4, 2025, but further modifications to our model
may be imposed during the appeal process, which could result in a materially worse user experience for European users and a significant impact to our European business and revenue.\n\n\n115\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)\n\nSecurities and Other Actions",
     "score": 0.5951
    }
   ]
  },
  {
   "ticker": "META",
   "fiscal_year": 2025,
   "item": "Item 3",
   "prelude": "Excerpts from META FY2025 10-K, Item 3 (Legal Proceedings) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-003942/3#142",
     "title": "META FY2025 10-K · Item 3",
     "content": "54\n\n\n\n\n[Table of Contents](#icc066a9e83ae4c46b57ee4d9dc9d7021_7)\n\nIn March 2024, the European Commission opened an investigation into the compliance of our \"subscription for no ads\" consent model with requirements under Article 5(2) of the Digital Markets Act (DMA). The
European Commission issued preliminary findings on July 1, 2024 reflecting its preliminary view that our model does not comply with such requirements. In April 2025, the European Commission issued a final decision that our \"subscription for no ads\" model does not comply with such requirements and
imposed a fine of EUR €200 million. Based on feedback from the European Commission in connection with the DMA, we launched less personalized ads (LPA) in November 2024 and made significant modifications to LPA since the European Commission issued its final decision. We appealed the European
Commission's decision on July 4, 2025, but further modifications to our model may be imposed during the appeal process, which could result in a materially worse user experience for European users and a significant impact to our European business and revenue.\n\n\nThe result of such litigation,
investigations or inquiries could subject us to substantial monetary remedies and costs, interrupt or require us to change our business practices, divert resources and the attention of management from our business, or subject us to other structural or behavioral remedies that adversely affect our
business.",
     "score": 0.577
    }
   ]
  }
 ]
}

[tool 6] finnhub_company_basic_financials {"ticker": "META"}
{
 "ticker": "META",
 "fiftyTwoWeekHigh": 779.8192,
 "fiftyTwoWeekLow": 520.26,
 "peTTM": 21.7503,
 "forwardPE": 22.28369,
 "psTTM": 6.7742,
 "pb": 6.7823,
 "marketCap": 1636687.1,
 "enterpriseValue": 1706387.1,
 "beta": 1.2670736,
 "epsTTM": 29.3369,
 "roeTTM": 30.270000000000003,
 "roaTTM": 17.810000000000002,
 "grossMarginTTM": 81.03,
 "netProfitMarginTTM": 31.15,
 "operatingMarginTTM": 32.86,
 "currentRatio": 1.9028,
 "quickRatio": 1.6785,
 "debtToEquity": 0.2971,
 "revenueGrowthTTMYoy": 27.53,
 "epsGrowthTTMYoy": 29.84,
 "tenDayAvgVolume": 21.92367
}

[tool 7] finnhub_company_basic_financials {"ticker": "AAPL"}
{
 "ticker": "AAPL",
 "fiftyTwoWeekHigh": 351.73,
 "fiftyTwoWeekLow": 243.42,
 "peTTM": 38.8212,
 "forwardPE": 35.33932,
 "psTTM": 10.7219,
 "pb": 38.486,
 "marketCap": 5005220,
 "enterpriseValue": 5050020,
 "beta": 1.1011555,
 "epsTTM": 8.723299999999998,
 "roeTTM": 137.17999999999998,
 "roaTTM": 34.55,
 "grossMarginTTM": 48.65,
 "netProfitMarginTTM": 27.62,
 "operatingMarginTTM": 33.17,
 "currentRatio": 1.0033,
 "quickRatio": 0.929,
 "debtToEquity": 0.7844,
 "dividendYield": 0.50534,
 "revenueGrowthTTMYoy": 14.24,
 "epsGrowthTTMYoy": 32.61,
 "tenDayAvgVolume": 40.71364
}
----- END EVIDENCE F0088 -----

----- BEGIN ANSWER F0088 -----
**結論：若看「持續性的直接商業衝擊」，我判斷 Meta 比 Apple 更大；若看「單一平台規則被迫改寫後對高毛利收入的集中打擊」，Apple 的尾部風險更尖銳。**

換句話說：

- **Meta：監管直接打在核心變現引擎——個人化廣告。**
- **Apple：監管主要打在 App Store 的抽成、分發與支付控制權。**

## 為什麼 Meta 的直接衝擊較大

Meta FY2025 10-K（截至 **2025-12-31**）明確表示，其收入「絕大部分」來自 Facebook 與 Instagram 廣告；而 GDPR、DMA、DSA、ePrivacy 規則及美國州級隱私法，已經限制其收集、組合和使用用戶數據來做廣告定向與成效衡量，並預期會繼續壓低廣告收入與用戶互動。[1][2]

這種衝擊不只是一次性罰款，而是會持續影響：

1. **廣告單價與轉化率**：少了跨網站、跨服務的數據訊號，廣告可能變得不夠精準，廣告主對投放預算和價格的接受度會受影響。
2. **產品設計與用戶體驗**：Meta 已在歐洲推出「無廣告付費」及「較少個人化廣告」選項；公司稱後者的廣告相關性和效果低於其高級廣告產品，且未來若被要求進一步修改，可能對歐洲業務和收入造成重大影響。[3]
3. **美國監管的延伸性**：Meta 受到 FTC 同意令、美國州級隱私法、未成年人與社交媒體規則等多重約束。公司表示，隱私合規需要大量人員、系統、管理層監督和技術基礎設施投入，也會使廣告及產品開發更慢、更昂貴。[4]

因此，Meta 面對的是「每一次數據使用限制，都可能直接反映到廣告變現效率」的風險，而不是只在出現裁決或罰款時才受影響。

## Apple 的衝擊較集中，但可能打到高毛利平台收入

Apple FY2025 10-K（截至 **2025-09-27**）顯示，2025 年 Services 收入為 **1,091.58 億美元**，總收入為 **4,161.61 億美元**；Services 約佔總收入四分之一以上。Services 增長來源包括廣告、App Store 和雲端服務。[5] Apple 對第三方 App 的銷售是按「保留的佣金」確認收入，因此 App Store 規則變化會直接觸及其平台抽成模式。[6]

在歐盟 DMA 下，Apple 已被迫改變：

- App Store 商業條款與費率；
- 第三方 App 的替代分發；
- 替代支付方式；
- 開發者引導用戶到 App Store 外交易的方式；
- iOS、iPadOS 和 Safari 的部分功能與接口。

2025 年 4 月，歐盟因 Apple 限制開發者引導用戶到外部購買，對其處以 **5 億歐元**罰款，並要求撤銷相關技術及商業限制。Apple 也表示，另一項 DMA 調查若最終認定違規，罰款最高可達全球年度銷售額的 **10%**。[7]

美國方面，Apple 也面對 DOJ 的反壟斷訴訟，以及 Epic 案相關命令。其 FY2025 10-K 指出，美國法院命令 Apple 不得對 App 外購買收取佣金或費用，也不得限制開發者如何引導用戶到 App 外購買；Apple 已提出上訴。[8]

這對 Apple 的主要風險是：

- App Store 抽成率下降；
- 用戶和開發者更容易繞過 Apple 的支付系統；
- Apple 對 iOS 分發、支付和商業條款的控制力下降；
- 安全、隱私與用戶體驗的差異化可能被削弱。

不過，Apple 的硬體銷售仍是主要收入來源，監管並沒有直接針對 iPhone 的核心銷售模式。因此，除非監管進一步要求開放更廣泛的系統層級功能，否則 Apple 的衝擊相對集中於 Services 和平台控制權，而不是整個收入模型。

## 美國與歐盟的差異

### 歐盟：兩家公司都已出現具體、已量化的商業後果

歐盟對 Apple 和 Meta 都不只是調查，而是已經迫使兩家公司修改產品與商業模式：

- Apple：App Store 外部支付、外部分發和開發者導流受規範，並已被罰 **5 億歐元**。[7]
- Meta：付費免廣告／同意模式被認定不符合 DMA，並被罰 **2 億歐元**；同時推出較少個人化廣告方案。[3]

Meta 的罰款金額較低，但其受影響的是廣告定向能力，而那是其幾乎全部收入的核心。Apple 的罰款較高，但受影響的主要是 Services 中的 App Store 等平台經濟。

### 美國：Apple 的平台反壟斷風險較集中，Meta 的結構性風險更大

Apple 在美國面對 DOJ 對 iPhone 生態系統和反壟斷行為的訴訟，以及 Epic 相關的 App Store 導流限制問題。[8]

Meta 則面對 FTC 關於 Instagram 和 WhatsApp 收購的反壟斷訴訟；公司披露，該案可能導致資產剝離或重組等結構性救濟。此外，Meta 也持續受到隱私、數據使用、內容及未成年人規範的約束。[4]

所以，美國部分可以這樣區分：

- **Apple：較大的風險是「平台規則被拆解」**，可能影響 App Store 抽成和生態系統控制力。
- **Meta：較大的風險是「數據與資產組合能力被削弱」**，可能同時影響廣告效率、產品整合和 Instagram／WhatsApp 的整體價值。

## 綜合判斷

| 評估面向 | Apple | Meta |
|---|---|---|
| 主要被監管的核心 | App Store、支付、分發、iOS 控制權 | 個人數據、廣告定向、跨服務數據組合 |
| 直接收入影響 | 主要集中於 Services／App Store 抽成 | 直接觸及幾乎整個廣告收入模型 |
| 歐盟目前已知罰款 | 7 億歐元 | 2 億歐元 |
| 美國結構性風險 | DOJ 反壟斷、App Store 導流與支付限制 | FTC 可能要求資產剝離或重組 |
| 衝擊型態 | 集中、可能高毛利、規則明確 | 持續、滲透整個廣告漏斗 |
| 我對直接商業衝擊的判斷 | **中高，集中在平台抽成和控制權** | **較高，直接作用於核心收入和產品效果** |

**最終判斷：Meta 的直接商業衝擊比較大。**原因不是 Meta 目前罰款比 Apple 高，而是監管直接削弱 Meta 的數據—定向—廣告變現鏈條；Apple 則主要面對 App Store 抽成與封閉生態系統被迫開放的問題。可是，若未來美國或歐盟要求 Apple 進一步開放 iOS 核心權限、第三方支付和分發，Apple 的單次盈利衝擊可能會非常集中，甚至超過 Meta。

需要注意的是，兩家 10-K 都披露了重大風險，但並未提供一個可直接拆分的「DMA／美國反壟斷導致收入減少多少」的獨立數字，因此上述結論是根據收入依賴度、已實施的產品改動、罰款與潛在補救措施所作的商業敏感度比較，而不是精確的損益預測。

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt  
[8]: SEC 10-K excerpt
----- END ANSWER F0088 -----
