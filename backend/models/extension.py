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
        # Handle None values and ensure correct types
        cleaned_data = {}
        for key, value in data.items():
            if key in cls.__dataclass_fields__:
                if value is None and key in [
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
                ]:
                    cleaned_data[key] = ""
                elif key == "permissions" and value is None:
                    cleaned_data[key] = []
                else:
                    cleaned_data[key] = value

        return cls(**cleaned_data)
