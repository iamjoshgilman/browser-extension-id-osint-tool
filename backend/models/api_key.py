"""
API Key data model
"""
from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class ApiKeyData:
    """API Key data structure"""

    id: Optional[int]
    key_hash: str
    key_prefix: str
    name: str
    description: str = ""
    created_by: str = ""
    rate_limit_per_minute: int = 30
    rate_limit_per_hour: int = 500
    is_active: bool = True
    permissions: List[str] = None
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: Optional[str] = None
    revoked_at: Optional[str] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ["search", "bulk-search", "search-by-name"]

    def to_dict(self):
        """Convert to dictionary"""
        data = asdict(self)
        # Ensure permissions is always a list
        if data.get("permissions") is None:
            data["permissions"] = ["search", "bulk-search", "search-by-name"]
        return data

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        # Handle None values and ensure correct types
        cleaned_data = {}
        for key, value in data.items():
            if key in cls.__dataclass_fields__:
                if value is None and key in [
                    "description",
                    "created_by",
                    "last_used_at",
                    "expires_at",
                    "created_at",
                    "revoked_at",
                ]:
                    cleaned_data[key] = "" if key in ["description", "created_by"] else None
                elif key == "permissions" and value is None:
                    cleaned_data[key] = ["search", "bulk-search", "search-by-name"]
                elif key in ["rate_limit_per_minute", "rate_limit_per_hour"] and value is None:
                    cleaned_data[key] = 30 if key == "rate_limit_per_minute" else 500
                elif key == "is_active" and value is None:
                    cleaned_data[key] = True
                else:
                    cleaned_data[key] = value

        return cls(**cleaned_data)
