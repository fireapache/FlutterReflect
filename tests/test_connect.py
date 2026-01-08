"""
Test Connect/Disconnect Tools
"""
import pytest
from conftest import MCP_TIMEOUT, FLUTTER_APP_URI, UI_SETTLE_TIME
import time


class TestConnectTool:
    """Test connect tool functionality"""

    def test_connect_completes_quickly(self, mcp_client, flutter_app_running):
        """Connect should complete in < 2 seconds"""
        start = time.time()
        result = mcp_client.call("connect", {"uri": FLUTTER_APP_URI})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"Connect took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"
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

    def test_connect_with_invalid_uri_fails(self, mcp_client):
        """Connect with invalid URI should fail quickly"""
        start = time.time()
        result = mcp_client.call("connect", {"uri": "ws://127.0.0.1:9999/invalid"}, timeout=5.0)
        elapsed = time.time() - start

        # Should fail, not timeout
        assert elapsed < 5.0, f"Invalid connect took too long: {elapsed:.2f}s"
        assert 'error' in result, "Expected error for invalid URI"


class TestDisconnectTool:
    """Test disconnect tool functionality"""

    def test_disconnect_completes_quickly(self, connected_client):
        """Disconnect should complete in < 2 seconds"""
        start = time.time()
        result = connected_client.call("disconnect", {})
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"Disconnect took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

    def test_disconnect_when_not_connected(self, mcp_client):
        """Disconnect when not connected should handle gracefully"""
        result = mcp_client.call("disconnect", {})

        # Should not error, just return
        assert result is not None
