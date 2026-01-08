"""
FlutterReflect MCP Server - Test Fixtures

Provides pytest fixtures for testing MCP tools with non-blocking operations.
All tool calls should complete in < 2 seconds.
"""
import pytest
import subprocess
import json
import os
import sys
import threading
import queue
import time
import socket

# Configuration
MCP_TIMEOUT = 2.0  # seconds - max time for any tool call
UI_SETTLE_TIME = 1.0  # seconds - wait after UI interaction before checking state
FLUTTER_APP_PORT = 8181
FLUTTER_APP_URI = f"ws://127.0.0.1:{FLUTTER_APP_PORT}/ws"


def find_executable():
    """Find flutter_reflect.exe in common locations"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locations = [
        os.path.join(base_dir, 'build', 'Debug', 'flutter_reflect.exe'),
        os.path.join(base_dir, 'build', 'Release', 'flutter_reflect.exe'),
        os.environ.get('FLUTTER_REFLECT_EXE', ''),
    ]
    for loc in locations:
        if loc and os.path.exists(loc):
            return loc
    return None


def is_flutter_app_running(port=FLUTTER_APP_PORT):
    """Check if Flutter app is running on the specified port"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        return result == 0
    except Exception:
        return False
    finally:
        sock.close()


class MCPClient:
    """MCP client wrapper with timeout support"""

    def __init__(self, proc):
        self.proc = proc
        self.request_id = 0
        self._initialized = False

    def _send_receive(self, request, timeout=MCP_TIMEOUT):
        """Send request and receive response with timeout"""
        def read_response(proc, q):
            try:
                line = proc.stdout.readline()
                if line:
                    q.put(json.loads(line.strip()))
                else:
                    q.put(None)
            except Exception as e:
                q.put({'error': str(e)})

        # Send request
        req_json = json.dumps(request) + '\n'
        self.proc.stdin.write(req_json)
        self.proc.stdin.flush()

        # Read response with timeout
        q = queue.Queue()
        thread = threading.Thread(target=read_response, args=(self.proc, q))
        thread.daemon = True
        thread.start()

        try:
            response = q.get(timeout=timeout)
            return response
        except queue.Empty:
            return {'error': {'code': -1, 'message': f'Timeout after {timeout}s'}}

    def initialize(self):
        """Initialize MCP connection"""
        if self._initialized:
            return True

        self.request_id += 1
        response = self._send_receive({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "pytest", "version": "1.0"},
                "capabilities": {}
            },
            "id": self.request_id
        }, timeout=5.0)

        if response and 'result' in response:
            self._initialized = True
            return True
        return False

    def call(self, tool_name, arguments=None, timeout=MCP_TIMEOUT):
        """Call an MCP tool and return the result"""
        if arguments is None:
            arguments = {}

        self.request_id += 1
        start_time = time.time()

        response = self._send_receive({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self.request_id
        }, timeout=timeout)

        elapsed = time.time() - start_time

        # Add timing info to response
        if response:
            response['_elapsed'] = elapsed
            response['_tool'] = tool_name

        return response

    def list_tools(self):
        """List available MCP tools"""
        self.request_id += 1
        response = self._send_receive({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self.request_id
        })

        if response and 'result' in response:
            return response['result'].get('tools', [])
        return []


@pytest.fixture(scope="session")
def mcp_executable():
    """Find and return the MCP executable path"""
    exe = find_executable()
    if not exe:
        pytest.skip("flutter_reflect.exe not found. Build the project first.")
    return exe


@pytest.fixture(scope="session")
def mcp_server(mcp_executable):
    """Start MCP server process for the test session"""
    proc = subprocess.Popen(
        [mcp_executable],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    yield proc

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def mcp_client(mcp_server):
    """Create and initialize MCP client"""
    client = MCPClient(mcp_server)
    if not client.initialize():
        pytest.fail("Failed to initialize MCP client")
    return client


@pytest.fixture
def flutter_app_running():
    """Check if Flutter app is running, skip test if not"""
    if not is_flutter_app_running():
        pytest.skip(
            f"Flutter app not running on port {FLUTTER_APP_PORT}. "
            f"Start with: flutter run -d windows --vm-service-port={FLUTTER_APP_PORT} --disable-service-auth-codes"
        )
    return True


@pytest.fixture
def connected_client(mcp_client, flutter_app_running):
    """Return an MCP client that's connected to the Flutter app"""
    # Connect to Flutter app
    result = mcp_client.call("connect", {"uri": FLUTTER_APP_URI}, timeout=5.0)

    if not result or 'error' in result:
        error_msg = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
        pytest.fail(f"Failed to connect to Flutter app: {error_msg}")

    yield mcp_client

    # Disconnect after test
    mcp_client.call("disconnect", {})


def find_widget(tree_result, widget_type=None, key=None, text=None):
    """Helper to find a widget in the tree result"""
    if not tree_result or 'result' not in tree_result:
        return None

    content = tree_result['result'].get('content', [])
    if not content:
        return None

    # Parse the tree data
    tree_text = content[0].get('text', '') if content else ''
    try:
        tree_data = json.loads(tree_text) if tree_text.startswith('{') else {}
    except json.JSONDecodeError:
        return None

    widgets = tree_data.get('widgets', [])

    for widget in widgets:
        if widget_type and widget.get('type') != widget_type:
            continue
        if key and widget.get('properties', {}).get('key') != key:
            continue
        if text and widget.get('text') != text:
            continue
        return widget

    return None
