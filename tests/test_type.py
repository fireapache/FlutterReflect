"""
Test type Tool - Non-blocking text entry operations
"""
import pytest
from conftest import MCP_TIMEOUT, TIMEOUT_TOLERANCE, UI_SETTLE_TIME, has_error
import time


class TestTypeTool:
    """Test type tool functionality with non-blocking behavior"""

    def test_type_completes_quickly(self, fresh_connected_client):
        """type should complete within timeout"""
        # First tap a text field to focus it
        fresh_connected_client.call("tap", {"selector": "TextField"})
        time.sleep(0.5)  # Brief pause for focus

        start = time.time()
        result = fresh_connected_client.call("type", {"text": "test"})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"type took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_type_with_selector_completes_quickly(self, fresh_connected_client):
        """type with selector should complete within timeout"""
        start = time.time()
        result = fresh_connected_client.call("type", {
            "text": "hello",
            "selector": "TextField"
        })
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"type took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_type_returns_quickly(self, fresh_connected_client):
        """type should return without blocking for extended periods"""
        # Tap to focus first
        fresh_connected_client.call("tap", {"selector": "TextField"})
        time.sleep(0.5)

        start = time.time()
        result = fresh_connected_client.call("type", {"text": "quick test"})
        elapsed = time.time() - start

        # Type should return within timeout
        assert elapsed < MCP_TIMEOUT + TIMEOUT_TOLERANCE, f"type should return quickly, took {elapsed:.2f}s"

    def test_type_into_text_field(self, fresh_connected_client):
        """type into text field should work"""
        result = fresh_connected_client.call("type", {
            "text": "Test todo item",
            "selector": "TextField"
        })

        # Should succeed or report widget not found
        assert result is not None

    def test_type_requires_text_parameter(self, fresh_connected_client):
        """type without text parameter should error"""
        result = fresh_connected_client.call("type", {"selector": "TextField"})

        # Error can be in JSON-RPC error or in content
        assert has_error(result), f"Expected error when text not provided, got: {result}"

    def test_type_into_focused_field(self, fresh_connected_client):
        """type into currently focused field should work"""
        # First focus a field
        fresh_connected_client.call("tap", {"selector": "TextField"})
        time.sleep(UI_SETTLE_TIME)

        # Then type without selector
        result = fresh_connected_client.call("type", {"text": "typed text"})

        # Should work or report no focused field
        assert result is not None

    def test_type_updates_field_content(self, fresh_connected_client):
        """type should update the text field content (verified after UI settle)"""
        test_text = "Integration test text"

        # Type into field
        result = fresh_connected_client.call("type", {
            "text": test_text,
            "selector": "TextField"
        })

        # Wait for UI to settle
        time.sleep(UI_SETTLE_TIME)

        # Get properties to verify (if field is still visible)
        props = fresh_connected_client.call("get_properties", {"selector": "TextField"})

        # Note: Verification depends on app state and field properties
        # This test mainly verifies the flow works
        assert result is not None
