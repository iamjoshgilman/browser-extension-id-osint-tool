"""
Safari Extensions scraper
"""
import re
import logging
from typing import Optional
from scrapers.base import ExtensionScraper
from models.extension import ExtensionData

logger = logging.getLogger(__name__)


class SafariExtensionScraper(ExtensionScraper):
    """Safari Extensions scraper using iTunes API"""

    def __init__(self):
        super().__init__()
        self.store_name = "safari"

    def validate_id(self, extension_id: str) -> bool:
        """Safari uses numeric Apple Track IDs (7-13 digits)"""
        return bool(re.match(r"^\d{7,13}$", extension_id.strip()))

    def normalize_id(self, extension_id: str) -> str:
        """Normalize extension ID"""
        return extension_id.strip()

    def get_extension_url(self, extension_id: str) -> str:
        """Get the Safari Extensions URL for an extension"""
        return f"https://apps.apple.com/app/id{extension_id}"

    def scrape(self, extension_id: str) -> Optional[ExtensionData]:
        """Scrape extension data from Safari Extensions (via iTunes API)"""
        if not self.validate_id(extension_id):
            logger.warning(f"Invalid Safari extension ID format: {extension_id}")
            return self.create_not_found_result(extension_id)

        normalized_id = self.normalize_id(extension_id)

        # iTunes Lookup API
        api_url = f"https://itunes.apple.com/lookup?id={normalized_id}&country=us"

        try:
            logger.info(f"Scraping Safari extension via iTunes API: {normalized_id}")
            response = self.session.get(api_url, timeout=self.timeout)

            if response.status_code != 200:
                logger.warning(
                    f"iTunes API returned status {response.status_code} for {normalized_id}"
                )
                return self.create_not_found_result(normalized_id)

            api_data = response.json()

            # Check if extension was found
            if api_data.get("resultCount", 0) == 0:
                logger.info(f"Safari extension not found: {normalized_id}")
                return self.create_not_found_result(normalized_id)

            # Get first result
            result = api_data.get("results", [{}])[0]

            # Ensure it's a Mac app (Safari extensions can be "mac-software" or "software")
            kind = result.get("kind", "")
            if kind not in ["mac-software", "software"]:
                logger.warning(
                    f"iTunes ID {normalized_id} is not a Mac/software app (kind: {kind})"
                )
                return self.create_not_found_result(normalized_id)

            # Extract description with 500 char limit
            description = result.get("description", "")
            if description:
                description = description[:500]

            # Extract icon URL (prefer 512px, fallback to 100px)
            icon_url = result.get("artworkUrl512", result.get("artworkUrl100", ""))

            # Extract genres/categories
            genres = result.get("genres", [])
            category = ", ".join(genres) if genres else ""

            # Extract homepage URL
            homepage_url = result.get("sellerUrl", "")

            # Extract content advisory rating (4+, 9+, 12+, 17+)
            content_rating = result.get("contentAdvisoryRating", "")

            # Extract file size and format as human-readable
            file_size_bytes = result.get("fileSizeBytes", "")
            file_size = ""
            if file_size_bytes:
                try:
                    size_int = int(file_size_bytes)
                    if size_int >= 1024 * 1024 * 1024:
                        file_size = f"{size_int / (1024 * 1024 * 1024):.1f} GB"
                    elif size_int >= 1024 * 1024:
                        file_size = f"{size_int / (1024 * 1024):.1f} MB"
                    elif size_int >= 1024:
                        file_size = f"{size_int / 1024:.1f} KB"
                    else:
                        file_size = f"{size_int} B"
                except (ValueError, TypeError):
                    pass

            # Extract supported languages
            language_codes = result.get("languageCodesISO2A", [])
            languages = ", ".join(language_codes) if language_codes else ""

            # Extract original release date
            release_date = result.get("releaseDate", "")

            # Extract price
            price = result.get("formattedPrice", "")

            # Extract developer website
            developer_website = result.get("sellerUrl", "")

            # Create extension data
            data = ExtensionData(
                extension_id=normalized_id,
                name=result.get("trackName", "Unknown"),
                publisher=result.get("artistName", ""),
                description=description,
                version=result.get("version", ""),
                rating=str(result.get("averageUserRating", "")) or "",
                rating_count=str(result.get("userRatingCount", "")) or "",
                category=category,
                store_source=self.store_name,
                store_url=result.get("trackViewUrl", self.get_extension_url(normalized_id)),
                icon_url=icon_url,
                homepage_url=homepage_url,
                last_updated=result.get("currentVersionReleaseDate", ""),
                found=True,
                content_rating=content_rating,
                file_size=file_size,
                languages=languages,
                release_date=release_date,
                price=price,
                developer_website=developer_website,
            )

            # Note: iTunes API doesn't provide:
            # - permissions (not available in API)
            # - user_count (not available in API)
            # We leave these as empty defaults

            logger.info(f"Successfully scraped Safari extension via iTunes API: {data.name}")
            return data

        except Exception as e:
            return self.handle_request_error(extension_id, e)

    def search_by_name(self, name: str, limit: int = 5) -> list:
        """Search Safari Extensions by name using iTunes Search API"""
        api_url = "https://itunes.apple.com/search"
        params = {
            "term": name,
            "entity": "macSoftware",
            "limit": min(limit, 10),
            "country": "us",
        }

        try:
            logger.info(f"Searching Safari extensions for: {name}")
            response = self.session.get(api_url, params=params, timeout=self.timeout)

            if response.status_code != 200:
                logger.warning(f"iTunes Search API returned status {response.status_code}")
                return []

            api_data = response.json()
            results = []

            for result in api_data.get("results", [])[:limit]:
                track_id = str(result.get("trackId", ""))
                track_name = result.get("trackName", "")

                # Skip if no valid ID
                if not track_id:
                    continue

                # Extract description with 500 char limit
                description = result.get("description", "")
                if description:
                    description = description[:500]

                # Extract icon URL
                icon_url = result.get("artworkUrl512", result.get("artworkUrl100", ""))

                # Extract genres/categories
                genres = result.get("genres", [])
                category = ", ".join(genres) if genres else ""

                # Extract homepage URL
                homepage_url = result.get("sellerUrl", "")

                data = ExtensionData(
                    extension_id=track_id,
                    name=track_name,
                    publisher=result.get("artistName", ""),
                    description=description,
                    version=result.get("version", ""),
                    rating=str(result.get("averageUserRating", "")) or "",
                    rating_count=str(result.get("userRatingCount", "")) or "",
                    category=category,
                    store_source=self.store_name,
                    store_url=result.get("trackViewUrl", self.get_extension_url(track_id)),
                    icon_url=icon_url,
                    homepage_url=homepage_url,
                    found=True,
                )

                results.append(data)

            return results

        except Exception as e:
            logger.error(f"Safari search failed for '{name}': {e}")
            return []
