import sys
import os

# Add parent directory to path so imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from scraper.scraper import run_scraper
except ModuleNotFoundError:
    from scraper import run_scraper

try:
    from backend.ingest import ingest_data
except ModuleNotFoundError:
    from ingest import ingest_data

if __name__ == "__main__":
    print("=== Starting Daily Mutual Fund ETL Sync ===")
    
    # 1. Scrape latest data from Groww URLs
    print("\n[ETL Step 1/2] Scraping target pages...")
    try:
        run_scraper()
    except Exception as e:
        print(f"Scraper encountered errors: {e}")
        # We still proceed to ingest what we successfully have
        
    # 2. Re-chunk and upsert into ChromaDB
    print("\n[ETL Step 2/2] Updating ChromaDB vector index...")
    try:
        ingest_data()
    except Exception as e:
        print(f"Ingestion failed: {e}")
        sys.exit(1)
        
    print("\n=== Daily Mutual Fund ETL Sync Completed ===")
