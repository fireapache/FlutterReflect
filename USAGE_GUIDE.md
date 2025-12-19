# FlutterReflect Usage Guide

## Overview

FlutterReflect is an **MCP (Model Context Protocol) server** that enables AI agents to interact with Flutter applications. It's **not** a traditional CLI tool - instead, it runs as a server that communicates with LLMs via JSON-RPC 2.0.

**Designed for: Claude Code** - The AI-powered command-line assistant for software development.

---

## How to Use with Claude Code

### Method 1: Through Claude Code (Primary Method)

This is the **primary** and **recommended** way to use FlutterReflect.

#### Step 1: Install FlutterReflect as an MCP Server

Claude Code can discover and use MCP servers automatically. To set up FlutterReflect:

**Option A: Add to Claude Code MCP Settings**

Add the MCP server to your Claude Code configuration:

```bash
# The configuration location depends on your Claude Code setup
# Typically in your user settings or project .claude/settings.json
```

**Option B: Use MCP Server Command**

You can also specify the MCP server directly when starting Claude Code or via settings.

#### Step 2: Verify MCP Server is Loaded

When Claude Code starts, FlutterReflect should be automatically discovered. You can verify by asking:

```
You: "What Flutter tools are available?"

Claude Code: I have access to 10 Flutter tools:
- flutter_list_instances - Discover running Flutter apps
- flutter_launch - Launch Flutter apps programmatically
- flutter_connect - Connect to Flutter apps
[... and 7 more tools ...]
```

#### Step 3: Use FlutterReflect Tools in Claude Code

Now you can use natural language in Claude Code:

```
You: "List all running Flutter apps on my system"

Claude Code: [Uses flutter_list_instances tool]
I found 2 running Flutter applications:
1. Bookfy on port 8181
2. my_flutter_app on port 8182

You: "Connect to the Bookfy app and show me the widget tree"

Claude Code: [Uses flutter_connect, then flutter_get_tree]
Connected to Bookfy. Here's the widget tree:
- MaterialApp
  - Scaffold
    - AppBar
      - Text: "Bookfy"
    - Column
      - ElevatedButton: "Login"
      - TextField: "Email"

You: "Tap on the Login button"

Claude Code: [Uses flutter_tap]
Tapped the Login button successfully.
```

**That's it!** Claude Code handles all the JSON-RPC communication behind the scenes.

---

### Method 2: Through Claude API (For Custom Integrations)

If you're building a custom application that uses the Claude API, you can configure MCP servers programmatically.

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

# Configure MCP server
mcp_config = {
    "mcpServers": {
        "flutter-reflect": {
            "command": "E:\\C++\\FlutterReflect\\build\\Release\\flutter_reflect.exe"
        }
    }
}

# Use Claude with MCP server
response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    mcp_servers=mcp_config,
    messages=[{
        "role": "user",
        "content": "List all running Flutter apps"
    }]
)

print(response.content)
```

---

## How Claude Code Uses It

When Claude Code is configured with FlutterReflect, here's what happens:

### 1. Tool Discovery

When the LLM starts, it queries FlutterReflect for available tools:

**LLM sends:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 1
}
```

**FlutterReflect responds:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "flutter_list_instances",
        "description": "Discover running Flutter applications...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "port_start": {"type": "integer", "default": 8080},
            "port_end": {"type": "integer", "default": 8200},
            "timeout_ms": {"type": "integer", "default": 500}
          }
        }
      },
      {
        "name": "flutter_connect",
        "description": "Connect to Flutter app...",
        "inputSchema": {...}
      }
      // ... 8 more tools
    ]
  }
}
```

### 2. Tool Execution

When the LLM wants to use a tool, it sends a tool call request:

**LLM sends:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "flutter_list_instances",
    "arguments": {
      "port_start": 8180,
      "port_end": 8185,
      "timeout_ms": 500
    }
  },
  "id": 2
}
```

**FlutterReflect responds:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\":true,\"data\":{\"instances\":[...],\"count\":1}}"
      }
    ]
  }
}
```

### 3. Autonomous Workflow

The LLM can chain multiple tool calls autonomously:

```
User: "Test the login flow of my Flutter app"

LLM thinks:
1. First, find running apps → flutter_list_instances
2. Connect to the app → flutter_connect
3. Get the widget tree → flutter_get_tree
4. Find the email field → flutter_find(selector="TextField")
5. Type email → flutter_type(text="test@example.com")
6. Find login button → flutter_find(selector="Button[text='Login']")
7. Tap it → flutter_tap
8. Verify success → flutter_get_tree (check for success screen)
```

---

## Manual Testing from CLI (Advanced)

For **testing** or **debugging**, you can manually interact with FlutterReflect using JSON-RPC:

### Method 1: Using Python Script

```python
#!/usr/bin/env python3
import subprocess
import json

# Start FlutterReflect
proc = subprocess.Popen(
    ["flutter_reflect.exe"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

def send_request(method, params, request_id):
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    proc.stdin.write(json.dumps(request).encode() + b'\n')
    proc.stdin.flush()

    response = proc.stdout.readline().decode().strip()
    return json.loads(response)

# Initialize
response = send_request("initialize", {
    "protocolVersion": "2024-11-05",
    "clientInfo": {"name": "test", "version": "1.0"},
    "capabilities": {}
}, 1)
print("Initialized:", response)

# List tools
response = send_request("tools/list", {}, 2)
print("\nAvailable tools:")
for tool in response['result']['tools']:
    print(f"  - {tool['name']}")

# Discover Flutter instances
response = send_request("tools/call", {
    "name": "flutter_list_instances",
    "arguments": {
        "port_start": 8180,
        "port_end": 8185,
        "timeout_ms": 500
    }
}, 3)
print("\nDiscovery result:", response)

proc.terminate()
```

### Method 2: Using curl + Named Pipes (Unix/Linux)

```bash
# Start server in background
mkfifo /tmp/mcp_in /tmp/mcp_out
flutter_reflect < /tmp/mcp_in > /tmp/mcp_out &

# Send initialize request
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test","version":"1.0"},"capabilities":{}},"id":1}' > /tmp/mcp_in

# Read response
cat /tmp/mcp_out

# Send tool list request
echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}' > /tmp/mcp_in

# Read response
cat /tmp/mcp_out
```

### Method 3: Interactive Node.js REPL

```javascript
const { spawn } = require('child_process');
const readline = require('readline');

// Start FlutterReflect
const proc = spawn('flutter_reflect.exe');

// Setup readline
const rl = readline.createInterface({
  input: proc.stdout,
  output: process.stdout,
  terminal: false
});

// Listen for responses
rl.on('line', (line) => {
  console.log('Response:', JSON.parse(line));
});

// Send request
function sendRequest(method, params, id) {
  const request = JSON.stringify({
    jsonrpc: "2.0",
    method,
    params,
    id
  });
  proc.stdin.write(request + '\n');
}

// Initialize
sendRequest("initialize", {
  protocolVersion: "2024-11-05",
  clientInfo: { name: "test", version: "1.0" },
  capabilities: {}
}, 1);

// List instances
setTimeout(() => {
  sendRequest("tools/call", {
    name: "flutter_list_instances",
    arguments: { port_start: 8180, port_end: 8185 }
  }, 2);
}, 1000);
```

---

## Example Workflows

### Workflow 1: Autonomous Testing

**User says to Claude:**
```
"Test the login flow of my Flutter app. It's running on my machine."
```

**Claude executes:**
```
1. flutter_list_instances()
   → Found app on port 8181

2. flutter_connect(port=8181)
   → Connected to "my_app"

3. flutter_get_tree(max_depth=5)
   → Found widget tree

4. flutter_find(selector="TextField[contains='email']")
   → Found email field: widget-42

5. flutter_type(widget_id="widget-42", text="test@example.com")
   → Typed email

6. flutter_find(selector="TextField[contains='password']")
   → Found password field: widget-43

7. flutter_type(widget_id="widget-43", text="password123")
   → Typed password

8. flutter_tap(selector="Button[text='Login']")
   → Tapped login button

9. flutter_get_tree(max_depth=3)
   → Check for success screen

10. flutter_disconnect()
    → Disconnected
```

**Claude reports:**
```
✅ Login flow test completed successfully!

Steps executed:
1. Discovered app on port 8181
2. Connected to "my_app"
3. Found and filled email field: test@example.com
4. Found and filled password field
5. Tapped Login button
6. Verified success screen appeared

The login flow is working correctly.
```

### Workflow 2: App Development Assistance

**User says to Claude:**
```
"I want to add a new button to my Flutter app. Show me where to place it."
```

**Claude executes:**
```
1. flutter_list_instances()
2. flutter_connect()
3. flutter_get_tree(max_depth=10)
4. Analyzes widget hierarchy
```

**Claude suggests:**
```
I can see your current layout:

MaterialApp
└── Scaffold
    ├── AppBar (Title: "My App")
    └── Column
        ├── Text: "Welcome"
        └── Row
            ├── ElevatedButton: "Submit"
            └── ElevatedButton: "Cancel"

I recommend adding your new button in one of these locations:

1. In the existing Row (next to Submit/Cancel):
   Row(
     children: [
       ElevatedButton("Submit"),
       ElevatedButton("Cancel"),
       ElevatedButton("New Button"),  // ← Add here
     ]
   )

2. As a new Row below the existing one:
   Column(
     children: [
       Text("Welcome"),
       Row(...existing buttons...),
       Row(  // ← Add new row
         children: [
           ElevatedButton("New Button"),
         ]
       ),
     ]
   )

Which location would you prefer?
```

### Workflow 3: Bug Diagnosis

**User says to Claude:**
```
"My login button isn't working. Can you help diagnose the issue?"
```

**Claude executes:**
```
1. flutter_list_instances()
2. flutter_connect()
3. flutter_find(selector="Button[text='Login']")
4. flutter_get_properties(widget_id="...")
```

**Claude reports:**
```
I found the issue with your login button:

Button Properties:
- Type: ElevatedButton
- Text: "Login"
- Enabled: false ❌ (This is the problem!)
- Visible: true
- Position: (x: 150, y: 300)
- Size: 120x48

The button is disabled (enabled=false). Check your Flutter code for:

1. Condition disabling the button:
   ElevatedButton(
     onPressed: _isValid ? _handleLogin : null,  // ← Check _isValid
     ...
   )

2. Form validation:
   - Are all required fields filled?
   - Is there a validation condition preventing enablement?

3. State management:
   - Check if button state is properly managed
   - Verify setState() is called after input changes
```

---

## Command-Line Options

FlutterReflect supports these flags for configuration:

```bash
# Display help
flutter_reflect --help
flutter_reflect -h

# Display version
flutter_reflect --version
flutter_reflect -v

# Set logging level
flutter_reflect --log-level debug
flutter_reflect --log-level info   # default
flutter_reflect --log-level warn
flutter_reflect --log-level error

# Log to file instead of stderr
flutter_reflect --log-file flutter_reflect.log

# Combine options
flutter_reflect --log-level debug --log-file debug.log
```

**Note:** These options are for server configuration, not for running tools. Tools are executed via JSON-RPC when the server is running.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User (Developer)                                            │
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
│ - Receives tool calls                                       │
│ - Executes Flutter operations                               │
│ - Returns results                                           │
└────────────────────┬────────────────────────────────────────┘
                     │ Flutter VM Service Protocol (WebSocket)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Flutter Application                                         │
│ - Running in debug mode                                     │
│ - VM Service enabled                                        │
│ - Flutter Driver enabled (for interaction)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Points

### ✅ DO:
- Configure FlutterReflect as an MCP server for Claude Code
- Use natural language in Claude Code to interact with Flutter apps
- Let Claude Code handle tool calls and JSON-RPC communication
- Use `--help` and `--version` flags to get information
- Use logging flags for debugging server issues

### ❌ DON'T:
- Try to use FlutterReflect like a traditional CLI tool (e.g., `flutter_reflect list-apps`)
- Send raw JSON-RPC manually (unless testing/debugging)
- Expect interactive prompts or CLI menus
- Use it without configuring as an MCP server in Claude Code

### 💡 REMEMBER:
- FlutterReflect is an **MCP server**, not a CLI tool
- It communicates via **JSON-RPC 2.0 over STDIO**
- Developers interact through **Claude Code** CLI
- Claude Code autonomously calls tools based on user intent
- Manual JSON-RPC is only for testing/debugging

---

## Troubleshooting

### "How do I run flutter_list_instances from command line?"

You don't run tools directly. Instead:

1. **Configure as MCP server in Claude Code**
2. **Tell Claude Code** what you want: "List all running Flutter apps"
3. **Claude Code executes** `flutter_list_instances` tool automatically

### "FlutterReflect starts then exits immediately"

That's normal! MCP servers:
- Wait for JSON-RPC initialization via STDIN
- Serve requests until parent process disconnects
- Exit when STDIN closes

This is managed by Claude Code automatically when it needs to use the tools.

### "I want to test without Claude Code"

Use the Python/Node.js scripts above to send JSON-RPC manually for debugging.

---

## Summary

| Use Case | Method | User Action |
|----------|--------|-------------|
| **Normal Use** | Claude Code CLI | Configure as MCP server, use natural language |
| **API Integration** | Claude API | Configure MCP in API calls programmatically |
| **Testing** | Manual JSON-RPC | Write Python/Node.js scripts to send requests |
| **Debugging** | Log flags | Use `--log-level debug --log-file debug.log` |
| **Information** | Help flags | Use `--help` or `--version` |

**Bottom line:** Developers never interact with FlutterReflect directly from CLI. They talk to Claude Code, and Claude Code uses FlutterReflect behind the scenes via MCP protocol.

---

**For more information:**
- MCP Protocol: https://modelcontextprotocol.io
- Claude Desktop: https://claude.ai/download
- FlutterReflect Documentation: See AUTONOMOUS_WORKFLOW.md
