# Specification: Create Realistic Test Cases for Flutter Sample App

## Overview

Create comprehensive GUI-based tests for the Flutter sample todo app that simulate realistic human interaction patterns. The tests will initialize the app, systematically interact with ALL UI components across both Home and Stats screens, verify each interaction occurred successfully, and detect UI state changes resulting from those interactions. This approach differs from traditional Flutter widget testing by performing actual GUI interactions through the FlutterReflect MCP server infrastructure, enabling detection of UI/UX issues invisible to conventional testing methods in the Flutter ecosystem.

## Workflow Type

**Type**: feature

**Rationale**: This is a new feature implementation - creating a comprehensive test suite that demonstrates GUI-based testing capabilities. The task requires building new test orchestration logic, verification mechanisms, and change detection systems on top of existing infrastructure (server, CLI commands, MCP tools).

## Task Scope

### Services Involved
- **FlutterReflect Server** (primary) - C++ MCP server providing interaction tools (connect, tap, type, scroll, get_tree, get_properties)
- **Flutter Sample App** (integration) - Todo app serving as the test subject with Home and Stats screens

### This Task Will:
- [ ] Create comprehensive test suite covering ALL UI components in the sample app
- [ ] Implement app initialization sequence (connect via VM Service, verify app is ready)
- [ ] Test all interactive components systematically (buttons, inputs, checkboxes, navigation)
- [ ] Implement verification logic for each interaction type (confirm interaction occurred)
- [ ] Implement change detection logic (compare pre/post interaction UI states)
- [ ] Ensure tests follow human-like interaction patterns (realistic delays, sequential actions)
- [ ] Document all tested components and expected behaviors

### Out of Scope:
- Building new FlutterReflect tools (use existing: connect, disconnect, get_tree, tap, type, scroll, get_properties, find)
- Modifying the sample app (use existing app as-is)
- Creating automated test generation framework (this is a manual test suite)
- Performance benchmarking or load testing
- Testing on multiple Flutter platforms (Windows Desktop only for now)

## Service Context

### FlutterReflect Server

**Tech Stack:**
- Language: C++
- Framework: Custom MCP (Model Context Protocol) server
- Build System: CMake
- Key dependencies: nlohmann/json, websocketpp, asio, spdlog

**Entry Point:** `src/main.cpp` → `flutter_reflect.exe`

**How to Run:**
```bash
# Build
cmake --build build --config Debug

# Run server
./build/Debug/flutter_reflect.exe --log-level info
```

**Port:** N/A (communicates via STDIO with MCP client, connects to Flutter app via VM Service WebSocket on port 8181)

**Available MCP Tools:**
- `flutter_connect` - Connect to Flutter app via VM Service WebSocket
- `flutter_disconnect` - Disconnect from Flutter app
- `flutter_get_tree` - Extract widget tree snapshot
- `flutter_get_properties` - Get properties of specific widget
- `flutter_find` - Find widgets by selector
- `flutter_tap` - Tap on widget (by selector, widget_id, or coordinates)
- `flutter_type` - Type text into input field
- `flutter_scroll` - Scroll a widget
- `flutter_list_instances` - List Flutter VM instances
- `flutter_launch` - Launch Flutter app

### Flutter Sample App

**Tech Stack:**
- Language: Dart
- Framework: Flutter 3.x
- Type: Desktop application (Windows)

**Entry Point:** `examples/flutter_sample_app/lib/main.dart`

**How to Run:**
```bash
cd examples/flutter_sample_app
flutter run -d windows --vm-service-port=8181 --disable-service-auth-codes
```

**Port:** VM Service on 8181 (WebSocket endpoint: `ws://127.0.0.1:8181/ws`)

**App Structure:**
- **Home Screen** (`lib/screens/home_screen.dart`): Main todo list with add/delete/complete functionality
- **Stats Screen** (`lib/screens/stats_screen.dart`): Statistics display with filtering and search
- **Key-Identified Components:** All interactive widgets have unique keys defined in `lib/utils/constants.dart`

## Files to Modify

| File | Service | What to Change |
|------|---------|----------------|
| `[NEW] test_realistic_gui_suite.py` | Test Suite | Create comprehensive test file with all realistic GUI tests |
| `[NEW] docs/realistic_test_report.md` | Documentation | Document test results and coverage |

## Files to Reference

These files show patterns to follow:

| File | Pattern to Copy |
|------|----------------|
| `test_comprehensive_suite.py` | Test runner structure, MCP JSON-RPC communication patterns |
| `test_get_tree.py` | Connection sequence, tree extraction, error handling |
| `src/tools/tap_tool.cpp` | Understanding how tap interaction works (selector, widget_id, coordinates) |
| `examples/flutter_sample_app/lib/utils/constants.dart` | Widget keys for targeting specific UI components |
| `examples/flutter_sample_app/lib/screens/home_screen.dart` | Home screen UI structure and interaction feedback |
| `examples/flutter_sample_app/lib/screens/stats_screen.dart` | Stats screen UI structure and navigation |

## Patterns to Follow

### Test Communication Pattern

From `test_get_tree.py`:

```python
def send_request(proc, request):
    """Send a JSON-RPC request and get response"""
    request_str = json.dumps(request) + '\n'
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()

    response_line = proc.stdout.readline().decode().strip()
    if response_line:
        response = json.loads(response_line)
        return response
    return None
```

**Key Points:**
- Always send JSON-RPC 2.0 compliant requests
- Include newline after JSON (MCP protocol requirement)
- Flush stdin after writing to ensure immediate delivery
- Parse response with error handling
- Use subprocess for MCP server communication

### Connection and Tool Initialization Pattern

From `test_comprehensive_suite.py` and `test_get_tree.py`:

```python
# 1. Initialize MCP
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

# 2. List available tools
tools_response = send_request(proc, {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 2
})

# 3. Connect to Flutter app
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
```

**Key Points:**
- Always initialize MCP connection first
- Verify tools are available before use
- Connect to Flutter app before any interaction
- Check for errors in each response
- Use sequential IDs for request tracking

### Widget Key Targeting Pattern

From `examples/flutter_sample_app/lib/utils/constants.dart`:

```dart
class WidgetKeys {
  static const String addTodoInput = 'addTodoInput';
  static const String addTodoButton = 'addTodoButton';
  static const String deleteButtonPrefix = 'deleteButton_';
  static const String todoDonePrefix = 'todoDone_';
  static const String statsButton = 'statsButton';
  // ... more keys
}
```

**Key Points:**
- All interactive widgets have unique keys
- Use these keys for selector-based targeting
- Some keys are prefixes (deleteButton_, todoDone_) + todo ID
- Keys organized by component type (input, button, list, etc.)

### State Change Detection Pattern

From existing test patterns and Flutter inspector protocol:

```python
# Get widget tree before interaction
before_tree = send_request(proc, {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "flutter_get_tree",
        "arguments": {}
    },
    "id": 1
})

# Perform interaction
send_request(proc, {...tap interaction...})

# Get widget tree after interaction
after_tree = send_request(proc, {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "flutter_get_tree",
        "arguments": {}
    },
    "id": 2
})

# Compare trees to detect changes
# Check for: new widgets, removed widgets, property changes
```

**Key Points:**
- Capture state before interaction
- Perform interaction
- Capture state after interaction
- Compare snapshots to detect changes
- Look for expected property/state changes

## Requirements

### Functional Requirements

1. **App Initialization**
   - Description: Connect FlutterReflect server to running Flutter sample app via VM Service, verify app is responsive, capture initial UI state
   - Acceptance: Connection successful, get_tree returns valid widget tree with HomeScreen visible, stats widget shows initial count (5/5 for sample todos)

2. **Input Field Testing**
   - Description: Test text input in add todo field (Home Screen) and search field (Stats Screen). Type text, verify text appears, clear text, verify field is empty
   - Acceptance: flutter_type tool successfully enters text, get_properties shows text field value updated, visual feedback shows entered text, clear operation empties field

3. **Button Click Testing**
   - Description: Test all button interactions: Add Task, Stats, Mark All Complete, Clear All, Back (on Stats screen), Delete (for each todo item), Filter buttons (All/Active/Completed)
   - Acceptance: Each button responds to tap, expected action occurs (e.g., clicking Add Task adds new todo, clicking Delete removes todo), visual feedback appears (toast/snackbar message)

4. **Checkbox Testing**
   - Description: Test todo item checkboxes. Click checkbox to toggle completion state, verify text decoration changes (strikethrough when complete), verify stats counter updates
   - Acceptance: Tap on checkbox toggles isCompleted state, todo text shows strikethrough decoration when completed, stats widget (X/5) updates count

5. **Navigation Testing**
   - Description: Test screen navigation. Click Stats button to navigate to StatsScreen, verify transition, click Back button to return to HomeScreen, verify return
   - Acceptance: flutter_tap on Stats button triggers navigation, StatsScreen becomes visible with stats display, Back button returns to HomeScreen, todos list visible again

6. **List Interaction Testing**
   - Description: Test scrolling through todo list if items exceed viewport, verify all items accessible, test scroll position changes
   - Acceptance: flutter_scroll can move through list, all todo items accessible via scrolling, scroll position changes detectable in tree properties

7. **State Change Detection**
   - Description: For each interaction, detect and verify UI state changes. Compare pre/post widget trees to confirm expected changes occurred
   - Acceptance: get_tree shows differences after interaction (e.g., new todo item appears, counter updates, item removed), property changes detected (isCompleted, text values), no unexpected state changes

8. **Error Handling**
   - Description: Test error scenarios. Tap on non-existent widget, type in disabled field, attempt invalid operations, verify graceful error handling
   - Acceptance: Invalid interactions return error messages, app remains stable, no crashes, error messages are descriptive

### Edge Cases

1. **Empty State Handling** - Test interactions when todo list is empty (e.g., Clear All then try Mark All Complete, verify no errors, appropriate feedback message)
2. **Rapid Interactions** - Test multiple rapid taps on same button, verify only one action occurs (debouncing), no duplicate todos added
3. **Long Text Input** - Test entering very long task names, verify text field handles it, no truncation issues, todo item displays correctly
4. **Special Characters** - Test input with special characters, emojis, unicode, verify proper handling and display
5. **Dialog Interactions** - Test confirmation dialog (Clear All shows confirmation), verify both Cancel and Clear All actions work
6. **Filter State Persistence** - Test filter selection on Stats screen, navigate away and back, verify filter state persists or resets appropriately
7. **Concurrent Operations** - Test operations that affect same data (e.g., toggle and delete same todo rapidly), verify no race conditions

## Implementation Notes

### DO
- Use widget keys for precise targeting (defined in `lib/utils/constants.dart`)
- Follow the existing test communication pattern from `test_get_tree.py` and `test_comprehensive_suite.py`
- Implement proper sequential test execution (one test completes before next starts)
- Add realistic delays between interactions (100-500ms) to simulate human behavior
- Capture and log pre/post interaction states for debugging
- Use try-except blocks for error handling and recovery
- Verify each interaction before proceeding to next
- Clean up state between tests (e.g., restore todo list to initial state)
- Use descriptive test names indicating what component is being tested
- Log all interactions and results for comprehensive test report

### DON'T
- Don't create new MCP tools (all needed tools exist: connect, get_tree, tap, type, scroll, get_properties, find)
- Don't modify the sample app code (use as-is)
- Don't skip verification steps (always confirm interaction occurred)
- Don't ignore error responses (handle and log them)
- Don't assume widgets exist (verify presence before interaction)
- Don't hardcode widget IDs (use keys from constants.dart when possible)
- Don't run tests in parallel (Flutter app state can get corrupted)
- Don't forget to disconnect from Flutter app after tests complete
- Don't rely on sleep delays for state verification (use polling or explicit state checks)

## Development Environment

### Start Services

**Terminal 1 - Start Flutter Sample App:**
```bash
cd examples/flutter_sample_app
flutter run -d windows --vm-service-port=8181 --disable-service-auth-codes
```

Wait for output showing: `A Dart VM Service on Windows is available at: http://127.0.0.1:8181/`

**Terminal 2 - Run Realistic Test Suite:**
```bash
cd E:\dev\FlutterReflect
python test_realistic_gui_suite.py
```

### Service URLs
- Flutter VM Service WebSocket: `ws://127.0.0.1:8181/ws`
- FlutterReflect MCP Server: Communicates via STDIO (subprocess)

### Required Environment Variables
- None (all paths are relative or configured in test script)

## Success Criteria

The task is complete when:

1. **Comprehensive Test Coverage**: All UI components in both Home and Stats screens are tested
2. **Successful Interaction Verification**: Every test includes verification that interaction occurred (e.g., get_properties shows change, get_tree shows new/modified widgets)
3. **State Change Detection**: Each test demonstrates ability to detect UI changes before/after interaction using widget tree comparison
4. **Realistic Interaction Patterns**: Tests follow human-like interaction sequences with appropriate delays and sequential operations
5. **Error Handling**: Tests demonstrate proper error handling for edge cases and invalid operations
6. **Documentation**: Test report documents all tested components, interactions performed, and results
7. **Reproducibility**: Tests can be run multiple times with consistent results (proper cleanup between tests)
8. **No App Crashes**: Flutter app remains stable throughout all test interactions
9. **All Tests Pass**: 100% of tests pass successfully without manual intervention

## QA Acceptance Criteria

**CRITICAL**: These criteria must be verified by the QA Agent before sign-off.

### Unit Tests
| Test | File | What to Verify |
|------|------|----------------|
| Connection Test | `test_realistic_gui_suite.py::test_app_initialization` | Flutter app connects successfully, initial tree captured |
| Input Test | `test_realistic_gui_suite.py::test_input_fields` | Text typing works in both add and search fields |
| Button Test | `test_realistic_gui_suite.py::test_all_buttons` | All 20+ interactive buttons respond to taps |
| Checkbox Test | `test_realistic_gui_suite.py::test_checkboxes` | Checkbox toggles work, state changes detected |
| Navigation Test | `test_realistic_gui_suite.py::test_navigation` | Screen navigation (Home ↔ Stats) works bidirectionally |

### Integration Tests
| Test | Services | What to Verify |
|------|----------|----------------|
| Full Workflow Test | FlutterReflect ↔ Flutter App | Complete user journey: add todos, navigate, filter, mark complete, delete |
| State Persistence Test | FlutterReflect ↔ Flutter App | Changes persist across screen navigation |
| Error Recovery Test | FlutterReflect ↔ Flutter App | App recovers gracefully from invalid operations |

### End-to-End Tests
| Flow | Steps | Expected Outcome |
|------|-------|------------------|
| Add Todo Flow | 1. Type in add field 2. Click Add button 3. Verify new todo appears in list 4. Verify counter updates | New todo created, visible in list, stats counter shows 6/5 |
| Complete Todo Flow | 1. Click checkbox on todo 2. Verify strikethrough appears 3. Verify stats counter updates | Todo marked complete, visual feedback, counter shows 5/5 or 4/5 |
| Navigate and Filter Flow | 1. Click Stats button 2. Click "Completed" filter 3. Verify only completed todos shown 4. Click Back 5. Verify return to home | Navigation works, filter shows correct subset, back button returns |
| Delete Todo Flow | 1. Click delete button on todo 2. Confirm in dialog 3. Verify todo removed from list 4. Verify counter updates | Todo deleted, list updated, counter decrements |
| Clear All Flow | 1. Click Clear All button 2. Confirm in dialog 3. Verify all todos removed 4. Verify empty state shown | All todos deleted, empty state message appears |

### Browser Verification (if applicable)
| Page/Component | URL | Checks |
|----------------|-----|--------|
| N/A | N/A | N/A (Windows Desktop app, not web-based) |

### Database Verification (if applicable)
| Check | Query/Command | Expected |
|-------|---------------|----------|
| N/A | N/A | N/A (In-memory state, no database) |

### UI Component Inventory
Must verify ALL components below are tested:

**Home Screen Components (18 items):**
1. ✓ Add todo input field (`addTodoInput`)
2. ✓ Add todo button (`addTodoButton`)
3. ✓ Stats button (`statsButton`)
4. ✓ Mark all complete button (`markAllCompleteButton`)
5. ✓ Clear all button (`clearAllButton`)
6. ✓ Stats widget display (`statsWidget`)
7. ✓ Todo list view (`todoListView`)
8. ✓ Todo item checkboxes (5 items: `todoDone_{id}`)
9. ✓ Todo item text labels (5 items: `todoText_{id}`)
10. ✓ Delete buttons (5 items: `deleteButton_{id}`)
11. ✓ Todo item tap targets (5 items: `todoItem_{id}`)

**Stats Screen Components (12 items):**
12. ✓ Back button (`backButton`)
13. ✓ Search input field (`searchInput`)
14. ✓ Filter bar container (`filterBar`)
15. ✓ Show all button (`showAllButton`)
16. ✓ Show active button (`showActiveButton`)
17. ✓ Show completed button (`showCompletedButton`)
18. ✓ Filtered list view (`filteredListView`)
19. ✓ Stat card: Total
20. ✓ Stat card: Completed
21. ✓ Stat card: Active
22. ✓ Progress bar
23. ✓ Interaction log widget (`interactionLog`)

### QA Sign-off Requirements
- [ ] All unit tests pass (5/5 tests)
- [ ] All integration tests pass (3/3 tests)
- [ ] All E2E tests pass (5/5 flows)
- [ ] All 23 UI components tested and verified
- [ ] State change detection working for all interaction types
- [ ] No regressions in existing FlutterReflect tools
- [ ] Tests reproduce consistently on multiple runs
- [ ] Test report is comprehensive and actionable
- [ ] Error handling verified for all edge cases
- [ ] App stability confirmed (no crashes during tests)
- [ ] Code follows established test patterns from `test_get_tree.py`
- [ ] Widget keys from `constants.dart` properly utilized
- [ ] No security vulnerabilities introduced
