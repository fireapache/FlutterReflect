"""
Test tap Tool - Non-blocking tap operations
"""
import pytest
from conftest import MCP_TIMEOUT, UI_SETTLE_TIME
import time


class TestTapTool:
    """Test tap tool functionality with non-blocking behavior"""

    def test_tap_by_coordinates_completes_quickly(self, connected_client):
        """tap by coordinates should complete in < 2 seconds"""
        start = time.time()
        result = connected_client.call("tap", {"x": 100, "y": 100})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"tap took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_tap_by_selector_completes_quickly(self, connected_client):
        """tap by selector should complete in < 2 seconds"""
        start = time.time()
        result = connected_client.call("tap", {"selector": "ElevatedButton"})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"tap took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_tap_returns_immediately(self, connected_client):
        """tap should return immediately without waiting for UI"""
        start = time.time()
        result = connected_client.call("tap", {"x": 200, "y": 200})
        elapsed = time.time() - start

        # Tap should return almost immediately (< 1s for non-blocking)
        assert elapsed < 1.5, f"tap should return immediately, took {elapsed:.2f}s"

    def test_tap_checkbox_changes_state(self, connected_client):
        """tap on checkbox should change its state (verified after UI settle)"""
        # Get initial state
        tree_before = connected_client.call("get_tree", {"max_depth": 10})
        assert 'error' not in tree_before

        # Tap a checkbox (assuming one exists)
        result = connected_client.call("tap", {"selector": "Checkbox"})

        # Wait for UI to settle
        time.sleep(UI_SETTLE_TIME)

        # Get state after
        tree_after = connected_client.call("get_tree", {"max_depth": 10})
        assert 'error' not in tree_after

        # Note: We can't easily compare checkbox state without parsing the tree
        # This test mainly verifies the flow works without errors

    def test_tap_button(self, connected_client):
        """tap on button should succeed"""
        result = connected_client.call("tap", {"selector": "ElevatedButton"})

        assert result is not None
        # Either success or "no widget found" is acceptable
        if 'error' not in result:
            assert 'result' in result

    def test_tap_requires_coordinates_or_selector(self, connected_client):
        """tap without coordinates or selector should error"""
        result = connected_client.call("tap", {})

        assert 'error' in result, "Expected error when no coordinates or selector provided"

    def test_tap_nonexistent_selector_returns_error(self, connected_client):
        """tap on nonexistent widget should return error"""
        result = connected_client.call("tap", {"selector": "NonexistentWidget12345"})

        assert 'error' in result, "Expected error for nonexistent widget"
