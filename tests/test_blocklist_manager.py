"""
Tests for BlocklistManager
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from unittest.mock import patch, MagicMock  # noqa: E402
from services.blocklist_manager import BlocklistManager  # noqa: E402


class TestBlocklistParsers:
    """Test blocklist format parsers"""

    def setup_method(self):
        self.manager = BlocklistManager(sources=[])

    def test_parse_text_basic(self):
        content = "abc123\ndef456\nghi789"
        result = self.manager._parse_text(content)
        assert result == ["abc123", "def456", "ghi789"]

    def test_parse_text_with_comments(self):
        content = "# comment\nabc123\n# another comment\ndef456"
        result = self.manager._parse_text(content)
        assert result == ["abc123", "def456"]

    def test_parse_text_with_empty_lines(self):
        content = "abc123\n\n\ndef456\n\n"
        result = self.manager._parse_text(content)
        assert result == ["abc123", "def456"]

    def test_parse_json_string_array(self):
        content = json.dumps(["ext1", "ext2", "ext3"])
        result = self.manager._parse_json(content)
        assert result == ["ext1", "ext2", "ext3"]

    def test_parse_json_object_array(self):
        content = json.dumps([{"id": "ext1", "name": "Bad Ext"}, {"id": "ext2"}])
        result = self.manager._parse_json(content)
        assert len(result) == 2
        assert result[0] == ("ext1", "Bad Ext")
        assert result[1] == "ext2"

    def test_parse_json_invalid(self):
        content = '"not an array"'
        result = self.manager._parse_json(content)
        assert result == []

    def test_parse_markdown_chrome_ids(self):
        content = """
# Malicious Extensions
| Extension ID | Name | Source | Insert Date |
| ------------- | ---- | ------ | ----------- |
| abcdefghijklmnopqrstuvwxyzabcdef | Bad Extension | source.com | 01/01/26 |
| zyxwvutsrqponmlkjihgfedcbazyxwvu | Another Bad | source.com | 01/01/26 |
"""
        result = self.manager._parse_markdown(content)
        assert len(result) == 2
        assert result[0] == ("abcdefghijklmnopqrstuvwxyzabcdef", "Bad Extension")
        assert result[1] == ("zyxwvutsrqponmlkjihgfedcbazyxwvu", "Another Bad")


class TestBlocklistCheck:
    """Test extension checking"""

    def test_check_known_extension(self):
        manager = BlocklistManager(sources=[])
        # Manually populate blocklist
        manager._blocklist = {
            "malicious123": [{"source": "TestList", "url": "https://example.com"}]
        }
        manager._last_refresh = 9999999999  # far future to prevent refresh

        result = manager.check_extension("malicious123")
        assert len(result) == 1
        assert result[0]["source"] == "TestList"

    def test_check_unknown_extension(self):
        manager = BlocklistManager(sources=[])
        manager._blocklist = {}
        manager._last_refresh = 9999999999

        result = manager.check_extension("safe_extension")
        assert result == []

    def test_check_case_insensitive(self):
        manager = BlocklistManager(sources=[])
        manager._blocklist = {"abcdef": [{"source": "TestList", "url": "https://example.com"}]}
        manager._last_refresh = 9999999999

        result = manager.check_extension("ABCDEF")
        assert len(result) == 1

    def test_get_status(self):
        manager = BlocklistManager(sources=[])
        manager._last_refresh = 1000.0
        manager._source_stats = {"TestList": 5}
        manager._blocklist = {"a": [], "b": []}

        status = manager.get_status()
        assert status["last_refresh"] == 1000.0
        assert status["total_ids"] == 2
        assert status["sources"]["TestList"] == 5


class TestBlocklistFetch:
    """Test network fetching with mocks"""

    @patch("services.blocklist_manager.requests.get")
    def test_fetch_text_source(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "ext1\next2\next3"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        manager = BlocklistManager(
            sources=[
                {
                    "name": "TestSource",
                    "url": "https://example.com/list.txt",
                    "format": "text",
                    "info_url": "https://example.com",
                }
            ]
        )
        manager.refresh_blocklists()

        assert len(manager._blocklist) == 3
        assert "ext1" in manager._blocklist

    @patch("services.blocklist_manager.requests.get")
    def test_fetch_failure_graceful(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        manager = BlocklistManager(
            sources=[
                {
                    "name": "FailSource",
                    "url": "https://example.com/list.txt",
                    "format": "text",
                    "info_url": "https://example.com",
                }
            ]
        )
        manager.refresh_blocklists()

        # Should not crash, blocklist should be empty
        assert len(manager._blocklist) == 0
        assert manager._last_refresh is not None


class TestBlocklistAPI:
    """Test blocklist API endpoint"""

    @pytest.fixture
    def client(self):
        from app import app

        app.config["TESTING"] = True
        app.config["API_KEY_REQUIRED"] = False
        with app.test_client() as client:
            yield client

    def test_blocklist_status_endpoint(self, client):
        response = client.get("/api/blocklist/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "total_ids" in data
        assert "source_count" in data
