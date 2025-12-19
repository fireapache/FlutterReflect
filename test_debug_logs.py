#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to capture detailed logs from flutter_reflect"""
import subprocess
import json
import sys
import io
import threading

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def read_stderr(proc):
    """Read and print stderr in real-time"""
    for line in iter(proc.stderr.readline, b''):
        try:
            print(f"[SERVER] {line.decode('utf-8', errors='replace').rstrip()}", file=sys.stderr)
        except:
            pass

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
            print(f"<<< Success", file=sys.stderr)
        elif 'error' in response:
            print(f"<<< Error: {response['error']}", file=sys.stderr)
        return response
    return None

def main():
    proc = subprocess.Popen(
        [r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe", "--log-level", "debug"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Start stderr reader thread
    stderr_thread = threading.Thread(target=read_stderr, args=(proc,), daemon=True)
    stderr_thread.start()

    try:
        print("=" * 70)
        print("FLUTTER INSPECTOR DEBUG WITH FULL LOGS")
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
        print("\n🔌 Connecting to Flutter app...", file=sys.stderr)
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
            print("❌ Failed to connect", file=sys.stderr)
            return

        print("✅ Connected!", file=sys.stderr)

        # Get widget tree
        print("\n📊 Getting widget tree (watch for service extension calls in logs)...", file=sys.stderr)
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

        # Give it time to log
        import time
        time.sleep(1)

        if tree_response.get('result'):
            result = tree_response['result']
            if 'content' in result:
                content = result['content'][0]['text']
                data = json.loads(content)
                if data.get('success'):
                    print(f"\n✅ SUCCESS! Tree extracted", file=sys.stderr)
                else:
                    print(f"\n❌ Error: {data.get('error', 'Unknown')}", file=sys.stderr)

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
