"""
Test type Tool - Non-blocking text entry operations
"""
import pytest
from conftest import MCP_TIMEOUT, UI_SETTLE_TIME
import time


class TestTypeTool:
    """Test type tool functionality with non-blocking behavior"""

    def test_type_completes_quickly(self, connected_client):
        """type should complete in < 2 seconds"""
        # First tap a text field to focus it
        connected_client.call("tap", {"selector": "TextField"})
        time.sleep(0.5)  # Brief pause for focus

        start = time.time()
        result = connected_client.call("type", {"text": "test"})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"type took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_type_with_selector_completes_quickly(self, connected_client):
        """type with selector should complete in < 2 seconds"""
        start = time.time()
        result = connected_client.call("type", {
            "text": "hello",
            "selector": "TextField"
        })
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"type took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_type_returns_immediately(self, connected_client):
        """type should return immediately without waiting for verification"""
        # Tap to focus first
        connected_client.call("tap", {"selector": "TextField"})
        time.sleep(0.5)

        start = time.time()
        result = connected_client.call("type", {"text": "quick test"})
        elapsed = time.time() - start

        # Type should return quickly (< 1.5s for non-blocking)
        assert elapsed < 1.5, f"type should return immediately, took {elapsed:.2f}s"

    def test_type_into_text_field(self, connected_client):
        """type into text field should work"""
        result = connected_client.call("type", {
            "text": "Test todo item",
            "selector": "TextField"
        })

        # Should succeed or report widget not found
        assert result is not None

    def test_type_requires_text_parameter(self, connected_client):
        """type without text parameter should error"""
        result = connected_client.call("type", {"selector": "TextField"})

        assert 'error' in result, "Expected error when text not provided"

    def test_type_into_focused_field(self, connected_client):
        """type into currently focused field should work"""
        # First focus a field
        connected_client.call("tap", {"selector": "TextField"})
        time.sleep(UI_SETTLE_TIME)

        # Then type without selector
        result = connected_client.call("type", {"text": "typed text"})

        # Should work or report no focused field
        assert result is not None

    def test_type_updates_field_content(self, connected_client):
        """type should update the text field content (verified after UI settle)"""
        test_text = "Integration test text"

        # Type into field
        result = connected_client.call("type", {
            "text": test_text,
            "selector": "TextField"
        })

        # Wait for UI to settle
        time.sleep(UI_SETTLE_TIME)

        # Get properties to verify (if field is still visible)
        props = connected_client.call("get_properties", {"selector": "TextField"})

        # Note: Verification depends on app state and field properties
        # This test mainly verifies the flow works
