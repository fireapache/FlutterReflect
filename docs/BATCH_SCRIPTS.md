# Batch Scripts Reference

Quick reference for all Windows batch scripts in the project.

## Visual Studio Solution Generation

### 📄 `generate_vs_solution.bat` (Interactive)
**Recommended for first-time setup**

```bash
generate_vs_solution.bat
```

**Features:**
- ✅ Auto-detects Visual Studio 2022/2019
- ✅ Option to clean previous build
- ✅ Interactive prompts
- ✅ Opens Visual Studio automatically
- ✅ Error checking and helpful messages

**What it does:**
1. Checks for CMake installation
2. Detects Visual Studio version
3. Optionally cleans build directory
4. Runs: `cmake -B build -G "Visual Studio 17 2022" -A x64`
5. Opens `build\FlutterReflect.sln`

---

### 📄 `generate_vs2022.bat` (Quick)
**For quick regeneration**

```bash
generate_vs2022.bat
```

**Features:**
- ✅ No prompts, just works
- ✅ Assumes VS 2022
- ✅ Opens solution immediately

**Best for:**
- Regenerating after CMakeLists.txt changes
- Quick project setup

---

## Building

### 📄 `build_debug.bat`
**Build Debug configuration**

```bash
build_debug.bat
```

**What it does:**
1. Checks if build directory exists
2. Builds Debug configuration with parallel compilation
3. Shows build result
4. Offers to run tests

**Output:**
- `build\Debug\flutter_reflect.exe`
- `build\Debug\flutter_reflect_tests.exe`

---

### 📄 `build_release.bat`
**Build Release configuration**

```bash
build_release.bat
```

**What it does:**
1. Checks if build directory exists
2. Builds Release configuration with parallel compilation
3. Shows executable size

**Output:**
- `build\Release\flutter_reflect.exe`
- Optimized, smaller binary

**Use for:**
- Final builds
- Performance testing
- Distribution

---

## Testing

### 📄 `run_tests.bat`
**Run unit tests**

```bash
run_tests.bat
```

**What it does:**
1. Looks for tests in Debug, then Release
2. Runs Google Test suite
3. Shows test results

**Output:**
```
[==========] Running 10 tests from 2 test suites.
...
[  PASSED  ] 10 tests.
```

---

## Maintenance

### 📄 `clean.bat`
**Clean build directory**

```bash
clean.bat
```

**What it does:**
1. Confirms deletion (safety check)
2. Removes entire `build\` directory
3. Forces fresh CMake configuration next time

**Use when:**
- Build system issues
- Dependency problems
- Want completely fresh start

**Note:** You'll need to regenerate the solution after cleaning.

---

## Quick Start Workflow

### First Time Setup
```bash
1. generate_vs_solution.bat   # Generate + open VS
2. Build in Visual Studio     # F7
3. Run tests                   # Ctrl+F5 on flutter_reflect_tests
```

### Daily Development
```bash
# Open existing solution
start build\FlutterReflect.sln

# Or rebuild from command line
build_debug.bat
```

### Before Committing
```bash
build_release.bat              # Ensure Release builds
run_tests.bat                  # Verify tests pass
```

### After Modifying CMakeLists.txt
```bash
generate_vs2022.bat            # Regenerate solution
# Visual Studio will auto-reload
```

### Troubleshooting
```bash
clean.bat                      # Clean everything
generate_vs_solution.bat       # Fresh start
```

---

## Script Locations

All scripts are in the project root:

```
FlutterReflect/
├── generate_vs_solution.bat   ⭐ Main generator (interactive)
├── generate_vs2022.bat         ⚡ Quick generator
├── build_debug.bat             🔨 Build Debug
├── build_release.bat           🚀 Build Release
├── run_tests.bat               🧪 Run tests
├── clean.bat                   🧹 Clean build
└── build/
    └── FlutterReflect.sln      📂 Solution file (after generation)
```

---

## Environment Requirements

### Required
- ✅ CMake 3.20+ (in PATH)
- ✅ Visual Studio 2022 or 2019
- ✅ Git (for dependency download)

### Optional
- Internet connection (first build only, for dependencies)

---

## Troubleshooting

### "CMake not found"
```bash
# Download from: https://cmake.org/download/
# Or via Chocolatey:
choco install cmake
```

### "Visual Studio not detected"
Scripts default to VS 2022. If you have a different version:
```bash
# Edit generate_vs2022.bat, change:
cmake -B build -G "Visual Studio 16 2019" -A x64  # For VS 2019
```

### "Build failed"
```bash
# Try clean build:
clean.bat
generate_vs_solution.bat
build_debug.bat
```

### Dependencies Download Failed
- Check internet connection
- Check firewall settings
- Try: `clean.bat` then regenerate

---

## Advanced Usage

### Custom Visual Studio Version
```bash
# VS 2019
cmake -B build -G "Visual Studio 16 2019" -A x64

# VS 2022 (default)
cmake -B build -G "Visual Studio 17 2022" -A x64
```

### Custom Build Directory
```bash
cmake -B mybuild -G "Visual Studio 17 2022" -A x64
cmake --build mybuild --config Debug
```

### Parallel Build (Faster)
```bash
# Use all CPU cores
cmake --build build --config Debug --parallel

# Or specify core count
cmake --build build --config Debug --parallel 8
```

### Build Specific Project
```bash
cmake --build build --config Debug --target flutter_reflect
cmake --build build --config Debug --target flutter_reflect_tests
```

### Verbose Build Output
```bash
cmake --build build --config Debug --verbose
```

---

## Integration with IDEs

### Visual Studio
Just open: `build\FlutterReflect.sln`

### Visual Studio Code
Install CMake Tools extension, then:
1. Ctrl+Shift+P > "CMake: Configure"
2. Select Visual Studio 2022 kit
3. F7 to build

### CLion
CLion can import CMake projects directly.
File > Open > Select CMakeLists.txt

---

## See Also

- [README.md](README.md) - Project overview
- [VISUAL_STUDIO_GUIDE.md](VISUAL_STUDIO_GUIDE.md) - Detailed VS instructions
- [CMakeLists.txt](CMakeLists.txt) - Build configuration

---

**Quick Tip:** For fastest workflow, just double-click `generate_vs_solution.bat` once, then use Visual Studio for everything else!
