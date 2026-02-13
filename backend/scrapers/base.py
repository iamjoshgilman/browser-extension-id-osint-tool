"""
Base scraper class
"""
import requests
import logging
from abc import ABC, abstractmethod
from typing import Optional
from models.extension import ExtensionData
from config import get_config

logger = logging.getLogger(__name__)


class ExtensionScraper(ABC):
    """Abstract base class for extension scrapers"""

    def __init__(self):
        config = get_config()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": config.SCRAPER_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        self.timeout = config.SCRAPER_TIMEOUT
        self.store_name = "unknown"

    @abstractmethod
    def scrape(self, extension_id: str) -> Optional[ExtensionData]:
        """Scrape extension data from store"""
        pass

    @abstractmethod
    def validate_id(self, extension_id: str) -> bool:
        """Validate extension ID format for this store"""
        pass

    @abstractmethod
    def normalize_id(self, extension_id: str) -> str:
        """Normalize extension ID format"""
        pass

    def create_not_found_result(self, extension_id: str) -> ExtensionData:
        """Create a not found result"""
        return ExtensionData(
            extension_id=extension_id,
            name="Not Found",
            store_source=self.store_name,
            store_url=self.get_extension_url(extension_id),
            found=False,
        )

    @abstractmethod
    def get_extension_url(self, extension_id: str) -> str:
        """Get the store URL for an extension"""
        pass

    def search_by_name(self, name: str, limit: int = 5) -> list:
        """Search extensions by name. Returns list of ExtensionData.
        Default implementation returns empty list. Subclasses with
        search API support should override this."""
        return []

    def handle_request_error(self, extension_id: str, error: Exception) -> Optional[ExtensionData]:
        """Handle request errors consistently"""
        logger.error(f"Error scraping {self.store_name} extension {extension_id}: {error}")

        # Return a basic result indicating an error occurred
        return ExtensionData(
            extension_id=extension_id,
            name=f"Error: {type(error).__name__}",
            store_source=self.store_name,
            store_url=self.get_extension_url(extension_id),
            found=False,
            description=str(error),
        )
