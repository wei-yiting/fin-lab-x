# Retrieval Diff — Naive vs Metadata-filter

_Generated 2026-08-27T02:04:15.068319+00:00_

- Naive collection: `sec_filings_naive` (no payload index, no `is_tenant`, query without filter)
- Metadata-filter collection: `sec_filings_rag_filter_en_baseline` (`is_tenant=True` on ticker, query with `must=[ticker=X]`)

Both collections share identical embeddings — naive was populated via Qdrant scroll + upsert from the metadata-filter collection. Only build-time payload-index config and query-time filter differ.

---

## Query: What supply chain and manufacturing process dependency risks does AMD face?
**Target**: `AMD` (AMD)

### Naive collection (no filter, no payload index, no tenant)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | AMD | Item 1A | 0.7118 | ### Operational and Technology Risks We rely on third parties to manufacture our products, and if they are unable to do… |
| 2 | ✓ | AMD | Item 1A | 0.6922 | If essential equipment, materials, substrates or manufacturing processes are not available to manufacture our products,… |
| 3 | ✗ | NVDA | Item 1A | 0.6670 | Dependency on third-party suppliers and their technology to manufacture, assemble, test, or package our products reduce… |
| 4 | ✓ | AMD | Item 1A | 0.6607 | ### Operational and Technology Risks •We rely on third parties to manufacture our products, and if they are unable to d… |
| 5 | ✗ | NVDA | Item 1A | 0.6593 | ### Risks Related to Demand, Supply, and Manufacturing Long manufacturing lead times and uncertain supply and capacity … |

### Metadata-filter collection (filter ticker, tenant-aware HNSW)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | AMD | Item 1A | 0.7118 | ### Operational and Technology Risks We rely on third parties to manufacture our products, and if they are unable to do… |
| 2 | ✓ | AMD | Item 1A | 0.6922 | If essential equipment, materials, substrates or manufacturing processes are not available to manufacture our products,… |
| 3 | ✓ | AMD | Item 1A | 0.6607 | ### Operational and Technology Risks •We rely on third parties to manufacture our products, and if they are unable to d… |
| 4 | ✓ | AMD | Item 1A | 0.6450 | We depend on third-party companies for the design, manufacture and supply of motherboards, software, memory and other c… |
| 5 | ✓ | AMD | Item 1A | 0.6309 | Failure to achieve expected manufacturing yields for our products could negatively impact our results of operations. Se… |

---

## Query: What supply chain risks does Google's latest earnings report mention?
**Target**: `GOOGL` (Google)

### Naive collection (no filter, no payload index, no tenant)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | GOOGL | Item 1A | 0.6927 | We have experienced and may in the future experience supply shortages, price increases, quality issues, or longer lead … |
| 2 | ✗ | INTC | _unknown | 0.6639 | We rely upon a complex global supply chain. We have a highly complex global supply chain composed of thousands of suppl… |
| 3 | ✗ | AAPL | Item 1A | 0.6274 | The Company depends on component and product manufacturing and logistical services provided by outsourcing partners, ma… |
| 4 | ✗ | AMD | Item 1A | 0.6199 | ### General Risks Our worldwide operations are subject to political, legal and economic risks and natural disasters, wh… |
| 5 | ✗ | NVDA | Item 1A | 0.6124 | ### Risks Related to Demand, Supply, and Manufacturing Long manufacturing lead times and uncertain supply and capacity … |

### Metadata-filter collection (filter ticker, tenant-aware HNSW)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | GOOGL | Item 1A | 0.6927 | We have experienced and may in the future experience supply shortages, price increases, quality issues, or longer lead … |
| 2 | ✓ | GOOGL | Item 1A | 0.5911 | Our devices have had, and in the future may have, quality issues resulting from design, manufacturing, or operations. S… |
| 3 | ✓ | GOOGL | Item 1A | 0.5813 | new and innovative products and services that better serve the needs of our users, advertisers, customers, content prov… |
| 4 | ✓ | GOOGL | Item 1A | 0.5745 | Within Google Services, we continue to invest heavily in devices, including our smartphones, home devices, and wearable… |
| 5 | ✓ | GOOGL | Item 1A | 0.5587 | ### General Risks Our operating results may fluctuate, which makes our results difficult to predict and could cause our… |

---

## Query: What customer concentration risks does NVIDIA face?
**Target**: `NVDA` (NVIDIA)

### Naive collection (no filter, no payload index, no tenant)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | NVDA | Item 7 | 0.7342 | #### Concentration of Revenue We refer to customers who purchase products directly from NVIDIA as direct customers, suc… |
| 2 | ✓ | NVDA | Item 1A | 0.6651 | We have experienced periods where we receive a significant amount of our revenue from a limited number of customers, an… |
| 3 | ✗ | INTC | _unknown | 0.6645 | We receive a significant portion of our revenue from a limited number of customers. Collectively, our three largest cus… |
| 4 | ✓ | NVDA | Item 15 | 0.6545 | (2)In fiscal year 2026, we estimate 76% of Data Center revenue from Taiwan-headquartered customers was attributed to en… |
| 5 | ✗ | INTC | _unknown | 0.6502 | We are subject to numerous risks associated with the evolving market for products with AI capabilities. The markets and… |

### Metadata-filter collection (filter ticker, tenant-aware HNSW)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | NVDA | Item 7 | 0.7342 | #### Concentration of Revenue We refer to customers who purchase products directly from NVIDIA as direct customers, suc… |
| 2 | ✓ | NVDA | Item 1A | 0.6651 | We have experienced periods where we receive a significant amount of our revenue from a limited number of customers, an… |
| 3 | ✓ | NVDA | Item 15 | 0.6545 | (2)In fiscal year 2026, we estimate 76% of Data Center revenue from Taiwan-headquartered customers was attributed to en… |
| 4 | ✓ | NVDA | Item 1A | 0.6285 | •changes that impact the ecosystem for the architectures underlying our products and technologies; •government actions … |
| 5 | ✓ | NVDA | Item 1A | 0.6170 | We have entered into an intellectual property license arrangement with Groq, Inc., or Groq, that required significant, … |

---

## Query: What is AMD's strategy for its AI accelerator products?
**Target**: `AMD` (AMD)

### Naive collection (no filter, no payload index, no tenant)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | AMD | Item 1 | 0.7502 | ### Our Strategy We believe AI is shaping the next era of computing and its full potential will be realized when it bec… |
| 2 | ✓ | AMD | Item 1 | 0.7272 | ### Overview AMD drives innovation in high performance and AI computing to solve the world’s most important challenges.… |
| 3 | ✓ | AMD | Item 1 | 0.6887 | 2 [Table of Conten](#i597c59c6d5f1435f9e98177202b657fc_7)[t](#i597c59c6d5f1435f9e98177202b657fc_7)[s](#i597c59c6d5f1435… |
| 4 | ✓ | AMD | Item 7 | 0.6748 | During 2025, we launched multiple leadership products and made significant progress executing our AI strategy. A priori… |
| 5 | ✓ | AMD | Item 1 | 0.6439 | We develop comprehensive software stacks that include development tools, compilers and drivers to enable our high-perfo… |

### Metadata-filter collection (filter ticker, tenant-aware HNSW)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | AMD | Item 1 | 0.7502 | ### Our Strategy We believe AI is shaping the next era of computing and its full potential will be realized when it bec… |
| 2 | ✓ | AMD | Item 1 | 0.7272 | ### Overview AMD drives innovation in high performance and AI computing to solve the world’s most important challenges.… |
| 3 | ✓ | AMD | Item 1 | 0.6887 | 2 [Table of Conten](#i597c59c6d5f1435f9e98177202b657fc_7)[t](#i597c59c6d5f1435f9e98177202b657fc_7)[s](#i597c59c6d5f1435… |
| 4 | ✓ | AMD | Item 7 | 0.6748 | During 2025, we launched multiple leadership products and made significant progress executing our AI strategy. A priori… |
| 5 | ✓ | AMD | Item 1 | 0.6439 | We develop comprehensive software stacks that include development tools, compilers and drivers to enable our high-perfo… |

---

## Query: What supply chain concentration issues affect Apple's hardware products?
**Target**: `AAPL` (Apple)

### Naive collection (no filter, no payload index, no tenant)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | AAPL | Item 8 | 0.7320 | ### Concentrations in the Available Sources of Supply of Materials and Product Although most components essential to th… |
| 2 | ✓ | AAPL | Item 1A | 0.6861 | The Company depends on component and product manufacturing and logistical services provided by outsourcing partners, ma… |
| 3 | ✓ | AAPL | Item 1 | 0.6799 | ### Supply of Components Although most components essential to the Company’s business are generally available from mult… |
| 4 | ✗ | INTC | _unknown | 0.6782 | We rely upon a complex global supply chain. We have a highly complex global supply chain composed of thousands of suppl… |
| 5 | ✓ | AAPL | Item 1A | 0.6604 | Additionally, the Company’s new products often utilize custom components available from only one source. When a compone… |

### Metadata-filter collection (filter ticker, tenant-aware HNSW)
| Rank | Match | Ticker | Item | Score | Snippet (first ~120 chars) |
|------|-------|--------|------|-------|----------------------|
| 1 | ✓ | AAPL | Item 8 | 0.7320 | ### Concentrations in the Available Sources of Supply of Materials and Product Although most components essential to th… |
| 2 | ✓ | AAPL | Item 1A | 0.6861 | The Company depends on component and product manufacturing and logistical services provided by outsourcing partners, ma… |
| 3 | ✓ | AAPL | Item 1 | 0.6799 | ### Supply of Components Although most components essential to the Company’s business are generally available from mult… |
| 4 | ✓ | AAPL | Item 1A | 0.6604 | Additionally, the Company’s new products often utilize custom components available from only one source. When a compone… |
| 5 | ✓ | AAPL | Item 1A | 0.5723 | Many of the Company’s operations, retail stores and facilities, as well as critical business operations of the Company’… |

---
