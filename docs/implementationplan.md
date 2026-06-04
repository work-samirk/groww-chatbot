# Implementation Plan: Mutual Fund FAQ Assistant (Groww RAG Chatbot)

This document outlines a phase-wise plan to implement the RAG-based Mutual Fund FAQ Assistant using **Gemini API** for LLM reasoning/embeddings and **ChromaDB** for local vector storage. 

We prioritize **free-tier and open-source tools** to ensure zero-cost development, calling out paid services only where they are optional or alternative solutions.

---

## 1. Cost & Tooling Matrix (Free vs. Paid)

| Task | Recommended Free Tool | Paid Alternative (Optional) | Notes / Details |
| :--- | :--- | :--- | :--- |
| **LLM & Embeddings** | **Gemini 2.0 Flash / Gemini 2.0 Flash-Lite** (via Google AI Studio) | OpenAI API (GPT-4o-mini) | **Free Tier**: Google AI Studio provides 15 RPM / 1500 RPD for free, which is more than enough for development and testing. |
| **Vector Database** | **ChromaDB** (Local & Open Source) | Pinecone (Serverless) | **ChromaDB** runs locally on the host machine for free, requiring no cloud account or credentials. |
| **Web Scraper** | **Playwright** + **BeautifulSoup4** | ScrapingBee / Zyte | Playwright is open-source and free, capable of executing client-side JS to scrape hydrated data from `groww.in`. |
| **Daily Scheduler** | **Local Crontab** or **GitHub Actions** | AWS EventBridge / Cronitor | **GitHub Actions** provides 2,000 free runner minutes per month for private repositories (unlimited for public repos). |
| **Web UI Hosting** | **Vercel** / **Netlify** / **Firebase Hosting** | AWS S3 / Amplify | Generous free tiers for hosting static frontends and API functions. |
| **Backend API** | **FastAPI** (Local development) | Render / Heroku | Runs locally for free. Render has a free tier for deploying web services. |

---

## 2. Phase-Wise Implementation Checklist

### Phase 1: Environment Setup & Project Initialization
*Goal: Configure dependencies and directory structure.*

- [x] **Directory Structure**:
  Create the following folders:
  ```text
  ├── data/                  # Scraped raw data & local database
  │   ├── raw/               # Scraped JSON files
  │   └── chroma/            # Persistent ChromaDB storage
  ├── docs/                  # Design & architecture docs
  ├── scraper/               # Playwright scraper scripts
  ├── backend/               # FastAPI app & RAG pipeline
  ├── frontend/              # Next.js frontend web interface
  ├── requirements.txt       # Python dependencies
  └── README.md              # Setup & run guide
  ```
- [x] **Dependency Setup**:
  Define `requirements.txt`:
  ```text
  fastapi==0.110.0
  uvicorn==0.28.0
  chromadb==0.4.24
  google-generativeai==0.4.0
  playwright==1.42.0
  beautifulsoup4==4.12.3
  pydantic==2.6.4
  python-dotenv==1.0.1
  ```
- [x] **Credential Configuration**:
  Set up a `.env` file with:
  ```env
  GEMINI_API_KEY=your_google_ai_studio_api_key
  PORT=8005
  ```

---

### Phase 2: Web Scraper Development (Playwright + BS4)
*Goal: Automate content extraction from the 30 specified Groww URLs.*

- [x] **Target URL List**: Define a configuration array containing the 30 exact URLs provided in the architecture document.
- [x] **Scraper Core Logic (`scraper/scraper.py`)**:
  - Launch Playwright headlessly.
  - Add human-like headers (`User-Agent`) and 2-second sleep delays to prevent rate limits.
  - Hydrate the JavaScript elements to ensure tabular data (Exit load, Expense ratio) loads.
- [x] **Content Parser**:
  - Extract text cleanly: Scheme Name, Category, Expense Ratio, Exit Load, Minimum SIP, Benchmarks, Fund Managers.
  - Parse HTML tables into structured Markdown text blocks (e.g. `| Period | Exit Load |`).
- [x] **Output Storage**:
  - Save scraped data as structured JSON files in `data/raw/` with fields: `scheme_name`, `url`, `content`, `tables`, and `scraped_at`.

---

### Phase 3: Vector Storage & Embedding Pipeline (ChromaDB)
*Goal: Segment text chunks, generate embeddings, and load them into ChromaDB.*

- [x] **Text Chunking Strategy**:
  - Implement semantic-based chunking with `RecursiveCharacterTextSplitter`.
  - Maintain tables as complete, undivided chunks so tabular relationships are not broken.
- [x] **Metadata Construction**:
  - Append mandatory tags to each chunk:
    - `source_url`: The exact Groww URL.
    - `last_updated_date`: Current ISO date of the scraping run.
    - `scheme_name`: Target scheme name.
- [x] **ChromaDB Loading (`backend/ingest.py`)**:
  - Instantiate ChromaDB with local persistent storage (`data/chroma/`).
  - Configure the embedding generator using Gemini API's `models/text-embedding-004` (free tier).
  - Ingest chunks and metadata, verifying indexing via simple validation tests.

---

### Phase 4: Automated Daily Scheduler
*Goal: Automate daily execution of scraping and DB upserts.*

- [x] **ETL Script (`scraper/run_etl.py`)**:
  - Create a master script that runs the Scraper, compares page hashes to detect updates, and triggers the Ingestion script to upsert changes in ChromaDB.
- [x] **Scheduler Options**:
  - **Local Cron** (Mac/Linux):
    Add a daily crontab entry:
    ```bash
    0 0 * * * cd "/Users/samirkhan/Nextleap Projects/Groww RAG Chatbot" && ./venv/bin/python scraper/run_etl.py >> data/cron_etl.log 2>&1
    ```
  - **GitHub Actions (Cloud)**:
    Configure a workflow file `.github/workflows/daily_scrape.yml`:
    ```yaml
    name: Daily Mutual Fund Data Sync
    on:
      schedule:
        - cron: '0 0 * * *' # Every day at midnight
    jobs:
      scrape:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - name: Set up Python
            uses: actions/setup-python@v4
          - name: Install dependencies
            run: pip install -r requirements.txt && playwright install
          - name: Run ETL
            env:
              GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
            run: python scraper/run_etl.py
    ```

---

### Phase 5: Query Guardrails & RAG Engine Implementation
*Goal: Classify query intents, retrieve documents, and synthesize answers.*

- [x] **Input Guardrail & Intent Classifier**:
  - Create a classifier using a lightweight prompt structure in **Gemini 2.0 Flash-Lite**:
    - *Task*: Classify if user query is **Factual** (numerical details, names, step-by-step processes) or **Advisory** (opinions, comparisons, buy/sell recommendations).
- [x] **Refusal Router**:
  - If query is advisory, return:
    - Polite refusal response.
    - Static educational links: [AMFI Mutual Funds Sahi Hai](https://www.mutualfundssahihai.com) or [SEBI Investor Education Portal](https://investor.sebi.gov.in).
- [x] **ChromaDB Retriever**:
  - For factual queries, query ChromaDB to get the top 3–5 matching chunks.
- [x] **LLM Generation Pipeline**:
  - Prompt **Gemini 2.0 Flash** with the retrieved context.
  - **Strict Prompt Instructions**:
    1. Maximum of 3 sentences.
    2. Exactly 1 citation link matching the `source_url` from the retrieved chunk.
    3. Mandatory footer: `Last updated from sources: <date>` using the chunk's metadata.
    4. Refuse to answer if context does not contain the answer.

---

### Phase 6: Minimal Chat Interface (Frontend)
*Goal: Build a modern, responsive chat interface resembling Groww's UI.*

- [ ] **Aesthetics**:
  - Dark mode with glassmorphism panels.
  - Accent Color: Groww Mint Green (`#00D09C`).
  - Font: Google Fonts (Inter or Outfit).
- [ ] **Key Layout Features**:
  - **Header**: Persistent disclaimer badge: `“Facts-only. No investment advice.”`
  - **Welcome Area**: Three clickable example questions:
    1. *"What is the exit load of Groww Large Cap Fund?"*
    2. *"Who is the fund manager of Groww Balance Advantage Fund?"*
    3. *"How do I invest in mutual funds?"* (Testing refusal routing)
  - **Chat Area**: Text bubbles separating user query, bot response, citation links, and date footers.

---

## 3. Verification & Testing Protocol

### Automated Evaluation Scripts
1. **Scraper Test**: Run the scraper script manually on 2–3 sample URLs and verify the scraped tables parse correctly.
2. **Intent Classification Test**: Feed 20 sample prompts (10 factual, 10 advisory) and assert that all 10 advisory queries trigger the SEBI/AMFI redirection response.
3. **Prompt Restriction Test**: Verify that response lengths do not exceed 3 sentences and citation URLs match the ground truth.

### Manual Verification
- Deploy locally and interact with the chatbot to test edge cases (e.g., trying to input fake PAN/Aadhaar details to verify privacy guardrails).
- Verify page responsiveness on mobile and desktop viewports.
