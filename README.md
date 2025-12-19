# FlutterReflect

A C++ Model Context Protocol (MCP) server that enables LLMs to autonomously inspect and interact with Flutter applications via the VM Service Protocol.

## Status: Phase 2 Complete ✅

Foundation & Build System complete. VM Service connection working end-to-end with real Flutter apps!

## What's Working

✅ **Core Infrastructure (Phase 1)**
- CMake build system with automatic dependency management
- JSON-RPC 2.0 protocol implementation
- STDIO transport for MCP communication
- MCP server with initialize and tools/list endpoints
- Tool registration system
- Comprehensive unit tests
- Windows build support

✅ **VM Service Connection (Phase 2 - Complete)**
- WebSocket client for Flutter VM Service Protocol
- JSON-RPC over WebSocket with async request/response correlation
- Isolate discovery and main isolate detection
- Connection management (connect/disconnect)
- **Tested with real Flutter app (Bookfy)** - Working perfectly!
- **MCP Tools Available:**
  - `flutter_connect` - Connect to Flutter app via VM Service
  - `flutter_disconnect` - Disconnect from Flutter app

## Building

### Requirements
- Windows 10/11
- Visual Studio 2019+ or MinGW-w64
- CMake 3.20+
- Git

### Dependencies (Auto-downloaded)
All dependencies are automatically fetched via CMake FetchContent:
- nlohmann/json v3.11.3 (JSON parsing)
- websocketpp 0.8.2 (WebSocket client)
- asio 1.28.0 (Async I/O)
- spdlog 1.12.0 (Logging)
- googletest 1.14.0 (Testing)

### Build Steps

#### Option 1: Using Batch Scripts (Easiest)

```bash
# Generate Visual Studio solution and open it
generate_vs_solution.bat

# Or quick generate for VS 2022
generate_vs2022.bat

# Build Debug
build_debug.bat

# Build Release
build_release.bat

# Run tests
run_tests.bat

# Clean build directory
clean.bat
```

#### Option 2: Command Line with CMake

```bash
# Configure
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# Build
cmake --build build --config Debug

# Run tests
./build/Debug/flutter_reflect_tests.exe
```

#### Option 3: Visual Studio IDE

See [VISUAL_STUDIO_GUIDE.md](VISUAL_STUDIO_GUIDE.md) for detailed instructions.

### Build Output
- `flutter_reflect.exe` - Main MCP server executable
- `flutter_reflect_tests.exe` - Unit test suite
- `simple_connect.exe` - Example program (placeholder)

## Usage

```bash
# Show help
flutter_reflect.exe --help

# Show version
flutter_reflect.exe --version

# Run with custom log level
flutter_reflect.exe --log-level debug

# Log to file
flutter_reflect.exe --log-file flutter_reflect.log
```

## Configuration for Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "flutter-reflect": {
      "command": "C:\\path\\to\\flutter_reflect.exe",
      "args": ["--log-level", "info"]
    }
  }
}
```

## Testing with Your Flutter App

### 1. Start your Flutter app with VM Service

```bash
# For Windows Desktop
flutter run -d windows --vm-service-port=8181 --disable-service-auth-codes

# For Chrome Web
flutter run -d chrome --vm-service-port=8181 --disable-service-auth-codes
```

### 2. Note the VM Service URI

Look for this line in the output:
```
A Dart VM Service on Windows is available at: http://127.0.0.1:8181/
```

The WebSocket URI is: `ws://127.0.0.1:8181/ws`

### 3. Test with Python script

```bash
cd E:\C++\FlutterReflect
python test_mcp.py
```

### 4. Or use with Claude Desktop

Once configured in Claude Desktop, you can ask Claude to:
- "Connect to my Flutter app at ws://127.0.0.1:8181/ws"
- "What's the VM version?"
- "Disconnect from the Flutter app"

### Test Results (Verified with Bookfy App)

```
✅ Initialize: FlutterReflect v1.0.0
✅ Tools available: ['flutter_connect', 'flutter_disconnect']
✅ Connected to Flutter app successfully
   - VM: Dart 3.11.0-93.1.beta
   - Main isolate: isolates/3149591706543463
   - Isolate count: 1
✅ Disconnected successfully
```

## Project Structure

```
FlutterReflect/
├── include/               # Public headers
│   ├── mcp/              # MCP protocol
│   ├── jsonrpc/          # JSON-RPC implementation
│   ├── flutter/          # Flutter VM Service (Phase 2+)
│   └── utils/            # Utilities
├── src/                  # Implementation files
│   ├── mcp/              # MCP server
│   ├── jsonrpc/          # JSON-RPC handlers
│   ├── flutter/          # Flutter integration (Phase 2+)
│   ├── tools/            # MCP tools (Phase 2+)
│   └── main.cpp          # Entry point
├── tests/                # Unit tests
├── examples/             # Example programs
└── CMakeLists.txt        # Build configuration
```

## Development Roadmap

### ✅ Phase 1: Foundation (Week 1) - COMPLETE
- CMake build system
- JSON-RPC 2.0 implementation
- STDIO transport
- MCP server skeleton
- Basic tests

### ✅ Phase 2: VM Service Connection (Week 2) - COMPLETE
- WebSocket client ✓
- Flutter VM Service integration ✓
- Connection tools (flutter_connect, flutter_disconnect) ✓
- Tested with real Flutter app (Bookfy) ✓

### 📋 Phase 3: Widget Inspection (Week 3)
- WidgetInspectorService wrapper
- Widget tree construction
- Inspection tools

### 📋 Phase 4: Selector Engine (Week 4)
- CSS-like selector syntax
- Widget matching
- Query tool

### 📋 Phase 5: Interaction Engine (Weeks 5-6)
- Tap, type, scroll operations
- Wait mechanisms
- Interaction tools

### 📋 Phase 6: Advanced Features (Week 7)
- Screenshot, navigation
- Error handling
- Performance optimization

### 📋 Phase 7: Release (Week 8)
- Windows packaging
- Documentation
- v1.0.0 release

## MCP Tools

### Connection Tools ✅ Implemented
- ✅ `flutter_connect` - Connect to Flutter app via VM Service
- ✅ `flutter_disconnect` - Disconnect from app

### Inspection Tools
- `flutter_get_tree` - Get widget tree snapshot
- `flutter_query` - Find widgets by selector
- `flutter_get_properties` - Get widget properties

### Interaction Tools
- `flutter_tap` - Tap on widget
- `flutter_type` - Type text
- `flutter_scroll` - Scroll widget
- `flutter_wait_for` - Wait for widget

### Utility Tools
- `flutter_screenshot` - Capture screenshot
- `flutter_navigate` - Navigate to route
- `flutter_go_back` - Go back

## Testing

```bash
# Run all tests
./build/Debug/flutter_reflect_tests.exe

# Run with CTest
cd build
ctest -C Debug --output-on-failure
```

Current test coverage:
- JSON-RPC message parsing/serialization ✓
- Request/response handling ✓
- Error handling ✓
- Notification support ✓

## Architecture

```
LLM (Claude) ←→ MCP Client (Claude Desktop) ←→ FlutterReflect (C++ Server)
                                                       ↓
                                        WebSocket (VM Service Protocol)
                                                       ↓
                                        Flutter App (Desktop or Web)
```

### Core Components

1. **MCP Server Layer**: JSON-RPC 2.0, STDIO transport, tool registry
2. **VM Service Client**: WebSocket client for Flutter VM Service (Phase 2)
3. **Widget Inspector**: High-level API for widget inspection (Phase 3)
4. **Selector Engine**: CSS-like selector syntax (Phase 4)
5. **Interaction Engine**: User interaction simulation (Phase 5)

## Current Limitations

- ✅ ~~No tools registered yet~~ - 2 connection tools now available!
- ✅ ~~Flutter VM Service connection not implemented~~ - Now implemented!
- Widget inspection not fully implemented yet (Phase 3 - Next)
- No widget query/selector capabilities yet (Phase 4)
- No interaction capabilities yet (tap, type, scroll - Phase 5)
- Testing with real Flutter app pending

## Contributing

Phase 2 (VM Service Connection) is partially complete! Next steps for contributors:

1. **Test Phase 2**: Test connection tools with real Flutter apps
2. **Phase 3**: Implement Widget Inspector and tree extraction
3. Create test Flutter applications for integration testing
4. Write integration tests for widget inspection

## License

To be determined.

## Links

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Flutter VM Service Protocol](https://github.com/dart-lang/sdk/blob/main/runtime/vm/service/service.md)
- [Implementation Plan](C:\Users\Vinicius Santos\.claude\plans\splendid-booping-dream.md)

---

**Built with**: C++17, CMake, nlohmann/json, websocketpp, asio, spdlog

**Target Platforms**: Windows Desktop + Flutter Web
