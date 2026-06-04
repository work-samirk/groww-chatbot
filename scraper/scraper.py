import os
import json
import time
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
try:
    from scraper.urls import GROWW_URLS
except ModuleNotFoundError:
    from urls import GROWW_URLS

RAW_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/raw"))

def get_url_safe_filename(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return "index"
    return re.sub(r'[^a-zA-Z0-9_-]', '_', path)

def table_to_markdown(table_soup):
    rows = table_soup.find_all('tr')
    if not rows:
        return ""
    md_lines = []
    for i, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        cell_texts = [cell.get_text(separator=" ", strip=True).replace('\n', ' ') for cell in cells]
        if not cell_texts:
            continue
        md_lines.append("| " + " | ".join(cell_texts) + " |")
        if i == 0 and len(cell_texts) > 0:
            md_lines.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")
    return "\n".join(md_lines)

def parse_groww_page(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Scheme name
    h1 = soup.find('h1')
    scheme_name = h1.get_text(strip=True) if h1 else "Unknown Scheme"
    
    # Clean scheme name if it contains subheadings
    scheme_name = re.sub(r'\s+', ' ', scheme_name)
    
    # 2. Extract tables
    tables = []
    for table_tag in soup.find_all('table'):
        table_md = table_to_markdown(table_tag)
        if table_md:
            tables.append(table_md)
            
    # 3. Extract text paragraphs
    paragraphs = []
    # Focus on main sections, typically paragraphs inside body text
    # Avoid header/footer navigation links by filtering out common class names
    for p in soup.find_all(['p', 'div', 'span']):
        # If it's a div/span, only keep if it has a small length or specific content, or is a direct info piece
        if p.name == 'p':
            text = p.get_text(strip=True)
            if len(text) > 20 and not text.startswith("Disclaimer"):
                paragraphs.append(text)
        elif p.name in ['div', 'span']:
            # Only extract high-value key-value pairs like "Expense Ratio", "Exit Load", etc.
            text = p.get_text(strip=True)
            if any(keyword in text for keyword in ["Expense ratio", "Exit load", "Min. investment", "Fund Manager", "Benchmark", "Riskometer"]):
                if len(text) < 300: # avoid giant containers
                    paragraphs.append(text)
                    
    # Remove duplicates preserving order
    seen = set()
    unique_paragraphs = []
    for p in paragraphs:
        cleaned_p = re.sub(r'\s+', ' ', p)
        if cleaned_p not in seen and len(cleaned_p) > 5:
            seen.add(cleaned_p)
            unique_paragraphs.append(cleaned_p)
            
    full_content = "\n\n".join(unique_paragraphs)
    
    return {
        "scheme_name": scheme_name,
        "url": url,
        "content": full_content,
        "tables": tables,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

def run_scraper(urls=GROWW_URLS):
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    print(f"Starting scraper for {len(urls)} URLs...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create page with custom user agent and viewport size
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Scraping {url}...")
            filename = get_url_safe_filename(url) + ".json"
            filepath = os.path.join(RAW_DATA_DIR, filename)
            
            try:
                # Go to URL and wait for DOM content loaded and network idle (up to 30s)
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait an extra 2 seconds for client-side JS hydration / dynamic fields
                time.sleep(2)
                
                html_content = page.content()
                data = parse_groww_page(html_content, url)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
                print(f"Successfully scraped & saved: {filename}")
                
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                
            # Rate limiting / polite delay
            time.sleep(2)
            
        browser.close()
    print("Scraper completed.")

if __name__ == "__main__":
    run_scraper()
