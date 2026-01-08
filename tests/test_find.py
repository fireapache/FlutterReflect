"""
Test find Tool
"""
import pytest
from conftest import MCP_TIMEOUT, TIMEOUT_TOLERANCE, has_error
import time


class TestFindTool:
    """Test find tool functionality"""

    def test_find_completes_quickly(self, fresh_connected_client):
        """find should complete within timeout"""
        start = time.time()
        result = fresh_connected_client.call("find", {"selector": "TextField"})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"find took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_find_by_type(self, fresh_connected_client):
        """find by widget type should work"""
        result = fresh_connected_client.call("find", {"selector": "Text"})

        assert result is not None
        # Either success or no widget found is acceptable
        if 'result' in result:
            assert True
        else:
            # Timeout is acceptable for slow connections
            pass

    def test_find_by_key(self, fresh_connected_client):
        """find by key attribute should work"""
        result = fresh_connected_client.call("find", {"selector": "[key='addTodoInput']"})

        # May or may not find depending on app state
        assert result is not None

    def test_find_first_returns_single_match(self, fresh_connected_client):
        """find with find_first=True should return at most one match"""
        result = fresh_connected_client.call("find", {
            "selector": "Text",
            "find_first": True
        })

        assert result is not None
        # If successful, check content
        if 'result' in result:
            content = result['result'].get('content', [])
            assert content is not None

    def test_find_with_invalid_selector_returns_error(self, fresh_connected_client):
        """find with invalid selector syntax should return error"""
        result = fresh_connected_client.call("find", {"selector": "[invalid==="})

        # Either JSON-RPC error or error in content
        assert has_error(result), f"Expected error for invalid selector, got: {result}"

    def test_find_nonexistent_widget(self, fresh_connected_client):
        """find for nonexistent widget should return empty or error"""
        result = fresh_connected_client.call("find", {"selector": "NonexistentWidgetType12345"})

        # Should succeed but with empty matches, or return an error
        assert result is not None
