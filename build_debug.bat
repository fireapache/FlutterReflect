@echo off
REM Build FlutterReflect in Debug mode

echo ========================================
echo Building FlutterReflect (Debug)
echo ========================================
echo.

REM Check if build directory exists
if not exist build (
    echo Build directory not found!
    echo Run generate_vs_solution.bat first.
    pause
    exit /b 1
)

REM Build Debug configuration
echo Building Debug configuration...
cmake --build build --config Debug --parallel

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Build successful!
    echo ========================================
    echo.
    echo Executable: build\Debug\flutter_reflect.exe
    echo Tests: build\Debug\flutter_reflect_tests.exe
    echo.
    echo Run tests? (Y/n)
    set RUN_TESTS=y
    set /p RUN_TESTS=
    if /i "!RUN_TESTS!"=="y" (
        echo.
        echo Running tests...
        build\Debug\flutter_reflect_tests.exe
    )
) else (
    echo.
    echo Build failed!
)

pause
