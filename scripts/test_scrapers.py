#!/usr/bin/env python3
"""
Test script for browser extension scrapers
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from scrapers.chrome import ChromeStoreScraper
from scrapers.firefox import FirefoxAddonsScraper
from scrapers.edge import EdgeAddonsScraper
from pprint import pprint
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_scraper(scraper_class, extension_id, name):
    """Test a scraper with a known extension ID"""
    print(f"\n{'='*60}")
    print(f"Testing {name} with ID: {extension_id}")
    print('='*60)
    
    scraper = scraper_class()
    result = scraper.scrape(extension_id)
    
    if result:
        print(f"✓ Success! Found: {result.name}")
        print(f"  Publisher: {result.publisher}")
        print(f"  Version: {result.version}")
        print(f"  Users: {result.user_count}")
        print(f"  Rating: {result.rating}")
        print(f"  Description: {result.description[:100]}...")
        print(f"  URL: {result.store_url}")
    else:
        print("✗ Failed to scrape extension")

def main():
    """Run tests for all scrapers"""
    print("Browser Extension Scraper Test Suite")
    print("====================================")
    
    # Test Chrome Web Store
    test_scraper(
        ChromeStoreScraper,
        "cjpalhdlnbpafiamejdnhcphjbkeiagm",  # uBlock Origin
        "Chrome Web Store"
    )
    
    # Test Firefox Add-ons
    test_scraper(
        FirefoxAddonsScraper,
        "uBlock0@raymondhill.net",  # uBlock Origin
        "Firefox Add-ons"
    )
    
    # Test Edge Add-ons
    test_scraper(
        EdgeAddonsScraper,
        "odfafepnkmbhccpbejgmiehpchacaeak",  # uBlock Origin
        "Edge Add-ons"
    )
    
    # Test with non-existent extension
    print("\n" + "="*60)
    print("Testing with non-existent extension")
    print("="*60)
    
    scraper = ChromeStoreScraper()
    result = scraper.scrape("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    if result and not result.found:
        print("✓ Correctly identified as not found")
    else:
        print("✗ Should have returned not found")

if __name__ == "__main__":
    main()
