# sec_retrieval_ab dataset — human review sheet

Mark decisions in `review.csv` (`approved`: yes/no + optional `reviewer_comment`). Snippet is **bold** inside its span; one sentence of context shown on each side.

## p01 — NVDA Item 1A/Item 7 (multi_passage, passage_first)

- sector: Information Technology / cap: large / FY2026 / detection: markdown_h3, markdown_h3
- **query**: Blackwell production issues and causes of fiscal 2026 gross margin decline
- curation_note: This evidence links a specific low-yield Blackwell inventory problem with the later margin effects of NVIDIA’s datacenter solution transition and H20 charge.

**Evidence 1** — `NVDA / 2026 / Item 1A. Risk Factors` / block: Risks Related to Our Global Operating Business

> …and future architecture transitions. Our financial results have been and may in the future be negatively impacted if we are unable to execute our architectural transitions as planned for any reason. The increased frequency and complexity of newly introduced products could result in unanticipated quality or production issues that could increase the magnitude of inventory provisions, warranty, or other costs or result in product delays. **For example, our gross margins in the second quarter of fiscal year 2025 were negatively impacted by inventory provisions for low-yielding Blackwell material.**  We incur significant engineering development resources for new products, and changes to our product roadmap may impact our ability to develop other products or adequately manage our supply chain cost. Customers may delay purchasing existing products as we increase the frequency of new products or may not be able to adopt our new   16   products as fast as forecasted, both impacting the timing of o…

**Evidence 2** — `NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …onal demand for Blackwell as well as the launch of our new DGX Spark.  Automotive revenue for fiscal year 2026 was up 39% from a year ago, driven by continued adoption of our self-driving platforms. **Gross margin decreased in fiscal year 2026 as our business model transitioned from offering Hopper HGX systems to Blackwell full-scale datacenter solutions.** The gross margin decrease was also impacted by a $4.5 billion charge associated with H20 excess inventory and purchase obligations. Operating expenses for fiscal year 2026 were up 41% from a year ago, driven by higher compensation and benefits expenses due to employee growth and compute and infrastructure costs.   37   Critical…

---

## p02 — DDOG Item 1A (multi_passage, passage_first)

- sector: Information Technology / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Datadog 2025 repository intrusion and EU AI law timing
- curation_note: This evidence pairs a specific credential-related source-code incident with the effective date of a named AI regulation, testing retrieval across operational and regulatory risk units.

**Evidence 1** — `DDOG / 2025 / Item 1A. Risk Factors` / block: Strategic and Operational Risks

> …ties fraudulently induce our employees or our members to disclose information or user names and/or passwords, or otherwise compromise the security of our networks, systems and/or physical facilities. **For example, in April 2025, we notified customers of access by an unauthorized third party to a number of Datadog source code repositories arising from compromised employee account credentials.** After discovering the access, we revoked the credentials and terminated the unauthorized access. However, such unauthorized access may increase our vulnerability to certain attacks at a later date th…

**Evidence 2** — `DDOG / 2025 / Item 1A. Risk Factors` / block: Industry and Competitive Risks

> …l jurisdictions around the globe, including Europe and certain U.S. states, have proposed, enacted, or are considering laws governing the development and use of AI and machine learning technologies. **For example, the European Union's Artificial Intelligence Act, which would apply beyond the European Union’s borders, came into effect in August 2024.** It contains numerous requirements regarding the development and use of AI and imposes significant monetary fines. Further, countries and states are applying their data and consumer protection laws to…

---

## p03 — LLY Item 1A (multi_passage, passage_first)

- sector: Health Care / cap: large / FY2025 / detection: markdown_h3, markdown_h3
- **query**: orforglipron regulatory submission and AI-assisted research collaborations
- curation_note: This pairing tests cross-unit retrieval of a named pipeline candidate and Lilly’s technology partnerships supporting medicine research.

**Evidence 1** — `LLY / 2025 / Item 1A. Risk Factors` / block: Risks Related to Our Business and Industry

> …il to pursue or invest sufficiently in product candidates or indications that may have been successful, or fail to optimally balance trial design, conduct, and speed to accomplish desired outcomes. **We regularly submit new product candidates and indications to regulatory agencies for approval, including highly anticipated candidates such as orforglipron.** Regulatory agencies establish high hurdles for the efficacy and safety of new products and indications. Delay, uncertainty, unpredictability, and inconsistency in drug approval processes across marke…

**Evidence 2** — `LLY / 2025 / Item 1A. Risk Factors` / block: Risks Related to Our Operations

> …rging technologies could adversely impact us.   We deploy AI and other emerging technologies in various facets of our operations and we continue to explore the development and use of AI technologies. **We have also entered into, and may continue to enter into, partnerships and collaborations relating to the use of AI technology to aid in drug discovery and other efforts.** The rapid advancement of these technologies presents opportunities for us in research, manufacturing, commercialization, and other business endeavors but also entails risks, including that AI-generat…

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
- **query**: JPMorganChase breach history and drivers of intensifying technology competition
- curation_note: These passages test retrieval across operational and strategic risks by linking prior security incidents with technology-driven competitive pressure.

**Evidence 1** — `JPM / 2025 / Item 1A. Risk Factors` / block: Operational

> …•sponsored by, or acting on behalf of, hostile countries or terrorist organizations  •cyber-criminals, or  •engaged in using technology to promote a political or social agenda (i.e., “hacktivists”). **JPMorganChase has experienced security breaches due to cyber attacks in the past, and future breaches are inevitable.** Any such breach could result in serious and harmful consequences for JPMorganChase or its clients and customers. JPMorganChase cannot guarantee that it will always detect cybersecurity threats to its systems or implement effective preventive measures against those threats. The reasons for this include:  •the t…

**Evidence 2** — `JPM / 2025 / Item 1A. Risk Factors` / block: Strategic

> …ssing and other products and services from the use of new technologies that may not require intermediation, such as tokenized securities or other products that leverage distributed ledger technology. New technologies have required and could require JPMorganChase to increase expenditures to modify its products to attract and retain clients and customers or to match products and services offered by its competitors, including technology companies. If JPMorganChase does not keep pace with rapidly changing technological advances, including the adoption of generative AI, it risks losing clients and market share to competitors, which could negatively impact revenues, operating costs and its competitive position. **Competition could be intensified as the feasibility, capability and scalability of new technologies improves.** In addition, new technologies (including generative AI) could be used by customers or bad actors in unexpected or disruptive ways, or could be breached or infiltrated by third parties, which could in…

---

## p06 — COIN Item 1A (multi_passage, passage_first)

- sector: Financials / cap: mid / FY2025 / detection: text_fallback, text_fallback
- **query**: Coinbase 2025 outage frequency and Apple's decentralized-app feature restriction
- curation_note: This pair tests retrieval of a quantified platform-reliability metric and a specific Apple-imposed limitation on Coinbase’s mobile application.

**Evidence 1** — `COIN / 2025 / Item 1A. Risk Factors` / block: •place us at a competitive disadvantage compared to our less leveraged competitors; and

> …n crypto assets may become more volatile and less liquid in a very short period of time, resulting in market prices being subject to erratic and abrupt market movement, which could harm our business. For instance, abrupt changes in volatility or market movement can lead to extreme pressures on our platform and infrastructure that can lead to inadvertent suspension of services across parts of the platform or the entire platform. As a result, from time to time we experience outages. **For example, in 2025, we experienced approximately 10 outages, with an average outage duration of 74.2 minutes.** Outages can lead to increased customer service expense, can cause customer loss and reputational damage, result in inquiries and actions by regulators, and can lead to other damages for which we may be responsible.

**Evidence 2** — `COIN / 2025 / Item 1A. Risk Factors` / block: Risks Related to Third Parties

> …tions related to crypto assets have disrupted the proposed launch of many features within the Coinbase and the Base App apps, including NFT transfer services and access to decentralized applications. If our products are found to be in violation of any such terms and conditions, we may no longer be able to offer our products through such third-party platforms. There can be no guarantee that third-party platforms will continue to support our product offerings, or that customers will be able to continue to use our products. **For example, in December 2019, we were instructed by Apple to remove certain features relating to decentralized applications from our application to comply with the Apple App Store’s policies.** Any changes, bugs, technical or regulatory issues with third-party platforms, our relationships with mobile manufacturers and carriers, or changes to their terms of service or policies could degrade our products’ functionalities, reduce or eliminate our ability to distribute our products, give preferential treatment to competitive products, limit our ability to deliver high quality offerings, or impose fees or other charges, any of which could affect our product usage and adversely affect our business, operating results, and financial condition.

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
- **query**: What compute bottlenecks and European AI-law deadlines does Alphabet disclose?
- curation_note: This evidence pairs concrete infrastructure constraints with a dated European regulatory rollout, testing cross-unit retrieval of operational and legal AI risks.

**Evidence 1** — `GOOGL / 2025 / Item 1A. Risk Factors` / block: Risks Specific to our Company

> …sruption. A significant supply interruption that affects us or our vendors could delay critical data center or network infrastructure upgrades or expansions and delay consumer product availability. Our ability to scale our technical infrastructure is increasingly constrained by the availability of power, water, and land. For example, energy supply is constrained globally due to the significant increase in demand for and limited availability of energy to power AI compute. Securing this capacity involves entering into complex, long-lead-time arrangements. **Additionally, manufacturing and supply of servers and network equipment for our technical infrastructure, particularly for specialized AI chips, is limited to a small number of qualified suppliers.** Extended or unforeseen disruptions at these suppliers could impact our ability to meet customer demand. Failure to secure sufficient capacity in a timely manner would limit our ability to train models and serve Cloud customers. We may enter into long-term contracts for materials and products that commit us to significant terms and conditions. We may face costs for materials and products that are not consumed due to market…

**Evidence 2** — `GOOGL / 2025 / Item 1A. Risk Factors` / block: Risks Related to Laws, Regulations, and Policies

> …: Laws and regulations focused on the development, use, and provision of AI technologies and other digital products and services, which could result in monetary penalties or other regulatory actions. **For example, the EU AI Act came into force on August 1, 2024, and will generally become fully applicable after a two-year transitional period (although certain obligations have already taken effect).** The EU AI Act introduces various requirements for AI systems and models placed on the market in the EU, including specific transparency, safety, and copyright requirements for general purpose AI systems and the models on which those systems are based. Various countries, including Brazil, India, Japan, South Korea, Singapore, and Vietnam, have also enacted or are considering enacting regulations focused on AI. In the US, an increasing amount of leg…

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

> …unting, regulatory, political and economic factors specific to the countries or regions in which we operate, which could adversely affect our business, financial condition and results of operations. At the end of 2025, we operated 285 warehouses outside of the U.S. **(31% of all warehouse locations), and we plan to continue expanding our international operations.** Future operating results internationally could be negatively affected by a variety of factors, many similar to those we face in the U.S., certain of which are beyond our control. These factors include political and economic conditions, regulatory constraints, currency regulations, policy changes, and other matters in any of the countries or regions in which we operate, now or…

**Evidence 2** — `COST / 2025 / Item 1A. Risk Factors` / block: Market and Other External Risks

> …da, generated 27% and 34% of our net sales and operating income. Our international operations have accounted for an increasing portion of our warehouses, and we plan to continue international growth. To prepare our consolidated financial statements, we translate the financial statements of our international operations from local currencies into U.S. dollars using current exchange rates. Future fluctuations in exchange rates that are unfavorable to us may adversely affect the financial performance of our Canadian and Other International operations and have a corresponding adverse period-over-period effect on our results of operations. **As we continue to expand internationally, our exposure to fluctuations in foreign-exchange rates may increase.** A portion of the products we purchase is paid for in a currency other than the local currency of the country in which the goods are sold. Currency fluctuations may increase our merchandise costs and…

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
- **query**: What were overseas revenue and top-ten customer rent concentrations?
- curation_note: This pair tests retrieval of two distinct, company-specific concentration metrics spanning international operations and customer exposure.

**Evidence 1** — `PLD / 2025 / Item 1A. Risk Factors` / block: Risks Related to our Global Operations

> …esults of operations and financial condition may be materially and adversely affected.   We conduct a significant portion of our business and employ a substantial number of people outside of the U.S. **During 2025, we generated approximately $788 million, or 9.0% of our consolidated revenues, from operations outside the U.S.** Circumstances and developments related to international operations that could negatively impact us include, but are not limited to, the following factors:  •difficulties and costs of staffing and man…

**Evidence 2** — `PLD / 2025 / Item 1A. Risk Factors` / block: •our ability to lease the properties at favorable rates and control variable operating costs; and

> …favorable terms as leases expire.  Our operating results and distributable cash flow would be adversely affected if a significant number of our customers were unable to meet their lease obligations. **At December 31, 2025, our top 10 customers accounted for 16.3% of our consolidated NER and 15.2% of our O&M NER.** In the event of default by a significant number of customers, we may experience delays and incur substantial costs in enforcing our rights as landlord, and we may be unable to re-lease spaces. A cust…

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
- **query**: How could tariffs and cross-border commerce barriers harm Datadog?
- user_intent: how do export controls or trade restrictions affect the business
- curation_note: This passage links shifting trade policy to economic uncertainty, reduced technology spending, delayed subscription effects, and potential harm to Datadog’s results.

**Evidence 1** — `DDOG / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …illion, $775.1 million and $597.5 million for the years ended December 31, 2025, 2024 and 2023, respectively. See the section titled “—Liquidity and Capital Resources—Non-GAAP Free Cash Flow” below. Unfavorable conditions in the economy both in the United States and abroad may negatively affect the growth of our business and our results of operations. For example, macroeconomic events including changes in trade policies, such as trade wars, tariffs or other trade restrictions or the threat of such actions, fluctuating inflation and interest rates, and the conflicts in Ukraine and the Middle East have led to economic uncertainty. **Historically, during periods of economic uncertainty and downturns, businesses may slow spending on information technology, which may impact our business and our customers’ businesses.**  Due to our subscription model, the effect of macroeconomic conditions may not be fully reflected in our results of operations until future periods. However, if economic uncertainty increases or the global economy worsens, our business, financial condition and results of operations may be harmed. For further discussion of the potential impacts of macroeconomic events on our business, financial condition, and operating results, see “Risk Factors” included in Part I, Item 1A of this report.  Fa…

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

> Comparison of the years ended December 31, 2025 and 2024  Revenue  For the years ended December 31, 2025 and 2024 we generated 84% and 83%, respectively, of total revenue in the U.S., with no other country contributing over 10%. **International revenue comprised mainly transaction revenue.** Transaction revenue  Year Ended December 31,Change  (in thousands, except %)  20252024$%  Consumer, net$3,322,835 $3,430,322 $(107,487)(3)  Institutional, net479,667 345,598 134,069 39   Other trans…

---

## p22 — AMZN Item 7 (passage, intent_first)

- sector: Consumer Discretionary / cap: large / FY2025 / detection: markdown_h3
- **query**: Factors behind Amazon's 2025 overseas retail and cloud revenue gains
- user_intent: what is driving the company's revenue growth
- curation_note: This passage captures distinct growth drivers for Amazon’s International and AWS businesses, testing retrieval across adjacent segment discussions.

**Evidence 1** — `AMZN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …nued focus on price, selection, and convenience for our customers, including from our fast shipping offers. Changes in foreign exchange rates reduced North America net sales by $454 million in 2025. International sales increased 13% in 2025, compared to the prior year. The sales growth primarily reflects increased unit sales, including sales by third-party sellers, advertising sales, and subscription services. Increased unit sales were driven largely   24   by our continued focus on price, selection, and convenience for our customers, including from our fast shipping offers. Changes in foreign exchange rates increased International net sales by $4.9 billion in 2025.  AWS sales increased 20% in 2025, compared to the prior year. **The sales growth primarily reflects increased customer usage, partially offset by pricing changes primarily driven by long-term customer contracts.** Operating Expenses  Information about operating expenses is as follows (in millions):    Year Ended December 31,    20242025  Operating Expenses:  Cost of sales$326,288 $356,414   Fulfillment98,505…

---

## p23 — DECK Item 7 (passage, intent_first)

- sector: Consumer Discretionary / cap: mid / FY2026 / detection: text_fallback
- **query**: Deckers expected spending for capital projects and cloud implementations
- user_intent: what risks does the company see around AI
- curation_note: This is the closest technology-related disclosure available, testing retrieval of Deckers’ quantified planned investment in cloud and capital projects rather than AI-specific risks.

**Evidence 1** — `DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: certain implementation costs for cloud computing arrangements to be made before the end of our next fiscal year

> **will range from approximately $145,000 to $155,000.** We anticipate these expenditures will primarily relate to

---

## p24 — GOOGL Item 7 (passage, intent_first)

- sector: Communication Services / cap: large / FY2025 / detection: markdown_h3
- **query**: How did Alphabet vary debt by denomination and coupon structure?
- user_intent: how does the company manage interest rate or currency exposure
- curation_note: This passage details Alphabet’s mix of dollar and euro borrowings and fixed versus floating coupons, testing retrieval of concrete financing choices relevant to currency and interest-rate exposure.

**Evidence 1** — `GOOGL / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Liquidity and Material Cash Requirements

> …•May 2025: We issued $5.0 billion of US dollar-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 4.89%, and a weighted-average maturity of approximately 24 years. **We also issued €6.75 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.31%, and a weighted-average maturity of approximately 14 years.**   •November 2025: We issued $500 million of US dollar-denominated floating-rate senior unsecured notes and $17.0 billion of US dollar-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 4.92% and a weighted-average maturity of approximately 20 years. We also issued €6.5 billion of euro-denominated fixed-rate senior unsecured notes with a weighted-average coupon rate of 3.44% and a weighted-average maturity of approximately 16 years. As of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring in April 2026 and $6.0 billion expiring in April 2030. No amounts have been borrowed under the cre…

---

## p25 — CAT Item 7 (passage, intent_first)

- sector: Industrials / cap: large / FY2025 / detection: markdown_h3
- **query**: Caterpillar cybersecurity threats and board oversight disclosures
- user_intent: what cybersecurity threats and governance does the company describe
- curation_note: This cross-reference directs retrieval toward Item 1A, where the filing indicates its significant business risks are discussed.

**Evidence 1** — `CAT / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations`

> …ng principles, policies and critical estimates affect our Consolidated Financial Statements. Our discussion also contains certain forward-looking statements related to future events and expectations. **This MD&A should be read in conjunction with our discussion of cautionary statements and significant risks to the company’s business under Item 1A.** Risk Factors of the 2025 Form 10-K. Highlights for the full-year 2025 include:  •Sales and revenues for 2025 were $67.589 billion, an increase of $2.780 billion, or 4 percent, compared with $64.809 billion for 2024. Sales were higher…

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

## p35 — LLY Item 1 (passage, passage_first)

- sector: Health Care / cap: large / FY2025 / detection: markdown_h3
- **query**: What access measures accompany Lilly's tentative federal pricing pact?
- curation_note: This passage details Lilly-specific Medicaid, Medicare, and direct-purchase measures and tests retrieval of concrete commitments under a tentative government agreement.

**Evidence 1** — `LLY / 2025 / Item 1. Business` / block: Government Regulation of Our Operations and Products

> …rnment actions to reduce federal spending on entitlement programs, including Medicare and Medicaid, affects reimbursement for our products or services associated with the provision of our products. In November 2025, we announced preliminary voluntary agreements with the U.S. government in which, among other arrangements, we agreed to implement measures to lower Medicaid and certain other drug prices for U.S. patients and to launch new medicines with a more balanced pricing approach across developed nations. As part of these agreements, we expect Medicare beneficiaries will have access to discounted Lilly obesity medicines by July 1, 2026, and States will have the option to expand access to these discounted medicines through Medicaid. **We will also participate in a government direct-to-patient purchasing platform that will direct people in the U.S.** to offerings to purchase certain medicines from us at significant discounts to current list prices. The preliminary agreements also provide a three-year grace period during which time our products under a Section 232 investigation will not face tariffs, provided that we meet U.S. manufacturing inve…

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
- **query**: How will Coinbase respond to regulatory investigations?
- curation_note: This sentence captures Coinbase’s stated response to investigations and tests retrieval of a specific legal-proceedings commitment.

**Evidence 1** — `COIN / 2025 / Item 3. Legal Proceedings`

> …existing and intended future products, including our processes for listing assets, the classification of certain listed assets, our staking programs, and our stablecoin and yield-generating products. **We intend to cooperate fully with such investigations.** These examples are not exhaustive.…

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

## a01 — NVDA Item 1A/Item 7 (multi_passage, passage_first, ALTERNATE)

- sector: Information Technology / cap: large / FY2026 / detection: markdown_h3, markdown_h3
- **query**: How much went to private startups, and what threatens recovery?
- curation_note: This pair connects NVIDIA’s quantified fiscal 2026 startup investment with the company-specific impairment and total-loss risk of unsuccessful private holdings.

**Evidence 1** — `NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: Overview

> …ty to ramp production supply to the required volume and on a timely basis.   We have made, and expect to continue making, investments that support our technology roadmap and the broader AI ecosystem. **In fiscal year 2026, we made the following investments:  •We invested $17.5 billion in private companies and infrastructure funds, primarily to support early‑stage startups.** These investments include AI model makers that purchase our products directly or through CSPs. Many of these investments are illiquid and non‑marketable. The related early-stage startups may not become profitable in the near term, or at all, and there can be no assurance that we will realize a return on our investments. •We made investments in publicly-held equity securities where the value may fluctuate significantly due to changes in stock prices and could adversely affect our financial results.   •To support th…

**Evidence 2** — `NVDA / 2026 / Item 1A. Risk Factors` / block: Risks Related to Our Global Operating Business

> …continue to invest in companies to further our strategic objectives and to support certain key business initiatives, which could be subject to delays and challenges in obtaining regulatory approvals. Our investments in private companies include early-stage companies still defining their strategic direction. Many of the securities in which we invest are non-marketable and illiquid at the time of our initial investment. **To the extent any of the companies in which we invest are not successful, we could recognize an impairment and/or lose all or part of our investment.** We are finalizing an investment and partnership agreement with OpenAI. There is no assurance that we will enter into an investment and partnership agreement with OpenAI or that a transaction will be…

---

## a02 — DDOG Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Information Technology / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: Datadog 2025 revenue and overseas full-time employee distribution
- curation_note: This row tests retrieval of a revenue figure and international workforce percentages from separate risk-factor units.

**Evidence 1** — `DDOG / 2025 / Item 1A. Risk Factors` / block: Risks Associated with our Growth

> …ur recent rapid growth may not be indicative of our future growth. Our rapid growth also makes it difficult to evaluate our future prospects and may increase the risk that we will not be successful. **Our revenue was $3,427.2 million, $2,684.3 million and $2,128.4 million for the years ended December 31, 2025, 2024 and 2023, respectively.** You should not rely on the revenue growth of any prior quarterly or annual period as an indication of our future performance. Even if our revenue continues to increase, we expect that our revenue gro…

**Evidence 2** — `DDOG / 2025 / Item 1A. Risk Factors` / block: Risks Related to Intellectual Property

> …h relationships with new partners in order to expand into certain countries, and if we fail to identify, establish and maintain such relationships, we may be unable to execute on our expansion plans. **As of December 31, 2025, approximately 44% of our full-time employees were located outside of the United States, 34% of whom were located in France.** We expect that our international activities will continue to grow for the foreseeable future as we continue to pursue opportunities in existing and new international markets, which will require signi…

---

## a03 — LLY Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Health Care / cap: large / FY2025 / detection: markdown_h3, markdown_h3
- **query**: Trulicity patent expiry and manufacturing ramp execution risks
- curation_note: This evidence pairs Trulicity’s approaching protection loss with delays in activating added production capacity, testing retrieval across distinct product-lifecycle and supply-growth risks.

**Evidence 1** — `LLY / 2025 / Item 1A. Risk Factors` / block: Risks Related to Our Business and Industry

> …f effective intellectual property protection for certain of our products has resulted, and in the future is likely to continue to result, in rapid and severe declines in revenues for those products. In the ordinary course of their lifecycles, our products lose significant patent protection and/or data protection after a specified period of time. **For example, Trulicity will lose significant patent and remaining data protections in the next few years.** Some products also lose patent protection as a result of successful third-party challenges. We have faced, and remain exposed to, generic or biosimilar competition following the expiration or loss of such intellectual property protection. Patent expirations of competitive products may also shift market conditions for our products by contracting the market for branded products, impacting product access, or otherwise intensifying pricin…

**Evidence 2** — `LLY / 2025 / Item 1A. Risk Factors` / block: Risks Related to Our Operations

> …public health outbreaks, epidemics, or pandemics; (vi) periods of uneven economic growth or downturns; and (vii) the emergence or escalation of, or responses to international tension and conflicts. Difficulties in predicting or variability in demand and supply for our products and those of our competitors and the very long lead times necessary for the expansion and regulatory qualification of pharmaceutical manufacturing capacity have resulted, and in the future may result, in difficulty meeting demand, causing disruptions, shortages, or higher costs in the supply of our products. Despite our ongoing efforts to meet projected worldwide demand for our products by obtaining additional internal and contracted manufacturing capacity, there can be no assurances that such capacity increases that we expect will be needed to meet   33  future demand will be realized as expected or that we will meet demand in launched markets in the future. **Delays or challenges in operationalizing additional manufacturing capacity could limit our ability to capitalize on demand for our products.** Conversely, overestimation of demand or events that limit demand for our products or anticipated demand for product candidates would undermine our ability to realize the full benefit of significant c…

---

## a04 — PODD Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Health Care / cap: mid / FY2025 / detection: markdown_h4, markdown_h4
- **query**: What rival delivery formats and sensor partnerships affect Omnipod?
- curation_note: This pair tests cross-unit retrieval of competing diabetes-treatment formats and named CGM collaborators supporting Omnipod 5.

**Evidence 1** — `PODD / 2025 / Item 1A. Risk Factors`

> …apy to pump therapy, which could result in price pressure and decreased revenue.  Our current competitors or other companies may at any time develop additional products for the treatment of diabetes. **Several companies are working to develop and market new insulin “patch” pumps, smart pens, and other methods for the treatment of insulin-dependent diabetes.** If an existing or future competitor develops a product that competes with or is superior to our Omnipod products, we risk losing our position as the perceived technology leader in our field, and our…

**Evidence 2** — `PODD / 2025 / Item 1A. Risk Factors` / block: Risks Related to our Intellectual Property

> …ell our current products and commercialize new products. If we cannot obtain or retain these agreements, licenses, or other rights, we may not be able to sell, develop, or commercialize our products. **For example, we have commercial agreements with Dexcom and Abbott that allow us to sell Omnipod 5 with integration to Dexcom’s and Abbott’s CGM sensors.** The loss of any of these rights could impair the functionality of our products or prevent us from selling our products without significant development activities and regulatory approvals that may not…

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

## a06 — COIN Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Financials / cap: mid / FY2025 / detection: text_fallback, text_fallback
- **query**: Coinbase hot-wallet allocation cap and Bitcoin address compatibility
- curation_note: This pair tests retrieval of Coinbase’s 2% hot-wallet target alongside the network-specific limitation governing Bitcoin addresses.

**Evidence 1** — `COIN / 2025 / Item 1A. Risk Factors` / block: The Most Material Risks Related to Our Business and Financial Position

> …duct or error, or other compromise by third parties could hurt our brand and reputation, result in significant losses, and adversely affect our business, operating results, and financial condition. To mitigate the risks associated with the loss or theft of keys, we utilize both hot wallets and cold wallets in our custodial solutions. **We actively manage wallet balances and generally seek to hold no more than 2% of custodied assets in hot wallets at any given time.** Cold wallet private key materials are   43   stored and secured at facilities within the United States and internationally. We store the substantial majority of our own crypto asset holdings utilizin…

**Evidence 2** — `COIN / 2025 / Item 1A. Risk Factors` / block: Risks Related to Crypto Assets

> …when depositing and withdrawing from our platforms, respectively. Alternatively, a user may transfer crypto assets to a wallet address that the user does not own, control or hold the private keys to. In addition, each wallet address is only compatible with the underlying blockchain network on which it is created. **For instance, a Bitcoin wallet address can only be used to send and receive Bitcoins.** If any Ethereum or other crypto assets are sent to a Bitcoin wallet address, or if any of the foregoing errors occur, all of the customer’s sent crypto assets will be permanently and irretrievably lost with no means of recovery. We have encountered and expect to continue to encounter similar incidents with our customers. Such incidents could result in customer disputes, damage to our brand and reputation, legal claims agains…

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
- **query**: DECK customer concentration and international revenue exposure
- curation_note: This pair tests retrieval of quantitative sales exposure across major customers and non-US markets.

**Evidence 1** — `DECK / 2026 / Item 1A. Risk Factors` / block: have a material adverse effect on our business.

> …or improved results.   We face the risk that key customers may not increase their business with us as anticipated, may significantly reduce   purchases, or may terminate their relationships with us. **However, no single customer accounted for 10.0% or more   of our total net sales during fiscal year 2026.** The failure to increase sales to these customers could negatively affect   our growth prospects, and any reduction or loss of their business could materially and adversely affect our net sales   and…

**Evidence 2** — `DECK / 2026 / Item 1A. Risk Factors` / block: financial condition.

> …ightened volatility in global markets.   We conduct business outside the US, which exposes us to foreign currency exchange rate risk, and could   have a negative effect on our results of operations. **We operate on a global basis, with 41.7% of our total net sales for the year ended March 31, 2026, generated from   operations outside the US.** As we continue to expand our international operations, our sales and expenditures in   foreign currencies are expected to become increasingly material and subject to foreign currency exchange rate…

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
- **query**: ATF oversight and active injury lawsuits involving Axon CEDs
- curation_note: This pair tests cross-unit retrieval of product-specific regulatory oversight and existing litigation tied to Axon’s conducted-energy devices.

**Evidence 1** — `AXON / 2025 / Item 1A. Risk Factors` / block: Operational Risks

> …ations applicable to our firearm product, the TASER 10 CED, could result in governmental actions or litigation, potentially harming our business prospects, operating results and financial condition. The TASER 10 CED is primarily regulated by the Bureau of Alcohol, Tobacco, Firearms and Explosives (the “ATF”), which regulates the manufacture, sale and import of firearms in the United States primarily under the National Firearms Act of 1934, the Gun Control Act of 1968, and the Firearms Owners’ Protection Act of 1986, each as amended from time to time.   **The ATF conducts periodic audits of our facilities that hold federal firearms licenses.** If we fail to comply with ATF rules and regulations, the ATF may limit our activities or growth related to the TASER 10 CED, fine us, or, ultimately, suspend our ability to produce and sell the TASER 10 CED product line. Such audits may also expose operational inefficiencies or cause delays affecting production timelines or permitting. Also, various state and local laws, regulations, and ordinances relating to firear…

**Evidence 2** — `AXON / 2025 / Item 1A. Risk Factors` / block: Legal and Compliance Risks

> …e personal injury, wrongful death, product liability and other liability claims that could harm our reputation and adversely affect our business prospects, operating results and financial condition. Third parties often use our CED products in aggressive confrontations that may result in serious, permanent bodily injury or death. Our CED products may be associated with these injuries. A person, or the family members of a person, injured or killed in a confrontation or otherwise in connection with the use of our products, may bring legal action against us to recover damages on the basis of a number of theories, including wrongful death, personal injury, negligent design, defective product, product performance issues, or inadequate warnings or training. **We are currently subject to a number of such lawsuits and have been and may be in the future subject to significant adverse judgments and settlements.** We may also be subject to lawsuits alleging criminal misuse of our products. We have no control over how our products are used by our customers or other end-users and cannot ensure they are used cons…

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
- **query**: Which dependencies threaten oil output growth and emerging-energy investment timing?
- curation_note: This pair links ExxonMobil’s production dependence on exploration success with its emerging-business dependence on durable policy and market support.

**Evidence 1** — `XOM / 2025 / Item 1A. Risk Factors` / block: Operational and Other Factors

> …tive to competition. For projects in which we are not the operator, we depend on the management effectiveness of one or more co-venturers whom we do not control.  Exploration and development program. **Our ability to maintain and grow our oil and gas production depends on the success of our exploration and development efforts.** Among other factors, we must continuously improve our ability to identify the most promising resource prospects and apply our project management expertise to bring discovered resources online as sche…

**Evidence 2** — `XOM / 2025 / Item 1A. Risk Factors` / block: Climate Change and Energy Transition

> …s in technology as discussed above, meeting society's needs for energy and reducing emissions will require appropriate support from governments and private participants throughout the global economy. Our ability to develop and deploy CCS and other new energy technologies at commercial scale, and the growth and future returns of LCS and other emerging businesses in which we invest, will depend in part on the development of stable and supportive government policies and markets. **Failure or delay of these policies or markets to materialize or be maintained could adversely impact or delay these investments.** Policy and other actions that result in restricting the availability of hydrocarbon products without a commensurate reduction in demand may have unpredictable adverse effects, including increased com…

---

## a14 — NEE Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Utilities / cap: large / FY2025 / detection: markdown_h4, markdown_h4
- **query**: 2021 campaign-finance accusations and uninsured transmission infrastructure
- curation_note: This pair tests cross-unit retrieval of a dated FPL legal allegation and NEE’s specific gap in property insurance coverage.

**Evidence 1** — `NEE / 2025 / Item 1A. Risk Factors` / block: Regulatory, Legislative and Legal Risks

> …could be adversely affected by allegations that FPL or NEE has violated laws, by any investigations or proceedings that arise from such allegations, or by ultimate determinations of legal violations. **For example, media articles were first published in 2021 that alleged, among other things, Florida state and federal campaign finance law violations by FPL.** FPL and NEE cannot provide assurance that the outcome of any allegations of violations of law will not result in the imposition of material fines, penalties, or otherwise result in other sanctions or…

**Evidence 2** — `NEE / 2025 / Item 1A. Risk Factors` / block: Development and Operational Risks

> …rance coverage, NEE may be required to pay costs associated with losses or adverse future events involving these entities.  NEE and FPL generally are not fully insured against all significant losses. **For example, NEE, including FPL, does not have property insurance coverage for a substantial portion of its transmission and distribution property and natural gas pipeline assets.** A loss for which NEE or FPL is not fully insured could have a material adverse effect on NEE's and FPL's business, financial condition, results of operations and prospects.  NEE invests in natural ga…

---

## a15 — PLD Item 1A (multi_passage, passage_first, ALTERNATE)

- sector: Real Estate / cap: large / FY2025 / detection: text_fallback, text_fallback
- **query**: Prologis foreign-currency exposure and major U.S. market concentrations
- curation_note: This pair tests retrieval across quantitative overseas asset exposure and named domestic logistics markets with significant holdings.

**Evidence 1** — `PLD / 2025 / Item 1A. Risk Factors` / block: •foreign ownership restrictions in operations with the respective countries; and

> …ment may adversely affect our results of operations and financial position.  We hold significant real estate investments in international markets where the U.S. dollar is not the functional currency. **At December 31, 2025, approximately $13.7 billion, or 13.8% of our total consolidated assets, were invested in a currency other than the U.S.** dollar, principally the British pound sterling, Canadian dollar, euro and Japanese yen. For the year ended December 31, 2025, $432.8 million, or 6.6% of our total consolidated segment NOI, was denominated in a currency other than the U.S. dollar. See Note 16 to the Consolidated Financial Statements in Item 8. Financial Statements and Supplementary Data for more information on these amounts. As a result, we are exposed to foreign curre…

**Evidence 2** — `PLD / 2025 / Item 1A. Risk Factors` / block: Risks Related to our Business

> …of the investment we have located in California, a downturn in California’s economy or real estate conditions, including state income tax and property tax laws, could adversely affect our business. In addition to California, we also have significant holdings (defined as more than 3% of total consolidated investment before depreciation) in operating properties in certain markets located in Atlanta, Chicago, Dallas/Fort Worth, Houston, Lehigh Valley, New Jersey/New York City, Seattle and South Florida. **Of these markets, no single market contributed more than 10% of our total consolidated investment before depreciation in operating properties.** Our operating performance could be adversely affected if conditions become less favorable in any of the markets in which we have a concentration of properties. Conditions such as an oversupply of logistics space or a reduction in demand for logistics space, among other factors, may impact operating conditions. Any material oversupply of logistics space or m…

---

## a16 — LIN Item 7 (passage, passage_first, ALTERNATE)

- sector: Materials / cap: large / FY2025 / detection: markdown_h4
- **query**: Factors behind unchanged APAC revenue in 2025
- curation_note: This passage decomposes flat APAC sales into acquisition gains offset by volume and currency declines, testing retrieval of segment-specific revenue drivers.

**Evidence 1** — `LIN / 2025 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: APAC

> …vestitures2 %  — %  The APAC segment includes Linde's industrial gases operations in approximately 15 Asian and South Pacific countries and regions including China, Australia, India and South Korea. Sales  Sales for the APAC segment were flat in 2025 versus 2024. Acquisitions increased sales by 2%. Volumes decreased sales by 1%. **Currency translation decreased sales by 1% primarily due to the weakening of the Australian dollar and Korean won against the U.S.** dollar. Cost pass-through and pricing were flat. Operating Profit  Operating profit in the APAC segment increased $15 million, or 1%, in 2025 versus 2024. The increase was primarily driven by productivity initiatives and acquisitions, partially of…

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
- **query**: Deckers fiscal year-end buyback capacity and purchase obligation
- curation_note: This evidence combines the remaining repurchase authorization with management’s discretion, testing retrieval of both a concrete capital-allocation amount and its nonbinding terms.

**Evidence 1** — `DECK / 2026 / Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations` / block: objectives, and drive stockholder value, including by potentially repurchasing additional shares of our common

> **stock. As of March 31, 2026, the aggregate remaining approved amount under our stock repurchase program is   $1,549,602.** Our stock repurchase program does not obligate us to acquire any amount of common stock and may   be suspended at any time at our discretion. On May 20, 2026, our Board approved an additional authorization of $3,500,000 to repurchase shares of our   common stock under the same conditions as the prior stock repurchase program, resulting i…

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
