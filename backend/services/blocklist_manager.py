"""
Blocklist manager for checking extensions against known malicious extension lists.
"""
import logging
import re
import threading
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

BLOCKLIST_TTL = 24 * 60 * 60  # 24 hours

BLOCKLIST_SOURCES = [
    {
        "name": "Malicious Extension Sentry",
        "url": (
            "https://raw.githubusercontent.com/toborrm9/"
            "malicious_extension_sentry/main/Malicious-Extensions.md"
        ),
        "format": "markdown",
        "info_url": "https://github.com/toborrm9/malicious_extension_sentry",
    },
]


class BlocklistManager:
    """Manages blocklists for checking extensions against known malicious lists."""

    def __init__(self, sources=None):
        self._sources = sources or BLOCKLIST_SOURCES
        self._blocklist: Dict[str, List[dict]] = {}  # extension_id -> [{source, url}]
        self._lock = threading.Lock()
        self._last_refresh: Optional[float] = None
        self._source_stats: Dict[str, int] = {}  # source_name -> count of IDs

    def refresh_blocklists(self):
        """Fetch and parse all blocklist sources."""
        new_blocklist: Dict[str, List[dict]] = {}
        new_stats: Dict[str, int] = {}

        for source in self._sources:
            try:
                entries = self._fetch_source(source)
                new_stats[source["name"]] = len(entries)
                for entry in entries:
                    if isinstance(entry, tuple):
                        ext_id, ext_name = entry
                    else:
                        ext_id, ext_name = entry, None
                    ext_id_lower = ext_id.lower().strip()
                    if not ext_id_lower:
                        continue
                    if ext_id_lower not in new_blocklist:
                        new_blocklist[ext_id_lower] = []
                    match = {
                        "source": source["name"],
                        "url": source.get("info_url", source["url"]),
                    }
                    if ext_name:
                        match["name"] = ext_name
                    new_blocklist[ext_id_lower].append(match)
                logger.info(f"Loaded {len(entries)} IDs from blocklist: {source['name']}")
            except Exception as e:
                logger.error(f"Failed to fetch blocklist {source['name']}: {e}")
                new_stats[source["name"]] = 0

        with self._lock:
            self._blocklist = new_blocklist
            self._last_refresh = time.time()
            self._source_stats = new_stats

        total = len(new_blocklist)
        logger.info(
            f"Blocklist refresh complete: {total} unique extension IDs from "
            f"{len(self._sources)} sources"
        )

    def _fetch_source(self, source: dict) -> list:
        """Fetch and parse a single blocklist source. Returns list of IDs or (id, name) tuples."""
        response = requests.get(source["url"], timeout=30)
        response.raise_for_status()
        content = response.text

        fmt = source.get("format", "text")
        if fmt == "json":
            return self._parse_json(content)
        elif fmt == "markdown":
            return self._parse_markdown(content)
        else:
            return self._parse_text(content)

    def _parse_text(self, content: str) -> List[str]:
        """Parse line-based text format (one ID per line, # for comments)."""
        ids = []
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                # Take first token (in case of comments after ID)
                ext_id = line.split()[0]
                if ext_id:
                    ids.append(ext_id)
        return ids

    def _parse_json(self, content: str) -> list:
        """Parse JSON format (array of strings or array of objects with 'id' key)."""
        import json

        data = json.loads(content)
        if not isinstance(data, list):
            return []
        results = []
        for item in data:
            if isinstance(item, str):
                results.append(item)
            elif isinstance(item, dict) and "id" in item:
                name = item.get("name")
                results.append((str(item["id"]), name) if name else str(item["id"]))
        return results

    def _parse_markdown(self, content: str) -> list:
        """Parse markdown table format with | Extension ID | Name | columns."""
        results = []
        for line in content.splitlines():
            match = re.match(r"\|\s*([a-z]{32})\s*\|\s*([^|]+)", line)
            if match:
                ext_id = match.group(1)
                name = match.group(2).strip()
                results.append((ext_id, name) if name else ext_id)
        return results

    def check_extension(self, extension_id: str) -> List[dict]:
        """Check if an extension is on any blocklist."""
        self._refresh_if_stale()
        with self._lock:
            return list(self._blocklist.get(extension_id.lower().strip(), []))

    def _refresh_if_stale(self):
        """Refresh blocklists if cache has expired."""
        with self._lock:
            if self._last_refresh is None:
                needs_refresh = True
            else:
                needs_refresh = (time.time() - self._last_refresh) > BLOCKLIST_TTL

        if needs_refresh:
            self.refresh_blocklists()

    def get_status(self) -> dict:
        """Get blocklist status information."""
        with self._lock:
            return {
                "last_refresh": self._last_refresh,
                "sources": self._source_stats,
                "total_ids": len(self._blocklist),
                "source_count": len(self._sources),
            }
