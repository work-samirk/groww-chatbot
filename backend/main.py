import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb

# Load environment variables
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")), override=True)

# Configure GenAI models
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Define models
MODEL_CLASSIFIER = "gemini-3.1-flash-lite"
MODEL_GENERATOR = "gemini-3.5-flash"
MODEL_EMBEDDING = "models/gemini-embedding-001"

# Initialize FastAPI App
app = FastAPI(title="Groww Mutual Fund FAQ RAG Assistant API")

# Enable CORS for Next.js frontend (typically port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to persistent ChromaDB storage
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROMA_DIR = os.path.join(BASE_DIR, "data/chroma")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(name="groww_mutual_funds")

from typing import Optional, List

# Pydantic schemas for request/response
class Message(BaseModel):
    sender: str
    text: str

class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Message]] = None

class QueryResponse(BaseModel):
    answer: str
    source_link: Optional[str] = None
    last_updated: Optional[str] = None
    is_refusal: bool

# 1. Intent Classifier using Gemini 2.0 Flash-Lite
def classify_intent(query: str) -> str:
    if not GEMINI_API_KEY:
        # Default mock intent for testing without key
        return "FACTUAL"

    prompt = f"""You are a mutual fund compliance assistant. Your task is to classify the user's query into one of two categories: 'FACTUAL' or 'ADVISORY'.

- 'FACTUAL': Questions seeking objective, historical, or statutory facts, figures, features, processes, or values of a mutual fund scheme. Examples:
  * "What is the exit load of Groww Large Cap Fund?"
  * "Who is the fund manager of Groww Balance Advantage Fund?"
  * "What is the expense ratio?"
  * "How do I download my capital gains statement?"
  
- 'ADVISORY': Questions seeking subjective opinions, comparisons, predictions, buy/sell/hold decisions, performance evaluation, or financial advice. Examples:
  * "Should I invest in Groww Large Cap Fund?"
  * "Which fund gives the best returns?"
  * "Is this a good mutual fund to buy right now?"
  * "Compare Groww Value Fund vs Large Cap Fund and tell me which is better."

User Query: "{query}"

Output ONLY a JSON object:
{{"intent": "FACTUAL"}} or {{"intent": "ADVISORY"}}"""

    try:
        model = genai.GenerativeModel(MODEL_CLASSIFIER)
        response = model.generate_content(prompt)
        text_content = response.text.strip()
        import re
        text_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_content, flags=re.MULTILINE | re.IGNORECASE).strip()
        data = json.loads(text_content)
        return data.get("intent", "FACTUAL").upper()
    except Exception as e:
        print(f"Error during classification: {e}")
        # Default fallback to be safe and let pipeline handle it
        return "FACTUAL"

# 2. Retrieve context from ChromaDB
def retrieve_context(query: str, top_k: int = 4):
    if not GEMINI_API_KEY:
        return []
        
    try:
        # Generate query embedding
        emb_response = genai.embed_content(
            model=MODEL_EMBEDDING,
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = emb_response["embedding"]
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        hits = []
        if results and results['documents'] and len(results['documents'][0]) > 0:
            for idx in range(len(results['documents'][0])):
                hits.append({
                    "document": results['documents'][0][idx],
                    "metadata": results['metadatas'][0][idx]
                })
        return hits
    except Exception as e:
        print(f"Error during ChromaDB retrieval: {e}")
        return []

# 3. RAG Generator using Gemini 2.0 Flash
def generate_rag_answer(query: str, hits: list) -> dict:
    if not hits:
        return {
            "answer": "I do not have access to objective facts matching your query in the official fund documentation.",
            "source_link": None,
            "last_updated": None,
            "is_refusal": False
        }

    # Format the retrieved documents into context block
    context_blocks = []
    for hit in hits:
        context_blocks.append(hit["document"])
    context = "\n---\n".join(context_blocks)
    
    # We take the metadata from the top-scoring hit
    top_metadata = hits[0]["metadata"]
    source_url = top_metadata.get("source_url")
    last_updated = top_metadata.get("last_updated_date")

    prompt = f"""You are a Facts-Only Mutual Fund Q&A Assistant.
Answer the user's query strictly based on the provided official context. You must conform to the following strict compliance rules:

1. Rely ONLY on facts stated in the context below. Do NOT assume, speculate, extrapolate, or use outside knowledge.
2. If the context does not contain the specific answer to the user's question, refuse politely by stating: "I do not have access to this information in the official documents."
3. Your answer must be maximum 3 sentences.
4. Do NOT provide any investment advice, recommendations, predictions, or comparisons. Keep it completely objective and factual.

Retrieved Context:
{context}

User Query: {query}

Synthesized Answer:"""

    try:
        model = genai.GenerativeModel(MODEL_GENERATOR)
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        return {
            "answer": answer,
            "source_link": source_url,
            "last_updated": last_updated,
            "is_refusal": False
        }
    except Exception as e:
        print(f"Error during response generation: {e}")
        return {
            "answer": "An error occurred while generating the response. Please try again.",
            "source_link": None,
            "last_updated": None,
            "is_refusal": False
        }

@app.get("/api/health")
def health_check():
    return {"status": "ok", "indexed_chunks": collection.count()}

def refine_query(query: str, history: List[Message]) -> dict:
    if not GEMINI_API_KEY:
        return {"action": "RETRIEVE", "search_query": query}
        
    history_str = ""
    if history:
        for msg in history:
            sender = getattr(msg, "sender", "user")
            text = getattr(msg, "text", "")
            history_str += f"{sender.upper()}: {text}\n"
        
    prompt = f"""You are a query refiner for a Groww Mutual Fund RAG Chatbot.
Analyze the user's new query and the conversation history to choose the next action.

Conversation History:
{history_str}

User's New Query: "{query}"

Task:
1. Does the query ask about specific mutual fund properties (like minimum SIP, fund manager, exit load, expense ratio, allotment date, sector, etc.)?
2. If yes, is the specific mutual fund scheme name clear from either the new query or the conversation history?
   - Note: Groww has multiple funds (e.g. Groww Large Cap Fund, Groww Nifty 50 Index Fund, Groww Multicap Fund, etc.)
3. If the specific fund name is clear or can be inferred, output:
   {{"action": "RETRIEVE", "search_query": "<A fully rewritten search query that includes the scheme name and the question for vector search. Example: 'What is the exit load of Groww Nifty 50 Index Fund'>"}}
4. If the query asks about a property but the fund is NOT specified (and cannot be inferred from history), output:
   {{"action": "CLARIFY", "clarification_message": "Could you please specify which Groww mutual fund you are referring to? (e.g., Groww Nifty 50 Index Fund, Groww Large Cap Fund, etc.)"}}
5. If the query is a general greeting, conversational follow-up, or meta-question (e.g., 'hello', 'thanks', 'why did you only mention 2 funds?'), output:
   {{"action": "RETRIEVE", "search_query": "{query}"}}

Output ONLY a raw JSON block (no markdown, no backticks)."""

    try:
        model = genai.GenerativeModel(MODEL_CLASSIFIER)
        response = model.generate_content(prompt)
        text_content = response.text.strip()
        import re
        text_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_content, flags=re.MULTILINE | re.IGNORECASE).strip()
        return json.loads(text_content)
    except Exception as e:
        print(f"Error during query refinement: {e}")
        return {"action": "RETRIEVE", "search_query": query}

@app.post("/api/chat", response_model=QueryResponse)
def handle_chat(payload: QueryRequest):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Step 1: Classify intent
    intent = classify_intent(query)
    print(f"Query: '{query}' -> Intent: {intent}")

    # Step 2: Route request
    if intent == "ADVISORY":
        # Static refusal response with compliant SEBI/AMFI educational links
        return QueryResponse(
            answer="I can only provide factual, objective details about mutual fund schemes. For investment advice, please consult a registered financial advisor. You can read more about mutual fund investments on AMFI or the SEBI Investor Education Portal.",
            source_link="https://www.mutualfundssahihai.com", # AMFI Portal
            last_updated=None,
            is_refusal=True
        )

    # Step 3: Refine query (handle ambiguous queries and conversational rewrites)
    refinement = refine_query(query, payload.history or [])
    action = refinement.get("action", "RETRIEVE")
    print(f"Refinement Action: {action}")

    if action == "CLARIFY":
        return QueryResponse(
            answer=refinement.get("clarification_message", "Could you please specify which Groww mutual fund you are referring to?"),
            source_link=None,
            last_updated=None,
            is_refusal=False
        )

    # Step 4: Run factual retrieval and generation
    search_query = refinement.get("search_query", query)
    print(f"Search Query: '{search_query}'")
    hits = retrieve_context(search_query)
    response_data = generate_rag_answer(search_query, hits)
    
    return QueryResponse(
        answer=response_data["answer"],
        source_link=response_data["source_link"],
        last_updated=response_data["last_updated"],
        is_refusal=response_data["is_refusal"]
    )

if __name__ == "__main__":
    import uvicorn
    # Read port from env, fallback to 8005
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)
