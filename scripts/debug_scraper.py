#!/usr/bin/env python3
"""
Debug scraper to check what data we're getting from extension stores
"""
import sys
import os
import requests
from bs4 import BeautifulSoup
import json
import re

# Test URLs
urls = {
    'chrome': 'https://chromewebstore.google.com/detail/cjpalhdlnbpafiamejdnhcphjbkeiagm',
    'edge': 'https://microsoftedge.microsoft.com/addons/detail/odfafepnkmbhccpbejgmiehpchacaeak'
}

def debug_chrome_scraper(url):
    """Debug Chrome Web Store scraping"""
    print("\n" + "="*60)
    print("CHROME WEB STORE DEBUG")
    print("="*60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Try to find structured data
    scripts = soup.find_all('script', type='application/ld+json')
    for i, script in enumerate(scripts):
        print(f"\nStructured Data {i+1}:")
        try:
            data = json.loads(script.string)
            print(json.dumps(data, indent=2)[:500] + "...")
        except:
            print("Failed to parse JSON")
    
    # Try various selectors
    print("\n--- Testing Selectors ---")
    
    # Name selectors
    name_selectors = [
        'h1[itemprop="name"]',
        'h1.Pa2dE',
        'h1',
        '.C-b-p-D-md',
        'div[role="heading"][aria-level="1"]'
    ]
    
    for selector in name_selectors:
        elem = soup.select_one(selector)
        if elem:
            print(f"Name ({selector}): {elem.get_text(strip=True)[:100]}")
    
    # Try to extract from page content
    print("\n--- Text Pattern Search ---")
    
    # User count
    users_match = re.search(r'([\d,]+\+?\s*users?)', response.text, re.IGNORECASE)
    if users_match:
        print(f"Users (regex): {users_match.group(1)}")
    
    # Version
    version_match = re.search(r'"version"\s*:\s*"([^"]+)"', response.text)
    if version_match:
        print(f"Version (regex): {version_match.group(1)}")
    
    # Save HTML for inspection
    with open('chrome_debug.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("\nSaved full HTML to chrome_debug.html")

def debug_edge_scraper(url):
    """Debug Edge Add-ons scraping"""
    print("\n" + "="*60)
    print("EDGE ADD-ONS DEBUG")
    print("="*60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Try various selectors
    print("\n--- Testing Selectors ---")
    
    # Name selectors
    name_selectors = [
        'h1.OverviewDetailsTitle',
        'h1[class*="title"]',
        'h1',
        '.ProductTitle',
        'div[class*="Title"]'
    ]
    
    for selector in name_selectors:
        elem = soup.select_one(selector)
        if elem:
            print(f"Name ({selector}): {elem.get_text(strip=True)[:100]}")
    
    # Check for JSON data
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'window.__data' in script.string:
            print("\nFound window.__data script")
            # Try to extract JSON
            match = re.search(r'window\.__data\s*=\s*({.+?});', script.string, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    print("Parsed JSON data structure found")
                    # Look for extension data
                    if 'productDetails' in str(data):
                        print("Found productDetails in data")
                except:
                    print("Failed to parse JSON data")
    
    # Save HTML for inspection
    with open('edge_debug.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("\nSaved full HTML to edge_debug.html")

def main():
    """Run debugging for all scrapers"""
    print("Browser Extension Scraper Debug Tool")
    print("====================================")
    
    # Test Chrome
    if 'chrome' in urls:
        try:
            debug_chrome_scraper(urls['chrome'])
        except Exception as e:
            print(f"Chrome scraper error: {e}")
    
    # Test Edge
    if 'edge' in urls:
        try:
            debug_edge_scraper(urls['edge'])
        except Exception as e:
            print(f"Edge scraper error: {e}")
    
    print("\n" + "="*60)
    print("Debug complete! Check the HTML files for full content.")
    print("="*60)

if __name__ == "__main__":
    main()
