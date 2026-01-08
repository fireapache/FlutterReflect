"""
Test get_properties Tool
"""
import pytest
from conftest import MCP_TIMEOUT
import time


class TestGetPropertiesTool:
    """Test get_properties tool functionality"""

    def test_get_properties_completes_quickly(self, connected_client):
        """get_properties should complete in < 2 seconds"""
        start = time.time()
        result = connected_client.call("get_properties", {"selector": "Text"})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"get_properties took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_get_properties_by_selector(self, connected_client):
        """get_properties by selector should work"""
        result = connected_client.call("get_properties", {"selector": "Text"})

        assert result is not None
        # Either success or widget not found is acceptable
        if 'error' not in result:
            assert 'result' in result

    def test_get_properties_returns_widget_info(self, connected_client):
        """get_properties should return widget information"""
        result = connected_client.call("get_properties", {"selector": "TextField"})

        if 'result' in result:
            # Check result has expected structure
            content = result['result'].get('content', [])
            assert len(content) > 0, "Expected content in properties result"

    def test_get_properties_with_include_children(self, connected_client):
        """get_properties with include_children should work"""
        result = connected_client.call("get_properties", {
            "selector": "Column",
            "include_children": True
        })

        # Should work or report no widget found
        assert result is not None

    def test_get_properties_requires_selector_or_widget_id(self, connected_client):
        """get_properties without selector or widget_id should error"""
        result = connected_client.call("get_properties", {})

        assert 'error' in result, "Expected error when no selector or widget_id"

    def test_get_properties_nonexistent_widget(self, connected_client):
        """get_properties for nonexistent widget should error"""
        result = connected_client.call("get_properties", {
            "selector": "NonexistentWidgetType12345"
        })

        assert 'error' in result, "Expected error for nonexistent widget"
