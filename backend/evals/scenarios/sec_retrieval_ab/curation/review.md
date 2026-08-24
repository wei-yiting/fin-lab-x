# sec_retrieval_ab dataset — human review sheet

Mark decisions in `review.csv` (`approved`: yes/no + optional `reviewer_comment`). Snippet is **bold** inside its span; one sentence of context shown on each side.

## a01 — NVDA Item 1A/Item 7 (multi_passage, passage_first)

- sector: Information Technology / cap: large / FY2026 / detection: markdown_h3, markdown_h3
- **query**: How much went to private startups, and what threatens recovery?
- curation_note: This pair connects NVIDIA’s quantified fiscal 2026 startup investment with the company-specific impairment and total-loss risk of unsuccessful private holdings.

**Evidence 1** — `NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …ty to ramp production supply to the required volume and on a timely basis.   We have made, and expect to continue making, investments that support our technology roadmap and the broader AI ecosystem. In fiscal year 2026, we made the following investments:  •**We invested $17.5 billion in private companies and infrastructure funds, primarily to support early‑stage startups.** These investments include AI model makers that purchase our products directly or through CSPs. Many of these investments are illiquid and non‑marketable. The related early-stage startups may not become profitable in the near term, or at all, and there can be no assurance that we will realize a return on our investments. •We made investments in publicly-held equity securities where the value may fluctuate significantly due to changes in stock prices and could adversely affect our financial results.   •To support th…

**Evidence 2** — `NVDA / 2026 / Item 1A. Risk Factors` / block: Risks Related to Our Global Operating Business

> …continue to invest in companies to further our strategic objectives and to support certain key business initiatives, which could be subject to delays and challenges in obtaining regulatory approvals. Our investments in private companies include early-stage companies still defining their strategic direction. Many of the securities in which we invest are non-marketable and illiquid at the time of our initial investment. **To the extent any of the companies in which we invest are not successful, we could recognize an impairment and/or lose all or part of our investment.** We are finalizing an investment and partnership agreement with OpenAI. There is no assurance that we will enter into an investment and partnership agreement with OpenAI or that a transaction will be…

---

## a02 — DDOG Item 1A (multi_passage, passage_first)

- sector: Information Technology / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Contractual exposure arising from Datadog's platform outage history
- curation_note: These passages connect Datadog’s documented March 2023 outage with customer credits, terminations, reduced renewals, and reputational consequences under its service commitments.

**Evidence 1** — `DDOG / 2025 / Item 1A. Risk Factors` / block: Strategic and Operational Risks

> …19  Our continued growth depends in part on the ability of our existing and potential customers to access our products and platform capabilities at any time and within an acceptable amount of time. We have experienced, and may in the future experience, disruptions, outages, and other performance problems due to a variety of factors, including infrastructure changes, introductions of new functionality, human or software errors, capacity constraints due to an overwhelming number of users accessing our products and platform capabilities simultaneously, denial of service attacks, or other security-related incidents. **For example, in March 2023, our platform experienced widespread outages across multiple products and regions, which was substantially resolved in approximately a day.** It may become increasingly difficult to maintain and improve our performance, especially during peak usage times and as our products and platform capabilities become more complex and our user traffi…

**Evidence 2** — `DDOG / 2025 / Item 1A. Risk Factors` / block: Legal and Regulatory Risks

> …ovide credits for future service or face subscription termination with refunds of prepaid amounts, which would lower our revenue and harm our business, financial condition and results of operations. Our subscription agreements typically contain service-level commitments. If we are unable to meet the stated service-level commitments, including failure to meet the uptime and response time requirements under our customer subscription agreements, we may be contractually obligated to provide these customers with service credits which could significantly affect our revenue in the periods in which the failure occurs and the credits are applied. **We could also face subscription terminations and a reduction in renewals, which could significantly affect both our current and future revenue.** Any service-level failures could also damage our reputation, which could also adversely affect our business, financial condition and results of operations. 26  Indemnity provisions in various agreements to which we are party potentially expose us to substantial liability for infringement, misappropriation or other violation of intellectual property rig…

---

## a05 — JPM Item 1A (multi_passage, passage_first)

- sector: Financials / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How could artificial intelligence reshape staffing needs and employee capabilities?
- curation_note: These passages connect AI adoption risks with staff shortages, skill erosion, displacement, retraining costs, and demand for advanced technical talent.

**Evidence 1** — `JPM / 2025 / Item 1A. Risk Factors` / block: Strategic

> …rs, or  •replacement or disintermediation of direct customer relationships if AI agents autonomously manage or intermediate financial decisions and product selection or other services for customers. **It is also possible that JPMorganChase could miscalibrate its workforce planning and employee training efforts either because of over-reliance on AI or the failure to appropriately adopt AI.** Over-reliance on AI could cause JPMorganChase to experience shortages in qualified staff due to reduced hiring or retention of employees, or could hinder the development or enhancement of important skills among its employees, including critical thinking, problem-solving, judgment, creativity and adaptability. On the other hand, any efficiencies or competitive advantages that AI may offer could be squandered if JPMorganChase fails to adopt AI in a timely and judicious manner and to make related adjustments to its workforce. Any of these factors could materially and adversely affect JPMorganChase’s business and operations, results of operations, competitive position or reputation.  The effects of climate change could ad…

**Evidence 2** — `JPM / 2025 / Item 1A. Risk Factors` / block: People

> …countries could inhibit JPMorganChase’s ability to attract and retain qualified employees, or necessitate adjustments to operating models that could reduce operational efficiency or increase costs. **Advances in technology, such as automation, AI and data science, could lead to workforce displacement.** This could require JPMorganChase to invest in additional employee training, manage impacts on morale and retention, and compete for employment candidates who possess more advanced technological skills, all of which could have a negative impact on JPMorganChase’s business and operations.

---

## p03 — LLY Item 1A (multi_passage, passage_first)

- sector: Health Care / cap: large / FY2025 / detection: markdown_h3, markdown_h3
- **query**: Why do enforcement gaps around illicit incretins threaten Lilly?
- curation_note: These passages connect counterfeit and mass-compounded incretins with the business and reputational consequences of inadequate industry oversight, testing cross-unit causal retrieval.

**Evidence 1** — `LLY / 2025 / Item 1A. Risk Factors` / block: Risks Related to Our Business and Industry

> …ess depends on a market that is observant of intellectual property rights and regulatory requirements. Developments that undermine that landscape can significantly impact our business and reputation. For example, we continue to see the production, marketing, and sale of counterfeit, misbranded, adulterated, and mass-compounded incretins in the U.S. and other markets that could materially impact us. In addition to patient safety concerns, improper commercialization and dispensation practices by these actors may inappropriately condition consumer expectations or otherwise disadvantage compliant market participants. Our actions intended to stop or prevent illegal sales of such medicines are costly and may be ineffective. See Item 1, "Business—Government Regulation of Our Operations and Products," for additional information on market risks related to counterfeit, misbranded, adulterated, and mass-compounded medicines. If inadequately regulated, e-commerce may increase the prevalence of dangerous counterfeit or mass-compounded products and scams, potentially exposing patients to significant risks. **Our reputation and business could suffer harm as a result of counterfeit or mass-compounded drugs sold under our brand name, which may also impact our business and financial results.** In addition, we rely on our ability to attract and retain highly qualified and skilled scientific, technical, management, and other personnel in order to compete effectively. To capitalize on the ra…

**Evidence 2** — `LLY / 2025 / Item 1A. Risk Factors` / block: Risks Related to Doing Business Internationally

> …on in such programs, notwithstanding the review processes involved and our adherence to applicable requirements and procedures, may expose us to legal, regulatory, political, and reputational risks. We rely on the FDA and other global regulatory bodies for appropriate oversight, administration and enforcement across our industry, anyone marketing or purporting to market medicines, and public health. **Oversight, administrative, and enforcement changes, delays, inconsistencies, lapses, and failures could materially impact our business and reputation.** See Item 1, "Business—Government Regulation of Our Operations and Products," for additional information on regulatory risks, including as related to counterfeit, misbranded, adulterated, and mass-compounded drugs. Regulatory oversight and compliance processes in jurisdictions outside the U.S. may be particularly unpredictable and result in additional costs, uncertainties, and risks.  Furthermore, there is a su…

---

## p04 — PODD Item 1A (multi_passage, passage_first)

- sector: Health Care / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: GLP-1 adoption effects on diabetes demand and Insulet shares
- curation_note: These passages connect GLP-1 uptake to delayed type 2 diabetes progression and investor concerns that depressed Insulet’s share price, testing cross-unit synthesis of commercial and valuation risks.

**Evidence 1** — `PODD / 2025 / Item 1A. Risk Factors`

> …duce the potential market for our products or render our products obsolete altogether, which would significantly reduce our sales or cause our sales to grow at a slower rate than we currently expect. **Further, increased availability and adoption of the GLP-1 class of drugs may delay the progression of type 2 diabetes in obese patients.** In addition, even the perception that new products may be introduced, or that technological or treatment advancements could occur, could cause consumers to delay the purchase of our products or impact our stock price. Future market or clinical studies may be unfavorable to our Omnipod products and their efficacy, which could hinder our sales efforts and have a material adverse effect on our business, results of…

**Evidence 2** — `PODD / 2025 / Item 1A. Risk Factors` / block: The price of our common stock may be volatile.

> …the U.S. equity markets have at times experienced significant price and volume fluctuations that have affected the market prices of equity securities of many medical device and technology companies. Also, in 2023, ongoing adoption of the GLP-1 class of drugs in diabetes and news surrounding the expansion of use of GLP-1 drugs in obesity led to speculation regarding the impact of GLP-1 drugs on the insulin therapy market. **We believe this negatively impacted the stock prices of companies in the medical device industry, including ours.** Broad market and industry factors such as these could materially and adversely affect the market price of our stock, regardless of our actual operating performance.  Changes in tax laws or exposures…

---

## p05 — JPM Item 1A (multi_passage, passage_first)

- sector: Financials / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How can rising rates trigger loan losses and capital constraints?
- curation_note: These passages connect variable-rate borrower distress to losses and higher risk-weighted assets that may restrict JPMorganChase’s capital deployment.

**Evidence 1** — `JPM / 2025 / Item 1A. Risk Factors` / block: Market

> …gher funding costs.  All of these outcomes could adversely affect JPMorganChase’s earnings or its liquidity and capital levels, with more severe impacts in a prolonged period of high interest rates. **Higher interest rates could also negatively affect the payment performance on loans within JPMorganChase’s consumer and wholesale loan portfolios that are linked to variable interest rates.** If borrowers of variable rate loans reduce or stop making payments at higher interest rates, JPMorganChase could incur losses as well as increased operational costs related to servicing a higher volume of delinquent loans. On the other hand, a low or negative interest rate environment could cause:  •compressed net interest margins, which could result in lower earnings on JPMorganChase’s investment securities portfolio…

**Evidence 2** — `JPM / 2025 / Item 1A. Risk Factors` / block: Capital

> **JPMorganChase’s ability to distribute capital to shareholders, and to support its business activities could be limited if it does not satisfy applicable regulatory capital requirements.**  JPMorganChase is subject to various regulatory capital requirements, and the amount of capital that it is required to hold under those requirements could increase at any given time due to factors such as:  19  Part I  •actions by banking regulators, as well as changes in applicable law or how applicable law is implemented by banking regulators  •changes in the composition of JPMorganChase’s balance sheet or developments that could increase RWA, such as increased market risk, customer delinquencies, client credit rating downgrades or other factors, and  •increases in estimated stress losses as determined by the Federal Reserve under CCAR, which could increase JPMorganChase’s SCB. Although more likely in times of stress, JPMorganChase may use its regulatory capital buffers allowing capital ratios to decline below regulatory requirements, subjecting it to restrictions on capit…

---

## p06 — COIN Item 1A (multi_passage, passage_first)

- sector: Financials / cap: mid / FY2025 / detection: text_fallback, text_fallback
- **query**: How did Deribit deepen Coinbase's vulnerability to cyberattacks?
- curation_note: This pair connects Deribit’s addition of derivatives offerings to the heightened third-party attack surface created as Coinbase expands those products.

**Evidence 1** — `COIN / 2025 / Item 1A. Risk Factors` / block: •place us at a competitive disadvantage compared to our less leveraged competitors; and

> …have made, and may continue to make, acquisitions of and investments in, among other   51   things, specialized employees and complementary companies, products, services, licenses, or technologies. **For example, as a result of our acquisition of Deribit in August 2025, we now provide additional cryptocurrency products and services internationally, including options and perpetual swaps.** If we are unable to successfully integrate Deribit or comply with evolving U.S. and international crypto and derivatives regulations applicable to our expanded operations and products, we could be required to modify or discontinue certain offerings, face limitations on our ability to onboard or serve customers in key markets, incur substantial compliance and remediation costs, or be subject to penalties and other enforcement actions, any of which could adversely affect our business, operating results, and financial condition. In the future, the pace and scale of our acquisitions may increase and may include larger acquisitions than we have done historically. We also invest in companies and technologies, many of which are…

**Evidence 2** — `COIN / 2025 / Item 1A. Risk Factors` / block: The Most Material Risks Related to Our Business and Financial Position

> …disclosing usernames, passwords, payment card information, or other sensitive information, which may in turn be   28   used to access our information technology systems and customers’ crypto assets. **As we grow our offering of products and services, including options and perpetual swaps, we face increased exposure to cyberattacks through third parties.** Threats can come from a variety of sources, including criminal hackers, hacktivists, state-sponsored intrusions, industrial espionage, and insiders. Certain threat actors may be supported by significant financial and technological resources, making them even more sophisticated and difficult to detect. We may also acquire other companies that expo…

---

## p07 — AMZN Item 1A (multi_passage, passage_first)

- sector: Consumer Discretionary / cap: large / FY2025 / detection: markdown_h3, markdown_h3
- **query**: What risks arise from unprofitable AI investments and scarce GPUs?
- curation_note: This pairing tests retrieval of Amazon’s potential technology investment write-offs alongside GPU supply constraints affecting AI development and operations.

**Evidence 1** — `AMZN / 2025 / Item 1A. Risk Factors` / block: Business and Industry Risks

> …icult technology challenges, may subject us to claims if customers of these offerings experience, or are otherwise impacted by, service disruptions, delays, setbacks, or failures or   quality issues. In addition, profitability or other intended benefits, if any, in our newer activities (including development and adoption of automation, artificial intelligence, and machine learning technologies for customer and internal use), may not meet our expectations, and we may not be successful enough in these newer activities to recoup our investments in them, which investments are often significant. **Failure to realize the benefits of amounts we invest in new technologies, products, or services could result in the value of those investments being written down or written off.** In addition, our sustainability initiatives may be unsuccessful for a variety of reasons, including if we are unable to realize the expected benefits of new technologies or if we do not successfully…

**Evidence 2** — `AMZN / 2025 / Item 1A. Risk Factors` / block: Our International Operations Expose Us to a Number of Risks

> …vents, labor and trade disputes, or for other reasons, may result in our being unable to procure alternatives from other suppliers in a timely and efficient manner and on acceptable terms, or at all. For example, we rely on a limited group of suppliers for semiconductor products, including products related to artificial intelligence infrastructure such as graphics processing units. **Constraints on the availability of these products could adversely affect our ability to develop and operate artificial intelligence technologies, products, or services.** In addition, violations by our suppliers or other vendors of applicable laws, regulations, contractual terms, intellectual property rights of others, or our Supply Chain Standards, as well as product…

---

## p08 — DECK Item 1A (multi_passage, passage_first)

- sector: Consumer Discretionary / cap: mid / FY2026 / detection: markdown_h4, markdown_h4
- **query**: Key partner and sheepskin processor concentration vulnerabilities
- curation_note: These passages pair dependence on limited manufacturing partners with UGG sheepskin's reliance on two qualifying Chinese tanneries, testing retrieval across distinct supply-chain concentration risks.

**Evidence 1** — `DECK / 2026 / Item 1A. Risk Factors` / block: have a material adverse effect on our business.

> …manufacturers’ inability to meet these expectations could adversely affect our ability to manufacture products or   fulfill customer orders, which could negatively affect our results of operations. Table of Contents                                                                                                                                                         16  There can be no assurance of a long-term, uninterrupted supply of products from our independent manufacturers.   **Our dependence on a limited number of key manufacturing partners may increase our exposure to disruptions,   pricing changes, or capacity constraints.** While we have long-standing relationships with most of these   manufacturers, they could terminate our engagement, seek to increase their prices, or extract other concessions   from us, and we may not be able to timely engage a suitable alternative. If we are required to find alternative   manufacturers, we could experience manufacturing delays, increased manufacturing costs, and substantial   disruption to our business, any of which could negatively affect our results of operations. Interruptions in the supply of our products can also result from adverse events that impair our manufacturers’   operations. For example, we keep proprietary materials necessary to produce our produ…

**Evidence 2** — `DECK / 2026 / Item 1A. Risk Factors` / block: effect on our business.

> We purchase raw materials and components that are subject to supplier and geographic concentration, most   significantly sheepskin, which is used in a substantial portion of our UGG brand products. **Sheepskin is in high   demand and sourced primarily from Australia and processed largely by two tanneries in China capable of meeting   our quality, volume, and animal welfare standards.** This geographic and supplier concentration exposes us to supply   disruption risk. We also rely on designated suppliers for certain other specialized raw materials, including   sugarcane-derived EVA, used in certain components of our products.  If suppliers of sheepskin, including…

---

## p09 — GOOGL Item 1A (multi_passage, passage_first)

- sector: Communication Services / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How laws complicate Alphabet's content and youth-safety controls
- curation_note: The evidence links legal constraints on filtering poor-quality material with child-safety mandates requiring product changes and monitoring, testing cross-unit retrieval of regulatory effects on platform governance.

**Evidence 1** — `GOOGL / 2025 / Item 1A. Risk Factors` / block: Risks Related to our Industry

> …rging threats, there is no guarantee that our technology and policy enforcement will always be successful, and our users may have negative experiences that make them less likely to use our platforms. **We face legal and regulatory challenges to our efforts to address low-quality content, and our ability to address it may be constrained or made more costly through added compliance requirements.** We also face other challenges to the quality of our search results from low-quality and irrelevant content websites, including content farms, which are websites that generate large quantities of low-…

**Evidence 2** — `GOOGL / 2025 / Item 1A. Risk Factors` / block: Risks Related to Laws, Regulations, and Policies

> …for services like Google Search and YouTube to detect and limit low-quality, deceptive, or harmful content, or, on the other hand, may impinge on the rights of free expression and access to content. Additionally, new regulations apply to online child safety, including access and content restrictions as well as other limitations for minors, which may also conflict with rights of free expression and access to information. **These regulations could result in our having to modify our products and services and monitor minors' experiences on our products and services.** •Consumer protection: Consumer protection laws, including the EU's New Deal for Consumers, which could result in monetary penalties and create a range of new compliance obligations.  In addition, th…

---

## p10 — CAT Item 1A (multi_passage, passage_first)

- sector: Industrials / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Cat Financial contingency funding and Dodd-Frank compliance burdens
- curation_note: These passages pair Cat Financial’s fallback liquidity options with its specific Dodd-Frank regulatory exposure, testing retrieval across distinct financial and legal risk sections.

**Evidence 1** — `CAT / 2025 / Item 1A. Risk Factors` / block: FINANCIAL RISKS

> …financial condition.  Continuing to meet Cat Financial's cash requirements over the long-term could require substantial liquidity and access to sources of funds, including capital and credit markets. Cat Financial has continued to maintain access to key global medium-term note and commercial paper markets, but there can be no assurance that such markets will continue to represent a reliable source of financing. If global economic conditions were to deteriorate, Cat Financial could face materially higher financing costs, become unable to access adequate funding to operate and grow its business and/or meet its debt service obligations as they mature.  **Cat Financial also could be required to draw upon contractually committed lending agreements and/or seek other funding sources.**  However, there can be no assurance that such agreements and other funding sources would be sufficient or even available under extreme market conditions. Any of these events could negatively impact Cat Financial’s business, as well as our and Cat Financial's results of operations and financial condition.   Market disruption and volatility may also le…

**Evidence 2** — `CAT / 2025 / Item 1A. Risk Factors` / block: LEGAL & REGULATORY RISKS

> …al.  Cat Financial’s operations are highly regulated by governmental authorities in the locations where it operates, which can impose significant additional costs and/or restrictions on its business. In the United States, for example, certain Cat Financial activities are subject to the U.S. **Dodd-Frank Wall Street Reform and Consumer Protection Act (Dodd-Frank), which includes extensive provisions regulating the financial services industry.** As a result, Cat Financial has become and could continue to become subject to additional regulatory costs that could be significant and have an adverse effect on Cat Financial’s and our results of operations and financial condition. Changes in regulations or additional regulations in the United States or internationally impacting the financial services industry could also add significant cost or operational constraints that might have an adverse effect on Cat Financial’s and our results of operations and financial condition. 18   We are subject to stringent environmental laws and regulations that impose significant compliance costs.  Our facilities, operations and products are subject to increasingly stringent environm…

---

## p11 — AXON Item 1A (multi_passage, passage_first)

- sector: Industrials / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Operational failures and IP litigation arising from Axon's AI use
- curation_note: These passages connect high-stakes defects in Axon's AI systems with increased infringement claims and costly technology or licensing remedies.

**Evidence 1** — `AXON / 2025 / Item 1A. Risk Factors` / block: Operational Risks

> …I-based technologies for internal use to drive efficiency. As with many new and emerging technologies, AI presents numerous risks and challenges to our internal business operations and our customers. **For example, unexpected failures or inaccuracies in AI-driven systems could expose our customers to operational risks, particularly in high-stakes use cases such as law enforcement or public safety.**  The development, adoption, integration and use of generative AI technology remains in the early stages and consequently, our AI technology may contain material defects or errors. Additionally, ineffective or inadequate AI or generative AI governance, development, use or deployment practices, including businesses we have acquired. or third parties could result in unintended co…

**Evidence 2** — `AXON / 2025 / Item 1A. Risk Factors` / block: Legal and Compliance Risks

> …product categories, and otherwise offer new products, services and technologies, additional intellectual property claims may be filed against us by these companies, entities and other third parties. **Our use of AI tools may also increase the likelihood of intellectual property claims.** Intellectual property claims may also be filed against us as our current products, services and technologies gain additional market share.   If our products, services or technologies were found to infringe a third party’s proprietary rights, we could be forced to discontinue use of the protected technology or enter into costly royalty or licensing agreements to be able to sell our products, services or technologies. Such royalty and licensing agreements may not be available on terms acceptable to us or at all. We could also be required to pay substantial damages, fines or other penalties, indemnify customers or distributors, cease the manufacture, use or sale of infringing products or processes and/or expend significant resources to develop or acquire non-infringing technologies. Our suppliers may not provide, or we may not be able to obtain, intellectual property indemnification sufficient to offset all damages, fines or other penalties resulting from any claims of intellect…

---

## p12 — COST Item 1A (multi_passage, passage_first)

- sector: Consumer Staples / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How large is Costco's overseas footprint, and how may expansion affect currency risk?
- curation_note: This pair links Costco's quantified non-U.S. warehouse presence and expansion plans with the resulting increase in foreign-currency exposure.

**Evidence 1** — `COST / 2025 / Item 1A. Risk Factors` / block: Legal and Regulatory Risks

> …unting, regulatory, political and economic factors specific to the countries or regions in which we operate, which could adversely affect our business, financial condition and results of operations. **At the end of 2025, we operated 285 warehouses outside of the U.S. (31% of all warehouse locations), and we plan to continue expanding our international operations.** Future operating results internationally could be negatively affected by a variety of factors, many similar to those we face in the U.S., certain of which are beyond our control. These factors include political and economic conditions, regulatory constraints, currency regulations, policy changes, and other matters in any of the countries or regions in which we operate, now or…

**Evidence 2** — `COST / 2025 / Item 1A. Risk Factors` / block: Market and Other External Risks

> …da, generated 27% and 34% of our net sales and operating income. Our international operations have accounted for an increasing portion of our warehouses, and we plan to continue international growth. To prepare our consolidated financial statements, we translate the financial statements of our international operations from local currencies into U.S. dollars using current exchange rates. Future fluctuations in exchange rates that are unfavorable to us may adversely affect the financial performance of our Canadian and Other International operations and have a corresponding adverse period-over-period effect on our results of operations. **As we continue to expand internationally, our exposure to fluctuations in foreign-exchange rates may increase.** A portion of the products we purchase is paid for in a currency other than the local currency of the country in which the goods are sold. Currency fluctuations may increase our merchandise costs and…

---

## p14 — NEE Item 1A (multi_passage, passage_first)

- sector: Utilities / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Duane Arnold revival dependencies and financial effects of nuclear mandates
- curation_note: This evidence connects NEER’s Duane Arnold restart approvals with the cost and revenue consequences of changing NRC requirements, testing retrieval across development and nuclear-risk units.

**Evidence 1** — `NEE / 2025 / Item 1A. Risk Factors` / block: Development and Operational Risks

> …ns have caused   26   minor, and could in the future cause material, disruptions in the ability of NEE and FPL to acquire certain generation equipment and batteries on time and at acceptable costs. **Additionally, NEER is actively pursuing the restart of the Duane Arnold nuclear generation facility.** The restart is subject to certain regulatory approvals, including NRC safety and environmental reviews, as well as permits from relevant state and local agencies. NEER has applied to the NRC to reinstate the operating license and to MISO for an interconnection agreement. Failure to obtain the necessary approvals could result in the impairment of amounts capitalized. Further, NEE could encounter difficulty in procuring or restoring specialized components which could impact the restart timeline. NEE could incur costs greater than expected or encounter unforeseen i…

**Evidence 2** — `NEE / 2025 / Item 1A. Risk Factors` / block: Nuclear Generation Risks

> …safety requirements promulgated by the NRC could require NEE and FPL to incur substantial operating and capital expenditures at their nuclear generation facilities and/or result in reduced revenues. The NRC has broad authority to impose licensing and safety-related requirements for the operation and maintenance of nuclear generation facilities, the addition of capacity at existing nuclear generation facilities and the construction of new nuclear generation facilities, and these requirements are subject to change. In the event of non-compliance, the NRC has the authority to impose fines and/or shut down a nuclear generation facility, depending upon the NRC's assessment of the severity of the situation, until compliance is achieved. **Any of the foregoing events could require NEE and FPL to incur increased costs and capital expenditures, and could reduce revenues.** Any serious nuclear incident occurring at a NEE or FPL plant could result in substantial remediation costs and other expenses. A major incident at a nuclear facility anywhere in the world could caus…

---

## p15 — PLD Item 1A (multi_passage, passage_first)

- sector: Real Estate / cap: large / FY2025 / detection: text_fallback, text_fallback
- **query**: Which portfolio region faces both business slowdowns and earthquake exposure?
- curation_note: This pair tests retrieval across disclosures linking California’s economic vulnerability with the seismic exposure of Prologis properties there.

**Evidence 1** — `PLD / 2025 / Item 1A. Risk Factors` / block: Risks Related to our Business

> …international geographies in which we own properties. Our operating performance is further impacted by the economic conditions of the specific markets in which we have concentrations of properties. At December 31, 2025, 30.6% of our consolidated operating properties or $24.7 billion (based on consolidated gross book value, or investment before depreciation) were located in California (Central Valley, San Francisco Bay Area and Southern California markets), which represented 23.6% of the aggregate square footage of our operating properties and 31.9% of our consolidated operating property NOI. Our revenues from, and the value of, our properties located in California may be affected by local real estate conditions (such as an oversupply of or reduced demand for logistics properties) and the local economic climate. **Business layoffs, downsizing, industry slowdowns, changing demographics and other factors may adversely impact California’s economic climate.** Because of the investment we have located in California, a downturn in California’s economy or real estate conditions, including state income tax and property tax laws, could adversely affect our business. In addition to California, we also have significant holdings (defined as more than 3% of total consolidated investment before depreciation) in operating properties in certain markets located in Atl…

**Evidence 2** — `PLD / 2025 / Item 1A. Risk Factors` / block: •we may experience delays (temporary or permanent) if there is public or government opposition to our activities; and

> …debt, then we would remain obligated for any mortgage debt or other financial obligations related to the properties. Any such losses or higher insurance costs could adversely affect our business. 19     A number of our investments, both wholly owned and owned through co-investment ventures, are located in areas that are known to be subject to earthquake activity. **U.S. properties located in active seismic areas include properties in our markets in California and Washington.** International properties located in active seismic areas include Japan and Mexico. We generally carry earthquake insurance on our properties located in areas historically subject to seismic activity, subject to coverage limitations and deductibles, if we believe it is commercially…

---

## p16 — LIN Item 7 (passage, intent_first)

- sector: Materials / cap: large / FY2025 / detection: markdown_h4
- **query**: Linde project exposure to materials, staffing, inflation, and scope changes
- user_intent: what supply chain risks does the company face
- curation_note: This passage captures Linde-specific engineering delivery risks involving input and labor estimates, construction duration, technical complexity, inflation, and changing scope.

**Evidence 1** — `LIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Revenue Recognition

> …t of such change. We assess performance as progress towards completion is achieved on specific projects, earnings will be impacted by changes to our forecast of revenues and costs on these projects. The cost incurred input method places considerable importance on accurate estimates of the extent of progress towards completion and may involve estimates on the scope of deliveries and services required to fulfill the contractually defined obligations. **The key source of estimation uncertainty is the total estimated costs at completion including material, labor and overhead costs and the resultant state of completion of the contracts.** There are inherent uncertainties associated with the estimation process, including technical complexity, duration of construction cycle, potential cost inflation (whether equipment or manpower), and scope considerations all of which may affect the total estimation process. Changes in these estimates may lead to a significant impact on future financial statements.

---

## p17 — NVDA Item 7 (passage, intent_first)

- sector: Information Technology / cap: large / FY2026 / detection: markdown_h3
- **query**: NVIDIA reliance on large downstream buyers and AI lab demand
- user_intent: how concentrated is the company's customer base
- curation_note: This passage identifies concentrated indirect-buyer exposure and a meaningful fiscal 2026 contribution linked to one AI company, testing retrieval beyond direct-customer percentages.

**Evidence 1** — `NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Results of Operations

> …utable to the Compute & Networking segment.  For fiscal year 2024, sales to one direct customer represented 13% of total revenue, and were primarily attributable to the Compute & Networking segment. Indirect Customers – Indirect customer revenue is an estimation based upon multiple factors including customer purchase order information, product specifications, internal sales data, and other sources. Indirect customers primarily purchase our products through system integrators and distributors. We generate a significant amount of our revenue from a limited number of indirect customers, some individually representing 10% or more of our revenue. Certain companies purchase cloud and related services through various direct and indirect customers. **We estimate that one AI research and deployment company contributed to a meaningful amount of our revenue purchasing cloud services from our customers in fiscal year 2026.** Revenue by geographic region is designated based on the location of the headquarters of direct customers. The end customer and shipping location may be different from our customers' headquarters loc…

---

## p18 — DDOG Item 7 (passage, intent_first)

- sector: Information Technology / cap: mid / FY2025 / detection: markdown_h3
- **query**: How can trade barriers affect Datadog’s growth and results?
- user_intent: how do export controls or trade restrictions affect the business
- curation_note: This passage links restrictive trade policies to economic uncertainty that may weaken Datadog’s growth and operating performance.

**Evidence 1** — `DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …illion, $775.1 million and $597.5 million for the years ended December 31, 2025, 2024 and 2023, respectively. See the section titled “—Liquidity and Capital Resources—Non-GAAP Free Cash Flow” below. **Unfavorable conditions in the economy both in the United States and abroad may negatively affect the growth of our business and our results of operations.** For example, macroeconomic events including changes in trade policies, such as trade wars, tariffs or other trade restrictions or the threat of such actions, fluctuating inflation and interest rates, and the conflicts in Ukraine and the Middle East have led to economic uncertainty. Historically, during periods of economic uncertainty and downturns, businesses may slow spending on information technology, which may impact our business and our customers’ businesses.  Due to our su…

---

## p19 — LLY Item 7 (passage, intent_first)

- sector: Health Care / cap: large / FY2025 / detection: markdown_h3
- **query**: competitive threats facing Lilly’s incretin franchise
- user_intent: what competitive pressures does the company highlight
- curation_note: This passage identifies both an evolving cardiometabolic treatment landscape and counterfeit or mass-compounded incretins, testing retrieval of product-specific competitive pressures.

**Evidence 1** — `LLY / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Financial Results

> …new incretin channels and markets. More generally, incretin volume fluctuations due to channel dynamics or demand can have a disproportionate impact on our results of operations in any given period. Longer term, the durability of our cardiometabolic health product offerings and sustainability of our growth and prospects will depend on our ability to maintain or strengthen our competitive position as the therapeutic landscape evolves and to deliver further innovations that provide sufficient value to sustain our growth momentum.  **We continue to see the production, marketing, and sale of counterfeit, misbranded, adulterated, and mass-compounded incretins.** These practices may impact patient safety and undermine regulatory drug approval processes. While the FDA confirmed in late 2024 that the previous shortage of tirzepatide had ended and that compounding pharmacies are required to cease mass production, we cannot guarantee adequate regulation or compliance. Lilly will continue to consider all options, including filing lawsuits where appropriate, to address unlawful practices and the patient safety risks of unapproved, untested, and manipulated drugs. 47  Tax Matters  We are subject to income taxes and various other taxes in the U.S. and in many foreign jurisdictions; therefore, changes in both domestic and international tax laws or regulations h…

---

## p20 — PODD Item 7 (passage, intent_first)

- sector: Health Care / cap: mid / FY2025 / detection: markdown_h3
- **query**: What threatens collection of the EOFlow trade-secret award?
- user_intent: what regulatory or legal challenges could hurt the business
- curation_note: This passage identifies a company-specific legal judgment and tests retrieval of appeal and collectability risks that could prevent Insulet from realizing the award.

**Evidence 1** — `PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Liquidity and Capital Resources

> …s for purchases of goods or services in the normal course of business. These commitments are derived from purchase orders, supplier contracts, and open orders based on projected demand information. Legal Proceedings—In December 2024, a jury found that EOFlow Co., Ltd. (“EOFlow”) and several other defendants misappropriated certain of our trade secrets and awarded us $452 million in damages. The Court subsequently upheld the jury verdict and further entered a permanent worldwide injunction. In view of the scope of the permanent injunction, the Court reduced our monetary award to $59.4 million to avoid a double recovery. **We have not recorded the damages awarded in our consolidated statements of income as EOFlow has appealed and EOFlow’s ability to satisfy the damages award is uncertain.** Refer to Note 16 to our consolidated financial statements for additional information regarding this matter.  Critical Accounting Policies and Estimates  The preparation of our consolidated financial…

---

## p21 — COIN Item 7 (passage, intent_first)

- sector: Financials / cap: mid / FY2025 / detection: markdown_h4
- **query**: Coinbase domestic versus overseas revenue mix and foreign revenue source
- user_intent: how exposed is the company to China or other foreign markets
- curation_note: This passage quantifies Coinbase’s geographic revenue concentration and identifies the main type of revenue earned internationally.

**Evidence 1** — `COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Results of Operations

> Comparison of the years ended December 31, 2025 and 2024  Revenue  **For the years ended December 31, 2025 and 2024 we generated 84% and 83%, respectively, of total revenue in the U.S., with no other country contributing over 10%.** International revenue comprised mainly transaction revenue. Transaction revenue  Year Ended December 31,Change  (in thousands, except %)  20252024$%  Consumer, net$3,322,835 $3,430,322 $(107,487)(3)  Institutional, net479,667 345,598 134,069 39   Other trans…

---

## p22 — AMZN Item 7 (passage, intent_first)

- sector: Consumer Discretionary / cap: large / FY2025 / detection: markdown_h3
- **query**: Factors behind Amazon's 2025 overseas retail and cloud revenue gains
- user_intent: what is driving the company's revenue growth
- curation_note: This passage captures distinct growth drivers for Amazon’s International and AWS businesses, testing retrieval across adjacent segment discussions.

**Evidence 1** — `AMZN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …nued focus on price, selection, and convenience for our customers, including from our fast shipping offers. Changes in foreign exchange rates reduced North America net sales by $454 million in 2025. International sales increased 13% in 2025, compared to the prior year. The sales growth primarily reflects increased unit sales, including sales by third-party sellers, advertising sales, and subscription services. Increased unit sales were driven largely   24   by our continued focus on price, selection, and convenience for our customers, including from our fast shipping offers. Changes in foreign exchange rates increased International net sales by $4.9 billion in 2025.  AWS sales increased 20% in 2025, compared to the prior year. **The sales growth primarily reflects increased customer usage, partially offset by pricing changes primarily driven by long-term customer contracts.** Operating Expenses  Information about operating expenses is as follows (in millions):    Year Ended December 31,    20242025  Operating Expenses:  Cost of sales$326,288 $356,414   Fulfillment98,505…

---

## p23 — DECK Item 7 (passage, passage_first)

- sector: Consumer Discretionary / cap: mid / FY2026 / detection: text_fallback
- **query**: Deckers fiscal 2026 supplemental sales growth and unit-volume metrics
- curation_note: This passage consolidates constant-currency growth, comparable direct-channel performance, and unit-volume data, testing retrieval of related supplemental operating metrics.

**Evidence 1** — `DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Supplemental Disclosure

> •On a constant currency basis, net sales increased by 9.0%, compared to the prior period.  •Comparable DTC channel net sales for the 52 weeks ended March 29, 2026, increased by 4.6%,   compared to the prior period.  **•We experienced an increase of 6.2% in the total volume of units sold to 78,700 from 74,100,   compared to the prior period.** Units sold include all categories such as footwear, apparel,   accessories, home goods, and care kits across all brands. Percentages may not calculate on   rounded units. Table of Contents                                                                                                                                                         38  Gross Profit. Gross marg…

---

## p24 — GOOGL Item 7 (passage, intent_first)

- sector: Communication Services / cap: large / FY2025 / detection: markdown_h3
- **query**: How did Alphabet vary debt by denomination and coupon structure?
- user_intent: how does the company manage interest rate or currency exposure
- curation_note: This passage details Alphabet’s mix of dollar and euro borrowings and fixed versus floating coupons, testing retrieval of concrete financing choices relevant to currency and interest-rate exposure.

**Evidence 1** — `GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Liquidity and Material Cash Requirements

> …•May 2025: We issued $5.0 billion of US dollar-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 4.89%, and a weighted-average maturity of approximately 24 years. **We also issued €6.75 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.31%, and a weighted-average maturity of approximately 14 years.**   •November 2025: We issued $500 million of US dollar-denominated floating-rate senior unsecured notes and $17.0 billion of US dollar-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 4.92% and a weighted-average maturity of approximately 20 years. We also issued €6.5 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.44% and a weighted-average maturity of approximately 16 years. As of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring in April 2026 and $6.0 billion expiring in April 2030. No amounts have been borrowed under the cre…

---

## p25 — CAT Item 7 (passage, passage_first)

- sector: Industrials / cap: large / FY2025 / detection: markdown_h3
- **query**: How much could tariffs cost without planned mitigation?
- curation_note: This passage quantifies Caterpillar’s 2026 tariff exposure and the additional downside if its countermeasures are not implemented.

**Evidence 1** — `CAT / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: OVERVIEW

> …t of sales and revenues. We expect machine dealer inventory to increase in 2026 and offset the $500 million decrease in 2025. Services revenues are also expected to grow in 2026 as compared to 2025. Based on the incremental tariffs announced in 2025 and in place by January 29, 2026, we expect the impact from tariffs to be around $2.6 billion in 2026, which is $800 million higher than incurred in 2025. **If we do not take the mitigating actions we plan to take in 2026, the impact from tariffs could be around 20 percent higher.** We remain confident that we will manage the impact of tariffs over time. In 2026, we expect restructuring costs of approximately $300 million to $350 million and capital expenditures of around $3.5 billion. We anticipate our 2026 estimated annual effective tax rate to b…

---

## p26 — AXON Item 7 (passage, passage_first)

- sector: Industrials / cap: mid / FY2025 / detection: markdown_h3
- **query**: What factors drove TASER, Personal Sensors, and Platform Solutions growth?
- curation_note: This evidence captures product-specific growth drivers across all three Connected Devices lines and tests retrieval of a compact comparative operating explanation.

**Evidence 1** — `AXON / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Results of Operations

> …training hardware, and related extended warranties.  Net sales for the Connected Devices segment increased 29.1% for the year ended December 31, 2025 as compared to the year ended December 31, 2024. The increase of $163.7 million in TASER is primarily driven by higher TASER 10 handle and cartridge volume. **Personal Sensors increased $80.1 million, which was primarily driven by the continued adoption of our newest body camera, AB4, and higher warranty revenue from more devices in the field.** The $111.7 million increase in Platform Solutions is primarily driven by higher volume for counter-drone equipment, virtual reality training, and fleet systems. Net sales for the Software and Services segment increased 39.6% for the year ended December 31, 2025 as compared to the year ended December 31, 2024. The increase in the aggregate number of users an…

---

## p27 — COST Item 7 (passage, passage_first)

- sector: Consumer Staples / cap: large / FY2025 / detection: markdown_h3
- **query**: Costco fiscal 2026 capital spending and warehouse expansion plans
- curation_note: This passage combines Costco’s projected fiscal 2026 investment range, funding sources, and planned openings, testing retrieval of a detailed forward capital plan.

**Evidence 1** — `COST / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: LIQUIDITY AND CAPITAL RESOURCES

> …led $5,311 in 2025, compared to $4,409 in 2024, and is primarily related to capital expenditures. Net cash from investing activities also includes purchases and maturities of short-term investments. Capital Expenditure Plans  Our primary requirements for capital are acquiring land, buildings, and equipment for new and remodeled warehouses, information systems, and manufacturing and distribution facilities. **In 2025, we spent $5,498 on capital expenditures, and it is our current intention to spend $6,000 to $6,500 during fiscal 2026.** These expenditures are expected to be financed with cash from operations, cash and cash equivalents, and short-term investments. We opened 27 new warehouses, including three relocations, in 2025, and plan to open up to 35 new warehouses, including five relocations, in 2026. There can be no assurance that current expectations will be realized, and plans are subject to change upon further review of our capital expenditure needs and the economic environment. Cash Flows from Financing Activities  Net cash used in financing activities totaled $3,775 in 2025, compared to $10,764 in 2024. Cash flow used in financing activities primarily related to the payme…

---

## p28 — NEE Item 7 (passage, passage_first)

- sector: Utilities / cap: large / FY2025 / detection: markdown_h4
- **query**: How sensitive were retirement obligations to cost inflation assumptions?
- curation_note: This passage links NEE’s estimation methodology to a quantified $179 million sensitivity from a 0.25% escalation-rate increase.

**Evidence 1** — `NEE / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Decommissioning and Dismantlement

> …missioning and plant dismantlement costs, involves estimating the amount and timing of future expenditures and making judgments concerning whether or not such costs are considered a legal obligation. Estimating the amount and timing of future expenditures includes, among other things, making projections of when assets will be retired and ultimately decommissioned and how costs will escalate with inflation. In addition, NEE also makes interest rate and rate of return projections on its investments in determining recommended funding requirements for nuclear decommissioning costs. Periodically, NEE is required to update these estimates and projections which can affect the annual expense amounts recognized, the liabilities recorded and the annual funding requirements for nuclear decommissioning costs. **For example, an increase of 0.25% in the assumed escalation rates for nuclear decommissioning costs would increase NEE’s AROs as of December 31, 2025 by approximately $179 million.** Assumptions and Accounting Approach  FPL – For ratemaking purposes, FPL accrues and funds for nuclear plant decommissioning costs over the expected service life of each unit based on studies that ar…

---

## p29 — PLD Item 7 (passage, passage_first)

- sector: Real Estate / cap: large / FY2025 / detection: text_fallback
- **query**: Employee allocation and expense timing for venture incentive fees
- curation_note: This passage captures Prologis’s specific 25% employee allocation, award mix, vesting treatment, and potential lag between incentive revenue and expense recognition.

**Evidence 1** — `PLD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Strategic Capital Segment

> …pment projects owned by the venture. Changes in asset valuations within the co-investment ventures during the promote period is one of the significant inputs to the calculation of promote revenues. **The Prologis Promote Plan ("PPP") awards up to 25% of the third-party portion of the promotes earned by us from the co-investment ventures to our employees.** This award is issued as a combination of cash and equity-based awards, pursuant to the terms of the PPP and expensed through Strategic Capital Expenses in the Consolidated Statements of Income, as vested. As a result, expenses recognized in the current period may relate to promote revenues recognized in prior periods.

---

## p30 — LIN Item 7 (passage, passage_first)

- sector: Materials / cap: large / FY2025 / detection: markdown_h4
- **query**: What drove Linde's 2025 investment spending and where was it concentrated?
- curation_note: This evidence captures both the backlog-related purpose and geographic allocation of Linde's capital investment, testing retrieval across adjacent quantitative details.

**Evidence 1** — `LIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Investing

> …Net cash used for investing activities was $5,721 million in 2025 compared to $4,644 million in 2024. The increase was primarily attributable to higher capital expenditures. Capital expenditures in 2025 were $5,261 million, an increase of $764 million from 2024. Capital expenditures during 2025 related primarily to investments in new plant and production equipment for backlog growth requirements.   **30   Approximately 60% of the capital expenditures were in the Americas segment with 21% in the APAC segment and the rest largely in the EMEA segment.** At December 31, 2025, Linde's sale of gas backlog of large projects under construction was approximately $7.3 billion. This represents the total estimated capital cost of large plants under constru…

---

## p31 — XOM Item 1 (passage, passage_first)

- sector: Energy / cap: large / FY2025 / detection: flat
- **query**: How does ExxonMobil cultivate and retain long-tenured career employees?
- curation_note: This evidence links individualized development, roughly 30-year average tenure, and performance-based rewards, testing retrieval of ExxonMobil’s specific workforce strategy.

**Evidence 1** — `XOM / 2025 / Item 1. Business`

> …business environment where decisions and risks play out over time horizons that are often decades in length. This long-term orientation underpins the Corporation's philosophy on talent development. Talent development begins with recruiting exceptional candidates and continues with individually planned experiences and training designed to facilitate broad development and a deep understanding of our business across the business cycle. **Our career-oriented approach to talent development results in strong retention and an average length of service of about 30 years for our career employees.** Compensation, benefits, and workplace programs support the Corporation's talent management approach, and are designed to attract and retain employees for a career through compensation that is market competitive, long-term oriented, and highly differentiated by individual performance. With over 59 percent of our global employees from outside the U.S. and more than 160 nationalities represented across the Company, we encourage and respect diversity of thought, ideas, and perspecti…

---

## p32 — XOM Item 1 (passage, passage_first)

- sector: Energy / cap: large / FY2025 / detection: flat
- **query**: Size and financial importance of ExxonMobil's intellectual property portfolio
- curation_note: This evidence gives a concrete worldwide patent count and clarifies that no single intellectual property right determines segment profitability.

**Evidence 1** — `XOM / 2025 / Item 1. Business`

> …d gas reserves is contained in the “Oil and Gas Reserves” part of the “Supplemental Information on Oil and Gas Exploration and Production Activities” portion of the Financial Section of this report. ExxonMobil has a long-standing commitment to the development of proprietary technology. We have a wide array of research programs designed to meet the needs identified in each of our businesses. **ExxonMobil held over 8 thousand active patents worldwide at the end of 2025.** Although technology is an important contributor to the overall operations and results of our Company, the profitability of each business segment is not dependent on any individual patent, trade secret, trademark, license, franchise, or concession. ExxonMobil operates in a highly complex, competitive, and changing global energy business environment where decisions and risks play out over time horizons that are often decades in length. This lon…

---

## p33 — NVDA Item 1 (passage, passage_first)

- sector: Information Technology / cap: large / FY2026 / detection: markdown_h4
- **query**: Rubin production timeline and token-cost improvement over Blackwell
- curation_note: This evidence pairs Rubin’s expected shipment schedule with its quantified efficiency advantage, testing retrieval of a product roadmap and performance claim.

**Evidence 1** — `NVDA / 2026 / Item 1. Business` / block: Data Center

> …computing workloads with market leading performance and efficiency. Offered in a number of configurations, for customers across industries and a diverse set of AI and accelerated computing use cases. In fiscal year 2026, we unveiled the NVIDIA Rubin platform, which is expected to commence production shipments in the second half of fiscal year 2027. **Built for agentic AI and reasoning, it excels at processing multi-step problem-solving and massive long-context workflows, delivering up to a 10x reduction in cost per token compared to Blackwell.** For physical AI, we provide an end-to-end platform spanning data center infrastructure, open models, systems, embedded compute modules, and software stacks to train, simulate, and deploy advanced a…

---

## p34 — DDOG Item 1 (passage, passage_first)

- sector: Information Technology / cap: mid / FY2025 / detection: markdown_h3
- **query**: How does Datadog identify database bottlenecks and resource constraints?
- curation_note: This passage explains Datadog’s concrete methods for diagnosing slow queries, execution issues, and infrastructure-related database performance problems.

**Evidence 1** — `DDOG / 2025 / Item 1. Business` / block: Overview

> …y and optimize the slowest and most resource-consuming parts in application code in order to improve mean time to resolution, reduce application latency, and lower cloud costs.  •Database Monitoring. Database Monitoring allows customers to view query metrics and explain plans from all of their databases in a single place. **With Database Monitoring, they can quickly pinpoint costly and slow queries and drill into precise execution details to address bottlenecks.** Additionally, query, host, and application metric correlation makes it easy to identify and understand the impact of resource constraints on database performance. •Data Observability. Data Observability brings production-level observability to the data engineering space, and consists of Data Streams Monitoring (DSM) and Data Jobs Monitoring (DJM). DSM enables…

---

## p35 — PODD Item 1 (passage, passage_first)

- sector: Health Care / cap: mid / FY2025 / detection: markdown_h3
- **query**: Insulet next-generation insulin automation development milestones
- curation_note: This evidence captures named pipeline programs, completed studies, enrollment progress, and a planned pivotal trial, testing retrieval of product-development status across a compact passage.

**Evidence 1** — `PODD / 2025 / Item 1. Business` / block: Data Management

> …to the Omnipod 5 algorithm to include a lower target glucose set point.   We also continue to advance work to improve the Omnipod 5 algorithm and simplify the data and insights provided to customers. In addition, we are working to integrate Omnipod 5 with Libre 3 Plus and developing Omnipod 6, our next-generation AID product. In 2025, we completed STRIVE, our pivotal study for the next generation hybrid closed loop system. Further, we continue to develop a fully closed loop AID system for type 2 diabetes (“FCL (T2)”). **In 2025, we completed enrollment for EVOLUTION 2, our safety and feasibility study for FCL (T2) and we plan to start the U.S. investigational device exemption (“IDE”) pivotal study in 2026.** Manufacturing and Quality Assurance   We produce our products at our two highly automated manufacturing facilities in Acton, Massachusetts and Johor, Malaysia. Additionally, we are investing in a th…

---

## p36 — PODD Item 1 (passage, passage_first)

- sector: Health Care / cap: mid / FY2025 / detection: markdown_h3
- **query**: How does Omnipod 5 receive glucose readings and respond?
- curation_note: This evidence explains the product-specific sensor connection and predictive algorithm, testing retrieval of how Omnipod 5 automates insulin adjustments.

**Evidence 1** — `PODD / 2025 / Item 1. Business` / block: Diabetes Management Challenges

> …lable in 19 countries. Additionally, in August 2024, we received FDA clearance for an expanded indication of Omnipod 5 for people with type 2 diabetes (ages 18 years and older) in the United States. Omnipod 5 includes a proprietary AID algorithm embedded in the Pod. **The Pod integrates with a third-party continuous glucose monitor (“CGM”) to obtain glucose values through secure wireless Bluetooth communication.** The embedded algorithm utilizes these glucose values to predict glucose levels into the future and automatically adjusts insulin dosing intended   to improve time-in-range (a dynamic measure of the percentage of time spent in glucose range) and reduce the occurrence of blood glucose highs and lows. The user can also deliver additional insulin doses for snacks or meals or to correct high blood glucose through the system. The Pod can be controlled by an Insulet-provided handheld device or, in the U.S., a user-downloaded Android app or iOS app, with full smartphone compatibility. The Omnipod 5 Controller and the Androi…

---

## p37 — AMZN Item 1 (passage, passage_first)

- sector: Consumer Discretionary / cap: large / FY2025 / detection: markdown_h4
- **query**: How do shoppers reach Amazon offerings, and which electronics does it make?
- curation_note: This evidence combines Amazon-specific customer access channels with its named device portfolio, testing retrieval across two adjacent substantive facts.

**Evidence 1** — `AMZN / 2025 / Item 1. Business` / block: Consumers

> …tores and focus on selection, price, and convenience. We design our stores to enable hundreds of millions of unique products to be sold by us and by third parties across dozens of product categories. Customers access our offerings through our websites, mobile apps, Alexa, devices, streaming, and physically visiting our stores. **We also manufacture and sell electronic devices, including Kindle, Fire tablet, Fire TV, Echo, Ring, Blink, and eero, and we develop and produce media content.** We seek to offer our customers low prices, fast and free delivery, easy-to-use functionality, and timely customer service. In addition, we offer subscription services such as Amazon Prime, a membership program that includes fast, free shipping on tens of millions of items, access to award-winning movies and series, live…

---

## p38 — COIN Item 1 (passage, passage_first)

- sector: Financials / cap: mid / FY2025 / detection: markdown_h4
- **query**: What happens to underlying Ether when cbETH changes hands?
- curation_note: This evidence explains cbETH ownership and transfer mechanics, testing retrieval of a product-specific consequence of selling or transferring the token.

**Evidence 1** — `COIN / 2025 / Item 1. Business` / block: Subscription products and other services

> …vice. As of December 31, 2025, over $15.2 billion worth of assets were staked by institutional customers through Coinbase Prime, as adjusted to USD.    We also operate a cbETH token wrapping service. cbETH is an Ethereum-based “wrapped staking token” that represents ownership of ETH staked through our platform. Eligible customers can obtain cbETH tokens by wrapping their staked ETH or by purchasing cbETH tokens on our exchange or on third-party exchanges. A cbETH holder can sell or transfer their cbETH within the Coinbase app or send cbETH to a self-custodial wallet or to other addresses on the Ethereum blockchain. **Selling or otherwise transferring cbETH automatically transfers ownership of the underlying staked ETH, along with any rewards earned.** There are risks associated with our staking services, which are described in the risk factor in the section titled “Risk Factors” in Part I, Item 1A of this Annual Report on Form 10-K: “We may suffe…

---

## p39 — AMZN Item 1 (passage, passage_first)

- sector: Consumer Discretionary / cap: large / FY2025 / detection: markdown_h4
- **query**: What does Career Choice provide, and how many workers joined?
- curation_note: This evidence combines Amazon’s description of Career Choice’s education benefit with a concrete participation figure, testing retrieval across adjacent sentences.

**Evidence 1** — `AMZN / 2025 / Item 1. Business` / block: Human Capital

> …ial intelligence and machine learning technologies), and constrained labor markets have increased competition for personnel across other parts of our business.  We strive to be Earth’s best employer. We rely on numerous and evolving initiatives to implement this objective and invent mechanisms for talent development, including competitive pay and benefits, flexible work arrangements, and skills training and educational programs such as Amazon Career Choice (education funding for eligible employees). **Over 300,000 Amazon employees around the world have participated in Career Choice.** We also continue to inspect and refine the mechanisms we use to hire, develop, evaluate, and retain our employees. In addition, safety is integral to everything we do at Amazon and we continue to inv…

---

## p40 — DECK Item 1C (passage, passage_first)

- sector: Consumer Discretionary / cap: mid / FY2026 / detection: text_fallback
- **query**: Which security documents undergo periodic refresh, and why?
- curation_note: This evidence identifies the specific policies Deckers updates and links those updates to changing threats and organizational needs.

**Evidence 1** — `DECK / 2026 / Item 1C. Cybersecurity` / block: incidents or breaches and other technology related exposures; and

> **•periodically reviewing and updating our IRP, privacy policy, and other relevant policies/procedures.**  We continuously evaluate and enhance our cybersecurity risk management practices in response to evolving   threats and business needs. In the three-year period ended March 31, 2026, our business, results of operations and financial condition have not…

---

## p41 — GOOGL Item 1C (factoid, passage_first)

- sector: Communication Services / cap: large / FY2025 / detection: flat
- **query**: Who independently evaluates Alphabet's cyber defenses?
- curation_note: This evidence identifies the specific internal function responsible for independent control testing and tests retrieval of Alphabet’s cybersecurity oversight structure.

**Evidence 1** — `GOOGL / 2025 / Item 1C. Cybersecurity`

> …riate, to the full Board for consideration. Senior management regularly discusses cybersecurity risks and trends and, should they arise, any material incidents with the Risk and Compliance Committee. **Internal Audit maintains a dedicated cybersecurity auditing team that independently tests our cybersecurity controls.** Our business strategy, results of operations and financial condition have not been materially affected by risks from cybersecurity threats, including as a result of previously identified cybersecur…

---

## p42 — CAT Item 1C (factoid, passage_first)

- sector: Industrials / cap: large / FY2025 / detection: markdown_h4
- **query**: How frequently does Caterpillar's IT chief attend Audit Committee meetings?
- curation_note: This evidence provides a company-specific meeting cadence and tests retrieval of Caterpillar's cybersecurity governance practices.

**Evidence 1** — `CAT / 2025 / Item 1C. Cybersecurity` / block: Cybersecurity Governance

> …ed to, among other things, the Company’s information security program. The AC assesses cybersecurity and information technology risks and the controls implemented to monitor and mitigate these risks. **The Company’s Chief Information Officer & Senior Vice President, Caterpillar IT (the “CIO”) attends all bimonthly AC meetings and provides cybersecurity updates to the AC and board.** Our cybersecurity program is overseen by our CIO, who has been a Caterpillar employee for over twenty-six years. Prior to her current appointment as our CIO in September 2020, she was the Chief Inf…

---

## p43 — AXON Item 7A (factoid, passage_first)

- sector: Industrials / cap: mid / FY2025 / detection: markdown_h4
- **query**: How much credit could Axon draw at year-end 2025?
- curation_note: This evidence gives Axon’s exact unused borrowing capacity and tests retrieval of a dated liquidity fact.

**Evidence 1** — `AXON / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk` / block: Interest Rate Risk

> …io and consolidated interest coverage ratio. Under the terms of the line of credit, available borrowings are reduced by outstanding letters of credit, which totaled $8.9 million at December 31, 2025. **As of the year ended December 31, 2025, there was no amount outstanding under the line of credit, and the available borrowing under the line of credit was $291.1 million.** We have not borrowed any funds under the line of credit since its inception; however, should we need to do so in the future, such borrowings could be subject to adverse or favorable changes in the un…

---

## p44 — COST Item 7A (factoid, passage_first)

- sector: Consumer Staples / cap: large / FY2025 / detection: text_fallback
- **query**: Impact of one-percentage-point rate shift on Costco investments
- curation_note: This evidence quantifies a company-specific sensitivity scenario and tests retrieval of the resulting valuation impact.

**Evidence 1** — `COST / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk` / block: Interest Rate Risk

> …Our Canadian and Other International subsidiaries’ investments are primarily in money market funds, bankers’ acceptances, and bank certificates of deposit, generally denominated in local currencies. **A 100 basis point change in interest rates as of the end of 2025 would have had an immaterial incremental change in fair market value.** For those investments that are classified as available-for-sale, the unrealized gains or losses related to fluctuations in market volatility and interest rates are reflected within stockholders’ equi…

---

## p45 — DDOG Item 7A (factoid, passage_first)

- sector: Information Technology / cap: mid / FY2025 / detection: markdown_h4
- **query**: Timing and size of Datadog's 2029 debt issuance
- curation_note: This sentence provides a company-specific issuance date and principal amount, testing retrieval of a precise financing fact.

**Evidence 1** — `DDOG / 2025 / Item 7A. Quantitative and Qualitative Disclosures About Market Risk` / block: Interest Rate Risk

> …and the fair market value of our investments. As of December 31, 2025, a hypothetical 10% relative change in interest rates would not have a material impact on our consolidated financial statements. **In December 2024, we issued $1.0 billion aggregate principal amount of the 2029 Notes.** The fair value of the 2029 Notes is subject to interest rate risk, market risk and other factors due to the conversion feature. The fair value of the 2029 Notes will generally increase as our Class A…

---

## p46 — COIN Item 3 (factoid, passage_first)

- sector: Financials / cap: mid / FY2025 / detection: flat
- **query**: Where does Coinbase cross-reference its significant litigation disclosures?
- curation_note: This evidence identifies the precise financial-statement note containing Coinbase's material litigation disclosures, testing cross-reference retrieval.

**Evidence 1** — `COIN / 2025 / Item 3. Legal Proceedings`

> **ITEM 3. LEGAL PROCEEDINGS  For a description of material legal proceedings in which we are involved, see Note 21.** Commitments and Contingencies of the Notes to our Consolidated Financial Statements included in Part II, Item 8 of this Annual Report on Form 10-K, which is incorporated herein by reference.   We are…

---

## p47 — XOM Item 2 (factoid, passage_first)

- sector: Energy / cap: large / FY2025 / detection: markdown_h4
- **query**: Which Brazilian development began producing via an FPSO?
- curation_note: This evidence identifies a named Brazilian project reaching operations and tests retrieval of a specific production start-up.

**Evidence 1** — `XOM / 2025 / Item 2. Properties` / block: B. Review of Principal Ongoing Activities

> …ry legislation by the Minister (typically up to 10 years) and provide for a production period of 20 years for an oil field and 30 years for a gas field, each with a renewal period of up to 10 years. **Brazil commenced operations in the Bacalhau Phase 1 development with the start-up of the floating production, storage and offloading vessel.** Europe  The Pegasus-1 exploratory well was drilled offshore Cyprus and encountered a gas-bearing reservoir. Evaluations are ongoing to develop potential commercialization options.   Africa  ExxonMo…

---

## p48 — PLD Item 5 (factoid, passage_first)

- sector: Real Estate / cap: large / FY2025 / detection: text_fallback
- **query**: Prologis Series Q per-share dividend amount for 2025
- curation_note: This evidence states a precise annual per-share dividend and tests retrieval of a company-specific preferred-stock payment.

**Evidence 1** — `PLD / 2025 / Item 5. Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities` / block: PREFERRED STOCK DIVIDENDS

> …ecember 31, 2025, we had 1.3 million shares of Series Q preferred stock outstanding with a liquidation preference of $50 per share that will be redeemable at our option on or after November 13, 2026. **Dividends payable per share were $4.27 for the year ended December 31, 2025.** For more information regarding dividends, see Note 8 to the Consolidated Financial Statements in Item 8. Financial Statements and Supplementary Data.…

---

## p49 — NVDA Item 9A (factoid, passage_first)

- sector: Information Technology / cap: large / FY2026 / detection: markdown_h3
- **query**: What corporate software modernization initiative is NVIDIA continuing?
- curation_note: This evidence identifies NVIDIA’s phased ERP upgrade and tests retrieval of a specific ongoing financial-systems initiative.

**Evidence 1** — `NVDA / 2026 / Item 9A. Controls and Procedures` / block: Changes in Internal Control Over Financial Reporting

> …control over financial reporting during the quarter ended January 25, 2026 that have materially affected, or are reasonably likely to materially affect, our internal control over financial reporting. **We are continuing a phased upgrade of our enterprise resource planning, or ERP, system to update our existing core financial systems.** The ERP system is designed to accurately maintain our financial records used to report operating results. We will continue to evaluate each quarter whether there are changes that materially affect ou…

---

## p50 — LIN Item 1A (factoid, passage_first)

- sector: Materials / cap: large / FY2025 / detection: flat
- **query**: Have cyber incidents materially affected Linde's performance so far?
- curation_note: This disclosure gives a company-specific historical outcome and tests retrieval of whether prior cyberattacks caused significant harm.

**Evidence 1** — `LIN / 2025 / Item 1A. Risk Factors`

> …s could result in business interruption or malfunction and lead to legal or regulatory actions that could result in a material adverse impact on Linde’s operations, reputation and financial results. **To date, such attempts have not had any significant impact on Linde's operations or financial results.** The inability to effectively integrate acquisitions or collaborate with joint venture partners could adversely impact Linde’s financial position and results of operations.  Linde has evaluated and e…

---

## a03 — LLY Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Health Care / cap: large / FY2025 / detection: markdown_h3, markdown_h3
- **query**: Why are trade levies especially difficult for Lilly to absorb?
- curation_note: The passages connect concentrated sourcing exposure with pharmaceutical-sector limits on recovering higher trade costs, testing causal retrieval across operational and international risks.

**Evidence 1** — `LLY / 2025 / Item 1A. Risk Factors` / block: Risks Related to Our Operations

> …auses, discontinuations, or other product availability issues in one or more markets, which could have a material adverse effect on our consolidated results of operations, cash flows, and reputation. Challenges and disruptions may include (i) actual or perceived quality, oversight, or regulatory compliance problems; (ii) equipment, mechanical, data, or IT system vulnerabilities, such as system inadequacies, inadequate controls or procedures, operating failures, unauthorized access, service interruptions or failures, security breaches, malicious intrusions, theft, exfiltration, ransomware or other cyber-attacks from a variety of sources; (iii) labor deficiencies; (iv) inability to obtain single-source or other raw or intermediate materials; or (v) issues related to contractors and suppliers, including the failure, inability, or refusal of a supplier or contract manufacturer to supply contracted quantities in a timely or compliant manner or at all, increases in demand on a supplier with constrained capacity, contractual disputes with our suppliers and contract manufacturers, and vertical integration by competitors within our supply chain.   **Regional or single-source dependencies may in some cases accentuate risks and costs (e.g., tariffs) related to manufacturing and supply.** For example, we, and the pharmaceutical industry generally, depend on China-based suppliers for portions of our supply chain, including integral chemical synthesis, reagents, starting materials, and…

**Evidence 2** — `LLY / 2025 / Item 1A. Risk Factors` / block: Risks Related to Doing Business Internationally

> …ctions. See Item 1A, "Risk Factors—Risks Related to Our Operations—Reliance on third-party relationships and outsourcing arrangements could adversely affect our business," for additional information. The precise impact of tariffs, trade protection measures, and other restrictions may depend on their ultimate scope, timing, and other factors. If enacted, additional restrictions could result in supply disruptions or delays, further increase costs, or otherwise have a negative impact on our business. **Given the nature of pharmaceutical regulation and commercialization, we may not be able to offset the burden of increased costs from tariffs and related impacts to any meaningful degree.** In most international markets, we operate in an environment of government-mandated cost-containment programs. In some markets, including the EU, Japan, and China, governments have significant power…

---

## a04 — PODD Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Health Care / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Why does Omnipod expansion heighten component sourcing vulnerability?
- curation_note: The passages connect demand-led organizational strain with sole-source components and regulatory obstacles to qualifying replacements.

**Evidence 1** — `PODD / 2025 / Item 1A. Risk Factors`

> …tively manage our rapid growth, our business resources may become strained and we may not be able to deliver our products in a timely manner, which could adversely affect our results of operations. As we continue to expand the number of customers we serve, driven by increasing demand for Omnipod 5, our international expansion and entrance into the insulin-requiring type 2 diabetes market, we expect to continue to increase our manufacturing capacity, our personnel, and the scope of our sales and marketing efforts. **Our growth will create challenges for our organization and may strain our management, operations, and customer service resources.** We may misjudge the amount of time or resources that will be required to effectively manage any anticipated or unanticipated growth in our business, we may not be able to manufacture sufficient inven…

**Evidence 2** — `PODD / 2025 / Item 1A. Risk Factors` / block: Risks Related to our Intellectual Property

> …of supply, but we cannot guarantee these efforts will always be successful. We have also seen significant price increases for various components and raw materials, including for semiconductor chips. We do not have long-term supply agreements with all of our suppliers, and, in many cases, we, or our contract manufacturer, make purchases based on individual purchase orders. In some cases, our agreements with suppliers can be terminated by either party upon short notice. **Additionally, while efforts are made to diversify our sources of components and materials, in certain instances we acquire components and materials from a sole supplier.** Also, due to the stringent regulations and requirements of the FDA and similar regulatory agencies in other countries regarding the manufacture of our products, we may not be able to quickly establish additional or replacement sources for some components or materials. Our reliance on third-party suppliers subjects us to other risks that could harm our business, including:  •our suppliers may give other customers’ needs higher priority than ours, impacting their…

---

## a06 — COIN Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Financials / cap: mid / FY2025 / detection: text_fallback, text_fallback
- **query**: How can crypto-sector contagion reduce Coinbase revenue?
- curation_note: This evidence traces a causal chain from crypto-firm distress and forced asset sales to lower prices and activity, then links those conditions to Coinbase’s revenue dependence.

**Evidence 1** — `COIN / 2025 / Item 1A. Risk Factors` / block: The Most Material Risks Related to Our Business and Financial Position

> …n one or more future quarters may fall below the expectations of securities analysts and investors. As a result, the trading price of our Class A common stock may increase or decrease significantly. **Our total revenue is substantially dependent on the prices of crypto assets and volume of transactions conducted on our platform.** If such price or volume declines, our business, operating results, and financial condition would be adversely affected and the price of our Class A common stock could decline.  We generate a large portion of our total revenue from transaction fees on our platform in connection with the purchase, sale, and trading of crypto assets by our customers. Transaction revenue is based on transaction fees that are either a flat fee or a percentage of the value of each transaction. For our consumer trading product, we also charge a spread to ensure that…

**Evidence 2** — `COIN / 2025 / Item 1A. Risk Factors` / block: Risks Related to Our Employees and Other Service Providers

> …ome of which are alleged or have been held to be the result of fraudulent activity by insiders, including misappropriation of customer funds and other illicit activity and internal controls failures. In connection with these failures, concerns were raised about the potential for a market condition where the failure of one company leads to the financial distress of other companies, which has the potential to depress the prices of assets used as collateral by other firms. If such a market condition were to become widespread in the onchain economy, we could suffer from increased counterparty risk, including defaults or bankruptcies of major customers or counterparties, which could lead to significantly reduced activity on our platform and fewer available crypto market opportunities in general. **Further, forced selling of crypto assets by distressed companies could lead to lower crypto asset prices and may lead to a reduction in our revenue.** To the extent that conditions in the general economic and crypto asset markets were to materially deteriorate, our ability to attract and retain customers may suffer.  Actual events involving limited…

---

## a07 — AMZN Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Consumer Discretionary / cap: large / FY2025 / detection: markdown_h3, markdown_h3
- **query**: Which rival advantages involve supplier terms, pricing, and local familiarity?
- curation_note: This pair combines rivals’ procurement and pricing leverage with local firms’ customer knowledge and brand strength, testing retrieval across general and international competition risks.

**Evidence 1** — `AMZN / 2025 / Item 1A. Risk Factors` / block: Business and Industry Risks

> …competitors have greater resources, longer histories, more customers, and/or greater brand recognition, particularly with our newly-launched products and services and in our newer geographic regions. **They may secure better terms from vendors, adopt more aggressive pricing, and devote more resources to technology, infrastructure, fulfillment, and marketing.** Competition continues to intensify, including with the development of new business models and the entry of new and well-funded competitors, and as our competitors enter into business combinations or…

**Evidence 2** — `AMZN / 2025 / Item 1A. Risk Factors` / block: Our International Operations Expose Us to a Number of Risks

> …terrorism.  As international physical, e-commerce, and omnichannel retail, cloud services, and other services grow, competition will intensify, including through adoption of evolving business models. **Local companies may have a substantial competitive advantage because of their greater understanding of, and focus on, the local customer, as well as their more established local brand names.** The inability to hire, train, retain, and manage sufficient required personnel may limit our international growth.  The People’s Republic of China (“PRC”) and India regulate Amazon’s and its affiliat…

---

## a08 — DECK Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Consumer Discretionary / cap: mid / FY2026 / detection: markdown_h4, markdown_h4
- **query**: How can overseas distribution transitions impede Deckers growth?
- curation_note: The passages connect an ongoing international logistics-provider change with broader risks from switching distribution models during overseas expansion.

**Evidence 1** — `DECK / 2026 / Item 1A. Risk Factors` / block: have a material adverse effect on our business.

> …ly, which could similarly have a material adverse effect on our business.  Internationally, we distribute our products through warehouses and DCs managed by 3PLs in certain international   locations. **For example, we are currently transitioning certain international 3PL operations to a new partner.** While   we conduct diligence prior to entering into service agreements with 3PLs, we depend on these providers to operate   their warehouses and DCs in a manner that meets our business and performance requirements, including with   respect to data security and compliance with applicable data protection and privacy laws, and the provision of   quality services on a timely basis at the prices we expect. If our 3PLs fail to manage these responsibilities, including   during or following an operational transition, system cutover, or data migration, or if their operations are disrupted as   a result of factors outside of their control, such as sanctions that could in the future be imposed by the US   government, or broader disruptions or inefficiencies in global logistics and transportation networks, our distribution   operations could face delays, reduced reliability, or increased costs. The loss of or disruption to the operations of   any one or more of these facilities could materially and adversely affect our sales, business performance, and   results of operations. Although we be…

**Evidence 2** — `DECK / 2026 / Item 1A. Risk Factors` / block: adversely affected.

> …ird parties to operate the stores in a manner consistent with our standards or our failure to adequately   monitor these third parties, which could result in reduced sales and harm our brand image. **As part of our international growth strategy, we may transition certain brands in certain geographies from a third-  party distribution model to a direct distribution model or vice versa.** Failure to effectively implement our growth   strategies, including transitioning between distribution models or developing our business in international markets,   or disappointing growth within existing markets, could negatively affect our sales growth rate. In addition, taking   steps to implement our growth strategies could have a number of negative effects, including increasing our working   capital needs, causing us to incur costs without correspondi…

---

## a09 — GOOGL Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Communication Services / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: What physical bottlenecks and decarbonization difficulties accompany AI expansion?
- curation_note: This evidence links Alphabet’s power, water, and land constraints with AI-driven challenges to reducing emissions, testing synthesis across operational and regulatory-risk passages.

**Evidence 1** — `GOOGL / 2025 / Item 1A. Risk Factors` / block: Risks Specific to our Company

> …sruption. A significant supply interruption that affects us or our vendors could delay critical data center or network infrastructure upgrades or expansions and delay consumer product availability. **Our ability to scale our technical infrastructure is increasingly constrained by the availability of power, water, and land.** For example, energy supply is constrained globally due to the significant increase in demand for and limited availability of energy to power AI compute. Securing this capacity involves entering into complex, long-lead-time arrangements. Additionally, manufacturing and supply of servers and network equipment for our technical infrastructure, particularly for specialized AI chips, is limited to a small number of qualified suppliers. E…

**Evidence 2** — `GOOGL / 2025 / Item 1A. Risk Factors` / block: Risks Related to Laws, Regulations, and Policies

> …nge, human capital, and employment matters. In response, we have implemented robust programs and initiatives and adopted reporting frameworks and principles that may require considerable investments. **For instance, AI's energy and water demands have made efforts to reduce our emissions more complex and challenging across every level.** We cannot guarantee that our initiatives will be fully realized on the timelines we expect or at all, and projects that are completed as planned may not achieve the results we anticipate.  We are and…

---

## a10 — CAT Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Industrials / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How do inventory mismatches hurt Caterpillar and its dealer network?
- curation_note: This evidence links Caterpillar’s excess-stock costs with lost sales caused by inadequate dealer and OEM inventories, testing cross-unit synthesis of opposite inventory imbalances.

**Evidence 1** — `CAT / 2025 / Item 1A. Risk Factors` / block: MACROECONOMIC RISKS

> …eries to or from suppliers or decreased availability of raw materials or commodities could have an adverse effect on our ability to meet our commitments to customers or increase our operating costs. **On the other hand, in circumstances where demand for our products is less than we expect, we may experience excess inventories and be forced to incur additional costs and our profitability may suffer.** Our business, competitive position, results of operations or financial condition could be negatively impacted if supply is insufficient for our operations, if significant transportation delays interfere with deliveries, if we experience excess inventories or if we are unable to adjust our production schedules or our purchases from suppliers to reflect changes in customer demand and market fluctuations on a timely basis. Changes in government monetary or fiscal policies may negatively impact our results.  Most countries where our products and services are sold have established central banks to regulate monetary sys…

**Evidence 2** — `CAT / 2025 / Item 1A. Risk Factors` / block: OPERATIONAL RISKS

> …nished products primarily through an independent dealer network and directly to OEMs and are subject to risks relating to their inventory management decisions and operational and sourcing practices. Both carry inventories of finished products as part of ongoing operations and adjust those inventories based on their assessments of future needs and market conditions, including levels of used equipment inventory and machine rental usage rates.  Such adjustments may impact our results positively or negatively.  If the inventory levels of our dealers and OEM customers are higher than they desire, they may postpone product purchases from us, which could cause our sales to be lower than the end-user demand for our products and negatively impact our results. **Similarly, our results could be negatively impacted through the loss of time-sensitive sales if our dealers and OEM customers do not maintain inventory levels sufficient to meet customer demand.** We may not realize all of the anticipated benefits of our acquisitions, joint ventures or divestitures, or these benefits may take longer to realize than expected.  In pursuing our business strateg…

---

## a11 — AXON Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Industrials / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How can fast-moving AI competition undermine Axon's offerings?
- curation_note: These passages connect AI-driven technological acceleration and obsolescence with competitive pressure to release insufficiently tested features, testing cross-location causal retrieval.

**Evidence 1** — `AXON / 2025 / Item 1A. Risk Factors` / block: Strategic Risks

> …achieve market acceptance, our business, financial results and competitive position could be adversely affected.  We face risks associated with rapid technological change and new competing products. The technology associated with law enforcement devices and software is rapidly evolving. **The introduction of products embodying new technologies and the emergence of new industry standards can render existing products obsolete.** In particular, AI and machine learning technologies are rapidly developing and as these technologies are incorporated into our products and the operations of our customers, the pace of change has in the past and may in the future continue to accelerate. Additionally, we expect our products to meet and keep pace with evolving security standards and requirements of our industry and customers, including those of the U.S. federal government and internat…

**Evidence 2** — `AXON / 2025 / Item 1A. Risk Factors` / block: Operational Risks

> …rors may be costly and time-consuming and could harm our business. Failure to adequately train customers or employees on the use and limitations of AI-driven features could also compound these risks. Thoroughly testing generative AI models is challenging due to their complexity and the unpredictability of their outputs. Developing, testing, and deploying resource-intensive AI systems may require additional investment and increase our costs. There also may be real or perceived social harm, environmental harm, unfairness or other outcomes that undermine public confidence in the deployment and use of AI. Furthermore, third parties may deploy AI technologies in a manner that reduces customer demand for our products and services. **Competitive pressures may also drive rapid AI development or deployment, increasing the risk of releasing inadequately tested or unreliable features.** Any of the foregoing may result in decreased demand for our products and services or harm to our business, financial results, or reputation. The legal and regulatory landscape surrounding AI technologies is rapidly evolving and uncertain, particularly in areas of intellectual property, cybersecurity, privacy, and data protection. For exa…

---

## a12 — COST Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Consumer Staples / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Which outside providers support Costco’s transaction processing and technology infrastructure?
- curation_note: These sentences pinpoint Costco’s reliance on external entities for card processing and IT networks, testing synthesis of vendor dependencies across distinct risk discussions.

**Evidence 1** — `COST / 2025 / Item 1A. Risk Factors` / block: We are subject to payment-related risks.

> …s, regulations, compliance requirements, and higher fraud losses. For certain payment methods, we pay interchange and other related acceptance fees, along with additional transaction processing fees. **We rely on third parties to provide payment transaction processing services for credit and debit cards and our shop card.** It could disrupt our business if these parties become unwilling or unable to provide these services to us. We are also subject to fee increases by these service providers.  We must comply with evolvi…

**Evidence 2** — `COST / 2025 / Item 1A. Risk Factors` / block: Business and Operating Risks

> …itional costs, and become subject to litigation and regulatory action.  Increased security threats and more sophisticated cyber misconduct pose a risk to our systems, networks, products and services. **We rely upon IT systems and networks, some of which are managed by or belong to third parties, including suppliers, partners, vendors, and service providers.** Additionally, we collect, store and process sensitive information relating to our business, members, employees, and other third parties. Operating these IT systems and networks and processing and mai…

---

## a13 — XOM Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Energy / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How can hydrocarbon supply curbs ultimately hurt ExxonMobil through economic contraction?
- curation_note: These passages form a company-specific causal chain from policy-driven supply constraints to macroeconomic weakness and then lower ExxonMobil results.

**Evidence 1** — `XOM / 2025 / Item 1A. Risk Factors` / block: Climate Change and Energy Transition

> …development of stable and supportive government policies and markets. Failure or delay of these policies or markets to materialize or be maintained could adversely impact or delay these investments. Policy and other actions that result in restricting the availability of hydrocarbon products without a commensurate reduction in demand may have unpredictable adverse effects, including increased commodity price volatility; periods of significantly higher commodity prices and resulting inflationary pressures; and local or regional energy shortages. **Such effects in turn may depress economic growth or lead to rapid or conflicting shifts in policy by different actors, with resulting adverse effects on our businesses.** In addition, the existence of supportive policies in any jurisdiction is not a guarantee that those policies will continue in the future. See also the discussion of “Supply and Demand,” “Government a…

**Evidence 2** — `XOM / 2025 / Item 1A. Risk Factors` / block: Supply and Demand

> …nd new technology to enable those products and services to be provided on a cost-effective basis at commercial scale. See “Climate Change and Energy Transition” in this Item 1A.  Economic conditions. The demand for energy and petrochemicals is generally linked closely with broad-based economic activities and levels of prosperity. **The occurrence of economic downturns, recessions or other periods of low or negative economic growth will typically have a direct adverse impact on our results.** Other factors that affect general economic conditions in the world or in a major region, such as changes in population growth rates or living standards, periods of civil unrest or armed hostilities,…

---

## a14 — NEE Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Utilities / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How an overseas reactor accident could block a planned restart
- curation_note: The passages form a causal chain from a global nuclear incident prompting NRC licensing restrictions to failed restart approvals and possible asset impairment.

**Evidence 1** — `NEE / 2025 / Item 1A. Risk Factors` / block: Development and Operational Risks

> …E and FPL to acquire certain generation equipment and batteries on time and at acceptable costs.   Additionally, NEER is actively pursuing the restart of the Duane Arnold nuclear generation facility. The restart is subject to certain regulatory approvals, including NRC safety and environmental reviews, as well as permits from relevant state and local agencies. **NEER has applied to the NRC to reinstate the operating license and to MISO for an interconnection agreement.** Failure to obtain the necessary approvals could result in the impairment of amounts capitalized. Further, NEE could encounter difficulty in procuring or restoring specialized components which could impact the restart timeline. NEE could incur costs greater than expected or encounter unforeseen i…

**Evidence 2** — `NEE / 2025 / Item 1A. Risk Factors` / block: Nuclear Generation Risks

> …nt of the severity of the situation, until compliance is achieved. Any of the foregoing events could require NEE and FPL to incur increased costs and capital expenditures, and could reduce revenues. Any serious nuclear incident occurring at a NEE or FPL plant could result in substantial remediation costs and other expenses. **A major incident at a nuclear facility anywhere in the world could cause the NRC to limit or prohibit the operation or licensing of any domestic nuclear generation facility.** An incident at a nuclear facility anywhere in the world also could cause the NRC to impose additional conditions or other requirements on the industry, or on certain types of nuclear generation units, which could increase costs, reduce revenues and result in additional capital expenditures for NEE and FPL. The inability to operate any of NEE's or FPL's nuclear generation units through the end of their respective operating licenses or planned license extensions could have a material adverse effect on N…

---

## a15 — PLD Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Real Estate / cap: large / FY2025 / detection: text_fallback, text_fallback
- **query**: Why can acquired sites leave Prologis paying cleanup costs without seller recourse?
- curation_note: This evidence links limited recourse for unknown acquisition liabilities with strict environmental cleanup obligations, testing retrieval across acquisition and contamination risk disclosures.

**Evidence 1** — `PLD / 2025 / Item 1A. Risk Factors` / block: •our ability to lease the properties at favorable rates and control variable operating costs; and

> …and we expect that there will continue to be, significant competition for properties that meet our investment criteria as well as risks associated with obtaining financing for acquisition activities. **The acquired properties or entities may be subject to liabilities, including tax liabilities, which may be without any recourse, or with only limited recourse, with respect to unknown liabilities.** As a result, if a liability were asserted against us based on our new ownership of any of these entities or properties, then we may have to pay substantial sums to settle it. We may be unable to integrate the operations of newly acquired companies and realize the anticipated synergies and other benefits or do so within the anticipated timeframe. Potential difficulties w…

**Evidence 2** — `PLD / 2025 / Item 1A. Risk Factors` / block: •we may experience delays (temporary or permanent) if there is public or government opposition to our activities; and

> …rent than investing in our core real estate business.  We are exposed to various environmental risks, which may result in unanticipated losses that could affect our business and financial condition. Under various federal, state and local laws, ordinances and regulations, a current or previous owner, developer or operator of real estate may be liable for the costs of removal or remediation of certain hazardous or toxic substances. The costs of removal or remediation of such substances could be substantial. **Such laws often impose liability without regard to whether the owner or operator knew of, or was responsible for, the release or presence of such hazardous substances.** In addition, third parties may sue the owner or operator of a site for damages based on personal injury, property damage or other costs, including investigation and clean-up costs, resulting from the…

---

## a16 — LIN Item 7 (passage, passage_first, ALTERNATE)

- sector: Materials / cap: large / FY2025 / detection: markdown_h4
- **query**: Factors behind unchanged APAC revenue in 2025
- curation_note: This passage decomposes flat APAC sales into acquisition gains offset by volume and currency declines, testing retrieval of segment-specific revenue drivers.

**Evidence 1** — `LIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: APAC

> …vestitures2 %  — %  The APAC segment includes Linde's industrial gases operations in approximately 15 Asian and South Pacific countries and regions including China, Australia, India and South Korea. Sales  Sales for the APAC segment were flat in 2025 versus 2024. Acquisitions increased sales by 2%. Volumes decreased sales by 1%. **Currency translation decreased sales by 1% primarily due to the weakening of the Australian dollar and Korean won against the U.S. dollar.** Cost pass-through and pricing were flat. Operating Profit  Operating profit in the APAC segment increased $15 million, or 1%, in 2025 versus 2024. The increase was primarily driven by productivity initiatives and acquisitions, partially of…

---

## a17 — NVDA Item 7 (passage, passage_first, ALTERNATE)

- sector: Information Technology / cap: large / FY2026 / detection: markdown_h3
- **query**: What propelled NVIDIA's Data Center compute and networking expansion?
- curation_note: This evidence pairs distinct growth rates with named Blackwell, NVLink, Ethernet, and InfiniBand demand drivers, testing retrieval of segment-specific operating details.

**Evidence 1** — `NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Results of Operations

> …Graphics9,156 5,085 4,071 80 %  Total$139,297 $87,960 $51,337 58 %  Compute & Networking revenue – The year over year increase was driven by the major platform shifts – accelerated computing and AI. Revenue from Data Center computing grew 59% driven by demand for our Blackwell computing platform. **Revenue from Data Center networking grew 142% driven by the introduction and continued ramp of NVLink compute fabric for GB200 and GB300 systems and the growth of Ethernet and InfiniBand platforms.** Graphics revenue – The year over year increase was driven by sales of our Blackwell architecture.  Reportable segment operating income – The year over year increase in Compute & Networking segment o…

---

## a18 — DDOG Item 7 (passage, passage_first, ALTERNATE)

- sector: Information Technology / cap: mid / FY2025 / detection: markdown_h3
- **query**: Datadog net retention change and its cause in 2025
- curation_note: This evidence quantifies the year-over-year retention improvement and attributes it to greater usage by established customers, testing metric-and-driver retrieval.

**Evidence 1** — `DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …y or annualized basis, as they are operating metrics that can be impacted by contract start and end dates, and renewal rates. ARR and MRR are not intended to be replacements or forecasts of revenue. A further indication of the propensity of our customer relationships to expand over time is our dollar-based net retention rate, which compares our ARR from the same set of customers in one period, relative to the year-ago period. As of December 31, 2025, our trailing 12-month dollar-based net retention rate was about 120%. As of December 31, 2024, our trailing 12-month dollar-based net retention rate was high-110%'s. **The increase in our trailing 12-month dollar-based net retention rate was attributable to increased usage growth from existing customers.** We calculate dollar-based net retention rate as of a period end by starting with the ARR from the cohort of all customers as of 12 months prior to such period-end, or the Prior Period ARR. We then ca…

---

## a19 — LLY Item 7 (passage, passage_first, ALTERNATE)

- sector: Health Care / cap: large / FY2025 / detection: markdown_h3
- **query**: Why will Lilly's near-term capital spending remain elevated?
- curation_note: This passage links rising capital expenditures to global manufacturing investments and tests retrieval of the specific operational driver behind Lilly's spending outlook.

**Evidence 1** — `LLY / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: RESULTS OF OPERATIONS

> …o the consolidated financial statements). We anticipate our cash requirements related to ordinary course purchases of goods and services will be consistent with our past levels relative to revenues. Capital expenditures were $7.8 billion during 2025, compared to $5.1 billion in 2024. We are making investments in global facilities to manufacture existing and future products. **These investments, and other capital investments that support our operations, have increased our capital expenditures and will result in meaningfully higher capital expenditures in the near term.**   As we expand our manufacturing capacity in order to meet existing and expected demand of our medicines, we have entered, and expect to continue to enter, into various agreements for contract manufacturing and for supply of materials. Executed agreements related to our medicines in development could, under certain circumstances, require us to pay up to approximately $10 billion if we do not purchase specified amounts of goods or s…

---

## a20 — PODD Item 7 (passage, passage_first, ALTERNATE)

- sector: Health Care / cap: mid / FY2025 / detection: markdown_h3
- **query**: 2025 capital spending increase and associated factory expansion projects
- curation_note: This passage links the year-over-year increase in capital expenditures to specific manufacturing investments in Costa Rica and Malaysia.

**Evidence 1** — `PODD / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Liquidity and Capital Resources

> …growing business, and an increase in accrued rebates due to higher sales volume. Finally, the increase in accounts payable was driven by the timing of payments and continued growth of our business. Investing Activities  Net cash used in investing activities was $222.7 million in 2025, compared with $146.2 million in 2024.  **Capital Spending—Capital expenditures were $191.6 million and $124.9 million in 2025 and 2024, respectively.** The $66.7 million increase primarily related to the investment in our third manufacturing plant in Costa Rica and the purchase of additional machinery and equipment for our Malaysia manufacturing facility to support continued business growth. We expect capital expenditures for 2026 to increase compared with 2025 as we continue to expand globally and optimize our manufacturing and supply chain operations. We expect to fund our capital expe…

---

## a21 — COIN Item 7 (passage, passage_first, ALTERNATE)

- sector: Financials / cap: mid / FY2025 / detection: markdown_h4
- **query**: Coinbase policy and liquidity constraints for investment digital assets
- curation_note: This passage explains Coinbase’s long-term holding approach, exceptional-sale policy, and potential difficulty monetizing investment crypto during market instability.

**Evidence 1** — `COIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Other resources and commitments

> …inancing, we hold crypto assets we borrow, as well as crypto assets customers pledge as collateral against certain of our loans to them. We do not use these assets as a source of liquidity otherwise. Crypto assets held for investment are primarily long-term holdings and in certain cases fulfill capital requirements set by regulators (see also Capital requirements below). **We do not plan to engage in regular trading of these crypto assets but may purchase additional crypto assets for investment as a buy and hold strategy.** In case of a liquidity stress event, or for other episodic purposes, which may necessitate the use of these assets, we may change our policy and sell crypto assets held for investment to generate liquidity. During times of instability in the crypto assets market, we may not be able to sell our crypto assets at reasonable prices or at all. Our crypto assets held are considered less liquid than our cash and cash equivalents and may not be able to serve as a source of liquidity for us to the same extent as cash and cash equivalents. As of December 31, 2025, we held the following crypto assets: $120.8 million held for operations, $822.8 million held as collateral, $318.8 million that were borrowed, and $2.0 billion held for inves…

---

## a22 — AMZN Item 7 (passage, passage_first, ALTERNATE)

- sector: Consumer Discretionary / cap: large / FY2025 / detection: markdown_h3
- **query**: How does Amazon account for satellite broadband development before and after viability?
- curation_note: This evidence captures Amazon-specific accounting treatment for its satellite network and tests retrieval of the capitalization threshold after commercial viability.

**Evidence 1** — `AMZN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …ily due to an increase in spending on infrastructure, including depreciation and amortization. Changes in foreign exchange rates increased technology and infrastructure costs by $312 million in 2025. We currently expense the majority of the costs associated with the development of our satellite network for global broadband service (including production, launch, and payroll costs, and launch services deposits upon launch). **We will capitalize certain of these costs once the service achieves commercial viability, including sales to customers.** Sales and Marketing  Sales and marketing costs include advertising and payroll and related expenses for personnel engaged in marketing and selling activities, including sales commissions related to…

---

## a23 — DECK Item 7 (passage, passage_first, ALTERNATE)

- sector: Consumer Discretionary / cap: mid / FY2026 / detection: text_fallback
- **query**: Deckers currency-neutral revenue and comparable direct-sales growth rates
- curation_note: This passage provides two related supplemental sales-growth measures, testing retrieval of adjusted revenue performance metrics.

**Evidence 1** — `DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Supplemental Disclosure

> •On a constant currency basis, net sales increased by 9.0%, compared to the prior period.  **•Comparable DTC channel net sales for the 52 weeks ended March 29, 2026, increased by 4.6%,   compared to the prior period.** •We experienced an increase of 6.2% in the total volume of units sold to 78,700 from 74,100,   compared to the prior period. Units sold include all categories such as footwear, apparel,   accessorie…

---

## a24 — GOOGL Item 7 (passage, passage_first, ALTERNATE)

- sector: Communication Services / cap: large / FY2025 / detection: markdown_h3
- **query**: What borrowing capacity and maturity schedule did Alphabet's unused revolvers have?
- curation_note: This evidence gives the company-specific size, expiration dates, and unused status of Alphabet’s revolving credit arrangements, testing retrieval of linked financing details.

**Evidence 1** — `GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Liquidity and Material Cash Requirements

> …ly 20 years. We also issued €6.5 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.44% and a weighted-average maturity of approximately 16 years. **As of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring in April 2026 and $6.0 billion expiring in April 2030.** No amounts have been borrowed under the credit facilities. We also have a commercial paper program of up to $25.0 billion, which is used for general corporate purposes. As of December 31, 2025, we had no commercial paper outstanding.  For additional informat…

---

## a25 — CAT Item 7 (passage, passage_first, ALTERNATE)

- sector: Industrials / cap: large / FY2025 / detection: markdown_h3
- **query**: RPMGlobal deal cost, completion schedule, and mining software capabilities
- curation_note: This passage combines the acquisition’s expected closing window and consideration with RPMGlobal’s specialized mining technology expertise, testing transaction-detail retrieval.

**Evidence 1** — `CAT / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Financial Products Segment

> …lence, advanced technology leadership and transforming how we work. These pillars work together to drive sustainable growth, innovation and operational efficiency for Caterpillar and our customers. On February 3, 2026, the Federal Court of Australia approved Caterpillar's acquisition of RPMGlobal Holdings Limited, an Australian based software company. **The transaction is expected to close in the final two weeks of February with a purchase price of approximately $790 million, excluding cash acquired.** RPMGlobal is a leading provider of mining software solutions with deep domain expertise in mining technology enablement and data-driven software solutions at every stage of the mining lifecycle. Return to shareholders — Our goal is to return substantially all MP&E free cash flow to shareholders over time in the form of dividends and share repurchases, while maintaining our mid-A rating.…

---

## p13 — XOM Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Energy / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: How do public policies intensify competitive threats to ExxonMobil?
- curation_note: This pairing links sanctions-based disadvantages with subsidized alternative-energy rivalry, testing retrieval across separate regulatory and competitive-risk passages.

**Evidence 1** — `XOM / 2025 / Item 1A. Risk Factors` / block: Government and Political Factors

> …ict the import or export of certain products based on point of origin, and such restrictions may increase during periods of escalating geopolitical or trade tensions.  Restrictions on doing business. ExxonMobil is subject to laws and sanctions imposed by the United States and by other jurisdictions where we do business that may prohibit ExxonMobil or its affiliates from doing business in certain countries or with certain counterparties or restrict or impede the kind of business that may be conducted, including acquiring and divesting certain assets or importing or exporting certain materials or products. **Such restrictions may provide a competitive advantage to competitors who may not be subject to comparable restrictions.** Lack of legal certainty. Some countries in which we do, or seek to do, business lack well-developed legal systems, lack political or governmental stability, may be subject to regime changes, have no…

**Evidence 2** — `XOM / 2025 / Item 1A. Risk Factors` / block: Operational and Other Factors

> …ve the internal resources and capabilities of ExxonMobil or reduce the need for resource-owning countries to partner with private-sector oil and gas companies in order to monetize national resources. **As described in more detail above, our hydrocarbon-based energy products are also subject to growing and, in many cases, government-supported competition from alternative energy sources.** In addition, as we enter new markets in pursuit of lower-emission and other new business opportunities, we will need to compete effectively with established competitors in these markets, as well as with new market entrants seeking to capitalize on these opportunities, while successfully navigating changing market conditions or technologies. Reputation. Our reputation is an important corporate asset. Factors that could have a negative impact on our reputation include an operating incident or significant cybersecurity disruption; changes…

---


# Rejected candidates

Removed from the draft after quality review; kept for provenance only. No review action needed.

## p01 — NVDA Item 1A/Item 7 (multi_passage, passage_first, REJECTED)

- sector: Information Technology / cap: large / FY2026 / detection: markdown_h3, markdown_h3
- **query**: Blackwell production issues and causes of fiscal 2026 gross margin decline
- curation_note: This evidence links a specific low-yield Blackwell inventory problem with the later margin effects of NVIDIA’s datacenter solution transition and H20 charge.
- **rejected because**: multi_passage query joins two facts from different fiscal periods with 'and'; evidence 1 (FY2025 Q2 Blackwell low-yield inventory provision) is not actually cited as a cause in evidence 2's own text (FY2026 full-year decline lists business-model transition + H20 charge as its causes) — the causal link in curation_note is the generator's inference, not textual. Prompt v1, never re-examined under rule 1b. Replaced by a01 (same ticker/items/query type).

**Evidence 1** — `NVDA / 2026 / Item 1A. Risk Factors` / block: Risks Related to Our Global Operating Business

> …and future architecture transitions. Our financial results have been and may in the future be negatively impacted if we are unable to execute our architectural transitions as planned for any reason. The increased frequency and complexity of newly introduced products could result in unanticipated quality or production issues that could increase the magnitude of inventory provisions, warranty, or other costs or result in product delays. **For example, our gross margins in the second quarter of fiscal year 2025 were negatively impacted by inventory provisions for low-yielding Blackwell material.**  We incur significant engineering development resources for new products, and changes to our product roadmap may impact our ability to develop other products or adequately manage our supply chain cost. Customers may delay purchasing existing products as we increase the frequency of new products or may not be able to adopt our new   16   products as fast as forecasted, both impacting the timing of o…

**Evidence 2** — `NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …onal demand for Blackwell as well as the launch of our new DGX Spark.  Automotive revenue for fiscal year 2026 was up 39% from a year ago, driven by continued adoption of our self-driving platforms. **Gross margin decreased in fiscal year 2026 as our business model transitioned from offering Hopper HGX systems to Blackwell full-scale datacenter solutions.** The gross margin decrease was also impacted by a $4.5 billion charge associated with H20 excess inventory and purchase obligations. Operating expenses for fiscal year 2026 were up 41% from a year ago, driven by higher compensation and benefits expenses due to employee growth and compute and infrastructure costs.   37   Critical…

---

## p02 — DDOG Item 1A (multi_passage, passage_first, REJECTED)

- sector: Information Technology / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Why do outsourced hosting failures threaten Datadog's contractual availability promises?
- curation_note: These passages connect Datadog’s near-total infrastructure outsourcing with the customer availability commitments that make provider disruptions consequential.
- **rejected because**: Query's information need ('why do hosting failures threaten availability promises') is fully answered by evidence 1 alone; evidence 2 covers breach consequences, not the asked 'why', and its only cap-compliant snippet restates a fact already present in evidence 1's span. Replaced by a02 (same ticker/item/query type).

**Evidence 1** — `DDOG / 2025 / Item 1A. Risk Factors` / block: Strategic and Operational Risks

> …nd improvements to our internal infrastructure will be effectively implemented on a timely basis, if at all, and such failures could harm our business, financial condition and results of operations. We rely upon third-party providers of cloud-based infrastructure to host our products. Any disruption in the operations of these third-party providers, limitations on capacity or interference with our use could adversely affect our business, financial condition and results of operations.  **We outsource substantially all of the infrastructure relating to our cloud solution to third-party hosting services.** Customers of our cloud-based products need to be able to access our platform at any time, without interruption or degradation of performance, and we provide them with service-level commitments with respect to uptime. Our cloud-based products depend on protecting the virtual cloud infrastructure hosted by third-party hosting services by maintaining its configuration, architecture, features and interconnection spec…

**Evidence 2** — `DDOG / 2025 / Item 1A. Risk Factors` / block: Legal and Regulatory Risks

> **We typically provide service-level commitments under our subscription agreements.** If we fail to meet these contractual commitments, we could be obligated to provide credits for future service or face subscription termination with refunds of prepaid amounts, which would lower our revenue and harm our business, financial condition and results of operations.  Our subscription agreements typically contain service-level commitments. If we are unable to meet the stated service-level commitments, including failure to meet the uptime and response time requirements under our customer subscription agreements, we may be contractually…

---
