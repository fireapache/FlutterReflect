#!/usr/bin/env python3
"""Test flutter_list_instances tool"""
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
    print("TESTING PHASE 1: INSTANCE DISCOVERY")
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

    # List tools to verify flutter_list_instances is there
    print("\n[Step 2] Checking if flutter_list_instances is registered...")
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

        if 'flutter_list_instances' in tool_names:
            tool = next(t for t in tools if t['name'] == 'flutter_list_instances')
            print(f"✅ flutter_list_instances is registered")
            print(f"   Description: {tool['description'][:80]}...")
        else:
            print(f"❌ flutter_list_instances NOT FOUND")
            print(f"   Available tools: {', '.join(tool_names)}")
            sys.exit(1)

    # Test calling flutter_list_instances
    print("\n[Step 3] Calling flutter_list_instances with narrow port range...")
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_list_instances",
            "arguments": {
                "port_start": 8180,
                "port_end": 8182,
                "timeout_ms": 300
            }
        },
        "id": 3
    }).encode() + b'\n')
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    response = json.loads(response_line)

    if response.get('result'):
        content = json.loads(response['result']['content'][0]['text'])
        print(f"✅ Tool executed successfully")
        print(f"   Response: {content['message']}")
        print(f"   Instances found: {content['data']['count']}")

        if content['data']['count'] == 0:
            print(f"   (No running Flutter instances found - this is expected if none are running)")
        else:
            print(f"   Instances:")
            for inst in content['data']['instances']:
                print(f"     - {inst['project_name']} on port {inst['port']}")
    else:
        error = response.get('error', response)
        print(f"❌ Tool call failed: {error}")
        sys.exit(1)

    print("\n" + "="*70)
    print("✅ PHASE 1 TEST SUCCESSFUL")
    print("="*70)

finally:
    proc.terminate()
    proc.wait()
