import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from scraper.scraper import run_scraper
except ModuleNotFoundError:
    from scraper import run_scraper

FAILED_URLS = [
    "https://groww.in/mutual-funds/groww-banking-psu-debt-fund-direct-growth",
    "https://groww.in/mutual-funds/groww-gilt-fund-direct-growth",
    "https://groww.in/mutual-funds/groww-gold-etf-fof-direct-growth"
]

if __name__ == "__main__":
    print(f"Scraping failed URLs: {FAILED_URLS}")
    run_scraper(FAILED_URLS)
