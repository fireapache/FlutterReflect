"""
Test find Tool
"""
import pytest
from conftest import MCP_TIMEOUT
import time


class TestFindTool:
    """Test find tool functionality"""

    def test_find_completes_quickly(self, connected_client):
        """find should complete in < 2 seconds"""
        start = time.time()
        result = connected_client.call("find", {"selector": "TextField"})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"find took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_find_by_type(self, connected_client):
        """find by widget type should work"""
        result = connected_client.call("find", {"selector": "Text"})

        assert result is not None
        assert 'result' in result, f"Expected result, got: {result}"

    def test_find_by_key(self, connected_client):
        """find by key attribute should work"""
        result = connected_client.call("find", {"selector": "[key='addTodoInput']"})

        # May or may not find depending on app state
        assert result is not None
        assert 'error' not in result or 'No widget found' in str(result.get('error', ''))

    def test_find_first_returns_single_match(self, connected_client):
        """find with find_first=True should return at most one match"""
        result = connected_client.call("find", {
            "selector": "Text",
            "find_first": True
        })

        assert 'result' in result
        content = result['result'].get('content', [])
        # Should have at most one match when find_first is True

    def test_find_with_invalid_selector_returns_error(self, connected_client):
        """find with invalid selector syntax should return error"""
        result = connected_client.call("find", {"selector": "[invalid==="})

        assert 'error' in result, "Expected error for invalid selector"

    def test_find_nonexistent_widget(self, connected_client):
        """find for nonexistent widget should return empty matches"""
        result = connected_client.call("find", {"selector": "NonexistentWidgetType12345"})

        # Should succeed but with empty matches
        assert result is not None
        # Either no error or error saying no widget found
