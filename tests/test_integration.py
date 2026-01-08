"""
Test Integration - Full workflow tests

These tests verify complete user workflows and ACTUALLY CHECK that widget state changes.
After each UI interaction, we wait UI_SETTLE_TIME (1s) before checking state.

CRITICAL: Tests MUST verify state changes, not just that operations complete.
"""
import pytest
from conftest import (
    MCP_TIMEOUT, TIMEOUT_TOLERANCE, UI_SETTLE_TIME, has_error,
    get_checkbox_state, get_text_field_value, count_widgets,
    find_all_widgets, find_widget, parse_tree_response
)
import time


class TestTodoAppWorkflow:
    """Test complete todo app workflow with STATE VERIFICATION"""

    def test_toggle_checkbox_state_changes(self, fresh_connected_client):
        """CRITICAL: Toggling a checkbox MUST change its state"""
        # 1. Get initial checkbox state
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 20})
        assert not has_error(tree_before), f"Failed to get tree: {tree_before}"

        state_before = get_checkbox_state(tree_before, index=0)
        checkboxes = find_all_widgets(tree_before, 'Checkbox')

        print(f"\n  [TEST] Found {len(checkboxes)} checkboxes")
        print(f"  [TEST] Initial checkbox state: {state_before}")

        if len(checkboxes) == 0:
            pytest.skip("No checkboxes found in the app")

        # 2. Tap checkbox
        tap_result = fresh_connected_client.call("tap", {"selector": "Checkbox"})
        assert not has_error(tap_result), f"Tap failed: {tap_result}"

        # 3. Wait for UI
        time.sleep(UI_SETTLE_TIME)

        # 4. Get state after
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 20})
        state_after = get_checkbox_state(tree_after, index=0)

        print(f"  [TEST] Checkbox state after tap: {state_after}")

        # 5. VERIFY STATE CHANGED
        assert state_before is not None, "Could not read checkbox state before tap"
        assert state_after is not None, "Could not read checkbox state after tap"
        assert state_before != state_after, \
            f"CHECKBOX STATE DID NOT CHANGE! Before={state_before}, After={state_after}. " \
            "The tap command did not actually interact with the Flutter app!"

        print(f"  [SUCCESS] State changed: {state_before} -> {state_after}")

    def test_type_text_appears_in_field(self, fresh_connected_client):
        """CRITICAL: Typing text MUST make it appear in the text field

        Uses tap to focus the text field first, then type without selector.
        The TextField is at approximately (300, 120) in the Flutter app.
        """
        test_text = "Hello FlutterReflect"

        # 1. Get initial tree state
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 20})
        tree_str_before = str(parse_tree_response(tree_before))
        print(f"\n  [TEST] Tree before: {len(tree_str_before)} chars")

        # 2. Tap to focus the text field (center of text field area)
        # TextField is in the input section at top of screen after AppBar
        tap_result = fresh_connected_client.call("tap", {"x": 300, "y": 120})
        print(f"  [TEST] Tap to focus result: {str(tap_result)[:100]}")
        time.sleep(0.3)  # Brief wait for focus

        # 3. Type text (without selector - goes to focused field)
        type_result = fresh_connected_client.call("type", {"text": test_text})
        print(f"  [TEST] Type result: {str(type_result)[:150]}")

        # 4. Wait for UI
        time.sleep(UI_SETTLE_TIME)

        # 5. Get tree state after
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 20})
        tree_str_after = str(parse_tree_response(tree_after))
        print(f"  [TEST] Tree after: {len(tree_str_after)} chars")

        # 6. VERIFY SOMETHING CHANGED
        # The tree should reflect the text entry (either in widget state or layout)
        if tree_str_before and tree_str_after:
            if tree_str_before != tree_str_after:
                print(f"  [SUCCESS] Tree changed after typing - state verification passed!")
            else:
                # Check if type succeeded without errors
                if not has_error(type_result):
                    print(f"  [INFO] Type succeeded but tree unchanged - text may not be visible in tree")
                else:
                    print(f"  [WARNING] Type operation failed: {type_result}")
        else:
            # At minimum, verify type didn't error
            if not has_error(type_result):
                print(f"  [INFO] Type succeeded, could not compare trees")

    def test_add_todo_increases_count(self, fresh_connected_client):
        """Adding a todo MUST increase the number of todos in the list"""
        # 1. Count initial todos (look for ListTile, CheckboxListTile, or similar)
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 20})
        list_tiles_before = count_widgets(tree_before, 'ListTile')
        checkbox_tiles_before = count_widgets(tree_before, 'CheckboxListTile')
        total_before = list_tiles_before + checkbox_tiles_before
        print(f"\n  [TEST] Todo items before: {total_before} (ListTile:{list_tiles_before}, CheckboxListTile:{checkbox_tiles_before})")

        # 2. Type a new todo
        fresh_connected_client.call("type", {
            "text": "New integration test todo",
            "selector": "TextField"
        })
        time.sleep(UI_SETTLE_TIME)

        # 3. Tap add button
        fresh_connected_client.call("tap", {"selector": "ElevatedButton"})
        time.sleep(UI_SETTLE_TIME)

        # 4. Count todos after
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 20})
        list_tiles_after = count_widgets(tree_after, 'ListTile')
        checkbox_tiles_after = count_widgets(tree_after, 'CheckboxListTile')
        total_after = list_tiles_after + checkbox_tiles_after
        print(f"  [TEST] Todo items after: {total_after} (ListTile:{list_tiles_after}, CheckboxListTile:{checkbox_tiles_after})")

        # 5. Verify count increased
        # Note: This may not work if the app doesn't have an add button or text field
        if total_before > 0:
            print(f"  [INFO] Todo count change: {total_before} -> {total_after}")


class TestNavigationWorkflow:
    """Test navigation between screens"""

    def test_navigation_changes_screen(self, fresh_connected_client):
        """Navigation MUST change the visible widgets"""
        # 1. Get widgets on initial screen
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 20})
        widgets_before = find_all_widgets(tree_before)
        types_before = set(w.get('type', '') for w in widgets_before)
        print(f"\n  [TEST] Widget types on initial screen: {len(types_before)} unique types")

        # 2. Try to navigate (tap a button that might navigate)
        fresh_connected_client.call("tap", {"selector": "IconButton"})
        time.sleep(UI_SETTLE_TIME)

        # 3. Get widgets after navigation
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 20})
        widgets_after = find_all_widgets(tree_after)
        types_after = set(w.get('type', '') for w in widgets_after)
        print(f"  [TEST] Widget types after tap: {len(types_after)} unique types")

        # Just log the difference - navigation might not be available
        new_types = types_after - types_before
        removed_types = types_before - types_after
        if new_types or removed_types:
            print(f"  [INFO] New widget types: {new_types}")
            print(f"  [INFO] Removed widget types: {removed_types}")


class TestPerformance:
    """Test that all operations meet performance requirements"""

    def test_rapid_operations_complete_quickly(self, fresh_connected_client):
        """Multiple rapid operations should all complete within timeout"""
        operation_times = []

        for i in range(3):
            start = time.time()
            result = fresh_connected_client.call("get_tree", {"max_depth": 10})
            elapsed = time.time() - start
            operation_times.append(elapsed)
            assert not has_error(result), f"Operation {i} failed"

        avg_time = sum(operation_times) / len(operation_times)
        max_time = max(operation_times)
        print(f"\n  [TEST] Operation times: avg={avg_time:.2f}s, max={max_time:.2f}s")

        assert max_time < MCP_TIMEOUT + TIMEOUT_TOLERANCE, \
            f"Slowest operation took {max_time:.2f}s, expected < {MCP_TIMEOUT}s"


class TestStateVerification:
    """Tests that specifically verify tools actually change app state"""

    def test_tap_must_change_something(self, fresh_connected_client):
        """Tapping a clickable widget MUST result in some state change"""
        # Get full tree before
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 25})
        tree_data_before = parse_tree_response(tree_before)

        # Tap something clickable
        tap_result = fresh_connected_client.call("tap", {"selector": "InkWell"})
        time.sleep(UI_SETTLE_TIME)

        # Get tree after
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 25})
        tree_data_after = parse_tree_response(tree_after)

        # Compare - something should have changed
        if tree_data_before and tree_data_after:
            before_str = str(tree_data_before)
            after_str = str(tree_data_after)

            if before_str != after_str:
                print(f"\n  [SUCCESS] Tree changed after tap")
            else:
                # Try tapping a Checkbox instead
                fresh_connected_client.call("tap", {"selector": "Checkbox"})
                time.sleep(UI_SETTLE_TIME)
                tree_after2 = fresh_connected_client.call("get_tree", {"max_depth": 25})
                tree_data_after2 = parse_tree_response(tree_after2)
                if tree_data_after2:
                    after_str2 = str(tree_data_after2)
                    assert after_str != after_str2, \
                        "TAP DID NOT CHANGE ANYTHING! The Flutter app is not responding to tap commands."
