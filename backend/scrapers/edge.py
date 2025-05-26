"""
Microsoft Edge Add-ons scraper with improved data extraction
"""
import re
import json
import logging
from typing import Optional
from bs4 import BeautifulSoup
from scrapers.base import ExtensionScraper
from models.extension import ExtensionData

logger = logging.getLogger(__name__)

class EdgeAddonsScraper(ExtensionScraper):
    """Microsoft Edge Add-ons scraper"""
    
    def __init__(self):
        super().__init__()
        self.store_name = "edge"
        # Use Edge-specific user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
    
    def validate_id(self, extension_id: str) -> bool:
        """Edge uses 32 character IDs similar to Chrome"""
        return bool(re.match(r'^[a-zA-Z0-9]{32}$', extension_id))
    
    def normalize_id(self, extension_id: str) -> str:
        """Normalize extension ID"""
        return extension_id.strip().lower()
    
    def get_extension_url(self, extension_id: str) -> str:
        """Get the Edge Add-ons URL for an extension"""
        return f"https://microsoftedge.microsoft.com/addons/detail/{extension_id}"
    
    def scrape(self, extension_id: str) -> Optional[ExtensionData]:
        """Scrape extension data from Edge Add-ons"""
        if not self.validate_id(extension_id):
            logger.warning(f"Invalid Edge extension ID format: {extension_id}")
            return self.create_not_found_result(extension_id)
        
        normalized_id = self.normalize_id(extension_id)
        url = self.get_extension_url(normalized_id)
        
        try:
            logger.info(f"Scraping Edge addon: {normalized_id}")
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                logger.info(f"Edge addon not found: {normalized_id}")
                return self.create_not_found_result(normalized_id)
            
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = ExtensionData(
                extension_id=normalized_id,
                name="Unknown Extension",
                store_source=self.store_name,
                store_url=url
            )
            
            # Edge often loads data dynamically, but we can try to extract from initial HTML
            # or look for data in script tags
            
            # Look for JSON data in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for __PRELOADED_STATE__ or similar
                    preloaded_match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.+?});', script.string, re.DOTALL)
                    if preloaded_match:
                        try:
                            json_data = json.loads(preloaded_match.group(1))
                            # Navigate through the JSON structure to find extension data
                            # This structure may vary, so we'll try multiple paths
                            logger.debug("Found preloaded state data")
                            
                            # Try to extract data from various possible paths
                            if 'data' in json_data:
                                self._extract_from_json(json_data['data'], data)
                            if 'productDetails' in json_data:
                                self._extract_from_json(json_data['productDetails'], data)
                        except Exception as e:
                            logger.debug(f"Failed to parse preloaded state: {e}")
                    
                    # Look for other data patterns
                    if '"name"' in script.string and '"version"' in script.string:
                        # Try to extract individual fields
                        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', script.string)
                        if name_match:
                            data.name = name_match.group(1)
                        
                        version_match = re.search(r'"version"\s*:\s*"([^"]+)"', script.string)
                        if version_match:
                            data.version = version_match.group(1)
                        
                        publisher_match = re.search(r'"publisher"\s*:\s*"([^"]+)"', script.string)
                        if publisher_match:
                            data.publisher = publisher_match.group(1)
            
            # Fallback to HTML parsing
            if data.name == "Unknown Extension":
                # Extract name - Edge uses various selectors
                name_selectors = [
                    'h1[class*="ProductTitle"]',
                    'h1[class*="title"]',
                    'div[class*="ExtensionName"]',
                    '[data-testid="extension-title"]',
                    'h1'
                ]
                for selector in name_selectors:
                    elem = soup.select_one(selector)
                    if elem and elem.get_text(strip=True):
                        data.name = elem.get_text(strip=True)
                        logger.debug(f"Found name with selector {selector}: {data.name}")
                        break
            
            # Extract publisher
            if not data.publisher:
                publisher_selectors = [
                    '[class*="PublisherName"]',
                    '[class*="publisher"]',
                    '[data-testid="publisher-name"]',
                    'a[href*="/publishers/"]'
                ]
                for selector in publisher_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        data.publisher = elem.get_text(strip=True)
                        break
            
            # Extract user count
            users_patterns = [
                r'([\d,]+)\s*users?',
                r'([\d,]+)\s*weekly active users',
                r'Users:\s*([\d,]+)',
                r'Active users:\s*([\d,]+)'
            ]
            for pattern in users_patterns:
                users_match = re.search(pattern, response.text, re.IGNORECASE)
                if users_match:
                    data.user_count = f"{users_match.group(1)} users"
                    break
            
            # Extract rating
            rating_selectors = [
                '[class*="RatingValue"]',
                '[class*="rating"]',
                '[aria-label*="rating"]'
            ]
            for selector in rating_selectors:
                elem = soup.select_one(selector)
                if elem:
                    rating_text = elem.get_text(strip=True)
                    rating_match = re.search(r'([0-9.]+)', rating_text)
                    if rating_match:
                        data.rating = rating_match.group(1)
                        break
            
            # Extract version
            if not data.version:
                version_patterns = [
                    r'Version[:\s]*([^\s<]+)',
                    r'"version"\s*:\s*"([^"]+)"',
                    r'v\.?\s*([0-9.]+)'
                ]
                for pattern in version_patterns:
                    version_match = re.search(pattern, response.text, re.IGNORECASE)
                    if version_match:
                        data.version = version_match.group(1).strip()
                        break
            
            # Extract description
            desc_selectors = [
                '[class*="Description"]',
                '[class*="overview"]',
                '[data-testid="description"]',
                'div[itemprop="description"]'
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    desc_text = elem.get_text(strip=True)
                    if desc_text and len(desc_text) > 10:
                        data.description = desc_text[:500]
                        break
            
            # Extract category
            category_selectors = [
                '[class*="Category"]',
                'a[href*="/category/"]'
            ]
            for selector in category_selectors:
                elem = soup.select_one(selector)
                if elem:
                    data.category = elem.get_text(strip=True)
                    break
            
            logger.info(f"Successfully scraped Edge addon: {data.name} (version: {data.version})")
            return data
            
        except Exception as e:
            return self.handle_request_error(normalized_id, e)
    
    def _extract_from_json(self, json_data, extension_data):
        """Helper to extract data from JSON structure"""
        if isinstance(json_data, dict):
            if 'name' in json_data:
                extension_data.name = json_data['name']
            if 'version' in json_data:
                extension_data.version = json_data['version']
            if 'publisher' in json_data:
                if isinstance(json_data['publisher'], dict):
                    extension_data.publisher = json_data['publisher'].get('name', '')
                else:
                    extension_data.publisher = str(json_data['publisher'])
            if 'description' in json_data:
                extension_data.description = json_data['description'][:500]
            if 'userCount' in json_data:
                extension_data.user_count = f"{json_data['userCount']} users"
            if 'rating' in json_data:
                if isinstance(json_data['rating'], dict):
                    extension_data.rating = str(json_data['rating'].get('average', ''))
                else:
                    extension_data.rating = str(json_data['rating'])
