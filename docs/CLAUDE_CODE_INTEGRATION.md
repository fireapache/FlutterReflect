# FlutterReflect - Claude Code Integration

## Overview

FlutterReflect is an MCP (Model Context Protocol) server designed for **Claude Code** - the AI-powered command-line assistant for software development.

**Date:** December 17, 2025
**Status:** ✅ Ready for Claude Code Integration
**Binary:** `E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe` (6.6 MB)

---

## What is FlutterReflect?

FlutterReflect enables Claude Code to autonomously discover, launch, connect to, and interact with Flutter applications through 10 MCP tools organized across 5 implementation phases.

### Key Capabilities

- **Auto-Discovery**: Find running Flutter apps automatically
- **App Launching**: Start Flutter apps programmatically
- **VM Connection**: Connect to Flutter VM Service (manual/auto)
- **Widget Inspection**: Retrieve and analyze widget trees
- **Widget Selection**: Find widgets using CSS-like selectors
- **User Interaction**: Tap, type, scroll, and more
- **Property Inspection**: Get detailed widget properties

---

## How to Use with Claude Code

### Step 1: MCP Server Configuration

FlutterReflect runs as an MCP server that communicates with Claude Code via JSON-RPC 2.0 over STDIO.

The MCP server binary is located at:
```
E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe
```

### Step 2: Natural Language Interface

Once configured, you can interact with Flutter apps using natural language in Claude Code:

```
You: "List all running Flutter apps on my system"
Claude Code: [Executes flutter_list_instances tool]

You: "Connect to the first Flutter app and show me the widget tree"
Claude Code: [Executes flutter_connect, then flutter_get_tree]

You: "Tap on the Login button"
Claude Code: [Executes flutter_tap with appropriate selector]
```

### Step 3: Autonomous Workflows

Claude Code will autonomously chain multiple tool calls to accomplish complex tasks:

**Example: Test Login Flow**
```
You: "Test the login flow in my Flutter app"

Claude Code will:
1. flutter_list_instances() → Discover running apps
2. flutter_connect() → Connect to the app
3. flutter_get_tree() → Inspect UI structure
4. flutter_find(selector="TextField[contains='email']") → Find email field
5. flutter_type(text="test@example.com") → Enter email
6. flutter_find(selector="TextField[contains='password']") → Find password field
7. flutter_type(text="password123") → Enter password
8. flutter_tap(selector="Button[text='Login']") → Tap login button
9. flutter_get_tree() → Verify navigation to success screen
```

---

## Available Tools (10 Total)

### Phase 1: Auto-Discovery & Launching
- `flutter_list_instances` - Discover running Flutter apps
- `flutter_launch` - Launch Flutter apps programmatically

### Phase 2: Connection Management
- `flutter_connect` - Connect to Flutter app (manual/auto-discovery)
- `flutter_disconnect` - Disconnect from app

### Phase 3: Widget Inspection
- `flutter_get_tree` - Get widget tree hierarchy
- `flutter_get_properties` - Get detailed widget properties

### Phase 4: Widget Selection
- `flutter_find` - Find widgets using CSS-like selectors

### Phase 5: User Interaction
- `flutter_tap` - Tap on widgets
- `flutter_type` - Enter text into input fields
- `flutter_scroll` - Scroll within the app

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Developer (You)                                             │
│ "Test my Flutter app's login flow"                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Claude Code CLI                                             │
│ - Understands natural language                              │
│ - Plans tool execution                                      │
│ - Chains multiple tool calls                                │
└────────────────────┬────────────────────────────────────────┘
                     │ JSON-RPC 2.0 (STDIO)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FlutterReflect MCP Server                                   │
│ - Receives tool calls from Claude Code                      │
│ - Executes Flutter operations                               │
│ - Returns results                                           │
└────────────────────┬────────────────────────────────────────┘
                     │ Flutter VM Service Protocol (WebSocket)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Your Flutter Application                                    │
│ - Running in debug mode                                     │
│ - VM Service enabled                                        │
│ - Port 8080-8200                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start Examples

### Example 1: Discover and Connect

```
You: "What Flutter apps are currently running?"
Claude Code: [Uses flutter_list_instances]
→ Returns list of running apps with ports and project names

You: "Connect to the first one"
Claude Code: [Uses flutter_connect with auto-discovery]
→ Establishes connection to Flutter app
```

### Example 2: Inspect UI

```
You: "Show me the widget tree of the connected Flutter app"
Claude Code: [Uses flutter_get_tree]
→ Returns hierarchical widget structure

You: "Find all buttons in the app"
Claude Code: [Uses flutter_find with selector="Button"]
→ Returns list of all button widgets with IDs
```

### Example 3: Automated Testing

```
You: "Automate filling out the login form with test@example.com and password123"
Claude Code:
1. [Uses flutter_find to locate email field]
2. [Uses flutter_type to enter email]
3. [Uses flutter_find to locate password field]
4. [Uses flutter_type to enter password]
5. [Uses flutter_find to locate login button]
6. [Uses flutter_tap to submit]
→ Completes entire login flow autonomously
```

---

## Command-Line Options

While FlutterReflect is not used as a traditional CLI tool, it supports these flags for information and debugging:

```bash
# Display comprehensive help (lists all 10 tools)
flutter_reflect.exe --help
flutter_reflect.exe -h

# Display version information
flutter_reflect.exe --version
flutter_reflect.exe -v

# Start with debug logging
flutter_reflect.exe --log-level debug

# Log to file
flutter_reflect.exe --log-file flutter_reflect.log
```

---

## Key Points

### ✅ DO:
- Configure FlutterReflect as an MCP server for Claude Code
- Use natural language to interact with Flutter apps
- Let Claude Code handle tool calls and JSON-RPC communication
- Use `--help` to see all available tools

### ❌ DON'T:
- Try to run tools directly like `flutter_reflect list-apps` (not how it works)
- Manually send JSON-RPC (unless testing/debugging)
- Expect interactive CLI menus
- Use it standalone without Claude Code

### 💡 REMEMBER:
- FlutterReflect is an **MCP server**, not a traditional CLI tool
- It communicates via **JSON-RPC 2.0 over STDIO**
- Developers interact through **Claude Code** using natural language
- Claude Code autonomously calls tools based on your intent
- All 10 tools work together to enable complete Flutter app automation

---

## Documentation Files

- `USAGE_GUIDE.md` - Complete usage guide with examples
- `AUTONOMOUS_WORKFLOW.md` - Autonomous workflow examples
- `PHASE_1_2_3_COMPLETE.md` - Implementation details
- `HELP_OUTPUT_IMPROVEMENTS.md` - Help system documentation
- `CLAUDE_CODE_INTEGRATION.md` - This file

---

## Technical Details

**MCP Protocol:** JSON-RPC 2.0
**Transport:** STDIO (stdin/stdout)
**Tools Registered:** 10
**Implementation Phases:** 5
**Platform:** Windows, macOS, Linux
**Flutter Support:** Desktop + Web
**C++ Standard:** C++17
**Compiler:** MSVC (Visual Studio 2022)
**Binary Size:** 6.6 MB (Debug)

---

## Example Session

```
You: "I'm working on a Flutter app. Can you help me test the login screen?"

Claude Code: "I'll help you test the login screen. Let me first check if your
Flutter app is running."

[Executes: flutter_list_instances()]

Claude Code: "I found your Flutter app running on port 8181. Let me connect to
it and inspect the login screen."

[Executes: flutter_connect()]
[Executes: flutter_get_tree()]

Claude Code: "I can see your login screen has:
- An email TextField
- A password TextField
- A Login button
- A 'Forgot Password?' link

Would you like me to test the login flow with sample credentials?"

You: "Yes, use test@example.com and password123"

Claude Code: "I'll test the login flow now."

[Executes: flutter_find(selector="TextField[contains='email']")]
[Executes: flutter_type(text="test@example.com")]
[Executes: flutter_find(selector="TextField[contains='password']")]
[Executes: flutter_type(text="password123")]
[Executes: flutter_tap(selector="Button[text='Login']")]
[Executes: flutter_get_tree()]

Claude Code: "✅ Login test completed successfully! The app navigated to the
home screen after login. The login flow is working correctly."
```

---

**Status:** ✅ Ready for Claude Code Integration
**Last Updated:** December 17, 2025
**All Tests:** PASSING
