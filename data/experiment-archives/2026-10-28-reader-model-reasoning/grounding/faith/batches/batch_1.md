# Faithfulness batch 1 — 6 items

===== ITEM F0001 =====

QUESTION:
迪士尼最近這些麻煩，真正該看串流、票房，還是樂園業務的訊號？

----- BEGIN EVIDENCE F0001 -----
[tool 0] finnhub_stock_quote {"ticker": "DIS"}
{
 "ticker": "DIS",
 "currentPrice": 109.92,
 "open": 110.38,
 "previousClose": 110.4,
 "change": -0.48,
 "percentChange": -0.4348,
 "dayHigh": 110.38,
 "dayLow": 109.425
}

[tool 1] sec_filing_search {"query": "recent challenges streaming Disney+ profitability subscriber trends theatrical box office parks attendance per guest spending", "ticker": "DIS", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-09-27",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "DIS",
   "fiscal_year": 2025,
   "item": "Item 7",
   "prelude": "Excerpts from DIS FY2025 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 7 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001744489-25-000155/7#95",
     "title": "DIS FY2025 10-K · Item 7 · CONSOLIDATED RESULTS AND NON-SEGMENT ITEMS",
     "content": "### CONSOLIDATED RESULTS AND NON-SEGMENT ITEMS\n\nRevenues for fiscal 2025 increased 3%, or $3.1 billion, to $94.4 billion; net income attributable to Disney increased $7.4 billion to income of $12.4 billion compared to $5.0 billion in the prior year; and diluted earnings per share
(EPS) from continuing operations attributable to Disney increased to $6.85 compared to $2.72 in the prior year. The net income and EPS increases were due to a lower effective tax rate in the current year compared to the prior year and the comparison to impairments related to the Star India
Transaction and goodwill in the prior year. In addition, the increases in net income and EPS were due to higher operating income at Entertainment and Experiences. The lower effective tax rate was due to a non-cash tax benefit recognized in the current year upon a change in Hulu’s U.S. income tax
classification (see Note 9 to the Consolidated Financial Statements).\n\nRevenues\n\nService revenues for fiscal 2025 increased 3%, or $2.7 billion, to $84.6 billion, which included an approximate 3 percentage point decrease from the Star India Transaction. Aside from this impact, service revenues
increased due to higher subscription revenue, growth at our parks and experiences businesses and an increase in content sales.\n\nProduct revenues for fiscal 2025 increased 3%, or $0.3 billion, to $9.8 billion, driven by growth at our parks and experiences businesses, partially offset by lower
physical home entertainment distribution revenue due to a shift to licensing of physical distribution rights to third parties.",
     "score": 0.6024,
     "subsection": "CONSOLIDATED RESULTS AND NON-SEGMENT ITEMS"
    },
    {
     "source": "sec://0001744489-25-000155/7#120",
     "title": "DIS FY2025 10-K · Item 7",
     "content": "Revenues - Other\n\nThe decrease in other revenue was primarily due to lower recognition of minimum guarantee shortfalls from wholesale distributors and an unfavorable Foreign Exchange Impact.\n\nKey Metrics(1)\n\nPaid subscribers at:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| (in millions) | | | September 27, 2025 | | |  | | | September 28, 2024 | | |  | | | % Change   Better (Worse) | | |\n| Disney+ | | |  | | |  | | |  | | |  | | |  | | |\n|
Domestic (U.S. and Canada)(2) | | | 59.3 | |  |  | | | 56.0 | |  |  | | | 6 % | | |\n| International(3) | | | 72.4 | |  |  | | | 69.3 | |  |  | | | 4 % | | |\n| Disney+(3)(4) | | | 131.6 | |  |  | | | 125.3 | |  |  | | | 5 % | | |\n|  | | |  | | |  | | |  | | |  | | |  | | |\n| Hulu | | |  | | |  |
| |  | | |  | | |  | | |\n| SVOD Only | | | 59.7 | |  |  | | | 47.4 | |  |  | | | 26 % | | |\n| Live TV + SVOD | | | 4.4 | |  |  | | | 4.6 | |  |  | | | (4) % | | |\n| Total Hulu(2)(4) | | | 64.1 | |  |  | | | 52.0 | |  |  | | | 23 % | | |\n\nAverage Monthly Revenue Per Paid Subscriber for the
fiscal year ended:",
     "score": 0.5969
    },
    {
     "source": "sec://0001744489-25-000155/7#121",
     "title": "DIS FY2025 10-K · Item 7",
     "content": "Average Monthly Revenue Per Paid Subscriber for the fiscal year ended:\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | 2025 | | |  | | | 2024 | | |  |
| | % Change   Better (Worse) | | |\n| Disney+ | | |  | | |  | | |  | | |  | | |  | | |\n| Domestic (U.S. and Canada) | | | $ | 8.06 | |  | | | $ | 7.89 | |  | | | 2 % | | |\n| International(3) | | | 7.59 | | |  | | | 6.38 | | |  | | | 19 % | | |\n| Disney+(3) | | | 7.81 | | |  | | | 7.04 | | |  | |
| 11 % | | |\n|  | | |  | | |  | | |  | | |  | | |  | | |\n| Hulu | | |  | | |  | | |  | | |  | | |  | | |\n| SVOD Only | | | 12.36 | | |  | | | 12.35 | | |  | | | — % | | |\n| Live TV + SVOD | | | 99.85 | | |  | | | 95.12 | | |  | | | 5 % | | |\n\n(1)See discussion on page
[55](#i7d9364b45e934103988233a5397789f1_145)—Entertainment DTC Product Descriptions and Key Definitions\n\n(2)Includes 43.7 million and 27.1 million subscribers to bundles that have both Disney+ and Hulu as of September 27, 2025 and September 28, 2024, respectively.",
     "score": 0.5814
    },
    {
     "source": "sec://0001744489-25-000155/7#122",
     "title": "DIS FY2025 10-K · Item 7",
     "content": "(2)Includes 43.7 million and 27.1 million subscribers to bundles that have both Disney+ and Hulu as of September 27, 2025 and September 28, 2024, respectively.\n\n(3)The prior year Paid Subscribers and Average Monthly Revenue per Paid Subscriber have been adjusted to include Disney+
subscribers in Southeast Asia. These subscribers were previously reported with Disney+ Hotstar, which is no longer presented as this business was included in the Star India Transaction.\n\n(4)Total may not equal the sum of the column due to rounding.\n\nDomestic Disney+ average monthly revenue per
paid subscriber increased from $7.89 to $8.06 due to increases in pricing, partially offset by the impact of subscriber mix shifts.\n\nInternational Disney+ average monthly revenue per paid subscriber increased from $6.38 to $7.59 due to increases in pricing, partially offset by the impact of
subscriber mix shifts.\n\nHulu SVOD Only average monthly revenue per paid subscriber was comparable to the prior year as increases in pricing were offset by lower advertising revenue and the impact of subscriber mix shifts.\n\nHulu Live TV + SVOD average monthly revenue per paid subscriber increased
from $95.12 to $99.85 due to increases in pricing, partially offset by the impact of subscriber mix shifts and lower advertising revenue.\n\n40\n\n\n[TABLE OF CONTENTS](#i7d9364b45e934103988233a5397789f1_7)\n\nOperating Expenses",
     "score": 0.6005
    },
    {
     "source": "sec://0001744489-25-000155/7#126",
     "title": "DIS FY2025 10-K · Item 7",
     "content": "Revenues - TV/VOD and home entertainment distribution\n\nThe increase in TV/VOD and home entertainment distribution revenue was primarily due to higher TV/VOD sales of episodic content and an increase in home entertainment distribution revenue. The increase in home entertainment
distribution revenue was due to higher electronic distribution revenue, partially offset by a decrease in physical distribution revenue attributable to a shift to licensing physical distribution rights.\n\nRevenues - Theatrical distribution\n\nThe increase in theatrical distribution revenue was due
to more releases in the current year compared to the prior year. Titles in the current year included Moana 2, Lilo & Stitch, Mufasa: The Lion King, The Fantastic Four: First Steps, Captain\n\n41\n\n\n[TABLE OF CONTENTS](#i7d9364b45e934103988233a5397789f1_7)\n\nAmerica: Brave New World, Thunderbolts*
and Snow White compared to Inside Out 2, Deadpool & Wolverine, Kingdom of the Planet of the Apes, Alien: Romulus, Wish and The Marvels in the prior year.\n\nRevenues - Other\n\nOther revenue was comparable to the prior year as lower revenue from stage plays as a result of fewer performances was
partially offset by a favorable Foreign Exchange Impact, higher music revenue and increased revenue from Lucasfilm’s special effects business driven by more projects.\n\nOperating expenses\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|\n| ($ in millions) | | | 2025 | | |  | | | 2024 | | |  | | | % Change   Better (Worse) | | |\n| Programming and production costs | | | $ | (4,260) | |  | | | $ | (4,135) | |  | | | (3) % | | |\n| Other operating expenses | | | (717) | |
|  | | | (766) | | |  | | | 6 % | | |\n|  | | | $ | (4,977) | |  | | | $ | (4,901) | |  | | | (2) % | | |",
     "score": 0.5768
    },
    {
     "source": "sec://0001744489-25-000155/7#138",
     "title": "DIS FY2025 10-K · Item 7",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|\n| ($ in millions) | | | 2025 | | |  | | | 2024 | | |  | | | % Change   Better (Worse) | | |\n| Revenues | | |  |
| |  | | |  | | |  | | |  | | |\n| Theme park admissions | | | $ | 11,707 |  |  | | | $ | 11,171 |  |  | | | 5 % | | |\n| Resorts and vacations | | | 9,210 | |  |  | | | 8,375 | |  |  | | | 10 % | | |\n| Parks & Experiences merchandise, food and beverage | | | 8,491 | |  |  | | | 8,039 | |  |  | | |
6 % | | |\n| Merchandise licensing and retail | | | 4,387 | |  |  | | | 4,307 | |  |  | | | 2 % | | |\n| Parks licensing and other | | | 2,361 | |  |  | | | 2,259 | |  |  | | | 5 % | | |\n| Total revenues | | | 36,156 | |  |  | | | 34,151 | |  |  | | | 6 % | | |\n| Operating expenses | | | (19,224)
| |  |  | | | (18,356) | |  |  | | | (5) % | | |\n| Selling, general, administrative and other | | | (4,114) | |  |  | | | (3,944) | |  |  | | | (4) % | | |",
     "score": 0.5776
    },
    {
     "source": "sec://0001744489-25-000155/7#140",
     "title": "DIS FY2025 10-K · Item 7",
     "content": "Revenues - Theme park admissions\n\nThe increase in theme park admissions revenue was due to an increase of 4% from higher average per capita ticket revenue.\n\n45\n\n\n[TABLE OF CONTENTS](#i7d9364b45e934103988233a5397789f1_7)\n\nRevenues - Resorts and vacations\n\nGrowth in resorts
and vacations revenue was primarily attributable to increases of 5% from additional passenger cruise days, 2% from higher occupied hotel room nights and 1% from increased unit sales at Disney Vacation Club. The increase in passenger cruise days reflected the launch of the Disney Treasure in the
first quarter of the current year.\n\nRevenues - Parks & Experiences merchandise, food and beverage\n\nParks & Experiences merchandise, food and beverage revenue growth was primarily due to increases of 3% from higher average guest spending and 1% from volume growth.\n\nRevenues - Merchandise
licensing and retail\n\nHigher merchandise licensing and retail revenue was due to an increase of 3% from merchandise licensing, partially offset by a decrease of 1% from an unfavorable Foreign Exchange Impact.\n\nRevenues - Parks licensing and other\n\nThe increase in parks licensing and other
revenue was driven by sponsorship and co-branding revenue growth, higher real estate sales and an increase in royalties from Tokyo Disney Resort, partially offset by an unfavorable Foreign Exchange Impact.\n\nKey Metrics\n\nIn addition to revenue, costs and operating income, management uses the
following key metrics to analyze trends and evaluate the overall performance of our theme parks and resorts, and we believe these metrics are useful to investors in analyzing the business:",
     "score": 0.5982
    }
   ]
  },
  {
   "ticker": "DIS",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from DIS FY2025 10-K, Item 1A (Risk Factors) — 2 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001744489-25-000155/1a#47",
     "title": "DIS FY2025 10-K · Item 1A",
     "content": "For example, COVID-19 and measures to prevent its spread impacted our businesses in a number of ways, including the closure of our theme parks and resorts, suspension of cruise ship sailings and guided tours, delayed, or in some cases, shortened or canceled, theatrical releases and
disruptions in the production and availability of content, significantly reducing revenues across all of our segments. Certain of our business operations have been temporarily disrupted by payment processing outages and widespread computing failures. Hurricanes have caused park closures and other
impacts to the operations of Walt Disney World Resort, adversely affecting segment results, and may do so in the future. The Company has ceased certain operations in certain regions, including in response to sanctions, trade restrictions and related developments, resulting in impairment
charges.\n\nIn addition, we derive affiliate fees and royalties from the distribution of our programming, sales of our licensed products and services by third parties, and the management of businesses operated under brands licensed from the Company and advertising revenues from the purchase of
advertising on our various platforms, including DTC services and linear networks, and we are therefore dependent on the successes of those third parties for that portion of our revenue. Our results of operations could be adversely impacted by a significant contraction of distribution channels for
our products and services, including through third-party licensees or sellers of our licensed goods and services, or a contraction in the number or kind of advertisers purchasing advertising on our platforms, including as a result of legal or regulatory developments. In addition, third-party
suppliers provide products and services essential to the operation of a number of our businesses. A wide variety of factors could influence the success of those third parties and if negative factors significantly impacted a sufficient number of those third parties or materially impacted a supplier
of a significant product or service, our results of operations could be adversely affected. In specific geographic markets, we have experienced delayed and/or partial payments from certain third parties due to liquidity issues.\n\nWe obtain insurance against the risk of losses relating to some of
these events, generally including certain physical damage to our property and resulting business interruption, certain injuries occurring on our property and some liabilities for alleged breach of legal responsibilities. When insurance is obtained it is subject to deductibles, exclusions, terms,
conditions and limits of liability. The types and levels of coverage we obtain vary from time to time depending on our view of the likelihood of specific types and levels of loss in relation to the cost of obtaining coverage for such types and levels of loss and we experience losses not covered by
our insurance, which could be material.",
     "score": 0.5966
    },
    {
     "source": "sec://0001744489-25-000155/1a#49",
     "title": "DIS FY2025 10-K · Item 1A",
     "content": "19\n\n\n[TABLE OF CONTENTS](#i7d9364b45e934103988233a5397789f1_7)\n\nin strategy, we have impaired the value of our content primarily at our DTC services and goodwill and intangible assets at our linear networks and impaired the value of certain of our retail store assets and
certain hotel experiences assets. We may write down other assets as our strategy evolves to account for the business environment.\n\nWe also make investments in existing or new businesses, including investments in international expansion of our business and in new business lines. For example, in
recent years, we have expanded our fleet of cruise ships, with announced plans for further fleet expansion, and increased investment in our parks and resorts; completed the acquisition of Hulu and of a 70% interest in Fubo; and made substantial investments related to DTC offerings. The ultimate
success of these investments is uncertain, some of these and future investments may ultimately result in returns that are negative or lower than anticipated, and these investments may negatively impact the resources available to our other businesses and ultimately, our results of operations. In
addition, our costs increase in connection with these investments, and we may have significant charges associated with the write-down of assets if the investments are not as successful as anticipated. Over the long term, our new strategies could be less successful than previous strategies. Even if
our strategies are effective in the long term, our new offerings generally negatively impact results of operations in the short term, results of our new offerings are unlikely to be even quarter over quarter and we may not expand into new markets as or when anticipated. Our ability to forecast for
new businesses is impacted by our lack of experience operating in those new businesses, speed with which the competitive landscape changes, volatility beyond our control (such as the events beyond our control noted above) and our ability to obtain or develop the content and rights on which our
projections are based. Accordingly, we may not achieve our forecasted outcomes.\n\nIncreased competitive pressures impact our revenues, increase our costs and impact our results of operations.\n\nWe face substantial competition in each of our businesses from alternative providers of the products and
services we offer and from other forms of entertainment, lodging, tourism and recreational activities. This includes, among other types, competition for personnel, content and other resources we require in operating our businesses. For example:",
     "score": 0.5763
    }
   ]
  },
  {
   "ticker": "DIS",
   "fiscal_year": 2025,
   "item": "Item 1",
   "prelude": "Excerpts from DIS FY2025 10-K, Item 1 (Business) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001744489-25-000155/1#8",
     "title": "DIS FY2025 10-K · Item 1",
     "content": "As of September 27, 2025, the estimated number of paid Hulu subscribers, based on internal management reports, was approximately 64 million.\n\nOn October 29, 2025, the Company and FuboTV Inc. (Fubo), a publicly traded vMVPD, combined certain of Hulu Live TV assets, including its
carriage agreements, subscription agreements and related data, advertising and sponsorship agreements and intellectual property exclusively related to the “Live TV” brand, with Fubo. The Company has a 70% interest in the combined entity, with the remaining 30% interest retained by Fubo shareholders.
Hulu Live TV will continue to be available to consumers as a separate offering post-closing. See Note 4 of the Consolidated Financial Statements for further information.\n\nContent Sales/Licensing and Other\n\nThe majority of Content Sales/Licensing revenue is derived from distribution in the
theatrical, TV/VOD and home entertainment windows. In addition, revenue is generated from music distribution, stage plays and post-production services through Industrial Light & Magic and Skywalker Sound.\n\nThe Company also publishes National Geographic magazine, which is reported with Content
Sales/Licensing.\n\nTheatrical Distribution\n\nThe Company licenses full-length live-action and animated films to theaters globally. Cumulatively through fiscal year 2025, the Company has released approximately 1,100 full-length live-action films and 100 full-length animated films. Domestically and
in most major international markets, we distribute and market our films directly. In certain international markets our films are distributed by independent companies. In some territories, certain films may be exclusively distributed on our DTC streaming services. During fiscal year 2026, we expect
to release approximately 20 films.\n\nThe Company incurs significant marketing and advertising costs before and throughout the theatrical release of a film in an effort to generate public awareness of the film, to increase the public’s intent to view the film and to help generate consumer interest
in the subsequent home entertainment and other ancillary markets. These costs are expensed as incurred, which may result in a loss on the theatrical distribution of a film, including in periods prior to the release of the film.\n\nTV/VOD Distribution\n\nWe license our content to third-party
television networks, television stations and other video service providers for distribution to viewers on television or a variety of internet-connected devices, including through other DTC services.\n\nHome Entertainment Distribution",
     "score": 0.5781
    }
   ]
  }
 ]
}

[tool 2] finnhub_company_basic_financials {"ticker": "DIS"}
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

[tool 3] tavily_financial_search {"query": "Disney DIS recent problems streaming box office parks business latest news", "ticker": "DIS"}
{
 "query": "DIS Disney DIS recent problems streaming box office parks business latest news",
 "results": [
  {
   "title": "Disney (DIS) earnings Q2 2026",
   "url": "https://www.cnbc.com/2026/05/06/disney-dis-earnings-q2-2026.html",
   "content": "Recent box-office wins, including \"Avatar: Fire and Ash,\" and \"Zootopia 2,\" also helped lift the unit's revenue.\n\nLast quarter Disney stopped reporting some details for the entertainment segment, including the breakdown of revenue and operating income for its linear TV networks.
The company has also stopped reporting quarterly streaming subscriber numbers.\n\nThe continued declines in linear TV due to the consumer shift to streaming has weighed on Disney and its peers in prior quarters. [...] Disney's entertainment segment – which includes its traditional TV, streaming and
theatrical releases – saw revenue increase 10% to $11.72 billion compared with the same period last year. Entertainment revenue got a 4% boost from the closed Fubo deal, Disney said.\n\nSubscription and affiliate fees climbed 14% to $7.8 billion, boosted by recent streaming price hikes. Advertising
revenue was also up, jumping 5%, in part due to higher impressions linked to streaming. [...] ESPN's direct-to-consumer streaming app – which launched in August – was a bright spot in the most recent quarter. The company said revenue generated from its digital subscribers during the period more than
offset the declines in the traditional TV ecosystem.",
   "published_date": null
  },
  {
   "title": "Watch Disney (DIS US) Beats Profit Estimates on Streaming, Parks - Bloomberg",
   "url": "https://www.bloomberg.com/news/videos/2025-08-06/disney-beats-profit-estimates-on-streaming-parks-video",
   "content": "Aug 6th, 2025\n\nDisney Beats Profit Estimates on Streaming, Parks\n\nDisney saw better-than-expected third-quarter earnings on the strength of continued growth at its parks and streaming business, while income from conventional entertainment TV fell 28% and the Disney film studio
suffered a loss. Richard Greenfield partner and analyst: media & technology at Lightshed Partners examines the results.",
   "published_date": null
  },
  {
   "title": "Disney (DIS)Reports Lower Streaming TV Loss, Boosts Profit Outlook - Bloomberg",
   "url": "https://www.bloomberg.com/news/articles/2024-05-07/disney-reports-lower-streaming-tv-loss-boosts-profit-outlook",
   "content": "The media giant added more than 6 million subscribers in the second quarter to its core Disney+ streaming offering, which includes popular movies and the cartoon phenomenon Bluey. And losses in the direct-to-consumer streaming business, which includes ESPN+, narrowed to $18 million in
the period from a loss of $659 million in the year earlier quarter. [...] # Disney Shares Decline on Outlook Despite Path to Profit\n\n Park visits expected to moderate from post-Covid pace\n Disney+ not expected to see subscriber growth in third quarter\n\nThis article is for subscribers
only.\n\nWalt Disney Co. shares tumbled the most in a year and a half after the company reported a tepid outlook for growth in streaming subscribers in the current quarter and said that visits to parks are expected to moderate from peak post-Covid levels.",
   "published_date": null
  },
  {
   "title": "Disney shares drop as streaming costs drag on earnings | Reuters",
   "url": "https://www.reuters.com/business/media-telecom/disney-streaming-beats-wall-street-targets-earnings-miss-2022-11-08",
   "content": "Nov 8 (Reuters) - Walt Disney Co (DIS.N) missed Wall Street earnings forecasts on Tuesday as the entertainment giant racked up more losses from its push into streaming video, sending its shares tumbling 9%.\n\nThe company gained more streaming customers than analysts had expected from
July through September, but media investors have increasingly focused on profits over streaming subscription numbers.\n\nSign up here. [...] The parks, experiences and products group reported revenue of $7.4 billion in the quarter, beating analysts' forecasts. Operating income reached $1.5 billion,
more than double a year ago. The hurricane cost the company an estimated $65 million, McCarthy said.\n\nNollen wrote that higher prices, and the technology Disney uses to distribute demand, have produced a 40% increase in spending per person since 2019. [...] \"The journey feels somewhat akin to
Netflix's path,\" PP Foresight analyst Paolo Pescatore said. \"Expect more bumps ahead and further losses in the streaming business as there's no silver bullet to profitability.\"\n\nOther media companies are struggling to grow their streaming services while delivering on Wall Street's profit
expectations.",
   "published_date": null
  },
  {
   "title": "Disney earnings beat estimates as new CEO outlines growth strategy | Reuters",
   "url": "https://www.reuters.com/business/media-telecom/disney-earnings-beat-estimates-new-ceo-outlines-growth-strategy-2026-05-06",
   "content": "LOS ANGELES, May 6 (Reuters) - Walt Disney's (DIS.N) new Chief Executive Josh D'Amaro laid out his strategy for the entertainment company Wednesday, saying it would remain committed to creative excellence, strengthen its streaming business, capitalize on the ​power of live sports and
continue to invest in its theme parks and cruise lines. [...] At the entertainment unit, operating income rose by 6% to $1.34 billion. The boost came partly from higher subscription and advertising revenue from streaming services including Disney+. Movie box-office hits \"Zootopia 2\" and \"Avatar:
Fire and Ash,\" released last year, continued to contribute during the ​quarter. [...] D'Amaro succeeded Bob Iger as Disney CEO in mid-March and is steering the company through a ​consumer shift to streaming, the advent of artificial intelligence tools, and a challenging economy hit by higher oil
prices and fewer international ​visitors to its theme parks.",
   "published_date": null
  }
 ]
}
----- END EVIDENCE F0001 -----

----- BEGIN ANSWER F0001 -----
**結論：目前最該看的是「串流獲利化＋樂園需求」，而不是單看票房。** 票房是高波動的內容週期訊號；真正能判斷迪士尼基本面是否改善的，是串流能否持續提高收入與利潤，以及樂園在價格上漲後仍能維持客流與消費。

### 1. 串流：最重要的結構性訊號

迪士尼 FY2025 10-K（截至 2025-09-27）顯示，Disney+ 付費訂戶增至 1.316 億，年增 5%；Hulu 總訂戶增至 6,410 萬，年增 23%[1]。更值得注意的是，Disney+ 全球平均每位付費訂戶月收入由 7.04 美元升至 7.81 美元，增幅 11%，主要來自提價[2]。

所以現在不應只問「訂戶還有沒有成長」，而要看：

- Disney+ 是否能持續提價而不造成大量流失；
- 串流內容成本是否受控；
- 串流營業利益是否能抵銷傳統電視網路的下滑；
- 廣告收入與 Disney+/Hulu 綁定是否改善每位用戶價值。

這是迪士尼從「追求訂戶」轉向「追求獲利」的核心驗證。近期報導也指出，市場已更重視串流利潤，而不只是訂戶數；迪士尼過去曾因串流虧損與公園成長放緩而承壓。[3]

### 2. 樂園：目前最健康，但要防「漲價掩蓋需求變弱」

FY2025，Parks & Experiences 營收增長 6% 至 361.56 億美元[4]。其中：

- 主題樂園門票收入增 5%，但主要由**每位遊客平均票價提高 4%**帶動；
- 飯店與度假收入增 10%，部分來自新增郵輪航程；
- 餐飲與商品收入增 6%，其中平均客戶消費增 3%、客流量只增 1%[5]。

這代表樂園目前仍是迪士尼最可靠的現金流與獲利支柱，但訊號並非完全無瑕：收入成長較多依賴提價、每客消費與新增供給，而不是強勁的客流增長。

因此要密切觀察：

- 入園人次是否持續放緩；
- 每位遊客消費能否抵銷客流疲弱；
- 美國消費者是否開始削減高價旅遊；
- 國際遊客、郵輪與新設施能否帶來真正的增量。

### 3. 票房：重要，但不適合當成單獨的投資判斷

FY2025 票房收入增加，主要原因是當年度上映作品較多，包括《Moana 2》、《Lilo & Stitch》、《Mufasa: The Lion King》等，而前一年則有《Inside Out 2》和《Deadpool & Wolverine》等作品[6]。

這說明票房對迪士尼很重要，因為成功電影會帶動：

- 院線收入；
- Disney+ 內容價值；
- 商品授權；
- 樂園角色與主題設施；
- 品牌熱度。

但票房本身高度依賴上映檔期與單部電影成敗。迪士尼也在 10-K 中說明，電影上映前就要承擔大量行銷成本，單部電影可能在上映前或上映期間造成虧損[7]。因此，票房更像是「內容供應鏈的領先指標」，不是最穩定的基本面指標。

### 我的排序

**第一：串流獲利化。**  
這決定迪士尼能否完成從傳統電視轉向數位媒體的轉型。

**第二：樂園客流與消費。**  
這是目前最穩定的業務，但要確認成長不是只靠漲價和新供給。

**第三：票房。**  
看作品組合與長期內容品質，不要因單季爆款或失敗就過度解讀。

目前 DIS 股價約 109.92 美元，當日下跌約 0.43%；Finnhub 顯示其預期本益比約 13.9 倍、TTM 營收年增約 4.6%，但 TTM EPS 年減 24%[8]。這種估值並不算極端昂貴，但市場仍需要看到獲利品質改善，而不只是營收增長。

**簡化成一句話：**如果串流利潤持續改善、樂園客流沒有明顯崩跌，票房短期失誤未必是大問題；但若串流重新擴大虧損、樂園客流下滑且只能靠漲價維持收入，那才是更嚴重的訊號。

[1]: SEC 10-K excerpt
[2]: SEC 10-K excerpt
[3]: https://www.reuters.com/business/media-telecom/disney-streaming-beats-wall-street-targets-earnings-miss-2022-11-08 "Disney shares drop as streaming costs drag on earnings"
[4]: SEC 10-K excerpt
[5]: SEC 10-K excerpt
[6]: SEC 10-K excerpt
[7]: SEC 10-K excerpt
[8]: Finnhub DIS company basic financials and real-time quote data
----- END ANSWER F0001 -----

===== ITEM F0002 =====

QUESTION:
分析輝達、禮來、好市多這幾種高品質贏家裡，誰最容易先被市場重新下修期待。

----- BEGIN EVIDENCE F0002 -----
[tool 0] sec_filing_search {"query": "key business risks demand concentration pricing competition customer concentration inventory supply chain artificial intelligence", "ticker": "NVDA", "fiscal_year": null}
{
 "fiscal_year": 2026,
 "fiscal_year_end": "2026-01-25",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "NVDA",
   "fiscal_year": 2026,
   "item": "Item 1A",
   "prelude": "Excerpts from NVDA FY2026 10-K, Item 1A (Risk Factors) — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001045810-26-000021/1a#35",
     "title": "NVDA FY2026 10-K · Item 1A · Risks Related to Our Industry and Markets",
     "content": "### Risks Related to Our Industry and Markets\n\n•Failure to meet the evolving needs of our industry and markets may adversely impact our financial results.\n\n•Competition could adversely impact our market share and financial results.",
     "score": 0.5186,
     "subsection": "Risks Related to Our Industry and Markets"
    },
    {
     "source": "sec://0001045810-26-000021/1a#36",
     "title": "NVDA FY2026 10-K · Item 1A · Risks Related to Demand, Supply, and Manufacturing",
     "content": "### Risks Related to Demand, Supply, and Manufacturing\n\n•Long manufacturing lead times and uncertain supply and capacity availability, combined with a failure to estimate customer demand accurately has led and could lead to mismatches between supply and demand.\n\n12\n\n\n[Table
of Contents](#i82ea215a7c1f4862b6518f1348ddc832_7)\n\n•Dependency on third-party suppliers and their technology to manufacture, assemble, test, or package our products reduces our control over product quantity and quality, manufacturing yields, and product delivery schedules and could harm our
business.\n\n•Defects in our products have caused and could cause us to incur significant expenses to remediate and could damage our business.",
     "score": 0.5387,
     "subsection": "Risks Related to Demand, Supply, and Manufacturing"
    },
    {
     "source": "sec://0001045810-26-000021/1a#37",
     "title": "NVDA FY2026 10-K · Item 1A · Risks Related to Our Global Operating Business",
     "content": "### Risks Related to Our Global Operating Business\n\n•Adverse economic conditions may harm our business.\n\n•International sales and operations are a significant part of our business, which exposes us to risks that could harm our business.\n\n•Product, system security and data
protection incidents or breaches, as well as cyber-attacks could disrupt our operations and adversely affect our financial condition, stock price and reputation.\n\n•Business disruptions could harm our operations and financial results.\n\n•Climate change may have a long-term impact on our
business.\n\n•We may not be able to realize the potential benefits of business investments or acquisitions, nor successfully integrate acquisition targets.\n\n•A significant amount of our revenue stems from a limited number of partners and distributors and we have a concentration of sales to
customers who purchase directly or indirectly from us, and our revenue could be adversely affected if we lose or are prevented from selling to any of these customers.\n\n•Commercial arrangements expose us to counterparty risks, which may negatively impact our business, financial condition, or
results of operations.\n\n•We may be unable to attract, retain, and motivate our executives and key employees.\n\n•Modification or interruption of our business processes and information systems may disrupt our business and internal controls.\n\n•Our operating results have in the past fluctuated and
may in the future fluctuate, and if our operating results are below the expectations of securities analysts or investors, our stock price could decline.",
     "score": 0.5286,
     "subsection": "Risks Related to Our Global Operating Business"
    },
    {
     "source": "sec://0001045810-26-000021/1a#42",
     "title": "NVDA FY2026 10-K · Item 1A",
     "content": "14\n\n\n[Table of Contents](#i82ea215a7c1f4862b6518f1348ddc832_7)\n\nfoundry capacity and scarce input materials during a supply-constrained environment, which could harm our business. Some of our customers have in-house expertise and internal development capabilities similar to
some of ours and can use or develop their own solutions to replace those we are providing. For example, others may offer cloud-based services that compete with our AI cloud service offerings, and we may not be able to establish market share sufficient to achieve the scale necessary to meet our
business objectives. If we are unable to successfully compete in this environment, demand for our products, services and technologies could decrease, which may negatively impact our business.",
     "score": 0.5855
    },
    {
     "source": "sec://0001045810-26-000021/1a#43",
     "title": "NVDA FY2026 10-K · Item 1A · Risks Related to Demand, Supply, and Manufacturing",
     "content": "### Risks Related to Demand, Supply, and Manufacturing\n\nLong manufacturing lead times and uncertain supply and capacity availability, combined with a failure to estimate customer demand accurately, has led and could lead to mismatches between supply and demand.\n\nWe have long
manufacturing lead times and build finished products and maintain inventory in advance of anticipated demand. In periods of shortages impacting the semiconductor industry and/or limited supply or capacity in our supply chain, the lead times for certain supply may be extended. We have previously
experienced and may continue to experience extended lead times of more than 12 months. To secure future supply and capacity, we have paid premiums, provided deposits, and entered into long-term supply agreements and capacity commitments, which have increased our product costs and this may continue.
We may still be unable to secure sufficient commitments for capacity to address our business needs.\n\nIf we inaccurately estimate demand, or our customers change orders, as we have experienced in the past, we may not be able to reduce our supply commitments in time, at the same rate, or at all.
Significant mismatches between supply and demand have varied across our market platforms, resulted in both product shortages and excess inventory, significantly harmed our financial results and could reoccur. If we underestimate demand, and our foundry partners and contract manufacturers are unable
to increase production or provide sufficient supply, we may not be able to meet increased customer demand in a timely manner, or at all. Our reputation and customer relationships could be damaged and we could lose revenue and market share. Additionally, since some of our products are part of a
complex data center buildout, supply constraints or availability issues with respect to any one component have had and may have a broader revenue impact. For example, our ability to sell certain products has been and could be impeded if components necessary for the finished products are not
available from third parties.",
     "score": 0.5365,
     "subsection": "Risks Related to Demand, Supply, and Manufacturing"
    },
    {
     "source": "sec://0001045810-26-000021/1a#44",
     "title": "NVDA FY2026 10-K · Item 1A",
     "content": "If we overestimate demand, or if customers cancel or defer orders or choose to purchase from our competitors, we may not be able to utilize on-hand inventory or reduce purchase commitments accordingly. We have had to reduce average selling prices, including due to our channel
pricing programs, increase prices for certain of our products as a result of our suppliers’ increase in prices, write down our inventory, incur cancellation penalties, and record impairments, and may have to do so in the future. The impact of these risks would be amplified by our non-cancellable and
non-returnable purchase orders placed in advance of our historical lead times and could be exacerbated if we need to make changes to the design of future products. These risks have increased and may continue to increase as our purchase obligations and prepaids have grown and are expected to continue
to grow and become a greater portion of our total supply. All of these factors may negatively impact our gross margins and financial results.\n\nFactors that have caused and/or could in the future cause us to underestimate or overestimate demand, and impact the timing and volume of our revenue,
include:\n\n•changes in product development cycles and time to market;\n\n•competing technologies and competitor product releases, announcements or other actions;\n\n•changes in business and economic conditions;\n\n•sudden or sustained government lockdowns or public health issues;\n\n•rapidly
changing technology or customer requirements;\n\n•the availability of sufficient data center capacity or energy for customers to procure;\n\n•new product introductions and transitions resulting in less demand for existing products;\n\n•new or unexpected end-use cases;\n\n•increase in demand for
competitive products;\n\n•changes in end-user demand;\n\n•purchasing decisions made, and inventory levels held by, distributors, ODMs, OEMs, system integrators, other channel partners and other third parties;\n\n15\n\n\n[Table of Contents](#i82ea215a7c1f4862b6518f1348ddc832_7)\n\n•the ability of
developers, end customers and other third parties to build, enhance, and maintain accelerated computing applications that leverage our platforms;\n\n•the demand for accelerated computing, AI-related cloud services, or large language models;\n\n•changes that impact the ecosystem for the architectures
underlying our products and technologies;\n\n•government actions or changes in governmental policies, such as export controls, increased restrictions on gaming usage, or tariffs;",
     "score": 0.5617
    },
    {
     "source": "sec://0001045810-26-000021/1a#45",
     "title": "NVDA FY2026 10-K · Item 1A",
     "content": "•changes that impact the ecosystem for the architectures underlying our products and technologies;\n\n•government actions or changes in governmental policies, such as export controls, increased restrictions on gaming usage, or tariffs;\n\n•our customers’ and partners’ ability to
secure capital and energy and to build complex datacenter infrastructure timely; and\n\n•the availability of third-party content on our platforms, such as GeForce NOW.\n\nThe availability of data centers, energy, and capital to support the buildout of NVIDIA AI infrastructure by our customers and
partners is crucial, and any shortage of these and other necessary resources could impact our future revenue and financial performance. Expanding energy capacity to meet demand is a complex, multi-year process involving significant regulatory, technical, and construction challenges. In addition,
access to capital can be particularly constrained for less-capitalized companies, which may face difficulties securing financing for large-scale infrastructure projects. These limitations could delay customer and partner deployments or reduce the scale of accelerated computing and AI
adoption.\n\nChallenges in estimating demand could become more pronounced or volatile in the future on both a global and regional basis. Extended lead times may occur if we experience other supply constraints caused by natural disasters, pandemics or other events. Geopolitical tensions in regions
where we rely on suppliers, contract manufacturers, and assembly partners that are critical to our supply continuity, could have a material adverse impact on us. Publicly announced intentions by governments or other companies to purchase our products can further complicate our demand estimates, as
such announcements are often non-binding and may not result in committed volumes.\n\nWe continue to increase our supply and capacity purchases with existing and new suppliers to support our demand projections and increasing complexity of our data center products. We expect supply constraints to be a
headwind to Gaming in the first quarter of fiscal year 2027 and beyond. We have also entered and may continue to enter into prepaid manufacturing and capacity agreements to supply both current and future products. The increased purchase volumes and integration of new suppliers and contract
manufacturers into our supply chain creates more complexity in managing multiple suppliers with variations in production planning, execution and logistics. Our expanding product portfolio and varying component compatibility and quality may lead to increased inventory levels. We have incurred and may
in the future incur inventory provisions or impairments if our inventory or supply or capacity commitments exceed demand for our products or demand declines.",
     "score": 0.5115
    },
    {
     "source": "sec://0001045810-26-000021/1a#53",
     "title": "NVDA FY2026 10-K · Item 1A",
     "content": "International sales and operations are a significant part of our business, which exposes us to risks that could harm our business.\n\nWe sell our products internationally, and we also have operations and conduct business internationally. Our semiconductor wafers are manufactured,
assembled, tested and packaged by third parties located outside of the United States, and we generated 31% of our revenue in fiscal year 2026 from sales outside the United States. The market in China, where our offerings are limited by export controls, is highly competitive and we expect it to
remain competitive going forward. The global nature of our business subjects us to a number of risks and uncertainties, which have had in the past and could in the future have a material adverse effect on our business, financial condition and results of operations. These include domestic and
international economic and political conditions in countries in which we and our suppliers and manufacturers do business, government lockdowns to control case spread of global or local health issues, differing legal standards with respect to protection of IP and employment practices, different
domestic and international business and cultural practices, disruptions to capital markets, counter-inflation policies, currency fluctuations, natural disasters, acts of war or other military actions, terrorism, public health issues, restrictions on international trade, such as tariffs, sanctions,
and other controls on imports or exports, and catastrophic events.\n\nProduct, system security, and data protection incidents or breaches, as well as cyber-attacks, could disrupt our operations, reduce our expected revenue, increase our expenses, and significantly harm our business and
reputation.\n\nSecurity breaches, computer malware, social-engineering attacks, denial-of-service attacks, software bugs, server malfunctions, software or hardware failures, loss of data or other information technology assets, and other cyber-attacks are becoming increasingly sophisticated, making
it more difficult to successfully detect, defend against them or implement adequate preventative measures.\n\nCyber-attacks, including ransomware attacks by organized criminal threat actors, nation-states, and nation-state-supported actors, may become more prevalent and severe. Our ability to
recover from ransomware attacks may be limited if our backups have been affected by the attack, or if restore from backups is delayed or not feasible.\n\nIndividuals, groups of hackers and sophisticated organizations, including nation-states and nation-state-supported actors, and other threat actors
have engaged and are expected to continue to engage in cyber-attacks. Additionally, some actors are using AI technology to launch more automated, targeted and coordinated attacks. Due to geopolitical conflicts\n\n19",
     "score": 0.5276
    },
    {
     "source": "sec://0001045810-26-000021/1a#65",
     "title": "NVDA FY2026 10-K · Item 1A",
     "content": "We have experienced periods where we receive a significant amount of our revenue from a limited number of customers, and this trend may continue. For fiscal year 2026, sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14%
of total revenue, all of which were primarily attributable to the Compute & Networking segment. With several of these partners, we are selling multiple products and systems in our portfolio through their channels. Our operating results depend on sales to our partner network, as well as the ability
of these partners to sell products that incorporate our technologies. We have a small number of partners that are involved in system integration with our key customers. As our system design becomes increasingly complex, system integrators may be unable to meet specifications of our key customers.
Changes in our partners' or customers' business models or their ownership can reduce the number of partners available to us and harm our ability to sell our advanced data center systems to customers. In the future, these partners may decide to purchase fewer products, not to incorporate our products
into their ecosystem, or to alter their purchasing patterns in some other way. Because most of our sales are made on a purchase order basis, our customers can generally cancel, change, or delay product purchase commitments with little notice to us and without penalty. Our partners or customers may
develop their own solutions; our customers may purchase products from our competitors; and our partners may discontinue sales or lose market share in the markets for which they purchase our products, all of which may alter partners’ or customers’ purchasing patterns. Many of our indirect customers
often do not purchase directly from us but through multiple OEMs, ODMs, system integrators, distributors, and other channel partners. We generate a significant amount of our revenue from a limited number of indirect customers, and we estimate some individually representing 10% or more of our
revenue. If end demand increases or our finished goods supply availability is concentrated near a quarter end, the system integrators, distributors, and channel partners may have limited ability to increase their credit, which could impact the timing and amount of our revenue. The loss of any of our
large customers, a significant reduction in purchases by them, our inability to sell to a customer due to U.S. or other countries’ trade restrictions, or any difficulties in collecting accounts receivable would likely harm our financial condition and results of operations.\n\nCommercial arrangements
expose us to counterparty risks.",
     "score": 0.5087
    },
    {
     "source": "sec://0001045810-26-000021/1a#82",
     "title": "NVDA FY2026 10-K · Item 1A",
     "content": "Issues relating to the responsible use of our technologies, including AI in our offerings, may result in reputational or financial harm and liability.\n\nConcerns relating to the responsible use of new and evolving technologies, such as AI, in our products and services may result in
reputational or financial harm and liability and may cause us to incur costs to resolve such issues. We are increasingly building AI capabilities and protections into many of our products and services, and we also offer stand-alone AI applications. AI poses emerging legal, social, and ethical issues
and presents risks and challenges that could affect its adoption, and therefore our business. If we enable or offer solutions that draw controversy due to their perceived or actual impact on society, such as AI solutions that have unintended consequences, infringe copyright or rights of publicity,
or are controversial because of their impact on human rights, privacy, employment or other social, economic or political issues, or if we are unable to implement effective internal policies and frameworks relating to the responsible development and use of AI models and systems offered through our
sales channels, we may experience brand or reputational harm, competitive harm or legal liability. Leveraging AI capabilities to potentially improve our internal functions and operations may present further risks, costs, and challenges. Complying with multiple regulations from different
jurisdictions related to AI may further increase our cost of doing business, may change the way that we operate in certain jurisdictions, and may impede our ability to offer certain products and services in certain jurisdictions if we are unable to comply with regulations. Compliance with existing
and proposed government regulation of AI, including in jurisdictions such as the European Union, may further increase the cost of related research and development, and create additional reporting and/or transparency requirements. For example, regulation adopted in response to the European Union Code
of Practice for General Purpose Artificial Intelligence could require us to notify the European Commission regarding details of some of our Trustworthy AI processes related to our risk framework. Furthermore, changes in AI-related regulation could disproportionately impact and disadvantage us and
require us to change our business practices, which may negatively impact our financial results. Our failure to adequately address concerns and regulations relating to the responsible use of AI by us or others could undermine public confidence in AI and slow adoption of AI in our products and
services or cause reputational or financial harm.\n\nActions to adequately protect our IP rights could result in substantial costs to us and our ability to compete could be harmed if we are unsuccessful or if we are prohibited from making or selling our products.",
     "score": 0.5119
    }
   ]
  }
 ]
}

[tool 1] sec_filing_search {"query": "key business risks membership renewal consumer spending competition pricing inflation supply chain", "ticker": "COST", "fiscal_year": null}
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
     "score": 0.606
    },
    {
     "source": "sec://0000909832-26-000093/unknown#15",
     "title": "COST FY2026 10-K",
     "content": "We may not timely identify or effectively respond to consumer tastes and preferences, which could negatively affect our relationship with our members, the demand for our products and services, and our market share.\n\nIt is difficult to consistently and successfully predict the
products and services that our members will desire. Our success depends, in part, on our ability to identify and respond to trends in demographics and consumer preferences. Failure to identify timely or effectively respond to changing consumer tastes, preferences and spending patterns including
those related to resource efficiency, environmental protection, human rights, and the transition to a low-carbon economy could negatively affect our relationship with our members, the demand for our products and services, and our market share. We sell a substantial amount of gasoline, the demand for
which could be impacted by concerns and regulation about climate change.\n\nIf we are not successful at predicting our sales trends and adjusting our purchases accordingly, we may have excess inventory, which could result in additional markdowns, or we may experience out-of-stock positions and
delivery delays, which could result in higher costs, both of which would reduce our operating performance. This could have an adverse effect on net sales, gross margin and operating income.\n\n10\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nAvailability and performance of our
IT systems are vital to our business. Failure to successfully execute IT projects and have IT systems available to our business would adversely impact our operations.",
     "score": 0.5506
    },
    {
     "source": "sec://0000909832-26-000093/unknown#19",
     "title": "COST FY2026 10-K",
     "content": "We are subject to payment-related risks.\n\nWe accept payments using a variety of methods, including select credit and debit cards, cash and checks, co-brand cardholder rebates, Executive member reward certificates, and our shop card. As we offer new payment options to our members,
we may be subject to additional rules, regulations, compliance requirements, and higher fraud losses. For certain payment methods, we pay interchange and other related acceptance fees, along with additional transaction processing fees. We rely on third parties to provide payment transaction
processing services for credit and debit cards and our shop card. It could disrupt our business if these parties become unwilling or unable to provide these services to us. We are also subject to fee increases by these service providers.\n\nWe must comply with evolving payment card association and
network operating rules, including data security rules, certification requirements, and rules governing electronic funds transfers. For example, we are subject to Payment Card Industry Data Security Standards, which contain compliance guidelines and standards with regard to our security surrounding
the physical and electronic storage, processing, and transmission of individual cardholder data. If our internal systems are breached or compromised, we may be liable for card re-issuance costs, subject to fines and higher transaction fees, and lose our ability to accept card payments from our
members, and our business and operating results could be adversely affected. Our failure to offer payment methods desired by our members could create a competitive disadvantage.\n\nWe might sell products that cause illness or injury to our members, harm to our reputation, and expose us to
litigation.\n\nIf our merchandise, including food and prepared food products for human consumption, drugs, children's products, pet products, and durable goods, do not meet or are perceived not to meet applicable safety or labeling standards or our members' expectations, we could experience lost
sales, increased costs, litigation, or reputational harm. The sale of these items involves the risk of illness or injury to our members. Such illnesses or injuries could result from tampering by unauthorized third parties, product\n\n12\n\n\n[Table of
Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)",
     "score": 0.5393
    },
    {
     "source": "sec://0000909832-26-000093/unknown#20",
     "title": "COST FY2026 10-K",
     "content": "12\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\ncontamination or spoilage, including the presence of foreign objects, substances, chemicals, other agents, or residues introduced during the growing, manufacturing, storage, handling, and transportation phases,
or faulty design. Our suppliers are generally contractually required to comply with product safety laws, and we are dependent on them to ensure that the products we buy comply with safety and other standards. While we are subject to governmental inspection and regulations and work to comply in all
material respects with applicable laws and regulations, we cannot be sure that consumption or use of our products will not cause illness or injury or that we will not be subject to claims, lawsuits, or government investigations relating to such matters, resulting in costly product recalls and other
liabilities that could adversely affect our business and results of operations. Even if a product liability claim is unsuccessful or is not fully pursued, negative publicity could adversely affect our reputation with existing and potential members and our corporate and brand image, and these effects
could be long-term.\n\nIf we do not successfully develop and maintain a relevant and comprehensive digital experience for our members, our results of operations could be adversely impacted.\n\nWe must keep pace with changing member expectations and new developments by our competitors. Our members
are increasingly using mobile phones, tablets, computers, and other devices to shop and otherwise interact with us. We are making investments in our websites and mobile applications. If we are unable to make, improve, or develop relevant member-facing technology in a timely manner, our ability to
compete and our results of operations could be adversely affected.\n\nInability to attract, train and retain qualified employees could adversely impact our business, financial condition and results of operations.",
     "score": 0.5248
    },
    {
     "source": "sec://0000909832-26-000093/unknown#21",
     "title": "COST FY2026 10-K",
     "content": "Inability to attract, train and retain qualified employees could adversely impact our business, financial condition and results of operations.\n\nOur success depends on the continued contributions of our employees, including members of our senior management and other key operations,
IT, merchandising, and administrative personnel. Failure to identify and implement a succession plan for senior management could negatively impact our business. We must attract, train, and retain a large and growing number of qualified employees, while controlling related labor costs, preserving our
culture, and maintaining our core values. Our ability to control labor and benefit costs is subject to numerous internal and external factors, including regulatory changes, prevailing wage rates, union relations, and healthcare and other insurance costs. We compete with other retail and non-retail
businesses for these employees and invest significant resources in training and motivating them. There is no assurance that we will be able to attract or retain highly qualified employees in the future, which could have a material adverse effect on our business, financial condition and results of
operations.\n\nWe may incur property, casualty or other losses not covered by our insurance.\n\nClaims for employee health care benefits, workers’ compensation, general liability, property damage, directors’ and officers’ liability, vehicle liability, inventory loss, and other exposures are funded
predominantly through self-insurance. Insurance coverage is maintained for certain risks to limit exposures arising from very large losses. The types and amounts of insurance may vary from time to time based on our decisions with respect to risk retention and regulatory requirements. Significant
claims or events, regulatory changes, a substantial rise in costs of health care or costs to maintain our insurance or the failure to maintain adequate insurance coverage could have an adverse impact on our financial condition and results of operations.\n\nAlthough we maintain specific coverages for
catastrophic property losses, we still bear a significant portion of the risk of losses incurred as a result of any physical damage to, or the destruction of, any warehouses, depots, manufacturing or home office facilities, loss or spoilage of inventory, and business interruption. Such losses could
materially impact our cash flows and results of operations.\n\n13\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nMarket and Other External Risks\n\nWe face strong competition from other retailers and warehouse club operators, which could adversely affect our business, financial
condition and results of operations.",
     "score": 0.5415
    },
    {
     "source": "sec://0000909832-26-000093/unknown#22",
     "title": "COST FY2026 10-K",
     "content": "Market and Other External Risks\n\nWe face strong competition from other retailers and warehouse club operators, which could adversely affect our business, financial condition and results of operations.\n\nThe retail business is highly competitive. We compete for members, employees,
sites, products and services, and in other important respects with a wide range of local, regional and national wholesalers and retailers, both in the United States and in foreign countries, including other warehouse-club operators, supermarkets, supercenters, online retailers, gasoline stations,
pharmacies, hard discounters, department and specialty stores and operators selling a single category or narrow range of merchandise or services. Such retailers and warehouse club operators compete vigorously and in a variety of ways, including pricing, selection and availability, services,
location, convenience, store hours, and the attractiveness, and ease of use of websites and mobile applications. The evolution of retailing in online and mobile channels has improved the ability of customers to comparison shop, which has enhanced competition. Additionally, the emergence of AI tools
may change consumer shopping habits and increase the competition we face. AI may also present inaccurate pricing or product data, or fail to capture the full value of our membership offering, impacting member purchasing decisions by prioritizing immediate or inaccurate price comparison or logistics
over member loyalty. Some competitors have greater technology capabilities, including the faster adoption of AI technologies, and greater market penetration than we do. Our inability to respond effectively to competitive pressures, changes in the retail markets or customer expectations could result
in lost market share and negatively affect our financial results.\n\nGeneral economic factors, domestically and internationally, may adversely affect our business, financial condition, and results of operations.",
     "score": 0.594
    },
    {
     "source": "sec://0000909832-26-000093/unknown#23",
     "title": "COST FY2026 10-K",
     "content": "General economic factors, domestically and internationally, may adversely affect our business, financial condition, and results of operations.\n\nHigher energy and gasoline costs, inflation, levels of unemployment, healthcare costs, consumer debt levels, foreign-currency exchange
rates, unsettled financial markets, weaknesses in housing and real estate markets, reduced consumer confidence, changes and uncertainties related to government fiscal, monetary, and tax policies including changes in interest rates, tax rates, duties, tariffs, or other restrictions, sovereign debt
crises, pandemics and other health crises, and other economic factors could adversely affect demand for our products and services, require a change in product mix, or impact the cost of or ability to purchase inventory. Additionally, trade-related actions in various countries have adversely affected
the costs of some of our merchandise. The degree of our exposure is dependent on (among other things) the type of goods, rates imposed, and timing of the tariffs and policy changes. The impact to our net sales and gross margin is influenced in part by our merchandising and pricing strategies in
response to potential cost increases. Higher tariffs could adversely impact our results.\n\nPrices of certain commodities, including gasoline and consumable goods used in manufacturing and our warehouse retail operations, are historically volatile and are subject to fluctuations arising from changes
in domestic and international supply and demand, inflationary pressures, labor costs, competition, market speculation, government regulations, taxes, and periodic delays in delivery. Rapid and significant changes in commodity prices and our ability and desire to pass them through to our members may
affect our sales and profit margins. These factors could also increase our merchandise costs and selling, general and administrative expenses, and otherwise adversely affect our operations and financial results. General economic conditions can also be affected by events like the outbreak of
hostilities or acts of terrorism.\n\nInflationary factors, such as increases in merchandise costs, may adversely affect our business, financial condition and results of operations. We may not be able to adjust prices to sufficiently offset the effect of cost increases without negatively impacting
consumer demand.\n\n14\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nSuppliers may be unable to timely provide us with quality merchandise at competitive prices or may fail to adhere to our high standards, resulting in adverse effects on our business, merchandise inventories,
sales, and profits.",
     "score": 0.5764
    },
    {
     "source": "sec://0000909832-26-000093/unknown#24",
     "title": "COST FY2026 10-K",
     "content": "Suppliers may be unable to timely provide us with quality merchandise at competitive prices or may fail to adhere to our high standards, resulting in adverse effects on our business, merchandise inventories, sales, and profits.\n\nWe depend heavily on our ability to purchase quality
merchandise in sufficient quantities at competitive prices. As the quantities we require continue to grow, we have no assurances of continued supply, appropriate pricing or access to new products, and any supplier has the ability to change the terms upon which they sell to us or discontinue selling
to us. Member demands may lead to out-of-stock positions causing a loss of sales and profits.\n\nWe buy from numerous domestic and foreign suppliers and importers. Our inability to acquire suitable merchandise on acceptable terms or the loss of key suppliers could negatively affect us. We may not be
able to develop relationships with new suppliers, and products from alternative sources, if any, may be of a lesser quality or more expensive. Because of our efforts to adhere to high-quality standards for which available supply may be limited, particularly for certain food items, the large volumes
we demand may not be consistently available. Our efforts to secure supply could lead to commitments that prove to be unsuccessful in the short and long-term.\n\nOur suppliers (and those they depend upon for materials and services) are subject to risks, including labor disputes, union organizing
activities, human rights violations, animal welfare violations, financial liquidity, climate change, natural disasters, extreme weather conditions, environmental degradation, public health emergencies, supply constraints, and general economic and political conditions and other risks similar to those
we face that could limit their ability to timely provide us with acceptable merchandise. One or more of our suppliers might not adhere to our quality control, packaging, legal, regulatory, labor, human rights, environmental, or animal welfare standards. These deficiencies may delay or preclude
delivery of merchandise to us and might not be identified before we sell such merchandise to our members. This failure could lead to recalls and litigation and otherwise damage our reputation and our brands, increase costs, and otherwise adversely impact our business.\n\nFluctuations in foreign-
exchange rates may adversely affect our results of operations.",
     "score": 0.5695
    },
    {
     "source": "sec://0000909832-26-000093/unknown#26",
     "title": "COST FY2026 10-K",
     "content": "15\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\ndisruption in the supply of products from some local or overseas suppliers, the temporary disruption in the transport of goods to or from overseas, delays in the delivery of goods to our warehouses or depots,
delays in online merchandise delivery, the temporary reduction in the availability of products in our warehouses, and long-term disruption or threats to the habitability of key markets in which we operate. These events could also reduce demand for our products or make it difficult or impossible to
procure products. We may be required to suspend operations in some or all of our locations, which could have a material adverse effect on our business, financial condition and results of operations.\n\nPandemics and other health crises could affect our business, financial condition and results of
operations in many respects.\n\nThe emergence, severity, magnitude, and duration of global or regional health crises are uncertain and difficult to predict. A pandemic could affect certain business operations, demand for our products and services, in-stock positions, costs of doing business,
availability of labor, access to inventory, supply chain operations, our ability to predict future performance, exposure to litigation, and our financial performance, among other things. Other factors and uncertainties include, but are not limited to: the severity and duration of pandemics; evolving
macroeconomic factors including general economic uncertainty, unemployment rates, and recessionary pressures; changes in labor markets affecting us and our suppliers; unknown consequences on our business performance and initiatives stemming from the substantial investment of time and other resources
to the pandemic response; the pace of post-pandemic recovery; the long-term impact of the pandemic on our business, including consumer behaviors; and disruption and volatility within the financial and credit markets.\n\nFailure to meet financial market expectations could adversely affect the market
price and volatility of our stock.\n\nWe believe that the price of our stock currently reflects high market expectations for our future operating results. Any failure to meet or delay in meeting these expectations, including our comparable sales growth rates, membership fee revenue, including new
member sign-ups and renewal rates, gross margin, earnings, earnings per share, new warehouse openings, or dividend or stock repurchase policies could cause the price of our stock to decline.\n\nLegal and Regulatory Risks\n\nChanges in or failure to comply with laws and regulations could adversely
impact our business, financial condition and results of operations.",
     "score": 0.5843
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
     "score": 0.5834
    }
   ]
  }
 ]
}

[tool 2] sec_filing_search {"query": "key business risks clinical trials regulatory approval competition pricing manufacturing supply demand obesity medicines", "ticker": "LLY", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "LLY",
   "fiscal_year": 2025,
   "item": "Item 1",
   "prelude": "Excerpts from LLY FY2025 10-K, Item 1 (Business) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000059478-26-000013/1#7",
     "title": "LLY FY2025 10-K · Item 1 · Competition",
     "content": "### Competition\n\nOur products compete globally with many other pharmaceutical products in highly competitive markets.\n\nImportant competitive factors include effectiveness, safety, availability, ease of use, patient preference, and overall experience; formulary placement, price,
payer coverage and reimbursement rates, and demonstrated cost-effectiveness; regulatory approvals; marketing effectiveness; and research and development of new products, processes, modalities, indications, and uses. Early market entry and rapid patient access can also be important to achieve product
acceptance and success. Barriers to reimbursable patient access in some cases include default payer coverage restrictions for our medicines. For example, in the U.S. self-insured employers must generally opt in for coverage of anti-obesity medicines. Payers in various international markets also do
not cover anti-obesity medicines for weight loss. Our anti-obesity medicines comprise a significant portion of our revenues, and barriers to reimbursable patient access impact our sales volumes, business, and results of operations.\n\nMost new products or uses that we introduce must compete with
other branded, biosimilar, or generic products already on the market or that are later developed. When new products, uses, or delivery systems with therapeutic, convenience, or cost advantages are introduced, including by developing new modalities, our existing products become subject to decreased
sales volumes, progressive price reductions, or both.\n\nWe believe our long-term competitive success depends on discovering and developing or acquiring and further developing innovative, cost-effective products that provide improved outcomes for patients and deliver value to payers, and
continuously improving the productivity of our operations in a highly competitive and global environment. We face intensifying competition worldwide, including from China and other markets that have significantly expanded and accelerated research and development capabilities. Companies in these
markets are increasingly licensing products to multinational pharmaceutical companies, entering into strategic partnerships, and competing directly in major markets. Our ability to compete effectively depends on our capacity to innovate at the pace of global scientific advancement, to access
innovation through strategic partnerships and licensing arrangements across geographies, and to efficiently bring differentiated products to market. There can be no assurance that our efforts will result in commercially successful products, and it is possible that our products or indications will
be, or will become, uncompetitive from time to time. See also \"—Competition—U.S. Private Sector Dynamics.\"\n\n8",
     "score": 0.619,
     "subsection": "Competition"
    }
   ]
  },
  {
   "ticker": "LLY",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from LLY FY2025 10-K, Item 1A (Risk Factors) — 7 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000059478-26-000013/1a#54",
     "title": "LLY FY2025 10-K · Item 1A · Risks Related to Our Business and Industry",
     "content": "### Risks Related to Our Business and Industry\n\nPharmaceutical research and development is very costly and highly uncertain; we may not succeed in developing, licensing, or acquiring commercially successful products sufficient in number or value to replace revenues of products
that have lost or will lose intellectual property protection or are displaced by competing products or therapies.\n\nThere are many difficulties and uncertainties inherent in pharmaceutical research and development, the introduction of new products and indications, business development activities to
enhance or refine our product pipeline, and commercialization of our products.\n\nThere is a high rate of failure inherent in drug discovery and development. To bring a product from the discovery phase to market takes considerable time and entails significant cost. Failure or results that misalign
with expectations can occur at any point in the process, including in later stages after substantial investment, following meaningful cost for manufacturing capabilities and inventory to prepare for launch, and after we and others may have attributed significant value for these potential products.
As a result, a significant portion of funds invested in research and development programs will not generate direct financial returns. New product candidates that appear promising in development or prior to being acquired may fail to reach the market or may have only limited commercial success
because of efficacy or safety concerns, inability to obtain or maintain necessary regulatory approvals or payer reimbursement or coverage, failure to obtain placement on guidelines or recommendations published by third-party organizations, the application of pricing controls, limited scope of
approved uses, label changes, changes in the relevant treatment standards or the availability of newer, better, or more cost-effective competitive products, difficulty or excessive costs to manufacture, insufficient infrastructure to support detection, diagnostic or other requisites for treatment,
ineffectiveness in connecting with healthcare professionals, including digitally through virtual engagements, or infringement of the patents or intellectual property rights of others. We may also fail to allocate research and development resources efficiently, fail to pursue or invest sufficiently
in product candidates or indications that may have been successful, or fail to optimally balance trial design, conduct, and speed to accomplish desired outcomes.",
     "score": 0.5973,
     "subsection": "Risks Related to Our Business and Industry"
    },
    {
     "source": "sec://0000059478-26-000013/1a#55",
     "title": "LLY FY2025 10-K · Item 1A",
     "content": "We regularly submit new product candidates and indications to regulatory agencies for approval, including highly anticipated candidates such as orforglipron. Regulatory agencies establish high hurdles for the efficacy and safety of new products and indications. Delay, uncertainty,
unpredictability, and inconsistency in drug approval processes across markets and agencies can result in delays in product launches, lost market opportunities, impairment of inventories, and other negative impacts. In addition, it can be very difficult to predict revenue growth rates of, or
variability in demand for, new or future products and indications, which in some cases leads to difficulty meeting product demand or, on the other hand, lower volume growth, excess inventory, and related financial charges.\n\nWe cannot state with certainty when or whether our products and
indications now under development will be approved or launched; whether, if initially granted, such approval will be maintained; whether we will be able to develop, license, or otherwise acquire additional product candidates, indications, or products; or whether our products and indications, once
launched, will be commercially successful.\n\nThrough internal innovation and business development we must maintain a flow of successful products and indications or line extensions sufficient both to cover our substantial research and development costs and investments and to replace revenues that
are lost as profitable products become subject to pricing controls, lose intellectual property exclusivity, are displaced by competing products, or therapies, or experience a reduction in patient access. Failure to replenish our product portfolio and pipeline in a timely manner would have a material
adverse effect on our business, results of operations, cash flows, and financial position. Our dependence on, or focus in, one or more key products or product classes exacerbates this risk. In addition, the growth of our business and revenue base increases the risk that products developed or
acquired by us may not provide adequate value to sustain further long-term growth.\n\n25",
     "score": 0.6103
    },
    {
     "source": "sec://0000059478-26-000013/1a#59",
     "title": "LLY FY2025 10-K · Item 1A",
     "content": "Our business is subject to government price controls and other public and private restrictions on pricing, reimbursement, and access for our drugs, which could have a material adverse effect on our results of operations, reputation, or business.\n\nPublic and private actors continue
to take aggressive steps to control expenditures for pharmaceuticals by placing restrictions on pricing and reimbursement for, and patient access to, our medicines. These pressures have negatively affected and we expect will continue to negatively affect our consolidated results of operations.
Governments and private actors worldwide are demanding greater commercial and clinical value from pharmaceutical companies in the form of strong product differentiation and demonstrated value. We continue to experience scrutiny on the pricing of current and potential products due to, among other
factors, payer concern over projected growth in demand and, for certain of these drugs, the anticipated duration of treatment. We have also observed scrutiny of pricing and access disparities across jurisdictions.\n\nIn November 2025, we announced preliminary voluntary agreements with the U.S.
government in which, among other arrangements, we agreed to implement measures to lower Medicaid and certain other drug prices for U.S. patients and to launch new medicines with a more balanced pricing approach across developed nations. We face risks and uncertainty associated with these
arrangements and negotiating the definitive agreements, including potential delays and the possibility of unfavorable terms related to pricing, access, and other key objectives. Among other risks, we may fail to adequately capitalize on the additional U.S. access to our obesity medicines resulting
from these agreements, particularly if the revenues generated from such expanded access are insufficient to offset pricing concessions. Moreover, the outcome of these arrangements and broader U.S. policy efforts to align domestic pharmaceutical pricing with international benchmarks from countries
with competing healthcare cost containment priorities is uncertain and could negatively impact our pricing strategies, product demand or access, or competitive positioning across global markets, and may result in reduced revenue in certain markets.",
     "score": 0.5997
    },
    {
     "source": "sec://0000059478-26-000013/1a#60",
     "title": "LLY FY2025 10-K · Item 1A",
     "content": "In general, securing and growing access for our obesity medicines is an important factor in the success of our business. Among other considerations, payers in various international markets do not currently provide coverage for obesity medicines for weight loss indications, requiring
patient self-pay. In addition, patient self-pay sales through LillyDirect represented a growing portion of our business in 2025, and we have launched, and continue to explore, new partnerships and tools, including through LillyDirect, to further expand access to our medicines. Our financial results
and prospects are subject to risks related to the level and pace of patient participation in cash-pay markets, which may be influenced by pricing, economic conditions, and competitive offerings, as well as regulatory or other actions that could restrict our ability to benefit from such markets, and
uncertainty regarding our ability to secure reimbursement coverage in such markets over time.\n\n27",
     "score": 0.5975
    },
    {
     "source": "sec://0000059478-26-000013/1a#63",
     "title": "LLY FY2025 10-K · Item 1A",
     "content": "Pharmaceutical products can develop safety or efficacy concerns, which could have a material adverse effect on our revenues, income, and reputation.\n\nPharmaceutical products receive regulatory approval based on data obtained in controlled clinical trials of fixed duration and
defined populations. After approval and launch, the products are used for longer periods of time by much larger numbers of patients, which may lead to identifying new or expanded safety or efficacy concerns. We and others (including regulatory agencies and private payers) collect extensive
information on the efficacy and safety of our marketed products by continuously monitoring the use of our products in the marketplace. In addition, we or others (including our competitors, in some cases) may conduct post-marketing clinical studies on efficacy and safety of our marketed products. New
safety or efficacy data may result in product label changes, or other measures that could reduce the product's market acceptance and result in declining sales. Relatedly, safety or efficacy concerns raised about a product in the same class, compounded or counterfeit versions of our products, or
products with the same mechanism of action as one of our products or product candidates could be imputed and have an adverse impact on the availability or commercial viability of our products or approval of product candidates. Serious safety or efficacy issues that arise after product approval have
resulted and could in the future result in voluntary or mandatory product recalls or withdrawals from the market. Safety issues have resulted and could in the future result in costly product liability claims. Any of these outcomes could result in material financial, legal, commercial, or
reputational harm to our business.\n\n28\n\n\n\nWe derive a significant percentage of our total revenue from relatively few products and sell our products through consolidated supply chain entities, which subjects us to various risks.",
     "score": 0.572
    },
    {
     "source": "sec://0000059478-26-000013/1a#64",
     "title": "LLY FY2025 10-K · Item 1A",
     "content": "28\n\n\n\nWe derive a significant percentage of our total revenue from relatively few products and sell our products through consolidated supply chain entities, which subjects us to various risks.\n\nWe derived direct product and/or collaboration and other revenues of more than $3
billion for each of Mounjaro, Zepbound, Verzenio, Trulicity, Taltz, and Jardiance (including Glyxambi, Synjardy, and Trijardy XR) that collectively accounted for 82 percent of our total revenues in 2025. In particular, Mounjaro and Zepbound accounted for 56 percent of our total revenues in 2025, and
we expect cardiometabolic health products will continue to represent a significant and growing portion of our business, revenues, and prospects. Factors such as loss of patent protection, changes in prescription rates, material product liability or pricing claims or litigation, unexpected side
effects or safety concerns, significant changes or fluctuations in demand, channel dynamics, regulatory proceedings and investigations, negative publicity affecting doctor or patient confidence, pressure from existing or new competitive products, pipeline developments by us or our competitors,
counterfeit and illegally compounded drugs, changes in labeling, pricing, and insufficient access, or reimbursement, or actual or perceived supply shortages, imbalances, or disruptions for these products or any of our other major products could materially impact our results of operations or result
in significant and sudden declines or volatility in the trading price of our common stock and market capitalization.\n\nIn addition, in the U.S., most of our products are distributed through a limited number of wholesalers. If one of these significant wholesalers encounters financial or other
difficulties or otherwise is unable or unwilling to support distribution of our products, it could cause disruption to our supply chain or we might be unable to timely collect the amounts that the wholesaler owes us, which could negatively impact our results of operations. See Item 1,
\"Business—Marketing and Distribution,\" for more details. Challenges to U.S. retail pharmacies due to pharmacy benefit manager reimbursement pressures, among other things, have resulted and may result in financial difficulties for some pharmacies that impact patient experiences, lead to
determinations by certain pharmacies to not carry one or more of our significant products or threaten the viability of these pharmacies, which could negatively impact our business and results of operations.",
     "score": 0.568
    },
    {
     "source": "sec://0000059478-26-000013/1a#66",
     "title": "LLY FY2025 10-K · Item 1A · Risks Related to Our Intellectual Property",
     "content": "### Risks Related to Our Intellectual Property\n\nWe depend on products with intellectual property protection for most of our revenues, cash flows, and earnings; the loss of effective intellectual property protection for certain of our products has resulted, and in the future is
likely to continue to result, in rapid and severe declines in revenues for those products.\n\nIn the ordinary course of their lifecycles, our products lose significant patent protection and/or data protection after a specified period of time. For example, Trulicity will lose significant patent and
remaining data protections in the next few years. Some products also lose patent protection as a result of successful third-party challenges. We have faced, and remain exposed to, generic or biosimilar competition following the expiration or loss of such intellectual property protection. Patent
expirations of competitive products may also shift market conditions for our products by contracting the market for branded products, impacting product access, or otherwise intensifying pricing pressures across similar treatments.\n\n29\n\n\n\nFor non-biologic products, loss of exclusivity typically
results in the entry of one or more generic competitors, leading to a rapid and severe decline in revenues, especially in the U.S. Generic pharmaceutical companies have in some cases introduced a generic product before resolution of any related patent litigation. For biologics, loss of exclusivity
may also result in the near-term entry of competitor versions (i.e., biosimilars).",
     "score": 0.567,
     "subsection": "Risks Related to Our Intellectual Property"
    }
   ]
  },
  {
   "ticker": "LLY",
   "fiscal_year": 2025,
   "item": "Item 7",
   "prelude": "Excerpts from LLY FY2025 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 2 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000059478-26-000013/7#114",
     "title": "LLY FY2025 10-K · Item 7 · Other Matters",
     "content": "### Other Matters\n\nTrends Affecting Pharmaceutical Pricing, Reimbursement, and Access and Certain Other Regulatory Developments\n\nGlobal concern over access to, and affordability of, pharmaceutical products continues to drive debate and action, as well as cost containment efforts
by governmental authorities and scrutiny of pricing and access disparities. Cost containment measures include the use of mandated discounts, price reporting requirements, mandated reference prices, restrictive formularies, changes to available intellectual property protections, as well as other
efforts.\n\nReforms, initiatives, and other actions, including those that may stem from political initiatives, periods of uneven economic growth or downturns, or as a result of inflation or deflation, trade and other global disputes and interruptions including related to tariffs, trade protection
measures, and similar restrictions, the emergence or escalation of, and responses to, international tension and conflicts, or government budgeting priorities, are expected to continue to result in added pressure on cost, pricing, reimbursement, and access for our products.\n\nIn November 2025, we
announced preliminary voluntary agreements with the U.S. government in which, among other arrangements, we agreed to lower Medicaid and certain other drug prices for U.S. patients and to launch new medicines with a more balanced pricing approach across developed nations. We face risks and
uncertainty associated with these arrangements and negotiating the definitive agreements, including potential delays and the possibility of unfavorable terms related to pricing, access, and other key objectives. Among other risks, we may fail to adequately capitalize on the additional U.S. access to
our obesity medicines resulting from these agreements, particularly if the revenues generated from such expanded access are insufficient to offset pricing concessions. Moreover, the outcome of these arrangements and broader U.S. policy efforts to align domestic pharmaceutical pricing with
international benchmarks from countries with competing healthcare cost containment priorities is uncertain and could negatively impact our pricing strategies, product demand or access, or competitive positioning across global markets, and may result in reduced revenue in certain markets.\n\nOther
policies, regulations, legislation, or enforcement, including those proposed or pursued by lawmakers, regulators, and other authorities in the U.S. and worldwide, have and may continue to adversely impact our business and consolidated results of operations.",
     "score": 0.5835,
     "subsection": "Other Matters"
    },
    {
     "source": "sec://0000059478-26-000013/7#116",
     "title": "LLY FY2025 10-K · Item 7",
     "content": "Private payers and pharmacy benefit managers in the U.S. continue to significantly impact the market for pharmaceuticals through negotiation of access, manufacturer price or rebate concessions and pharmacy reimbursement rates. Restrictive or unfavorable pricing, coverage, or
reimbursement determinations for our medicines or product candidates by governments, regulatory agencies, courts, or private actors have and may continue to adversely impact our business and consolidated results of operations. In addition, we are engaged in litigation and investigations related to
the 340B program, access to insulin, pricing, product safety, and other matters that, if resolved adversely to us, could negatively impact our business and consolidated results of operations. It is not currently possible to predict the overall potential adverse impact to us or the general
pharmaceutical industry of continued cost containment efforts worldwide.\n\nIn addition, regulatory issues concerning compliance with current Good Manufacturing Practices, quality assurance, safety signals, evolving standards, and increased scrutiny around excipients and potential impurities such as
nitrosamines, and similar regulations and standards (and comparable foreign regulations and standards) for our products in some cases lead to regulatory and legal actions, product recalls and seizures, fines and penalties, interruption of production leading to product shortages, import bans or
denials of import certifications, inability to realize the benefit of capital expenditures, or delays or denials in new product approvals, line extensions or supplemental approvals of current products pending resolution of the issues, or other negative impacts, any of which result in reputational
harm or adversely affect our business.\n\nIncretin Medicines\n\nMounjaro and Zepbound accounted for 56 percent of our total revenues in 2025 and we expect cardiometabolic health products will continue to represent a significant and growing portion of our business, revenues, and prospects. In 2025,
we reached preliminary drug pricing agreements with the U.S. government. As part of these agreements, Medicare beneficiaries will have access to discounted Lilly obesity medicines by July 1, 2026 and individual state Medicaid programs will have the option to expand access to these medicines. Also in
2025, we received a U.S. Commissioner’s National Priority Voucher for our product candidate orforglipron for the treatment of obesity, and we submitted to the FDA under that expedited review pathway. Internationally, we launched Mounjaro in all major markets. To support anticipated demand for our
current and prospective products, we have undertaken significant manufacturing expansion initiatives. Additional capacity is expected to become operational over the next several years.",
     "score": 0.6007
    }
   ]
  }
 ]
}

[tool 3] finnhub_company_basic_financials {"ticker": "LLY"}
{
 "ticker": "LLY",
 "fiftyTwoWeekHigh": 1321.21,
 "fiftyTwoWeekLow": 806.02,
 "peTTM": 45.2679,
 "forwardPE": 26.24741,
 "psTTM": 15.1779,
 "pb": 33.3408,
 "marketCap": 1209159,
 "enterpriseValue": 1255117,
 "beta": 0.41343352,
 "epsTTM": 29.7962,
 "roeTTM": 92.58,
 "roaTTM": 21.97,
 "grossMarginTTM": 83.4,
 "netProfitMarginTTM": 33.53,
 "operatingMarginTTM": 42.22,
 "currentRatio": 1.3546,
 "quickRatio": 0.681,
 "debtToEquity": 1.6207,
 "dividendYield": 0.75195,
 "revenueGrowthTTMYoy": 49.58,
 "epsGrowthTTMYoy": 94.62,
 "tenDayAvgVolume": 2.41775
}

[tool 4] finnhub_company_basic_financials {"ticker": "NVDA"}
{
 "ticker": "NVDA",
 "fiftyTwoWeekHigh": 243.37,
 "fiftyTwoWeekLow": 164.27,
 "peTTM": 26.8559,
 "forwardPE": 17.02191,
 "psTTM": 17.0972,
 "pb": 20.768,
 "marketCap": 5179933.5,
 "enterpriseValue": 5190856.5,
 "beta": 2.269422,
 "epsTTM": 7.9108,
 "roeTTM": 110.11,
 "roaTTM": 81.41000000000001,
 "grossMarginTTM": 74.67,
 "netProfitMarginTTM": 63.66,
 "operatingMarginTTM": 65.17,
 "currentRatio": 4.5889,
 "quickRatio": 3.7757,
 "debtToEquity": 0.1457,
 "dividendYield": 0.03349,
 "revenueGrowthTTMYoy": 83.38,
 "epsGrowthTTMYoy": 125.15,
 "tenDayAvgVolume": 99.27746
}

[tool 5] finnhub_company_basic_financials {"ticker": "COST"}
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

[tool 6] tavily_financial_search {"query": "LLY recent news earnings expectations guidance obesity drugs valuation", "ticker": "LLY"}
{
 "query": "LLY LLY recent news earnings expectations guidance obesity drugs valuation",
 "results": [
  {
   "title": "Eli Lilly (LLY) earnings Q2 2026",
   "url": "https://www.cnbc.com/2026/08/05/eli-lilly-lly-earnings-q2-2026.html",
   "content": "In this article\n\nEli Lilly on Wednesday reported second-quarter earnings and revenue that blew past estimates and hiked its full-year sales outlook, as demand for its blockbuster weight loss drug Zepbound and diabetes treatment Mounjaro surged again.\n\nThe pharmaceutical giant now
expects 2026 revenue to come in between $85 billion and $87 billion, up from previous guidance of $82 billion to $85 billion. [...] Lilly's newly launched obesity pill, Foundayo, which won U.S. approval in April, took in $98 million in sales for the second quarter. Analyst estimates compiled by
FactSet as of Wednesday forecasted nearly $103 million in sales.\n\n\"We're really pleased with the start; it's accelerating as we speak,\" Ricks said, adding that the company had to build physician and consumer awareness as well as access on formularies. [...] Ricks said in an interview in late
April that he expects lower prices to accelerate prescription volumes in the U.S. He estimated that global GLP-1 use will rise from approximately 20 million patients at the end of last year to 30 million at the end of 2026.\n\nBoth Lilly and Novo are expected to benefit from Medicare's new coverage
of obesity drugs, which launched in early July, in the back half of the year. That allows eligible seniors to access branded GLP-1s for a monthly copay of $50.",
   "published_date": null
  },
  {
   "title": "Eli Lilly (LLY) earnings Q1 2026",
   "url": "https://www.cnbc.com/2026/04/30/eli-lilly-lly-earnings-q1-2026.html",
   "content": "In this article\n\nEli Lilly on Thursday reported first-quarter earnings and revenue that blew past estimates and hiked its full-year sales outlook by $2 billion, as demand for its blockbuster weight loss drug Zepbound and diabetes treatment Mounjaro spiked again.\n\nThe
pharmaceutical giant now expects 2026 revenue to come in between $82 billion and $85 billion, up from previous guidance of $80 billion to $83 billion. [...] \"So what we're seeing now is basically organic demand, which is really strong to us,\" Ricks said.\n\nIn February, Lilly said it expects to
benefit from Foundayo's launch, Medicare coverage of obesity drugs coming online later this year, and continued worldwide demand for Mounjaro and Zepbound. But the company also expects to face pricing pressure, driven by a drug pricing deal with President Donald Trump and lower cash-pay prices for
Zepbound, among other factors. [...] Lilly is working to maintain its dominance in the booming market for GLP-1 drugs, with the company holding 60.1% share of the U.S. obesity and diabetes drug market in the first quarter, according to an earnings presentation. Novo Nordisk's market share in the
quarter was 39.4%.\n\nHere's what Eli Lilly reported for the first quarter compared with what Wall Street was expecting, based on a survey of analysts by LSEG:\n\nShares of Lilly rose more than 10% in afternoon trading Thursday.",
   "published_date": null
  },
  {
   "title": "Eli Lilly (LLY) earnings Q4 2025",
   "url": "https://www.cnbc.com/2026/02/04/eli-lilly-lly-earnings-q4-2025.html",
   "content": "Eli Lilly on Wednesday posted fourth-quarter earnings and revenue and 2026 guidance that blew past estimates, as demand for its blockbuster weight loss drug Zepbound and diabetes treatment Mounjaro soars.\n\nThe pharmaceutical giant anticipates its 2026 revenue will come in between
$80 billion and $83 billion. Analysts expected revenue of $77.62 billion, according to LSEG. [...] Meanwhile, the midpoint of Lilly's revenue guidance sees sales growing by 25% this year.\n\nThe strong outlook comes days after Lilly CEO Dave Ricks told CNBC in an exclusive interview that he expects
upcoming government Medicare coverage of obesity treatments to expand the U.S. market for those drugs this year, saying it's a \"big multiplier on the eligible pool\" of patients. [...] The guidance comes in stark contrast to the outlook of rival Novo Nordisk, which is also grappling with lower
prices in the U.S. following landmark deals both companies struck with President Donald Trump to slash obesity and diabetes drug costs. Unlike Lilly, Novo warned on Tuesday that it sees sales and profit declining as much as 13% this year, as prices fall in the U.S. and exclusivity expires for its
blockbuster obesity and diabetes drugs in China, Brazil and Canada.",
   "published_date": null
  },
  {
   "title": "Lilly becomes first drugmaker to hit $1 trillion valuation on weight-loss demand | Reuters",
   "url": "https://www.reuters.com/business/healthcare-pharmaceuticals/lilly-becomes-first-drugmaker-join-trillion-dollar-club-weight-loss-demand-boom-2025-11-21",
   "content": "The company's shares, which briefly hit a record high, were trading nearly 1% higher at $1,051.\n\nLilly now trades at one of the richest valuations in big pharma, at about 50 times its anticipated earnings over the next 12 months, according to LSEG data, reflecting investors' bets
that demand for obesity drugs will remain strong. [...] \"The current valuation points to investor confidence in the longer-term durability of the company's metabolic health franchise. It also suggests that investors prefer Lilly over Novo in the obesity arms race,\" said Evan Seigerman, analyst at
BMO Capital Markets.\n\nIn October, Lilly lifted its annual revenue forecast by more than $2 billion at the midpoint on surging global demand for its obesity and diabetes drugs. [...] Wall Street estimates the weight-loss drug market to be worth $150 billion by 2030, with Lilly and Novo together
controlling the majority of projected global sales.\n\nInvestors are now focused on Lilly's oral obesity drug, orforglipron, which is expected to be approved early next year.\n\nIn a note last week, Citi analysts said the latest generation of GLP-1 drugs have already been a \"sales phenomenon\", and
orforglipron is poised to benefit from the \"inroads made by its injectable predecessors.\"",
   "published_date": null
  },
  {
   "title": "Lilly reassures investors that weight-loss drug demand is strong, shares rise | Reuters",
   "url": "https://www.reuters.com/business/healthcare-pharmaceuticals/eli-lilly-forecasts-2025-profit-largely-above-estimates-launch-weight-loss-drug-2025-02-06",
   "content": "Novo on Wednesday forecast slower growth this year compared to 2024, and said it saw \"intact strong demand for obesity treatments\" in the United States and elsewhere.\n\nLilly last month forecast total sales to be between $58 billion and $61 billion in 2025, banking on the launch of
Mounjaro in new markets, including China, India, Brazil and Mexico, for both diabetes and obesity. Analysts on average estimate revenues of $59.21 billion for 2025, according to LSEG data. [...] Eli Lilly also forecast annual profit largely above Wall Street estimates on Thursday, saying it expects
to earn between $22.50 and $24.00 per share on an adjusted basis this year. Analysts were expecting a profit of $22.86 per share, according to data compiled by LSEG. [...] The Indianapolis-based drugmaker reported sales for its Zepbound and Mounjaro of $1.91 billion and $3.53 billion respectively,
in line with its forecast from last month that fell below analysts' expectations for the second straight quarter and raised questions about demand.\n\nAnalysts as of Thursday were expecting $2.03 billion for Zepbound and $4.27 billion for Mounjaro, according to LSEG data. Lilly has previously
attributed the miss to issues in the supply chain.",
   "published_date": null
  }
 ]
}

[tool 7] tavily_financial_search {"query": "COST recent news earnings expectations guidance valuation membership consumer spending", "ticker": "COST"}
{
 "query": "COST COST recent news earnings expectations guidance valuation membership consumer spending",
 "results": [
  {
   "title": "Costco’s Earnings Beat Estimates on Steady Consumer Demand - Bloomberg",
   "url": "https://www.bloomberg.com/news/articles/2025-09-25/costco-s-earnings-beat-estimates-on-steady-consumer-demand",
   "content": "The retailer said it generated earnings per share of $5.87 for the quarter through the end of August, higher than what Wall Street analysts were expecting. Its comparable sales, excluding gas and currency fluctuations, also beat expectations. [...] Consumer\n\n# Costco’s Earnings Beat
Estimates on Steady Consumer Demand\n\nThis article is for subscribers only.\n\n## Takeaways by Bloomberg AI\n\nCostco Wholesale Corp. reported quarterly profit that was better than expectations, a sign that spending remains healthy as shoppers prioritize essentials and seek value.",
   "published_date": null
  },
  {
   "title": "Short- and Medium-Term Inflation Expectations Increase, Gas Price Growth Expectations Fall - FEDERAL RESERVE BANK of NEW YORK",
   "url": "https://links.message.bloomberg.com/s/c/HIhdPy0HfZW004tGEoJrwcaQ9iSEPDtwIXgpE3ux-LTLFMTqDwb-P1MU_TPi847igVy4TFEEdp2NGru0mjJvR16HRrpWbtea4nqkTW4pOqKDBOUO-
eDO2GzL76eDAXcT__VtyJgpJwqlo0G-W2XBmrpI63Kvzi99Cvg3MyXWMjYFi6asDu8NtVjdrwDblpIH2-SlTjtxfFiTacxPYWv_X_leY3BZ3QMyrVTIhK-o7NePqAhJe2CQCURVOXsd_6sgV67hURYNbO1VYfMHD9MgDcITYg/2by9EeUqDL2EVbMb8R5gl0CVKYUtsZZu/22",
   "content": "Median one-year-ahead earnings growth expectations increased by 0.1 percentage point to 2.8% in June. This is the highest reading since March 2025.\n Mean unemployment expectations—or the mean probability that the U.S. unemployment rate will be higher one year from now—decreased by
1.5 percentage points to 41.7%, remaining above the 12-month trailing average of 41.3%. [...] The SCE contains information about how consumers expect overall inflation and prices for food, gas, housing, and education to behave. It also provides insight into Americans’ views about job prospects and
earnings growth and their expectations about future spending and access to credit. The SCE also provides measures of uncertainty regarding consumers’ outlooks. Expectations are also available by age, geography, income, education, and numeracy. [...] about the unemployment rate declining. Spending
growth expectations were unchanged. Respondents were more optimistic about their future household financial situations, while expectations about future credit availability deteriorated slightly. The survey was fielded from June 1 through June 30, 2026.",
   "published_date": null
  },
  {
   "title": "General Motors beats Wall Street’s Q3 earnings expectations, narrows full-year guidance",
   "url": "https://www.cnbc.com/video/2026/10/20/general-motors-beats-wall-streetas-q3-earnings-expectations-narrows-full-year-guidance.html",
   "content": "Load More [...] 27 min ago\nwatch now\nwatch now\nVIDEO\n06:23\nWe're in the 'final innings' of the market correction, says Morgan Stanley's Mike Wilson\n33 min ago\nwatch now\nwatch now\nVIDEO\n29:06\nWPP AI chief says AI will start shopping for you, changing how brands
advertise\nwatch now\nwatch now\nVIDEO\n01:27\nTrump on Putin-Xi summit without Zelenskyy: I would do anything to stop the war\nwatch now\nwatch now\nVIDEO\n01:53\nUkraine’s Zelenskyy criticizes President Trump’s decision to suspend new sanctions on Russia [...] Share Article via LinkedIn\nShare
Article via Email\nSquawk Box\nGeneral Motors beats Wall Street’s Q3 earnings expectations, narrows full-year guidance\nCNBC's Phil LeBeau reports on the company's quarterly earnings results.\n03:27\nan hour ago\nwatch now\nwatch now\nVIDEO\n07:11\nGM CFO Paul Jacobson on $20B stock buyback: Driven
by our stellar free cash flow generation\n27 min ago\nwatch now\nwatch now\nVIDEO\n06:23\nWe're in the 'final innings' of the market correction, says Morgan Stanley's Mike Wilson",
   "published_date": null
  },
  {
   "title": "Baby boomers may be driving resilient consumer spending",
   "url": "https://www.cnbc.com/2026/10/12/baby-boomers-may-be-driving-resilient-consumer-spending.html",
   "content": "Investment withdrawals also represented a growing share of consumer spending, the report found. In April 2026, net transfers from investments to checking accounts equaled 6.8% of spending, up from 3.5% in April 2019. [...] Families headed by someone age 75 or older experienced a 37%
increase in inflation-adjusted median net worth between 2022 and 2025, according to the Fed's \"Changes in U.S. Family Finances from 2022 to 2025\" report from the Survey of Consumer Finances, released Friday.\n\nMeanwhile, families headed by someone under age 35 saw their median net worth decline
23% over the same period. [...] During the three months ending in April 2026, 8.2% of individuals moved money from investment holdings to their checking accounts, according to a September report from the JPMorganChase Institute. That's up from 4% during the same period in 2019. The economic think
tank, which is part of JPMorgan Chase, examined more than 20 million de-identified Chase checking accounts.",
   "published_date": null
  },
  {
   "title": "Fed’s preferred gauge showed core inflation at 3.0% in August, much lighter than expected",
   "url": "https://www.cnbc.com/2026/09/30/feds-preferred-gauge-showed-core-inflation-at-3point0percent-in-august-much-lighter-than-expected.html",
   "content": "The August personal consumption expenditures price index, the Fed’s main inflation gauge, saw an increase of 3.4% on headline and 3% for core, both well below estimates.\n   In addition, the Commerce Department reported stronger-than-expected spending numbers for the month, though
income was light.\n   Markets priced in a lower probability for an October rate hike following the release, though they still expect an increase in December. [...] Second-quarter GDP was revised sharply higher, due to increases in consumer and government spending as well as private sales. [...] The
personal consumption expenditures price index rose a seasonally adjusted 0.3% for the month, putting the 12-month gain at 3.4%. Economists surveyed by Dow Jones had been looking for increases of 0.3% and 3.7%, respectively.\n\nExcluding food and energy, PCE posted a 0.2% climb that put the annual
core level at 3%. The respective forecasts were for 0.3% and 3.3%.\n\nThough the Fed officially follows the headline PCE number, officials generally consider core a better gauge of longer-term trends.",
   "published_date": null
  }
 ]
}

[tool 8] tavily_financial_search {"query": "NVDA recent news earnings expectations guidance AI demand valuation", "ticker": "NVDA"}
{
 "query": "NVDA NVDA recent news earnings expectations guidance AI demand valuation",
 "results": [
  {
   "title": "Nvidia (NVDA) earnings report Q3 2026",
   "url": "https://www.cnbc.com/2025/11/19/nvidia-nvda-earnings-report-q3-2026.html?msockid=145bdde735ce6a2d1ececb5e34906bb6",
   "content": "In this article\n\nNvidia reported fiscal third-quarter earnings and revenue that topped Wall Street expectations on Wednesday and provided stronger-than-expected sales guidance for the fourth quarter.\n\nShares of the AI chipmaker rose more than 4% in extended trading.\n\nHere's how
the company did, compared with estimates from analysts polled by LSEG:\n\nNvidia said it expects about $65 billion in sales in the current quarter, versus $61.66 billion expected by analysts. [...] The company said net income in the quarter rose 65% to $31.91 billion, or $1.30 per share, from $19.31
billion, or 78 cents per share, in the year-ago period.\n\nNvidia has become the most valuable publicly traded company, mostly on insatiable demand for its AI chips, called GPUs. Nvidia counts Microsoft, Amazon, Google, Oracle, and Meta as customers. Its chips are used by all the leading tech
companies to develop new artificial intelligence models. [...] Nvidia's sales and outlook are closely watched by the technology industry as a sign for the health of the AI boom.\n\n\"There's been a lot of talk about an AI bubble,\" Nvidia CEO Jensen Huang told investors on an earnings call. \"From
our vantage point, we see something very different.\"",
   "published_date": null
  },
  {
   "title": "Nvidia (NVDA) earnings report Q3 2026",
   "url": "https://www.cnbc.com/2025/11/19/nvidia-nvda-earnings-report-q3-2026.html?msockid=2c352abfc211605b36253c06c32f614a",
   "content": "In this article\n\nNvidia reported fiscal third-quarter earnings and revenue that topped Wall Street expectations on Wednesday and provided stronger-than-expected sales guidance for the fourth quarter.\n\nShares of the AI chipmaker rose more than 4% in extended trading.\n\nHere's how
the company did, compared with estimates from analysts polled by LSEG:\n\nNvidia said it expects about $65 billion in sales in the current quarter, versus $61.66 billion expected by analysts. [...] The company said net income in the quarter rose 65% to $31.91 billion, or $1.30 per share, from $19.31
billion, or 78 cents per share, in the year-ago period.\n\nNvidia has become the most valuable publicly traded company, mostly on insatiable demand for its AI chips, called GPUs. Nvidia counts Microsoft, Amazon, Google, Oracle, and Meta as customers. Its chips are used by all the leading tech
companies to develop new artificial intelligence models. [...] Nvidia's sales and outlook are closely watched by the technology industry as a sign for the health of the AI boom.\n\n\"There's been a lot of talk about an AI bubble,\" Nvidia CEO Jensen Huang told investors on an earnings call. \"From
our vantage point, we see something very different.\"",
   "published_date": null
  },
  {
   "title": "Nvidia (NVDA) earnings report Q3 2026",
   "url": "https://www.cnbc.com/2025/11/19/nvidia-nvda-earnings-report-q3-2026.html?msockid=2cf2fb09be3368db1905edb0bfce698b",
   "content": "In this article\n\nNvidia reported fiscal third-quarter earnings and revenue that topped Wall Street expectations on Wednesday and provided stronger-than-expected sales guidance for the fourth quarter.\n\nShares of the AI chipmaker rose more than 4% in extended trading.\n\nHere's how
the company did, compared with estimates from analysts polled by LSEG:\n\nNvidia said it expects about $65 billion in sales in the current quarter, versus $61.66 billion expected by analysts. [...] The company said net income in the quarter rose 65% to $31.91 billion, or $1.30 per share, from $19.31
billion, or 78 cents per share, in the year-ago period.\n\nNvidia has become the most valuable publicly traded company, mostly on insatiable demand for its AI chips, called GPUs. Nvidia counts Microsoft, Amazon, Google, Oracle, and Meta as customers. Its chips are used by all the leading tech
companies to develop new artificial intelligence models. [...] Nvidia's sales and outlook are closely watched by the technology industry as a sign for the health of the AI boom.\n\n\"There's been a lot of talk about an AI bubble,\" Nvidia CEO Jensen Huang told investors on an earnings call. \"From
our vantage point, we see something very different.\"",
   "published_date": null
  },
  {
   "title": "Nvidia (NVDA) earnings report Q3 2026",
   "url": "https://www.cnbc.com/2025/11/19/nvidia-nvda-earnings-report-q3-2026.html?msockid=2479bd23514565df1790ab9a50b564eb",
   "content": "In this article\n\nNvidia reported fiscal third-quarter earnings and revenue that topped Wall Street expectations on Wednesday and provided stronger-than-expected sales guidance for the fourth quarter.\n\nShares of the AI chipmaker rose more than 4% in extended trading.\n\nHere's how
the company did, compared with estimates from analysts polled by LSEG:\n\nNvidia said it expects about $65 billion in sales in the current quarter, versus $61.66 billion expected by analysts. [...] The company said net income in the quarter rose 65% to $31.91 billion, or $1.30 per share, from $19.31
billion, or 78 cents per share, in the year-ago period.\n\nNvidia has become the most valuable publicly traded company, mostly on insatiable demand for its AI chips, called GPUs. Nvidia counts Microsoft, Amazon, Google, Oracle, and Meta as customers. Its chips are used by all the leading tech
companies to develop new artificial intelligence models. [...] Nvidia's sales and outlook are closely watched by the technology industry as a sign for the health of the AI boom.\n\n\"There's been a lot of talk about an AI bubble,\" Nvidia CEO Jensen Huang told investors on an earnings call. \"From
our vantage point, we see something very different.\"",
   "published_date": null
  },
  {
   "title": "Nvidia (NVDA) earnings report Q3 2026",
   "url": "https://www.cnbc.com/2025/11/19/nvidia-nvda-earnings-report-q3-2026.html?msockid=1a309ca143f16a4724c98a1842de6be4",
   "content": "In this article\n\nNvidia reported fiscal third-quarter earnings and revenue that topped Wall Street expectations on Wednesday and provided stronger-than-expected sales guidance for the fourth quarter.\n\nShares of the AI chipmaker rose more than 4% in extended trading.\n\nHere's how
the company did, compared with estimates from analysts polled by LSEG:\n\nNvidia said it expects about $65 billion in sales in the current quarter, versus $61.66 billion expected by analysts. [...] The company said net income in the quarter rose 65% to $31.91 billion, or $1.30 per share, from $19.31
billion, or 78 cents per share, in the year-ago period.\n\nNvidia has become the most valuable publicly traded company, mostly on insatiable demand for its AI chips, called GPUs. Nvidia counts Microsoft, Amazon, Google, Oracle, and Meta as customers. Its chips are used by all the leading tech
companies to develop new artificial intelligence models.",
   "published_date": null
  }
 ]
}
----- END EVIDENCE F0002 -----

----- BEGIN ANSWER F0002 -----
**結論：若問「誰最容易先被市場重新下修期待」，我會排序為：輝達 NVDA ＞ 禮來 LLY ＞ 好市多 COST。**

這不是在說基本面最差，而是比較三家公司目前股價所隱含的期待，哪一家最容易因為「成長沒有繼續超預期」而遭遇估值或預期重設。

## 1. 輝達：最容易先被下修，因為市場期待最高、業績對少數變數極敏感

Finnhub數據顯示，輝達TTM營收年增約83%、EPS年增約125%，TTM本益比約26.9倍、預估本益比約17.0倍；這代表估值表面上不算極端，但前提是AI需求與獲利仍要維持非常高的成長速度。

輝達的問題不是目前成長不夠，而是市場已經把「AI資本支出持續爆發、主要客戶持續加單、供應鏈能順利擴張」納入預期。公司FY2026 10-K（截至2026-01-25）明確指出，長製造週期、需求預估錯誤與供應能力不確定，可能造成供需錯配、缺貨或過剩庫存[1][2]。公司也披露，FY2026兩個直接客戶分別占營收22%與14%，而客戶通常可以取消、修改或延後訂單[3]。

更重要的是，輝達自己列出的需求風險包括資料中心容量、能源、客戶資本、AI應用需求、競爭技術與出口管制等因素[2][4]。因此，只要市場開始懷疑：

- 超大規模雲端客戶的AI資本支出回報率；
- Blackwell或後續產品的出貨節奏；
- 客戶是否延後訂單或自行開發替代方案；
- AI基礎設施是否受到電力、資料中心或融資限制；

市場可能不必等到輝達實際衰退，就先下修未來幾季的成長假設。

近期新聞仍顯示輝達業績與指引超過分析師預期，且公司預估下一季營收約650億美元，高於市場預期的616.6億美元[5]。這反而提高了「必須持續超預期」的門檻。**輝達最容易先被下修的核心原因，是它的股價與市場情緒高度依賴未來需求，而不是已經成熟、可預測的現金流。**

## 2. 禮來：估值高，但需求仍有實質驗證；風險集中在GLP-1價格、支付與產品集中度

禮來TTM本益比約45.3倍、預估本益比約26.2倍，營收年增約49.6%、EPS年增約94.6%。估值明顯高於傳統大型製藥公司，市場對Mounjaro、Zepbound及後續口服減重藥的長期市場規模抱有很高期待。

禮來FY2025 10-K（截至2025-12-43）披露，Mounjaro與Zepbound合計占2025年總營收56%，六項主要產品合計占82%[6]。公司也指出，減重藥的支付覆蓋、患者自費能力、價格、競爭產品與政府定價政策，都可能影響銷量與收入[7][8]。

因此，禮來的預期下修觸發點可能包括：

- GLP-1藥物價格下降速度快於銷量增加；
- 保險或政府支付覆蓋不如預期；
- 口服產品上市或臨床進度不順；
- 供應擴張跟不上需求，或需求預估過高；
- 競爭者推出更便宜、更方便或療效更好的產品。

不過，禮來目前仍有較強的需求支撐。近期報導顯示，公司持續上調營收指引，主要受Zepbound與Mounjaro需求推動[9][10]。所以相較輝達，禮來的成長雖然也被高度定價，但其需求來自醫療使用與患者治療，而非完全依賴少數科技公司的資本支出。

**禮來是第二容易被下修者：估值與產品集中度都高，但目前需求的可見度仍略優於輝達。**

## 3. 好市多：估值最昂貴，但基本面預期較容易維持

好市多TTM本益比約48.3倍、預估本益比約39.7倍，明顯是三者中估值最昂貴者；但其營收年增約10.1%、EPS年增約14.0%，成長速度遠低於輝達與禮來。

表面上看，這似乎代表好市多最容易因估值過高而下修。但好市多的市場期待通常是：

- 會員數持續成長；
- 續約率維持高位；
- 同店銷售穩定；
- Executive會員滲透率提高；
- 低價與價值定位持續吸引消費者。

好市多FY2026 10-K（截至2026-08-30）明確表示，會員成長、忠誠度、品牌與續約率是盈利的核心；公司也承認股價反映了很高的未來營運期待，若同店銷售、會員費收入、續約率、毛利率或EPS未達預期，股價可能下跌[11][12]。

但好市多的預期通常是「穩定複利」，而不是每季都要大幅超越高成長預測。其會員制、低價定位與高續約黏著度，讓收入與現金流相對容易預測。即使消費環境轉弱，價值型消費也可能使好市多相對受益；近期新聞亦顯示其季度獲利與可比銷售優於預期，反映消費者仍重視必需品與價格價值[13]。

所以，好市多最大的風險是**估值壓縮**，而不是基本面突然反轉。只要會員成長與續約率沒有明顯惡化，市場可能接受較低報酬率，而不一定立即大幅下修營運預期。

## 綜合比較

| 公司 | 市場最在意的指標 | 預期下修的主要觸發點 | 先被下修機率 |
|---|---|---|---|
| 輝達 | AI需求、雲端資本支出、資料中心出貨 | 客戶延單、AI投資回報疑慮、供需錯配、競爭或出口限制 | **最高** |
| 禮來 | GLP-1銷量、價格、支付覆蓋、口服藥進度 | 價格壓力、支付不及預期、競爭、產品集中風險 | **中高** |
| 好市多 | 會員成長、續約率、同店銷售、毛利率 | 會員指標放緩、消費轉弱、估值壓縮 | **中等** |

**我的判斷是：輝達最可能最先遭遇「預期下修」；禮來其次；好市多則最可能先遭遇「估值消化」，而不是盈利預期快速下修。**

換句話說：

- **輝達：最怕成長率下降。**
- **禮來：最怕GLP-1商業模式的價格與支付被重新定價。**
- **好市多：最怕高估值，但基本面韌性相對最好。**

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: https://www.cnbc.com/2025/11/19/nvidia-nvda-earnings-report-q3-2026.html?msockid=145bdde735ce6a2d1ececb5e34906bb6 "Nvidia (NVDA) earnings report Q3 2026"  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt  
[8]: SEC 10-K excerpt  
[9]: https://www.cnbc.com/2026/04/30/eli-lilly-lly-earnings-q1-2026.html "Eli Lilly (LLY) earnings Q1 2026"  
[10]: https://www.cnbc.com/2026/08/05/eli-lilly-lly-earnings-q2-2026.html "Eli Lilly (LLY) earnings Q2 2026"  
[11]: SEC 10-K excerpt  
[12]: SEC 10-K excerpt  
[13]: https://www.bloomberg.com/news/articles/2025-09-25/costco-s-earnings-beat-estimates-on-steady-consumer-demand "Costco’s Earnings Beat Estimates on Steady Consumer Demand"
----- END ANSWER F0002 -----

===== ITEM F0003 =====

QUESTION:
好市多真正的賺錢核心到底是什麼？會員費的重要性有多高？

----- BEGIN EVIDENCE F0003 -----
[tool 0] sec_filing_search {"query": "Costco business model core profit drivers membership fees importance renewal rates gross margin operating income", "ticker": "COST", "fiscal_year": null}
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
     "source": "sec://0000909832-26-000093/unknown#0",
     "title": "COST FY2026 10-K",
     "content": "# Part I\n\nItem 1—Business\n\nCostco Wholesale Corporation and its subsidiaries (Costco or the Company) began operations in 1983, in Seattle, Washington. We are principally engaged in the operation of membership warehouses in the United States (U.S.) and Puerto Rico, Canada,
Mexico, Japan, the United Kingdom (U.K.), Korea, Australia, Taiwan, China, Spain, France, Sweden, Iceland, and New Zealand. Costco operated 939, 914, and 890 warehouses worldwide at August 30, 2026, August 31, 2025, and September 1, 2024. The Company operates e-commerce sites in the U.S., Canada,
Mexico, the U.K., Korea, Taiwan, Japan, Australia, and China. Our common stock trades on the NASDAQ Global Select Market, under the symbol “COST.”\n\nWe report on a 52/53-week fiscal year, consisting of thirteen four-week periods and ending on the Sunday nearest the end of August. The first three
quarters consist of three periods each, and the fourth quarter consists of four periods (five weeks in the thirteenth period in a 53-week year). The material seasonal impact in our operations is increased net sales and earnings during the winter holiday season. References to 2026, 2025, and 2024
relate to the 52-week fiscal years ended August 30, 2026, August 31, 2025, and September 1, 2024.\n\nGeneral\n\nWe operate membership warehouses and e-commerce sites based on the concept that offering low prices on a limited selection of nationally-branded and private-label products in a wide range
of categories will produce high sales volumes and rapid inventory turnover. When combined with the operating efficiencies achieved by volume purchasing, efficient distribution and reduced handling of merchandise in no-frills, self-service warehouse facilities, these volumes and turnover enable us to
operate profitably at significantly lower gross margins (net sales less merchandise costs) than most other retailers. We often sell inventory before we are required to pay for it, even while taking advantage of early payment discounts.\n\nWe buy most of our merchandise directly from suppliers and
route it to cross-docking consolidation points (depots) or directly to our warehouses. Our depots receive large shipments from suppliers and quickly\n\n3\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)",
     "score": 0.5708
    },
    {
     "source": "sec://0000909832-26-000093/unknown#1",
     "title": "COST FY2026 10-K",
     "content": "3\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nship these goods to warehouses. This process creates freight volume and handling efficiencies, lowering costs associated with traditional multiple-step distribution channels. Our e-commerce operations ship
merchandise through our depots and logistics operations, as well as through drop-ship and other delivery arrangements with our suppliers.\n\nOur average warehouse space is approximately 148,000 square feet, with newer units being slightly larger. Floor plans are designed for efficiency in the use of
selling space, the handling of merchandise, and the control of inventory. Because shoppers are attracted principally by the quality of merchandise and low prices, our warehouses are not elaborate. By strictly controlling the entrances and exits and using a membership format, we believe our inventory
losses (shrinkage) are well below those of typical retail operations.\n\nOur operating hours are shorter than many other retailers, and due to other efficiencies inherent in a warehouse club operation, we believe labor costs are lower relative to the volume of sales. In the U.S., we offer exclusive
shopping hours for our Executive members and our gasoline operations generally have extended hours. Merchandise is generally stored on racks above the sales floor and displayed on pallets containing large quantities, reducing labor required. In general, with variations by country, our warehouses
accept certain credit cards, including Costco co-branded cards, debit cards, cash and checks, Executive member reward certificates, co-brand cardholder rebates, and our proprietary stored-value card (shop card).\n\nOur strategy is to provide our members with a broad range of high-quality merchandise
at prices we believe are consistently lower than elsewhere. We seek to limit most items to fast-selling models, sizes, and colors. We carry less than 4,000 active stock keeping units (SKUs) per warehouse in our core warehouse business, significantly less than other broadline retailers. We average
from 9,000 to 11,000 SKUs online, some of which are available in our warehouses. Many consumable products are offered for sale in case, carton, or multiple-pack quantities only.\n\nTo promote member satisfaction, we generally accept returns of merchandise. On certain electronic items, we have a
90-day return policy and provide, free of charge, technical support services, as well as an extended warranty. Additional third-party warranty coverage is sold on certain electronic items and major appliances.\n\nWe offer merchandise and services in the following categories:\n\n■Core Merchandise
Categories:",
     "score": 0.5432
    },
    {
     "source": "sec://0000909832-26-000093/unknown#2",
     "title": "COST FY2026 10-K",
     "content": "We offer merchandise and services in the following categories:\n\n■Core Merchandise Categories:\n\n•Foods and Sundries (including sundries, dry grocery, candy, cooler, freezer, liquor, and tobacco)\n\n•Non-Foods (including consumer electronics, appliances, small electrics, health
and beauty aids, hardware, lawn and garden, sporting goods, tires, toys and seasonal, automotive, stamps, tickets, apparel, furniture, domestics, housewares, special order kiosk, and jewelry)\n\n•Fresh Foods (including meat, produce, deli, and bakery)\n\n■Warehouse Ancillary (includes gasoline,
pharmacy, food court, optical, hearing aids, and tire installation)\n\n■Other Businesses (includes e-commerce, business centers, travel, and other)\n\nWarehouse ancillary operate primarily within, next to or near our warehouses, encouraging more frequent shopping. The number of warehouses with gas
stations varies significantly by country. We operated 774 gas stations at the end of 2026. Our gasoline business represented 11% of total net sales in 2026.\n\n4\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nOur other businesses sell products and services that largely
complement our warehouse operations. Our business centers carry items tailored for food services, convenience stores, and offices, and offer walk-in shopping and deliveries. Business centers are included in our total warehouse count. Our e-commerce operations give members convenience and a broader
selection of goods and services. Costco Travel offers vacation packages, car rentals, cruises and other travel products exclusively for Costco members in varying degrees in the U.S., Canada, the U.K., and Australia. Digitally-enabled sales, which represents sales that are initiated through a digital
device, whether fulfilled through a warehouse or distribution center, as well as Costco Travel, represented 11% of total net sales in 2026.\n\nWe have direct relationships with many producers of brand-name merchandise. We do not obtain a significant portion of merchandise from any one supplier. When
sources of supply become unavailable, we seek alternative sources or items. We pursue diversification in our supply-chain and seek to expand in-country production. We also purchase and manufacture private-label merchandise, where quality and member demand are high and the value to our members is
significant.",
     "score": 0.5515
    },
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
     "score": 0.5793
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
     "score": 0.5971
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
     "score": 0.5655
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
     "score": 0.7097
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
     "score": 0.5418
    },
    {
     "source": "sec://0000909832-26-000093/unknown#52",
     "title": "COST FY2026 10-K",
     "content": "26\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nAs previously reported, we increased annual membership fees in the U.S. and Canada, effective September 1, 2024. We account for membership fee revenue on a deferred basis, recognized ratably over the one-year
membership period. The fee income increase accounted for approximately 30% and 40% of membership income growth during 2026 and 2025.\n\nGross Margin\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- |\n|  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net sales | | | $ | 297,247 | |  | | | $ | 269,912 | |  | | | $ | 249,625 | |\n| Less merchandise costs | | | 264,279 | | |  | | | 239,886 | | |  | | | 222,358 | | |\n| Gross margin | | | $ | 32,968 | |  | | | $ | 30,026 |
|  | | | $ | 27,267 | |\n| Gross margin percentage | | | 11.09 | | % |  | | | 11.12 | | % |  | | | 10.92 | | % |",
     "score": 0.5517
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
     "score": 0.5666
    }
   ]
  }
 ]
}

[tool 1] finnhub_company_basic_financials {"ticker": "COST"}
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
----- END EVIDENCE F0003 -----

----- BEGIN ANSWER F0003 -----
**結論：好市多真正的賺錢核心，不是靠商品高毛利，而是「會員制帶來的高頻、低價、高周轉零售飛輪」；會員費則是最穩定、利潤率最高、支撐低商品毛利策略的關鍵收入來源。**

以下採用好市多 **FY2026 10-K，財政年度截至 2026-08-30** 的資料。

### 1. 核心不是「賣貴」，而是用低價換取高銷量與高周轉

好市多明確表示，其模式是以有限商品選擇、低價格、高銷售量和快速庫存周轉為基礎；大量採購、交叉轉運、簡化倉儲和較低的門市營運成本，使公司能以遠低於多數零售商的商品毛利率營運。[1]

這代表好市多的主要經濟引擎是：

- 會員願意反覆進店；
- 每次購買金額高；
- 商品周轉快；
- 大量採購降低進貨與物流成本；
- 高銷售額攤薄人工、租金和管理費用；
- 低價強化會員續費與購物頻率。

公司自己也指出，**最重要的獲利驅動因素是增加淨銷售，尤其是同店銷售**；同店銷售成長主要來自購物頻率和平均客單價提高，而更高的銷售額能讓固定營運費用被攤薄，提升獲利能力。[2]

### 2. 商品本身的毛利其實很薄

FY2026：

- 商品銷售額：2,972.47 億美元
- 商品成本：2,642.79 億美元
- 商品毛利：329.68 億美元
- 商品毛利率：**11.09%**
- 會員費收入：**59.07 億美元**[3]

這個 11% 左右的毛利率非常低，正是好市多與一般零售商不同的地方。它不是靠單件商品賺很多，而是靠**規模、周轉、效率和會員黏著度**賺錢。

此外，汽油等業務通常毛利率更低，但能增加到店流量；公司也表示汽油業務主要具有引流作用，而不是高毛利來源。[4]

### 3. 會員費的重要性有多高？

會員費的重要性可以分成三個層次：

#### 第一，會員費是高品質、可預測的收入

FY2026 會員費收入為 **59.07 億美元**，較 FY2025 的 53.23 億美元增加約 11%。會員費收入增加，主要來自新會員、會員費調整，以及升級至 Executive 會員。[3]

會員費不是一次性收入，而是按一年會員期間遞延並平均確認，因此具有相對穩定、可預測的特性。[5]

#### 第二，會員費支撐好市多的低價策略

好市多的會員制並不只是收費工具，而是整個商業模式的基礎。公司明確表示，會員制對業務和獲利能力具有整合性作用，會員數成長、Executive 會員滲透率和續費率，都會重大影響獲利。[6]

換句話說，會員費讓好市多可以：

- 不必把商品價格訂得很高；
- 維持「價格權威」和低價形象；
- 用低價吸引會員增加購物；
- 再用高購物頻率提高整體銷售；
- 透過規模和效率獲利。

因此，會員費的價值不只在帳面上的 59 億美元，而在於它讓整個商品零售業務能以低毛利模式運作。

#### 第三，會員費對獲利的貢獻可能遠高於其收入占比

會員費約占 FY2026 商品銷售額的 **2%**，看起來不算很大；但它通常不需要像商品銷售一樣承擔進貨成本，因此對營業利益的貢獻會非常重要。

不過，根據目前取得的 10-K 摘錄，**沒有提供會員費的獨立營業利益或稅後淨利數字**，所以不能嚴格地說「會員費占淨利多少百分比」。能確定的是：在商品毛利率僅約 11.09%、整體零售利潤率很薄的模式下，會員費對獲利具有不成比例的重要性。[3]

### 4. 會員黏著度是比會員費價格更重要的資產

FY2026 好市多有：

- 付費會員：8,410 萬
- 全球持卡人：1.504 億
- Executive 會員：4,230 萬
- Executive 會員約占全球淨銷售：**75.2%**
- 美國及加拿大續費率：**92.3%**
- 全球續費率：**89.8%**[7]

這些數字說明，好市多真正珍貴的資產不是單純的會員費，而是：

> **大量會員 × 高續費率 × 高購物金額 × 高 Executive 滲透率**

Executive 會員尤其重要，因為他們支付更高年費，且約占全球銷售額 75.2%，代表高價值會員對銷售有高度集中貢獻。[7]

### 5. 最值得注意的「飛輪」

好市多的商業飛輪可以簡化為：

**會員費 → 支持低價 → 會員增加購物 → 銷售量與周轉提高 → 採購及營運效率改善 → 更有能力維持低價 → 續費率提高**

所以，會員費本身不是唯一的獲利來源；它更像是整個飛輪的「入場費」和穩定資金來源。

### 投資上應該看什麼？

比起只看會員費收入，應該重點追蹤：

1. **續費率**：是否仍維持高於 90% 的核心市場水準；
2. **付費會員成長**；
3. **Executive 會員滲透率**；
4. **同店銷售成長**；
5. **購物頻率與平均客單價**；
6. **商品毛利率是否失控**；
7. **會員費調漲後是否影響續費率**。

**一句話總結：**好市多不是「靠會員費養活的零售商」，而是「用會員費建立低價、高周轉、高黏著零售系統的公司」。會員費是獲利的底座；真正的長期價值，來自會員制帶動的銷售規模、續費率和購物頻率。

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt
----- END ANSWER F0003 -----

===== ITEM F0004 =====

QUESTION:
如果只是輕度衰退，沃爾瑪、好市多、麥當勞誰最有相對韌性？

----- BEGIN EVIDENCE F0004 -----
[tool 0] sec_filing_search {"query": "recession resilience consumer spending defensive demand value proposition membership renewal traffic comparable sales risks", "ticker": "COST", "fiscal_year": null}
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
     "score": 0.5745
    },
    {
     "source": "sec://0000909832-26-000093/unknown#15",
     "title": "COST FY2026 10-K",
     "content": "We may not timely identify or effectively respond to consumer tastes and preferences, which could negatively affect our relationship with our members, the demand for our products and services, and our market share.\n\nIt is difficult to consistently and successfully predict the
products and services that our members will desire. Our success depends, in part, on our ability to identify and respond to trends in demographics and consumer preferences. Failure to identify timely or effectively respond to changing consumer tastes, preferences and spending patterns including
those related to resource efficiency, environmental protection, human rights, and the transition to a low-carbon economy could negatively affect our relationship with our members, the demand for our products and services, and our market share. We sell a substantial amount of gasoline, the demand for
which could be impacted by concerns and regulation about climate change.\n\nIf we are not successful at predicting our sales trends and adjusting our purchases accordingly, we may have excess inventory, which could result in additional markdowns, or we may experience out-of-stock positions and
delivery delays, which could result in higher costs, both of which would reduce our operating performance. This could have an adverse effect on net sales, gross margin and operating income.\n\n10\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nAvailability and performance of our
IT systems are vital to our business. Failure to successfully execute IT projects and have IT systems available to our business would adversely impact our operations.",
     "score": 0.5012
    },
    {
     "source": "sec://0000909832-26-000093/unknown#19",
     "title": "COST FY2026 10-K",
     "content": "We are subject to payment-related risks.\n\nWe accept payments using a variety of methods, including select credit and debit cards, cash and checks, co-brand cardholder rebates, Executive member reward certificates, and our shop card. As we offer new payment options to our members,
we may be subject to additional rules, regulations, compliance requirements, and higher fraud losses. For certain payment methods, we pay interchange and other related acceptance fees, along with additional transaction processing fees. We rely on third parties to provide payment transaction
processing services for credit and debit cards and our shop card. It could disrupt our business if these parties become unwilling or unable to provide these services to us. We are also subject to fee increases by these service providers.\n\nWe must comply with evolving payment card association and
network operating rules, including data security rules, certification requirements, and rules governing electronic funds transfers. For example, we are subject to Payment Card Industry Data Security Standards, which contain compliance guidelines and standards with regard to our security surrounding
the physical and electronic storage, processing, and transmission of individual cardholder data. If our internal systems are breached or compromised, we may be liable for card re-issuance costs, subject to fines and higher transaction fees, and lose our ability to accept card payments from our
members, and our business and operating results could be adversely affected. Our failure to offer payment methods desired by our members could create a competitive disadvantage.\n\nWe might sell products that cause illness or injury to our members, harm to our reputation, and expose us to
litigation.\n\nIf our merchandise, including food and prepared food products for human consumption, drugs, children's products, pet products, and durable goods, do not meet or are perceived not to meet applicable safety or labeling standards or our members' expectations, we could experience lost
sales, increased costs, litigation, or reputational harm. The sale of these items involves the risk of illness or injury to our members. Such illnesses or injuries could result from tampering by unauthorized third parties, product\n\n12\n\n\n[Table of
Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)",
     "score": 0.4978
    },
    {
     "source": "sec://0000909832-26-000093/unknown#22",
     "title": "COST FY2026 10-K",
     "content": "Market and Other External Risks\n\nWe face strong competition from other retailers and warehouse club operators, which could adversely affect our business, financial condition and results of operations.\n\nThe retail business is highly competitive. We compete for members, employees,
sites, products and services, and in other important respects with a wide range of local, regional and national wholesalers and retailers, both in the United States and in foreign countries, including other warehouse-club operators, supermarkets, supercenters, online retailers, gasoline stations,
pharmacies, hard discounters, department and specialty stores and operators selling a single category or narrow range of merchandise or services. Such retailers and warehouse club operators compete vigorously and in a variety of ways, including pricing, selection and availability, services,
location, convenience, store hours, and the attractiveness, and ease of use of websites and mobile applications. The evolution of retailing in online and mobile channels has improved the ability of customers to comparison shop, which has enhanced competition. Additionally, the emergence of AI tools
may change consumer shopping habits and increase the competition we face. AI may also present inaccurate pricing or product data, or fail to capture the full value of our membership offering, impacting member purchasing decisions by prioritizing immediate or inaccurate price comparison or logistics
over member loyalty. Some competitors have greater technology capabilities, including the faster adoption of AI technologies, and greater market penetration than we do. Our inability to respond effectively to competitive pressures, changes in the retail markets or customer expectations could result
in lost market share and negatively affect our financial results.\n\nGeneral economic factors, domestically and internationally, may adversely affect our business, financial condition, and results of operations.",
     "score": 0.5036
    },
    {
     "source": "sec://0000909832-26-000093/unknown#23",
     "title": "COST FY2026 10-K",
     "content": "General economic factors, domestically and internationally, may adversely affect our business, financial condition, and results of operations.\n\nHigher energy and gasoline costs, inflation, levels of unemployment, healthcare costs, consumer debt levels, foreign-currency exchange
rates, unsettled financial markets, weaknesses in housing and real estate markets, reduced consumer confidence, changes and uncertainties related to government fiscal, monetary, and tax policies including changes in interest rates, tax rates, duties, tariffs, or other restrictions, sovereign debt
crises, pandemics and other health crises, and other economic factors could adversely affect demand for our products and services, require a change in product mix, or impact the cost of or ability to purchase inventory. Additionally, trade-related actions in various countries have adversely affected
the costs of some of our merchandise. The degree of our exposure is dependent on (among other things) the type of goods, rates imposed, and timing of the tariffs and policy changes. The impact to our net sales and gross margin is influenced in part by our merchandising and pricing strategies in
response to potential cost increases. Higher tariffs could adversely impact our results.\n\nPrices of certain commodities, including gasoline and consumable goods used in manufacturing and our warehouse retail operations, are historically volatile and are subject to fluctuations arising from changes
in domestic and international supply and demand, inflationary pressures, labor costs, competition, market speculation, government regulations, taxes, and periodic delays in delivery. Rapid and significant changes in commodity prices and our ability and desire to pass them through to our members may
affect our sales and profit margins. These factors could also increase our merchandise costs and selling, general and administrative expenses, and otherwise adversely affect our operations and financial results. General economic conditions can also be affected by events like the outbreak of
hostilities or acts of terrorism.\n\nInflationary factors, such as increases in merchandise costs, may adversely affect our business, financial condition and results of operations. We may not be able to adjust prices to sufficiently offset the effect of cost increases without negatively impacting
consumer demand.\n\n14\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\nSuppliers may be unable to timely provide us with quality merchandise at competitive prices or may fail to adhere to our high standards, resulting in adverse effects on our business, merchandise inventories,
sales, and profits.",
     "score": 0.5021
    },
    {
     "source": "sec://0000909832-26-000093/unknown#26",
     "title": "COST FY2026 10-K",
     "content": "15\n\n\n[Table of Contents](#iae87f9b9600946fdb18e1436ed6ec90c_7)\n\n\ndisruption in the supply of products from some local or overseas suppliers, the temporary disruption in the transport of goods to or from overseas, delays in the delivery of goods to our warehouses or depots,
delays in online merchandise delivery, the temporary reduction in the availability of products in our warehouses, and long-term disruption or threats to the habitability of key markets in which we operate. These events could also reduce demand for our products or make it difficult or impossible to
procure products. We may be required to suspend operations in some or all of our locations, which could have a material adverse effect on our business, financial condition and results of operations.\n\nPandemics and other health crises could affect our business, financial condition and results of
operations in many respects.\n\nThe emergence, severity, magnitude, and duration of global or regional health crises are uncertain and difficult to predict. A pandemic could affect certain business operations, demand for our products and services, in-stock positions, costs of doing business,
availability of labor, access to inventory, supply chain operations, our ability to predict future performance, exposure to litigation, and our financial performance, among other things. Other factors and uncertainties include, but are not limited to: the severity and duration of pandemics; evolving
macroeconomic factors including general economic uncertainty, unemployment rates, and recessionary pressures; changes in labor markets affecting us and our suppliers; unknown consequences on our business performance and initiatives stemming from the substantial investment of time and other resources
to the pandemic response; the pace of post-pandemic recovery; the long-term impact of the pandemic on our business, including consumer behaviors; and disruption and volatility within the financial and credit markets.\n\nFailure to meet financial market expectations could adversely affect the market
price and volatility of our stock.\n\nWe believe that the price of our stock currently reflects high market expectations for our future operating results. Any failure to meet or delay in meeting these expectations, including our comparable sales growth rates, membership fee revenue, including new
member sign-ups and renewal rates, gross margin, earnings, earnings per share, new warehouse openings, or dividend or stock repurchase policies could cause the price of our stock to decline.\n\nLegal and Regulatory Risks\n\nChanges in or failure to comply with laws and regulations could adversely
impact our business, financial condition and results of operations.",
     "score": 0.518
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
     "score": 0.5326
    },
    {
     "source": "sec://0000909832-26-000093/unknown#44",
     "title": "COST FY2026 10-K",
     "content": "cannot control or reliably predict general economic health or changes in competition, we believe that we have been successful, historically, in adapting our business to these changes, such as through adjustments to our pricing and merchandise mix, including increasing the
penetration of our private-label items, and through online offerings.",
     "score": 0.4827
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
     "score": 0.5634
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
     "score": 0.5087
    }
   ]
  }
 ]
}

[tool 1] sec_filing_search {"query": "recession resilience consumer spending defensive demand value proposition membership renewal traffic comparable sales risks", "ticker": "WMT", "fiscal_year": null}
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
   "prelude": "Excerpts from WMT FY2026 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 6 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000104169-26-000055/7#94",
     "title": "WMT FY2026 10-K · Item 7 · Overview",
     "content": "### Overview\n\nThis discussion, which presents our results for the fiscal years ended January 31, 2026 (\"fiscal 2026\"), January 31, 2025 (\"fiscal 2025\") and January 31, 2024 (\"fiscal 2024\"), should be read in conjunction with our Consolidated Financial Statements and the
accompanying notes. We intend for this discussion to provide the reader with information that will assist in understanding our financial statements, the changes in certain key items in those financial statements from period to period and the primary factors that accounted for those changes. We also
discuss certain performance metrics that management uses to assess the Company's performance. Additionally, the discussion provides information about the financial results of each of the three segments of our business to provide a better understanding of how each of those segments and its results of
operations affect the financial condition and results of operations of the Company as a whole.\n\nThroughout this Item 7, we discuss segment operating income, comparable store and club sales and other measures. Management measures the results of the Company's segments using each segment's operating
income, including certain corporate overhead allocations, as well as other measures. From time to time, we revise the measurement of each segment's operating income and other measures as determined by the information regularly reviewed by our chief operating decision maker.\n\nIn discussing our
operating results, the term currency exchange rates refers to the currency exchange rates we use to convert the operating results for countries where the functional currency is not the U.S. dollar into U.S. dollars. We calculate the effect of changes in currency exchange rates as the difference
between current period activity translated using the current period's currency exchange rates and the comparable prior year period's currency exchange rates. Additionally, no currency exchange rate fluctuations are calculated for non-USD acquisitions until owned for 12 months. Throughout our
discussion, we refer to the results of this calculation as the impact of currency exchange rate fluctuations.\n\nRecent Developments, Macroeconomic Conditions and Potential Impacts",
     "score": 0.4869,
     "subsection": "Overview"
    },
    {
     "source": "sec://0000104169-26-000055/7#95",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "Recent Developments, Macroeconomic Conditions and Potential Impacts\n\nWe expect continued uncertainty in our business and the global economy due to the following factors: tariffs and trade restrictions; inflationary trends; fluctuations in global currencies; swings in macroeconomic
conditions and their effect on consumer confidence; changes in employment trends; volatility in fuel prices; and supply chain pressures, any of which may impact our results. While we operate in a highly dynamic tariff environment, less than one third of what we sell in the U.S. is imported, with
most of our imports coming from China, Mexico, Vietnam, India and Canada. Information on certain risks, factors, and uncertainties that can affect our operating results and an investment in our securities can be found herein under \"[Item 1A. Risk
Factors](#i6e16e33efce1499a82f13fd9f63b74c6_40).\"\n\nOur net sales and gross profit margin are influenced in part by our pricing and merchandising strategies in response to cost increases. Those pricing strategies include, but are not limited to: absorbing cost increases instead of passing those
cost increases on to our customers and members; reducing prices in certain merchandise categories; focusing on opening price points for certain food categories; and when necessary, passing cost increases on to our customers and members. Merchandising strategies include, but are not limited to:
working with our suppliers to reduce product costs and share in absorbing cost increases; focusing on private label brands and smaller pack sizes; earlier-than-usual purchasing and in greater volumes or moderating purchasing in certain categories; and securing ocean carrier and container capacity.
These strategies have and may continue to impact gross profit as a percentage of net sales.\n\nIn July 2025, the One Big Beautiful Bill Act (the \"OBBB Act\") was enacted, introducing a series of corporate tax changes in the U.S., including 100% bonus depreciation on qualified property and full
expensing for research and development expenditures. The impacts of the OBBB Act were not material to our income tax expense or effective tax rate. Certain provisions decreased cash taxes paid in fiscal 2026 and may change the timing of cash tax payments in future periods.\n\nFor a detailed
discussion on results of operations by reportable segment, refer to \"[Results of Operations](#i6e16e33efce1499a82f13fd9f63b74c6_91)\" below.",
     "score": 0.5124
    },
    {
     "source": "sec://0000104169-26-000055/7#97",
     "title": "WMT FY2026 10-K · Item 7 · Growth",
     "content": "### Growth\n\nOur objective of prioritizing growth means we will focus on serving customers and members however they want to shop through our omnichannel business model. This includes increasing comparable store and club sales through increasing membership at Sam's Club U.S. and
through Walmart+, accelerating eCommerce sales growth and expansion of omnichannel initiatives that complement our strategy.\n\nComparable sales is a metric that indicates the performance of our existing stores and clubs by measuring the change in sales for such stores and clubs, including eCommerce
sales, for a particular period over the corresponding period in the previous year. Walmart's definition of comparable sales includes sales from stores and clubs open for the previous 12 months, including remodels, relocations, expansions and conversions, as well as eCommerce sales. We measure the
eCommerce sales impact by including all sales initiated digitally, including omnichannel transactions which are fulfilled through our stores and clubs as well as certain other business offerings that are part of our ecosystem, such as our advertising net sales. Comparable sales are also referred to
as \"same-store\" sales by others within the retail industry. The method of calculating comparable sales varies across the retail industry. As a result, our calculation of comparable sales is not necessarily comparable to similarly titled measures reported by other companies.\n\nOur discussion of
our comparable sales below refers to our calendar comparable sales calculated using our fiscal calendar, which may result in differences when compared to comparable sales using the retail calendar (also known as the 4-5-4 calendar) as provided in our quarterly earnings releases. We report on
comparable sales in the U.S. as we believe it is a meaningful metric within the context of the U.S. retail market where there is a single currency, one inflationary market and generally consistent store and club formats from year to year.\n\nCalendar comparable sales, as well as the impact of fuel,
for fiscal 2026 and 2025, were as follows:",
     "score": 0.4985,
     "subsection": "Growth"
    },
    {
     "source": "sec://0000104169-26-000055/7#113",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | |  | | | Fiscal Years Ended January 31, | | | | | | | | | | | | | | |\n| (Dollar
amounts and retail square feet in millions) | | |  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net sales | | |  | | | $ | 706,413 |  |  | | | $ | 674,538 |  |  | | | $ | 642,637 |  |\n| Percentage change from comparable period | | |  | | | 4.7 | | % |  | | | 5.0 | | % |  | | | 6.1 | | %
|\n| Membership and other income(1) | | |  | | | 6,750 | |  |  | | | 6,447 | |  |  | | | 5,488 | |  |\n| Total revenues | | |  | | | 713,163 | |  |  | | | 680,985 | |  |  | | | 648,125 | |  |\n| Percentage change from comparable period | | |  | | | 4.7 | | % |  | | | 5.1 | | % |  | | | 6.0 | | %
|\n| Gross profit(2) | | |  | | | 171,018 | |  |  | | | 162,785 | |  |  | | | 152,495 | |  |\n| Operating expenses(2) | | |  | | | 147,943 | |  |  | | | 139,884 | |  |  | | | 130,971 | |  |",
     "score": 0.4747
    },
    {
     "source": "sec://0000104169-26-000055/7#123",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | |  | | | Fiscal Years Ended January 31, | | | | | | | | | | | | | | |\n| (Dollar
amounts and retail square feet in millions) | | |  | | | 2026 | | |  | | | 2025 | | |  | | | 2024 | | |\n| Net sales | | |  | | | $ | 130,423 |  |  | | | $ | 121,885 |  |  | | | $ | 114,641 |  |\n| Percentage change from comparable period | | |  | | | 7.0 | | % |  | | | 6.3 | | % |  | | | 13.5 | | %
|\n| Membership and other income | | |  | | | 1,565 | |  |  | | | 1,478 | |  |  | | | 1,408 | |  |\n| Gross profit | | |  | | | 27,847 | |  |  | | | 26,618 | |  |  | | | 24,810 | |  |\n| Operating expenses | | |  | | | 24,309 | |  |  | | | 22,595 | |  |  | | | 21,309 | |  |\n| Operating income | | |
| | | $ | 5,103 |  |  | | | $ | 5,501 |  |  | | | $ | 4,909 |  |\n|  | | |  | | |  | | |  | | |  | | |  | | |  | | |\n| Percentage of net sales | | |  | | |  | | |  | | |  | | |  | | |  | | |",
     "score": 0.4767
    },
    {
     "source": "sec://0000104169-26-000055/7#130",
     "title": "WMT FY2026 10-K · Item 7",
     "content": "(1)We believe the \"Excluding Fuel\" information is useful to investors because it permits investors to understand the effect of the Sam's Club U.S. segment's fuel sales on its results of operations, which are impacted by the volatility of fuel prices. Volatility in fuel prices may
continue to impact the operating results of the Sam's Club U.S. segment in the future.\n\nNet sales for the Sam's Club U.S. segment increased $2.8 billion or 3.1% and $4.1 billion or 4.7% for fiscal 2026 and 2025, respectively, when compared to the previous fiscal year. The increases in net sales
were primarily due to increases in comparable sales, including fuel, of 2.9% and 4.7% for fiscal 2026 and 2025, respectively. Comparable sales in fiscal 2026 were driven by growth in unit volumes and transactions, reflecting strong sales in grocery, health and wellness and general merchandise.
Comparable sales in fiscal 2025 were driven by growth in transactions and unit volumes, with strong sales in grocery and health and wellness. Additionally, fiscal 2026 and 2025 growth was partially offset by lower fuel sales, negatively impacting comparable sales by 1.9% and 1.5%, respectively,
primarily due to lower fuel prices. Sam's Club U.S. eCommerce sales positively contributed approximately 3.3% and 2.3% to comparable sales for fiscal 2026 and 2025, respectively, which reflects continued strength in member engagement with omnichannel offerings.\n\nMembership and other income
increased 8.7% and 13.3% for fiscal 2026 and 2025, respectively, when compared to the previous fiscal year. For fiscal 2026 and 2025, the increases were primarily due to growth in the membership base and Plus penetration. Fiscal 2026 was also positively impacted by additional breakage income related
to unredeemed Sam's Cash rewards, while fiscal 2025 was positively impacted by the expiration of a promotional offering offsetting membership fee increases during the fourth quarter of fiscal 2024.",
     "score": 0.4862
    }
   ]
  },
  {
   "ticker": "WMT",
   "fiscal_year": 2026,
   "item": "_unknown",
   "prelude": "Excerpts from WMT FY2026 10-K, _unknown — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000104169-26-000055/unknown#1",
     "title": "WMT FY2026 10-K",
     "content": "•the amount, number, growth, increase, reduction or decrease in or over certain periods, of or in certain financial items or measures or operating measures, including our earnings per share, net sales, growth rates, comparable store and club sales, our eCommerce sales, liabilities,
expenses of certain categories, including share-based compensation, expense leverage, operating income, returns, capital and operating investments or expenditures of particular types and new store and club openings, inventory levels and associated costs, product mix and demand for certain
merchandise, consumer confidence, disposable income, credit availability, spending levels, shopping patterns and debt levels;\n\n•our increasing investments in eCommerce, technology (including the use of artificial intelligence \"AI\"), automation, supply chain, new stores and clubs as well as
remodels and other omnichannel customer initiatives, such as same day pickup and delivery;\n\n•investments and capital expenditures we will make and how certain of those investments and capital expenditures are expected to be financed;\n\n•our workforce strategy, including the availability of
necessary personnel to staff our stores, clubs and other facilities and the potential impact of changes to the costs of labor;\n\n•volatility in currency exchange rates affecting our consolidated, or one or more of our segments' results of operations;\n\n•the Company continuing to provide returns to
shareholders through share repurchases and dividends, the use of share repurchase authorization over a certain period or the source of funding of a certain portion of our share repurchases;\n\n•our sources of liquidity, including our cash, continuing to be adequate or sufficient to fund our
operations, finance our global investment and expansion activities, pay dividends and fund share repurchases;\n\n•cash flows from operations, our current cash position and access to capital markets or credit will continue to be sufficient to meet our anticipated operating cash needs;\n\n•our
effective tax rate for certain periods and the realization of certain net deferred tax assets and the effects of resolutions of tax-related matters;\n\n4\n\n\n\n•the adoption or creation of new, and modification of existing, governmental policies, programs, initiatives and actions in the markets in
which we operate and elsewhere and actions with respect to such policies, programs and initiatives (including, but not limited to, changes in the enforcement priorities of regulatory authorities);",
     "score": 0.5097
    }
   ]
  },
  {
   "ticker": "WMT",
   "fiscal_year": 2026,
   "item": "Item 1A",
   "prelude": "Excerpts from WMT FY2026 10-K, Item 1A (Risk Factors) — 2 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000104169-26-000055/1a#29",
     "title": "WMT FY2026 10-K · Item 1A · Strategic Risks",
     "content": "### Strategic Risks\n\nFailure to successfully execute our omnichannel strategy and the cost of our investments in eCommerce and technology may materially adversely affect our market position, net sales and financial performance.\n\nThe retail business continues to rapidly evolve
with consumers embracing the digital shopping experience and expecting a robust online marketplace of goods available for purchase and delivery. As a result, the portion of total consumer expenditures with retailers and wholesale clubs occurring through digital platforms is increasing and the pace
of this increase could continue to accelerate.\n\nOur strategy, which includes investments in eCommerce, technology, AI, talent, supply chain automation and enhancements, advertising, acquisitions, joint ventures, new store and club openings and remodels and other customer initiatives, may not
adequately or effectively allow us to continue to grow our omnichannel business offerings, increase comparable sales or maintain or grow our overall market position. The success of this strategy will depend in large measure on our ability to continue building and delivering a seamless omnichannel
shopping experience and interconnected ecosystem for our customers that deepens and maintains our relationships with our customers across our various businesses and partnerships. Customers are using digital means, including websites, captive and third-party digital applications, social media, and
emerging agentic platforms to shop with us and our competitors and to do comparison shopping, and we use these digital means along with digital advertising, text messages and email to interact with our customers and enhance their shopping experience.\n\nThe success of this strategy is further
subject to the related risks discussed in this [Item 1A](#i6e16e33efce1499a82f13fd9f63b74c6_40). With the interconnected components of this enterprise strategy and an increasing allocation of capital expenditures focused on these initiatives, changes in customer or member perceptions about our
reputation in general, or our failure to successfully execute on individual components of this strategy may adversely affect our market position, net sales and financial performance, which could also result in impairment charges to intangible assets or other long-lived assets. In addition, a greater
concentration of eCommerce sales, including increasing online grocery sales and the increasing role of AI-enabled platforms in product search, discovery, advertising and purchasing, could result in a reduction in the amount of traffic in our stores and clubs, which would, in turn, reduce the
opportunities for cross-store or cross-club sales of merchandise that such traffic creates and could reduce our sales within our stores and clubs and materially adversely affect our financial performance.",
     "score": 0.4921,
     "subsection": "Strategic Risks"
    },
    {
     "source": "sec://0000104169-26-000055/1a#33",
     "title": "WMT FY2026 10-K · Item 1A",
     "content": "Certain segments of the retail industry are undergoing consolidation or substantially reducing operations, whether due to bankruptcy, economics or other factors. Such consolidation, or other business combinations or alliances, competitive omnichannel ecosystems or reductions in
operations may result in competitors with improved financial resources, improved access to merchandise, greater market penetration and other improvements in their competitive positions. Such business combinations or alliances could allow these companies to provide a wider variety of products and
services at competitive prices, which could adversely affect our financial performance.\n\nGeneral or macro-economic factors, both domestically and internationally, may materially adversely affect our financial performance.\n\nGeneral economic conditions and other economic factors, globally or in
one or more of the markets we serve, may adversely affect our financial performance. Higher interest rates, higher prices of petroleum products, including crude oil, natural gas, gasoline and diesel fuel, increased costs for electricity and other energy, weakness in the housing market, inflation,
deflation, increased costs of essential services, such as medical care and utilities, higher levels of unemployment, decreases in GDP and consumer purchasing power (including from reductions resulting from changes to government programs), unavailability of\n\n14\n\n\n\nconsumer credit, higher
consumer debt levels, changes in consumer spending and shopping patterns, fluctuations in currency exchange rates, higher tax rates, imposition of new taxes or other changes in tax laws, changes in healthcare laws, other regulatory changes, the imposition of export and import restrictions, tariffs,
trade barriers or other measures that create barriers to or increase the costs associated with international trade, overall economic slowdown or recession and other economic factors in the U.S., or in any of the other markets in which we operate, could adversely affect consumer demand for the
products and services we sell in the U.S. or such other markets, change the mix of products we sell to any one or more markets with a lower average gross margin, cause a slowdown in discretionary purchases of goods, adversely affect our net sales, growth rates, operating income and result in slower
inventory turnover and greater markdowns of inventory, or otherwise materially adversely affect our operations and operating results and could result in impairment charges to intangible assets, goodwill or other long-lived assets.\n\nIn addition, the economic factors listed above, any other economic
factors or circumstances resulting in higher transportation, labor, insurance or healthcare costs or commodity prices, including energy prices, and other economic factors in the U.S. and other countries in which we operate can increase our cost of sales and operating, selling, general and
administrative expenses and otherwise materially adversely affect our operations and operating results.",
     "score": 0.4887
    }
   ]
  },
  {
   "ticker": "WMT",
   "fiscal_year": 2026,
   "item": "Item 1",
   "prelude": "Excerpts from WMT FY2026 10-K, Item 1 (Business) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000104169-26-000055/1#16",
     "title": "WMT FY2026 10-K · Item 1",
     "content": "•Expanding our ecosystem and the products and services we offer in areas such as digital advertising, marketplace and fulfillment services, health and wellness, and financial services to provide our customers a broader set of offerings to meet expanding needs;\n\n•Opening new stores
and clubs, as well as remodeling existing locations, to enhance the customer experience, support omnichannel capabilities, and strengthen our physical footprint in existing and new markets; and\n\n•Investing in technology, automation, and our associates to deliver growth, expand operating margins
and improve returns.\n\nSeasonal Aspects of Operations. Our business is seasonal to a certain extent and varies by country due to different national and religious holidays, festivals and customs, as well as different weather patterns. Historically, our highest sales volume for each segment has
occurred in the fourth quarter of our fiscal year.\n\nSuppliers, Supply Chain and Distribution. As a retailer and warehouse club operator, we utilize a global supply chain that includes both U.S. and international suppliers from whom we purchase the merchandise that we sell in our stores, clubs and
online. In many instances, we purchase merchandise from producers located near the stores and clubs in which such merchandise will be sold, particularly perishable items. Consistent with applicable laws, we offer our suppliers the opportunity to efficiently sell significant quantities of their
products to us. These relationships enable us to obtain pricing that reflects the volume, certainty and cost-effectiveness these arrangements provide to such suppliers, which in turn enables us to provide low prices to our customers. Our suppliers are subject to standards of conduct, including
requirements that they comply with local labor laws, local worker safety laws and other applicable laws. Our ability to acquire from our suppliers the assortment and volume of products we wish to offer to our customers, to receive those products within the required time through our supply chain and
to distribute those products to our stores and clubs, determines, along with other supply chain logistics matters (such as containers or port access for example), in part, our in-stock levels in our stores and clubs and the attractiveness of our merchandise assortment we offer to our customers and
members.",
     "score": 0.4645
    }
   ]
  }
 ]
}

[tool 2] sec_filing_search {"query": "recession resilience consumer spending defensive demand value proposition traffic comparable sales franchise risks", "ticker": "MCD", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "MCD",
   "fiscal_year": 2025,
   "item": "_unknown",
   "prelude": "Excerpts from MCD FY2025 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000063908-26-000035/unknown#0",
     "title": "MCD FY2025 10-K",
     "content": "# Part I",
     "score": 0.0963
    },
    {
     "source": "sec://0000063908-26-000035/unknown#1",
     "title": "MCD FY2025 10-K",
     "content": "# Part II",
     "score": 0.0924
    },
    {
     "source": "sec://0000063908-26-000035/unknown#2",
     "title": "MCD FY2025 10-K",
     "content": "# Part III",
     "score": 0.089
    },
    {
     "source": "sec://0000063908-26-000035/unknown#3",
     "title": "MCD FY2025 10-K",
     "content": "# Part IV",
     "score": 0.0957
    },
    {
     "source": "sec://0000063908-26-000035/unknown#4",
     "title": "MCD FY2025 10-K",
     "content": "- Page reference\n- Item 1 Business Page [3](#i6d278eb3cca24d478428bd1e8807ef56_16)\n- Item 1A Risk Factors Page [27](#i6d278eb3cca24d478428bd1e8807ef56_58)\n- Item 1B Unresolved Staff Comments Not applicable\n- Item 1C Cybersecurity Page
[34](#i6d278eb3cca24d478428bd1e8807ef56_2510)\n- Item 2 Properties Page [36](#i6d278eb3cca24d478428bd1e8807ef56_64)\n- Item 3 Legal Proceedings Page [36](#i6d278eb3cca24d478428bd1e8807ef56_61)\n- Item 4 Mine Safety Disclosures Not applicable\n- Item 5 Market for Registrant’s Common Equity, Related
Stockholder Matters and Issuer Purchases of Equity Securities Page [26](#i6d278eb3cca24d478428bd1e8807ef56_55)\n- Item 6 [Reserved] Not applicable\n- Item 7 Management’s Discussion and Analysis of Financial Condition and Results of Operations Page [7](#i6d278eb3cca24d478428bd1e8807ef56_19)\n- Item
7A Quantitative and Qualitative Disclosures About Market Risk Page [22](#i6d278eb3cca24d478428bd1e8807ef56_40)\n- Item 8 Financial Statements and Supplementary Data Page [38](#i6d278eb3cca24d478428bd1e8807ef56_73)\n- Item 9 Changes in and Disagreements with Accountants on Accounting and Financial
Disclosure Not applicable\n- Item 9A Controls and Procedures Page [68](#i6d278eb3cca24d478428bd1e8807ef56_217)\n- Item 9B Other Information Page [69](#i6d278eb3cca24d478428bd1e8807ef56_2620)\n- Item 9C Disclosure Regarding Foreign Jurisdictions that Prevent Inspections Not applicable",
     "score": 0.3067
    },
    {
     "source": "sec://0000063908-26-000035/unknown#5",
     "title": "MCD FY2025 10-K",
     "content": "- Item 9C Disclosure Regarding Foreign Jurisdictions that Prevent Inspections Not applicable\n- Item 10 Directors, Executive Officers and Corporate Governance Page [37](#i6d278eb3cca24d478428bd1e8807ef56_67), (a)\n- Item 11 Executive Compensation (a)\n- Item 12 Security Ownership of
Certain Beneficial Owners and Management and Related Stockholder Matters Page [68](#i6d278eb3cca24d478428bd1e8807ef56_220), (a)\n- Item 13 Certain Relationships and Related Transactions, and Director Independence (a)\n- Item 14 Principal Accountant Fees and Services (a)\n- Item 15 Exhibits and
Financial Statement Schedules Page [70](#i6d278eb3cca24d478428bd1e8807ef56_223)\n- Item 16 Form 10-K Summary Not applicable\n- Signatures Page [73](#i6d278eb3cca24d478428bd1e8807ef56_229)",
     "score": 0.2209
    },
    {
     "source": "sec://0000063908-26-000035/unknown#6",
     "title": "MCD FY2025 10-K",
     "content": "(a) - The information required by this item is incorporated herein by reference from the Company's definitive proxy statement, which will be filed no later than 120 days after December 31, 2025.\n\n\n\nMcDonald's Corporation 2025 Annual Report 72\n\n\n\n\n\n|  |  |  |\n| --- | --- |
--- |\n| Signatures | | |\n|  | | |\n\nPursuant to the requirements of Section 13 or 15(d) of the Securities Exchange Act of 1934, the registrant has duly caused this report to be signed on its behalf by the undersigned, thereunto duly authorized.\n\nMcDonald’s Corporation\n\n(Registrant)\n\n|  |  |
|  |  |  |\n| --- | --- | --- | --- | --- | --- |\n| By | | | /s/ Ian F. Borden | | |\n|  | | | Ian F. Borden | | |\n|  | | | Executive Vice President and Global Chief Financial Officer | | |\n|  | | | | | |\n|  | | | February 24, 2026 | | |\n\n\nPursuant to the requirements of the Securities
Exchange Act of 1934, this report has been signed below by the following persons on behalf of the registrant and in the capacities indicated below on the 24th day of February, 2026:",
     "score": 0.2324
    },
    {
     "source": "sec://0000063908-26-000035/unknown#7",
     "title": "MCD FY2025 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| By | | | /s/ Ian F. Borden | | | By | | | /s/ Margaret H. Georgiadis | | |\n|  | | | Ian F. Borden | | |  | | | Margaret H. Georgiadis | | |\n|  | | | Executive Vice
President and Global Chief Financial Officer | | |  | | | Director | | |\n|  | | | (Principal Financial Officer) | | |  | | |  | | |\n|  | | |  | | |  | | |  | | |\n| By | | | /s/ Anthony G. Capuano | | | By | | | /s/ Michael D. Hsu | | |\n|  | | | Anthony G. Capuano | | |  | | | Michael D. Hsu | |
|\n|  | | | Director | | |  | | | Director | | |\n|  | | |  | | |  | | |  | | |\n| By | | | /s/ Kareem Daniel | | | By | | | /s/ Christopher J. Kempczinski | | |\n|  | | | Kareem Daniel | | |  | | | Christopher J. Kempczinski | | |\n|  | | | Director | | |  | | | Chairman of the Board of Directors,
President, and | | |\n|  | | |  | | |  | | | Chief Executive Officer | | |\n|  | | |  | | |  | | | (Principal Executive Officer) | | |\n|  | | |  | | |  | | |  | | |\n| By | | | /s/ Lloyd H. Dean | | | By | | | /s/ Jennifer L. Taubert | | |\n|  | | | Lloyd H. Dean | | |  | | | Jennifer L. Taubert |
| |\n|  | | | Director | | |  | | | Director | | |\n|  | | |  | | |  | | |  | | |",
     "score": 0.1933
    },
    {
     "source": "sec://0000063908-26-000035/unknown#8",
     "title": "MCD FY2025 10-K",
     "content": "|  | | | Director | | |  | | | Director | | |\n|  | | |  | | |  | | |  | | |\n| By | | | /s/ Lauren B. Elting | | | By | | | /s/ Paul S. Walsh | | |\n|  | | | Lauren B. Elting | | |  | | | Paul S. Walsh | | |\n|  | | | Vice President - Chief Accounting Officer and | | |  | | |
Director | | |\n|  | | | Corporate Controller | | |  | | |  | | |\n|  | | | (Principal Accounting Officer) | | |  | | |  | | |\n|  | | |  | | |  | | |  | | |\n| By | | | /s/ Catherine M. Engelbert | | | By | | | /s/ Amy E. Weaver | | |\n|  | | | Catherine M. Engelbert | | |  | | | Amy E. Weaver | |
|\n|  | | | Director | | |  | | | Director | | |\n|  | | |  | | |  | | |  | | |\n| By | | | /s/ James D. Farley, Jr. | | | By | | | /s/ Miles D. White | | |\n|  | | | James D. Farley, Jr. | | |  | | | Miles D. White | | |\n|  | | | Director | | |  | | | Director | | |\n|  | | |  | | |  | | |  | |
|",
     "score": 0.1397
    },
    {
     "source": "sec://0000063908-26-000035/unknown#9",
     "title": "MCD FY2025 10-K",
     "content": "McDonald's Corporation 2025 Annual Report 73",
     "score": 0.3911
    }
   ]
  }
 ]
}

[tool 3] finnhub_company_basic_financials {"ticker": "WMT"}
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

[tool 4] finnhub_company_basic_financials {"ticker": "MCD"}
{
 "ticker": "MCD",
 "fiftyTwoWeekHigh": 341.75,
 "fiftyTwoWeekLow": 229.2,
 "peTTM": 20.1653,
 "forwardPE": 18.33299,
 "psTTM": 6.3954,
 "pb": 160.4594,
 "marketCap": 177172.2,
 "enterpriseValue": 216213.2,
 "beta": 0.44770226,
 "epsTTM": 12.3123,
 "roeTTM": 95.13000000000001,
 "roaTTM": 14.64,
 "grossMarginTTM": 57.38,
 "netProfitMarginTTM": 31.71,
 "operatingMarginTTM": 46.22,
 "currentRatio": 1.0814,
 "quickRatio": 0.823,
 "debtToEquity": 40.6406,
 "dividendYield": 2.36427,
 "revenueGrowthTTMYoy": 6.3,
 "epsGrowthTTMYoy": 5.44,
 "tenDayAvgVolume": 5.27351
}

[tool 5] finnhub_company_basic_financials {"ticker": "COST"}
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
----- END EVIDENCE F0004 -----

----- BEGIN ANSWER F0004 -----
**結論：若只是「輕度衰退」，我會把相對韌性排序為：沃爾瑪（WMT）≈ 好市多（COST）＞ 麥當勞（MCD）。**  
若必須選一檔作為最防禦性的核心持股，我偏向 **沃爾瑪**；若重視會員黏著度與長期成長，則 **好市多可能更強**，但估值風險也明顯較高。

### 1. 沃爾瑪：最直接受惠於消費降級

沃爾瑪的商品組合包含大量食品、日用品與必需品；經濟轉弱時，消費者可能從較昂貴的通路轉向低價零售商。公司也明確表示，會透過低價、開放價位、私有品牌與小包裝等策略應對成本上升與消費者壓力。FY2026 10-K 顯示，總營收仍年增 4.7%，美國 Sam’s Club 可比銷售也增長 2.9%。[1][2]

**優點：**
- 必需品占比高，需求相對穩定；
- 能吸收或部分轉嫁成本；
- 規模、供應鏈與全通路能力強；
- 輕度衰退時容易吸收從超市、百貨與較高價通路轉來的客流。

**缺點：**
- 利潤率很薄，成本、關稅與勞動力壓力可能侵蝕獲利；
- Finnhub 數據顯示其本益比約 **43 倍**，防禦性雖高，但股價並不便宜；
- 公司也警告，衰退可能導致消費組合轉向低毛利商品。[3]

### 2. 好市多：會員模式提供很強的收入黏性

好市多的核心優勢是會員制。FY2026 10-K 顯示，美國與加拿大續卡率為 **92.3%**，全球續卡率為 **89.8%**；會員費收入年增 11%，可比銷售增長 8%，其中平均客單價增 5%、購物頻率增 3%。[4]

這代表在輕度衰退中，會員可能更願意集中採購、購買 Kirkland 私有品牌，並利用好市多的價格優勢。公司也表示，過去能透過調整價格、商品組合與增加私有品牌滲透率來適應經濟環境變化。[5]

**優點：**
- 高續卡率與會員費收入形成穩定性；
- 大包裝、低單位價格與 Kirkland 品牌符合消費者節省支出的需求；
- 會員黏著度與購物頻率可能在衰退中提升。

**缺點：**
- 估值是三者中最昂貴之一：Finnhub 顯示本益比約 **48 倍**；
- 公司本身指出，會員成長、續卡率與品牌信任對獲利非常關鍵；若消費者開始取消非必要會員，影響可能被放大；
- 低毛利模式對商品成本與營運費用相當敏感。[6]

因此，**營運韌性可能接近甚至略勝沃爾瑪，但股票價格的安全邊際較低**。

### 3. 麥當勞：有「消費降級」優勢，但更依賴可選消費

麥當勞也可能受惠於消費者從高價餐廳轉向平價外食。不過，相較沃爾瑪與好市多，餐飲仍屬於可延後或替代的消費；在輕度衰退中，消費者可能減少外食、改在家用餐。

Finnhub 數據顯示，麥當勞的本益比約 **20 倍**、股息率約 **2.36%**，估值與股息吸引力明顯優於沃爾瑪和好市多；但其負債權益比約 **40.6**，遠高於沃爾瑪約 **0.58** 與好市多約 **0.17**。這使它在利率、加盟商財務狀況或銷售疲弱時，財務風險相對更值得注意。這些 Finnhub 指標沒有直接證明衰退期間的營收表現，因此只能作為財務結構與估值的補充，而非衰退預測。[7]

**優點：**
- 價格低於完整餐飲，可能吸收部分消費降級需求；
- 加盟模式帶來高營業利潤率與現金流特性；
- 估值與股息相對合理。

**缺點：**
- 外食仍是可削減支出；
- 食品、工資與加盟商成本壓力可能影響菜單價格與客流；
- 高槓桿使其對利率與營運下滑更敏感。

### 我的簡化判斷

| 公司 | 輕度衰退營運韌性 | 估值安全邊際 | 主要理由 |
|---|---:|---:|---|
| 沃爾瑪 | **最高或並列最高** | 中等偏低 | 必需品、低價定位、可能吸收消費降級 |
| 好市多 | **非常高** | **最低** | 高續卡率、會員黏性、私有品牌與低價 |
| 麥當勞 | 中等 | **相對較高** | 平價外食受惠，但仍屬可選消費且槓桿高 |

**最終排序：**
1. **沃爾瑪：最穩健的衰退防禦選擇**
2. **好市多：營運品質可能最佳，但估值風險最高**
3. **麥當勞：估值與股息較有吸引力，但衰退防禦性略遜**

需要注意的是，沃爾瑪與好市多使用的最新 10-K 分別是 **FY2026、截至 2026-01-31 與 2026-08-30**；麥當勞檢索到的是 **FY2025、截至 2025-12-31**，年度並不完全一致，因此三者的營運數據不能視為同一時點的嚴格比較。

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt  
[5]: SEC 10-K excerpt  
[6]: SEC 10-K excerpt  
[7]: SEC 10-K excerpt
----- END ANSWER F0004 -----

===== ITEM F0005 =====

QUESTION:
大家都說摩根大通是大型銀行裡比較穩的那家，這說法現在還站得住嗎？

----- BEGIN EVIDENCE F0005 -----
[tool 0] sec_filing_search {"query": "capital adequacy liquidity risk deposits funding unrealized losses commercial real estate risk stress testing", "ticker": "JPM", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "JPM",
   "fiscal_year": 2025,
   "item": "_unknown",
   "prelude": "Excerpts from JPM FY2025 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-008131/unknown#248",
     "title": "JPM FY2025 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| CAPITAL RISK MANAGEMENT | | | | | | | | | | | | | | |\n\nCapital risk is the risk that the Firm has an insufficient level or composition of
capital to support the Firm’s business activities and associated risks during normal economic environments and under stressed conditions.\n\nA strong capital position is essential to the Firm’s business strategy and competitive position. Maintaining a strong balance sheet to manage through economic
volatility is a strategic imperative of the Firm’s Board of Directors, CEO and Operating Committee. The Firm’s “fortress balance sheet” philosophy focuses on risk-adjusted returns, strong capital and robust liquidity. The Firm’s capital risk management strategy focuses on maintaining long-term
stability to enable the Firm to build and invest in market-leading businesses, including in highly stressed environments. Senior management considers the implications on the Firm’s capital prior to making significant decisions that could impact future business activities. In addition to considering
the Firm’s earnings outlook, senior management evaluates all sources and uses of capital with a view to ensuring the Firm’s capital strength.",
     "score": 0.5354
    },
    {
     "source": "sec://0001628280-26-008131/unknown#252",
     "title": "JPM FY2025 10-K",
     "content": "##### Capital planning and stress testing\n\nComprehensive Capital Analysis and Review\n\nThe Federal Reserve requires the Firm, as a large Bank Holding Company (“BHC”), to submit at least annually a capital plan that has been reviewed and approved by the Board of Directors. The
Federal Reserve uses Comprehensive Capital Analysis and Review (“CCAR”) and other stress testing processes to assess whether large BHCs, such as the Firm, have sufficient capital during periods of economic and financial stress, and have robust, forward-looking capital assessment and planning
processes in place that address each BHC’s unique risks to enable it to absorb losses under certain stress scenarios. Through CCAR, the Federal Reserve evaluates each BHC’s capital adequacy and internal capital adequacy assessment processes (“ICAAP”), as well as its plans to make capital
distributions, such as dividend payments or stock repurchases. The Federal\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| JPMorgan Chase & Co./2025 Form 10-K | | |  | | | 89 | | |\n\n\nManagement’s discussion and analysis\n\nReserve uses results under the
severely adverse scenario from its supervisory stress test to determine each firm’s Stress Capital Buffer (“SCB”) requirement for the coming year.\n\nThe Firm's current SCB requirement is 2.5% and will remain in effect through September 30, 2027, based on the current rules. The Firm’s Standardized
CET1 capital ratio requirement, including regulatory buffers, was 11.5% as of December 31, 2025. Refer to Key Regulatory Developments on page 91 for information related to proposed changes to the SCB requirement and stress testing framework.\n\nRefer to Capital actions on page 97 for information on
actions taken by the Firm’s Board of Directors.\n\nInternal Capital Adequacy Assessment Process\n\nAnnually, the Firm prepares the ICAAP, which informs the Board of Directors of the ongoing assessment of the Firm’s processes for managing the sources and uses of capital as well as compliance with
supervisory expectations for capital planning and capital adequacy. The Firm’s ICAAP integrates stress testing protocols with capital planning. The Firm’s Audit Committee is responsible for reviewing and approving the capital planning framework.",
     "score": 0.5476
    },
    {
     "source": "sec://0001628280-26-008131/unknown#253",
     "title": "JPM FY2025 10-K",
     "content": "Stress testing assesses the potential impact of alternative economic and business scenarios on the Firm’s earnings and capital. Economic scenarios, and the parameters underlying those scenarios, are defined centrally and applied uniformly across the businesses. These scenarios are
articulated in terms of macroeconomic factors, which are key drivers of business results; global market shocks, which generate short-term but severe trading losses; and idiosyncratic operational risk events. The scenarios are intended to capture and stress key vulnerabilities and idiosyncratic risks
facing the Firm. In addition to CCAR and other periodic stress testing, management also considers tailored stress scenarios and sensitivity analyses, as necessary.",
     "score": 0.5352
    },
    {
     "source": "sec://0001628280-26-008131/unknown#296",
     "title": "JPM FY2025 10-K",
     "content": "##### Internal stress testing\n\nThe Firm conducts internal liquidity stress testing to identify liquidity risks and monitor liquidity positions at the Firm and its material legal entities under a variety of adverse scenarios, including scenarios analyzed as part of the Firm’s
resolution and recovery planning. Internal stress tests are produced on a daily basis, and other stress tests are performed in response to specific market events or concerns. Liquidity stress tests assume all of the Firm’s contractual financial obligations are met and take into
consideration:\n\n•Varying levels of access to unsecured and secured funding markets;\n\n•Estimated non-contractual and contingent cash outflows;\n\n•Credit rating downgrades;\n\n•Collateral haircuts; and\n\n•Potential impediments to the availability and transferability of liquidity between
jurisdictions and material legal entities such as regulatory, legal or other restrictions.\n\nLiquidity outflows are modeled across a range of time horizons and currency dimensions and contemplate both market and idiosyncratic stresses.\n\nResults of stress tests are considered in the formulation of
the Firm’s funding plan and assessment of its liquidity position. The Parent Company acts as a source of funding for the Firm through equity and\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 100 | | |  | | | JPMorgan Chase & Co./2025 Form 10-K | |
|\n\n\n\nlong-term debt issuances, and its intermediate holding company, JPMorgan Chase Holdings LLC (the “IHC”), provides funding to support the ongoing operations of the Parent Company and its subsidiaries. The Firm manages liquidity at the Parent Company, the IHC, and operating subsidiaries at
levels sufficient to comply with liquidity risk tolerances and minimum liquidity requirements, and to manage through periods of stress when access to normal funding sources may be disrupted.",
     "score": 0.5431
    },
    {
     "source": "sec://0001628280-26-008131/unknown#330",
     "title": "JPM FY2025 10-K",
     "content": "##### Stress testing\n\nStress testing is important in assessing, measuring and monitoring credit risk in the Firm’s credit portfolio. The stress testing process assesses the potential impact of alternative economic and business scenarios on estimated credit losses for the Firm.
Economic scenarios and the underlying parameters are defined centrally, articulated in terms of macroeconomic factors and applied across the businesses. The stress test results may indicate credit migration, changes in delinquency trends and potential losses in the credit portfolio. In addition to
the periodic stress testing processes, management also considers additional stresses outside these scenarios, including industry and country- specific stress scenarios, as appropriate. The Firm uses stress testing to inform decisions on setting risk appetite both at a Firm and LOB level, as well as
to assess the impact of stress on individual counterparties.\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| JPMorgan Chase & Co./2025 Form 10-K | | |  | | | 109 | | |\n\n\nManagement’s discussion and analysis",
     "score": 0.5511
    },
    {
     "source": "sec://0001628280-26-008131/unknown#411",
     "title": "JPM FY2025 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| LOBs and Corporate | | | Predominant business activities | | | Related market risks | | | Positions included in
Risk Management VaR | | | Positions included in earnings-at-risk | | | Positions included in other sensitivity-based measures | | |\n| CCB | | | •Originates and services mortgage loans  •Originates loans and takes deposits | | | •Risk from changes in the probability of newly originated mortgage
commitments closing  •Interest rate risk and prepayment risk | | | •Mortgage commitments, classified as derivatives  •Warehouse loans that are fair value option elected, classified as loans – debt instruments  •MSRs  •Hedges of mortgage commitments, warehouse loans and MSRs, classified as
derivatives  •Interest-only and mortgage-backed securities, classified as trading assets-debt instruments, and related hedges, classified as derivatives  •Fair value option elected liabilities(a) | | | •Retained and held-for-sale loan portfolios  •Deposits | | | •Fair value option elected
liabilities DVA(a) | | |",
     "score": 0.5379
    },
    {
     "source": "sec://0001628280-26-008131/unknown#413",
     "title": "JPM FY2025 10-K",
     "content": "| Corporate | | | •Manages the Firm’s liquidity, funding, capital, structural interest rate and foreign exchange risks | | | •Structural interest rate risk from the Firm’s traditional banking activities  •Structural non-USD foreign exchange risks | | | •Derivative positions measured
through noninterest revenue in earnings  •Marketable equity investments | | | •Deposits with banks and financing activities  •Investment securities portfolio and related interest rate hedges  •Cash flow hedges on retained loan portfolios in the LOBs  •Long-term and short-term funding and related
interest rate hedges  •Deposits  •Foreign exchange hedges of non-U.S. dollar capital investments | | | •Privately held equity and other investments measured at fair value  •Foreign exchange exposure related to Firm-issued non-USD long-term debt (“LTD”) and related hedges | | |",
     "score": 0.5594
    },
    {
     "source": "sec://0001628280-26-008131/unknown#429",
     "title": "JPM FY2025 10-K",
     "content": "##### Stress testing\n\nAlong with VaR, stress testing is an important tool used to assess risk. While VaR reflects the risk of loss due to adverse changes in markets using recent historical market behavior, stress testing reflects the risk of loss from hypothetical changes in the
value of market risk sensitive positions applied simultaneously. Stress testing measures the Firm’s vulnerability to losses under a range of stressed but possible economic and market scenarios. The results are used to understand the exposures responsible for those potential losses and are measured
against limits.\n\nThe Firm’s stress framework covers market risk sensitive positions in the LOBs and Corporate. The framework is used to calculate multiple magnitudes of potential stress for both market rallies and market sell-offs, assuming significant changes in market factors such as credit
spreads, equity prices, interest rates, currency rates and commodity prices, and combines them in multiple ways to capture an array of hypothetical economic and market scenarios.\n\nThe Firm generates a number of scenarios that focus on tail events in specific asset classes and geographies,
including how the event may impact multiple market factors simultaneously. Scenarios also incorporate specific idiosyncratic risks and stress basis risk between different products. The flexibility in the stress framework allows the Firm to construct new scenarios that can test the outcomes against
possible future stress events. Stress testing results are reported periodically to senior management of the Firm, as appropriate.\n\nStress methodologies are governed by the overall stress framework, under the oversight of Market Risk Management. The Firmwide Market Risk Stress Methodology Committee
reviews and approves changes to stress testing methodology and scenarios across the Firm. Significant changes to the framework are escalated to senior management, as appropriate. In addition, stress methodology and the models to calculate the stress results are subject to the Firm’s Estimations and
Model Risk Management Policy\n\nThe Firm’s stress testing framework is utilized in calculating the Firm’s CCAR and other stress test results, which are reported periodically to the Board of Directors. In addition, stress testing results are incorporated into the Firm’s Risk Appetite framework, and
are reported periodically to the Board Risk Committee.",
     "score": 0.5625
    },
    {
     "source": "sec://0001628280-26-008131/unknown#447",
     "title": "JPM FY2025 10-K",
     "content": "##### Stress testing\n\nStress testing is an important component of the Firm’s country risk management framework, which aims to estimate and limit losses arising from a country crisis by measuring the impact of adverse asset price movements to a country based on market shocks
combined with counterparty specific assumptions. Country Risk Management periodically designs and runs tailored stress scenarios to test vulnerabilities to individual countries or sets of countries in response to specific or potential market events, sector performance concerns, sovereign actions and
geopolitical risks. These tailored stress results are used to inform potential risk reduction across the Firm, as necessary.",
     "score": 0.5577
    },
    {
     "source": "sec://0001628280-26-008131/unknown#456",
     "title": "JPM FY2025 10-K",
     "content": "In addition, Operational Risk and Compliance assesses operational risks through quantitative means, including operational risk-based capital and estimation of operational risk losses under both baseline and stressed conditions.\n\nThe primary component of the operational risk-based
capital estimate is the Loss Distribution Approach (“LDA”) statistical model, which simulates the projected frequency and severity of operational risk losses based on historical data. The LDA model is used to estimate an aggregate operational risk loss over a one-year time horizon, at a 99.9%
confidence level. The LDA model incorporates actual internal operational risk losses in the quarter following the period in which those losses were realized, and the calculation generally continues to reflect such losses even after the issues or business activities giving rise to the losses have
been remediated or reduced.\n\nAs required under the Basel III capital framework, the Firm’s operational risk capital methodology, which uses the Advanced Measurement Approach (“AMA”), incorporates internal and external losses as well as management’s view of tail risk captured through operational
risk scenario analysis, and evaluation of key business environment and internal control metrics. The Firm does not reflect the impact of insurance in its AMA estimate of operational risk capital.\n\nThe Firm considers the impact of stressed economic conditions on operational risk losses and develops
a forward looking view of material operational risk events that may occur in a stressed environment. The Firm’s operational risk stress testing framework is utilized in calculating results for the Firm’s CCAR and other stress testing processes.\n\nRefer to Capital Risk Management on pages 89–99 for
information related to operational risk RWA, and CCAR.\n\nOperational Risk Monitoring and Testing\n\nIndependent testing and monitoring of controls are integral components of the CCOR Management Framework. These testing and monitoring activities are\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | ---
| --- | --- | --- | --- | --- | --- |\n| 146 | | |  | | | JPMorgan Chase & Co./2025 Form 10-K | | |\n\n\n\nconducted under the CCOR organization’s Monitoring and Testing Program (“M&T Program”) and:\n\n•are based upon the Firm’s compliance, conduct and operational risk assessments;\n\n•are designed
to identify control gaps or deficiencies, including potential non-compliance with applicable laws, rules and regulations; and\n\n•assess whether the procedures, processes and controls used by the Firm to mitigate compliance, conduct and operational risk are well-designed and functioning as
intended.",
     "score": 0.5371
    }
   ]
  }
 ]
}

[tool 1] finnhub_stock_quote {"ticker": "JPM"}
{
 "ticker": "JPM",
 "currentPrice": 336.21,
 "open": 336.365,
 "previousClose": 334.04,
 "change": 2.17,
 "percentChange": 0.6496,
 "dayHigh": 337.51,
 "dayLow": 334.5
}

[tool 2] finnhub_company_basic_financials {"ticker": "BAC"}
{
 "ticker": "BAC",
 "fiftyTwoWeekHigh": 65.225,
 "fiftyTwoWeekLow": 46.12,
 "peTTM": 10.9846,
 "forwardPE": 10.98968,
 "psTTM": 2.32875,
 "pb": 1.2698,
 "marketCap": 352815.2,
 "enterpriseValue": 1049150.2,
 "beta": 1.2105174,
 "epsTTM": 4.3585,
 "roeTTM": 10.69,
 "roaTTM": 0.9299999999999999,
 "netProfitMarginTTM": 30.15501,
 "operatingMarginTTM": 32.73721,
 "debtToEquity": 2.3465,
 "dividendYield": 3.22906,
 "revenueGrowthTTMYoy": 99.36713,
 "epsGrowthTTMYoy": 14.53,
 "tenDayAvgVolume": 48.37076
}

[tool 3] finnhub_company_basic_financials {"ticker": "JPM"}
{
 "ticker": "JPM",
 "fiftyTwoWeekHigh": 366.5,
 "fiftyTwoWeekLow": 279.1,
 "peTTM": 13.4922,
 "forwardPE": 13.57398,
 "psTTM": 2.89596,
 "pb": 2.3617,
 "marketCap": 890199.94,
 "enterpriseValue": 2125090.94,
 "beta": 1.0379301,
 "epsTTM": 24.373,
 "roeTTM": 17.91,
 "roaTTM": 1.3599999999999999,
 "netProfitMarginTTM": 33.26454,
 "operatingMarginTTM": 41.22809,
 "debtToEquity": 3.3163,
 "dividendYield": 2.73544,
 "revenueGrowthTTMYoy": 108.9793,
 "epsGrowthTTMYoy": 17.88,
 "tenDayAvgVolume": 7.66413
}

[tool 4] tavily_financial_search {"query": "JPMorgan Chase recent capital liquidity balance sheet stress tests risks 2025 2026", "ticker": "JPM"}
{
 "query": "JPM JPMorgan Chase recent capital liquidity balance sheet stress tests risks 2025 2026",
 "results": [
  {
   "title": "424B4",
   "url": "https://links.message.bloomberg.com/s/c/4_ylfM5-102V3xd1NYV-KGoc3OJc23GsvCS_9xCIAfcU_TLWJd4K6G-yDgEV7cPp6RweE83CAeepqp5YNN1E5agmIxVs4e9QyOsDznPPry8b9byJ3CIoqabkg26b0zqaqh5S77-oDbI45dHhDKYdx1JbmVWtwBlAwQpC6uceD48il_5pIoNNIDnd1V3bMHBoqgYwvePKU96s-Gcn8jSFScCrR1Ol9dm1Kr-
CBd7RrZVnYcpWCHiKsT7SUmOam-DUevVUbvvWiYEuk8obD2ZfAX6fYymJRnAAGqaWNS56Zf5pn_75ZD4qdem7E9ssoiMsKQY_UNL3ZVDx9Y9HTpx5ZX_tQi2tM61fO83Djme_ag5v28qu6d5QxAaNXX0/ezHH20sb5S9JubeZP-sWSChWks2EYM23/20",
   "content": "no other financial covenants) requiring the 2026 Note Issuers to maintain no less than $1.0 billion of liquidity, which liquidity covenant will fall away upon meeting a fixed charge coverage ratio of greater than 1.0 to 1.0 for two consecutive fiscal quarters. [...] the ABL Facility
(refer to Note 6 “Debt”) and a minimum liquidity covenant. The 2026 Notes are secured by a second priority security interest in the same assets in which the ABL Facility has a first priority security interest and are guaranteed by certain subsidiaries of the Company. [...] 41\n\nOur business,
prospects, financial condition, results of operations, and cash flows may be materially and adversely affected by the risks related to health epidemics, including the recent COVID-19 pandemic.",
   "published_date": null
  },
  {
   "title": "GE Whistleblower Report",
   "url": "https://fm.cnbc.com/applications/cnbc.com/resources/editorialfiles/2019/8/15/2019_08_15_GE_Whistleblower_Report.pdf",
   "content": "And the stock has reacted pretty well to what you had to say, even though you said you may lose some money in terms of cashflow. Do you anticipate a debt review? Are you worried about the debt-rating situation because there were some of those ratings that were based on some
assumptions that don’t seem to be right anymore. Read: GE jet leasing unit’s portfolio churn makes JPMorgan wary A: It seems like investors understand that the deleveraging plan we have in place both for the industrial [...] cash flow impact was already recognized in $15 billion SAP reserve
adjustment 86 GE’s Capital Contributions to GE-ERAC 2018 2019 2020 2021 2022 2023 2024 2025 2026 2027 Total Prior Reserve Adjustment - 2018 ($3,400) ($1,900 ($1,940) ($1,940) ($1,940) ($1,940) ($1,940) ($15,000) New Reserve Adjustment - 2019 ($3,400) ($2,467) ($2,467) ($2,467) ($2,467) ($2,467)
($2,467) ($18,500) Total ($3,400) ($1,900) ($1,940) ($5,340) ($4,407) ($4,407) ($4,407) ($2,467) ($2,467) ($2,467) ($33,500) Best Case: [...] GE’s 14.7% Profit Margins Were Real: Where’s the cash? $29.0 billion Long Term Care liabilities would be fully reserved $27.2 billion pension shortfall would
be fully funded GE wouldn’t have a BBB+ credit rating and be on credit watch GE dividends would be a lot higher than a penny per share GE shares would be trading at prices a lot higher than a shoe size 1 2 3 4 5 6 Conclusion: By Failing All of the Above Tests, the Reported Profit Margins Are Not
True 17 Reasons for the Disconnect Between",
   "published_date": null
  },
  {
   "title": "Jamie Dimon’s Doubts on the Credit Market Are Well Founded - Bloomberg",
   "url": "https://www.bloomberg.com/news/articles/2026-02-24/dimon-s-doubts-on-credit-market-are-well-founded-macroscope-mm0m64mk",
   "content": "MacroScope\n\n# Why Jamie Dimon’s Doubts on the Credit Market Are Well Founded\n\n## Takeaways by Bloomberg AI\n\nCorporate bonds are exposed to abrupt downside as liquidity providers are increasingly replaced by liquidity takers.\n\nJPMorgan Chase and Co.’s Jamie Dimon has warned of
parallels to the era prior to the 2008 financial crisis. He’s not wrong to be concerned, as we will see, but you wouldn’t know it from looking at credit spreads, which are back near historic lows.",
   "published_date": null
  },
  {
   "title": "Credit Fund Stress Rises as PIK Loans Swell - Bloomberg",
   "url": "https://www.bloomberg.com/news/newsletters/2026-06-26/credit-fund-stress-rises-as-pik-loans-swell",
   "content": "# Private Credit Fund Stress Rises as PIK Loans Swell [...] Exit caps are in place and cash is seeping back to fleeing investors. Though it may seem like non-traded business development companies have weathered this year’s redemption rout, bigger crises may be brewing. [...] direct
lending funds. If you’re not already on our list, sign up here. Have feedback? Email us at goingprivate@bloomberg.net",
   "published_date": null
  },
  {
   "title": "Wall Street Traders Smash Records as AI Threat From Mythos Takes Spotlight - Bloomberg",
   "url": "https://www.bloomberg.com/news/newsletters/2026-04-16/wall-street-traders-smash-records-as-ai-threat-from-mythos-takes-spotlight",
   "content": "This was a curious earnings week, where Wall Street banks like JPMorgan Chase and Goldman Sachs Group could utterly smash their own trading records and still not entirely thrill investors. Wells Fargo gave its shareholders little to be thrilled about, and they reacted accordingly.
Let’s skip a line-by-line, bank-by-bank rundown and concentrate on the broad themes that emerged. [...] Speaking of AI wipeouts, bankers and regulators are sifting through Anthropic’s Mythos to see if its ability to find flaws in security systems could trigger some kind of financial crisis for
banks. How real is the danger? Will Mythos render a “fortress balance sheet” into something more like a lightly defended foxhole? Bloomberg is hosting a Live Q&A on Friday, April 17 on the Mythos threat, featuring real humans. Bloomberg’s Edward Ludlow leads a conversation with reporters Shirin
Ghaffary, [...] Trading overall was strong with new records set amid war and volatility, but you can’t please everyone: some banks fell short on FICC, accounting for part of the investor disappointment. Notably, the Iran war upended the rates trading desk at Goldman Sach Group. Private credit was
top of mind, and bankers were optimistic about its prospects, especially in their own portfolios. If there’s a systemic threat, they mostly don’t see it. In spite of the good numbers, headcount fell, due mainly to",
   "published_date": null
  }
 ]
}

[tool 5] sec_filing_search {"query": "CET1 ratio actual December 31 2025 total assets deposits net charge-offs provision credit losses liquidity", "ticker": "JPM", "fiscal_year": 2025}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "requested",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "JPM",
   "fiscal_year": 2025,
   "item": "_unknown",
   "prelude": "Excerpts from JPM FY2025 10-K, _unknown — 10 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001628280-26-008131/unknown#92",
     "title": "JPM FY2025 10-K",
     "content": "- As of or for the year ended December 31,(in millions, except per share, ratio, employee data and where otherwise noted)\n- 2025 2024 2023\n- Selected income statement data\n- Total net revenue $ 182,447 $ 177,556 (g) $ 158,104\n- Total noninterest expense 95,640 91,797 (g)
87,172\n- Pre-provision profit(a) 86,807 85,759 70,932\n- Provision for credit losses 14,212 (e) 10,678 9,320\n- Income before income tax expense 72,595 75,081 61,612\n- Income tax expense 15,547 16,610 12,060\n- Net income $ 57,048 $ 58,471 $ 49,552\n- Earnings per share data\n- Net income: Basic $
20.05 $ 19.79 $ 16.25\n- Diluted 20.02 19.75 16.23\n- Average shares: Basic 2,776.5 2,873.9 2,938.6\n- Diluted 2,781.5 2,879.0 2,943.1\n- Market and per common share data\n- Market capitalization 868,793 670,618 489,320\n- Common shares at period-end 2,696.2 2,797.6 2,876.6\n- Book value per share
126.99 116.07 104.45\n- Tangible book value per share (“TBVPS”)(a) 107.56 97.30 86.08\n- Cash dividends declared per share 5.80 4.80 4.10\n- Selected ratios and metrics\n- Return on common equity (“ROE”) 17 % 18 % 17 %\n- Return on tangible common equity (“ROTCE”)(a) 20 22 21\n- Return on assets
(“ROA”) 1.29 1.43 1.30\n- Overhead ratio 52 52 55\n- Loans-to-deposits ratio 58 56 55\n- Firm Liquidity coverage ratio (“LCR”) (average)(b) 111 113 113",
     "score": 0.591
    },
    {
     "source": "sec://0001628280-26-008131/unknown#122",
     "title": "JPM FY2025 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| Selected Consolidated balance sheets data | | | | | | | | | | | |  | | |\n| December 31, (in millions) | | | 2025 | | |  | | | 2024 | | |
Change | | |\n| Assets | | |  | | |  | | |  | | |  | | |\n| Cash and due from banks | | | $ | 21,742 |  |  | | | $ | 23,372 |  | (7) | | % |\n| Deposits with banks | | | 321,596 | |  |  | | | 445,945 | |  | (28) | |  |\n| Federal funds sold and securities purchased under resale agreements | | |
336,426 | |  |  | | | 295,001 | |  | 14 | |  |\n| Securities borrowed | | | 286,191 | |  |  | | | 219,546 | |  | 30 | |  |\n| Trading assets | | | 802,873 | |  |  | | | 637,784 | |  | 26 | |  |\n| Available-for-sale securities | | | 507,198 | |  |  | | | 406,852 | |  | 25 | |  |\n| Held-to-maturity
securities | | | 270,134 | |  |  | | | 274,468 | |  | (2) | |  |\n| Investment securities, net of allowance for credit losses | | | 777,332 | |  |  | | | 681,320 | |  | 14 | |  |\n| Loans | | | 1,493,429 | |  |  | | | 1,347,988 | |  | 11 | |  |\n| Allowance for loan losses | | | (25,765) | |  |  | |
| (24,345) | |  | 6 | |  |",
     "score": 0.5916
    },
    {
     "source": "sec://0001628280-26-008131/unknown#188",
     "title": "JPM FY2025 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| Selected metrics | | |  | | |  | | |  | | |  | | |  | | |\n| As of or for the year ended    December 31, (in
millions, except ratios) | | | 2025 | | |  | | | 2024 | | |  | | | 2023 | | |\n| Credit data and quality statistics | | |  | | |  | | |  | | |  | | |  | | |\n| Net charge-offs/(recoveries) | | | $ | 1,509 |  |  | | | $ | 689 |  | (d) | | | $ | 588 |  |\n| Nonperforming assets: | | |  | | |  | | |  |
| |  | | |  | | |\n| Nonaccrual loans: | | |  | | |  | | |  | | |  | | |  | | |\n| Nonaccrual loans retained(a) | | | $ | 3,641 |  |  | | | $ | 3,258 |  |  | | | $ | 1,675 |  |\n| Nonaccrual loans held-for-sale and loans at fair value(b) | | | 1,518 | |  |  | | | 1,502 | |  |  | | | 828 | |  |\n|
Total nonaccrual loans | | | 5,159 | |  |  | | | 4,760 | |  |  | | | 2,503 | |  |\n| Derivative receivables | | | 204 | |  |  | | | 145 | |  |  | | | 364 | |  |\n| Assets acquired in loan satisfactions | | | 192 | |  |  | | | 213 | |  |  | | | 169 | |  |",
     "score": 0.5933
    },
    {
     "source": "sec://0001628280-26-008131/unknown#266",
     "title": "JPM FY2025 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | Standardized | | | | | | | | | | | | | | |  | | | Advanced | | | | | | | | | | | | | | |\n| (in millions, except ratios) | | | December 31, 2025 | | |  | | | December 31, 2024 | | |  | | | Capital ratio requirements(d) | | |  | | | December
31, 2025 | | |  | | | December 31, 2024 | | |  | | | Capital ratio requirements(d) | | |\n| Risk-based capital metrics:(a) | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |  | | |\n| CET1 capital | | | $ | 288,469 |  |  | | | $ | 275,513 |  |  | | |  | | |  | | | $ |
288,469 |  |  | | | $ | 275,513 |  |  | | |  | | |\n| Tier 1 capital | | | 307,630 | |  |  | | | 294,881 | |  |  | | |  | | |  | | | 307,630 | |  |  | | | 294,881 | |  |  | | |  | | |",
     "score": 0.6485
    },
    {
     "source": "sec://0001628280-26-008131/unknown#267",
     "title": "JPM FY2025 10-K",
     "content": "| Total capital | | | 343,843 | |  |  | | | 325,589 | |  |  | | |  | | |  | | | 328,962 | |  | (e) | | | 311,898 | |  | (e) | | |  | | |\n| Risk-weighted assets | | | 1,981,692 | |  | (b) | | | 1,757,460 | |  |  | | |  | | |  | | | 2,045,249 | |  | (b)(e) | | | 1,740,429 | |  | (e)
| | |  | | |\n| CET1 capital ratio | | | 14.6 | | % | (c) | | | 15.7 | | % |  | | | 11.5 | | % |  | | | 14.1 | | % | (c) | | | 15.8 | | % |  | | | 11.5 | | % |\n| Tier 1 capital ratio | | | 15.5 | |  | (c) | | | 16.8 | |  |  | | | 13.0 | |  |  | | | 15.0 | |  | (c) | | | 16.9 | |  |  | | | 13.0 | |
|\n| Total capital ratio | | | 17.4 | |  | (c) | | | 18.5 | |  |  | | | 15.0 | |  |  | | | 16.1 | |  | (c) | | | 17.9 | |  |  | | | 15.0 | |  |",
     "score": 0.592
    },
    {
     "source": "sec://0001628280-26-008131/unknown#268",
     "title": "JPM FY2025 10-K",
     "content": "(a)As of January 1, 2025, the benefit from the CECL capital transition provision had been fully phased out. For the year ended December 31, 2024, CET1 capital reflected a $720 million benefit. Refer to Note 27 for additional information.\n\n(b)Includes approximately $23 billion
under the Standardized approach and approximately $110 billion under the Advanced approach related to the Apple Card transaction. Advanced RWA is expected to reduce to approximately $30 billion once the necessary modeling steps are completed, which is expected in the near term.\n\n(c)Includes
decreases of approximately 25 basis points under the Standardized approach and approximately 90 basis points under the Advanced approach related to the Apple Card transaction. The impact under the Advanced approach is expected to reduce to approximately 30 basis points once the necessary modeling
steps are completed, which is expected in the near term.\n\n(d)Represents minimum requirements and regulatory buffers applicable to the Firm for the year ended December 31, 2025. For the year ended December 31, 2024, the Standardized CET1, Tier 1, and Total capital ratio requirements applicable to
the Firm were 12.3%, 13.8%, and 15.8%, respectively; the Advanced CET1, Tier 1, and Total capital ratio requirements applicable to the Firm were 11.5%, 13.0%, and 15.0%, respectively. Refer to Note 27 for additional information.\n\n(e)Includes the impacts of certain assets associated with First
Republic to which the Standardized approach has been applied as permitted by the transition provisions in the U.S. capital rules.",
     "score": 0.6192
    },
    {
     "source": "sec://0001628280-26-008131/unknown#269",
     "title": "JPM FY2025 10-K",
     "content": "(e)Includes the impacts of certain assets associated with First Republic to which the Standardized approach has been applied as permitted by the transition provisions in the U.S. capital rules.\n\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | ---
| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| Three months ended   (in millions, except ratios) | | | December 31, 2025 | | | December 31, 2024 | | |  | | | Capital ratio requirements(c) | | |\n| Leverage-based capital metrics:(a) | | |  | | |  | | |  | | |  | | |\n| Adjusted average
assets(b) | | | $ | 4,472,394 |  | $ | 4,070,499 |  |  | | |  | | |\n| Tier 1 leverage ratio | | | 6.9 | | % | 7.2 | | % |  | | | 4.0 | | % |\n| Total leverage exposure | | | $ | 5,302,001 |  | $ | 4,837,568 |  |  | | |  | | |\n| SLR | | | 5.8 | | % | 6.1 | | % |  | | | 5.0 | | % |\n\n(a)As of
January 1, 2025, the benefit from the CECL capital transition provision had been fully phased out. The capital metrics for the year ended December 31, 2024 reflected the CECL capital transition provisions. Refer to Note 27 for additional information.\n\n(b)Adjusted average assets, for purposes of
calculating the leverage ratios, includes quarterly average assets adjusted for on-balance sheet assets that are subject to deduction from Tier 1 capital, predominantly goodwill (inclusive of estimated equity method goodwill) and other intangible assets.\n\n(c)Represents minimum requirements and
regulatory buffers applicable to the Firm. Refer to Note 27 for additional information.",
     "score": 0.6249
    },
    {
     "source": "sec://0001628280-26-008131/unknown#275",
     "title": "JPM FY2025 10-K",
     "content": "| Standardized/Advanced Tier 1 capital at December 31, 2025 | | | $ | 307,630 |  |\n|  | | |  | | |\n| Standardized Tier 2 capital at December 31, 2024 | | | $ | 30,708 |  |\n| Change in long-term debt and other instruments qualifying as Tier 2(c) | | | 3,227 | |  |\n| Change in
qualifying allowance for credit losses(b) | | | 2,741 | |  |\n| Other | | | (463) | |  |\n| Change in Standardized Tier 2 capital | | | 5,505 | |  |\n| Standardized Tier 2 capital at December 31, 2025 | | | $ | 36,213 |  |\n| Standardized Total capital at December 31, 2025 | | | $ | 343,843 |  |\n|
Advanced Tier 2 capital at December 31, 2024 | | | $ | 17,017 |  |\n| Change in long-term debt and other instruments qualifying as Tier 2(c) | | | 3,227 | |  |\n| Change in qualifying allowance for credit losses(b)(d) | | | 1,551 | |  |\n| Other | | | (463) | |  |\n| Change in Advanced Tier 2
capital | | | 4,315 | |  |\n| Advanced Tier 2 capital at December 31, 2025 | | | $ | 21,332 |  |\n| Advanced Total capital at December 31, 2025 | | | $ | 328,962 |  |",
     "score": 0.6094
    },
    {
     "source": "sec://0001628280-26-008131/unknown#287",
     "title": "JPM FY2025 10-K",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | December 31, 2025 | | | | | | December 31, 2024 | | | | | |\n| (in billions, except ratio) | | | External TLAC | | | LTD | | |
External TLAC | | | LTD | | |\n| Total eligible amount | | | $ | 563.7 |  | $ | 246.0 |  | $ | 546.6 |  | $ | 236.8 |  |\n| % of RWA | | | 27.6 | | % | 12.0 | | % | 31.1 | | % | 13.5 | | % |\n| Regulatory requirements | | | 23.0 | |  | 10.5 | |  | 23.0 | |  | 10.5 | |  |\n| Surplus/(shortfall) | | |
$ | 93.3 |  | $ | 31.2 |  | $ | 142.3 |  | $ | 52.3 |  |\n|  | | |  | | |  | | |  | | |  | | |\n| % of total leverage exposure | | | 10.6 | | % | 4.6 | | % | 11.3 | | % | 4.9 | | % |\n| Regulatory requirements | | | 9.5 | |  | 4.5 | |  | 9.5 | |  | 4.5 | |  |\n| Surplus/(shortfall) | | | $ | 60.1 |
| $ | 7.4 |  | $ | 87.0 |  | $ | 19.2 |  |\n\nRefer to Liquidity Risk Management on pages 100–107 for further information on long-term debt issued by the Parent Company.",
     "score": 0.5905
    },
    {
     "source": "sec://0001628280-26-008131/unknown#991",
     "title": "JPM FY2025 10-K",
     "content": "(d)Includes the impacts of certain assets associated with First Republic to which the Standardized approach has been applied as permitted by the transition provisions in the U.S. capital rules.\n\n- Three months ended\n(in millions, except ratios) December 31, 2025 December 31,
2024\n- JPMorgan\nChase & Co. JPMorgan\nChase Bank, N.A. JPMorgan\nChase & Co. JPMorgan\nChase Bank, N.A.\n- Leverage-based capital metrics:(a)\n- Adjusted average assets(b) $ 4,472,394 $ 3,766,709 $ 4,070,499 $ 3,491,283\n- Tier 1 leverage ratio 6.9 % 7.8 % 7.2 % 7.9 %\n- Total leverage exposure $
5,302,001 $ 4,571,728 $ 4,837,568 $ 4,246,516\n- SLR 5.8 % 6.4 % 6.1 % 6.5 %\n\n(a)As of January 1, 2025, the benefit from the CECL capital transition provision had been fully phased out. The capital metrics for the year ended December 31, 2024 reflected the CECL capital transition
provisions.\n\n(b)Adjusted average assets, for purposes of calculating the leverage ratios, includes quarterly average assets adjusted for on-balance sheet assets that are subject to deduction from Tier 1 capital, predominantly goodwill (inclusive of estimated equity method goodwill) and other
intangible assets.\n\n|  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 294 | | |  | | | JPMorgan Chase & Co./2025 Form 10-K | | |",
     "score": 0.5961
    }
   ]
  }
 ]
}

[tool 6] finnhub_company_basic_financials {"ticker": "WFC"}
{
 "ticker": "WFC",
 "fiftyTwoWeekHigh": 97.76,
 "fiftyTwoWeekLow": 72.78,
 "peTTM": 10.8882,
 "forwardPE": 11.17733,
 "psTTM": 1.90599,
 "pb": 1.3671,
 "marketCap": 250124.22,
 "enterpriseValue": 691686.22,
 "beta": 0.9418643,
 "epsTTM": 7.4163,
 "roeTTM": 12.839999999999998,
 "roaTTM": 1.03,
 "netProfitMarginTTM": 22.19029,
 "operatingMarginTTM": 25.34514,
 "debtToEquity": 2.5123,
 "dividendYield": 2.2733013387218994,
 "revenueGrowthTTMYoy": 72.74767,
 "epsGrowthTTMYoy": 15.87,
 "tenDayAvgVolume": 17.9129
}

[tool 7] finnhub_company_basic_financials {"ticker": "C"}
{
 "ticker": "C",
 "fiftyTwoWeekHigh": 147.96,
 "fiftyTwoWeekLow": 95.83,
 "peTTM": 10.5174,
 "forwardPE": 10.66883,
 "psTTM": 1.09533,
 "pb": 1.0234,
 "marketCap": 203322.11,
 "enterpriseValue": 1020799.11,
 "beta": 1.1610881,
 "epsTTM": 11.0502,
 "roeTTM": 9.15,
 "roaTTM": 0.69,
 "netProfitMarginTTM": 17.3666,
 "operatingMarginTTM": 23.01502,
 "debtToEquity": 3.9037,
 "dividendYield": 4.68715,
 "revenueGrowthTTMYoy": 99.23775,
 "epsGrowthTTMYoy": 42.89,
 "tenDayAvgVolume": 10.13462
}
----- END EVIDENCE F0005 -----

----- BEGIN ANSWER F0005 -----
**結論：這個說法目前仍大致站得住，但應理解成「資本與風險管理相對強韌」，不是「不會受景氣或信貸週期影響」。** JPMorgan 的確比多數大型銀行更像「核心持有型」銀行；不過它的規模、交易業務與信貸曝險也讓它不可能沒有風險。

### 為什麼「穩」的說法仍有根據

- **資本緩衝仍然厚。** JPMorgan FY2025 10-K（財政年度截至 2025-12-31）顯示，標準法 CET1 比率為 **14.6%**，相對適用的 **11.5%** 要求高出約 3.1 個百分點；SLR 槓桿比率為 **5.8%**，高於 5.0% 要求。[1][2]
- **流動性與存款基礎仍偏穩健。** FY2025 平均流動性覆蓋率（LCR）為 **111%**，貸款對存款比為 **58%**；這表示它並不是高度依賴短期批發融資來支撐貸款。[1]
- **盈利能力明顯優於幾家主要同業。** 根據 Finnhub 最新基本面資料，JPMorgan 的 TTM ROE 約 **17.9%**、ROA 約 **1.36%**；相較之下，Bank of America 約為 10.7%／0.93%、Wells Fargo 約為 12.8%／1.03%、花旗約為 9.2%／0.69%。這種持續產生資本的能力，是大型銀行「穩」的重要來源。
- **風險管理框架較制度化。** 10-K 說明其每日進行流動性壓力測試，納入融資市場中斷、信用評級下調、抵押品折價與跨法域資金調度限制等情境。[3]

### 但不能忽略的轉弱訊號

- **信用成本正在上升。** FY2025 信貸損失準備為 **142.12 億美元**，高於 FY2024 的 106.78 億美元；淨沖銷也由 6.89 億美元升至 **15.09 億美元**。[1][4]
- **不良貸款有所增加。** FY2025 總非應計貸款為 **51.59 億美元**，高於前一年的 47.60 億美元；同時，貸款餘額年增約 11%。這不代表已出現危機，但意味著在經濟放緩或企業違約上升時，損失可能繼續增加。[4]
- **規模越大，複雜度與系統性曝險也越高。** JPMorgan 不只是傳統存放款銀行，還有投資銀行、交易、信用卡、衍生品及資本市場業務。這讓收入來源多元，但也使它暴露於市場波動、交易損失、操作風險與監管變化。
- **股價已反映部分「優質銀行」溢價。** Finnhub 最新資料顯示，JPM 約 **13.5 倍 TTM 本益比、2.36 倍市淨率**；相較之下，BAC 約 11.0 倍／1.27 倍、WFC 約 10.9 倍／1.37 倍、C 約 10.5 倍／1.02 倍。換句話說，JPM 可能是品質較高者，但不代表目前估值一定便宜。

目前 Finnhub 報價顯示 JPM 約為 **336.21 美元**，當日上漲約 **0.65%**。單日價格本身不能判定銀行是否穩健，但市場顯然仍給予它高於多數大型銀行的估值。

**我的判斷是：**  
- 若「穩」是指資本、流動性、盈利能力和危機承受力，**說法仍成立**。  
- 若「穩」被理解為信貸損失不會上升、股價不會大跌或沒有監管與市場風險，**就過度簡化了**。  
- 接下來最值得觀察的是：CET1 是否維持在要求之上、淨沖銷與信貸準備是否繼續上升、貸款成長是否放慢，以及其高估值能否由盈利增長支撐。

[1]: SEC 10-K excerpt  
[2]: SEC 10-K excerpt  
[3]: SEC 10-K excerpt  
[4]: SEC 10-K excerpt
----- END ANSWER F0005 -----

===== ITEM F0006 =====

QUESTION:
蘋果、微軟、Google 裡面，誰最有餘裕同時維持回購，又不把財務風險拉太高？

----- BEGIN EVIDENCE F0006 -----
[tool 0] sec_filing_search {"query": "share repurchases cash flow liquidity debt obligations financial risk", "ticker": "AAPL", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-09-27",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 8",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 8 (Financial Statements and Supplementary Data) — 6 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/8#103",
     "title": "AAPL FY2025 10-K · Item 8",
     "content": "| Total assets | | | $ | 359,241 |  |  | | | $ | 364,980 |  |\n|  | | |  | | |  | | |  | | |\n| LIABILITIES AND SHAREHOLDERS’ EQUITY: | | | | | | | | | | | |\n| Current liabilities: | | |  | | |  | | |  | | |\n| Accounts payable | | | $ | 69,860 |  |  | | | $ | 68,960 |  |\n| Other
current liabilities | | | 66,387 | |  |  | | | 78,304 | |  |\n| Deferred revenue | | | 9,055 | |  |  | | | 8,249 | |  |\n| Commercial paper | | | 7,979 | |  |  | | | 9,967 | |  |\n| Term debt | | | 12,350 | |  |  | | | 10,912 | |  |\n| Total current liabilities | | | 165,631 | |  |  | | | 176,392 |
|  |\n|  | | |  | | |  | | |  | | |\n| Non-current liabilities: | | |  | | |  | | |  | | |\n| Term debt | | | 78,328 | |  |  | | | 85,750 | |  |\n| Other non-current liabilities | | | 41,549 | |  |  | | | 45,888 | |  |\n| Total non-current liabilities | | | 119,877 | |  |  | | | 131,638 | |  |\n|
Total liabilities | | | 285,508 | |  |  | | | 308,030 | |  |\n|  | | |  | | |  | | |  | | |\n| Commitments and contingencies | | |  | | |  | | |  | | |\n|  | | |  | | |  | | |  | | |\n| Shareholders’ equity: | | |  | | |  | | |  | | |",
     "score": 0.4881
    },
    {
     "source": "sec://0000320193-25-000079/8#114",
     "title": "AAPL FY2025 10-K · Item 8",
     "content": "| Proceeds from maturities of marketable securities | | | 40,907 | |  |  | | | 51,211 | |  |  | | | 39,686 | |  |\n| Proceeds from sales of marketable securities | | | 12,890 | |  |  | | | 11,135 | |  |  | | | 5,828 | |  |\n| Payments for acquisition of property, plant and equipment
| | | (12,715) | |  |  | | | (9,447) | |  |  | | | (10,959) | |  |\n|\n| Other | | | (1,480) | |  |  | | | (1,308) | |  |  | | | (1,337) | |  |\n| Cash generated by investing activities | | | 15,195 | |  |  | | | 2,935 | |  |  | | | 3,705 | |  |\n|  | | |  | | |  | | |  | | |  | | |  | | |\n|
Financing activities: | | |  | | |  | | |  | | |  | | |  | | |\n| Payments for taxes related to net share settlement of equity awards | | | (5,960) | |  |  | | | (5,441) | |  |  | | | (5,431) | |  |\n| Payments for dividends and dividend equivalents | | | (15,421) | |  |  | | | (15,234) | |  |  | |
| (15,025) | |  |\n| Repurchases of common stock | | | (90,711) | |  |  | | | (94,949) | |  |  | | | (77,550) | |  |\n| Proceeds from issuance of term debt, net | | | 4,481 | |  |  | | | — | |  |  | | | 5,228 | |  |\n| Repayments of term debt | | | (10,932) | |  |  | | | (9,958) | |  |  | | |
(11,151) | |  |",
     "score": 0.4868
    },
    {
     "source": "sec://0000320193-25-000079/8#115",
     "title": "AAPL FY2025 10-K · Item 8",
     "content": "| Repayments of term debt | | | (10,932) | |  |  | | | (9,958) | |  |  | | | (11,151) | |  |\n| Proceeds from/(Repayments of) commercial paper, net | | | (2,032) | |  |  | | | 3,960 | |  |  | | | (3,978) | |  |\n| Other | | | (111) | |  |  | | | (361) | |  |  | | | (581) | |  |\n|
Cash used in financing activities | | | (120,686) | |  |  | | | (121,983) | |  |  | | | (108,488) | |  |\n|  | | |  | | |  | | |  | | |  | | |  | | |\n| Increase/(Decrease) in cash, cash equivalents, and restricted cash and cash equivalents | | | 5,991 | |  |  | | | (794) | |  |  | | | 5,760 | |
|\n| Cash, cash equivalents, and restricted cash and cash equivalents, ending balances | | | $ | 35,934 |  |  | | | $ | 29,943 |  |  | | | $ | 30,737 |  |\n|  | | |  | | |  | | |  | | |  | | |  | | |\n| Supplemental cash flow disclosure: | | |  | | |  | | |  | | |  | | |  | | |\n| Cash paid for
income taxes, net | | | $ | 43,369 |  |  | | | $ | 26,102 |  |  | | | $ | 18,679 |  |",
     "score": 0.4894
    },
    {
     "source": "sec://0000320193-25-000079/8#176",
     "title": "AAPL FY2025 10-K · Item 8 · Commercial Paper",
     "content": "### Commercial Paper\n\nThe Company issues unsecured short-term promissory notes pursuant to a commercial paper program. The Company uses net proceeds from the commercial paper program for general corporate purposes, including dividends and share repurchases. As of September 27,
2025 and September 28, 2024, the Company had $8.0 billion and $10.0 billion of commercial paper outstanding, respectively, with maturities generally less than nine months. The weighted-average interest rate of the Company’s commercial paper was 4.19% and 5.00% as of September 27, 2025 and September
28, 2024, respectively. The following table provides a summary of cash flows associated with commercial paper for 2025, 2024 and 2023 (in millions):",
     "score": 0.5529,
     "subsection": "Commercial Paper"
    },
    {
     "source": "sec://0000320193-25-000079/8#181",
     "title": "AAPL FY2025 10-K · Item 8 · Share Repurchase Program",
     "content": "### Share Repurchase Program\n\nDuring 2025, the Company repurchased 402 million shares of its common stock for $89.3 billion. The Company’s share repurchase programs do not obligate the Company to acquire a minimum amount of shares. Under the programs, shares may be repurchased in
privately negotiated or open market transactions, including under plans complying with Rule 10b5-1 under the Exchange Act.\n\nApple Inc. | 2025 Form 10-K | 44",
     "score": 0.5433,
     "subsection": "Share Repurchase Program"
    },
    {
     "source": "sec://0000320193-25-000079/8#182",
     "title": "AAPL FY2025 10-K · Item 8 · Shares of Common Stock",
     "content": "### Shares of Common Stock\n\nThe following table shows the changes in shares of common stock for 2025, 2024 and 2023 (in thousands):\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
| --- | --- | --- |\n|  | | | 2025 | | |  | | | 2024 | | |  | | | 2023 | | |\n| Common stock outstanding, beginning balances | | | 15,116,786 | |  |  | | | 15,550,061 | |  |  | | | 15,943,425 | |  |\n| Common stock repurchased | | | (401,672) | |  |  | | | (499,372) | |  |  | | | (471,419) | |  |\n|
Common stock issued, net of shares withheld for employee taxes | | | 58,146 | |  |  | | | 66,097 | |  |  | | | 78,055 | |  |\n| Common stock outstanding, ending balances | | | 14,773,260 | |  |  | | | 15,116,786 | |  |  | | | 15,550,061 | |  |",
     "score": 0.4917,
     "subsection": "Shares of Common Stock"
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 7",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/7#80",
     "title": "AAPL FY2025 10-K · Item 7 · Liquidity and Capital Resources",
     "content": "### Liquidity and Capital Resources\n\nThe Company believes its balances of cash, cash equivalents and marketable securities, which totaled $132.4 billion as of September 27, 2025, along with cash generated by ongoing operations and continued access to debt markets, will be
sufficient to satisfy its cash requirements and capital return program over the next 12 months and beyond.\n\nThe Company’s material cash requirements include the following contractual obligations:\n\nDebt\n\nAs of September 27, 2025, the Company had outstanding fixed-rate notes with varying
maturities for an aggregate principal amount of $91.3 billion (collectively the “Notes”), with $12.4 billion payable within 12 months. Future interest payments associated with the Notes total $37.0 billion, with $2.6 billion payable within 12 months.\n\nThe Company also issues unsecured short-term
promissory notes pursuant to a commercial paper program. As of September 27, 2025, the Company had $8.0 billion of commercial paper outstanding, which was payable within 12 months.\n\nLeases\n\nThe Company has lease arrangements for certain equipment and facilities, including corporate, data center,
manufacturing and retail space. As of September 27, 2025, the Company had fixed lease payment obligations of $16.8 billion, with $2.6 billion payable within 12 months.\n\nManufacturing Purchase Obligations\n\nThe Company utilizes several outsourcing partners to manufacture subassemblies for the
Company’s products and to perform final assembly and testing of finished products. The Company also obtains individual components for its products from a wide variety of individual suppliers. As of September 27, 2025, the Company had manufacturing purchase obligations of $56.2 billion, with $55.4
billion payable within 12 months.\n\nOther Purchase Obligations\n\nThe Company’s other purchase obligations primarily consist of noncancelable obligations to acquire capital assets, including assets related to product manufacturing, and noncancelable obligations related to supplier arrangements,
licensed intellectual property and content, and distribution rights. As of September 27, 2025, the Company had other purchase obligations of $14.8 billion, with $7.0 billion payable within 12 months.\n\nDeemed Repatriation Tax Payable",
     "score": 0.5296,
     "subsection": "Liquidity and Capital Resources"
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 5",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 5 (Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities) — 2 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/5#54",
     "title": "AAPL FY2025 10-K · Item 5 · Purchases of Equity Securities by the Issuer and Affiliated Purchasers",
     "content": "### Purchases of Equity Securities by the Issuer and Affiliated Purchasers\n\nShare repurchase activity during the three months ended September 27, 2025, was as follows (in millions, except number of shares, which are reflected in thousands, and per-share amounts):",
     "score": 0.4908,
     "subsection": "Purchases of Equity Securities by the Issuer and Affiliated Purchasers"
    },
    {
     "source": "sec://0000320193-25-000079/5#57",
     "title": "AAPL FY2025 10-K · Item 5",
     "content": "(1)On May 2, 2024, the Company announced a program to repurchase up to $110 billion of the Company’s common stock. During the fourth quarter of 2025, the Company utilized the final $19.8 billion under the May 2024 program. On May 1, 2025, the Company announced an additional program
to repurchase up to $100 billion of the Company’s common stock. As of September 27, 2025, $221 million of the May 2025 program had been utilized. The programs do not obligate the Company to acquire a minimum amount of shares. Under the programs, shares may be repurchased in privately negotiated or
open market transactions, including under plans complying with Rule 10b5-1 under the Exchange Act.\n\nApple Inc. | 2025 Form 10-K | 19",
     "score": 0.4863
    }
   ]
  },
  {
   "ticker": "AAPL",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from AAPL FY2025 10-K, Item 1A (Risk Factors) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0000320193-25-000079/1a#43",
     "title": "AAPL FY2025 10-K · Item 1A · General Risks",
     "content": "### General Risks\n\nThe price of the Company’s stock is subject to volatility.\n\nThe Company’s stock has experienced substantial price volatility in the past and may continue to do so in the future. Additionally, the Company, the technology industry and the stock market as a whole
have, from time to time, experienced extreme stock price and volume fluctuations that have affected stock prices in ways that may have been unrelated to these companies’ operating performance. Price volatility may cause the average price at which the Company repurchases its stock in a given period
to exceed the stock’s price at a given point in time. The Company believes the price of its stock should reflect expectations of future growth and profitability. The Company also believes the price of its stock should reflect expectations that its cash dividend will continue at current levels or
grow, and that its current share repurchase program will be fully consummated. Future dividends are subject to declaration by the Company’s Board of Directors (“Board”), and the Company’s share repurchase program does not obligate it to acquire any specific number of shares. If the Company fails to
meet expectations related to future growth, profitability, dividends, share repurchases or other market expectations, the price of the Company’s stock may decline significantly, which could have a material adverse impact on investor confidence and employee retention.",
     "score": 0.4862,
     "subsection": "General Risks"
    }
   ]
  }
 ]
}

[tool 1] sec_filing_search {"query": "share repurchases cash flow liquidity debt obligations financial risk", "ticker": "GOOGL", "fiscal_year": null}
{
 "fiscal_year": 2025,
 "fiscal_year_end": "2025-12-31",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "GOOGL",
   "fiscal_year": 2025,
   "item": "Item 8",
   "prelude": "Excerpts from GOOGL FY2025 10-K, Item 8 (Financial Statements and Supplementary Data) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001652044-26-000018/8#311",
     "title": "GOOGL FY2025 10-K · Item 8 · Share Repurchases",
     "content": "### Share Repurchases\n\nIn the years ended December 31, 2023, 2024, and 2025, we continued to repurchase both Class A and Class C shares in a manner deemed in the best interest of the company and its stockholders, taking into account the economic cost and prevailing market
conditions, including the relative trading prices and volumes of the Class A and Class C shares. In April 2024, the company's Board of Directors authorized a $70.0 billion share repurchase program for its Class A and Class C shares. In April 2025, the company's Board of Directors authorized an
additional $70.0 billion share repurchase program for its Class A and Class C shares. As of December 31, 2025, $69.5 billion remained available for Class A and Class C share repurchases.\n\nThe following table presents Class A and Class C shares repurchased and subsequently retired (in millions):",
     "score": 0.53,
     "subsection": "Share Repurchases"
    },
    {
     "source": "sec://0001652044-26-000018/8#312",
     "title": "GOOGL FY2025 10-K · Item 8",
     "content": "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
--- | --- | --- | --- | --- | --- | --- | --- |\n|  | | | Year Ended December 31, | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |\n|  | | | 2023 | | | | | | | | |  | | | 2024 | | | | | | | | |  | | | 2025 | | | | | | | | |\n|  | | | Shares | | |  | | | Amount | | |  | | | Shares |
| |  | | | Amount | | |  | | | Shares | | |  | | | Amount | | |\n| Class A share repurchases | | | 78 | | |  | | | $ | 9,316 |  |  | | | 73 | | |  | | | $ | 11,855 |  |  | | | 37 | | |  | | | $ | 6,501 |  |\n| Class C share repurchases | | | 450 | | |  | | | 52,868 | |  |  | | | 306 | | |  | | |
50,192 | |  |  | | | 203 | | |  | | | 38,897 | |  |",
     "score": 0.4966
    },
    {
     "source": "sec://0001652044-26-000018/8#313",
     "title": "GOOGL FY2025 10-K · Item 8",
     "content": "| Total share repurchases(1) | | | 528 | | |  | | | $ | 62,184 |  |  | | | 379 | | |  | | | $ | 62,047 |  |  | | | 240 | | |  | | | $ | 45,398 |  |(1) Shares repurchased include any unsettled repurchases.",
     "score": 0.5552
    },
    {
     "source": "sec://0001652044-26-000018/8#314",
     "title": "GOOGL FY2025 10-K · Item 8",
     "content": "Repurchases are executed from time to time, subject to general business and market conditions and other investment opportunities, through open market purchases or privately negotiated transactions, including through Rule 10b5-1 plans. The repurchase programs do not have an
expiration date.",
     "score": 0.5197
    }
   ]
  },
  {
   "ticker": "GOOGL",
   "fiscal_year": 2025,
   "item": "Item 7",
   "prelude": "Excerpts from GOOGL FY2025 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001652044-26-000018/7#112",
     "title": "GOOGL FY2025 10-K · Item 7 · Sources, Uses of Cash and Related Trends",
     "content": "### Sources, Uses of Cash and Related Trends\n\nOur principal sources of liquidity are cash, cash equivalents, and marketable securities, as well as the cash flow that we generate from operations. The primary use of capital continues to be to invest for the long-term growth of the
business. We regularly evaluate our cash and capital structure, including the size, pace, and form of capital return to stockholders.\n\nThe following table presents cash flows (in millions):\n\n|  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
| --- |\n|  | | | Year Ended December 31, | | | | | | | | |\n|  | | | 2024 | | |  | | | 2025 | | |\n| Net cash provided by operating activities | | | $ | 125,299 |  |  | | | $ | 164,713 |  |\n| Net cash used in investing activities | | | $ | (45,536) |  |  | | | $ | (120,291) |  |\n| Net cash used
in financing activities | | | $ | (79,733) |  |  | | | $ | (37,388) |  |",
     "score": 0.5271,
     "subsection": "Sources, Uses of Cash and Related Trends"
    },
    {
     "source": "sec://0001652044-26-000018/7#115",
     "title": "GOOGL FY2025 10-K · Item 7 · Cash Used in Financing Activities",
     "content": "### Cash Used in Financing Activities\n\nCash provided by financing activities consists primarily of proceeds from issuance of debt and proceeds from the sale of interests in consolidated entities. Cash used in financing activities consists primarily of repurchases of stock,
repayments of debt, net payments related to stock-based award activities, and dividend payments.\n\nNet cash used in financing activities decreased from 2024 to 2025 due to an increase in proceeds from issuance of debt and a decrease in repurchases of stock, partially offset by repayments of debt.",
     "score": 0.4842,
     "subsection": "Cash Used in Financing Activities"
    },
    {
     "source": "sec://0001652044-26-000018/7#119",
     "title": "GOOGL FY2025 10-K · Item 7 · Financing",
     "content": "### Financing\n\nAs of December 31, 2025, we had senior unsecured notes outstanding with a total carrying value of $48.5 billion, of which $2.0 billion was short-term. The associated short-term and long-term future interest payments were $1.8 billion and $35.7 billion,
respectively.\n\nDuring 2025, we issued $22.5 billion of US dollar-denominated senior unsecured notes and €13.25 billion of euro-denominated senior unsecured notes for general corporate purposes, comprised of the following:\n\n•May 2025: We issued $5.0 billion of US dollar-denominated fixed-rate
senior unsecured notes with a weighted-average coupon rate of 4.89%, and a weighted-average maturity of approximately 24 years. We also issued €6.75 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.31%, and a weighted-average maturity of
approximately 14 years.\n\n•November 2025: We issued $500 million of US dollar-denominated floating-rate senior unsecured notes and $17.0 billion of US dollar-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 4.92% and a weighted-average maturity of approximately
20 years. We also issued €6.5 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.44% and a weighted-average maturity of approximately 16 years.\n\nAs of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring
in April 2026 and $6.0 billion expiring in April 2030. No amounts have been borrowed under the credit facilities. We also have a commercial paper program of up to $25.0 billion, which is used for general corporate purposes. As of December 31, 2025, we had no commercial paper outstanding.\n\nFor
additional information, see Note 6 of the Notes to Consolidated Financial Statements included in Item 8 of this Annual Report on Form 10-K.\n\nWe use contract manufacturers for our technical infrastructure and device assembly and may supply them with components purchased directly from suppliers.
Certain of these arrangements result in a portion of the cash received from and paid to contract manufacturers to be presented as financing activities on the Consolidated Statements of Cash Flows included in Item 8 of this Annual Report on Form 10-K.",
     "score": 0.4832,
     "subsection": "Financing"
    },
    {
     "source": "sec://0001652044-26-000018/7#120",
     "title": "GOOGL FY2025 10-K · Item 7 · Share Repurchase Program",
     "content": "### Share Repurchase Program\n\nDuring 2025, we repurchased and subsequently retired 240 million shares for $45.4 billion.\n\nIn April 2024, the company's Board of Directors authorized a $70.0 billion share repurchase program for its Class A and Class C shares. In April 2025, the
company's Board of Directors authorized an additional $70.0 billion share repurchase program for its Class A and Class C shares. As of December 31, 2025, $69.5 billion remained available for Class A and Class C share repurchases.\n\nFor additional information, see Note 11 of the Notes to
Consolidated Financial Statements included in Item 8 of this Annual Report on Form 10-K.",
     "score": 0.5219,
     "subsection": "Share Repurchase Program"
    }
   ]
  },
  {
   "ticker": "GOOGL",
   "fiscal_year": 2025,
   "item": "Item 5",
   "prelude": "Excerpts from GOOGL FY2025 10-K, Item 5 (Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001652044-26-000018/5#71",
     "title": "GOOGL FY2025 10-K · Item 5",
     "content": "(1) In April 2024, the company's Board of Directors authorized a $70.0 billion share repurchase program for its Class A and Class C shares. In April 2025, the company's Board of Directors authorized an additional $70.0 billion share repurchase program for its Class A and Class C
shares. Repurchases are being executed from time to time, subject to general business and market conditions and other investment opportunities, through open market purchases or privately negotiated transactions, including through Rule 10b5-1 plans. The repurchase programs do not have an expiration
date. For additional information related to share repurchases, see Note 11 of the Notes to Consolidated Financial Statements included in Item 8 of this Annual Report on Form 10-K.\n\n(2) Average price paid per share includes costs associated with the repurchases.\n\n\n25.\n\n\n|  |  |  |  |  |  |\n|
--- | --- | --- | --- | --- | --- |\n| [Table of Contents](#i6be430fe3ebf411481dcec8b0abe9149_7) | | | Alphabet Inc. | | |",
     "score": 0.4888
    }
   ]
  },
  {
   "ticker": "GOOGL",
   "fiscal_year": 2025,
   "item": "Item 1A",
   "prelude": "Excerpts from GOOGL FY2025 10-K, Item 1A (Risk Factors) — 1 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001652044-26-000018/1a#52",
     "title": "GOOGL FY2025 10-K · Item 1A · Risks Related to Ownership of Our Stock",
     "content": "### Risks Related to Ownership of Our Stock\n\nWe cannot guarantee that any share repurchase program or dividend program will be continuously active or fully consummated or will enhance long-term stockholder value, and share repurchases or dividends could increase the volatility of
our stock prices and could diminish our cash reserves.\n\nWe engage in share repurchases of our Class A and Class C stock from time to time in accordance with authorizations from the Board of Directors of Alphabet. Our repurchase program does not have an expiration date and does not obligate
Alphabet to repurchase any specific dollar amount or to acquire any specific number of shares. Our cash dividend program pays regular cash dividends to our Class A, Class B, and Class C stockholders. Any and all future cash dividends are subject to declaration by our Board of Directors in its sole
discretion, and in accordance with the requirements of any applicable laws, rules, and regulations, including the Delaware General Corporation Law. Our cash dividend program does not require, and our Board of Directors may decide not to declare, a cash dividend each quarter, and does not obligate
our Board of Directors to declare a dividend at any specific dollar amount per share. Any such decision by our Board of Directors may depend on a variety of factors that it may deem relevant, including but not limited to our earnings, liquidity, financial condition, other capital deployment
opportunities, level of indebtedness, and general market conditions. Our share repurchases and dividends could affect our share trading prices, increase their volatility, reduce our cash reserves and may be suspended or terminated at any time, which may result in a decrease in the trading prices of
our stock.\n\nThe concentration of our stock ownership limits our stockholders' ability to influence corporate matters.\n\nOur Class B stock has 10 votes per share, our Class A stock has one vote per share, and our Class C stock has no voting rights. As of December 31, 2025, Larry Page and Sergey
Brin beneficially owned approximately 89.3% of our\n\n21.\n\n\n|  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- |\n| [Table of Contents](#i6be430fe3ebf411481dcec8b0abe9149_7) | | | Alphabet Inc. | | |",
     "score": 0.4813,
     "subsection": "Risks Related to Ownership of Our Stock"
    }
   ]
  }
 ]
}

[tool 2] sec_filing_search {"query": "share repurchases cash flow liquidity debt obligations financial risk", "ticker": "MSFT", "fiscal_year": null}
{
 "fiscal_year": 2026,
 "fiscal_year_end": "2026-06-30",
 "fiscal_year_source": "latest",
 "total_chunks": 10,
 "groups": [
  {
   "ticker": "MSFT",
   "fiscal_year": 2026,
   "item": "Item 7",
   "prelude": "Excerpts from MSFT FY2026 10-K, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001193125-26-323660/7#106",
     "title": "MSFT FY2026 10-K · Item 7",
     "content": "LIQUIDITY AND CAPITAL RESOURCES\n\nWe expect existing cash, cash equivalents, short-term investments, cash flows from operations, and access to capital markets to continue to be sufficient to fund our operating activities and cash commitments for investing and financing activities,
such as dividends, share repurchases, debt maturities, and material capital expenditures, for at least the next 12 months and thereafter for the foreseeable future.\n\n\n\n42\n\n\nPART II\n\nItem 7",
     "score": 0.5172
    },
    {
     "source": "sec://0001193125-26-323660/7#109",
     "title": "MSFT FY2026 10-K · Item 7 · Cash Flows",
     "content": "### Cash Flows\n\nCash from operations increased $46.8 billion to $182.9 billion for fiscal year 2026, primarily due to an increase in cash received from customers and a decrease in cash used to pay income taxes, offset in part by an increase in cash paid to suppliers. Cash used in
financing increased $847 million to $52.5 billion for fiscal year 2026, primarily due to a $6.0 billion decrease in cash used for repayments of debt, offset in part by a $3.9 billion increase in common stock repurchases and a $2.4 billion increase in dividends paid. Cash used in investing increased
$66.9 billion to $139.5 billion for fiscal year 2026, primarily due to a $51.4 billion increase in additions to property and equipment and a $22.2 billion increase in cash used in other investing primarily to facilitate the purchase of components, offset in part by a $4.2 billion decrease in cash
used in the acquisition of companies, net of cash acquired and divestitures, and purchases of intangible and other assets and a $2.4 billion decrease in cash used in net investment purchases, sales, and maturities.",
     "score": 0.4937,
     "subsection": "Cash Flows"
    },
    {
     "source": "sec://0001193125-26-323660/7#110",
     "title": "MSFT FY2026 10-K · Item 7 · Debt Proceeds",
     "content": "### Debt Proceeds\n\nWe issue debt to take advantage of favorable pricing and liquidity in the debt markets, reflecting our credit rating. The proceeds of these issuances were or will be used for general corporate purposes, which may include, among other things, funding for working
capital, capital expenditures, repurchases of capital stock, acquisitions, and repayment of existing debt. Refer to Note 10 – Debt of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).\n\n\n\n43\n\n\nPART II\n\nItem 7",
     "score": 0.5323,
     "subsection": "Debt Proceeds"
    },
    {
     "source": "sec://0001193125-26-323660/7#115",
     "title": "MSFT FY2026 10-K · Item 7 · Share Repurchases",
     "content": "### Share Repurchases\n\nDuring fiscal years 2026 and 2025, we repurchased 36 million shares and 31 million shares of our common stock for $16.7 billion and $13.0 billion, respectively, through our share repurchase program. All repurchases were made using cash resources. As of June
30, 2026, $40.6 billion remained of our $60 billion share repurchase program. Refer to Note 15 – Stockholders’ Equity of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).\n\n\n\n44\n\n\nPART II\n\nItem 7",
     "score": 0.5773,
     "subsection": "Share Repurchases"
    }
   ]
  },
  {
   "ticker": "MSFT",
   "fiscal_year": 2026,
   "item": "Item 8",
   "prelude": "Excerpts from MSFT FY2026 10-K, Item 8 (Financial Statements and Supplementary Data) — 4 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001193125-26-323660/8#149",
     "title": "MSFT FY2026 10-K · Item 8",
     "content": "|  | | | |  |  |  |  |  |  |  |  |  |\n|  |  |  |  |  |  |  |  |  |  |  |  |  |\n| Financing |  |  |  |  |  |  |  |  |  |  |  |  |\n| Proceeds from issuance (repayments) of debt, maturities of 90 days or less, net |  |  | 0 |  |  |  | (5,746 | ) |  |  | 5,250 |  |\n| Proceeds from
issuance of debt |  |  | 0 |  |  |  | 0 |  |  |  | 24,395 |  |\n| Repayments of debt |  |  | (3,000 | ) |  |  | (3,216 | ) |  |  | (29,070 | ) |\n| Common stock issued |  |  | 2,009 |  |  |  | 2,056 |  |  |  | 2,002 |  |\n| Common stock repurchased |  |  | (22,271 | ) |  |  | (18,420 | ) |  |  |
(17,254 | ) |\n| Common stock cash dividends paid |  |  | (26,445 | ) |  |  | (24,082 | ) |  |  | (21,771 | ) |\n| Other, net |  |  | (2,839 | ) |  |  | (2,291 | ) |  |  | (1,309 | ) |\n|  | | | |  |  |  |  |  |  |  |  |  |\n|  |  |  |  |  |  |  |  |  |  |  |  |  |\n| Net cash used in financing |  |
| (52,546 | ) |  |  | (51,699 | ) |  |  | (37,757 | ) |\n|  | | | |  |  |  |  |  |  |  |  |  |",
     "score": 0.5216
    },
    {
     "source": "sec://0001193125-26-323660/8#284",
     "title": "MSFT FY2026 10-K · Item 8 · Shares Outstanding",
     "content": "### Shares Outstanding\n\nShares of common stock outstanding were as follows:\n\n\n\n\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| (In millions) |  |  | |  |  |  | |  |  |  | |  |\n|  | | | | | | | |
| | | |  |\n|  |  | | | |  | | | |  | | |  |\n| Year Ended June 30, |  | 2026 | |  |  | 2025 | |  |  | 2024 | |  |\n|  |  | | | |  | | | |  | | | |\n| Balance, beginning of year |  |  | 7,434 |  |  |  | 7,434 |  |  |  | 7,432 |  |\n| Issued |  |  | 29 |  |  |  | 31 |  |  |  | 34 |  |\n| Repurchased
|  |  | (36 | ) |  |  | (31 | ) |  |  | (32 | ) |\n|  | | | |  |  |  |  |  |  |  |  |  |\n|  | | | |  |  |  |  |  |  |  |  |  |\n| Balance, end of year |  |  | 7,427 |  |  |  | 7,434 |  |  |  | 7,434 |  |\n|  |  |  |  |  |  |  |  |  |  |  |  |  |",
     "score": 0.4938,
     "subsection": "Shares Outstanding"
    },
    {
     "source": "sec://0001193125-26-323660/8#285",
     "title": "MSFT FY2026 10-K · Item 8 · Share Repurchases",
     "content": "### Share Repurchases\n\nOn September 14, 2021, our Board of Directors approved a share repurchase program authorizing up to $60.0 billion in share repurchases. This share repurchase program commenced in November 2021 and was completed in April 2025.\n\nOn September 16, 2024, our
Board of Directors approved a share repurchase program authorizing up to $60.0 billion in share repurchases. This share repurchase program commenced in April 2025, following completion of the program approved on September 14, 2021, has no expiration date, and may be terminated at any time. As of
June 30, 2026, $40.6 billion remained of this $60.0 billion share repurchase program.\n\nWe repurchased the following shares of common stock under the share repurchase programs:",
     "score": 0.5268,
     "subsection": "Share Repurchases"
    },
    {
     "source": "sec://0001193125-26-323660/8#288",
     "title": "MSFT FY2026 10-K · Item 8",
     "content": "79\n\n\nPART II\n\nItem 8\n\n\n\n\n\nAll share repurchases were made using cash resources. Shares repurchased during fiscal year 2026 were under the share repurchase program approved on September 16, 2024. Shares repurchased during the fourth quarter of fiscal year 2025 were under
the share repurchase programs approved on September 14, 2021 and September 16, 2024. All other shares repurchased were under the share repurchase program approved on September 14, 2021. The above table excludes shares repurchased to settle employee tax withholding related to the vesting of stock
awards of $5.6 billion, $5.4 billion, and $5.3 billion for fiscal years 2026, 2025, and 2024, respectively.",
     "score": 0.543
    }
   ]
  },
  {
   "ticker": "MSFT",
   "fiscal_year": 2026,
   "item": "_unknown",
   "prelude": "Excerpts from MSFT FY2026 10-K, _unknown — 2 passage(s) in document order.",
   "chunks": [
    {
     "source": "sec://0001193125-26-323660/unknown#74",
     "title": "MSFT FY2026 10-K",
     "content": "All share repurchases were made using cash resources. Our share repurchases may occur through open market purchases or pursuant to a Rule 10b5-1 trading plan. The above table excludes shares repurchased to settle employee tax withholding related to the vesting of stock
awards.\n\nOur Board of Directors declared the following dividends during the fourth quarter of fiscal year 2026:\n\n\n\n\n\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| Declaration
Date |  |  | Record Date |  |  |  | Payment Date |  |  |  | Dividend<br>Per Share |  |  |  | Amount |  |\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | (In millions) |  |\n|  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |\n| June 10, 2026 |  |  | August 20, 2026 |  |  |  | September 10, 2026 |  |  | $ | 0.91 |  |  | $ | 6,759 |  |\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |",
     "score": 0.4816
    },
    {
     "source": "sec://0001193125-26-323660/unknown#75",
     "title": "MSFT FY2026 10-K",
     "content": "We returned $10.2 billion to shareholders in the form of share repurchases and dividends in the fourth quarter of fiscal year 2026. Refer to Note 15 – Stockholders’ Equity of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K) for further discussion regarding share
repurchases and dividends.\n\n\n\n32\n\n\nPART II\n\nItem 6",
     "score": 0.5351
    }
   ]
  }
 ]
}

[tool 3] finnhub_company_basic_financials {"ticker": "GOOGL"}
{
 "ticker": "GOOGL",
 "fiftyTwoWeekHigh": 408.61,
 "fiftyTwoWeekLow": 251.85,
 "peTTM": 15.9302,
 "forwardPE": 21.39245,
 "psTTM": 8.7251,
 "pb": 6.7585,
 "marketCap": 3890240.8,
 "enterpriseValue": 3932494.8,
 "beta": 1.2143896,
 "epsTTM": 19.9118,
 "roeTTM": 50.839999999999996,
 "roaTTM": 35.42,
 "grossMarginTTM": 60.9,
 "netProfitMarginTTM": 54.77,
 "operatingMarginTTM": 33.11,
 "currentRatio": 2.724,
 "quickRatio": 2.6448,
 "debtToEquity": 0.1533,
 "revenueGrowthTTMYoy": 20.05,
 "epsGrowthTTMYoy": 115.31,
 "tenDayAvgVolume": 23.28811
}

[tool 4] finnhub_company_basic_financials {"ticker": "AAPL"}
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

[tool 5] finnhub_company_basic_financials {"ticker": "MSFT"}
{
 "ticker": "MSFT",
 "fiftyTwoWeekHigh": 553.72,
 "fiftyTwoWeekLow": 349.2,
 "peTTM": 29.0385,
 "forwardPE": 24.19122,
 "psTTM": 11.7041,
 "pb": 6.2636,
 "marketCap": 3883872.5,
 "enterpriseValue": 3969825.5,
 "beta": 1.0569117,
 "epsTTM": 17.9466,
 "roeTTM": 33.22,
 "roaTTM": 19.42,
 "grossMarginTTM": 67.94,
 "netProfitMarginTTM": 40.31,
 "operatingMarginTTM": 46.73,
 "currentRatio": 1.2303,
 "quickRatio": 1.2221,
 "debtToEquity": 0.2416,
 "dividendYield": 0.79485,
 "revenueGrowthTTMYoy": 17.79,
 "epsGrowthTTMYoy": 31.56,
 "tenDayAvgVolume": 19.49467
}
----- END EVIDENCE F0006 -----

----- BEGIN ANSWER F0006 -----
**結論：若把「持續回購」與「不把財務風險拉太高」放在一起看，我會排：Google（Alphabet）第一、微軟第二、蘋果第三。**  
但若更重視「回購政策的可預測性與現金流穩定度」，微軟是最均衡的選擇；Google 則是資產負債表最寬裕。

### 1. Google：財務餘裕最大

Alphabet FY2025（截至 2025-12-31）營業活動現金流為 **1,647 億美元**，全年回購 **454 億美元**；回購後仍有很大的現金流空間。[1][2]

Finnhub 基本面資料也顯示，Google 的流動比率 **2.72**、速動比率 **2.64**、負債權益比 **0.15**，三者中流動性與槓桿狀況最好。相較之下，Google FY2025 的有息票據帳面金額為 **485 億美元**，且商業本票餘額為零。[3]

此外，Google 在 2025 年底仍有 **695 億美元**的回購額度可用，代表它不需要為了維持回購而承擔很高的財務槓桿。[4]

**缺點是：** Google 的回購金額彈性較大，FY2025 回購額從前一年的 620 億美元降至 454 億美元；公司也明確表示回購可能因投資機會、現金需求或市場狀況而調整。[2][5]

### 2. 微軟：最均衡、政策可預測性高

微軟 FY2026（截至 2026-06-30）營業活動現金流達 **1,829 億美元**，回購約 **167 億美元**，另支付股利約 **264 億美元**。[6][7]

Finnhub 資料顯示，微軟流動比率 **1.23**、速動比率 **1.22**、負債權益比 **0.24**，雖然不如 Google 寬裕，但仍屬相對保守；其淨利率 **40.31%**、營業利益率 **46.73%**，獲利對資本回饋的支撐很強。

微軟也表示，現金、短期投資、營業現金流與資本市場管道，足以支應營運、股利、回購、債務到期與資本支出，至少涵蓋未來 12 個月及可預見期間。[8] 截至 FY2026 年底，新的 600 億美元回購計畫仍有 **406 億美元**額度。[9]

**所以微軟的特色是：** 回購規模相對不激進，但現金流覆蓋力很強，且公司對未來資本需求的表述最直接。若你要的是「穩定回購、同時保留投資 AI 與資料中心的能力」，微軟可能是最平衡的答案。

### 3. 蘋果：回購能力強，但財務彈性相對較小

蘋果 FY2025（截至 2025-09-27）回購約 **907 億美元**，股利約 **154 億美元**；回購金額遠高於 Google 或微軟。[10]

蘋果管理層表示，現金、約當現金與有價證券合計 **1,324 億美元**，加上營運現金流與債務市場管道，足以支應未來 12 個月及更長期間的現金需求與資本回報計畫。[11]

不過，Finnhub 資料顯示蘋果流動比率約 **1.00**、速動比率約 **0.93**、負債權益比 **0.78**，流動性與槓桿指標明顯不如 Google 和微軟。蘋果 FY2025 也有約 **913 億美元**固定利率票據本金、**80 億美元**商業本票，以及大量供應商採購承諾。[11]

因此，蘋果不是沒有能力回購，而是它的回購更依賴龐大的持續現金流、資本市場與資產配置管理。它目前仍然很強，但在三家公司中，**回購對財務資源的消耗最重，安全緩衝相對較薄**。

### 簡單排名

| 排名 | 公司 | 判斷 |
|---|---|---|
| **1** | **Google** | 流動性最高、槓桿最低，最有餘裕維持回購 |
| **2** | **微軟** | 現金流最強韌、回購較保守，整體最均衡 |
| **3** | **蘋果** | 回購能力最強，但回購規模大、流動性與槓桿指標較弱 |

**我的最終判斷：**  
- 追求**最低財務風險與最大資產負債表餘裕**：選 **Google**。  
- 追求**回購穩定性、現金流品質與成長投資兼顧**：選 **微軟**。  
- 追求**最積極的股東回報**、且能接受較低財務緩衝：才考慮 **蘋果**。  

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
----- END ANSWER F0006 -----
