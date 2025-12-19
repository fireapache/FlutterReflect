#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for FlutterReflect MCP server"""
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
    print(f">>> Sending: {request}", file=sys.stderr)
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline().decode().strip()
    if response_line:
        response = json.loads(response_line)
        print(f"<<< Received: {json.dumps(response, indent=2)}", file=sys.stderr)
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
        init_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test", "version": "1.0"},
                "capabilities": {}
            },
            "id": 1
        })
        print(f"\n✅ Initialize: {init_response.get('result', {}).get('serverInfo', {}).get('name')}")

        # 2. List tools
        tools_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        })
        tools = tools_response.get('result', {}).get('tools', [])
        print(f"\n✅ Tools available: {[t['name'] for t in tools]}")

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

        result = connect_response.get('result', {}).get('content', [{}])[0].get('text', '')
        print(f"\n✅ Connection result:\n{result}")

        # 4. Disconnect
        print("\n🔌 Disconnecting...")
        disconnect_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_disconnect",
                "arguments": {}
            },
            "id": 4
        })

        result = disconnect_response.get('result', {}).get('content', [{}])[0].get('text', '')
        print(f"\n✅ Disconnect result:\n{result}")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    main()
