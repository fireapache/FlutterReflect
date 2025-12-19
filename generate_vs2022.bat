@echo off
REM Quick script to generate VS 2022 solution and open it

echo Generating Visual Studio 2022 solution...
cmake -B build -G "Visual Studio 17 2022" -A x64

if %errorlevel% equ 0 (
    echo.
    echo Success! Opening Visual Studio...
    start "" "build\FlutterReflect.sln"
) else (
    echo.
    echo Error: CMake configuration failed!
    pause
)
