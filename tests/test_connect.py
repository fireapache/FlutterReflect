"""
Test Connect/Disconnect Tools

Note: test_disconnect_when_not_connected runs FIRST before any app spawning.
"""
import pytest
from conftest import MCP_TIMEOUT, FLUTTER_APP_URI, UI_SETTLE_TIME
import time


class TestDisconnectWithoutApp:
    """Tests that don't require Flutter app - run first"""

    def test_disconnect_when_not_connected(self, mcp_client):
        """Disconnect when not connected should handle gracefully (runs before app spawn)"""
        result = mcp_client.call("disconnect", {})

        # Should not error, just return gracefully
        assert result is not None
        # Either success or a message that we weren't connected
        assert 'error' not in result or 'not connected' in str(result.get('error', '')).lower()


class TestConnectTool:
    """Test connect tool functionality (requires Flutter app)"""

    def test_connect_completes_quickly(self, mcp_client, flutter_app_running):
        """Connect should complete in < 2 seconds"""
        start = time.time()
        result = mcp_client.call("connect", {"uri": FLUTTER_APP_URI})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + 0.1, f"Connect took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"
        assert 'error' not in result, f"Connect failed: {result.get('error')}"

        # Cleanup
        mcp_client.call("disconnect", {})

    def test_connect_returns_success(self, mcp_client, flutter_app_running):
        """Connect should return success result"""
        result = mcp_client.call("connect", {"uri": FLUTTER_APP_URI})

        assert result is not None
        assert 'result' in result, f"Expected result, got: {result}"

        # Cleanup
        mcp_client.call("disconnect", {})

    def test_connect_with_invalid_uri_fails(self, fresh_mcp_client):
        """Connect with invalid URI should fail quickly (uses fresh client to avoid corrupting session state)"""
        start = time.time()
        result = fresh_mcp_client.call("connect", {"uri": "ws://127.0.0.1:9999/invalid"}, timeout=6.0)
        elapsed = time.time() - start

        # Should fail within reasonable time (connection timeout + overhead)
        assert elapsed < 6.0, f"Invalid connect took too long: {elapsed:.2f}s"
        # MCP returns success with error in content, or JSON-RPC error
        if 'error' in result:
            pass  # JSON-RPC error
        elif 'result' in result:
            # Check content for error indication
            content = result['result'].get('content', [])
            content_text = content[0].get('text', '') if content else ''
            assert 'error' in content_text.lower() or 'failed' in content_text.lower(), \
                f"Expected error in content for invalid URI, got: {content_text}"


class TestDisconnectTool:
    """Test disconnect tool functionality (requires Flutter app)"""

    def test_disconnect_completes_quickly(self, fresh_connected_client):
        """Disconnect should complete in < 2 seconds (uses fresh client to avoid session state issues)"""
        start = time.time()
        result = fresh_connected_client.call("disconnect", {})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT + 0.1, f"Disconnect took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"
