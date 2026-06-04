import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from scraper.urls import GROWW_URLS
    from scraper.scraper import run_scraper
except ModuleNotFoundError:
    from urls import GROWW_URLS
    from scraper import run_scraper

if __name__ == "__main__":
    # Test with the first 2 URLs
    test_urls = GROWW_URLS[:2]
    print(f"Running scraper test on: {test_urls}")
    run_scraper(test_urls)
