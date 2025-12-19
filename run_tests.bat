@echo off
REM Run FlutterReflect unit tests

echo ========================================
echo FlutterReflect - Unit Tests
echo ========================================
echo.

if exist build\Debug\flutter_reflect_tests.exe (
    echo Running Debug tests...
    build\Debug\flutter_reflect_tests.exe
) else if exist build\Release\flutter_reflect_tests.exe (
    echo Running Release tests...
    build\Release\flutter_reflect_tests.exe
) else (
    echo Tests executable not found!
    echo Build the project first.
    pause
    exit /b 1
)

echo.
pause
