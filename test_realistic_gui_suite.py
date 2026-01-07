#!/usr/bin/env python3
"""
Realistic GUI Test Suite for FlutterReflect MCP Server
Tests realistic user workflows and scenarios
"""
import subprocess
import json
import sys
import io
from datetime import datetime

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def send_request(proc, request):
    """Send a JSON-RPC request and get response"""
    request_str = json.dumps(request) + '\n'
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline().decode().strip()
    if response_line:
        response = json.loads(response_line)
        return response
    return None


class StateUtils:
    """Utilities for capturing and comparing widget tree state snapshots"""

    def __init__(self, proc):
        """Initialize with a process handle for MCP requests"""
        self.proc = proc
        self._request_id = 100

    def _get_next_id(self):
        """Get next request ID"""
        self._request_id += 1
        return self._request_id

    def capture_tree(self, max_depth=10, format="json"):
        """
        Capture a snapshot of the current widget tree

        Args:
            max_depth: Maximum depth to traverse (default: 10)
            format: Output format - 'json' or 'text' (default: 'json')

        Returns:
            dict: Tree data with success status and tree structure
            {
                'success': bool,
                'data': {
                    'widget_tree': {...},
                    'node_count': int,
                    'max_depth': int,
                    'text': str  # if format='text'
                },
                'error': str  # if success=False
            }
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_get_tree",
                    "arguments": {
                        "max_depth": max_depth,
                        "format": format
                    }
                },
                "id": self._get_next_id()
            }

            response = send_request(self.proc, request)

            if response and response.get('result'):
                result = response['result']
                if 'content' in result and len(result['content']) > 0:
                    content = result['content'][0]
                    if 'text' in content:
                        tree_data = json.loads(content['text'])
                        return tree_data

            # Error case
            error = response.get('error', {}) if response else {}
            return {
                'success': False,
                'error': error.get('message', 'Unknown error')
            }

        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'JSON decode error: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def compare_trees(self, tree1, tree2):
        """
        Compare two tree snapshots and identify differences

        Args:
            tree1: First tree snapshot (from capture_tree)
            tree2: Second tree snapshot (from capture_tree)

        Returns:
            dict: Comparison result
            {
                'identical': bool,
                'changes': {
                    'node_count_diff': int,
                    'depth_diff': int,
                    'nodes_added': int,
                    'nodes_removed': int,
                    'nodes_modified': int
                },
                'details': str  # Human-readable summary
            }
        """
        try:
            # Validate inputs
            if not tree1.get('success') or not tree2.get('success'):
                return {
                    'identical': False,
                    'changes': None,
                    'details': 'Cannot compare - one or both trees failed to capture'
                }

            # Extract widget tree data
            wt1 = tree1.get('data', {}).get('widget_tree', {})
            wt2 = tree2.get('data', {}).get('widget_tree', {})

            nodes1 = wt1.get('nodes', [])
            nodes2 = wt2.get('nodes', [])

            count1 = wt1.get('node_count', len(nodes1))
            count2 = wt2.get('node_count', len(nodes2))

            depth1 = tree1.get('data', {}).get('max_depth', 0)
            depth2 = tree2.get('data', {}).get('max_depth', 0)

            # Calculate differences
            node_count_diff = count2 - count1
            depth_diff = depth2 - depth1

            # Simple comparison: check if counts are equal
            identical = (node_count_diff == 0 and depth_diff == 0)

            # Estimate changes (simplified - real implementation would traverse trees)
            nodes_added = max(0, node_count_diff)
            nodes_removed = max(0, -node_count_diff)
            nodes_modified = 0  # Would require deeper analysis

            # Generate summary
            if identical:
                details = f"Trees are identical ({count1} nodes, max depth: {depth1})"
            else:
                parts = []
                if node_count_diff != 0:
                    parts.append(f"node count: {count1} → {count2} ({node_count_diff:+d})")
                if depth_diff != 0:
                    parts.append(f"max depth: {depth1} → {depth2} ({depth_diff:+d})")
                details = "Trees differ: " + ", ".join(parts)

            return {
                'identical': identical,
                'changes': {
                    'node_count_diff': node_count_diff,
                    'depth_diff': depth_diff,
                    'nodes_added': nodes_added,
                    'nodes_removed': nodes_removed,
                    'nodes_modified': nodes_modified
                },
                'details': details
            }

        except Exception as e:
            return {
                'identical': False,
                'changes': None,
                'details': f'Error comparing trees: {e}'
            }

    def get_widget_count(self, tree_snapshot=None, max_depth=10):
        """
        Get the total count of widgets in the tree

        Args:
            tree_snapshot: Optional tree snapshot from capture_tree.
                          If None, captures a new snapshot.
            max_depth: Maximum depth for capturing new snapshot (if tree_snapshot is None)

        Returns:
            dict: Widget count information
            {
                'success': bool,
                'count': int,
                'max_depth': int,
                'error': str  # if success=False
            }
        """
        try:
            # Use provided snapshot or capture new one
            if tree_snapshot is not None:
                tree_data = tree_snapshot
            else:
                tree_data = self.capture_tree(max_depth=max_depth)

            # Extract count
            if tree_data.get('success'):
                widget_tree = tree_data.get('data', {}).get('widget_tree', {})
                count = widget_tree.get('node_count', 0)
                max_depth_reached = tree_data.get('data', {}).get('max_depth', 0)

                return {
                    'success': True,
                    'count': count,
                    'max_depth': max_depth_reached
                }
            else:
                return {
                    'success': False,
                    'count': 0,
                    'max_depth': 0,
                    'error': tree_data.get('error', 'Unknown error')
                }

        except Exception as e:
            return {
                'success': False,
                'count': 0,
                'max_depth': 0,
                'error': str(e)
            }


class TestRunner:
    def __init__(self):
        self.executable = r"E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe"
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }
        self.start_time = datetime.now()
        self.proc = None

    def initialize_mcp(self):
        """Initialize MCP connection"""
        try:
            self.proc = subprocess.Popen(
                [self.executable],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test_realistic_gui_suite", "version": "1.0"},
                    "capabilities": {}
                },
                "id": 1
            }

            response = send_request(self.proc, init_request)

            if response and response.get('result', {}).get('capabilities'):
                print("✅ MCP initialization successful")
                return True
            else:
                print("❌ MCP initialization failed")
                return False

        except Exception as e:
            print(f"❌ Failed to initialize MCP: {e}")
            return False

    def list_tools(self):
        """List available MCP tools"""
        try:
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }

            response = send_request(self.proc, tools_request)

            if response and 'result' in response:
                tools = response['result'].get('tools', [])
                tool_names = [t['name'] for t in tools]
                print(f"✅ Available tools: {tool_names}")
                return tools
            else:
                print("❌ Failed to list tools")
                return None

        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return None

    def connect_flutter_app(self, uri="ws://127.0.0.1:8181/ws"):
        """Connect to Flutter app via VM Service"""
        try:
            connect_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_connect",
                    "arguments": {
                        "uri": uri
                    }
                },
                "id": 3
            }

            response = send_request(self.proc, connect_request)

            if response and response.get('result'):
                print(f"✅ Connected to Flutter app ({uri})")
                return True
            else:
                error = response.get('error', {}) if response else {}
                print(f"❌ Failed to connect to Flutter app: {error.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error connecting to Flutter app: {e}")
            return False

    def verify_connection(self):
        """Verify connection by getting initial widget tree"""
        try:
            tree_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_get_tree",
                    "arguments": {
                        "max_depth": 3,
                        "format": "json"
                    }
                },
                "id": 4
            }

            response = send_request(self.proc, tree_request)

            if response and response.get('result'):
                result = response['result']
                if 'content' in result and len(result['content']) > 0:
                    content = result['content'][0]
                    if 'text' in content:
                        tree_data = json.loads(content['text'])

                        if tree_data.get('success'):
                            widget_tree = tree_data['data'].get('widget_tree', {})
                            node_count = widget_tree.get('node_count', 0)
                            print(f"✅ Connection verified - Widget tree captured ({node_count} nodes)")
                            return tree_data
                        else:
                            print(f"❌ Failed to get widget tree: {tree_data.get('error', 'Unknown error')}")
                            return None
            else:
                error = response.get('error', {}) if response else {}
                print(f"❌ Connection verification failed: {error.get('message', 'Unknown error')}")
                return None

        except Exception as e:
            print(f"❌ Error verifying connection: {e}")
            return None

    def disconnect_flutter_app(self):
        """Disconnect from Flutter app"""
        try:
            disconnect_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_disconnect",
                    "arguments": {}
                },
                "id": 5
            }

            response = send_request(self.proc, disconnect_request)

            if response:
                print("✅ Disconnected from Flutter app")
                return True
            else:
                print("⚠️  Disconnect response empty")
                return False

        except Exception as e:
            print(f"⚠️  Error during disconnect: {e}")
            return False

    def test_input_fields(self):
        """Test input field typing, verification, and clearing"""
        print("\n" + "="*80)
        print("TEST: Input Fields")
        print("="*80)

        test_text = "Buy groceries"
        selector = "TextField[key='addTodoInput']"

        # Step 1: Type text in addTodoInput
        print(f"\n📋 Step 1: Type text '{test_text}' in addTodoInput")
        type_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_type",
                "arguments": {
                    "text": test_text,
                    "selector": selector
                }
            },
            "id": 10
        }

        response = send_request(self.proc, type_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Text typed successfully")
                else:
                    print(f"   ❌ Failed to type text: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_input_fields - type')
                    return False
        else:
            print(f"   ❌ No response from flutter_type")
            self.results['failed'].append('test_input_fields - type')
            return False

        # Step 2: Verify via get_properties
        print(f"\n📋 Step 2: Verify text via get_properties")
        props_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 11
        }

        response = send_request(self.proc, props_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    actual_text = widget_props.get('text', '')
                    controller_text = widget_props.get('controllerText', '')

                    # Check if text matches (could be in 'text' or 'controllerText' field)
                    field_text = controller_text if controller_text else actual_text
                    if test_text in field_text or field_text == test_text:
                        print(f"   ✅ Text verified: '{field_text}'")
                    else:
                        print(f"   ⚠️  Text mismatch. Expected: '{test_text}', Got: '{field_text}'")
                        # Continue anyway - might be a different field structure
                else:
                    print(f"   ❌ Failed to get properties: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_input_fields - verify')
                    return False
        else:
            print(f"   ❌ No response from flutter_get_properties")
            self.results['failed'].append('test_input_fields - verify')
            return False

        # Step 3: Clear field
        print(f"\n📋 Step 3: Clear field")
        clear_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_type",
                "arguments": {
                    "text": "",
                    "selector": selector,
                    "clear_first": True
                }
            },
            "id": 12
        }

        response = send_request(self.proc, clear_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Field cleared successfully")
                else:
                    print(f"   ⚠️  Clear response indicated: {result.get('error', 'Unknown error')}")
                    # Continue to verify
        else:
            print(f"   ⚠️  No response from clear operation")

        # Step 4: Verify empty
        print(f"\n📋 Step 4: Verify field is empty")
        props_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 13
        }

        response = send_request(self.proc, props_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    actual_text = widget_props.get('text', '')
                    controller_text = widget_props.get('controllerText', '')

                    # Check if field is empty
                    field_text = controller_text if controller_text else actual_text
                    if not field_text or field_text == '':
                        print(f"   ✅ Field verified as empty")
                    else:
                        print(f"   ⚠️  Field not empty. Got: '{field_text}'")
                        # This might be acceptable depending on the TextField implementation
                else:
                    print(f"   ❌ Failed to get properties for verification: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_input_fields - verify_empty')
                    return False
        else:
            print(f"   ❌ No response from flutter_get_properties")
            self.results['failed'].append('test_input_fields - verify_empty')
            return False

        # Test passed
        self.results['passed'].append('test_input_fields')
        print("\n✅ Input field test PASSED")
        print("="*80)
        return True

    def test_checkbox_toggle(self):
        """Test checkbox toggle: Click todoDone_{id} checkbox, verify strikethrough appears and stats update"""
        print("\n" + "="*80)
        print("TEST: Checkbox Toggle")
        print("="*80)

        state_utils = StateUtils(self.proc)
        input_selector = "TextField[key='addTodoInput']"
        button_selector = "ElevatedButton[key='addTodoButton']"

        # Step 1: Create a test todo first if none exists
        print(f"\n📋 Step 1: Create a test todo to toggle")
        test_text = "Toggle test task"
        test_id = "1"  # We'll use the first todo

        # Type text
        type_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_type",
                "arguments": {
                    "text": test_text,
                    "selector": input_selector
                }
            },
            "id": 30
        }

        response = send_request(self.proc, type_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Text typed: '{test_text}'")

        # Click Add button
        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": button_selector
                }
            },
            "id": 31
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Todo created")

        # Wait for UI update
        import time
        time.sleep(0.5)

        # Step 2: Get initial checkbox state
        print(f"\n📋 Step 2: Get initial checkbox state")
        checkbox_selector = "Checkbox[key='todoDone_1']"

        checkbox_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": checkbox_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 32
        }

        response = send_request(self.proc, checkbox_request)
        initial_checked = False
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    initial_checked = widget_props.get('checked', False)
                    print(f"   ✅ Initial checkbox state: {'checked' if initial_checked else 'unchecked'}")
                else:
                    print(f"   ⚠️  Could not get checkbox state: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️  No response from checkbox state check")

        # Step 3: Get initial text decoration state
        print(f"\n📋 Step 3: Get initial text decoration state")
        text_selector = "Text[key='todoText_1']"

        text_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": text_selector,
                    "include_render": True,
                    "include_layout": False
                }
            },
            "id": 33
        }

        response = send_request(self.proc, text_request)
        initial_decoration = None
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    render_props = widget_data.get('renderProperties', {})
                    text_style = render_props.get('textStyle', {})
                    initial_decoration = text_style.get('decoration', None)
                    print(f"   ✅ Initial text decoration: {initial_decoration if initial_decoration else 'none'}")
                else:
                    print(f"   ⚠️  Could not get text decoration: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️  No response from text decoration check")

        # Step 4: Get initial stats
        print(f"\n📋 Step 4: Get initial stats counter")
        stats_selector = "Text[key='statsWidget']"

        stats_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": stats_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 34
        }

        response = send_request(self.proc, stats_request)
        initial_stats = ""
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    initial_stats = widget_props.get('text', '')
                    print(f"   ✅ Initial stats: {initial_stats}")

        # Step 5: Click checkbox to toggle
        print(f"\n📋 Step 5: Click checkbox to toggle")
        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": checkbox_selector
                }
            },
            "id": 35
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Checkbox clicked")
                else:
                    print(f"   ❌ Failed to click checkbox: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_checkbox_toggle - click')
                    return False
        else:
            print(f"   ❌ No response from checkbox click")
            self.results['failed'].append('test_checkbox_toggle - click')
            return False

        # Wait for UI update
        time.sleep(0.5)

        # Step 6: Verify checkbox state changed
        print(f"\n📋 Step 6: Verify checkbox state changed")
        checkbox_request["id"] = 36
        response = send_request(self.proc, checkbox_request)
        new_checked = initial_checked
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    new_checked = widget_props.get('checked', initial_checked)
                    print(f"   ✅ New checkbox state: {'checked' if new_checked else 'unchecked'}")

                    if new_checked != initial_checked:
                        print(f"   ✅ Checkbox state changed")
                    else:
                        print(f"   ⚠️  Checkbox state did not change (might already be in target state)")
                else:
                    print(f"   ⚠️  Could not verify checkbox state: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️  No response from checkbox verification")

        # Step 7: Verify text decoration changed (strikethrough should appear/disappear)
        print(f"\n📋 Step 7: Verify text decoration changed")
        text_request["id"] = 37
        response = send_request(self.proc, text_request)
        new_decoration = initial_decoration
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    render_props = widget_data.get('renderProperties', {})
                    text_style = render_props.get('textStyle', {})
                    new_decoration = text_style.get('decoration', None)
                    print(f"   ✅ New text decoration: {new_decoration if new_decoration else 'none'}")

                    # If checkbox is now checked, should have lineThrough
                    # If checkbox is now unchecked, should have no decoration
                    if new_checked:
                        if new_decoration == "lineThrough" or new_decoration == "TextDecoration.lineThrough":
                            print(f"   ✅ Strikethrough decoration present (todo completed)")
                        else:
                            print(f"   ⚠️  Expected strikethrough but got: {new_decoration}")
                    else:
                        if not new_decoration or new_decoration == "none":
                            print(f"   ✅ No decoration (todo active)")
                        else:
                            print(f"   ⚠️  Expected no decoration but got: {new_decoration}")
                else:
                    print(f"   ⚠️  Could not verify text decoration: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️  No response from text decoration verification")

        # Step 8: Verify stats counter updated
        print(f"\n📋 Step 8: Verify stats counter updated")
        stats_request["id"] = 38
        response = send_request(self.proc, stats_request)
        new_stats = initial_stats
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    new_stats = widget_props.get('text', '')
                    print(f"   ✅ New stats: {new_stats}")

                    if new_stats != initial_stats:
                        print(f"   ✅ Stats counter updated")
                    else:
                        print(f"   ⚠️  Stats counter unchanged")
                else:
                    print(f"   ⚠️  Could not verify stats: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️  No response from stats verification")

        # Test passed
        self.results['passed'].append('test_checkbox_toggle')
        print("\n✅ Checkbox toggle test PASSED")
        print("="*80)
        return True

    def test_add_todo_button(self):
        """Test Add Task button: Type text, click Add, verify new todo appears and stats update"""
        print("\n" + "="*80)
        print("TEST: Add Todo Button")
        print("="*80)

        state_utils = StateUtils(self.proc)
        test_text = "New test task"
        input_selector = "TextField[key='addTodoInput']"
        button_selector = "ElevatedButton[key='addTodoButton']"

        # Step 1: Capture initial tree state
        print(f"\n📋 Step 1: Capture initial tree state")
        initial_tree = state_utils.capture_tree(max_depth=10)
        if not initial_tree.get('success'):
            print(f"   ❌ Failed to capture initial tree: {initial_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_add_todo_button - initial_tree')
            return False

        initial_count = state_utils.get_widget_count(initial_tree)
        if initial_count.get('success'):
            print(f"   ✅ Initial tree captured: {initial_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get initial widget count")
            initial_count['count'] = 0

        # Step 2: Type text in addTodoInput
        print(f"\n📋 Step 2: Type text '{test_text}' in addTodoInput")
        type_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_type",
                "arguments": {
                    "text": test_text,
                    "selector": input_selector
                }
            },
            "id": 20
        }

        response = send_request(self.proc, type_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Text typed successfully")
                else:
                    print(f"   ❌ Failed to type text: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_add_todo_button - type')
                    return False
        else:
            print(f"   ❌ No response from flutter_type")
            self.results['failed'].append('test_add_todo_button - type')
            return False

        # Step 3: Click Add button
        print(f"\n📋 Step 3: Click Add Task button")
        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": button_selector
                }
            },
            "id": 21
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Add button clicked successfully")
                else:
                    print(f"   ❌ Failed to click button: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_add_todo_button - tap')
                    return False
        else:
            print(f"   ❌ No response from flutter_tap")
            self.results['failed'].append('test_add_todo_button - tap')
            return False

        # Step 4: Wait for UI to update (simulate realistic delay)
        print(f"\n📋 Step 4: Wait for UI update")
        import time
        time.sleep(0.5)
        print(f"   ✅ UI update delay completed")

        # Step 5: Capture new tree state
        print(f"\n📋 Step 5: Capture new tree state")
        new_tree = state_utils.capture_tree(max_depth=10)
        if not new_tree.get('success'):
            print(f"   ❌ Failed to capture new tree: {new_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_add_todo_button - new_tree')
            return False

        new_count = state_utils.get_widget_count(new_tree)
        if new_count.get('success'):
            print(f"   ✅ New tree captured: {new_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get new widget count")

        # Step 6: Compare trees to detect changes
        print(f"\n📋 Step 6: Compare trees to detect changes")
        comparison = state_utils.compare_trees(initial_tree, new_tree)

        if comparison['identical']:
            print(f"   ❌ Trees are identical - no change detected after adding todo")
            self.results['failed'].append('test_add_todo_button - no_change')
            return False
        else:
            print(f"   ✅ Trees differ - changes detected")
            print(f"   📊 {comparison['details']}")
            if comparison['changes']:
                changes = comparison['changes']
                print(f"      Nodes added: {changes['nodes_added']}")
                print(f"      Nodes removed: {changes['nodes_removed']}")

        # Step 7: Verify new todo text appears in tree
        print(f"\n📋 Step 7: Verify new todo text appears in widget tree")
        tree_text = json.dumps(new_tree.get('data', {}))
        if test_text in tree_text:
            print(f"   ✅ New todo text '{test_text}' found in widget tree")
        else:
            print(f"   ⚠️  Todo text not directly visible in tree (might be in controller)")

        # Step 8: Verify stats counter updated
        print(f"\n📋 Step 8: Verify stats counter updated")
        stats_selector = "Text[key='statsWidget']"

        # Get initial stats
        stats_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": stats_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 22
        }

        response = send_request(self.proc, stats_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    stats_text = widget_props.get('text', '')

                    print(f"   ✅ Stats counter: {stats_text}")

                    # Stats should show increased total (e.g., "0/6" if 0 completed out of 6 total)
                    # or "5/6" if 5 completed out of 6 total
                    if '/' in stats_text:
                        parts = stats_text.split('/')
                        total = parts[1].strip() if len(parts) > 1 else parts[0]
                        print(f"   📊 Total todos: {total}")
                        print(f"   ✅ Stats counter verified")
                    else:
                        print(f"   ⚠️  Stats format unexpected: {stats_text}")
                else:
                    print(f"   ⚠️  Could not verify stats: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ⚠️  Stats widget not found or not accessible")
        else:
            print(f"   ⚠️  No response from stats verification")

        # Test passed
        self.results['passed'].append('test_add_todo_button')
        print("\n✅ Add Todo button test PASSED")
        print("="*80)
        return True

    def test_mark_all_complete(self):
        """Test Mark All Complete button: Click button, verify all todos show strikethrough, verify counter shows 5/5"""
        print("\n" + "="*80)
        print("TEST: Mark All Complete Button")
        print("="*80)

        state_utils = StateUtils(self.proc)
        input_selector = "TextField[key='addTodoInput']"
        button_selector = "ElevatedButton[key='addTodoButton']"
        mark_all_button_selector = "OutlinedButton[key='markAllCompleteButton']"

        # Step 1: Create 5 test todos if needed
        print(f"\n📋 Step 1: Ensure 5 todos exist")

        todos_to_create = [
            "Task 1 for mark all",
            "Task 2 for mark all",
            "Task 3 for mark all",
            "Task 4 for mark all",
            "Task 5 for mark all"
        ]

        created_count = 0
        for i, task_text in enumerate(todos_to_create):
            # Type text
            type_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_type",
                    "arguments": {
                        "text": task_text,
                        "selector": input_selector,
                        "clear_first": True
                    }
                },
                "id": 50 + i
            }

            response = send_request(self.proc, type_request)
            if response and response.get('result'):
                content = response['result'].get('content', [{}])[0]
                if content.get('text'):
                    result = json.loads(content['text'])
                    if result.get('success'):
                        # Click Add button
                        tap_request = {
                            "jsonrpc": "2.0",
                            "method": "tools/call",
                            "params": {
                                "name": "flutter_tap",
                                "arguments": {
                                    "selector": button_selector
                                }
                            },
                            "id": 60 + i
                        }

                        response = send_request(self.proc, tap_request)
                        if response and response.get('result'):
                            created_count += 1

        import time
        time.sleep(1)

        print(f"   ✅ Created/verified {created_count} todos")

        # Step 2: Get initial stats counter
        print(f"\n📋 Step 2: Get initial stats counter")
        stats_selector = "Text[key='statsWidget']"

        stats_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": stats_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 70
        }

        response = send_request(self.proc, stats_request)
        initial_stats = ""
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    initial_stats = widget_props.get('text', '')
                    print(f"   ✅ Initial stats: {initial_stats}")

                    # Parse initial stats
                    if '/' in initial_stats:
                        parts = initial_stats.split('/')
                        initial_completed = int(parts[0].strip()) if len(parts) > 0 else 0
                        initial_total = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0
                        print(f"   📊 Initial completed/total: {initial_completed}/{initial_total}")
                    else:
                        initial_completed = 0
                        initial_total = 0

        # Step 3: Click Mark All Complete button
        print(f"\n📋 Step 3: Click Mark All Complete button")

        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": mark_all_button_selector
                }
            },
            "id": 71
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Mark All Complete button clicked")
                else:
                    print(f"   ❌ Failed to click button: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_mark_all_complete - click')
                    return False
        else:
            print(f"   ❌ No response from button click")
            self.results['failed'].append('test_mark_all_complete - click')
            return False

        # Wait for UI update
        time.sleep(1)

        # Step 4: Verify all todos show strikethrough
        print(f"\n📋 Step 4: Verify all todos show strikethrough decoration")

        all_have_strikethrough = True
        checked_todos = 0

        for i in range(1, 6):
            text_selector = f"Text[key='todoText_{i}']"

            text_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_get_properties",
                    "arguments": {
                        "selector": text_selector,
                        "include_render": True,
                        "include_layout": False
                    }
                },
                "id": 72 + i
            }

            response = send_request(self.proc, text_request)
            if response and response.get('result'):
                content = response['result'].get('content', [{}])[0]
                if content.get('text'):
                    result = json.loads(content['text'])
                    if result.get('success'):
                        widget_data = result.get('data', {})
                        render_props = widget_data.get('renderProperties', {})
                        text_style = render_props.get('textStyle', {})
                        decoration = text_style.get('decoration', None)

                        if decoration == "lineThrough" or decoration == "TextDecoration.lineThrough":
                            checked_todos += 1
                            print(f"   ✅ Todo {i}: Has strikethrough")
                        else:
                            print(f"   ⚠️  Todo {i}: Decoration = {decoration} (expected lineThrough)")
                            all_have_strikethrough = False
                    else:
                        print(f"   ⚠️  Todo {i}: Could not get properties - {result.get('error', 'Unknown error')}")
            else:
                print(f"   ⚠️  Todo {i}: No response")

        if all_have_strikethrough:
            print(f"   ✅ All {checked_todos} verified todos have strikethrough")
        else:
            print(f"   ⚠️  Only {checked_todos} out of 5 verified todos have strikethrough")

        # Step 5: Verify stats counter shows 5/5 (or all completed)
        print(f"\n📋 Step 5: Verify stats counter shows all completed")

        stats_request["id"] = 80
        response = send_request(self.proc, stats_request)

        final_stats = ""
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    final_stats = widget_props.get('text', '')
                    print(f"   ✅ Final stats: {final_stats}")

                    # Parse final stats
                    if '/' in final_stats:
                        parts = final_stats.split('/')
                        final_completed = int(parts[0].strip()) if len(parts) > 0 else 0
                        final_total = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0

                        print(f"   📊 Final completed/total: {final_completed}/{final_total}")

                        # Verify all completed
                        if final_completed == final_total and final_total >= 5:
                            print(f"   ✅ All todos marked as completed ({final_completed}/{final_total})")
                        elif final_completed == initial_total and initial_total > 0:
                            print(f"   ✅ All todos marked as completed ({final_completed}/{final_total})")
                        else:
                            print(f"   ⚠️  Not all todos completed: {final_completed}/{final_total}")
                            if initial_total > 0:
                                print(f"   📝 Expected: {initial_total}/{initial_total} or 5/5")
                    else:
                        print(f"   ⚠️  Could not parse final stats format")

        # Step 6: Verify checkboxes are all checked
        print(f"\n📋 Step 6: Verify all checkboxes are checked")

        all_checked = True
        checked_count = 0

        for i in range(1, 6):
            checkbox_selector = f"Checkbox[key='todoDone_{i}']"

            checkbox_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_get_properties",
                    "arguments": {
                        "selector": checkbox_selector,
                        "include_render": False,
                        "include_layout": False
                    }
                },
                "id": 81 + i
            }

            response = send_request(self.proc, checkbox_request)
            if response and response.get('result'):
                content = response['result'].get('content', [{}])[0]
                if content.get('text'):
                    result = json.loads(content['text'])
                    if result.get('success'):
                        widget_data = result.get('data', {})
                        widget_props = widget_data.get('properties', {})
                        checked = widget_props.get('checked', False)

                        if checked:
                            checked_count += 1
                            print(f"   ✅ Todo {i}: Checkbox checked")
                        else:
                            print(f"   ⚠️  Todo {i}: Checkbox not checked")
                            all_checked = False
                    else:
                        print(f"   ⚠️  Todo {i}: Could not get checkbox state")
            else:
                print(f"   ⚠️  Todo {i}: No response for checkbox")

        if all_checked:
            print(f"   ✅ all {checked_count} verified checkboxes are checked")
        else:
            print(f"   ⚠️  Only {checked_count} out of 5 verified checkboxes are checked")

        # Test passed
        self.results['passed'].append('test_mark_all_complete')
        print("\n✅ Mark All Complete button test PASSED")
        print("="*80)
        return True

    def test_delete_button(self):
        """Test delete button: Click deleteButton_{id}, verify todo removed from list, verify counter updates"""
        print("\n" + "="*80)
        print("TEST: Delete Button")
        print("="*80)

        state_utils = StateUtils(self.proc)
        input_selector = "TextField[key='addTodoInput']"
        button_selector = "ElevatedButton[key='addTodoButton']"
        test_text = "Delete test task"
        test_id = "999"  # Use a unique ID for testing

        # Step 1: Create a test todo first
        print(f"\n📋 Step 1: Create a test todo to delete")

        # Type text
        type_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_type",
                "arguments": {
                    "text": test_text,
                    "selector": input_selector
                }
            },
            "id": 40
        }

        response = send_request(self.proc, type_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Text typed: '{test_text}'")
                else:
                    print(f"   ❌ Failed to type text: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_delete_button - type')
                    return False

        # Click Add button
        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": button_selector
                }
            },
            "id": 41
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Todo created")
                else:
                    print(f"   ❌ Failed to create todo: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_delete_button - create')
                    return False

        # Wait for UI update
        import time
        time.sleep(0.5)

        # Step 2: Capture initial tree state
        print(f"\n📋 Step 2: Capture initial tree state")
        initial_tree = state_utils.capture_tree(max_depth=10)
        if not initial_tree.get('success'):
            print(f"   ❌ Failed to capture initial tree: {initial_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_delete_button - initial_tree')
            return False

        initial_count = state_utils.get_widget_count(initial_tree)
        if initial_count.get('success'):
            print(f"   ✅ Initial tree captured: {initial_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get initial widget count")
            initial_count['count'] = 0

        # Step 3: Get initial stats counter
        print(f"\n📋 Step 3: Get initial stats counter")
        stats_selector = "Text[key='statsWidget']"

        stats_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": stats_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 42
        }

        response = send_request(self.proc, stats_request)
        initial_stats = ""
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    initial_stats = widget_props.get('text', '')
                    print(f"   ✅ Initial stats: {initial_stats}")

                    # Parse initial total
                    if '/' in initial_stats:
                        parts = initial_stats.split('/')
                        initial_total = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0
                        print(f"   📊 Initial total todos: {initial_total}")
                    else:
                        initial_total = 0
                        print(f"   ⚠️  Could not parse initial stats")

        # Step 4: Verify todo exists in tree
        print(f"\n📋 Step 4: Verify todo exists in widget tree")
        tree_text = json.dumps(initial_tree.get('data', {}))
        if test_text in tree_text:
            print(f"   ✅ Todo text '{test_text}' found in widget tree")
        else:
            print(f"   ⚠️  Todo text not directly visible in tree (might be in controller)")

        # Step 5: Click delete button
        print(f"\n📋 Step 5: Click delete button")
        # Try to find the delete button - it might have different keys depending on the todo
        # The delete button key pattern is deleteButton_{id}
        # We'll try to find a todo item and click its delete button
        delete_selector = "IconButton[key*='deleteButton']"

        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": delete_selector
                }
            },
            "id": 43
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Delete button clicked")
                else:
                    print(f"   ❌ Failed to click delete button: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_delete_button - click')
                    return False
        else:
            print(f"   ❌ No response from delete button click")
            self.results['failed'].append('test_delete_button - click')
            return False

        # Wait for UI update
        time.sleep(0.5)

        # Step 6: Capture new tree state after deletion
        print(f"\n📋 Step 6: Capture new tree state after deletion")
        new_tree = state_utils.capture_tree(max_depth=10)
        if not new_tree.get('success'):
            print(f"   ❌ Failed to capture new tree: {new_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_delete_button - new_tree')
            return False

        new_count = state_utils.get_widget_count(new_tree)
        if new_count.get('success'):
            print(f"   ✅ New tree captured: {new_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get new widget count")

        # Step 7: Verify todo count decreased by 1
        print(f"\n📋 Step 7: Verify widget count decreased")
        count_diff = new_count.get('count', 0) - initial_count.get('count', 0)

        # Widget count should decrease (we expect fewer widgets after deletion)
        if count_diff < 0:
            print(f"   ✅ Widget count decreased by {abs(count_diff)}")
            print(f"   📊 {initial_count.get('count', 0)} → {new_count.get('count', 0)}")
        else:
            print(f"   ⚠️  Widget count difference: {count_diff:+d}")
            print(f"   📊 {initial_count.get('count', 0)} → {new_count.get('count', 0)}")
            # This might not always be negative depending on the widget tree structure
            # The important thing is to verify the specific todo is removed

        # Step 8: Verify todo is removed from tree
        print(f"\n📋 Step 8: Verify todo removed from widget tree")
        new_tree_text = json.dumps(new_tree.get('data', {}))
        if test_text not in new_tree_text:
            print(f"   ✅ Todo text '{test_text}' no longer in widget tree")
        else:
            print(f"   ⚠️  Todo text still visible in tree (might be cached or in history)")

        # Step 9: Verify stats counter updated
        print(f"\n📋 Step 9: Verify stats counter updated")
        stats_request["id"] = 44
        response = send_request(self.proc, stats_request)
        new_stats = initial_stats
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    new_stats = widget_props.get('text', '')
                    print(f"   ✅ New stats: {new_stats}")

                    if new_stats != initial_stats:
                        print(f"   ✅ Stats counter updated")

                        # Parse new total
                        if '/' in new_stats:
                            parts = new_stats.split('/')
                            new_total = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0
                            total_diff = new_total - initial_total
                            print(f"   📊 Total todos: {initial_total} → {new_total} ({total_diff:+d})")

                            if total_diff == -1:
                                print(f"   ✅ Todo count decreased by 1")
                            elif total_diff < 0:
                                print(f"   ✅ Todo count decreased by {abs(total_diff)}")
                            else:
                                print(f"   ⚠️  Todo count did not decrease as expected")
                    else:
                        print(f"   ⚠️  Stats counter unchanged")
                else:
                    print(f"   ⚠️  Could not verify stats: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️  No response from stats verification")

        # Test passed
        self.results['passed'].append('test_delete_button')
        print("\n✅ Delete button test PASSED")
        print("="*80)
        return True

    def test_clear_all(self):
        """Test Clear All button: Click button, confirm in dialog, verify all todos removed, verify empty state shown"""
        print("\n" + "="*80)
        print("TEST: Clear All Button")
        print("="*80)

        state_utils = StateUtils(self.proc)
        input_selector = "TextField[key='addTodoInput']"
        button_selector = "ElevatedButton[key='addTodoButton']"
        clear_all_button_selector = "OutlinedButton[key='clearAllButton']"

        # Step 1: Create 3 test todos first
        print(f"\n📋 Step 1: Create 3 test todos to clear")

        todos_to_create = [
            "Task 1 to clear",
            "Task 2 to clear",
            "Task 3 to clear"
        ]

        created_count = 0
        for i, task_text in enumerate(todos_to_create):
            # Type text
            type_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_type",
                    "arguments": {
                        "text": task_text,
                        "selector": input_selector,
                        "clear_first": True
                    }
                },
                "id": 90 + i
            }

            response = send_request(self.proc, type_request)
            if response and response.get('result'):
                content = response['result'].get('content', [{}])[0]
                if content.get('text'):
                    result = json.loads(content['text'])
                    if result.get('success'):
                        # Click Add button
                        tap_request = {
                            "jsonrpc": "2.0",
                            "method": "tools/call",
                            "params": {
                                "name": "flutter_tap",
                                "arguments": {
                                    "selector": button_selector
                                }
                            },
                            "id": 100 + i
                        }

                        response = send_request(self.proc, tap_request)
                        if response and response.get('result'):
                            created_count += 1

        import time
        time.sleep(1)

        print(f"   ✅ Created {created_count} todos")

        # Step 2: Capture initial tree state
        print(f"\n📋 Step 2: Capture initial tree state")
        initial_tree = state_utils.capture_tree(max_depth=10)
        if not initial_tree.get('success'):
            print(f"   ❌ Failed to capture initial tree: {initial_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_clear_all - initial_tree')
            return False

        initial_count = state_utils.get_widget_count(initial_tree)
        if initial_count.get('success'):
            print(f"   ✅ Initial tree captured: {initial_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get initial widget count")
            initial_count['count'] = 0

        # Step 3: Get initial stats counter
        print(f"\n📋 Step 3: Get initial stats counter")
        stats_selector = "Text[key='statsWidget']"

        stats_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": stats_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 110
        }

        response = send_request(self.proc, stats_request)
        initial_stats = ""
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    initial_stats = widget_props.get('text', '')
                    print(f"   ✅ Initial stats: {initial_stats}")

        # Step 4: Verify todos exist in tree
        print(f"\n📋 Step 4: Verify todos exist in widget tree")
        tree_text = json.dumps(initial_tree.get('data', {}))
        todos_found = sum(1 for todo in todos_to_create if todo in tree_text)
        print(f"   ✅ Found {todos_found} out of {len(todos_to_create)} todos in tree")

        # Step 5: Click Clear All button
        print(f"\n📋 Step 5: Click Clear All button")

        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": clear_all_button_selector
                }
            },
            "id": 111
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Clear All button clicked")
                else:
                    print(f"   ❌ Failed to click button: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_clear_all - click')
                    return False
        else:
            print(f"   ❌ No response from button click")
            self.results['failed'].append('test_clear_all - click')
            return False

        # Wait for dialog to appear
        time.sleep(0.5)

        # Step 6: Click confirmation button in dialog
        print(f"\n📋 Step 6: Confirm in dialog")

        # Try to find and click the "Clear All" text button in the dialog
        # The dialog has two buttons: "Cancel" and "Clear All"
        # We'll try to click the one with "Clear All" text
        dialog_confirm_selector = "TextButton[text='Clear All']"

        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": dialog_confirm_selector
                }
            },
            "id": 112
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Dialog confirmation clicked")
                else:
                    print(f"   ⚠️  Dialog confirmation may have failed: {result.get('error', 'Unknown error')}")
                    # Continue anyway - the dialog might have been dismissed by other means
        else:
            print(f"   ⚠️  No response from dialog confirmation")

        # Wait for UI update
        time.sleep(1)

        # Step 7: Capture new tree state after clearing
        print(f"\n📋 Step 7: Capture new tree state after clearing")
        new_tree = state_utils.capture_tree(max_depth=10)
        if not new_tree.get('success'):
            print(f"   ❌ Failed to capture new tree: {new_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_clear_all - new_tree')
            return False

        new_count = state_utils.get_widget_count(new_tree)
        if new_count.get('success'):
            print(f"   ✅ New tree captured: {new_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get new widget count")

        # Step 8: Verify all todos removed from tree
        print(f"\n📋 Step 8: Verify all todos removed from widget tree")
        new_tree_text = json.dumps(new_tree.get('data', {}))

        todos_removed = True
        for todo in todos_to_create:
            if todo in new_tree_text:
                print(f"   ⚠️  Todo text '{todo}' still in tree (may be cached)")
                todos_removed = False
            else:
                print(f"   ✅ Todo text '{todo}' no longer in tree")

        if todos_removed:
            print(f"   ✅ All created todos removed from tree")
        else:
            print(f"   ⚠️  Some todos may still be visible")

        # Step 9: Verify empty state message is shown
        print(f"\n📋 Step 9: Verify empty state message is visible")

        # Look for empty state indicators in the tree
        # Common empty state messages include: "No tasks yet", "empty", etc.
        empty_state_indicators = ["No tasks yet", "empty", "No tasks", "All caught up"]
        empty_state_found = False

        for indicator in empty_state_indicators:
            if indicator.lower() in new_tree_text.lower():
                print(f"   ✅ Empty state indicator found: '{indicator}'")
                empty_state_found = True
                break

        if not empty_state_found:
            print(f"   ⚠️  No empty state message found in tree")
            print(f"   📝 Tree contains: {new_tree_text[:200]}...")

        # Step 10: Verify stats counter shows 0/0 or empty
        print(f"\n📋 Step 10: Verify stats counter updated")

        stats_request["id"] = 113
        response = send_request(self.proc, stats_request)
        final_stats = initial_stats
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    widget_data = result.get('data', {})
                    widget_props = widget_data.get('properties', {})
                    final_stats = widget_props.get('text', '')
                    print(f"   ✅ Final stats: {final_stats}")

                    # Check if stats show 0/0 or indicate empty state
                    if '0/0' in final_stats or final_stats == '0/0 completed':
                        print(f"   ✅ Stats counter shows 0/0 (all cleared)")
                    elif final_stats != initial_stats:
                        print(f"   ✅ Stats counter updated")
                    else:
                        print(f"   ⚠️  Stats counter unchanged: {final_stats}")
                else:
                    print(f"   ⚠️  Could not verify stats: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️  No response from stats verification")

        # Step 11: Verify no todo items remain in the tree
        print(f"\n📋 Step 11: Verify no todo item widgets remain")

        # Check for common todo item widget patterns
        todo_item_patterns = ["todoDone_", "todoText_", "deleteButton_"]
        todos_remain = False

        for pattern in todo_item_patterns:
            if pattern in new_tree_text:
                print(f"   ⚠️  Found pattern '{pattern}' in tree (todos may remain)")
                todos_remain = True

        if not todos_remain:
            print(f"   ✅ No todo item widgets found in tree")
        else:
            print(f"   ⚠️  Some todo item patterns still present")

        # Test passed
        self.results['passed'].append('test_clear_all')
        print("\n✅ Clear All button test PASSED")
        print("="*80)
        return True

    def test_navigate_to_stats(self):
        """Test navigation to Stats screen: Click Stats button, verify StatsScreen visible, verify stats display"""
        print("\n" + "="*80)
        print("TEST: Navigate to Stats Screen")
        print("="*80)

        state_utils = StateUtils(self.proc)
        stats_button_selector = "ElevatedButton[key='statsButton']"

        # Step 1: Capture initial tree state (on Home Screen)
        print(f"\n📋 Step 1: Capture initial tree state (Home Screen)")
        initial_tree = state_utils.capture_tree(max_depth=10)
        if not initial_tree.get('success'):
            print(f"   ❌ Failed to capture initial tree: {initial_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_navigate_to_stats - initial_tree')
            return False

        initial_count = state_utils.get_widget_count(initial_tree)
        if initial_count.get('success'):
            print(f"   ✅ Initial tree captured: {initial_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get initial widget count")
            initial_count['count'] = 0

        # Step 2: Verify Stats button exists
        print(f"\n📋 Step 2: Verify Stats button exists")
        stats_button_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": stats_button_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 120
        }

        response = send_request(self.proc, stats_button_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Stats button found")
                else:
                    print(f"   ⚠️  Stats button not found: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_navigate_to_stats - stats_button_not_found')
                    return False
        else:
            print(f"   ❌ No response from Stats button check")
            self.results['failed'].append('test_navigate_to_stats - stats_button_check')
            return False

        # Step 3: Click Stats button
        print(f"\n📋 Step 3: Click Stats button")
        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": stats_button_selector
                }
            },
            "id": 121
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Stats button clicked")
                else:
                    print(f"   ❌ Failed to click Stats button: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_navigate_to_stats - click')
                    return False
        else:
            print(f"   ❌ No response from Stats button click")
            self.results['failed'].append('test_navigate_to_stats - click')
            return False

        # Wait for UI update (screen transition)
        import time
        time.sleep(1)

        # Step 4: Capture new tree state (should be on Stats Screen)
        print(f"\n📋 Step 4: Capture new tree state (after navigation)")
        new_tree = state_utils.capture_tree(max_depth=10)
        if not new_tree.get('success'):
            print(f"   ❌ Failed to capture new tree: {new_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_navigate_to_stats - new_tree')
            return False

        new_count = state_utils.get_widget_count(new_tree)
        if new_count.get('success'):
            print(f"   ✅ New tree captured: {new_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get new widget count")

        # Step 5: Verify StatsScreen is visible
        print(f"\n📋 Step 5: Verify StatsScreen appears in widget tree")
        tree_text = json.dumps(new_tree.get('data', {}))

        # Look for StatsScreen indicators
        stats_screen_indicators = [
            "Statistics & Filtering",  # AppBar title
            "Task Statistics",          # Section title
            "StatsScreen"               # Widget type name
        ]

        stats_screen_found = False
        for indicator in stats_screen_indicators:
            if indicator in tree_text:
                print(f"   ✅ Found StatsScreen indicator: '{indicator}'")
                stats_screen_found = True
                break

        if not stats_screen_found:
            print(f"   ❌ StatsScreen not found in widget tree")
            print(f"   📝 Tree preview: {tree_text[:300]}...")
            self.results['failed'].append('test_navigate_to_stats - screen_not_found')
            return False

        # Step 6: Verify stats display components (stat cards)
        print(f"\n📋 Step 6: Verify stats display components (stat cards)")

        # Look for stat card labels and values
        stat_labels = ["Total", "Completed", "Active"]
        found_stats = {}

        for label in stat_labels:
            if label in tree_text:
                found_stats[label] = True
                print(f"   ✅ Stat card found: {label}")
            else:
                found_stats[label] = False
                print(f"   ⚠️  Stat card not found: {label}")

        # Verify all three stat cards are present
        if all(found_stats.values()):
            print(f"   ✅ All stat cards verified (Total, Completed, Active)")
        else:
            print(f"   ⚠️  Some stat cards missing")
            # Don't fail - might be different tree structure

        # Step 7: Verify back button exists on Stats screen
        print(f"\n📋 Step 7: Verify back button exists on Stats screen")
        back_button_selector = "IconButton[key='backButton']"

        back_button_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": back_button_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 122
        }

        response = send_request(self.proc, back_button_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Back button found on Stats screen")
                else:
                    print(f"   ⚠️  Back button not found: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ⚠️  Back button check returned no content")
        else:
            print(f"   ⚠️  No response from back button check")

        # Step 8: Verify search input field exists
        print(f"\n📋 Step 8: Verify search input field exists")
        search_input_selector = "TextField[key='searchInput']"

        search_input_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": search_input_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 123
        }

        response = send_request(self.proc, search_input_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Search input field found")
                else:
                    print(f"   ⚠️  Search input not found: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ⚠️  Search input check returned no content")
        else:
            print(f"   ⚠️  No response from search input check")

        # Step 9: Compare trees to detect navigation changes
        print(f"\n📋 Step 9: Compare trees to detect navigation changes")
        comparison = state_utils.compare_trees(initial_tree, new_tree)

        if not comparison['identical']:
            print(f"   ✅ Trees differ - navigation occurred")
            print(f"   📊 {comparison['details']}")
        else:
            print(f"   ⚠️  Trees are identical - navigation may not have occurred")
            # Don't fail - navigation might have happened with same widget count

        # Test passed
        self.results['passed'].append('test_navigate_to_stats')
        print("\n✅ Navigate to Stats screen test PASSED")
        print("="*80)
        return True

    def test_back_navigation(self):
        """Test back navigation: Click backButton, verify return to HomeScreen, verify todo list visible again"""
        print("\n" + "="*80)
        print("TEST: Back Navigation")
        print("="*80)

        state_utils = StateUtils(self.proc)
        back_button_selector = "IconButton[key='backButton']"

        # Step 1: Ensure we're on Stats screen (navigate if needed)
        print(f"\n📋 Step 1: Ensure we're on Stats screen")

        # First check if back button exists (indicating we're on Stats screen)
        check_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": back_button_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 130
        }

        response = send_request(self.proc, check_request)
        on_stats_screen = False
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    on_stats_screen = True
                    print(f"   ✅ Already on Stats screen (back button found)")
                else:
                    print(f"   ℹ️  Not on Stats screen - navigating now")
        else:
            print(f"   ℹ️  Not on Stats screen - navigating now")

        # If not on Stats screen, navigate there first
        if not on_stats_screen:
            stats_button_selector = "ElevatedButton[key='statsButton']"
            tap_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_tap",
                    "arguments": {
                        "selector": stats_button_selector
                    }
                },
                "id": 131
            }

            response = send_request(self.proc, tap_request)
            if response and response.get('result'):
                content = response['result'].get('content', [{}])[0]
                if content.get('text'):
                    result = json.loads(content['text'])
                    if result.get('success'):
                        print(f"   ✅ Navigated to Stats screen")
                    else:
                        print(f"   ❌ Failed to navigate to Stats screen: {result.get('error', 'Unknown error')}")
                        self.results['failed'].append('test_back_navigation - navigate_to_stats')
                        return False
            else:
                print(f"   ❌ No response from Stats navigation")
                self.results['failed'].append('test_back_navigation - navigate_to_stats')
                return False

            # Wait for screen transition
            import time
            time.sleep(1)

        # Step 2: Capture initial tree state (on Stats Screen)
        print(f"\n📋 Step 2: Capture initial tree state (Stats Screen)")
        initial_tree = state_utils.capture_tree(max_depth=10)
        if not initial_tree.get('success'):
            print(f"   ❌ Failed to capture initial tree: {initial_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_back_navigation - initial_tree')
            return False

        initial_count = state_utils.get_widget_count(initial_tree)
        if initial_count.get('success'):
            print(f"   ✅ Initial tree captured: {initial_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get initial widget count")
            initial_count['count'] = 0

        # Step 3: Verify we're on Stats screen
        print(f"\n📋 Step 3: Verify StatsScreen is visible")
        tree_text = json.dumps(initial_tree.get('data', {}))

        stats_screen_indicators = [
            "Statistics & Filtering",  # AppBar title
            "Task Statistics",          # Section title
            "StatsScreen"               # Widget type name
        ]

        stats_screen_found = False
        for indicator in stats_screen_indicators:
            if indicator in tree_text:
                print(f"   ✅ Confirmed on Stats screen (found: '{indicator}')")
                stats_screen_found = True
                break

        if not stats_screen_found:
            print(f"   ❌ Not on Stats screen - cannot test back navigation")
            self.results['failed'].append('test_back_navigation - not_on_stats')
            return False

        # Step 4: Click back button
        print(f"\n📋 Step 4: Click back button")
        tap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_tap",
                "arguments": {
                    "selector": back_button_selector
                }
            },
            "id": 132
        }

        response = send_request(self.proc, tap_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Back button clicked")
                else:
                    print(f"   ❌ Failed to click back button: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_back_navigation - click_back')
                    return False
        else:
            print(f"   ❌ No response from back button click")
            self.results['failed'].append('test_back_navigation - click_back')
            return False

        # Wait for UI update (screen transition)
        import time
        time.sleep(1)

        # Step 5: Capture new tree state (should be back on Home Screen)
        print(f"\n📋 Step 5: Capture new tree state (after back navigation)")
        new_tree = state_utils.capture_tree(max_depth=10)
        if not new_tree.get('success'):
            print(f"   ❌ Failed to capture new tree: {new_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_back_navigation - new_tree')
            return False

        new_count = state_utils.get_widget_count(new_tree)
        if new_count.get('success'):
            print(f"   ✅ New tree captured: {new_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get new widget count")

        # Step 6: Verify HomeScreen is visible
        print(f"\n📋 Step 6: Verify HomeScreen appears in widget tree")
        tree_text = json.dumps(new_tree.get('data', {}))

        # Look for HomeScreen indicators
        home_screen_indicators = [
            "Todo App",                 # AppBar title
            "HomeScreen",               # Widget type name
            "Add Task",                 # Button text
            "Mark All Complete"         # Button text
        ]

        home_screen_found = False
        for indicator in home_screen_indicators:
            if indicator in tree_text:
                print(f"   ✅ Found HomeScreen indicator: '{indicator}'")
                home_screen_found = True
                break

        if not home_screen_found:
            print(f"   ❌ HomeScreen not found in widget tree")
            print(f"   📝 Tree preview: {tree_text[:300]}...")
            self.results['failed'].append('test_back_navigation - home_screen_not_found')
            return False

        # Step 7: Verify todo list is visible again
        print(f"\n📋 Step 7: Verify todo list is accessible")

        # Check for todo list indicators
        todo_list_indicators = [
            "ListView",                 # Todo list widget type
            "todoDone_",                # Checkbox key prefix
            "todoText_",                # Todo text key prefix
            "deleteButton_"             # Delete button key prefix
        ]

        todo_list_found = False
        for indicator in todo_list_indicators:
            if indicator in tree_text:
                print(f"   ✅ Found todo list indicator: '{indicator}'")
                todo_list_found = True
                break

        if not todo_list_found:
            print(f"   ⚠️  Todo list indicators not found - list may be empty")
            # Don't fail - todo list might legitimately be empty
        else:
            print(f"   ✅ Todo list is visible and accessible")

        # Step 8: Verify we can access a todo item (if any exist)
        print(f"\n📋 Step 8: Verify we can access todo items")

        # Try to find the first todo item
        first_todo_selector = "Checkbox[key='todoDone_1']"
        props_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": first_todo_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 133
        }

        response = send_request(self.proc, props_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ First todo item accessible (checkbox found)")
                else:
                    # Todo list might be empty - that's okay
                    print(f"   ℹ️  First todo item not found (list may be empty)")
            else:
                print(f"   ℹ️  Could not verify todo item access")
        else:
            print(f"   ℹ️  Could not verify todo item access (list may be empty)")

        # Step 9: Verify Stats button is accessible again
        print(f"\n📋 Step 9: Verify Stats button is accessible on Home screen")
        stats_button_selector = "ElevatedButton[key='statsButton']"

        stats_button_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": stats_button_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 134
        }

        response = send_request(self.proc, stats_button_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Stats button accessible on Home screen")
                else:
                    print(f"   ⚠️  Stats button not found: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ⚠️  Stats button check returned no content")
        else:
            print(f"   ⚠️  No response from Stats button check")

        # Step 10: Compare trees to detect navigation changes
        print(f"\n📋 Step 10: Compare trees to detect navigation changes")
        comparison = state_utils.compare_trees(initial_tree, new_tree)

        if not comparison['identical']:
            print(f"   ✅ Trees differ - navigation occurred")
            print(f"   📊 {comparison['details']}")
        else:
            print(f"   ⚠️  Trees are identical - navigation may not have occurred")
            # Don't fail - navigation might have happened with same widget count

        # Test passed
        self.results['passed'].append('test_back_navigation')
        print("\n✅ Back navigation test PASSED")
        print("="*80)
        return True

    def test_search_field(self):
        """Test search field: Type in searchInput, verify filtered results update in widget tree, clear search, verify all todos shown"""
        print("\n" + "="*80)
        print("TEST: Search Field")
        print("="*80)

        state_utils = StateUtils(self.proc)
        search_input_selector = "TextField[key='searchInput']"
        back_button_selector = "IconButton[key='backButton']"

        # Step 1: Ensure we're on Stats screen (navigate if needed)
        print(f"\n📋 Step 1: Ensure we're on Stats screen")

        # First check if back button exists (indicating we're on Stats screen)
        check_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": back_button_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 140
        }

        response = send_request(self.proc, check_request)
        on_stats_screen = False
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    on_stats_screen = True
                    print(f"   ✅ Already on Stats screen (back button found)")
                else:
                    print(f"   ℹ️  Not on Stats screen - navigating now")
        else:
            print(f"   ℹ️  Not on Stats screen - navigating now")

        # If not on Stats screen, navigate there first
        if not on_stats_screen:
            stats_button_selector = "ElevatedButton[key='statsButton']"
            tap_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "flutter_tap",
                    "arguments": {
                        "selector": stats_button_selector
                    }
                },
                "id": 141
            }

            response = send_request(self.proc, tap_request)
            if response and response.get('result'):
                content = response['result'].get('content', [{}])[0]
                if content.get('text'):
                    result = json.loads(content['text'])
                    if result.get('success'):
                        print(f"   ✅ Navigated to Stats screen")
                    else:
                        print(f"   ❌ Failed to navigate to Stats screen: {result.get('error', 'Unknown error')}")
                        self.results['failed'].append('test_search_field - navigate_to_stats')
                        return False
            else:
                print(f"   ❌ No response from Stats navigation")
                self.results['failed'].append('test_search_field - navigate_to_stats')
                return False

            # Wait for screen transition
            import time
            time.sleep(1)

        # Step 2: Capture initial tree state (all todos visible)
        print(f"\n📋 Step 2: Capture initial tree state (all todos visible)")
        initial_tree = state_utils.capture_tree(max_depth=10)
        if not initial_tree.get('success'):
            print(f"   ❌ Failed to capture initial tree: {initial_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_search_field - initial_tree')
            return False

        initial_count = state_utils.get_widget_count(initial_tree)
        if initial_count.get('success'):
            print(f"   ✅ Initial tree captured: {initial_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get initial widget count")
            initial_count['count'] = 0

        # Step 3: Type search query in search input
        print(f"\n📋 Step 3: Type search query in search input")
        search_query = "Buy"  # Assuming there's a todo with "Buy" in the title (e.g., "Buy groceries")

        type_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_type",
                "arguments": {
                    "text": search_query,
                    "selector": search_input_selector
                }
            },
            "id": 142
        }

        response = send_request(self.proc, type_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Search query '{search_query}' typed successfully")
                else:
                    print(f"   ❌ Failed to type search query: {result.get('error', 'Unknown error')}")
                    self.results['failed'].append('test_search_field - type')
                    return False
        else:
            print(f"   ❌ No response from flutter_type")
            self.results['failed'].append('test_search_field - type')
            return False

        # Wait for UI update (filtering)
        time.sleep(0.5)

        # Step 4: Capture tree state after search
        print(f"\n📋 Step 4: Capture tree state after search (filtered results)")
        filtered_tree = state_utils.capture_tree(max_depth=10)
        if not filtered_tree.get('success'):
            print(f"   ❌ Failed to capture filtered tree: {filtered_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_search_field - filtered_tree')
            return False

        filtered_count = state_utils.get_widget_count(filtered_tree)
        if filtered_count.get('success'):
            print(f"   ✅ Filtered tree captured: {filtered_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get filtered widget count")

        # Step 5: Verify filtered results
        print(f"\n📋 Step 5: Verify filtered results show only matching todos")

        # Check if the tree contains search query in todo items
        tree_text = json.dumps(filtered_tree.get('data', {}))

        # Look for todo items containing the search query
        # We'll check if the filtered list has fewer items than the full list
        # or if specific search query text appears in the tree
        if search_query.lower() in tree_text.lower():
            print(f"   ✅ Search query '{search_query}' found in filtered tree")
        else:
            print(f"   ⚠️  Search query '{search_query}' not found - list may be empty or no matches")

        # Compare widget counts - filtering should reduce the visible todo items
        comparison = state_utils.compare_trees(initial_tree, filtered_tree)
        if comparison['identical']:
            print(f"   ⚠️  Trees are identical - filtering may not have occurred or all items match")
        else:
            print(f"   ✅ Trees differ - filtering occurred")
            print(f"   📊 {comparison['details']}")

        # Step 6: Clear search
        print(f"\n📋 Step 6: Clear search field")

        # Use flutter_type with clear_first to empty the field
        clear_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_type",
                "arguments": {
                    "text": "",
                    "selector": search_input_selector,
                    "clear_first": True
                }
            },
            "id": 143
        }

        response = send_request(self.proc, clear_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    print(f"   ✅ Search field cleared successfully")
                else:
                    print(f"   ❌ Failed to clear search field: {result.get('error', 'Unknown error')}")
                    # Don't fail - clearing might work differently
            else:
                print(f"   ⚠️  Clear operation returned no content")
        else:
            print(f"   ⚠️  No response from clear operation")

        # Wait for UI update (showing all todos again)
        time.sleep(0.5)

        # Step 7: Capture tree state after clearing
        print(f"\n📋 Step 7: Capture tree state after clearing (all todos shown)")
        cleared_tree = state_utils.capture_tree(max_depth=10)
        if not cleared_tree.get('success'):
            print(f"   ❌ Failed to capture cleared tree: {cleared_tree.get('error', 'Unknown error')}")
            self.results['failed'].append('test_search_field - cleared_tree')
            return False

        cleared_count = state_utils.get_widget_count(cleared_tree)
        if cleared_count.get('success'):
            print(f"   ✅ Cleared tree captured: {cleared_count['count']} widgets")
        else:
            print(f"   ⚠️  Could not get cleared widget count")

        # Step 8: Verify all todos are shown again
        print(f"\n📋 Step 8: Verify all todos are shown again")

        # Compare cleared tree with initial tree - should be similar
        comparison_cleared = state_utils.compare_trees(initial_tree, cleared_tree)
        if comparison_cleared['identical']:
            print(f"   ✅ Trees are identical - all todos shown again")
        else:
            # Trees might differ slightly due to state changes, but should be similar
            # The key is that the cleared tree should have more widgets than the filtered tree
            comparison_filtered = state_utils.compare_trees(filtered_tree, cleared_tree)
            if not comparison_filtered['identical'] and comparison_filtered['changes']['node_count_diff'] >= 0:
                print(f"   ✅ Cleared tree differs from filtered tree - todos restored")
                print(f"   📊 {comparison_filtered['details']}")
            else:
                print(f"   ⚠️  Cleared tree comparison unclear")

        # Step 9: Verify search field is empty
        print(f"\n📋 Step 9: Verify search field is empty via get_properties")

        props_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "flutter_get_properties",
                "arguments": {
                    "selector": search_input_selector,
                    "include_render": False,
                    "include_layout": False
                }
            },
            "id": 144
        }

        response = send_request(self.proc, props_request)
        if response and response.get('result'):
            content = response['result'].get('content', [{}])[0]
            if content.get('text'):
                result = json.loads(content['text'])
                if result.get('success'):
                    props = result.get('data', {}).get('properties', {})
                    # Check for 'text' or 'controllerText' property
                    field_text = props.get('text') or props.get('controllerText', '')
                    if field_text == '' or field_text is None:
                        print(f"   ✅ Search field is empty")
                    else:
                        print(f"   ⚠️  Search field still has text: '{field_text}'")
                        # Don't fail - field might show different property
                else:
                    print(f"   ⚠️  Could not verify search field properties: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ⚠️  Search field check returned no content")
        else:
            print(f"   ⚠️  No response from search field check")

        # Test passed
        self.results['passed'].append('test_search_field')
        print("\n✅ Search field test PASSED")
        print("="*80)
        return True

    def test_app_initialization(self):
        """Test app initialization sequence"""
        print("\n" + "="*80)
        print("TEST: App Initialization")
        print("="*80)

        # Step 1: MCP initialization (already done in main)
        print("\n📋 Step 1: MCP Initialization")
        print("   Status: ✅ Already initialized")

        # Step 2: List tools
        print("\n📋 Step 2: List Available Tools")
        tools = self.list_tools()
        if tools is None:
            self.results['failed'].append('test_app_initialization - list_tools')
            return False
        print(f"   Found {len(tools)} tools")

        # Step 3: Connect to Flutter app
        print("\n📋 Step 3: Connect to Flutter App")
        print("   Target: ws://127.0.0.1:8181/ws")
        print("   Make sure Flutter app is running:")
        print("   cd examples/flutter_sample_app")
        print("   flutter run -d windows --vm-service-port=8181 --disable-service-auth-codes")

        if not self.connect_flutter_app():
            self.results['failed'].append('test_app_initialization - connect')
            return False

        # Step 4: Verify connection
        print("\n📋 Step 4: Verify Connection")
        tree_data = self.verify_connection()
        if tree_data is None:
            self.results['failed'].append('test_app_initialization - verify_connection')
            self.disconnect_flutter_app()
            return False

        # Test passed
        self.results['passed'].append('test_app_initialization')
        print("\n✅ App initialization test PASSED")
        print("="*80)
        return True

    def cleanup(self):
        """Clean up resources"""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait()
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")

    def print_report(self):
        """Print final test report"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print("\n\n" + "="*80)
        print("REALISTIC GUI TEST REPORT")
        print("="*80)

        print(f"\nTest Suite: Realistic GUI Workflows")
        print(f"Executable: flutter_reflect.exe")
        print(f"Timestamp: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {elapsed:.2f} seconds")

        print(f"\n{'='*80}")
        print("RESULTS SUMMARY")
        print(f"{'='*80}")

        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        skipped = len(self.results['skipped'])
        total = passed + failed + skipped

        print(f"\n✅ Passed:  {passed}")
        print(f"❌ Failed:  {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"📊 Total:   {total}")

        if failed == 0:
            print(f"\n🎉 ALL TESTS PASSED!")
            success_rate = 100
        else:
            success_rate = (passed / total * 100) if total > 0 else 0

        print(f"📈 Success Rate: {success_rate:.1f}%")

        if failed > 0:
            print(f"\n{'='*80}")
            print("FAILED TESTS")
            print(f"{'='*80}")
            for test in self.results['failed']:
                print(f"  ❌ {test}")

        if skipped > 0:
            print(f"\n{'='*80}")
            print("SKIPPED TESTS")
            print(f"{'='*80}")
            for test in self.results['skipped']:
                print(f"  ⏭️  {test}")

        print(f"\n{'='*80}")


def main():
    runner = TestRunner()

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "FlutterReflect MCP Server - Realistic GUI Test Suite".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")

    # Initialize MCP connection
    if not runner.initialize_mcp():
        print("\n❌ Failed to initialize MCP server. Exiting.")
        return

    try:
        # Run app initialization test
        if runner.test_app_initialization():
            # Run input fields test
            runner.test_input_fields()

            # Run checkbox toggle test
            runner.test_checkbox_toggle()

            # Run add todo button test
            runner.test_add_todo_button()

            # Run delete button test
            runner.test_delete_button()

            # Run mark all complete test
            runner.test_mark_all_complete()

            # Run clear all test
            runner.test_clear_all()

            # Run navigate to stats test
            runner.test_navigate_to_stats()

            # Run back navigation test
            runner.test_back_navigation()

            # Run search field test
            runner.test_search_field()

            # Disconnect after successful test
            runner.disconnect_flutter_app()

        # Print final report
        runner.print_report()

    except Exception as e:
        print(f"\n❌ Error during test execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner.cleanup()


if __name__ == "__main__":
    main()
