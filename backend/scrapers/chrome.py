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
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
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
            
            # Try to extract from structured data (ld+json) if available
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
                        logger.info(f"Extracted data from structured data: {data.name}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to parse structured data: {e}")
            
            # Extract name from h1 if not found via structured data
            if not data.name:
                h1 = soup.find('h1')
                if h1:
                    data.name = h1.get_text(strip=True)
            
            # Check if this is actually an extension page
            if not data.name or data.name in ["Chrome Web Store", ""]:
                error_indicators = ["Item not found", "This item may have been removed", "404", "Not found"]
                page_text = response.text.lower()
                for indicator in error_indicators:
                    if indicator.lower() in page_text:
                        return self.create_not_found_result(normalized_id)
                if not data.name:
                    return self.create_not_found_result(normalized_id)
            
            # Extract description from meta tags if not from structured data
            if not data.description:
                og_desc = soup.find('meta', property='og:description')
                if og_desc and og_desc.get('content'):
                    desc = og_desc['content']
                    # Strip store suffix
                    if desc.endswith(' - Chrome Web Store'):
                        desc = desc[:-len(' - Chrome Web Store')]
                    data.description = desc[:500]
                if not data.description:
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc and meta_desc.get('content'):
                        data.description = meta_desc['content'][:500]
            
            # Extract icon from og:image
            if not data.icon_url:
                og_img = soup.find('meta', property='og:image')
                if og_img and og_img.get('content'):
                    data.icon_url = og_img['content']
            
            # Extract publisher from "Offered by" HTML structure
            # Structure: <div class="QDHp8e">Offered by</div><div>Publisher Name</div>
            if not data.publisher:
                offered_divs = soup.find_all('div', string=re.compile(r'Offered by', re.IGNORECASE))
                for offered_div in offered_divs:
                    next_div = offered_div.find_next_sibling('div')
                    if next_div:
                        data.publisher = next_div.get_text(strip=True)
                        break
                # Fallback: regex on raw text
                if not data.publisher:
                    offered_match = re.search(r'Offered by</div><div[^>]*>([^<]+)</div>', response.text, re.IGNORECASE)
                    if offered_match:
                        data.publisher = offered_match.group(1).strip()
            
            # Extract user count
            if not data.user_count:
                users_patterns = [
                    r'([\d,]+\+?\s*users?)',
                    r'([\d,]+)\s*weekly active users',
                ]
                for pattern in users_patterns:
                    users_match = re.search(pattern, response.text, re.IGNORECASE)
                    if users_match:
                        data.user_count = users_match.group(1)
                        break
            
            # Extract version
            if not data.version:
                version_match = re.search(r'"version"\s*:\s*"([0-9][0-9.]+)"', response.text)
                if version_match:
                    data.version = version_match.group(1).strip()
            
            # Extract rating
            if not data.rating:
                rating_patterns = [
                    r'"ratingValue"\s*:\s*"?([0-9.]+)"?',
                    r'([0-9.]+)\s*out of\s*5',
                ]
                for pattern in rating_patterns:
                    rating_match = re.search(pattern, response.text)
                    if rating_match:
                        data.rating = rating_match.group(1)
                        break
            
            # Extract last updated date
            if not data.last_updated:
                updated_patterns = [
                    r'"datePublished"\s*:\s*"([^"]+)"',
                    r'Updated[:\s]*([^<\n]+)',
                ]
                for pattern in updated_patterns:
                    updated_match = re.search(pattern, response.text)
                    if updated_match:
                        data.last_updated = updated_match.group(1).strip()
                        break
            
            # Final validation
            if data.name and data.name not in ["Chrome Web Store", ""]:
                data.found = True
                logger.info(f"Successfully scraped Chrome extension: {data.name} (publisher: {data.publisher}, users: {data.user_count}, version: {data.version})")
                return data
            else:
                return self.create_not_found_result(normalized_id)
            
        except Exception as e:
            return self.handle_request_error(normalized_id, e)
