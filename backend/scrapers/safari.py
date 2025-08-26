"""
Safari App Store scraper using iTunes Search API
"""
import logging
from typing import Optional

from scrapers.base import ExtensionScraper
from models.extension import ExtensionData

logger = logging.getLogger(__name__)


class SafariExtensionsScraper(ExtensionScraper):
    """Safari App Store scraper"""

    def __init__(self):
        super().__init__()
        self.store_name = "safari"
        # Use a Safari-like user agent
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15"
            )
        })

    def validate_id(self, extension_id: str) -> bool:
        """Safari extensions use numeric IDs from the App Store"""
        return extension_id.isdigit()

    def normalize_id(self, extension_id: str) -> str:
        """IDs are numeric; simply strip whitespace"""
        return extension_id.strip()

    def get_extension_url(self, extension_id: str) -> str:
        """Return the public App Store URL"""
        return f"https://apps.apple.com/us/app/id{extension_id}"

    def scrape(self, extension_id: str) -> Optional[ExtensionData]:
        """Scrape extension data from the App Store"""
        if not self.validate_id(extension_id):
            logger.warning(f"Invalid Safari extension ID format: {extension_id}")
            return self.create_not_found_result(extension_id)

        normalized_id = self.normalize_id(extension_id)
        api_url = f"https://itunes.apple.com/lookup?id={normalized_id}&country=us"

        try:
            logger.info(f"Scraping Safari extension: {normalized_id}")
            response = self.session.get(api_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("resultCount", 0) == 0:
                return self.create_not_found_result(normalized_id)

            result = data["results"][0]
            ext_data = ExtensionData(
                extension_id=normalized_id,
                name=result.get("trackName", ""),
                publisher=result.get("sellerName", ""),
                description=result.get("description", "")[:500],
                version=result.get("version", ""),
                rating=str(result.get("averageUserRating", "")),
                rating_count=str(result.get("userRatingCount", "")),
                last_updated=result.get("currentVersionReleaseDate", ""),
                store_source=self.store_name,
                store_url=result.get("trackViewUrl", self.get_extension_url(normalized_id)),
                icon_url=result.get("artworkUrl100", ""),
                found=True,
            )
            return ext_data

        except Exception as e:
            return self.handle_request_error(normalized_id, e)
