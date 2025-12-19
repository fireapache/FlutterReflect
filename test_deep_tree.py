#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get deeper widget tree to see actual UI widgets"""
import subprocess
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def send_request(proc, request):
    """Send a JSON-RPC request and get response"""
    request_str = json.dumps(request) + '\n'
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()
    return json.loads(proc.stdout.readline().decode().strip())

def main():
    proc = subprocess.Popen(
        [r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Initialize
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

        # Connect
        send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_connect",
                "arguments": {"uri": "ws://127.0.0.1:8181/ws"}
            },
            "id": 2
        })

        # Get deep tree
        tree_response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_tree",
                "arguments": {
                    "max_depth": 20,
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
                if data.get('success'):
                    print(data['data']['text'])

        # Disconnect
        send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "flutter_disconnect", "arguments": {}},
            "id": 4
        })

    except Exception as e:
        print(f"Exception: {e}", file=sys.stderr)
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    main()
