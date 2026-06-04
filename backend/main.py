import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb

# Load environment variables
load_dotenv()

# Configure GenAI models
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Define models
MODEL_CLASSIFIER = "gemini-2.0-flash-lite"
MODEL_GENERATOR = "gemini-2.0-flash"
MODEL_EMBEDDING = "models/text-embedding-004"

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

from typing import Optional

# Pydantic schemas for request/response
class QueryRequest(BaseModel):
    query: str

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
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text.strip())
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

    # Step 3: Run factual retrieval and generation
    hits = retrieve_context(query)
    response_data = generate_rag_answer(query, hits)
    
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
