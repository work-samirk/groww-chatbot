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

from chromadb.utils import embedding_functions
default_ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(name="groww_mutual_funds", embedding_function=default_ef)

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

# 1. Rule-Based Heuristics (Quick-Pass Guardrails)
def check_heuristics(query: str, history: List[Message]) -> Optional[dict]:
    q_lower = query.lower().strip()
    
    # Simple greetings
    greetings = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings"}
    if q_lower in greetings or any(q_lower.startswith(g + " ") for g in greetings):
        return {
            "answer": "Hello! I am your Groww Mutual Fund Assistant. How can I help you today? You can ask me about fund managers, exit loads, minimum SIP amounts, and more.",
            "source_link": None,
            "last_updated": None,
            "is_refusal": False
        }
        
    # Simple closures/thanks
    closings = {"thanks", "thank you", "thank you so much", "bye", "goodbye", "exit"}
    if q_lower in closings or any(q_lower.startswith(c) for c in closings):
        return {
            "answer": "You're welcome! Let me know if you have any other questions about Groww mutual funds.",
            "source_link": None,
            "last_updated": None,
            "is_refusal": False
        }
        
    # Intercept user complaints / meta-questions about the bot not replying
    complaints = {
        "you are not replying", "you are not answering", "why are you not replying",
        "why you dont have", "why you don't have", "why can't you answer", 
        "are you there", "reply to me", "please reply", "you are not replying for my query"
    }
    if q_lower in complaints or any(c in q_lower for c in complaints):
        return {
            "answer": "I apologize if my previous responses were not helpful. I can only provide objective, factual details about Groww mutual funds if they are documented in the official fund documentation. Could you please specify which Groww mutual fund you are asking about, and what details (such as minimum SIP, exit load, or fund manager) you need?",
            "source_link": None,
            "last_updated": None,
            "is_refusal": False
        }

    # Intercept request to list all schemes
    list_all_patterns = [
        "list all of them", "list all schemes", "show all funds", "list of all funds",
        "can you list all", "list all funds", "list all mutual funds", "show all mutual funds"
    ]
    if any(p in q_lower for p in list_all_patterns):
        schemes_list = (
            "Here are the mutual fund schemes offered by Groww:\n\n"
            "1. Groww Aggressive Hybrid Fund\n"
            "2. Groww Arbitrage Fund\n"
            "3. Groww Banking & Financial Services Fund\n"
            "4. Groww ELSS Tax Saver Fund\n"
            "5. Groww Gilt Fund\n"
            "6. Groww Gold ETF FOF\n"
            "7. Groww Large Cap Fund\n"
            "8. Groww Liquid Fund\n"
            "9. Groww Money Market Fund\n"
            "10. Groww Multicap Fund\n"
            "11. Groww Nifty 50 Index Fund\n"
            "12. Groww Nifty EV & New Age Automotive ETF FoF\n"
            "13. Groww Nifty India Defence ETF FoF\n"
            "14. Groww Nifty Next 50 Index Fund\n"
            "15. Groww Nifty Private Bank Index Fund\n"
            "16. Groww Nifty Smallcap 250 Index Fund\n"
            "17. Groww Nifty Total Market Index Fund\n"
            "18. Groww Overnight Fund\n"
            "19. Groww Short Term Fund\n"
            "20. Groww Silver ETF FoF\n"
            "21. Groww Small Cap Fund\n"
            "22. Groww Value Fund\n\n"
            "Please specify which fund you'd like to know about!"
        )
        return {
            "answer": schemes_list,
            "source_link": "https://groww.in/mutual-funds/amc/groww-mutual-funds",
            "last_updated": "2026-06-04",
            "is_refusal": False
        }

    # Intercept request to list gold/silver/commodity funds specifically
    if ("list" in q_lower or "show" in q_lower) and ("gold" in q_lower or "silver" in q_lower or "commodity" in q_lower or "commodities" in q_lower):
        return {
            "answer": "Groww offers the following commodities/precious metals schemes:\n1. **Groww Gold ETF FOF Direct Growth**\n2. **Groww Silver ETF FoF Direct Growth**\n\nWhich of these would you like to know more about?",
            "source_link": "https://groww.in/mutual-funds/amc/groww-mutual-funds",
            "last_updated": "2026-06-04",
            "is_refusal": False
        }
        
    # Explicit advisory keywords (compliance guardrail)
    advisory_keywords = [
        "should i invest", "where should i invest", "which is better", 
        "is it a good buy", "is it good to invest", "best mutual fund",
        "which fund gives the best return", "give me advice", "financial advice",
        "should i buy", "should i sell", "recommend me", "which one to buy"
    ]
    if any(k in q_lower for k in advisory_keywords):
        return {
            "answer": "I can only provide factual, objective details about mutual fund schemes. For investment advice, please consult a registered financial advisor. You can read more about mutual fund investments on AMFI or the SEBI Investor Education Portal.",
            "source_link": "https://www.mutualfundssahihai.com",
            "last_updated": None,
            "is_refusal": True
        }

    # Intercept general platform-level questions
    platform_patterns = ["how to start a sip", "how to invest", "how to buy", "how to start investing", "how do i start a sip"]
    if any(p in q_lower for p in platform_patterns):
        return {
            "answer": "To start a SIP on Groww:\n1. Log in to your Groww account.\n2. Search for the Groww Mutual Fund scheme you want to invest in.\n3. Click on 'Start SIP' and enter your monthly investment amount and date.\n4. Complete the one-time KYC and bank mandate setups to automate payments.",
            "source_link": "https://groww.in/mutual-funds",
            "last_updated": "2026-06-04",
            "is_refusal": False
        }

    redeem_patterns = ["how to redeem", "how to sell", "how to withdraw", "how to close my investment"]
    if any(p in q_lower for p in redeem_patterns):
        return {
            "answer": "To redeem your mutual fund investments on Groww:\n1. Go to your Dashboard or Portfolio holdings on the Groww app or website.\n2. Select the mutual fund scheme you want to redeem.\n3. Click on 'Redeem', specify either a custom amount or select 'Redeem All' to withdraw your entire balance.\n4. Confirm the transaction, and the funds will be credited to your bank account within the standard redemption timeline (typically T+1 to T+3 working days).",
            "source_link": "https://groww.in/mutual-funds",
            "last_updated": "2026-06-04",
            "is_refusal": False
        }

    kyc_patterns = ["kyc", "complete kyc", "kyc registration", "verify my account"]
    if any(p in q_lower for p in kyc_patterns):
        return {
            "answer": "To complete your KYC on Groww:\n1. Complete your online registration by entering your PAN card and Aadhaar details.\n2. Verify your identity with a quick online selfie/video verification.\n3. Upload your address proof and digital signature.\n4. Once submitted, Groww processes your paperless KYC within a few hours.",
            "source_link": "https://groww.in",
            "last_updated": "2026-06-04",
            "is_refusal": False
        }
        
    return None

# 1b. Combined Intent Classifier and Query Refinement (Saves 1 LLM Call)
def classify_and_refine_query(query: str, history: List[Message]) -> dict:
    if not GEMINI_API_KEY:
        return {
            "intent": "FACTUAL",
            "action": "RETRIEVE",
            "search_query": query,
            "clarification_message": None
        }
        
    history_str = ""
    if history:
        for msg in history:
            sender = getattr(msg, "sender", "user")
            text = getattr(msg, "text", "")
            history_str += f"{sender.upper()}: {text}\n"
            
    prompt = f"""You are a compliance guardrail and query refiner for a Groww Mutual Fund RAG Chatbot.
Analyze the user's new query and the conversation history.

Conversation History:
{history_str}

User's New Query: "{query}"

Valid Mutual Fund Schemes in the database (You MUST use these exact names when rewriting queries):
- Groww Aggressive Hybrid Fund Direct Growth
- Groww Arbitrage Fund Direct Growth
- Groww Banking & Financial Services Fund Direct Growth
- Groww ELSS Tax Saver Fund Direct Growth
- Groww Gilt Fund Direct Growth
- Groww Gold ETF FOF Direct Growth
- Groww Large Cap Fund Direct Growth
- Groww Liquid Fund Direct Growth
- Groww Money Market Fund Direct Growth
- Groww Multicap Fund Direct Growth
- Groww Nifty 50 Index Fund Direct Growth
- Groww Nifty EV & New Age Automotive ETF FoF Direct Growth
- Groww Nifty India Defence ETF FoF Direct Growth
- Groww Nifty Next 50 Index Fund Direct Growth
- Groww Nifty Private Bank Index Fund Direct Growth
- Groww Nifty Smallcap 250 Index Fund Direct Growth
- Groww Nifty Total Market Index Fund Direct Growth
- Groww Overnight Fund Direct Growth
- Groww Short Term Fund Direct Growth
- Groww Silver ETF FoF Direct Growth
- Groww Small Cap Fund Direct Growth
- Groww Value Fund Direct Growth

Tasks & Strict Compliance Rules:
1. Classify the user's query into 'FACTUAL' or 'ADVISORY'.
   - 'FACTUAL': Questions seeking objective, historical, or statutory facts, features, processes, or values of a mutual fund scheme.
   - 'ADVISORY': Questions seeking subjective opinions, predictions, buy/sell/hold decisions, comparisons, or financial recommendations.
   
2. If the query is FACTUAL, determine if it asks about properties of a mutual fund.
   - You MUST match references to the EXACT Groww mutual fund names from the "Valid Mutual Fund Schemes" list above.
   - If the user refers to a general type of fund (e.g. "gold fund", "gold etf") and there is only ONE matching Groww scheme (e.g. "Groww Gold ETF FOF Direct Growth"), you MUST automatically infer it and set action to 'RETRIEVE' (do not ask for clarification).
   - If multiple Groww schemes could match and you need to clarify, set action to 'CLARIFY'.
   - CRITICAL: When suggesting examples in your clarification message, you MUST ONLY suggest schemes from the "Valid Mutual Fund Schemes" list above. Never suggest schemes from other fund houses (like Nippon, HDFC, SBI, etc.). All schemes in our system start with "Groww".

3. CRITICAL: If the action is 'RETRIEVE', you MUST generate a 'search_query'.
   - The 'search_query' MUST be a fully self-contained, standalone question that combines the user's latest query with the context from the Conversation History.
   - For example, if history asks "What is the exit load?" and user says "gold fund", the search_query MUST be "What is the exit load for Groww Gold ETF FOF Direct Growth?".
   - NEVER output a null or short phrase for 'search_query' if the action is RETRIEVE.

Output ONLY a JSON block (no markdown, no backticks, no extra text):
{{
  "intent": "FACTUAL" or "ADVISORY",
  "action": "RETRIEVE" or "CLARIFY",
  "search_query": "<fully rewritten standalone question combining history and current query, or null if clarifying>",
  "clarification_message": "<polite clarification message suggesting ONLY valid Groww schemes, or null>"
}}"""

    try:
        model = genai.GenerativeModel(MODEL_CLASSIFIER)
        response = model.generate_content(prompt)
        text_content = response.text.strip()
        import re
        text_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_content, flags=re.MULTILINE | re.IGNORECASE).strip()
        return json.loads(text_content)
    except Exception as e:
        print(f"Error during combined classify and refine: {e}")
        return {
            "intent": "FACTUAL",
            "action": "RETRIEVE",
            "search_query": query,
            "clarification_message": None
        }

# 2. Retrieve context from ChromaDB using local embedding function
def retrieve_context(query: str, top_k: int = 4):
    try:
        # Query ChromaDB directly using text (ChromaDB automatically generates local embeddings)
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Format results
        hits = []
        if results and results.get('documents') and len(results['documents']) > 0 and len(results['documents'][0]) > 0:
            for idx in range(len(results['documents'][0])):
                hits.append({
                    "document": results['documents'][0][idx],
                    "metadata": results['metadatas'][0][idx]
                })
        print(f"ChromaDB retrieval for '{query}' returned {len(hits)} hits.")
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

def get_latest_scraped_time() -> Optional[str]:
    try:
        raw_dir = os.path.join(BASE_DIR, "data/raw")
        if not os.path.exists(raw_dir):
            return None
        amc_file = os.path.join(raw_dir, "mutual-funds_amc_groww-mutual-funds.json")
        if os.path.exists(amc_file):
            with open(amc_file, 'r') as f:
                data = json.load(f)
                scraped_at = data.get("scraped_at")
                if scraped_at:
                    return scraped_at.replace("T", " ").replace("Z", "")
        # Fallback to any JSON
        for f in os.listdir(raw_dir):
            if f.endswith(".json"):
                fp = os.path.join(raw_dir, f)
                with open(fp, 'r') as file_obj:
                    data = json.load(file_obj)
                    scraped_at = data.get("scraped_at")
                    if scraped_at:
                        return scraped_at.replace("T", " ").replace("Z", "")
    except Exception as e:
        print(f"Error reading scraped time: {e}")
    return None

@app.get("/api/v1/groww/health")
def health_check():
    return {
        "status": "ok", 
        "indexed_chunks": collection.count(),
        "last_updated": get_latest_scraped_time()
    }

@app.post("/api/v1/groww/chat", response_model=QueryResponse)
def handle_chat(payload: QueryRequest):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Step 1: Check Rule-Based Heuristics (Quick-Pass Guardrails)
    heuristic_response = check_heuristics(query, payload.history or [])
    if heuristic_response:
        print(f"Query: '{query}' handled by heuristics.")
        return QueryResponse(
            answer=heuristic_response["answer"],
            source_link=heuristic_response["source_link"],
            last_updated=heuristic_response["last_updated"],
            is_refusal=heuristic_response["is_refusal"]
        )

    # Step 2: Call Combined Classifier and Query Refinement (Only 1 LLM call!)
    decision = classify_and_refine_query(query, payload.history or [])
    intent = decision.get("intent", "FACTUAL").upper()
    action = decision.get("action", "RETRIEVE").upper()
    print(f"Query: '{query}' -> Intent: {intent}, Action: {action}")

    # Step 3: Route advisory requests
    if intent == "ADVISORY":
        return QueryResponse(
            answer="I can only provide factual, objective details about mutual fund schemes. For investment advice, please consult a registered financial advisor. You can read more about mutual fund investments on AMFI or the SEBI Investor Education Portal.",
            source_link="https://www.mutualfundssahihai.com",
            last_updated=None,
            is_refusal=True
        )

    # Step 4: Route clarification actions
    if action == "CLARIFY":
        return QueryResponse(
            answer=decision.get("clarification_message", "Could you please specify which Groww mutual fund you are referring to?"),
            source_link=None,
            last_updated=None,
            is_refusal=False
        )

    # Step 5: Execute factual retrieval and generation
    search_query = decision.get("search_query") or query
    print(f"Search Query: '{search_query}'")
    hits = retrieve_context(search_query)
    response_data = generate_rag_answer(search_query, hits)
    
    return QueryResponse(
        answer=response_data["answer"],
        source_link=response_data.get("source_link"),
        last_updated=response_data.get("last_updated"),
        is_refusal=response_data.get("is_refusal", False)
    )

if __name__ == "__main__":
    import uvicorn
    # Read port from env, fallback to 8005
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)
