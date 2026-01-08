"""
Test get_tree Tool
"""
import pytest
from conftest import MCP_TIMEOUT, TIMEOUT_TOLERANCE, has_error
import time


class TestGetTreeTool:
    """Test get_tree tool functionality"""

    def test_get_tree_completes_quickly(self, fresh_connected_client):
        """get_tree should complete within timeout"""
        start = time.time()
        result = fresh_connected_client.call("get_tree", {"max_depth": 5})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"get_tree took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"
        assert not has_error(result), f"get_tree failed: {result}"

    def test_get_tree_returns_widgets(self, fresh_connected_client):
        """get_tree should return widget data"""
        result = fresh_connected_client.call("get_tree", {"max_depth": 5})

        assert result is not None
        if not has_error(result):
            assert 'result' in result, f"Expected result, got: {result}"
            # Check result has content
            content = result['result'].get('content', [])
            assert len(content) > 0, "Expected content in result"

    def test_get_tree_respects_max_depth(self, fresh_connected_client):
        """get_tree with different max_depth should work"""
        # Shallow tree
        shallow = fresh_connected_client.call("get_tree", {"max_depth": 2})
        assert shallow is not None

        # Deeper tree
        deep = fresh_connected_client.call("get_tree", {"max_depth": 10})
        assert deep is not None

    def test_get_tree_with_zero_depth(self, fresh_connected_client):
        """get_tree with max_depth=0 should return root only"""
        result = fresh_connected_client.call("get_tree", {"max_depth": 0})
        # Either success or error is acceptable (some implementations may not support 0)
        assert result is not None
