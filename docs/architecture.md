# System Architecture: Mutual Fund FAQ Assistant (Groww RAG Chatbot)

This document details the phase-wise system architecture for the Mutual Fund FAQ Assistant. The system leverages a **Retrieval-Augmented Generation (RAG)** pipeline to answer objective, factual questions about mutual fund schemes from official documents, while strictly enforcing compliance guardrails against investment advice.

---

## 1. System Architecture Diagram

The flowchart below visualizes the end-to-end data ingestion (offline) and query-response (online) pipelines.

```mermaid
graph TD
    %% Offline Pipeline: Data Ingestion
    subgraph Offline Ingestion Pipeline (ETL)
        A1[Daily Cron Scheduler] --> A2[Web Scraper: Target Groww URLs]
        A2 --> A3[Semantic & Table-Aware Chunking]
        A3 --> A4[Metadata Enrichment: Source URL, Timestamp]
        A4 --> A5[Embedding Generator]
        A5 --> A6[(Vector Database)]
    end

    %% Online Pipeline: Request-Response Flow
    subgraph Online Query Pipeline
        U[User Chat Interface] -->|Query| Q1[Input Guardrail / Intent Classifier]
        
        %% Refusal Path
        Q1 -->|Advisory / Speculative Query| R1[Refusal Router]
        R1 -->|Educational Resource Link| U
        
        %% Factual Path
        Q1 -->|Factual / Objective Query| Q2[Query Expansion & Vectorization]
        Q2 -->|Embedding Vector| Q3[Retriever: Hybrid Semantic + Keyword Search]
        A6 -->|Query Matches| Q3
        
        %% Reranking & Synthesis
        Q3 -->|Top Chunks & Metadata| Q4[Re-ranker Engine]
        Q4 -->|Filtered Context| Q5[LLM Generator: Grounded Prompt]
        Q5 -->|Synthesized Response| G1[Output Verification Guardrail]
        
        %% Compliance & Output
        G1 -->|Compliant: Factual, Citations, Footer| U
        G1 -->|Non-Compliant / Hallucinated| G2[Fallback / Refusal Response]
        G2 --> U
    end

    %% Styles
    classDef offline fill:#f9f9fb,stroke:#2b2b2b,stroke-width:1px;
    classDef online fill:#f4fbf7,stroke:#1db954,stroke-width:1px;
    class Offline Ingestion Pipeline offline;
    class Online Query Pipeline online;
```

---

## 2. Phase-Wise Architecture Breakdown

### Phase 1: Data Ingestion, Scraping & Daily Scheduling Pipeline (ETL)
This phase is responsible for daily, automated scraping, processing, chunking, and embedding of mutual fund scheme data restricted **strictly** to the official target Groww Mutual Fund pages.

#### 1. Scope of Scraped URLs
The scraper is restricted to target **only** the following official Groww AMC URLs. No other external sources or aggregators are crawled:

*   **AMC Directory Landing Page**:
    *   `https://groww.in/mutual-funds/amc/groww-mutual-funds`
*   **🟠 Equity Funds**:
    *   `https://groww.in/mutual-funds/groww-large-cap-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-flexi-cap-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-multicap-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-midcap-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-small-cap-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-value-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-elss-tax-saver-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-banking-financial-services-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-focused-fund-direct-growth`
*   **🟠 Index / ETF Funds (Equity)**:
    *   `https://groww.in/mutual-funds/groww-nifty-total-market-index-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-nifty-smallcap-250-index-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-nifty-private-bank-index-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-nifty-ev-new-age-automotive-etf-fof-direct-growth`
    *   `https://groww.in/mutual-funds/groww-nifty-india-defence-etf-fof-direct-growth`
    *   `https://groww.in/mutual-funds/groww-nifty-india-defence-etf-direct-growth`
    *   `https://groww.in/mutual-funds/groww-nifty-50-index-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-nifty-next-50-index-fund-direct-growth`
*   **🟡 Hybrid Funds**:
    *   `https://groww.in/mutual-funds/groww-aggressive-hybrid-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-balanced-advantage-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-arbitrage-fund-direct-growth`
*   **🔵 Debt Funds**:
    *   `https://groww.in/mutual-funds/groww-liquid-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-overnight-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-short-duration-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-money-market-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-corporate-bond-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-banking-psu-debt-fund-direct-growth`
    *   `https://groww.in/mutual-funds/groww-gilt-fund-direct-growth`
*   **🟤 Commodity / Other FoFs**:
    *   `https://groww.in/mutual-funds/groww-gold-etf-fof-direct-growth`
    *   `https://groww.in/mutual-funds/groww-silver-etf-fof-direct-growth`
    *   `https://groww.in/mutual-funds/groww-gold-etf-direct-growth`

#### 2. Web Scraper Specification
- **Framework**: `Playwright` or `Puppeteer` (configured headlessly to handle dynamic client-side hydration of fund pages).
- **Target Fields**: Scrapes critical fields dynamically from the page layouts:
  - Fund performance metrics & NAV histories (to extract factsheets or direct factual links).
  - Expense ratios, exit loads, tax implications.
  - Risk classification metrics (Riskometer) and benchmark indices.
  - Portfolio holdings structure and fund manager details.
  - Min SIP / one-time investment thresholds.
- **Anti-Scraping / Respectful Crawling**: Configured with request delays, custom User-Agent headers, and retry strategies to avoid rate limits.

#### 3. Automated Daily Scheduler
- **Mechanism**: A Cron task configured via GitHub Actions or an internal cron scheduler (such as `APScheduler` or system `cron`).
- **Timing**: Fires **every day at midnight (00:00 UTC)**.
- **Incremental Updates**:
  1. Runs the Scraper on the complete set of exact URLs.
  2. Compares scraped hashes/contents with the existing database.
  3. Detects updates (e.g., NAV changes, updated expense ratios).
  4. Reparses updated content, recreates vector embeddings, and performs upsert operations on the Vector Database.
  5. Updates the metadata field `last_updated_date` to the current execution date.

#### 4. Document Parser, Chunking & Embeddings
- **Table-Aware Chunking**: Tables (such as exit load schedules, asset allocation tables) are extracted cleanly and kept intact within single text blocks with descriptions.
- **Metadata Tagging**: Mandatory metadata fields appended to every chunk:
  - `source_url`: The exact page URL from the list of URLs.
  - `document_type`: Web Page / Factsheet.
  - `last_updated_date`: Date of the latest scraper run.
  - `scheme_name`: Target mutual fund scheme name (extracted from URL/HTML).
- **Vector Database Ingestion**: Upserts chunk embeddings into `ChromaDB` or `Pinecone`.

---

### Phase 2: Intent Classification & Input Guardrails
Before querying the Vector Database, incoming queries are routed through an input guardrail to detect advisory queries early.

1. **Intent Classifier**:
   - Evaluates the user query to classify the intent into one of two categories:
     - **Factual**: Objective questions about facts (e.g., *"What is the exit load?"*, *"Who is the fund manager?"*).
     - **Advisory/Subjective**: Questions asking for opinions, comparisons, or predictions (e.g., *"Is this a good fund?"*, *"Should I buy?"*, *"Which fund gives better returns?"*).
   - Implementation: Small fine-tuned classifier, structured JSON LLM output, or keyword-based regex matching.
2. **Refusal Router**:
   - If classified as **Advisory**, the system bypasses retrieval and LLM generation entirely.
   - It issues a pre-formatted, polite refusal:  
     *“I can only provide factual, objective details about mutual fund schemes. For investment advice, please consult a registered financial advisor. You can read more about mutual fund investments on [AMFI Mutual Funds Sahi Hai](https://www.mutualfundssahihai.com) or the [SEBI Investor Education Portal](https://investor.sebi.gov.in).”*
3. **Query Pre-Processing**:
   - For **Factual** queries, standardizes terminology (e.g., mapping *"charge for leaving"* to *"exit load"*).

---

### Phase 3: Retrieval & Re-ranking Engine
This phase retrieves the most relevant facts from the vector store while maintaining high precision.

1. **Hybrid Retrieval**:
   - Combines semantic search (vector similarity matching) with keyword search (BM25) to catch specific terms (like exact scheme names or numbers).
2. **Metadata Filtering**:
   - Restricts search space strictly to the selected AMC's corpus.
3. **Re-ranking (Optional but Recommended)**:
   - Uses a light re-ranker model (e.g., Cohere Re-rank or Cohere Cross-Encoder) to re-evaluate the top 10 retrieved chunks.
   - Re-ranking ensures that exact matching tables, factsheets, or lock-in details move to the top of the context payload.

---

### Phase 4: Synthesis, Generation, & Output Verification
This phase controls the generation of the response using an LLM (e.g., Gemini Flash), enforcing formatting and content constraints.

1. **System Prompt Design**:
   - Instructs the LLM to act strictly as a "Facts-Only Assistant".
   - Mandates that if the information is not present in the provided context, the model must refuse to answer.
   - Enforces formatting rules:
     - Response must be **maximum 3 sentences**.
     - Must reference **exactly one** citation link from the chunk's metadata.
     - Must append the **Last updated** date footer.
2. **Response Generation**:
   - Calls the LLM with the retrieved context and system prompt.
3. **Output Verification (Post-Guardrails)**:
   - Evaluates the generated output programmatically or through a secondary light check:
     - **Hallucination Check**: Ensures the LLM did not add speculative returns or unsourced facts.
     - **Length Check**: Validates that sentence count $\le 3$.
     - **Citation Validation**: Confirms the citation link is present, matches the metadata, and is a valid official URL.
     - If checks fail, a safe fallback template is returned.

---

### Phase 5: UI & API Presentation Layer
The front end of the application is designed to be sleek, user-friendly, and compliant with Groww's design principles.

1. **UI Elements**:
   - **Disclaimer Banner**: A persistent banner at the top/bottom: `“Facts-only. No investment advice.”`
   - **Example Queries**: A set of clickable quick-start questions (e.g., *"What is the exit load of Scheme X?"*).
   - **Chat window**: A clean message bubble window showing user questions and assistant responses with highlighted citation links.
2. **API Endpoint**:
   - `/api/chat`: Accepts the user query and returns a structured JSON payload:
     ```json
     {
       "answer": "The exit load for SBI Bluechip Fund is 1% if redeemed within 1 year from the date of allotment. There is no exit load if redeemed after 1 year.",
       "source_link": "https://www.sbimf.com/en-us/downloads/sid",
       "last_updated": "2026-05-15",
       "is_refusal": false
     }
     ```

---

## 3. Technology Stack Recommendations

| Component | Technology Choices | Rationale |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js (React) | Modern, sleek, responsive interface matching Groww's color palette (Mint Green, Sleek Grey, Dark Mode). |
| **Backend API** | Python (FastAPI) | Lightweight, fast execution, handles JSON requests and manages ChromaDB in-process. |
| **Parser / Chunking** | Python (`PyPDF`, `Unstructured`, `LlamaIndex`) | Best-in-class libraries for layout-aware PDF reading and table parsing. |
| **Vector DB** | ChromaDB (local) or Pinecone (cloud-based) | Simple setup, fast querying, native metadata filtering. |
| **LLM Orchestrator** | Firebase AI Logic / Google Antigravity SDK | Directly integrates Gemini API securely with pre-configured schemas. |
| **Embedding Model** | `text-embedding-3-small` or Gemini Embeddings | High semantic accuracy with low latency. |
| **GenAI Model** | Gemini 3.5 Flash & Gemini 3.1 Flash-Lite | Extremely fast responses, industry-leading low latency, and highly optimized token costs. We use 3.1 Flash-Lite for intent classification and 3.5 Flash for context synthesis. |

---

## 4. Compliance & Security Guardrails Matrix

| Scenario | System Action | Rationale / Compliance Standard |
| :--- | :--- | :--- |
| **User asks for subjective advice** (e.g., *"Which fund should I buy?"*) | **Refuse immediately** and provide educational link. | Strictly complies with SEBI's restrictions against unregistered financial advisory. |
| **User enters sensitive PII** (e.g., Aadhaar, OTPs, PAN) | **Filter out / block** PII prior to processing query. | Ensures user privacy and data security. |
| **User queries performance statistics** | Retrieve only official factsheet URL, **do not compute or compare returns**. | Prevents outdated or speculative data generation; guides users to official sources. |
| **Data not found in Vector DB** | Output polite refusal: *"I do not have access to this information."* | Minimizes hallucination risk (strictly bounds the LLM to the context). |
