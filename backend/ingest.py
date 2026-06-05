import os
import json
import re
import uuid
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb

# Load environment variables
import os
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")), override=True)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_google_ai_studio_api_key":
    print("Warning: GEMINI_API_KEY is not set correctly in your .env file.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data/raw")
CHROMA_DIR = os.path.join(BASE_DIR, "data/chroma")

def split_text(text, max_chars=800, overlap=150):
    """
    Split text into chunks of max_chars with overlap, keeping paragraphs/sentences intact.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If a single paragraph is too large, split it into sentences
        if len(paragraph) > max_chars:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                if len(sentence) > max_chars:
                    # If a sentence is still too large, force character split
                    for i in range(0, len(sentence), max_chars - overlap):
                        chunks.append(sentence[i:i + max_chars])
                else:
                    if current_length + len(sentence) > max_chars:
                        # Save current chunk
                        chunks.append(" ".join(current_chunk))
                        # Keep overlap words
                        overlap_text = " ".join(current_chunk)[-(overlap):] if current_chunk else ""
                        current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                        current_length = len(overlap_text) + len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence) + 1
        else:
            if current_length + len(paragraph) > max_chars:
                chunks.append("\n\n".join(current_chunk))
                # Keep overlap
                overlap_text = "\n\n".join(current_chunk)[-(overlap):] if current_chunk else ""
                current_chunk = [overlap_text, paragraph] if overlap_text else [paragraph]
                current_length = len(overlap_text) + len(paragraph)
            else:
                current_chunk.append(paragraph)
                current_length += len(paragraph) + 2
                
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return [c.strip() for c in chunks if c.strip()]


def ingest_data():
    print(f"Reading scraped files from {RAW_DATA_DIR}...")
    if not os.path.exists(RAW_DATA_DIR):
        print("Error: No raw data directory found. Run scraper first.")
        return
        
    files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".json")]
    if not files:
        print("No scraped JSON files found.")
        return
        
    documents = []
    metadatas = []
    ids = []
    
    for filename in files:
        filepath = os.path.join(RAW_DATA_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        scheme_name = data.get("scheme_name", "Unknown Scheme")
        url = data.get("url", "")
        content = data.get("content", "")
        tables = data.get("tables", [])
        scraped_at = data.get("scraped_at", "")
        
        # Skip empty files (e.g. failed scrapes or draft pages)
        if not content.strip() and not tables:
            print(f"Skipping empty data file: {filename}")
            continue
            
        # 1. Process unstructured content text
        text_chunks = split_text(content)
        for i, chunk in enumerate(text_chunks):
            # Prepended context header
            enriched_text = f"Scheme Name: {scheme_name}\nSource URL: {url}\n\n{chunk}"
            documents.append(enriched_text)
            metadatas.append({
                "scheme_name": scheme_name,
                "source_url": url,
                "last_updated_date": scraped_at[:10], # Keep YYYY-MM-DD
                "chunk_type": "text",
                "part_index": i
            })
            ids.append(f"doc_{uuid.uuid4().hex[:12]}")
            
        # 2. Process table chunks (treated as complete entities)
        for idx, table_md in enumerate(tables):
            enriched_table = f"Scheme Name: {scheme_name}\nSource URL: {url}\nTable Category: Mutual Fund Portfolio/Return Data\n\n{table_md}"
            documents.append(enriched_table)
            metadatas.append({
                "scheme_name": scheme_name,
                "source_url": url,
                "last_updated_date": scraped_at[:10],
                "chunk_type": "table",
                "part_index": idx
            })
            ids.append(f"table_{uuid.uuid4().hex[:12]}")
            
    print(f"Total chunks created: {len(documents)} ({len([m for m in metadatas if m['chunk_type'] == 'text'])} text chunks, {len([m for m in metadatas if m['chunk_type'] == 'table'])} table chunks)")
    
    # Delete the old database directory to prevent dimension mismatches (768 vs 3072)
    if os.path.exists(CHROMA_DIR):
        import shutil
        try:
            shutil.rmtree(CHROMA_DIR)
            print(f"Deleted old database directory: {CHROMA_DIR}")
        except Exception as e:
            print(f"Warning: Could not delete database directory: {e}")

    # Initialize ChromaDB client
    os.makedirs(CHROMA_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Recreate the collection with local embedding function
    collection_name = "groww_mutual_funds"
    from chromadb.utils import embedding_functions
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    
    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=default_ef
    )
    
    # Generate local embeddings one by one (avoids ONNX threading deadlocks on batch inputs)
    print("Generating local embeddings one by one...")
    embeddings = []
    import time
    start_time = time.time()
    for idx, doc in enumerate(documents):
        embeddings.append(default_ef([doc])[0])
        if idx > 0 and idx % 100 == 0:
            print(f"Processed {idx}/{len(documents)} embeddings (elapsed: {time.time() - start_time:.1f}s)...")
            
    print(f"Embedding generation completed in {time.time() - start_time:.1f}s. Preparing database insert...")
    
    # Insert chunks and pre-computed embeddings into ChromaDB
    print(f"Upserting {len(documents)} vectors into ChromaDB...")
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        end = i + batch_size
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end]
        )
        
    print("Ingestion pipeline successfully completed. Vector database indexed!")

if __name__ == "__main__":
    ingest_data()
