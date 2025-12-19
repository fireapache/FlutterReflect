# Flutter Sample Todo App - FlutterReflect Testing Guide

A comprehensive Flutter sample app designed to demonstrate all FlutterReflect tools and their capabilities. This app is a fully-featured todo list with state management, navigation, filtering, and search functionality.

## Overview

This app showcases:
- ✅ **Text Input** - Type tasks using the `type` tool
- ✅ **Button Interactions** - Tap buttons using the `tap` tool
- ✅ **Scrollable Lists** - Scroll through tasks using the `scroll` tool
- ✅ **Widget Finding** - Locate widgets using the `find` tool
- ✅ **Tree Inspection** - Analyze widget hierarchy using the `get_tree` tool
- ✅ **Property Inspection** - Extract widget details using the `get_properties` tool
- ✅ **Multi-Screen Navigation** - Navigate between screens
- ✅ **Real-Time Feedback** - Visual feedback for all interactions
- ✅ **Complex Scenarios** - Filtering, searching, and state management

## Setup Instructions

### 1. Prerequisites
- Flutter SDK installed
- FlutterReflect MCP server running
- A Flutter-compatible device or emulator

### 2. Running the App

```bash
# Navigate to the app directory
cd E:\C++\FlutterReflect\examples\flutter_sample_app

# Get dependencies
flutter pub get

# Run the app
flutter run
```

### 3. FlutterDriver Extension

The app automatically registers the FlutterDriver extension handler in `main.dart`:

```dart
enableFlutterDriverExtension(
  handler: (String request) async {
    // Handles custom commands from FlutterReflect
    return jsonEncode({'result': 'success'});
  }
);
```

This enables FlutterReflect to:
- Inject tap gestures at specific coordinates
- Type text into text fields
- Scroll through lists
- Query the widget tree
- Get widget properties

## Tool Usage Examples

### 1. LIST INSTANCES (Discovery)

Discover the running Flutter app:

```bash
flutter_reflect list_instances --port-start 8080 --port-end 8200
```

**Expected Output:**
```json
{
  "success": true,
  "instances": [
    {
      "port": 8181,
      "uri": "ws://localhost:8181/abc123...",
      "projectName": "flutter_sample_app",
      "deviceType": "android|ios|web",
      "status": "connected"
    }
  ]
}
```

---

### 2. CONNECT (VM Service Connection)

Connect to the app's VM Service:

```bash
# Auto-discover and connect to first instance
flutter_reflect connect

# Or connect to specific URI
flutter_reflect connect --uri ws://localhost:8181/abc123...
```

**Note:** Once connected, subsequent tool calls maintain the connection.

---

### 3. TYPE (Text Input)

Add a task by typing in the text field:

```bash
flutter_reflect type \
  --selector "TextField[key='addTodoInput']" \
  --text "Buy groceries"
```

**What happens:**
1. FlutterReflect finds the TextField with key `addTodoInput`
2. Focuses the field
3. Types "Buy groceries"
4. You'll see the text appear in the input field

---

### 4. TAP (Button Interactions)

Tap the "Add Task" button to add the task:

```bash
flutter_reflect tap \
  --selector "ElevatedButton[key='addTodoButton']"
```

**What happens:**
1. The "Add Task" button is located
2. A tap gesture is injected at its center
3. The task is added to the list
4. Green feedback message appears: "✓ Task added: Buy groceries"

---

### 5. DELETE TASK (Compound Interaction)

Find a task and delete it:

```bash
# Find the delete button for a specific task
flutter_reflect find \
  --selector "IconButton[key*='deleteButton']"

# Tap the first delete button
flutter_reflect tap \
  --selector "IconButton[key*='deleteButton_']"
```

**What happens:**
1. The find tool locates all delete buttons
2. Tapping the button triggers deletion
3. Red feedback: "✓ Task deleted: Buy groceries"

---

### 6. SCROLL (List Navigation)

Scroll down to see more tasks:

```bash
# Scroll down 500 pixels
flutter_reflect scroll \
  --selector "ListView[key='todoListView']" \
  --dy 500

# Scroll up 300 pixels
flutter_reflect scroll \
  --selector "ListView[key='todoListView']" \
  --dy -300

# Scroll with custom animation duration
flutter_reflect scroll \
  --selector "ListView[key='todoListView']" \
  --dy 500 \
  --duration 800
```

**What happens:**
1. The ListView is located
2. Smooth scroll gesture is performed
3. Different tasks become visible
4. Feedback message: "↻ Scrolled list"

---

### 7. FIND (Widget Location)

Search for widgets by selector:

```bash
# Find all tasks containing "grocery"
flutter_reflect find \
  --selector "Text[contains='grocery']" \
  --find-all true

# Find incomplete tasks
flutter_reflect find \
  --selector "Checkbox[value=false]" \
  --find-all true

# Find the stats display
flutter_reflect find \
  --selector "Text[key='statsWidget']"
```

**What happens:**
1. FlutterReflect queries the widget tree
2. Returns matching widget IDs and metadata
3. Can be used to dynamically target widgets

---

### 8. GET_TREE (Widget Hierarchy)

Inspect the complete widget tree:

```bash
# Get full tree
flutter_reflect get_tree

# Get tree limited to depth 3
flutter_reflect get_tree --max-depth 3

# Get tree as JSON
flutter_reflect get_tree --max-depth 5 --format json
```

**Expected structure:**
```
Scaffold
├── AppBar
│   ├── Text(Flutter Sample Todo App)
│   └── Text(stats_widget: 2/5 completed)
├── Column
│   ├── TextField(addTodoInput)
│   ├── ElevatedButton(addTodoButton)
│   ├── ListView(todoListView)
│   │   ├── Card
│   │   │   └── ListTile
│   │   │       ├── Checkbox(todoDone_1)
│   │   │       ├── Text(todoText_1)
│   │   │       └── IconButton(deleteButton_1)
│   │   └── ... more items
```

---

### 9. GET_PROPERTIES (Widget Details)

Extract detailed information about widgets:

```bash
# Get stats widget properties
flutter_reflect get_properties \
  --selector "Text[key='statsWidget']"

# Get TextField properties including bounds
flutter_reflect get_properties \
  --selector "TextField[key='addTodoInput']" \
  --include-render true \
  --include-layout true

# Get ListView properties
flutter_reflect get_properties \
  --selector "ListView[key='todoListView']" \
  --include-children true \
  --max-depth 2
```

**What you get:**
- Widget type (Text, TextField, ListView, etc.)
- Key identifier
- Geometric bounds (position and size)
- Enabled/visible state
- Text content
- Child widgets (if requested)
- Layout constraints

---

### 10. NAVIGATE TO STATS SCREEN

Tap the "Stats" button to navigate:

```bash
flutter_reflect tap \
  --selector "ElevatedButton[key='statsButton']"
```

**Screen changes to show:**
- Task statistics (total, completed, active)
- Progress bar
- Search field
- Filter buttons
- Filtered task list

---

### 11. SEARCH TASKS (Complex Scenario)

Navigate to Stats screen and search:

```bash
# Type in search field
flutter_reflect type \
  --selector "TextField[key='searchInput']" \
  --text "learn"

# Find tasks containing "learn"
flutter_reflect find \
  --selector "Text[contains='learn']" \
  --find-all true
```

**What happens:**
1. Search field gets focused
2. Text "learn" is typed
3. List filters to show only matching tasks
4. Feedback: "🔍 Search: \"learn\""

---

### 12. FILTER TASKS (Complex Scenario)

Use filter buttons to show different task sets:

```bash
# Show only active tasks
flutter_reflect tap \
  --selector "ElevatedButton[key='showActiveButton']"

# Show only completed tasks
flutter_reflect tap \
  --selector "ElevatedButton[key='showCompletedButton']"

# Show all tasks
flutter_reflect tap \
  --selector "ElevatedButton[key='showAllButton']"
```

**Each filter:**
- Changes the list content
- Updates stats display
- Shows feedback message

---

### 13. MARK TASK COMPLETE (Checkbox Interaction)

Check/uncheck a task:

```bash
# Find and tap checkbox for first task
flutter_reflect tap \
  --selector "Checkbox[key='todoDone_1']"
```

**What happens:**
1. Checkbox state toggles
2. Task text gets strikethrough
3. Stats update automatically
4. Feedback: "✓ Task marked complete"

---

### 14. CLEAR ALL TASKS (Confirmation Dialog)

Trigger the clear all function:

```bash
flutter_reflect tap \
  --selector "OutlinedButton[key='clearAllButton']"

# A dialog appears - tap "Clear All" button
flutter_reflect tap \
  --selector "TextButton[text='Clear All']"
```

**What happens:**
1. Confirmation dialog shows
2. All tasks are deleted
3. List becomes empty
4. Stats reset to 0/0
5. Feedback: "✓ All tasks cleared"

---

### 15. MARK ALL COMPLETE (Bulk Action)

Mark all tasks as complete:

```bash
flutter_reflect tap \
  --selector "OutlinedButton[key='markAllCompleteButton']"
```

**What happens:**
1. All tasks get strikethrough
2. Checkboxes all become checked
3. Stats update: "5/5 completed"
4. Feedback: "✓ All tasks completed"

---

### 16. RETURN TO HOME (Navigation)

Go back from Stats screen:

```bash
flutter_reflect tap \
  --selector "IconButton[key='backButton']"
```

**What happens:**
1. Stats screen closes
2. Returns to home screen
3. All todos still there (state preserved)
4. Feedback: "← Returned home"

---

## All Available Widget Keys

### Home Screen Keys

| Key | Widget Type | Purpose |
|-----|-------------|---------|
| `addTodoInput` | TextField | Add todo input field |
| `addTodoButton` | ElevatedButton | Submit new todo |
| `statsButton` | ElevatedButton | Navigate to stats |
| `todoListView` | ListView | Main todo list |
| `todoDone_{id}` | Checkbox | Toggle todo completion |
| `todoText_{id}` | Text | Task title display |
| `deleteButton_{id}` | IconButton | Delete todo |
| `markAllCompleteButton` | OutlinedButton | Mark all complete |
| `clearAllButton` | OutlinedButton | Clear all todos |
| `statsWidget` | Text | "X/Y completed" display |

### Stats Screen Keys

| Key | Widget Type | Purpose |
|-----|-------------|---------|
| `backButton` | IconButton | Return to home |
| `searchInput` | TextField | Search tasks field |
| `filterBar` | Container | Filter button container |
| `showAllButton` | ElevatedButton | Show all filter |
| `showActiveButton` | ElevatedButton | Show active filter |
| `showCompletedButton` | ElevatedButton | Show completed filter |
| `filteredListView` | ListView | Filtered todo list |

---

## Test Scenarios

### Scenario 1: Basic CRUD Operations (5 minutes)

```bash
# 1. Add first task
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "First task"
flutter_reflect tap --selector "ElevatedButton[key='addTodoButton']"

# 2. Add second task
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Second task"
flutter_reflect tap --selector "ElevatedButton[key='addTodoButton']"

# 3. Mark first task complete
flutter_reflect tap --selector "Checkbox[key='todoDone_1']"

# 4. Delete second task
flutter_reflect tap --selector "IconButton[key*='deleteButton_']"

# 5. Verify final state
flutter_reflect get_tree --max-depth 3
```

### Scenario 2: List Navigation (5 minutes)

```bash
# 1. Add multiple tasks
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Task 1"
flutter_reflect tap --selector "ElevatedButton[key='addTodoButton']"
# ... repeat 5 times to have 5 tasks

# 2. Scroll down to see all
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy 500

# 3. Scroll back up
flutter_reflect scroll --selector "ListView[key='todoListView']" --dy -500

# 4. Get properties of list
flutter_reflect get_properties --selector "ListView[key='todoListView']"
```

### Scenario 3: Advanced Filtering (10 minutes)

```bash
# 1. Add varied tasks
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Buy groceries"
flutter_reflect tap --selector "ElevatedButton[key='addTodoButton']"
# ... add more tasks

# 2. Navigate to stats
flutter_reflect tap --selector "ElevatedButton[key='statsButton']"

# 3. Filter to active tasks
flutter_reflect tap --selector "ElevatedButton[key='showActiveButton']"

# 4. Search within results
flutter_reflect type --selector "TextField[key='searchInput']" --text "grocery"

# 5. Get properties of filtered list
flutter_reflect get_properties --selector "ListView[key='filteredListView']"

# 6. Return home
flutter_reflect tap --selector "IconButton[key='backButton']"
```

### Scenario 4: Complex Multi-Step (15 minutes)

```bash
# Add 10 tasks with specific names
flutter_reflect type --selector "TextField[key='addTodoInput']" --text "Learn Flutter basics"
flutter_reflect tap --selector "ElevatedButton[key='addTodoButton']"
# ... repeat for different tasks

# Complete half of them
flutter_reflect tap --selector "Checkbox[key='todoDone_1']"
flutter_reflect tap --selector "Checkbox[key='todoDone_3']"
# ... etc

# Navigate to stats and verify filtering
flutter_reflect tap --selector "ElevatedButton[key='statsButton']"
flutter_reflect get_properties --selector "Text[key='statsWidget']"
flutter_reflect tap --selector "ElevatedButton[key='showCompletedButton']"

# Search for specific task
flutter_reflect type --selector "TextField[key='searchInput']" --text "Flutter"
flutter_reflect find --selector "Text[contains='Flutter']" --find-all true

# Navigate back and delete some
flutter_reflect tap --selector "IconButton[key='backButton']"
flutter_reflect tap --selector "IconButton[key*='deleteButton_1']"
flutter_reflect tap --selector "IconButton[key*='deleteButton_2']"

# Mark all remaining complete
flutter_reflect tap --selector "OutlinedButton[key='markAllCompleteButton']"

# Final verification
flutter_reflect get_tree --max-depth 5
```

---

## Interaction Feedback Messages

The app displays real-time feedback for all interactions:

| Message | Trigger |
|---------|---------|
| ✓ Task added: {name} | Task added to list |
| ✓ Task deleted: {name} | Task removed |
| ✓ Task marked complete | Checkbox checked |
| ✓ Task marked incomplete | Checkbox unchecked |
| ↻ Scrolled list | List scrolled |
| ✓ All tasks cleared | Clear all executed |
| ✓ All tasks completed | Mark all complete executed |
| 🔍 Filtered: X tasks shown | Filter applied |
| 🔍 Search: "query" | Search executed |
| → Navigated to stats | Stats button tapped |
| ← Returned home | Back button tapped |

---

## Project Structure

```
flutter_sample_app/
├── pubspec.yaml                    # Flutter dependencies
├── analysis_options.yaml           # Lint configuration
├── README.md                       # This file
├── lib/
│   ├── main.dart                   # Entry point with FlutterDriver handler
│   ├── models/
│   │   └── todo_model.dart         # Todo data model and manager
│   ├── screens/
│   │   ├── home_screen.dart        # Main todo list screen
│   │   └── stats_screen.dart       # Stats and filtering screen
│   ├── widgets/
│   │   ├── todo_item_widget.dart   # Individual todo display
│   │   ├── interaction_log.dart    # Feedback message widget
│   │   └── filter_bar.dart         # Filter button bar
│   └── utils/
│       └── constants.dart          # Widget keys and messages
└── test/
    └── dummy_test.dart             # Required test file
```

---

## Troubleshooting

### App not appearing in `list_instances`
- Ensure `flutter run` is still executing
- Check that the device/emulator is running
- Try different port ranges: `--port-start 8080 --port-end 8300`

### Connection fails
- Verify the VM Service URI is correct
- Check that the FlutterDriver extension is loaded (see main.dart)
- Ensure the Flutter app hasn't crashed

### Selectors not finding widgets
- Use `get_tree` to inspect the actual widget hierarchy
- Verify the widget key matches exactly (case-sensitive)
- Try finding by parent-child relationships: `Column > TextField`

### Tap/scroll not working
- Confirm widget is visible on screen (may need to scroll first)
- Check that widget is interactive (not disabled)
- Verify the target widget type in the selector

### Search/filter not updating
- Type tool may need a small delay between characters
- Try using `--clear-first true` if the field has existing text
- Use `submit: true` to trigger onChange handlers

---

## Next Steps

1. **Run the app** with `flutter run`
2. **Connect FlutterReflect** with `flutter_reflect connect`
3. **Try basic operations** - add, delete, complete tasks
4. **Test advanced features** - search, filter, navigate
5. **Inspect the widget tree** with `get_tree` and `get_properties`

The app is designed to be completely automatable - every interaction can be driven by FlutterReflect tools!
