# Context: Mutual Fund FAQ Assistant (Groww RAG Chatbot)

## Overview
The goal of this project is to build a **facts-only FAQ assistant for mutual fund schemes**, using Groww as the reference product context. The assistant will answer objective, verifiable queries about mutual funds by retrieving information exclusively from official public sources such as Asset Management Company (AMC) websites, AMFI, and SEBI. 

The system is designed with a strict compliance-first approach: it must never provide investment advice, recommendations, or speculative content. Every response must be concise, accurate, and back-referenced with a single official source link.

---

## Objectives
1. **Accurate Retrieval**: Design a lightweight Retrieval-Augmented Generation (RAG)-based assistant.
2. **Official Source Grounding**: Rely on a curated corpus of official documents.
3. **Factual & Concise Q&A**: Limit responses to short, factual, and source-backed answers.
4. **Refusal Handling**: Strictly refuse advisory, speculative, or performance-comparison queries.

---

## Scope of Work

### 1. Corpus Definition
The assistant's knowledge base will be constructed from:
- A single selected **Asset Management Company (AMC)**.
- **15–25 official public URLs** including:
  - Scheme Factsheets
  - KIM (Key Information Memorandum)
  - SID (Scheme Information Document)
  - AMC FAQ/help pages
  - AMFI/SEBI guidance pages
  - Guides on downloading statements or capital gains reports

### 2. FAQ Assistant Requirements
The assistant must answer objective queries such as:
- Expense ratios of schemes
- Exit load details
- Minimum SIP amount
- ELSS lock-in periods
- Riskometer classifications
- Benchmark indices
- Fund Manager names
- Step-by-step processes to download statements or capital gains reports

**Response Formatting Constraints:**
- **Length**: Maximum of **3 sentences** per response.
- **Citations**: Exactly **one citation link** pointing to the official source.
- **Footer**: Every response must include the footer:  
  `Last updated from sources: <date>`

### 3. Refusal Handling
The assistant must refuse non-factual or advisory queries (e.g., *"Should I invest in this fund?"*, *"Which fund is better?"*).
- **Refusal Tone**: Polite and clearly worded.
- **Refusal Style**: Reinforce the facts-only limitation and redirect the user by providing a relevant educational link (e.g., AMFI or SEBI official resource).

### 4. User Interface (Minimal & Sleek)
A simple, clean interface featuring:
- A welcome message introducing the assistant.
- Three example questions to guide the user.
- A prominent disclaimer snippet:  
  `“Facts-only. No investment advice.”`

---

## Constraints & Compliance Guidelines

| Category | Strict Guidelines & Constraints |
| :--- | :--- |
| **Data & Sources** | Use ONLY official public sources (AMC, AMFI, SEBI). No third-party blogs or aggregator websites. |
| **Privacy & Security** | DO NOT collect, store, or process sensitive user data (PAN, Aadhaar, Account Numbers, OTPs, Email, Phone Numbers). |
| **Content Restrictions** | Absolute ban on investment advice or subjective recommendations. No return calculations or performance comparisons (for performance queries, link directly to the official factsheet). |
| **Transparency** | Answers must be short, factual, verifiable, and include the source link and last updated date. |

---

## Expected Deliverables
1. **README Document**:
   - Complete setup instructions.
   - Selected AMC and schemes included in the corpus.
   - Architecture overview (RAG pipeline details).
   - Known limitations of the assistant.
2. **Disclaimer Snippet**:
   - Manifested visibly in the UI: `“Facts-only. No investment advice.”`
3. **Working Codebase**:
   - The RAG ingestion and retrieval system.
   - User-friendly web/chat interface.

---

## Success Criteria
- **High Accuracy**: Answers are correctly retrieved and match official data.
- **Strict Compliance**: Zero instances of advisory or opinionated responses.
- **Clean Citations**: Proper verification links accompanying all answers.
- **Polite Refusals**: Graceful handling of out-of-scope/advisory questions.
- **Elegant UI**: Modern, clean, and responsive user interface matching the Groww-inspired theme.
