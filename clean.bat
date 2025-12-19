@echo off
REM Clean build directory

echo ========================================
echo FlutterReflect - Clean Build Directory
echo ========================================
echo.

if not exist build (
    echo Build directory doesn't exist. Nothing to clean.
    pause
    exit /b 0
)

echo WARNING: This will delete the entire build directory.
echo You will need to regenerate the Visual Studio solution.
echo.
set /p CONFIRM="Are you sure? (y/N): "

if /i "%CONFIRM%"=="y" (
    echo Cleaning...
    rmdir /s /q build
    echo Done! Build directory removed.
) else (
    echo Cancelled.
)

echo.
pause
