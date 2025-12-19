#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive test for Phases 4-6: Selector, Interaction, Properties"""
import subprocess
import json
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def send_request(proc, request):
    """Send MCP request and get response"""
    request_str = json.dumps(request) + '\n'
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()
    response_line = proc.stdout.readline().decode().strip()
    return json.loads(response_line) if response_line else None

def test_phase_4_selector(proc):
    """Test Phase 4: Widget Selector Engine"""
    print("\n" + "="*70)
    print("PHASE 4: WIDGET SELECTOR ENGINE")
    print("="*70)

    # Test 1: Find by widget type
    print("\n[Test 1] Find by widget type: 'Text'")
    resp = send_request(proc, {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_find",
            "arguments": {
                "selector": "Text",
                "find_all": True
            }
        },
        "id": 10
    })

    if resp and resp.get('result'):
        content = json.loads(resp['result']['content'][0]['text'])
        print(f"✅ Found {content['data']['count']} Text widgets")
        for widget in content['data']['widgets'][:3]:
            print(f"   - {widget['type']}: '{widget.get('text', 'N/A')}'")

    # Test 2: Find by exact text
    print("\n[Test 2] Find by exact text match")
    resp = send_request(proc, {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_find",
            "arguments": {
                "selector": "Text[text='MyApp']",
                "find_all": False
            }
        },
        "id": 11
    })

    if resp and resp.get('result'):
        content = json.loads(resp['result']['content'][0]['text'])
        if content.get('success'):
            print(f"✅ Found: {content['data']['widgets'][0]['type']}")
        else:
            print(f"⚠️  {content.get('error', 'Not found')}")

    # Test 3: Find by text contains
    print("\n[Test 3] Find by text contains")
    resp = send_request(proc, {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_find",
            "arguments": {
                "selector": "Text[contains='Multi']",
                "find_all": True
            }
        },
        "id": 12
    })

    if resp and resp.get('result'):
        content = json.loads(resp['result']['content'][0]['text'])
        print(f"✅ Found {content['data']['count']} widgets containing 'Multi'")

def test_phase_5_interaction(proc):
    """Test Phase 5: Widget Interaction"""
    print("\n" + "="*70)
    print("PHASE 5: WIDGET INTERACTION (requires Flutter Driver)")
    print("="*70)
    print("\n⚠️  NOTE: Interaction tools require Flutter Driver to be enabled.")
    print("    Add this to your Flutter app's main.dart:")
    print("    import 'package:flutter_driver/driver_extension.dart';")
    print("    void main() { enableFlutterDriverExtension(); runApp(MyApp()); }")

    # Test 1: Try tap (may fail if Driver not enabled, which is OK for this test)
    print("\n[Test 1] Tap tool availability")
    resp = send_request(proc, {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 20
    })

    if resp and resp.get('result'):
        tools = [t['name'] for t in resp['result']['tools']]
        tap_available = 'flutter_tap' in tools
        scroll_available = 'flutter_scroll' in tools
        type_available = 'flutter_type' in tools

        print(f"✅ flutter_tap available: {tap_available}")
        print(f"✅ flutter_scroll available: {scroll_available}")
        print(f"✅ flutter_type available: {type_available}")

def test_phase_6_properties(proc):
    """Test Phase 6: Property Inspection"""
    print("\n" + "="*70)
    print("PHASE 6: DETAILED PROPERTY INSPECTION")
    print("="*70)

    # First, find a widget to inspect
    print("\n[Step 1] Finding a widget to inspect...")
    find_resp = send_request(proc, {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_find",
            "arguments": {
                "selector": "Text",
                "find_all": False
            }
        },
        "id": 30
    })

    widget_id = None
    if find_resp and find_resp.get('result'):
        content = json.loads(find_resp['result']['content'][0]['text'])
        if content.get('success') and content['data']['widgets']:
            widget_id = content['data']['widgets'][0]['id']
            print(f"✅ Found widget: {widget_id}")

    if not widget_id:
        print("❌ Could not find a widget to inspect")
        return

    # Test 2: Get detailed properties
    print(f"\n[Step 2] Getting detailed properties for {widget_id}...")
    props_resp = send_request(proc, {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "flutter_get_properties",
            "arguments": {
                "widget_id": widget_id,
                "include_render": True,
                "include_layout": True
            }
        },
        "id": 31
    })

    if props_resp and props_resp.get('result'):
        content = json.loads(props_resp['result']['content'][0]['text'])
        if content.get('success'):
            data = content['data']
            print(f"\n✅ Properties retrieved:")
            print(f"   Type: {data['type']}")
            print(f"   Bounds: {data.get('bounds', 'N/A')}")
            print(f"   Enabled: {data['properties'].get('enabled', 'N/A')}")
            print(f"   Visible: {data['properties'].get('visible', 'N/A')}")
            if 'text' in data['properties']:
                print(f"   Text: '{data['properties']['text']}'")
            if data.get('render'):
                print(f"   Render Size: {data['render'].get('size', 'N/A')}")
        else:
            print(f"❌ {content.get('error', 'Failed to get properties')}")

def main():
    # Start MCP server
    proc = subprocess.Popen(
        [r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        print("="*70)
        print("FLUTTER REFLECT - PHASES 4-6 COMPREHENSIVE TEST")
        print("="*70)

        # Initialize
        print("\n🔧 Initializing MCP server...")
        init_resp = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test", "version": "1.0"},
                "capabilities": {}
            },
            "id": 1
        })

        if not init_resp:
            print("❌ Failed to initialize")
            return
        print("✅ MCP server initialized")

        # Connect to Flutter app
        print("\n🔌 Connecting to Flutter app (Bookfy)...")
        conn_resp = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_connect",
                "arguments": {"uri": "ws://127.0.0.1:8181/ws"}
            },
            "id": 2
        })

        if not conn_resp or not conn_resp.get('result'):
            print("❌ Failed to connect to Flutter app")
            print("   Make sure Bookfy app is running with: flutter run")
            return

        content = json.loads(conn_resp['result']['content'][0]['text'])
        if not content.get('success'):
            print("❌ Connection failed")
            return

        print("✅ Connected to Flutter app")

        # Run tests
        test_phase_4_selector(proc)
        test_phase_5_interaction(proc)
        test_phase_6_properties(proc)

        # Disconnect
        print("\n🔌 Disconnecting...")
        send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "flutter_disconnect", "arguments": {}},
            "id": 99
        })

        print("\n" + "="*70)
        print("✅ PHASES 4-6 TEST COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    main()
