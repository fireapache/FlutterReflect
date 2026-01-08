# FlutterReflect Tool Testing Guide

Comprehensive testing guide for each of the 10 FlutterReflect tools with the sample Flutter app.

**Date:** December 19, 2025
**Sample App Location:** `examples/flutter_sample_app/`
**Build Status:** ✅ Ready for testing

---

## Prerequisites

1. **Flutter SDK** installed and in PATH
2. **FlutterReflect executable** built: `build/Debug/flutter_reflect.exe`
3. **Sample app** ready: `examples/flutter_sample_app/`

### Setup

```bash
# Terminal 1: Start the sample app
cd examples/flutter_sample_app
flutter run

# Terminal 2: Run FlutterReflect tests
# (Will connect to the running app)
```

---

## Tool 1: list_instances 🔍

### Purpose
Discover running Flutter applications without manual configuration.

### What It Tests
- Network scanning for Flutter VM Service ports
- Port range configuration
- Instance discovery and metadata extraction

### Test Cases

#### Test 1.1: Default Port Range
```bash
flutter_reflect list_instances --port-start 8080 --port-end 8200
```

**Expected Output:**
- JSON response with discovered instances
- Instance URI, port, project name, device type
- Connection status for each instance

**Sample Response:**
```json
{
  "success": true,
  "instances": [
    {
      "port": 8181,
      "uri": "ws://localhost:8181/abc123...",
      "projectName": "flutter_sample_app",
      "deviceType": "android|ios|windows|web",
      "status": "connected"
    }
  ]
}
```

#### Test 1.2: Custom Port Range
```bash
flutter_reflect list_instances --port-start 8100 --port-end 8300
```

**Expected:** Discovers app on custom range

#### Test 1.3: Narrow Range
```bash
flutter_reflect list_instances --port-start 8180 --port-end 8182
```

**Expected:** Finds instance within narrow range

#### Test 1.4: Timeout Configuration
```bash
flutter_reflect list_instances --port-start 8080 --port-end 8200 --timeout-ms 1000
```

**Expected:** Completes within reasonable time

### Success Criteria
- ✅ App discovered with correct port
- ✅ Metadata includes project name
- ✅ URI is valid WebSocket format
- ✅ Handles multiple apps correctly

### Performance Notes
- Default timeout: 500ms per port
- Range 8080-8200 scans ~120 ports
- Total time: ~60 seconds

---

## Tool 2: launch 🚀

### Purpose
Launch Flutter apps programmatically and monitor startup.

### What It Tests
- Flutter project compilation and execution
- VM Service port allocation
- Startup progress monitoring
- App readiness detection

### Test Cases

#### Test 2.1: Launch with Project Path
```bash
flutter_reflect launch --project-path E:\C++\FlutterReflect\examples\flutter_sample_app
```

**Expected Output:**
```json
{
  "success": true,
  "app_uri": "ws://localhost:8181/abc...",
  "port": 8181,
  "startup_time_ms": 5000,
  "status": "ready"
}
```

**Verification:**
- ✅ App launches and starts
- ✅ VM Service becomes available
- ✅ Returns valid URI
- ✅ Status shows "ready"

#### Test 2.2: Custom VM Service Port
```bash
flutter_reflect launch --project-path ./flutter_sample_app --vm-service-port 8500
```

**Expected:** App launches on specified port

#### Test 2.3: Device Selection
```bash
flutter_reflect launch --project-path ./flutter_sample_app --device emulator-5554
```

**Expected:** Launches on specified device

#### Test 2.4: Startup Timeout
```bash
flutter_reflect launch --project-path ./flutter_sample_app --startup-timeout 120
```

**Expected:** Waits up to 120 seconds for startup

### Success Criteria
- ✅ App compiles without errors
- ✅ VM Service becomes available
- ✅ Correct port reported
- ✅ Returns valid WebSocket URI
- ✅ App state shows "ready"

---

## Tool 3: connect 🔗

### Purpose
Establish WebSocket connection to Flutter VM Service.

### What It Tests
- WebSocket protocol handling
- Connection state management
- Auto-discovery capability
- Authentication (if needed)

### Test Cases

#### Test 3.1: Connect via URI
```bash
flutter_reflect connect --uri ws://localhost:8181/abc123def456
```

**Expected:**
```json
{
  "success": true,
  "connected": true,
  "uri": "ws://localhost:8181/abc123def456",
  "app_name": "flutter_sample_app"
}
```

#### Test 3.2: Auto-Discovery
```bash
flutter_reflect connect
```

**Expected:**
- Auto-discovers first running Flutter app
- Connects without manual URI
- Returns connection details

#### Test 3.3: Auto-Discovery with Port Filter
```bash
flutter_reflect connect --port 8181
```

**Expected:** Discovers app on specified port

#### Test 3.4: Project Name Filter
```bash
flutter_reflect connect --project-name flutter_sample_app
```

**Expected:** Connects to app matching project name

#### Test 3.5: Instance Index Selection
```bash
flutter_reflect connect --instance-index 0
```

**Expected:** Connects to first instance

### Success Criteria
- ✅ WebSocket connection established
- ✅ Connection state tracked
- ✅ Auto-discovery works without URI
- ✅ Filtering options work
- ✅ Returns app metadata

### Connection Persistence
- Once connected, subsequent tool calls maintain connection
- Connection remains active until `disconnect` is called
- Automatic reconnection on temporary failures

---

## Tool 4: disconnect 🔌

### Purpose
Clean disconnection from Flutter app with resource cleanup.

### What It Tests
- Graceful connection termination
- Resource cleanup
- State reset

### Test Cases

#### Test 4.1: Disconnect After Connect
```bash
# First connect
flutter_reflect connect

# Then disconnect
flutter_reflect disconnect
```

**Expected:**
```json
{
  "success": true,
  "message": "Disconnected from Flutter app"
}
```

#### Test 4.2: Disconnect Without Prior Connection
```bash
flutter_reflect disconnect
```

**Expected:**
- Should handle gracefully
- Return success (idempotent)

#### Test 4.3: Reconnect After Disconnect
```bash
flutter_reflect connect
flutter_reflect disconnect
flutter_reflect connect  # Should reconnect successfully
```

**Expected:** Reconnection succeeds

### Success Criteria
- ✅ Disconnects gracefully
- ✅ Resources cleaned up
- ✅ Idempotent (safe to call multiple times)
- ✅ Allows reconnection

---

## Tool 5: get_tree 🌳

### Purpose
Retrieve complete widget tree hierarchy for inspection.

### What It Tests
- Widget tree traversal
- Tree serialization
- Depth limiting
- Output formatting (text/JSON)

### Test Cases

#### Test 5.1: Full Tree
```bash
flutter_reflect get_tree
```

**Expected:** Complete widget hierarchy from root

#### Test 5.2: Limited Depth
```bash
flutter_reflect get_tree --max-depth 3
```

**Expected:** Tree truncated at depth 3

#### Test 5.3: JSON Format
```bash
flutter_reflect get_tree --max-depth 5 --format json
```

**Expected:** Structured JSON output

**Sample Output:**
```json
{
  "success": true,
  "tree": {
    "type": "Scaffold",
    "key": "home_screen",
    "children": [
      {
        "type": "AppBar",
        "properties": {...}
      },
      {
        "type": "ListView",
        "key": "todoListView",
        "children": [...]
      }
    ]
  }
}
```

#### Test 5.4: Text Format
```bash
flutter_reflect get_tree --max-depth 3 --format text
```

**Expected:** Indented tree view in text format

### Widget Tree Navigation

After `get_tree`, use returned widget IDs with other tools:

```bash
# Get tree
flutter_reflect get_tree --max-depth 2

# Get properties of specific widget using ID
flutter_reflect get_properties --widget-id "todoListView"
```

### Success Criteria
- ✅ All widgets returned
- ✅ Correct hierarchy
- ✅ Depth limiting works
- ✅ JSON valid and parseable
- ✅ Text format readable

---

## Tool 6: find 🔎

### Purpose
Locate widgets using CSS-like selector syntax.

### What It Tests
- Selector parsing
- Widget matching logic
- Pattern matching variations
- Multi-match scenarios

### Test Cases

#### Test 6.1: Find by Type
```bash
flutter_reflect find --selector "Button"
```

**Expected:** All Button widgets found

#### Test 6.2: Find by Text
```bash
flutter_reflect find --selector "Text[text='Add Task']"
```

**Expected:** Text widget with exact match

#### Test 6.3: Find by Contains
```bash
flutter_reflect find --selector "Text[contains='Buy']"
```

**Expected:** Text widgets containing "Buy"

#### Test 6.4: Find by Key
```bash
flutter_reflect find --selector "TextField[key='addTodoInput']"
```

**Expected:** Widget with specific key

#### Test 6.5: Find All Matches
```bash
flutter_reflect find --selector "TodoItemWidget" --find-all true
```

**Expected:** All matching widgets returned

#### Test 6.6: Hierarchical Selector
```bash
flutter_reflect find --selector "ListView > Card"
```

**Expected:** Cards that are direct children of ListView

#### Test 6.7: Find with Properties
```bash
flutter_reflect find --selector "Checkbox[value=true]"
```

**Expected:** Checked checkboxes

### Sample App Selectors

```bash
# Add todo input
flutter_reflect find --selector "TextField[key='addTodoInput']"

# Add button
flutter_reflect find --selector "Button[text='Add Task']"

# Todo list
flutter_reflect find --selector "ListView[key='todoListView']"

# Delete buttons (multiple)
flutter_reflect find --selector "IconButton[key*='deleteButton']" --find-all true

# Checkboxes (multiple)
flutter_reflect find --selector "Checkbox[key*='todoDone']" --find-all true

# Stats display
flutter_reflect find --selector "Text[key='statsWidget']"

# Navigation button
flutter_reflect find --selector "Button[text='Stats']"

# Filter buttons
flutter_reflect find --selector "Button[text='Active']"
flutter_reflect find --selector "Button[text='Completed']"

# Search field
flutter_reflect find --selector "TextField[key='searchInput']"
```

### Success Criteria
- ✅ Correct widgets found
- ✅ Selectors parsed properly
- ✅ Multiple matches supported
- ✅ Edge cases handled
- ✅ Returns widget metadata

---

## Tool 7: tap 👆

### Purpose
Simulate user tap/click interactions on widgets.

### What It Tests
- Gesture injection
- Coordinate calculation
- Widget bounds validation
- Tap event propagation

### Test Cases

#### Test 7.1: Tap by Selector
```bash
flutter_reflect tap --selector "ElevatedButton[key='addTodoButton']"
```

**Expected:**
- Button tapped
- Action triggered
- Feedback message appears: "✓ Task added"

**Verification:** Check app UI for task added

#### Test 7.2: Tap by Widget ID
```bash
flutter_reflect tap --widget-id "addTodoButton"
```

**Expected:** Same as selector-based tap

#### Test 7.3: Tap by Coordinates
```bash
flutter_reflect tap --x 100 --y 200
```

**Expected:** Tap injected at specified coordinates

#### Test 7.4: Tap with Offset
```bash
flutter_reflect tap --selector "Button[text='Login']" --x-offset 10 --y-offset 5
```

**Expected:** Tap offset from widget center

#### Test 7.5: Multiple Taps in Sequence
```bash
# Add task 1
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Task 1"
flutter_reflect tap --selector "Button[key='addTodoButton']"

# Add task 2
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Task 2"
flutter_reflect tap --selector "Button[key='addTodoButton']"
```

**Expected:** Multiple tasks added, UI updates

#### Test 7.6: Tap Checkbox
```bash
flutter_reflect tap --selector "Checkbox[key='todoDone_1']"
```

**Expected:**
- Checkbox state toggles
- Task marked complete/incomplete
- UI updates (strikethrough)

#### Test 7.7: Tap Delete Button
```bash
flutter_reflect tap --selector "IconButton[key*='deleteButton_1']"
```

**Expected:**
- Task deleted
- List updates
- Stats decrease

#### Test 7.8: Tap Navigation Button
```bash
flutter_reflect tap --selector "Button[key='statsButton']"
```

**Expected:**
- Screen changes to Stats
- New widgets appear

### Error Handling

#### Test 7.9: Tap Non-existent Widget
```bash
flutter_reflect tap --selector "Button[text='NonExistent']"
```

**Expected:**
```json
{
  "success": false,
  "error": "Widget not found",
  "details": "No widget matching selector found"
}
```

#### Test 7.10: Tap Disabled Widget
```bash
flutter_reflect tap --selector "ElevatedButton[enabled=false]"
```

**Expected:**
- Graceful error
- Helpful error message

### Success Criteria
- ✅ Tap reaches intended widget
- ✅ Widget action triggered
- ✅ UI updates reflect tap
- ✅ Error messages helpful
- ✅ Coordinate taps work
- ✅ Multiple rapid taps handled

### Feedback Messages
Each successful tap shows feedback:
- "✓ Task added: Task name"
- "✓ Task deleted: Task name"
- "✓ Task marked complete"
- "→ Navigated to stats"

---

## Tool 8: type ⌨️

### Purpose
Enter text into input fields, simulating keyboard input.

### What It Tests
- Text field focusing
- Character input
- Text validation
- Input state management

### Test Cases

#### Test 8.1: Type into TextField
```bash
flutter_reflect type --text "Buy groceries" --selector "TextField[key='addTodoInput']"
```

**Expected:**
- Text appears in field
- Field focused
- Text entered character by character

**Verification:** Look at text field in app

#### Test 8.2: Type with Clear First
```bash
flutter_reflect type --text "New task" --selector "TextField[key='addTodoInput']" --clear-first true
```

**Expected:**
- Field cleared first
- New text entered

#### Test 8.3: Type with Submit
```bash
flutter_reflect type --text "New task" --selector "TextField[key='addTodoInput']" --submit true
```

**Expected:**
- Text entered
- Enter key pressed
- Task added automatically

#### Test 8.4: Slow Typing
```bash
flutter_reflect type --text "This is a longer text entry" --selector "TextField[key='addTodoInput']"
```

**Expected:** All characters entered correctly

#### Test 8.5: Special Characters
```bash
flutter_reflect type --text "Email: user@example.com" --selector "TextField[key='addTodoInput']"
```

**Expected:** Special characters handled correctly

#### Test 8.6: Type in Search Field
```bash
flutter_reflect tap --selector "Button[key='statsButton']"  # Navigate to stats
flutter_reflect type --text "learn" --selector "TextField[key='searchInput']"
```

**Expected:**
- Text entered in search field
- List filters in real-time
- Feedback: "🔍 Search: 'learn'"

#### Test 8.7: Type Multiple Fields
```bash
# Email field
flutter_reflect type --text "test@example.com" --selector "TextField[key='emailField']"

# Password field
flutter_reflect type --text "password123" --selector "TextField[key='passwordField']" --clear-first true
```

**Expected:** Each field receives correct text

### Error Handling

#### Test 8.8: Type into Disabled Field
```bash
flutter_reflect type --text "test" --selector "TextField[enabled=false]"
```

**Expected:** Graceful error about disabled field

#### Test 8.9: Type into Non-TextField
```bash
flutter_reflect type --text "test" --selector "Text[key='labelText']"
```

**Expected:** Error that Text widget is not editable

### Success Criteria
- ✅ Text enters correctly
- ✅ Field focused properly
- ✅ All characters rendered
- ✅ Special characters work
- ✅ Validation messages helpful
- ✅ Feedback shown

### Feedback Messages
- Field focus feedback
- Text entry confirmation
- Input validation errors

---

## Tool 9: scroll 📜

### Purpose
Perform scroll gestures in scrollable widgets or entire view.

### What It Tests
- Scroll offset calculation
- Animation duration handling
- Scroll direction (vertical/horizontal)
- List bounds validation

### Test Cases

#### Test 9.1: Scroll Down
```bash
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 500
```

**Expected:**
- List scrolls down 500 pixels
- New items visible if list is tall
- Smooth animation

**Verification:** Check that different items are visible

#### Test 9.2: Scroll Up
```bash
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy -300
```

**Expected:** List scrolls up

#### Test 9.3: Multiple Scrolls
```bash
# Add many tasks first (to make list scrollable)
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 500
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 500
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy -1000
```

**Expected:** Multiple scroll operations work

#### Test 9.4: Custom Duration
```bash
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 500 --duration 1000
```

**Expected:** Scroll animation takes ~1000ms

#### Test 9.5: Fast Scroll
```bash
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 500 --duration 100
```

**Expected:** Rapid scroll animation

#### Test 9.6: Horizontal Scroll
```bash
flutter_reflect scroll --selector "HorizontalScrollView" --dx 200 --dy 0
```

**Expected:** Scrolls horizontally

#### Test 9.7: Filtered List Scroll (Stats Screen)
```bash
flutter_reflect tap --selector "Button[key='statsButton']"  # Go to stats
flutter_reflect tap --selector "Button[key='showActiveButton']"  # Filter active
flutter_reflect scroll --selector "ListView[key='filteredListView']" --dy 300
```

**Expected:** Scrolls filtered list

### Scroll Bounds Testing

#### Test 9.8: Scroll Beyond End
```bash
# Scroll down very far (more than list height)
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 10000
```

**Expected:** Stops at bottom, doesn't error

#### Test 9.9: Scroll Beyond Start
```bash
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy -10000
```

**Expected:** Stops at top, doesn't error

### Success Criteria
- ✅ List scrolls in correct direction
- ✅ Correct scroll distance
- ✅ Animation timing respected
- ✅ Bounds checked
- ✅ Handles rapid scrolls
- ✅ Works on filtered lists

### Feedback Messages
- "↻ Scrolled list"
- Scroll offset confirmation

---

## Tool 10: get_properties 🔬

### Purpose
Extract detailed properties from specific widgets.

### What It Tests
- Property extraction
- Widget bounds calculation
- State inspection
- Child enumeration

### Test Cases

#### Test 10.1: Get TextField Properties
```bash
flutter_reflect get_properties --selector "TextField[key='addTodoInput']"
```

**Expected Output:**
```json
{
  "success": true,
  "widget": {
    "type": "TextField",
    "key": "addTodoInput",
    "enabled": true,
    "properties": {
      "hintText": "Add a new task...",
      "obscureText": false,
      "maxLines": 1
    },
    "bounds": {
      "x": 16,
      "y": 200,
      "width": 300,
      "height": 50
    }
  }
}
```

#### Test 10.2: Get Button Properties
```bash
flutter_reflect get_properties --widget-id "addTodoButton"
```

**Expected:**
- Button type
- Text content
- Enabled state
- Bounds (position and size)

#### Test 10.3: Get Properties with Render Details
```bash
flutter_reflect get_properties --selector "ListView[key='todoListView']" --include-render true
```

**Expected:**
- Render object type
- Layout information
- Paint bounds

#### Test 10.4: Get Properties with Layout
```bash
flutter_reflect get_properties --selector "ListView[key='todoListView']" --include-layout true
```

**Expected:**
- Constraints
- Size
- Alignment
- Padding/margin info

#### Test 10.5: Get Properties with Children
```bash
flutter_reflect get_properties --selector "ListView[key='todoListView']" --include-children true --max-depth 1
```

**Expected:**
- List of direct children
- Child widget types
- Child count

#### Test 10.6: Get Text Widget Properties
```bash
flutter_reflect get_properties --selector "Text[key='statsWidget']"
```

**Expected:**
```json
{
  "widget": {
    "type": "Text",
    "key": "statsWidget",
    "text": "2/5 completed",
    "style": {
      "fontSize": 14,
      "fontWeight": "w600"
    },
    "bounds": {...}
  }
}
```

#### Test 10.7: Get Checkbox Properties
```bash
flutter_reflect get_properties --selector "Checkbox[key='todoDone_1']"
```

**Expected:**
```json
{
  "widget": {
    "type": "Checkbox",
    "key": "todoDone_1",
    "value": true,  // or false
    "enabled": true,
    "bounds": {...}
  }
}
```

#### Test 10.8: Get Multiple Properties for Comparison
```bash
# Get properties of same type widget at different times
flutter_reflect get_properties --selector "Text[key='statsWidget']"
# Add a task
flutter_reflect tap --selector "Button[key='addTodoButton']"
# Get properties again to see change
flutter_reflect get_properties --selector "Text[key='statsWidget']"
```

**Expected:**
- First call: "1/5 completed"
- Second call: "1/6 completed"

### Bounds Calculation

#### Test 10.9: Verify Bounds for Tapping
```bash
# Get bounds of button
flutter_reflect get_properties --selector "Button[key='addTodoButton']"
# Response includes x, y, width, height
# Use these to tap at specific location
flutter_reflect tap --x <center_x> --y <center_y>
```

**Expected:** Tap lands on button

### Complex Property Retrieval

#### Test 10.10: Get Full Widget Info
```bash
flutter_reflect get_properties \
  --selector "ListTile" \
  --include-render true \
  --include-layout true \
  --include-children true \
  --max-depth 2
```

**Expected:**
- Complete widget hierarchy
- All properties
- Layout constraints
- Child structure

### Success Criteria
- ✅ Properties extracted correctly
- ✅ Bounds accurate
- ✅ Text content matches
- ✅ State reflected (enabled/disabled)
- ✅ Child enumeration works
- ✅ Supports deep inspection

---

## Integration Tests: Multi-Tool Scenarios

### Scenario A: Complete Todo Workflow

```bash
# 1. Discover app
flutter_reflect list_instances --port-start 8080 --port-end 8200

# 2. Connect
flutter_reflect connect

# 3. Add task
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Buy milk"
flutter_reflect tap --selector "Button[key='addTodoButton']"

# 4. Inspect tree
flutter_reflect get_tree --max-depth 3

# 5. Find the new task
flutter_reflect find --selector "Text[contains='Buy milk']"

# 6. Mark as complete
flutter_reflect tap --selector "Checkbox[key='todoDone_1']"

# 7. Get updated properties
flutter_reflect get_properties --selector "Text[key='statsWidget']"

# 8. Navigate to stats
flutter_reflect tap --selector "Button[key='statsButton']"

# 9. Filter completed
flutter_reflect tap --selector "Button[key='showCompletedButton']"

# 10. Scroll
flutter_reflect scroll --selector "ListView[key='filteredListView']" --dy 200

# 11. Return home
flutter_reflect tap --selector "Button[key='backButton']"

# 12. Disconnect
flutter_reflect disconnect
```

### Scenario B: Advanced Search & Filter

```bash
# Setup: Add multiple tasks with varied content
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Learn Flutter"
flutter_reflect tap --selector "Button[key='addTodoButton']"
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Learn Dart"
flutter_reflect tap --selector "Button[key='addTodoButton']"
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Buy groceries"
flutter_reflect tap --selector "Button[key='addTodoButton']"

# Navigate to stats
flutter_reflect tap --selector "Button[key='statsButton']"

# Filter active tasks
flutter_reflect tap --selector "Button[key='showActiveButton']"
flutter_reflect find --selector "Text" --find-all true

# Search within active
flutter_reflect type --selector "TextField[key='searchInput']" --text "Learn"
flutter_reflect find --selector "Text[contains='Learn']" --find-all true

# Get properties of filtered list
flutter_reflect get_properties --selector "ListView[key='filteredListView']" --include-children true
```

### Scenario C: Performance Testing

```bash
# Test with many items
for i in {1..20}; do
  flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Task $i"
  flutter_reflect tap --selector "Button[key='addTodoButton']"
done

# Test scrolling with many items
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 1000
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 1000
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy -2000

# Test finding with many items
flutter_reflect find --selector "Text" --find-all true

# Get tree with many items
flutter_reflect get_tree --max-depth 5
```

---

## Success Checklist

### After All Tests

- [ ] All 10 tools functional
- [ ] Sample app responds to all interactions
- [ ] Feedback messages display correctly
- [ ] No crashes or hangs
- [ ] Error messages are helpful
- [ ] No encoding issues
- [ ] Performance acceptable
- [ ] Multi-tool workflows complete

---

**End of Tool Testing Guide**
**Created:** December 19, 2025
