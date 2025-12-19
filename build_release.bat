@echo off
REM Build FlutterReflect in Release mode

echo ========================================
echo Building FlutterReflect (Release)
echo ========================================
echo.

REM Check if build directory exists
if not exist build (
    echo Build directory not found!
    echo Run generate_vs_solution.bat first.
    pause
    exit /b 1
)

REM Build Release configuration
echo Building Release configuration...
cmake --build build --config Release --parallel

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Build successful!
    echo ========================================
    echo.
    echo Executable: build\Release\flutter_reflect.exe
    echo Size:
    dir /s build\Release\flutter_reflect.exe | findstr flutter_reflect.exe
    echo.
) else (
    echo.
    echo Build failed!
)

pause
