"""
Test MCP Protocol - Basic protocol operations
"""
import pytest
from conftest import MCP_TIMEOUT


class TestMCPProtocol:
    """Test basic MCP protocol functionality"""

    def test_initialize_completes_quickly(self, mcp_executable):
        """Initialize should complete in < 2 seconds"""
        import subprocess
        import json
        import time

        proc = subprocess.Popen(
            [mcp_executable],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            start = time.time()

            request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                    "capabilities": {}
                },
                "id": 1
            }

            proc.stdin.write(json.dumps(request) + '\n')
            proc.stdin.flush()

            response_line = proc.stdout.readline()
            elapsed = time.time() - start

            assert elapsed < MCP_TIMEOUT, f"Initialize took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"

            response = json.loads(response_line)
            assert 'result' in response, f"Expected result, got: {response}"
            assert response['result'].get('protocolVersion') == "2024-11-05"

        finally:
            proc.terminate()

    def test_list_tools_completes_quickly(self, mcp_client):
        """tools/list should complete in < 2 seconds"""
        import time

        start = time.time()
        tools = mcp_client.list_tools()
        elapsed = time.time() - start

        assert elapsed < MCP_TIMEOUT, f"tools/list took {elapsed:.2f}s, expected < {MCP_TIMEOUT}s"
        assert len(tools) > 0, "Expected at least one tool"

    def test_expected_tools_available(self, mcp_client):
        """Verify expected tools are available"""
        tools = mcp_client.list_tools()
        tool_names = [t['name'] for t in tools]

        expected_tools = ['connect', 'disconnect', 'get_tree', 'find', 'tap', 'type', 'get_properties', 'scroll']

        for tool in expected_tools:
            assert tool in tool_names, f"Expected tool '{tool}' not found. Available: {tool_names}"

    def test_invalid_tool_returns_error(self, mcp_client):
        """Calling an invalid tool should return an error"""
        result = mcp_client.call("nonexistent_tool", {})

        assert result is not None
        assert 'error' in result, f"Expected error for invalid tool, got: {result}"
