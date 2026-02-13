"""
Extension data model
"""
from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class ExtensionData:
    """Unified extension data structure"""

    extension_id: str
    name: str
    store_source: str
    publisher: str = ""
    description: str = ""
    version: str = ""
    user_count: str = ""
    category: str = ""
    rating: str = ""
    rating_count: str = ""
    last_updated: str = ""
    store_url: str = ""
    icon_url: str = ""
    homepage_url: str = ""
    privacy_policy_url: str = ""
    permissions: List[str] = None
    found: bool = True
    cached: bool = False
    scraped_at: Optional[str] = None

    # SOC-relevant fields
    content_rating: str = ""
    file_size: str = ""
    languages: str = ""
    release_date: str = ""
    update_frequency: str = ""
    price: str = ""
    developer_website: str = ""
    developer_email: str = ""
    support_url: str = ""

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []

    def to_dict(self):
        """Convert to dictionary"""
        data = asdict(self)
        # Ensure permissions is always a list
        if data.get("permissions") is None:
            data["permissions"] = []
        return data

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        # String fields that should default to "" instead of None
        string_fields = {
            "publisher",
            "description",
            "version",
            "user_count",
            "category",
            "rating",
            "rating_count",
            "last_updated",
            "store_url",
            "icon_url",
            "homepage_url",
            "privacy_policy_url",
            "content_rating",
            "file_size",
            "languages",
            "release_date",
            "update_frequency",
            "price",
            "developer_website",
            "developer_email",
            "support_url",
        }

        # Handle None values and ensure correct types
        cleaned_data = {}
        for key, value in data.items():
            if key in cls.__dataclass_fields__:
                if value is None and key in string_fields:
                    cleaned_data[key] = ""
                elif key == "permissions" and value is None:
                    cleaned_data[key] = []
                else:
                    cleaned_data[key] = value

        return cls(**cleaned_data)
