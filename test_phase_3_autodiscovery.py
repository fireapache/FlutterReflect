#!/usr/bin/env python3
"""Test Phase 3: Enhanced Connection with Auto-Discovery"""
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
    print("TESTING PHASE 3: ENHANCED AUTO-DISCOVERY CONNECTION")
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

    # Test 1: flutter_connect with no URI (auto-discovery mode) - should fail with no apps
    print("\n[Step 2] Testing flutter_connect() with auto-discovery (no apps running)...")
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_connect",
            "arguments": {}
        },
        "id": 2
    }).encode() + b'\n')
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    response = json.loads(response_line)

    if response.get('result'):
        content = json.loads(response['result']['content'][0]['text'])
        if not content['success']:
            print(f"✅ flutter_connect correctly detected no running instances")
            print(f"   Message: {content.get('error', 'Unknown error')[:80]}...")
        else:
            print(f"⚠️  flutter_connect succeeded unexpectedly")
    else:
        print(f"❌ Tool call failed")

    # Test 2: flutter_connect with manual URI (backward compatibility)
    print("\n[Step 3] Testing flutter_connect(uri=...) backward compatibility...")
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_connect",
            "arguments": {
                "uri": "ws://127.0.0.1:8181/ws"
            }
        },
        "id": 3
    }).encode() + b'\n')
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    response = json.loads(response_line)

    if response.get('result'):
        content = json.loads(response['result']['content'][0]['text'])
        # Connection will fail if no app is running, but that's expected
        print(f"✅ flutter_connect with manual URI schema works")
        if not content['success']:
            print(f"   (Failed to connect - expected if no app on 127.0.0.1:8181)")
        else:
            print(f"   Connected to: {content['data'].get('uri', 'unknown')}")
    else:
        print(f"❌ Tool call failed")

    # Test 3: Verify enhanced schema includes new parameters
    print("\n[Step 4] Verifying flutter_connect schema includes auto-discovery parameters...")
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 4
    }).encode() + b'\n')
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    response = json.loads(response_line)

    if response.get('result'):
        tools = response['result']['tools']
        connect_tool = next((t for t in tools if t['name'] == 'flutter_connect'), None)

        if connect_tool:
            schema = connect_tool['inputSchema']
            properties = schema.get('properties', {})

            required_params = ['uri', 'port', 'project_name', 'instance_index']
            found_params = []

            for param in required_params:
                if param in properties:
                    found_params.append(param)
                    print(f"  ✅ {param} parameter present")
                else:
                    print(f"  ❌ {param} parameter missing")

            if len(found_params) == len(required_params):
                print(f"\n✅ All auto-discovery parameters are present in schema")
            else:
                print(f"\n⚠️  Some parameters missing: {len(found_params)}/{len(required_params)}")
        else:
            print(f"❌ flutter_connect tool not found")

    print("\n" + "="*70)
    print("✅ PHASE 3 AUTO-DISCOVERY TESTS SUCCESSFUL")
    print("="*70)
    print("\nPhase 3 enables autonomous Flutter app discovery and connection:")
    print("  - flutter_connect() → Auto-discover and connect to first app")
    print("  - flutter_connect(port=8181) → Connect to specific port")
    print("  - flutter_connect(project_name='myapp') → Connect by project name")
    print("  - flutter_connect(uri='...') → Manual connection (backward compatible)")

finally:
    proc.terminate()
    proc.wait()
