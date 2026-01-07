#!/usr/bin/env python3
"""
Realistic GUI Test Suite for FlutterReflect MCP Server
Tests realistic user workflows and scenarios
"""
import subprocess
import json
import sys
import io
from datetime import datetime

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def send_request(proc, request):
    """Send a JSON-RPC request and get response"""
    request_str = json.dumps(request) + '\n'
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline().decode().strip()
    if response_line:
        response = json.loads(response_line)
        return response
    return None


class TestRunner:
    def __init__(self):
        self.executable = r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe"
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }
        self.start_time = datetime.now()
        self.proc = None

    def initialize_mcp(self):
        """Initialize MCP connection"""
        try:
            self.proc = subprocess.Popen(
                [self.executable],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test_realistic_gui_suite", "version": "1.0"},
                    "capabilities": {}
                },
                "id": 1
            }

            response = send_request(self.proc, init_request)

            if response and response.get('result', {}).get('capabilities'):
                print("✅ MCP initialization successful")
                return True
            else:
                print("❌ MCP initialization failed")
                return False

        except Exception as e:
            print(f"❌ Failed to initialize MCP: {e}")
            return False

    def list_tools(self):
        """List available MCP tools"""
        try:
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }

            response = send_request(self.proc, tools_request)

            if response and 'result' in response:
                tools = response['result'].get('tools', [])
                tool_names = [t['name'] for t in tools]
                print(f"✅ Available tools: {tool_names}")
                return tools
            else:
                print("❌ Failed to list tools")
                return None

        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return None

    def connect_flutter_app(self, uri="ws://127.0.0.1:8181/ws"):
        """Connect to Flutter app via VM Service"""
        try:
            connect_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_connect",
                    "arguments": {
                        "uri": uri
                    }
                },
                "id": 3
            }

            response = send_request(self.proc, connect_request)

            if response and response.get('result'):
                print(f"✅ Connected to Flutter app ({uri})")
                return True
            else:
                error = response.get('error', {}) if response else {}
                print(f"❌ Failed to connect to Flutter app: {error.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error connecting to Flutter app: {e}")
            return False

    def verify_connection(self):
        """Verify connection by getting initial widget tree"""
        try:
            tree_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_get_tree",
                    "arguments": {
                        "max_depth": 3,
                        "format": "json"
                    }
                },
                "id": 4
            }

            response = send_request(self.proc, tree_request)

            if response and response.get('result'):
                result = response['result']
                if 'content' in result and len(result['content']) > 0:
                    content = result['content'][0]
                    if 'text' in content:
                        tree_data = json.loads(content['text'])

                        if tree_data.get('success'):
                            widget_tree = tree_data['data'].get('widget_tree', {})
                            node_count = widget_tree.get('node_count', 0)
                            print(f"✅ Connection verified - Widget tree captured ({node_count} nodes)")
                            return tree_data
                        else:
                            print(f"❌ Failed to get widget tree: {tree_data.get('error', 'Unknown error')}")
                            return None
            else:
                error = response.get('error', {}) if response else {}
                print(f"❌ Connection verification failed: {error.get('message', 'Unknown error')}")
                return None

        except Exception as e:
            print(f"❌ Error verifying connection: {e}")
            return None

    def disconnect_flutter_app(self):
        """Disconnect from Flutter app"""
        try:
            disconnect_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_disconnect",
                    "arguments": {}
                },
                "id": 5
            }

            response = send_request(self.proc, disconnect_request)

            if response:
                print("✅ Disconnected from Flutter app")
                return True
            else:
                print("⚠️  Disconnect response empty")
                return False

        except Exception as e:
            print(f"⚠️  Error during disconnect: {e}")
            return False

    def test_app_initialization(self):
        """Test app initialization sequence"""
        print("\n" + "="*80)
        print("TEST: App Initialization")
        print("="*80)

        # Step 1: MCP initialization (already done in main)
        print("\n📋 Step 1: MCP Initialization")
        print("   Status: ✅ Already initialized")

        # Step 2: List tools
        print("\n📋 Step 2: List Available Tools")
        tools = self.list_tools()
        if tools is None:
            self.results['failed'].append('test_app_initialization - list_tools')
            return False
        print(f"   Found {len(tools)} tools")

        # Step 3: Connect to Flutter app
        print("\n📋 Step 3: Connect to Flutter App")
        print("   Target: ws://127.0.0.1:8181/ws")
        print("   Make sure Flutter app is running:")
        print("   cd examples/flutter_sample_app")
        print("   flutter run -d windows --vm-service-port=8181 --disable-service-auth-codes")

        if not self.connect_flutter_app():
            self.results['failed'].append('test_app_initialization - connect')
            return False

        # Step 4: Verify connection
        print("\n📋 Step 4: Verify Connection")
        tree_data = self.verify_connection()
        if tree_data is None:
            self.results['failed'].append('test_app_initialization - verify_connection')
            self.disconnect_flutter_app()
            return False

        # Test passed
        self.results['passed'].append('test_app_initialization')
        print("\n✅ App initialization test PASSED")
        print("="*80)
        return True

    def cleanup(self):
        """Clean up resources"""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait()
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")

    def print_report(self):
        """Print final test report"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print("\n\n" + "="*80)
        print("REALISTIC GUI TEST REPORT")
        print("="*80)

        print(f"\nTest Suite: Realistic GUI Workflows")
        print(f"Executable: flutter_reflect.exe")
        print(f"Timestamp: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {elapsed:.2f} seconds")

        print(f"\n{'='*80}")
        print("RESULTS SUMMARY")
        print(f"{'='*80}")

        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        skipped = len(self.results['skipped'])
        total = passed + failed + skipped

        print(f"\n✅ Passed:  {passed}")
        print(f"❌ Failed:  {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"📊 Total:   {total}")

        if failed == 0:
            print(f"\n🎉 ALL TESTS PASSED!")
            success_rate = 100
        else:
            success_rate = (passed / total * 100) if total > 0 else 0

        print(f"📈 Success Rate: {success_rate:.1f}%")

        if failed > 0:
            print(f"\n{'='*80}")
            print("FAILED TESTS")
            print(f"{'='*80}")
            for test in self.results['failed']:
                print(f"  ❌ {test}")

        if skipped > 0:
            print(f"\n{'='*80}")
            print("SKIPPED TESTS")
            print(f"{'='*80}")
            for test in self.results['skipped']:
                print(f"  ⏭️  {test}")

        print(f"\n{'='*80}")


def main():
    runner = TestRunner()

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "FlutterReflect MCP Server - Realistic GUI Test Suite".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")

    # Initialize MCP connection
    if not runner.initialize_mcp():
        print("\n❌ Failed to initialize MCP server. Exiting.")
        return

    try:
        # Run app initialization test
        if runner.test_app_initialization():
            # Disconnect after successful test
            runner.disconnect_flutter_app()

        # Print final report
        runner.print_report()

    except Exception as e:
        print(f"\n❌ Error during test execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner.cleanup()


if __name__ == "__main__":
    main()
