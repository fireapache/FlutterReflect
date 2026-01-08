"""
FlutterReflect MCP Server - Test Fixtures

Provides pytest fixtures for testing MCP tools with non-blocking operations.
All tool calls should complete in < 2 seconds.

Auto-spawns Flutter sample app if not running.
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
import signal

# Configuration
MCP_TIMEOUT = 2.0  # seconds - max time for any tool call
UI_SETTLE_TIME = 1.0  # seconds - wait after UI interaction before checking state
FLUTTER_APP_PORT = 8181
FLUTTER_APP_URI = f"ws://127.0.0.1:{FLUTTER_APP_PORT}/ws"
FLUTTER_APP_STARTUP_TIMEOUT = 90  # seconds to wait for app to start


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


def find_flutter_sample_app():
    """Find the Flutter sample app directory"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sample_app = os.path.join(base_dir, 'examples', 'flutter_sample_app')
    if os.path.exists(sample_app):
        return sample_app
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


class FlutterAppManager:
    """Manages Flutter app lifecycle for testing"""

    def __init__(self, project_path, port=FLUTTER_APP_PORT):
        self.project_path = project_path
        self.port = port
        self.process = None
        self._spawned = False

    def is_running(self):
        """Check if app is running"""
        return is_flutter_app_running(self.port)

    def spawn(self, timeout=FLUTTER_APP_STARTUP_TIMEOUT):
        """Spawn Flutter app if not already running"""
        if self.is_running():
            print(f"\n  Flutter app already running on port {self.port}")
            return True

        print(f"\n  Spawning Flutter app from: {self.project_path}")
        print(f"  Target port: {self.port}")

        cmd = f'flutter run -d windows --vm-service-port={self.port} --disable-service-auth-codes'

        try:
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

            self.process = subprocess.Popen(
                cmd,
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                creationflags=creation_flags
            )

            print(f"  Flutter process started (PID: {self.process.pid})")
            self._spawned = True

            # Wait for app to be ready
            return self._wait_for_ready(timeout)

        except Exception as e:
            print(f"  ERROR: Failed to spawn Flutter app: {e}")
            return False

    def _wait_for_ready(self, timeout):
        """Wait for app to be ready"""
        print(f"  Waiting for VM Service to be ready...")
        start = time.time()

        while time.time() - start < timeout:
            elapsed = int(time.time() - start)

            # Check if process died
            if self.process and self.process.poll() is not None:
                print(f"  ERROR: Flutter process exited with code {self.process.returncode}")
                return False

            # Check if port is open
            if self.is_running():
                time.sleep(2)  # Give it a moment to fully initialize
                if self.is_running():
                    print(f"  Flutter app ready on port {self.port} (took {elapsed}s)")
                    return True

            time.sleep(1)

        print(f"  ERROR: Timeout waiting for Flutter app to start")
        return False

    def terminate(self):
        """Terminate spawned Flutter app"""
        if not self._spawned or not self.process:
            return

        print(f"\n  Terminating Flutter app (PID: {self.process.pid})...")

        try:
            if sys.platform == 'win32':
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.process.terminate()

            self.process.wait(timeout=10)
            print("  Flutter app terminated")
        except subprocess.TimeoutExpired:
            print("  Force killing Flutter app...")
            self.process.kill()
        except Exception as e:
            print(f"  Error terminating Flutter app: {e}")


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


# Global Flutter app manager (created once per session)
_flutter_app_manager = None


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


@pytest.fixture(scope="session")
def flutter_app_manager():
    """Session-scoped Flutter app manager that auto-spawns app if needed"""
    global _flutter_app_manager

    sample_app_path = find_flutter_sample_app()
    if not sample_app_path:
        pytest.skip("Flutter sample app not found in examples/flutter_sample_app")

    _flutter_app_manager = FlutterAppManager(sample_app_path)

    yield _flutter_app_manager

    # Cleanup - terminate if we spawned it
    _flutter_app_manager.terminate()


@pytest.fixture
def flutter_app_running(flutter_app_manager):
    """Ensure Flutter app is running (auto-spawn if needed)"""
    if not flutter_app_manager.is_running():
        if not flutter_app_manager.spawn():
            pytest.fail(
                f"Failed to start Flutter app. "
                f"Manual start: cd examples/flutter_sample_app && "
                f"flutter run -d windows --vm-service-port={FLUTTER_APP_PORT} --disable-service-auth-codes"
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
