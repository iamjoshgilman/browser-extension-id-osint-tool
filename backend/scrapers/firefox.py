"""
Firefox Add-ons scraper
"""
import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
from scrapers.base import ExtensionScraper
from models.extension import ExtensionData

logger = logging.getLogger(__name__)


class FirefoxAddonsScraper(ExtensionScraper):
    """Firefox Add-ons scraper"""

    def __init__(self):
        super().__init__()
        self.store_name = "firefox"

    def validate_id(self, extension_id: str) -> bool:
        """Firefox can use various formats:
        - {UUID} format: {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}
        - Email-like: something@somewhere
        - Simple string ID
        """
        return len(extension_id) > 1

    def normalize_id(self, extension_id: str) -> str:
        """Normalize extension ID"""
        return extension_id.strip()

    def get_extension_url(self, extension_id: str) -> str:
        """Get the Firefox Add-ons URL for an extension"""
        return f"https://addons.mozilla.org/en-US/firefox/addon/{extension_id}/"

    def _extract_localized_string(self, value):
        """Extract a string from a potentially localized API field.
        The Firefox API may return either a plain string or a dict of locale keys.
        """
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            # Try common fields for nested URL objects
            if "url" in value:
                return self._extract_localized_string(value["url"])
            # Try en-US first, then any non-empty value
            if "en-US" in value and value["en-US"]:
                return value["en-US"]
            for v in value.values():
                if v and isinstance(v, str):
                    return v
        return ""

    def scrape(self, extension_id: str) -> Optional[ExtensionData]:
        """Scrape extension data from Firefox Add-ons"""
        if not self.validate_id(extension_id):
            logger.warning(f"Invalid Firefox addon ID format: {extension_id}")
            return self.create_not_found_result(extension_id)

        normalized_id = self.normalize_id(extension_id)

        api_url = f"https://addons.mozilla.org/api/v5/addons/addon/{normalized_id}/"

        try:
            logger.info(f"Scraping Firefox addon via API: {normalized_id}")
            response = self.session.get(api_url, timeout=self.timeout)

            if response.status_code == 404:
                logger.info(f"Firefox addon not found: {normalized_id}")
                return self.create_not_found_result(normalized_id)

            if response.status_code == 200:
                addon_data = response.json()

                # Extract homepage URL properly (may be localized dict)
                homepage_raw = addon_data.get("homepage", "")
                homepage_url = self._extract_localized_string(homepage_raw)

                data = ExtensionData(
                    extension_id=normalized_id,
                    name=self._extract_localized_string(addon_data.get("name", "Unknown")),
                    publisher=addon_data.get("authors", [{}])[0].get("name", ""),
                    description=self._extract_localized_string(addon_data.get("summary", ""))[:500],
                    version=addon_data.get("current_version", {}).get("version", ""),
                    user_count=f"{addon_data.get('average_daily_users', 0):,} users",
                    rating=str(addon_data.get("ratings", {}).get("average", "")),
                    rating_count=str(addon_data.get("ratings", {}).get("count", "")),
                    store_source=self.store_name,
                    store_url=addon_data.get("url", self.get_extension_url(normalized_id)),
                    homepage_url=homepage_url,
                    found=True,
                )

                # Extract icon URL
                icons = addon_data.get("icons", {})
                if icons:
                    # Prefer largest icon
                    for size in ["128", "64", "32"]:
                        if size in icons:
                            data.icon_url = icons[size]
                            break
                    if not data.icon_url and icons:
                        data.icon_url = list(icons.values())[0]

                # Extract category
                if addon_data.get("categories"):
                    categories = addon_data.get("categories", {})
                    if "firefox" in categories and categories["firefox"]:
                        data.category = categories["firefox"][0]

                # Extract permissions from current_version.file.permissions
                current_version = addon_data.get("current_version", {})
                file_data = current_version.get("file", {})
                if isinstance(file_data, dict) and file_data.get("permissions"):
                    data.permissions = file_data["permissions"]
                elif current_version.get("permissions"):
                    data.permissions = current_version["permissions"]

                # Extract last updated
                if current_version.get("created"):
                    data.last_updated = current_version["created"]

                # Extract privacy policy
                privacy_url = addon_data.get("contributions_url", "")
                if not privacy_url:
                    privacy_url = addon_data.get("privacy_policy_url", "")
                if privacy_url:
                    data.privacy_policy_url = self._extract_localized_string(privacy_url)

                logger.info(f"Successfully scraped Firefox addon via API: {data.name}")
                return data

            # Fallback to web scraping if API fails
            return self._scrape_web(normalized_id)

        except Exception as e:
            logger.warning(f"API scraping failed for {normalized_id}, trying web scraping: {e}")
            return self._scrape_web(normalized_id)

    def search_by_name(self, name: str, limit: int = 5) -> list:
        """Search Firefox Add-ons by name using the API"""
        api_url = "https://addons.mozilla.org/api/v5/addons/search/"
        params = {
            "q": name,
            "type": "extension",
            "page_size": min(limit, 10),
        }
        try:
            logger.info(f"Searching Firefox addons for: {name}")
            response = self.session.get(api_url, params=params, timeout=self.timeout)
            if response.status_code != 200:
                return []

            results = []
            for addon in response.json().get("results", [])[:limit]:
                guid = addon.get("guid", "")
                addon_name = self._extract_localized_string(addon.get("name", ""))

                file_data = addon.get("current_version", {}).get("file", {})
                permissions = []
                if isinstance(file_data, dict):
                    permissions = file_data.get("permissions", [])

                data = ExtensionData(
                    extension_id=guid,
                    name=addon_name,
                    publisher=addon.get("authors", [{}])[0].get("name", ""),
                    description=self._extract_localized_string(addon.get("summary", ""))[:500],
                    version=addon.get("current_version", {}).get("version", ""),
                    user_count=f"{addon.get('average_daily_users', 0):,} users",
                    rating=str(addon.get("ratings", {}).get("average", "")),
                    rating_count=str(addon.get("ratings", {}).get("count", "")),
                    store_source=self.store_name,
                    store_url=addon.get("url", ""),
                    permissions=permissions,
                    found=True,
                )
                # Extract icon
                icons = addon.get("icons", {})
                for size in ["128", "64", "32"]:
                    if size in icons:
                        data.icon_url = icons[size]
                        break
                results.append(data)
            return results
        except Exception as e:
            logger.error(f"Firefox search failed for '{name}': {e}")
            return []

    def _scrape_web(self, extension_id: str) -> Optional[ExtensionData]:
        """Fallback web scraping method"""
        url = self.get_extension_url(extension_id)

        try:
            logger.info(f"Scraping Firefox addon via web: {extension_id}")
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 404:
                return self.create_not_found_result(extension_id)

            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            data = ExtensionData(
                extension_id=extension_id,
                name="Unknown Addon",
                store_source=self.store_name,
                store_url=url,
            )

            # Extract name
            name_elem = soup.select_one("h1.AddonTitle")
            if not name_elem:
                name_elem = soup.select_one("h1")
            if name_elem:
                title_text = name_elem.get_text(strip=True)
                if " by " in title_text:
                    data.name = title_text.split(" by ")[0].strip()
                else:
                    data.name = title_text

            # Extract publisher
            author_elem = soup.select_one(".AddonTitle-author a")
            if not author_elem:
                author_elem = soup.select_one(".AddonTitle-author")
            if author_elem:
                data.publisher = author_elem.get_text(strip=True).replace("by ", "")

            # Extract description
            desc_elem = soup.select_one(".Addon-summary")
            if not desc_elem:
                desc_elem = soup.select_one(".AddonDescription-contents")
            if desc_elem:
                data.description = desc_elem.get_text(strip=True)[:500]

            # Extract user count
            users_elem = soup.select_one(".MetadataCard-content")
            if users_elem:
                users_text = users_elem.get_text()
                users_match = re.search(r"([\d,]+)\s+users?", users_text)
                if users_match:
                    data.user_count = f"{users_match.group(1)} users"

            # Extract rating
            rating_elem = soup.select_one(".AddonMeta-rating-title")
            if rating_elem:
                rating_match = re.search(r"(\d+\.?\d*)", rating_elem.get_text())
                if rating_match:
                    data.rating = rating_match.group(1)

            # Extract version
            version_elem = soup.select_one(".AddonMoreInfo-version")
            if version_elem:
                version_text = version_elem.get_text(strip=True)
                version_match = re.search(r"Version\s+(.+)", version_text)
                if version_match:
                    data.version = version_match.group(1)

            # Extract last updated
            updated_elem = soup.select_one(".AddonMoreInfo-last-updated")
            if updated_elem:
                updated_text = updated_elem.get_text(strip=True)
                updated_match = re.search(r"Last updated:\s+(.+)", updated_text)
                if updated_match:
                    data.last_updated = updated_match.group(1)

            if data.name and data.name != "Unknown Addon":
                data.found = True

            logger.info(f"Successfully scraped Firefox addon via web: {data.name}")
            return data

        except Exception as e:
            return self.handle_request_error(extension_id, e)
