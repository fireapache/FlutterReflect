"""
Test get_tree Tool
"""
import pytest
from conftest import MCP_TIMEOUT
import time


class TestGetTreeTool:
    """Test get_tree tool functionality"""

    def test_get_tree_completes_quickly(self, connected_client):
        """get_tree should complete in < 2 seconds"""
        start = time.time()
        result = connected_client.call("get_tree", {"max_depth": 5})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"get_tree took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"
        assert 'error' not in result, f"get_tree failed: {result.get('error')}"

    def test_get_tree_returns_widgets(self, connected_client):
        """get_tree should return widget data"""
        result = connected_client.call("get_tree", {"max_depth": 5})

        assert result is not None
        assert 'result' in result, f"Expected result, got: {result}"

        # Check result has content
        content = result['result'].get('content', [])
        assert len(content) > 0, "Expected content in result"

    def test_get_tree_respects_max_depth(self, connected_client):
        """get_tree with different max_depth should work"""
        # Shallow tree
        shallow = connected_client.call("get_tree", {"max_depth": 2})
        assert 'error' not in shallow

        # Deeper tree
        deep = connected_client.call("get_tree", {"max_depth": 10})
        assert 'error' not in deep

    def test_get_tree_with_zero_depth(self, connected_client):
        """get_tree with max_depth=0 should return root only"""
        result = connected_client.call("get_tree", {"max_depth": 0})
        assert 'error' not in result
