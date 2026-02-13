"""
Microsoft Edge Add-ons scraper using the product details API
"""
import re
import json
import logging
from typing import Optional
from scrapers.base import ExtensionScraper
from models.extension import ExtensionData

logger = logging.getLogger(__name__)

class EdgeAddonsScraper(ExtensionScraper):
    """Microsoft Edge Add-ons scraper"""
    
    def __init__(self):
        super().__init__()
        self.store_name = "edge"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
            'Accept': 'application/json, text/plain, */*',
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
    
    def scrape(self, extension_id: str) -> Optional[ExtensionData]:
        """Scrape extension data from Edge Add-ons using the product details API"""
        if not self.validate_id(extension_id):
            logger.warning(f"Invalid Edge extension ID format: {extension_id}")
            return self.create_not_found_result(extension_id)
        
        normalized_id = self.normalize_id(extension_id)
        logger.info(f"Scraping Edge addon: {normalized_id}")
        
        api_url = f"https://microsoftedge.microsoft.com/addons/getproductdetailsbycrxid/{normalized_id}"
        
        try:
            response = self.session.get(api_url, timeout=self.timeout)
            
            if response.status_code == 404:
                logger.info(f"Edge addon not found: {normalized_id}")
                return self.create_not_found_result(normalized_id)
            
            if response.status_code != 200:
                logger.warning(f"Edge API returned status {response.status_code} for {normalized_id}")
                return self.create_not_found_result(normalized_id)
            
            try:
                api_data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"Edge API returned non-JSON response for {normalized_id}")
                return self.create_not_found_result(normalized_id)
            
            name = api_data.get('name', '')
            if not name:
                logger.info(f"Edge addon has no name in API response: {normalized_id}")
                return self.create_not_found_result(normalized_id)
            
            # Format user count
            install_count = api_data.get('activeInstallCount', 0)
            if install_count:
                user_count = f"{install_count:,} users"
            else:
                user_count = ''
            
            # Extract version from top-level or manifest
            version = api_data.get('version', '')
            if not version:
                manifest_str = api_data.get('manifest', '')
                if manifest_str:
                    try:
                        manifest = json.loads(manifest_str)
                        version = manifest.get('version_name', manifest.get('version', ''))
                    except json.JSONDecodeError:
                        pass
            
            # Extract permissions from manifest
            permissions = []
            manifest_str = api_data.get('manifest', '')
            if manifest_str:
                try:
                    manifest = json.loads(manifest_str)
                    permissions = manifest.get('permissions', [])
                except json.JSONDecodeError:
                    pass
            
            # Build icon URL
            icon_url = api_data.get('logoUrl', '')
            if icon_url and icon_url.startswith('//'):
                icon_url = 'https:' + icon_url
            
            data = ExtensionData(
                extension_id=normalized_id,
                name=name,
                store_source=self.store_name,
                store_url=self.get_extension_url(normalized_id),
                publisher=api_data.get('developer', ''),
                description=api_data.get('shortDescription', api_data.get('description', ''))[:500],
                version=version,
                user_count=user_count,
                rating=str(api_data.get('averageRating', '')),
                rating_count=str(api_data.get('ratingCount', '')),
                category=api_data.get('category', ''),
                icon_url=icon_url,
                homepage_url=api_data.get('publisherWebsiteUri', ''),
                privacy_policy_url=api_data.get('privacyUrl', ''),
                permissions=permissions,
                found=True
            )
            
            # Extract last updated from timestamp
            last_updated = api_data.get('lastUpdateDate')
            if last_updated:
                try:
                    from datetime import datetime
                    dt = datetime.fromtimestamp(last_updated)
                    data.last_updated = dt.strftime('%Y-%m-%d')
                except (ValueError, OSError, OverflowError):
                    pass
            
            logger.info(f"Successfully scraped Edge addon: {data.name} (publisher: {data.publisher}, users: {data.user_count})")
            return data
            
        except Exception as e:
            return self.handle_request_error(normalized_id, e)
