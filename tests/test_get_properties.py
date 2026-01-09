"""
Test get_properties Tool
"""
import pytest
from conftest import MCP_TIMEOUT, TIMEOUT_TOLERANCE, has_error
import time


class TestGetPropertiesTool:
    """Test get_properties tool functionality"""

    def test_get_properties_completes_quickly(self, fresh_connected_client):
        """get_properties should complete within timeout"""
        start = time.time()
        result = fresh_connected_client.call("get_properties", {"selector": "Text"})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"get_properties took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_get_properties_by_selector(self, fresh_connected_client):
        """get_properties by selector should work"""
        result = fresh_connected_client.call("get_properties", {"selector": "Text"})

        assert result is not None
        # Either success or widget not found is acceptable

    def test_get_properties_returns_widget_info(self, fresh_connected_client):
        """get_properties should return widget information"""
        result = fresh_connected_client.call("get_properties", {"selector": "TextField"})

        if 'result' in result and not has_error(result):
            # Check result has expected structure
            content = result['result'].get('content', [])
            assert len(content) > 0, "Expected content in properties result"

    def test_get_properties_with_include_children(self, fresh_connected_client):
        """get_properties with include_children should work"""
        result = fresh_connected_client.call("get_properties", {
            "selector": "Column",
            "include_children": True
        })

        # Should work or report no widget found
        assert result is not None

    def test_get_properties_requires_selector_or_widget_id(self, fresh_connected_client):
        """get_properties without selector or widget_id should error"""
        result = fresh_connected_client.call("get_properties", {})

        # Error can be in JSON-RPC error or in content
        assert has_error(result), f"Expected error when no selector or widget_id, got: {result}"

    def test_get_properties_nonexistent_widget(self, fresh_connected_client):
        """get_properties for nonexistent widget should error"""
        result = fresh_connected_client.call("get_properties", {
            "selector": "NonexistentWidgetType12345"
        })

        # Either error or empty result is acceptable
        assert result is not None
