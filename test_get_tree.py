#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for flutter_get_tree tool"""
import subprocess
import json
import sys
import io

# Force UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def send_request(proc, request):
    """Send a JSON-RPC request and get response"""
    request_str = json.dumps(request) + '\n'
    print(f">>> Sending: {request['method']}", file=sys.stderr)
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline().decode().strip()
    if response_line:
        response = json.loads(response_line)
        return response
    return None

def main():
    # Start MCP server
    proc = subprocess.Popen(
        [r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # 1. Initialize
        print("=" * 60)
        print("PHASE 3 TEST: Widget Tree Extraction")
        print("=" * 60)

        send_request(proc, {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test", "version": "1.0"},
                "capabilities": {}
            },
            "id": 1
        })
        print("✅ Initialized MCP server")

        # 2. List tools
        tools_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        })
        tools = tools_response.get('result', {}).get('tools', [])
        tool_names = [t['name'] for t in tools]
        print(f"✅ Tools available: {tool_names}")

        if 'flutter_get_tree' not in tool_names:
            print("❌ ERROR: flutter_get_tree tool not found!")
            return

        # 3. Connect to Flutter app
        print("\n🔌 Connecting to Flutter app...")
        connect_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_connect",
                "arguments": {
                    "uri": "ws://127.0.0.1:8181/ws"
                }
            },
            "id": 3
        })

        if connect_response.get('result'):
            print("✅ Connected to Flutter app")
        else:
            print("❌ Failed to connect to Flutter app")
            print("Make sure Bookfy app is running with:")
            print("  flutter run -d windows --vm-service-port=8181 --disable-service-auth-codes")
            return

        # 4. Get widget tree (text format)
        print("\n📊 Getting widget tree (text format, depth=5)...")
        tree_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_tree",
                "arguments": {
                    "max_depth": 5,
                    "format": "text"
                }
            },
            "id": 4
        })

        if tree_response.get('result'):
            result = tree_response['result']
            if 'content' in result and len(result['content']) > 0:
                content = result['content'][0]
                if 'text' in content:
                    # Parse the JSON text
                    tree_data = json.loads(content['text'])

                    if tree_data.get('success'):
                        print(f"✅ Widget tree extracted successfully!")
                        print(f"   Node count: {tree_data['data'].get('node_count', 0)}")
                        print(f"   Max depth: {tree_data['data'].get('max_depth', 0)}")

                        if 'text' in tree_data['data']:
                            print(f"\n📋 Widget Tree:")
                            print("-" * 60)
                            print(tree_data['data']['text'])
                            print("-" * 60)
                    else:
                        print(f"❌ Error: {tree_data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ No text in response")
            else:
                print(f"❌ No content in response")
        else:
            error = tree_response.get('error', {})
            print(f"❌ Failed to get widget tree: {error}")

        # 5. Get widget tree (JSON format)
        print("\n📊 Getting widget tree (JSON format, depth=3)...")
        tree_json_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_tree",
                "arguments": {
                    "max_depth": 3,
                    "format": "json"
                }
            },
            "id": 5
        })

        if tree_json_response.get('result'):
            result = tree_json_response['result']
            if 'content' in result and len(result['content']) > 0:
                content = result['content'][0]
                if 'text' in content:
                    tree_data = json.loads(content['text'])

                    if tree_data.get('success'):
                        print(f"✅ Widget tree (JSON) extracted successfully!")
                        widget_tree = tree_data['data'].get('widget_tree', {})
                        print(f"   Root ID: {widget_tree.get('root_id', 'N/A')}")
                        print(f"   Total nodes: {widget_tree.get('node_count', 0)}")

                        # Show first few nodes
                        nodes = widget_tree.get('nodes', [])[:5]
                        print(f"\n📋 First 5 widgets:")
                        for node in nodes:
                            print(f"   - {node.get('type', 'Unknown')}")
                            if node.get('text'):
                                print(f"     Text: '{node['text']}'")
                    else:
                        print(f"❌ Error: {tree_data.get('error', 'Unknown error')}")

        # 6. Disconnect
        print("\n🔌 Disconnecting...")
        send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_disconnect",
                "arguments": {}
            },
            "id": 6
        })
        print("✅ Disconnected")

        print("\n" + "=" * 60)
        print("TEST COMPLETE!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    main()
