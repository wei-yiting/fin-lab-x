# Product Requirements Document (PRD): FinLab-X

## 1. Context and Architectural Philosophy

**FinLab-X** is an experimental AI project designed to provide just-in-time, deep research on US growth stocks. It abandons traditional, static databases in favor of an on-demand, JIT (Just-in-Time) data ingestion and reasoning architecture.

### Architectural Shift: Single Orchestrator + Modular Skills

Based on modern "AI-Native" best practices, FinLab-X will **not** utilize a complex multi-agent routing. Instead, it adopts a **Single Orchestrator Agent + Skills + MCP (Model Context Protocol)** model.

- **The Orchestrator:** A powerful foundational model acts as the single central brain.
- **MCP (Connectivity):** Acts as the system's "senses and tentacles," responsible for fetching external raw data.
- **Skills (Expertise):** Encapsulated, composable procedural knowledge (Python/Bash scripts) stored in dedicated folders. The Orchestrator dynamically calls these skills when specific financial analysis (e.g., moving average calculation, DCF) is required.
- **Progressive Disclosure:** To protect the context window, the Orchestrator initially only sees metadata about available Skills. Detailed instructions and code are loaded only when the Orchestrator decides a specific Skill is needed.

This approach solves the "cold start" problem, provides dynamic modifiability, and treats code as a universal interface.

---

## 2. The "Laboratory" Evolutionary Path (v1 - v5)

The project is structured as a laboratory to demonstrate the evolution of AI capabilities and the resolution of common financial analysis pain points (latency, structural reasoning, and numerical hallucinations).

### Evaluation-Driven Development (EDD)

Every phase must be evaluated using a predetermined "Golden Dataset" of 30-100 financial questions. Progress is measured by tangible improvements in specific metrics (e.g., Ragas scores for Faithfulness, Context Precision).

---

### Phase 1: v1 - The Naive Generalist (Baseline)

- **Goal:** Establish a baseline to demonstrate the flaws of relying solely on LLMs + basic web search for complex financial queries (specifically highlighting "information noise" and lack of cross-document reasoning).
- **Architecture:** Direct LLM Function Calling (Reactive). **No dedicated Router.**
- **Tools Available:**
  - `tavily_financial_search`: For recent news and sentiment.
  - `yfinance_stock_quote`: For basic quantitative metrics.
  - `sec_filing_retriever`: A simplified grabber that pulls raw text sections (e.g., Item 1A Risk Factors) directly into the prompt without vectorization.
- **Expected Failure Points:** Context window exhaustion, tool misuse (calling SEC retrieval unnecessarily), and logic gaps due to lack of planning.
- **Evaluation Focus:** Baseline scores for hallucination rate and tool utilization accuracy.

---

### Phase 2: v2 - The Intelligent Reader (Structured RAG)

- **Goal:** Solve the "long-context hallucination" problem and improve reading comprehension of dense financial texts.
- **Architecture:** Introduction of a Basic Classifier/Router (Chat vs. RAG).
- **New Capabilities (Data Foundry):**
  - Vector Database (e.g., Qdrant) integration.
  - Intelligent chunking strategies (e.g., semantic or section-based parsing) for SEC filings (10-K, 10-Q).
- **Evaluation Focus:** Improvement in Context Precision and Faithfulness (Ragas) compared to v1.

---

### Phase 3: v3 - The Quant Specialist (Structured Data Integration)

- **Goal:** Solve "numerical hallucinations" by enabling precise queries on structured financial data.
- **Architecture:** Tri-State Router (Qualitative / Quantitative / Web Search).
- **New Capabilities (Data Foundry & Skills):**
  - Local OLAP Database integration (e.g., DuckDB).
  - **JIT ETL:** On-demand scripts to fetch API data (yfinance/Alpha Vantage), flatten JSON, and ingest into DuckDB.
  - **Text-to-SQL Skill:** Teaching the Orchestrator to generate safe SQL queries to calculate metrics (e.g., gross margin trends).
- **New Capabilities (UI):** Dynamic rendering of Data Charts and Financial Tables based on JSON output.
- **Evaluation Focus:** Absolute accuracy on numerical queries and Text-to-SQL success rates.

---

### Phase 4: v4 - The Detective (Graph Reasoning)

- **Goal:** Solve the "implicit relationship" problem to identify hidden supply chain or competitive risks.
- **Architecture:** Semantic Router incorporating Graph-Query logic.
- **New Capabilities (Data Foundry & Skills):**
  - Graph Database integration (e.g., Memgraph or Neo4j).
  - **Ontology Design:** Defining Nodes (Company, Product) and Edges (SUPPLIER, COMPETES).
  - **Entity Extraction Skill:** JIT extraction of relationships from SEC "Business" sections to populate the graph.
  - **Text-to-Cypher Skill:** Enabling the Orchestrator to query relationship paths.
- **New Capabilities (UI):** Interactive Network Graph visualization.
- **Evaluation Focus:** Recall rate for identifying documented relationships within SEC filings.

---

### Phase 5: v5 - The Analyst (Synthesis and Generative UI)

- **Goal:** Combine all capabilities into a cohesive, interactive terminal experience that performs multi-step reasoning.
- **Architecture:** The Orchestrator matures into a "Planner," orchestrating multiple tools and skills sequentially (e.g., Plan -> Execute SQL Skill -> Execute Graph Skill -> Synthesize).
- **New Capabilities:**
  - Complete integration of the Single Orchestrator + Skills + MCP architecture.
  - **Generative UI Streaming:** The frontend dynamically renders widgets (Charts, Graphs, Tables, expandable text cards) using the Vercel AI SDK based on the Orchestrator's synthesized findings.
- **Evaluation Focus:** End-to-end task completion rate and subjective UX quality of the Generative UI response.
