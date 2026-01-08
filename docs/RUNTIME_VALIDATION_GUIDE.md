# Runtime Validation Guide

**Purpose**: Execute the realistic GUI test suite to validate implementation completion
**Date**: 2026-01-07
**QA Fix Session**: 0

---

## Overview

This guide provides step-by-step instructions for executing the test suite in a Windows environment where Flutter and Python are available. The test suite has been implemented (13 test methods, 23 components) but requires runtime validation to achieve full sign-off.

---

## Prerequisites Checklist

Before running the tests, ensure you have:

- [ ] **Flutter SDK** installed and in PATH
  - Verify: Run `flutter --version` in Command Prompt or PowerShell
  - Required: Flutter 3.x for Windows desktop support

- [ ] **Python 3.7+** installed and in PATH
  - Verify: Run `python --version` or `python3 --version`
  - Required: For executing test_realistic_gui_suite.py

- [ ] **FlutterReflect executable** built
  - Path: `E:\C++\FlutterReflect\build\Debug\flutter_reflect.exe`
  - If not built: Run `cmake --build build --config Debug` from project root

- [ ] **Flutter Sample App** ready to run
  - Location: `examples/flutter_sample_app`
  - This is the test subject app

---

## Phase 1: Start Flutter Sample App

**Terminal 1 - Command Prompt or PowerShell:**

```bash
# Navigate to sample app directory
cd E:\dev\FlutterReflect\.auto-claude\worktrees\tasks\001-create-realistic-test-cases\examples\flutter_sample_app

# Start Flutter app with VM Service on port 8181
flutter run -d windows --vm-service-port=8181 --disable-service-auth-codes
```

**Expected Output:**
```
Flutter run key commands.
r Hot reload.
R Hot restart.
h List all available interactive commands.
q Quit (terminate the application on the device).

A Dart VM Service on Windows is available at: http://127.0.0.1:8181/
The Flutter app is running.
```

**Important**: Keep this terminal open and the app running throughout testing.

---

## Phase 2: Verify Flutter App is Ready

**Check VM Service is accessible:**

Open a browser and navigate to: `http://127.0.0.1:8181/`

You should see the Dart VM Service page showing the running Flutter app.

---

## Phase 3: Run Test Suite

**Terminal 2 - Command Prompt or PowerShell:**

```bash
# Navigate to worktree directory
cd E:\dev\FlutterReflect\.auto-claude\worktrees\tasks\001-create-realistic-test-cases

# Run the realistic GUI test suite
python test_realistic_gui_suite.py
```

**What Happens:**

The test suite will:
1. **Initialize** FlutterReflect server via MCP protocol
2. **Connect** to Flutter app via VM Service (ws://127.0.0.1:8181/ws)
3. **Verify** app is responsive (capture initial widget tree)
4. **Execute** 13 test methods sequentially:
   - `test_app_initialization` - Connection and baseline state
   - `test_input_fields` - Text input in add and search fields
   - `test_add_todo_button` - Add new todo items
   - `test_checkbox_toggle` - Toggle todo completion state
   - `test_mark_all_complete` - Batch complete all todos
   - `test_delete_button` - Delete individual todos
   - `test_clear_all` - Clear all todos with confirmation
   - `test_navigate_to_stats` - Navigate to Stats screen
   - `test_back_navigation` - Return to Home screen
   - `test_search_field` - Search filtering
   - `test_filter_buttons` - Filter by All/Active/Completed
   - `test_full_workflow_e2e` - Complete user journey
   - `test_edge_cases` - Error scenarios and edge cases

5. **Verify** each interaction occurred (via widget tree comparison)
6. **Detect** state changes before/after each interaction
7. **Generate** comprehensive test report

---

## Expected Test Output

### Successful Run

```
========================================
Realistic GUI Test Suite for Flutter Sample App
========================================

Starting tests at 2026-01-07 15:30:00

Test Suite: Realistic GUI Tests
Platform: Windows
App: flutter_reflect.exe

[1/13] test_app_initialization
  ✅ Connection successful
  ✅ Widget tree captured (42 nodes)
  ✅ App ready for testing

[2/13] test_input_fields
  ✅ Add todo input field tested
  ✅ Search input field tested
  ✅ Text entry and clearing verified

[3/13] test_add_todo_button
  ✅ Todo added: "Test todo item"
  ✅ Widget count increased: 5 → 6
  ✅ Stats counter updated: 5/5 → 6/5

... (all tests pass)

========================================
Test Suite Summary
========================================
Total Tests: 13
Passed: 13
Failed: 0
Skipped: 0

Component Coverage: 23/23 (100%)
Runtime: ~2 minutes

Status: ✅ ALL TESTS PASSED
```

### If Tests Fail

**Common Issues and Solutions:**

1. **"Connection refused" on port 8181**
   - Cause: Flutter app not running or wrong port
   - Fix: Ensure Terminal 1 has `flutter run` running and shows VM Service on 8181

2. **"flutter_reflect.exe not found"**
   - Cause: Executable not built
   - Fix: Run `cmake --build build --config Debug` from `E:\C++\FlutterReflect\`

3. **"Widget not found: addTodoInput"**
   - Cause: App not fully loaded or wrong screen
   - Fix: Wait for app to fully initialize, ensure HomeScreen is visible

4. **"Python not found"**
   - Cause: Python not in PATH
   - Fix: Add Python to Windows PATH or use full path to python.exe

---

## Phase 4: Review Test Report

After tests complete, review the generated report:

**Location**: `docs/realistic_test_report.md`

The report contains:
- Executive summary
- Component inventory (23 items)
- Detailed test breakdown
- Coverage analysis
- Test architecture documentation
- Performance metrics
- Known limitations (if any)

---

## Phase 5: Validation Criteria

For full QA sign-off, verify:

✅ **All 13 tests pass** (100% success rate)
✅ **All 23 UI components tested** (100% coverage)
✅ **No app crashes** during test execution
✅ **State change detection working** (widget trees show differences)
✅ **No console errors** in Flutter app during tests
✅ **Test report generated** successfully

---

## Troubleshooting

### Issue: Tests Hang or Timeout

**Symptoms**: Test progress stops, no output for 30+ seconds

**Solutions**:
1. Check if Flutter app is frozen (restart Terminal 1)
2. Verify VM Service is still accessible (refresh http://127.0.0.1:8181/)
3. Restart test suite (Ctrl+C in Terminal 2, then run again)

### Issue: Intermittent Failures

**Symptoms**: Tests sometimes pass, sometimes fail

**Solutions**:
1. Ensure no rapid interactions before tests start (let app settle for 5 seconds)
2. Close other apps consuming CPU/memory
3. Restart Flutter app and test suite

### Issue: Wrong Executable Path

**Symptoms**: "flutter_reflect.exe not found at E:\C++\FlutterReflect\..."

**Solution**:
If your build directory is different, update the path in `test_realistic_gui_suite.py`:

```python
# Line 248 - Change this path to your actual build location
self.executable = r"YOUR_PATH_HERE\flutter_reflect.exe"
```

---

## Advanced: Manual Testing

If automated tests fail, you can manually verify key functionality:

1. **Open Flutter app** (should show 5 sample todos)
2. **Add a todo**: Type in input field, click "Add Task"
3. **Complete a todo**: Click checkbox on any todo
4. **Navigate**: Click "Stats" button, verify stats screen
5. **Filter**: On Stats screen, click "Completed" button
6. **Go back**: Click back button, return to Home
7. **Delete**: Click delete button on a todo

If all manual interactions work, the implementation is functional.

---

## Next Steps After Successful Validation

Once all tests pass:

1. **Document results** in `qa_report.md` (add runtime validation section)
2. **Update** `implementation_plan.json` qa_signoff.status to "approved"
3. **Commit** validation results with message:
   ```
   fix: Complete runtime validation

   - All 13 tests passed successfully
   - 23/23 components covered (100%)
   - State change detection verified
   - App stable throughout test suite

   Runtime validation complete - ready for production.
   ```

4. **Notify QA Agent** that runtime validation is complete

---

## Contact and Support

**If issues persist:**

1. Check the test file: `test_realistic_gui_suite.py` (4,197 lines)
2. Review the spec: `.auto-claude/specs/001-create-realistic-test-cases/spec.md`
3. Check implementation plan: `.auto-claude/specs/001-create-realistic-test-cases/implementation_plan.json`
4. Review previous QA report: `.auto-claude/specs/001-create-realistic-test-cases/qa_report.md`

---

## Summary

**What this validates:**
- ✅ All 17 subtasks implemented correctly
- ✅ All 13 test methods execute successfully
- ✅ All 23 UI components tested and verified
- ✅ State change detection working (widget tree comparison)
- ✅ MCP protocol communication (JSON-RPC 2.0)
- ✅ FlutterReflect server tools (connect, tap, type, get_tree, etc.)
- ✅ App stability (no crashes during full test suite)

**Expected runtime**: ~2 minutes

**Success criteria**: 13/13 tests pass, 23/23 components verified

**Ready for production**: ✅ (after successful validation)

---

**Generated by**: QA Fix Agent (Session 0)
**Date**: 2026-01-07
**Purpose**: Runtime validation guide for test suite execution
