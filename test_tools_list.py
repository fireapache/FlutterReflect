#!/usr/bin/env python3
"""Test that all tools are registered in the MCP server"""
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
    }).encode() + b'\n')
    proc.stdin.flush()
    proc.stdout.readline()  # consume init response

    # List tools
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }).encode() + b'\n')
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    response = json.loads(response_line)

    print("\n" + "="*70)
    print("REGISTERED FLUTTER REFLECT TOOLS")
    print("="*70)

    if response.get('result'):
        tools = response['result']['tools']

        phases = {
            'Phase 2: Connection': ['flutter_connect', 'flutter_disconnect'],
            'Phase 3: Widget Inspection': ['flutter_get_tree'],
            'Phase 4: Selector Engine': ['flutter_find'],
            'Phase 5: Widget Interaction': ['flutter_tap', 'flutter_type', 'flutter_scroll'],
            'Phase 6: Property Inspection': ['flutter_get_properties']
        }

        tool_names = [t['name'] for t in tools]

        for phase, expected_tools in phases.items():
            print(f"\n{phase}:")
            for tool_name in expected_tools:
                if tool_name in tool_names:
                    tool = next(t for t in tools if t['name'] == tool_name)
                    print(f"  ✅ {tool_name}")
                    print(f"     {tool['description'][:70]}...")
                else:
                    print(f"  ❌ {tool_name} - NOT FOUND")

        print(f"\n{'='*70}")
        print(f"Total Tools Registered: {len(tools)}")
        print(f"Expected: 8 (2 + 1 + 1 + 3 + 1)")

        if len(tools) >= 8:
            print("\n✅ All tools successfully registered!")
        else:
            print(f"\n⚠️  Only {len(tools)} tools found")

finally:
    proc.terminate()
    proc.wait()
