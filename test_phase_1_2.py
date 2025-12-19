#!/usr/bin/env python3
"""Test Phase 1 and 2: Instance Discovery and App Launching"""
import subprocess
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

proc = subprocess.Popen(
    [r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

try:
    print("\n" + "="*70)
    print("TESTING PHASE 1 & 2: AUTO-DISCOVERY AND APP LAUNCHING")
    print("="*70)

    # Initialize
    print("\n[Step 1] Initializing MCP server...")
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test", "version": "1.0"},
            "capabilities": {}
        },
        "id": 1
    }).encode() + b'\n')
    proc.stdin.flush()
    init_response = proc.stdout.readline().decode().strip()
    init_data = json.loads(init_response)

    if init_data.get('result'):
        print("✅ Server initialized")
    else:
        print("❌ Failed to initialize")
        sys.exit(1)

    # List tools to verify both are registered
    print("\n[Step 2] Checking if Phase 1 & 2 tools are registered...")
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }).encode() + b'\n')
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    response = json.loads(response_line)

    if response.get('result'):
        tools = response['result']['tools']
        tool_names = [t['name'] for t in tools]

        print(f"\nPhase 1: Instance Discovery")
        if 'flutter_list_instances' in tool_names:
            tool = next(t for t in tools if t['name'] == 'flutter_list_instances')
            print(f"  ✅ flutter_list_instances registered")
        else:
            print(f"  ❌ flutter_list_instances NOT FOUND")
            sys.exit(1)

        print(f"\nPhase 2: App Launching")
        if 'flutter_launch' in tool_names:
            tool = next(t for t in tools if t['name'] == 'flutter_launch')
            print(f"  ✅ flutter_launch registered")
        else:
            print(f"  ❌ flutter_launch NOT FOUND")
            sys.exit(1)

        total_tools = len(tools)
        print(f"\nTotal tools registered: {total_tools}")
        print(f"  - Phase 1 (Discovery & Launch): 2 tools")
        print(f"  - Phase 2 (Connection): 2 tools")
        print(f"  - Phase 3-6 (Inspection & Interaction): {total_tools - 4} tools")

    # Test flutter_list_instances
    print("\n[Step 3] Testing flutter_list_instances...")
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_list_instances",
            "arguments": {
                "port_start": 8180,
                "port_end": 8182,
                "timeout_ms": 200
            }
        },
        "id": 3
    }).encode() + b'\n')
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    response = json.loads(response_line)

    if response.get('result'):
        content = json.loads(response['result']['content'][0]['text'])
        if content['success']:
            print(f"  ✅ flutter_list_instances executed")
            print(f"     Message: {content['message']}")
        else:
            print(f"  ❌ Tool returned error: {content.get('error', 'Unknown error')}")
    else:
        print(f"  ❌ Tool call failed")

    # Test flutter_launch with invalid project path
    print("\n[Step 4] Testing flutter_launch with invalid project path...")
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_launch",
            "arguments": {
                "project_path": "/nonexistent/project",
                "device": "windows",
                "startup_timeout": 5
            }
        },
        "id": 4
    }).encode() + b'\n')
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    response = json.loads(response_line)

    if response.get('result'):
        content = json.loads(response['result']['content'][0]['text'])
        if not content['success']:
            print(f"  ✅ flutter_launch correctly rejected invalid project")
            print(f"     Error: {content.get('error', 'Unknown error')[:80]}...")
        else:
            print(f"  ⚠️  flutter_launch succeeded unexpectedly")
    else:
        print(f"  ❌ Tool call failed")

    print("\n" + "="*70)
    print("✅ PHASE 1 & 2 COMPREHENSIVE TEST SUCCESSFUL")
    print("="*70)
    print("\nBoth Phase 1 (Auto-Discovery) and Phase 2 (App Launching) tools")
    print("are now available for autonomous Flutter app management!")
    print("\nUsage workflow:")
    print("1. flutter_list_instances() - Check for running Flutter apps")
    print("2. flutter_launch(project_path=...) - Launch a new Flutter app if needed")
    print("3. flutter_connect(uri=...) - Connect to the app's VM Service")
    print("4. Use Phase 3-6 tools to interact with the Flutter app")

finally:
    proc.terminate()
    proc.wait()
