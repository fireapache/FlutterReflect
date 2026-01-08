@echo off
echo ========================================
echo FlutterReflect - Test Suite
echo ========================================
echo.

REM Run pytest tests
echo Running pytest tests...
pytest tests/ -v --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Tests FAILED
    exit /b 1
)

echo.
echo Tests PASSED
