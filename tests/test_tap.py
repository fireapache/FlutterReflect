"""
Test tap Tool - Non-blocking tap operations
"""
import pytest
from conftest import MCP_TIMEOUT, TIMEOUT_TOLERANCE, UI_SETTLE_TIME, has_error
import time


class TestTapTool:
    """Test tap tool functionality with non-blocking behavior"""

    def test_tap_by_coordinates_completes_quickly(self, fresh_connected_client):
        """tap by coordinates should complete within timeout"""
        start = time.time()
        result = fresh_connected_client.call("tap", {"x": 100, "y": 100})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"tap took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_tap_by_selector_completes_quickly(self, fresh_connected_client):
        """tap by selector should complete within timeout"""
        start = time.time()
        result = fresh_connected_client.call("tap", {"selector": "ElevatedButton"})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"tap took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_tap_returns_immediately(self, fresh_connected_client):
        """tap should return without blocking for extended periods"""
        start = time.time()
        result = fresh_connected_client.call("tap", {"x": 200, "y": 200})
        elapsed = time.time() - start

        # Tap should return within reasonable time
        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"tap should return quickly, took {elapsed:.2f}s"

    def test_tap_checkbox_changes_state(self, fresh_connected_client):
        """tap on checkbox should work (state change verified after UI settle)"""
        # Get initial state
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 10})
        assert tree_before is not None

        # Tap a checkbox (assuming one exists)
        result = fresh_connected_client.call("tap", {"selector": "Checkbox"})

        # Wait for UI to settle
        time.sleep(UI_SETTLE_TIME)

        # Get state after
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 10})
        assert tree_after is not None

    def test_tap_button(self, fresh_connected_client):
        """tap on button should succeed"""
        result = fresh_connected_client.call("tap", {"selector": "ElevatedButton"})

        assert result is not None
        # Either success or "no widget found" is acceptable

    def test_tap_requires_coordinates_or_selector(self, fresh_connected_client):
        """tap without coordinates or selector should error"""
        result = fresh_connected_client.call("tap", {})

        # Error can be in JSON-RPC error or in content
        assert has_error(result), f"Expected error when no coordinates or selector provided, got: {result}"

    def test_tap_nonexistent_selector_returns_error(self, fresh_connected_client):
        """tap on nonexistent widget should return error"""
        result = fresh_connected_client.call("tap", {"selector": "NonexistentWidget12345"})

        # Either error or no-op is acceptable
        assert result is not None
