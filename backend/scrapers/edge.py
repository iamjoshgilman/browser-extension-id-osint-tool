"""
Microsoft Edge Add-ons scraper with API exploration
This version tries API endpoints first, then falls back to HTML scraping
"""
import re
import json
import logging
from typing import Optional
from scrapers.base import ExtensionScraper
from models.extension import ExtensionData
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class EdgeAddonsScraper(ExtensionScraper):
    """Microsoft Edge Add-ons scraper with multiple strategies"""
    
    def __init__(self):
        super().__init__()
        self.store_name = "edge"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def validate_id(self, extension_id: str) -> bool:
        """Edge uses alphanumeric IDs of various lengths"""
        return bool(re.match(r'^[a-zA-Z0-9]{20,}$', extension_id))
    
    def normalize_id(self, extension_id: str) -> str:
        """Keep original case for Edge IDs"""
        return extension_id.strip()
    
    def get_extension_url(self, extension_id: str) -> str:
        """Get the Edge Add-ons URL for an extension"""
        return f"https://microsoftedge.microsoft.com/addons/detail/{extension_id}"
    
    def _try_api_endpoints(self, extension_id: str) -> Optional[ExtensionData]:
        """Try various potential API endpoints"""
        # Potential API endpoints to try
        api_endpoints = [
            f"https://microsoftedge.microsoft.com/addons/getproductdetailsbycrxid/{extension_id}",
            f"https://microsoftedge.microsoft.com/addons/api/details/{extension_id}",
            f"https://storeedgefd.dsx.mp.microsoft.com/v9.0/products/lookup?market=US&locale=en-US&productIds={extension_id}",
        ]
        
        for endpoint in api_endpoints:
            try:
                logger.debug(f"Trying API endpoint: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.debug(f"Got API response: {json.dumps(data, indent=2)[:500]}...")
                        
                        # Try to parse the API response
                        # This is speculative as we don't know the exact API format
                        if isinstance(data, dict):
                            ext_data = ExtensionData(
                                extension_id=extension_id,
                                name=data.get('name', data.get('title', 'Unknown')),
                                store_source=self.store_name,
                                publisher=data.get('publisher', data.get('author', '')),
                                description=data.get('description', '')[:500],
                                version=data.get('version', ''),
                                user_count=str(data.get('userCount', data.get('installCount', ''))),
                                rating=str(data.get('rating', data.get('averageRating', ''))),
                                store_url=self.get_extension_url(extension_id),
                                found=True
                            )
                            
                            if ext_data.name != 'Unknown':
                                logger.info(f"Successfully got data from API for {extension_id}")
                                return ext_data
                    except json.JSONDecodeError:
                        logger.debug(f"Response was not JSON from {endpoint}")
            except Exception as e:
                logger.debug(f"API endpoint {endpoint} failed: {e}")
        
        return None
    
    def _scrape_html(self, url: str, extension_id: str) -> Optional[ExtensionData]:
        """Scrape from HTML page"""
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 404:
                return self.create_not_found_result(extension_id)
            
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Create base extension data
            data = ExtensionData(
                extension_id=extension_id,
                name="Unknown Extension",
                store_source=self.store_name,
                store_url=response.url,  # Use final URL after redirects
                found=False
            )
            
            # Strategy 1: Check meta tags
            meta_title = soup.find('meta', property='og:title')
            if meta_title and meta_title.get('content'):
                title = meta_title['content'].strip()
                if title and "Microsoft Edge" not in title:
                    data.name = title
                    data.found = True
            
            # Strategy 2: Check title tag
            if not data.found:
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    if " - Microsoft Edge" in title_text:
                        name = title_text.split(" - Microsoft Edge")[0].strip()
                        if name and name != "Microsoft Edge Addons":
                            data.name = name
                            data.found = True
            
            # Strategy 3: Look for specific Edge elements
            if not data.found:
                # Try common class names Edge might use
                for selector in ['h1', '[class*="title"]', '[class*="name"]', '[role="heading"]']:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 2 and "Microsoft Edge" not in text:
                            data.name = text
                            data.found = True
                            break
            
            if not data.found:
                return self.create_not_found_result(extension_id)
            
            # Extract additional metadata
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                data.description = meta_desc.get('content', '')[:500]
            
            # Look for any inline JSON data
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('extension' in script.string.lower() or 'addon' in script.string.lower()):
                    # Try to extract JSON data
                    json_patterns = [
                        r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                        r'window\.__data\s*=\s*({.+?});',
                        r'{\s*"extension[^}]+}',
                    ]
                    
                    for pattern in json_patterns:
                        match = re.search(pattern, script.string, re.DOTALL)
                        if match:
                            try:
                                json_data = json.loads(match.group(1))
                                # Extract any useful data from the JSON
                                logger.debug("Found inline JSON data")
                            except:
                                pass
            
            # Use regex to find additional info
            text_content = response.text
            
            # User count
            user_match = re.search(r'([\d,]+)\s*(?:users?|installs?|downloads?)', text_content, re.I)
            if user_match:
                data.user_count = user_match.group(0)
            
            # Version
            version_match = re.search(r'version[:\s]*([0-9.]+)', text_content, re.I)
            if version_match:
                data.version = version_match.group(1)
            
            # Rating
            rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of\s*5|stars?)', text_content, re.I)
            if rating_match:
                data.rating = rating_match.group(1)
            
            return data
            
        except Exception as e:
            logger.error(f"HTML scraping error for {extension_id}: {e}")
            return self.handle_request_error(extension_id, e)
    
    def scrape(self, extension_id: str) -> Optional[ExtensionData]:
        """Scrape extension data using multiple strategies"""
        if not self.validate_id(extension_id):
            logger.warning(f"Invalid Edge extension ID format: {extension_id}")
            return self.create_not_found_result(extension_id)
        
        normalized_id = self.normalize_id(extension_id)
        
        # Strategy 1: Try API endpoints first (fastest if they work)
        logger.info(f"Attempting to scrape Edge addon: {normalized_id}")
        api_result = self._try_api_endpoints(normalized_id)
        if api_result:
            return api_result
        
        # Strategy 2: Scrape HTML page
        url = self.get_extension_url(normalized_id)
        return self._scrape_html(url, normalized_id)
