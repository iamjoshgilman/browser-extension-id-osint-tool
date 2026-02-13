#!/usr/bin/env python3
"""
Test script for browser extension scrapers
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from scrapers.chrome import ChromeStoreScraper
from scrapers.firefox import FirefoxAddonsScraper
from scrapers.edge import EdgeAddonsScraper
import json

# Test extension IDs
TEST_IDS = {
    'chrome': [
        'cjpalhdlnbpafiamejdnhcphjbkeiagm',  # uBlock Origin
        'gighmmpiobklfepjocnamgkkbiglidom',  # AdBlock
        'invalidextensionid123',              # Invalid ID
    ],
    'firefox': [
        'uBlock0@raymondhill.net',            # uBlock Origin
        '{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}',  # AdBlock Plus
        'invalid-addon',                      # Invalid ID
    ],
    'edge': [
        'odfafepnkmbhccpbejgmiehpchacaeak',  # uBlock Origin (Edge)
        'ndcileolkflehcjpmjnfbnaibdcgglog',  # Bitwarden
        'INVALIDEDGEEXTENSION',               # Invalid ID
    ]
}

def test_scraper(scraper_class, store_name, test_ids):
    """Test a specific scraper"""
    print(f"\n{'='*60}")
    print(f"Testing {store_name} Scraper")
    print(f"{'='*60}")
    
    scraper = scraper_class()
    
    for ext_id in test_ids:
        print(f"\nTesting ID: {ext_id}")
        print(f"Valid format: {scraper.validate_id(ext_id)}")
        
        try:
            result = scraper.scrape(ext_id)
            
            if result:
                print(f"Found: {result.found}")
                if result.found:
                    print(f"Name: {result.name}")
                    print(f"Publisher: {result.publisher}")
                    print(f"Version: {result.version}")
                    print(f"Users: {result.user_count}")
                    print(f"Rating: {result.rating}")
                    print(f"Description: {result.description[:100]}..." if result.description else "")
                else:
                    print("Extension not found in store")
            else:
                print("Scraping failed - no result returned")
                
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

def main():
    """Run all scraper tests"""
    print("Browser Extension OSINT Tool - Scraper Test")
    print("==========================================")
    
    # Test Chrome scraper
    test_scraper(ChromeStoreScraper, "Chrome Web Store", TEST_IDS['chrome'])
    
    # Test Firefox scraper
    test_scraper(FirefoxAddonsScraper, "Firefox Add-ons", TEST_IDS['firefox'])
    
    # Test Edge scraper
    test_scraper(EdgeAddonsScraper, "Edge Add-ons", TEST_IDS['edge'])
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

if __name__ == "__main__":
    main()
