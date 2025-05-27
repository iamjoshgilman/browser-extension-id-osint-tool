"""
Chrome Web Store scraper with improved data extraction
"""
import re
import json
import logging
from typing import Optional
from bs4 import BeautifulSoup
from scrapers.base import ExtensionScraper
from models.extension import ExtensionData

logger = logging.getLogger(__name__)

class ChromeStoreScraper(ExtensionScraper):
    """Chrome Web Store scraper"""
    
    def __init__(self):
        super().__init__()
        self.store_name = "chrome"
        # Update user agent to a more recent one
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
    
    def validate_id(self, extension_id: str) -> bool:
        """Chrome extension IDs are 32 lowercase letters"""
        return bool(re.match(r'^[a-z]{32}$', extension_id))
    
    def normalize_id(self, extension_id: str) -> str:
        """Normalize extension ID to lowercase"""
        return extension_id.strip().lower()
    
    def get_extension_url(self, extension_id: str) -> str:
        """Get the Chrome Web Store URL for an extension"""
        return f"https://chromewebstore.google.com/detail/{extension_id}"
    
    def scrape(self, extension_id: str) -> Optional[ExtensionData]:
        """Scrape extension data from Chrome Web Store"""
        if not self.validate_id(extension_id):
            logger.warning(f"Invalid Chrome extension ID format: {extension_id}")
            return self.create_not_found_result(extension_id)
        
        normalized_id = self.normalize_id(extension_id)
        url = self.get_extension_url(normalized_id)
        
        try:
            logger.info(f"Scraping Chrome extension: {normalized_id}")
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                logger.info(f"Chrome extension not found: {normalized_id}")
                return self.create_not_found_result(normalized_id)
            
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialize with default values
            data = ExtensionData(
                extension_id=normalized_id,
                name="",
                store_source=self.store_name,
                store_url=url
            )
            
            # Try to extract from structured data first
            found_structured_data = False
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    json_data = json.loads(script.string)
                    if '@type' in json_data and json_data['@type'] == 'WebApplication':
                        data.name = json_data.get('name', '')
                        if 'author' in json_data:
                            data.publisher = json_data['author'].get('name', '')
                        if 'description' in json_data:
                            data.description = json_data['description'][:500]
                        if 'version' in json_data:
                            data.version = json_data['version']
                        if 'aggregateRating' in json_data:
                            rating_data = json_data['aggregateRating']
                            data.rating = str(rating_data.get('ratingValue', ''))
                            data.rating_count = str(rating_data.get('ratingCount', ''))
                        found_structured_data = True
                        logger.info(f"Extracted data from structured data: {data.name}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to parse structured data: {e}")
            
            # If no structured data or no name found, try HTML parsing
            if not data.name:
                # Extract name - try multiple selectors
                name_selectors = [
                    'h1[class*="webstore-test-wall-tile-name"]',
                    'h1.e-f-w',
                    'div[itemprop="name"]',
                    'h1'
                ]
                for selector in name_selectors:
                    elem = soup.select_one(selector)
                    if elem and elem.get_text(strip=True):
                        data.name = elem.get_text(strip=True)
                        break
            
            # Check if this is actually an extension page or a 404/error page
            # Chrome Web Store shows a page even for non-existent extensions but with generic content
            if not data.name or data.name in ["Unknown Extension", "Chrome Web Store", ""]:
                # Additional check: look for specific error indicators
                error_indicators = [
                    "Item not found",
                    "This item may have been removed",
                    "404",
                    "Not found"
                ]
                
                page_text = response.text.lower()
                for indicator in error_indicators:
                    if indicator.lower() in page_text:
                        logger.info(f"Chrome extension not found (error indicator): {normalized_id}")
                        return self.create_not_found_result(normalized_id)
                
                # If we still don't have a valid name, it's likely not found
                if not data.name or data.name == "Unknown Extension":
                    logger.info(f"Chrome extension not found (no valid data): {normalized_id}")
                    return self.create_not_found_result(normalized_id)
            
            # Extract user count from text
            users_patterns = [
                r'([\d,]+\+?\s*users?)',
                r'([\d,]+)\s*weekly active users',
                r'Used by ([\d,]+\+?) people'
            ]
            for pattern in users_patterns:
                users_match = re.search(pattern, response.text, re.IGNORECASE)
                if users_match:
                    data.user_count = users_match.group(1)
                    break
            
            # Extract publisher - look for "offered by" text
            offered_by_match = re.search(r'offered by[:\s]+([^<\n]+)', response.text, re.IGNORECASE)
            if offered_by_match:
                data.publisher = offered_by_match.group(1).strip()
            
            # Extract version from various possible locations
            version_patterns = [
                r'"version"\s*:\s*"([^"]+)"',
                r'Version:\s*([^\s<]+)',
                r'<span[^>]*class="[^"]*version[^"]*"[^>]*>([^<]+)</span>'
            ]
            for pattern in version_patterns:
                version_match = re.search(pattern, response.text)
                if version_match:
                    data.version = version_match.group(1).strip()
                    break
            
            # Extract rating
            rating_patterns = [
                r'"ratingValue"\s*:\s*"?([0-9.]+)"?',
                r'([0-9.]+)\s*out of\s*5',
                r'Average rating[:\s]*([0-9.]+)'
            ]
            for pattern in rating_patterns:
                rating_match = re.search(pattern, response.text)
                if rating_match:
                    data.rating = rating_match.group(1)
                    break
            
            # Extract description if not already found
            if not data.description:
                desc_selectors = [
                    'div[itemprop="description"]',
                    'div.C-b-p-j-D-K',
                    'section[class*="description"]',
                    'div[class*="overview"]'
                ]
                for selector in desc_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        desc_text = elem.get_text(strip=True)
                        if desc_text and len(desc_text) > 10:
                            data.description = desc_text[:500]
                            break
            
            # Extract last updated date
            updated_patterns = [
                r'"datePublished"\s*:\s*"([^"]+)"',
                r'Updated[:\s]*([^<\n]+)',
                r'Last updated[:\s]*([^<\n]+)'
            ]
            for pattern in updated_patterns:
                updated_match = re.search(pattern, response.text)
                if updated_match:
                    data.last_updated = updated_match.group(1).strip()
                    break
            
            # Final validation - ensure we have meaningful data
            if data.name and data.name not in ["Unknown Extension", "Chrome Web Store", ""]:
                data.found = True
                logger.info(f"Successfully scraped Chrome extension: {data.name} (users: {data.user_count}, version: {data.version})")
                return data
            else:
                logger.info(f"Chrome extension not found (insufficient data): {normalized_id}")
                return self.create_not_found_result(normalized_id)
            
        except Exception as e:
            return self.handle_request_error(normalized_id, e)
