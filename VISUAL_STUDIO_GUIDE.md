# Visual Studio Quick Start Guide

## Generating Visual Studio Solution

### Option 1: Interactive (Recommended)
Double-click `generate_vs_solution.bat`

This will:
- Detect your Visual Studio version automatically
- Ask if you want to clean previous build
- Generate the solution
- Optionally open Visual Studio

### Option 2: Quick Generate & Open
Double-click `generate_vs2022.bat`

Generates VS 2022 solution and opens it immediately.

### Option 3: Manual (Command Line)
```bash
cmake -B build -G "Visual Studio 17 2022" -A x64
```

## Opening in Visual Studio

After generation, open:
```
build\FlutterReflect.sln
```

Or double-click the `.sln` file in Windows Explorer.

## Visual Studio Projects

The solution contains these projects:

### Main Projects
- **flutter_reflect** - Main MCP server executable
- **flutter_reflect_lib** - Core library (static)
- **flutter_reflect_tests** - Unit test suite
- **simple_connect** - Example program

### Utility Projects
- **ALL_BUILD** - Builds all projects
- **RUN_TESTS** - Runs all tests
- **ZERO_CHECK** - Checks if CMake needs to rerun

### External Dependencies
- **gtest, gtest_main** - Google Test framework
- **gmock, gmock_main** - Google Mock framework
- **spdlog** - Logging library

## Building in Visual Studio

### Build Configuration
1. Select configuration: **Debug** or **Release**
2. Select platform: **x64**
3. Build > Build Solution (or press F7)

### Quick Build Options
- **Build Solution** (F7) - Build all projects
- **Build flutter_reflect** - Build only main executable
- **Build flutter_reflect_tests** - Build only tests
- **Rebuild Solution** - Clean and rebuild all

### Output Locations
- Debug: `build\Debug\flutter_reflect.exe`
- Release: `build\Release\flutter_reflect.exe`

## Running & Debugging

### Run Main Executable
1. Right-click **flutter_reflect** project
2. Set as StartUp Project
3. Press F5 (Debug) or Ctrl+F5 (Run without debugging)

### Run with Command-Line Arguments
1. Right-click **flutter_reflect** project
2. Properties > Debugging > Command Arguments
3. Add arguments, e.g., `--log-level debug`

### Run Tests
1. Right-click **flutter_reflect_tests** project
2. Set as StartUp Project
3. Press Ctrl+F5

Or use Test Explorer:
- View > Test Explorer
- Run All Tests

## Quick Build Scripts

### Build Debug
Double-click `build_debug.bat`
- Builds Debug configuration
- Offers to run tests

### Build Release
Double-click `build_release.bat`
- Builds Release configuration
- Shows executable size

### Run Tests
Double-click `run_tests.bat`
- Runs unit tests (Debug or Release)

### Clean Build
Double-click `clean.bat`
- Removes entire build directory
- Requires regenerating solution

## Useful Visual Studio Features

### Code Navigation
- **Go to Definition** (F12) - Jump to definition
- **Find All References** (Shift+F12) - Find usages
- **Go to File** (Ctrl+,) - Quick file search

### Debugging
- **Breakpoints** (F9) - Toggle breakpoint
- **Step Over** (F10) - Execute next line
- **Step Into** (F11) - Step into function
- **Watch Window** - Monitor variables

### Build Output
- View > Output (Ctrl+Alt+O)
- Shows compiler warnings and errors
- Double-click errors to jump to code

## Common Issues

### "CMake not found"
- Install CMake from https://cmake.org/download/
- Add to PATH during installation

### "Visual Studio not detected"
- Install Visual Studio 2022 Community
- Include "Desktop development with C++"

### Build Errors
- Clean solution: Build > Clean Solution
- Regenerate: Run `generate_vs_solution.bat` again
- Check build output for specific errors

### Missing Dependencies
Dependencies are downloaded automatically by CMake.
If download fails:
- Check internet connection
- Try regenerating solution
- Check firewall/proxy settings

## Project Structure in Visual Studio

```
FlutterReflect (Solution)
├── flutter_reflect (Executable)
│   └── main.cpp
├── flutter_reflect_lib (Static Library)
│   ├── Header Files
│   │   ├── mcp/
│   │   ├── jsonrpc/
│   │   ├── flutter/
│   │   └── utils/
│   └── Source Files
│       ├── mcp/
│       ├── jsonrpc/
│       ├── flutter/
│       └── tools/
├── flutter_reflect_tests (Executable)
│   └── tests/
├── simple_connect (Executable)
│   └── examples/
└── External Dependencies
    ├── nlohmann_json
    ├── spdlog
    ├── websocketpp
    ├── asio
    └── googletest
```

## Productivity Tips

### Set Startup Project
Right-click project > Set as StartUp Project
(Bold project name indicates startup project)

### Multi-Core Build
Tools > Options > Projects and Solutions > Build and Run
Set "maximum number of parallel project builds" to CPU count

### Hide External Dependencies
Right-click solution > Properties > Common Properties
Uncheck "Show All Files" to reduce clutter

### IntelliSense Performance
For faster IntelliSense:
- Tools > Options > Text Editor > C/C++ > Advanced
- Set "Disable IntelliSense" to False
- Set "Max Cached Translation Units" to 4-8

## NuGet Packages (Not Used)

This project uses CMake FetchContent, not NuGet.
All dependencies are C++ libraries managed by CMake.

## Regenerating Solution

If you modify `CMakeLists.txt`:
1. Save changes
2. Run `generate_vs_solution.bat` again
3. Visual Studio will detect changes
4. Reload solution when prompted

Or let Visual Studio auto-regenerate:
- Build solution
- ZERO_CHECK will detect changes
- Solution will regenerate automatically

## Additional Resources

- [CMake Documentation](https://cmake.org/documentation/)
- [Visual Studio C++ Docs](https://docs.microsoft.com/en-us/cpp/)
- [FlutterReflect README](README.md)
- [Implementation Plan](C:\Users\Vinicius Santos\.claude\plans\splendid-booping-dream.md)

---

**Quick Start**: Double-click `generate_vs_solution.bat`, then open `build\FlutterReflect.sln`
