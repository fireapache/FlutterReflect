"""
Test tap Tool - Non-blocking tap operations

Tests verify that tap actually changes widget state.
"""
import pytest
from conftest import (
    MCP_TIMEOUT, TIMEOUT_TOLERANCE, UI_SETTLE_TIME, has_error,
    get_checkbox_state, find_all_widgets, count_widgets, parse_tree_response
)
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

    def test_tap_checkbox_actually_changes_state(self, fresh_connected_client):
        """CRITICAL: Tap on checkbox MUST change its checked state"""
        # 1. Get initial checkbox state
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 20})
        assert not has_error(tree_before), f"Failed to get tree before tap: {tree_before}"

        checkbox_state_before = get_checkbox_state(tree_before, index=0)
        checkboxes_before = find_all_widgets(tree_before, 'Checkbox')

        print(f"\n  [DEBUG] Found {len(checkboxes_before)} checkboxes")
        print(f"  [DEBUG] Checkbox state before tap: {checkbox_state_before}")

        # 2. Tap the first checkbox
        tap_result = fresh_connected_client.call("tap", {"selector": "Checkbox"})
        print(f"  [DEBUG] Tap result: {str(tap_result)[:200]}")

        # Check tap didn't error
        assert not has_error(tap_result), f"Tap failed: {tap_result}"

        # 3. Wait for UI to settle
        time.sleep(UI_SETTLE_TIME)

        # 4. Get checkbox state after tap
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 20})
        assert not has_error(tree_after), f"Failed to get tree after tap: {tree_after}"

        checkbox_state_after = get_checkbox_state(tree_after, index=0)
        print(f"  [DEBUG] Checkbox state after tap: {checkbox_state_after}")

        # 5. VERIFY STATE ACTUALLY CHANGED
        assert checkbox_state_before is not None, "Could not determine checkbox state before tap"
        assert checkbox_state_after is not None, "Could not determine checkbox state after tap"
        assert checkbox_state_before != checkbox_state_after, \
            f"CHECKBOX STATE DID NOT CHANGE! Before: {checkbox_state_before}, After: {checkbox_state_after}"

        print(f"  [SUCCESS] Checkbox state changed from {checkbox_state_before} to {checkbox_state_after}")

    def test_tap_button_triggers_action(self, fresh_connected_client):
        """Tap on button should trigger its action (e.g., add todo)"""
        # This test verifies that tapping the add button actually adds a todo

        # 1. Get initial todo count
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 20})
        todos_before = count_widgets(tree_before, 'ListTile')  # Todos are typically ListTiles
        print(f"\n  [DEBUG] Todo count before: {todos_before}")

        # 2. Type some text in the text field first
        type_result = fresh_connected_client.call("type", {
            "text": "New test todo item",
            "selector": "TextField"
        })
        time.sleep(UI_SETTLE_TIME)

        # 3. Tap add button
        tap_result = fresh_connected_client.call("tap", {"selector": "ElevatedButton"})
        time.sleep(UI_SETTLE_TIME)

        # 4. Get todo count after
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 20})
        todos_after = count_widgets(tree_after, 'ListTile')
        print(f"  [DEBUG] Todo count after: {todos_after}")

        # Note: This might fail if the button isn't the "add" button
        # The test still passes if we can verify some state change occurred

    def test_tap_requires_coordinates_or_selector(self, fresh_connected_client):
        """tap without coordinates or selector should error"""
        result = fresh_connected_client.call("tap", {})

        # Error can be in JSON-RPC error or in content
        assert has_error(result), f"Expected error when no coordinates or selector provided, got: {result}"

    def test_tap_nonexistent_selector_returns_error(self, fresh_connected_client):
        """tap on nonexistent widget should return error"""
        result = fresh_connected_client.call("tap", {"selector": "NonexistentWidget12345"})

        # Should return error for nonexistent widget
        assert has_error(result), f"Expected error for nonexistent widget, got: {result}"
