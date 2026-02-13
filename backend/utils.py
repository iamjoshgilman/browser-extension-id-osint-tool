"""
Utility functions for Browser Extension OSINT Tool
"""
import re
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def validate_extension_id(extension_id: str, store: str) -> bool:
    """
    Validate extension ID format for different stores

    Args:
        extension_id: The extension ID to validate
        store: The store type (chrome, firefox, edge)

    Returns:
        bool: True if valid, False otherwise
    """
    if not extension_id:
        return False

    if store == "chrome":
        # Chrome: 32 lowercase letters
        return bool(re.match(r"^[a-z]{32}$", extension_id))

    elif store == "firefox":
        # Firefox: Various formats allowed
        return len(extension_id) > 1

    elif store == "edge":
        # Edge: 32 alphanumeric characters
        return bool(re.match(r"^[a-zA-Z0-9]{32}$", extension_id))

    return False


def sanitize_extension_id(extension_id: str) -> str:
    """
    Sanitize extension ID to prevent injection attacks

    Args:
        extension_id: The extension ID to sanitize

    Returns:
        str: Sanitized extension ID
    """
    # Remove any potentially dangerous characters
    # Allow alphanumeric, hyphens, underscores, @ and dots
    sanitized = re.sub(r"[^a-zA-Z0-9\-_@.{}]", "", extension_id)
    return sanitized[:256]  # Limit length


def generate_cache_key(extension_id: str, store: str) -> str:
    """
    Generate a cache key for extension data

    Args:
        extension_id: The extension ID
        store: The store name

    Returns:
        str: Cache key
    """
    combined = f"{store}:{extension_id}"
    return hashlib.md5(combined.encode()).hexdigest()


def parse_user_count(user_count_str: str) -> int:
    """
    Parse user count string to integer

    Args:
        user_count_str: User count string (e.g., "10,000+ users")

    Returns:
        int: Parsed user count
    """
    if not user_count_str:
        return 0

    # Remove non-numeric characters except digits and commas
    clean = re.sub(r"[^\d,]", "", user_count_str)
    clean = clean.replace(",", "")

    try:
        return int(clean)
    except ValueError:
        return 0


def format_user_count(count: int) -> str:
    """
    Format user count for display

    Args:
        count: User count as integer

    Returns:
        str: Formatted user count
    """
    if count >= 1000000:
        return f"{count/1000000:.1f}M+ users"
    elif count >= 1000:
        return f"{count/1000:.0f}K+ users"
    else:
        return f"{count} users"


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to specified length

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        str: Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def extract_domain(url: str) -> str:
    """
    Extract domain from URL

    Args:
        url: URL to extract domain from

    Returns:
        str: Domain name
    """
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if match:
        return match.group(1)
    return ""


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid

    Args:
        url: URL to validate

    Returns:
        bool: True if valid, False otherwise
    """
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return bool(url_pattern.match(url))


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format

    Returns:
        str: ISO formatted timestamp
    """
    return datetime.now().isoformat()


def calculate_cache_age(scraped_at: str) -> Dict[str, int]:
    """
    Calculate age of cached data

    Args:
        scraped_at: ISO formatted timestamp

    Returns:
        dict: Age in days, hours, minutes
    """
    try:
        scraped_time = datetime.fromisoformat(scraped_at)
        age = datetime.now() - scraped_time

        return {
            "days": age.days,
            "hours": age.seconds // 3600,
            "minutes": (age.seconds % 3600) // 60,
        }
    except (ValueError, TypeError):
        return {"days": 0, "hours": 0, "minutes": 0}


def merge_extension_data(existing: Dict, new: Dict) -> Dict:
    """
    Merge new extension data with existing data

    Args:
        existing: Existing extension data
        new: New extension data

    Returns:
        dict: Merged data
    """
    merged = existing.copy()

    # Update fields that might have changed
    update_fields = ["name", "version", "user_count", "rating", "description", "last_updated"]

    for field in update_fields:
        if field in new and new[field]:
            merged[field] = new[field]

    # Merge permissions lists
    if "permissions" in new and isinstance(new["permissions"], list):
        existing_perms = set(merged.get("permissions", []))
        new_perms = set(new["permissions"])
        merged["permissions"] = list(existing_perms.union(new_perms))

    return merged


def batch_list(items: List, batch_size: int) -> List[List]:
    """
    Split list into batches

    Args:
        items: List to split
        batch_size: Size of each batch

    Returns:
        list: List of batches
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i : i + batch_size])
    return batches


def safe_get(dictionary: Dict, *keys, default=None):
    """
    Safely get nested dictionary values

    Args:
        dictionary: Dictionary to get value from
        *keys: Keys to traverse
        default: Default value if not found

    Returns:
        Value or default
    """
    value = dictionary
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value if value is not None else default
