# Groww Mutual Fund FAQ RAG Assistant

A trustworthy, compliant, and transparent RAG (Retrieval-Augmented Generation) chatbot designed to answer factual queries regarding Groww Mutual Fund schemes. It operates on a strict **facts-only** compliance model and refuses to provide investment advice, recommendations, or return projections.

---

## Scope

### Target AMC
* **Groww Asset Management Company (AMC)**

### Covered Schemes
1. **Equity Funds**: Large Cap, Flexi Cap, Multicap, Midcap, Small Cap, Value Fund, ELSS Tax Saver, Banking & Financial Services, Focused Fund.
2. **Index / ETF Funds**: Nifty 50 Index, Nifty Next 50 Index, Nifty Total Market Index, Nifty Smallcap 250 Index, Nifty Private Bank Index, Nifty EV & New Age Automotive ETF FoF, Nifty India Defence ETF FoF, Nifty India Defence ETF.
3. **Hybrid Funds**: Aggressive Hybrid Fund, Balanced Advantage Fund, Arbitrage Fund.
4. **Debt Funds**: Liquid Fund, Overnight Fund, Short Duration Fund, Money Market Fund, Corporate Bond Fund, Banking & PSU Debt Fund, Gilt Fund.
5. **Commodity Funds**: Gold ETF FoF, Silver ETF FoF, Gold ETF.

---

## Key Features

1. **Facts-Only Compliance**:
   - Programmed to refuse queries seeking investment suggestions, performance forecasts, comparisons, or recommendations (e.g., "should I invest in...", "which fund is better...").
   - Intercepts and blocks non-factual advisory prompts immediately using intent routing and keyword heuristics.
2. **Deterministic Citations**:
   - Every factual response includes the exact official source URL and the data's last updated date.
3. **Local Vector Database**:
   - Uses **ChromaDB** with local embeddings (`all-MiniLM-L6-v2`) to run 100% free vector indexing and semantic retrieval.
4. **Combined Intent Classifier**:
   - Combines query classification and refinement into a single LLM request (saves 50% on API costs/overhead).

---

## Technology Stack

* **Frontend**: Next.js 16 (React 19, Tailwind CSS)
* **Backend**: FastAPI (Python 3.10)
* **Database**: ChromaDB (Persistent local vector storage)
* **LLM API**: Google Gemini API (`gemini-3.5-flash` / `gemini-3.1-flash-lite`)

---

## Setup & Running Instructions

### Prerequisites
* Python 3.10+
* Node.js 20+
* Docker (Optional, for running containers)
* A Google Gemini API Key

### Local Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/work-samirk/groww-chatbot.git
   cd groww-chatbot
   ```

2. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   PORT=8005
   ```

3. **Backend Setup**:
   ```bash
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Run the ingest script to build the vector DB
   python -m backend.ingest

   # Start the FastAPI server
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8005
   ```

4. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   
   # Run local dev server
   npm run dev
   ```
   Open `http://localhost:3005` in your browser.

---

## Running with Docker

You can run both services locally on localhost or on a virtual machine using the official Docker images built for `linux/amd64` (Ubuntu 22.04 base).

### 1. Run Backend Container (Port 8005)
```bash
docker run -d \
  -p 8005:8005 \
  -e GEMINI_API_KEY="your_gemini_api_key_here" \
  --name groww-backend-container \
  samirpm/portfolio:groww-chatbot-backend
```

### 2. Run Frontend Container (Port 3005)
```bash
docker run -d \
  -p 3005:3005 \
  --name groww-frontend-container \
  samirpm/portfolio:groww-chatbot-frontend
```
Open `http://localhost:3005` to access the chat interface.

---

## Known Limitations

1. **Static Factsheets**: Data is sourced from snapshot web scrapes. Real-time NAV fluctuations or intraday changes are not accounted for until the daily scheduled scraper ETL runs.
2. **Context Refusal**: If a mutual fund scheme is not part of the Groww AMC target schemes list, the chatbot will politely clarify that the fund is out of scope and suggest valid options.
3. **No Mathematical Projections**: The system does not compute future compound interest or compare scheme returns dynamically (returns are cited directly from static factsheet tables only).
