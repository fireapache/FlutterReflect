#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to explore Flutter VM Service and inspector API"""
import subprocess
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def send_request(proc, request):
    """Send a JSON-RPC request and get response"""
    request_str = json.dumps(request) + '\n'
    print(f"\n>>> {request['method']}", file=sys.stderr)
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    if response_line:
        response = json.loads(response_line)
        if 'result' in response:
            print(f"<<< Result: {json.dumps(response['result'], indent=2)[:500]}...", file=sys.stderr)
        elif 'error' in response:
            print(f"<<< Error: {response['error']}", file=sys.stderr)
        return response
    return None

def main():
    proc = subprocess.Popen(
        [r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        print("=" * 70)
        print("FLUTTER INSPECTOR API DEBUG")
        print("=" * 70)

        # Initialize
        send_request(proc, {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "debug", "version": "1.0"},
                "capabilities": {}
            },
            "id": 1
        })

        # Connect
        print("\n🔌 Connecting to Flutter app...")
        connect_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_connect",
                "arguments": {"uri": "ws://127.0.0.1:8181/ws"}
            },
            "id": 2
        })

        if not connect_response.get('result'):
            print("❌ Failed to connect")
            return

        print("✅ Connected!")

        # Now let's try calling the inspector via MCP tool with detailed logging
        print("\n📊 Trying to get widget tree...")
        tree_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_tree",
                "arguments": {
                    "max_depth": 3,
                    "format": "text"
                }
            },
            "id": 3
        })

        if tree_response.get('result'):
            result = tree_response['result']
            if 'content' in result:
                content = result['content'][0]['text']
                data = json.loads(content)
                print(f"\n✅ Response: {json.dumps(data, indent=2)}")
        else:
            error = tree_response.get('error', {})
            print(f"\n❌ Error: {error}")

        # Disconnect
        send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "flutter_disconnect", "arguments": {}},
            "id": 4
        })

    except Exception as e:
        print(f"\n❌ Exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    main()
