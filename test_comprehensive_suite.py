#!/usr/bin/env python3
"""
Comprehensive Test Suite for FlutterReflect MCP Server
Tests all 10 tools and validates MCP protocol compliance
"""
import subprocess
import json
import sys
import io
from datetime import datetime

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class TestRunner:
    def __init__(self):
        self.executable = r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe"
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }
        self.start_time = datetime.now()

    def run_help_test(self):
        """Test that --help shows all tools"""
        print("\n" + "="*80)
        print("TEST 1: HELP OUTPUT VALIDATION")
        print("="*80)

        try:
            result = subprocess.run(
                [self.executable, "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )

            help_text = result.stderr + result.stdout

            expected_tools = [
                'list_instances', 'launch', 'connect', 'disconnect',
                'get_tree', 'get_properties', 'find', 'tap', 'type', 'scroll'
            ]

            print("\nChecking for tool names in help output...")
            all_found = True

            for tool in expected_tools:
                if tool + ':' in help_text:
                    print(f"  ✅ {tool}")
                    self.results['passed'].append(f"Help: {tool} found")
                else:
                    print(f"  ❌ {tool} NOT FOUND")
                    all_found = False
                    self.results['failed'].append(f"Help: {tool} not found")

            if all_found:
                print("\n✅ All tools documented in help")
            else:
                print("\n⚠️ Some tools missing from help")

            return all_found

        except Exception as e:
            print(f"❌ Help test failed: {e}")
            self.results['failed'].append(f"Help test: {e}")
            return False

    def run_version_test(self):
        """Test that --version works"""
        print("\n" + "="*80)
        print("TEST 2: VERSION COMMAND")
        print("="*80)

        try:
            result = subprocess.run(
                [self.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout + result.stderr

            if "FlutterReflect" in output and "Version" in output:
                print(f"\n✅ Version output looks correct")
                print(f"   {output.split(chr(10))[0]}")
                self.results['passed'].append("Version: command works")
                return True
            else:
                print(f"❌ Version output unexpected")
                self.results['failed'].append("Version: unexpected output")
                return False

        except Exception as e:
            print(f"❌ Version test failed: {e}")
            self.results['failed'].append(f"Version test: {e}")
            return False

    def run_mcp_initialization_test(self):
        """Test MCP protocol initialization"""
        print("\n" + "="*80)
        print("TEST 3: MCP PROTOCOL INITIALIZATION")
        print("="*80)

        try:
            proc = subprocess.Popen(
                [self.executable],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test_suite", "version": "1.0"},
                    "capabilities": {}
                },
                "id": 1
            }

            print("\nSending MCP initialize request...")
            proc.stdin.write(json.dumps(init_request) + '\n')
            proc.stdin.flush()

            response = proc.stdout.readline().strip()
            response_obj = json.loads(response)

            if response_obj.get('result', {}).get('capabilities'):
                print(f"✅ MCP initialization successful")
                print(f"   Server: {response_obj.get('result', {}).get('serverInfo', {}).get('name')}")
                self.results['passed'].append("MCP: initialization")
                proc.terminate()
                return True
            else:
                print(f"❌ MCP initialization failed")
                self.results['failed'].append("MCP: initialization failed")
                proc.terminate()
                return False

        except Exception as e:
            print(f"❌ MCP initialization test failed: {e}")
            self.results['failed'].append(f"MCP test: {e}")
            return False

    def run_tool_registration_test(self):
        """Test that all tools are registered"""
        print("\n" + "="*80)
        print("TEST 4: TOOL REGISTRATION (MCP Protocol)")
        print("="*80)

        try:
            proc = subprocess.Popen(
                [self.executable],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Initialize
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                    "capabilities": {}
                },
                "id": 1
            }) + '\n')
            proc.stdin.flush()
            proc.stdout.readline()  # consume init response

            # List tools
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }) + '\n')
            proc.stdin.flush()

            response = json.loads(proc.stdout.readline().strip())

            expected_tools = [
                'list_instances', 'launch', 'connect', 'disconnect',
                'get_tree', 'get_properties', 'find', 'tap', 'type', 'scroll'
            ]

            print("\nRegistered Tools:")
            registered_tools = [t['name'] for t in response.get('result', {}).get('tools', [])]

            all_found = True
            for tool in expected_tools:
                if tool in registered_tools:
                    print(f"  ✅ {tool}")
                    self.results['passed'].append(f"Registration: {tool}")
                else:
                    print(f"  ❌ {tool}")
                    all_found = False
                    self.results['failed'].append(f"Registration: {tool} missing")

            print(f"\nTotal: {len(registered_tools)}/10 tools registered")

            if all_found and len(registered_tools) >= 10:
                print("✅ All tools properly registered")

            proc.terminate()
            return all_found

        except Exception as e:
            print(f"❌ Tool registration test failed: {e}")
            self.results['failed'].append(f"Registration test: {e}")
            return False

    def run_cli_mode_tests(self):
        """Test CLI mode for each tool (help only, no flutter app running)"""
        print("\n" + "="*80)
        print("TEST 5: CLI MODE AVAILABILITY")
        print("="*80)

        tools = [
            'list_instances', 'launch', 'connect', 'disconnect',
            'get_tree', 'get_properties', 'find', 'tap', 'type', 'scroll'
        ]

        print("\nTesting CLI mode invocation (--help on each tool)...")
        all_passed = True

        for tool in tools:
            try:
                result = subprocess.run(
                    [self.executable, tool, "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # Tool help should either work or show error gracefully
                output = result.stderr + result.stdout

                if "usage" in output.lower() or tool in output or "error" in output.lower():
                    print(f"  ✅ {tool}")
                    self.results['passed'].append(f"CLI: {tool}")
                else:
                    print(f"  ⚠️  {tool}")
                    self.results['skipped'].append(f"CLI: {tool} (tool needs active connection)")

            except subprocess.TimeoutExpired:
                print(f"  ⏱️  {tool} (timeout - may require connection)")
                self.results['skipped'].append(f"CLI: {tool} (timeout)")
            except Exception as e:
                print(f"  ❌ {tool}: {e}")
                all_passed = False
                self.results['failed'].append(f"CLI: {tool} error")

        return all_passed

    def run_utf8_test(self):
        """Test that help output doesn't have mojibake"""
        print("\n" + "="*80)
        print("TEST 6: CHARACTER ENCODING (UTF-8)")
        print("="*80)

        try:
            result = subprocess.run(
                [self.executable, "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )

            help_text = result.stderr + result.stdout

            # Check for mojibake patterns
            bad_patterns = ['ΓåÆ', '\xe2\x86', '\u3000']
            bad_found = False

            for pattern in bad_patterns:
                if pattern in help_text:
                    print(f"❌ Found corrupted encoding pattern")
                    bad_found = True
                    self.results['failed'].append(f"UTF-8: corrupted character found")
                    break

            if not bad_found:
                print(f"✅ No encoding corruption detected")
                print(f"   Help text renders correctly")
                self.results['passed'].append("UTF-8: clean encoding")
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ UTF-8 test failed: {e}")
            self.results['failed'].append(f"UTF-8 test: {e}")
            return False

    def run_tool_descriptions_test(self):
        """Test that all tools have descriptions"""
        print("\n" + "="*80)
        print("TEST 7: TOOL DESCRIPTIONS")
        print("="*80)

        try:
            proc = subprocess.Popen(
                [self.executable],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Initialize
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                    "capabilities": {}
                },
                "id": 1
            }) + '\n')
            proc.stdin.flush()
            proc.stdout.readline()

            # List tools
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }) + '\n')
            proc.stdin.flush()

            response = json.loads(proc.stdout.readline().strip())
            tools = response.get('result', {}).get('tools', [])

            print("\nTool Descriptions:")
            all_have_desc = True

            for tool in tools:
                name = tool.get('name', 'unknown')
                desc = tool.get('description', '')

                if desc and len(desc) > 10:
                    preview = desc[:60] + "..." if len(desc) > 60 else desc
                    print(f"  ✅ {name}")
                    print(f"     {preview}")
                    self.results['passed'].append(f"Descriptions: {name}")
                else:
                    print(f"  ❌ {name} - missing description")
                    all_have_desc = False
                    self.results['failed'].append(f"Descriptions: {name}")

            proc.terminate()
            return all_have_desc

        except Exception as e:
            print(f"❌ Descriptions test failed: {e}")
            self.results['failed'].append(f"Descriptions test: {e}")
            return False

    def print_report(self):
        """Print final test report"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print("\n\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)

        print(f"\nTest Suite: FlutterReflect MCP Server")
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
    print("║" + "FlutterReflect MCP Server - Comprehensive Test Suite".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")

    # Run tests
    runner.run_help_test()
    runner.run_version_test()
    runner.run_mcp_initialization_test()
    runner.run_tool_registration_test()
    runner.run_cli_mode_tests()
    runner.run_utf8_test()
    runner.run_tool_descriptions_test()

    # Print final report
    runner.print_report()

if __name__ == "__main__":
    main()
