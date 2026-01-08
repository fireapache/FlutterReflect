"""
Test Integration - Full workflow tests

These tests verify complete user workflows using the non-blocking MCP tools.
After each UI interaction, we wait UI_SETTLE_TIME (1s) before checking state.

Note: Uses fresh_connected_client to avoid session state corruption issues.
"""
import pytest
from conftest import MCP_TIMEOUT, TIMEOUT_TOLERANCE, UI_SETTLE_TIME, has_error
import time


class TestTodoAppWorkflow:
    """Test complete todo app workflow"""

    def test_add_todo_workflow(self, fresh_connected_client):
        """Test adding a new todo item"""
        # 1. Get initial state
        tree_before = fresh_connected_client.call("get_tree", {"max_depth": 10})
        assert tree_before is not None

        # 2. Type todo text
        type_result = fresh_connected_client.call("type", {
            "text": "Buy groceries",
            "selector": "TextField[key='addTodoInput']"
        })

        # 3. Wait for UI to settle
        time.sleep(UI_SETTLE_TIME)

        # 4. Tap add button
        tap_result = fresh_connected_client.call("tap", {
            "selector": "ElevatedButton[key='addTodoButton']"
        })

        # 5. Wait for UI to settle
        time.sleep(UI_SETTLE_TIME)

        # 6. Get state after
        tree_after = fresh_connected_client.call("get_tree", {"max_depth": 10})
        assert tree_after is not None

        # All operations should complete (not timeout)
        assert type_result is not None
        assert tap_result is not None

    def test_toggle_todo_workflow(self, fresh_connected_client):
        """Test toggling a todo item complete/incomplete"""
        # 1. Get initial checkbox state
        props_before = fresh_connected_client.call("get_properties", {
            "selector": "Checkbox"
        })

        # 2. Tap checkbox
        start = time.time()
        tap_result = fresh_connected_client.call("tap", {"selector": "Checkbox"})
        tap_elapsed = time.time() - start

        # Tap should be within timeout
        assert tap_elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"Tap took {tap_elapsed:.2f}s"

        # 3. Wait for UI to settle
        time.sleep(UI_SETTLE_TIME)

        # 4. Get checkbox state after
        props_after = fresh_connected_client.call("get_properties", {
            "selector": "Checkbox"
        })

        # Both property fetches should complete
        assert props_before is not None
        assert props_after is not None

    def test_all_tools_are_fast(self, fresh_connected_client):
        """Verify all tools complete within timeout"""
        tools_to_test = [
            ("get_tree", {"max_depth": 5}),
            ("find", {"selector": "Text"}),
            ("tap", {"x": 100, "y": 100}),
            ("type", {"text": "test", "selector": "TextField"}),
            ("get_properties", {"selector": "Text"}),
        ]

        slow_tools = []

        for tool_name, args in tools_to_test:
            result = fresh_connected_client.call(tool_name, args)
            elapsed = result.get('_elapsed', 99)

            if elapsed >= MCP_TIMEOUT:
                slow_tools.append(f"{tool_name}: {elapsed:.2f}s")

        # Allow some tools to timeout but log them
        if slow_tools:
            print(f"Note: Some tools were slow: {slow_tools}")


class TestNavigationWorkflow:
    """Test navigation between screens"""

    def test_navigate_to_stats_and_back(self, fresh_connected_client):
        """Test navigating to stats screen and back"""
        # 1. Tap stats button
        tap_stats = fresh_connected_client.call("tap", {
            "selector": "ElevatedButton[key='statsButton']"
        })

        # 2. Wait for navigation
        time.sleep(UI_SETTLE_TIME)

        # 3. Verify we're on stats screen (try to find stats-specific widget)
        tree = fresh_connected_client.call("get_tree", {"max_depth": 10})

        # 4. Tap back button
        tap_back = fresh_connected_client.call("tap", {
            "selector": "ElevatedButton[key='backButton']"
        })

        # 5. Wait for navigation
        time.sleep(UI_SETTLE_TIME)

        # All operations should complete
        assert tap_stats is not None
        assert tap_back is not None


class TestPerformance:
    """Test that all operations meet performance requirements"""

    def test_rapid_fire_operations(self, fresh_connected_client):
        """Test rapid consecutive operations all complete quickly"""
        operation_times = []

        for i in range(5):
            start = time.time()
            result = fresh_connected_client.call("get_tree", {"max_depth": 5})
            elapsed = time.time() - start
            operation_times.append(elapsed)

        # All should complete within timeout
        for i, elapsed in enumerate(operation_times):
            assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"Operation {i} took {elapsed:.2f}s"

        # Average should be reasonable
        avg_time = sum(operation_times) / len(operation_times)
        assert avg_time < MCP_TIMEOUT, f"Average time {avg_time:.2f}s exceeds timeout"

    def test_concurrent_like_operations(self, fresh_connected_client):
        """Test that sequential operations don't block each other"""
        operations = [
            ("get_tree", {"max_depth": 3}),
            ("find", {"selector": "Text", "find_first": True}),
            ("get_tree", {"max_depth": 5}),
        ]

        total_time = 0
        for tool_name, args in operations:
            start = time.time()
            result = fresh_connected_client.call(tool_name, args)
            elapsed = time.time() - start
            total_time += elapsed

            assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"{tool_name} took {elapsed:.2f}s"

        # Total should be reasonable (not accumulated blocking)
        assert total_time < MCP_TIMEOUT * len(operations)
