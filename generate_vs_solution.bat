@echo off
REM Generate Visual Studio solution for FlutterReflect
REM This script creates Visual Studio project files using CMake

echo ========================================
echo FlutterReflect - Visual Studio Solution Generator
echo ========================================
echo.

REM Check if CMake is installed
where cmake >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: CMake not found in PATH
    echo Please install CMake from https://cmake.org/download/
    pause
    exit /b 1
)

REM Detect Visual Studio version
set VS_VERSION=
set VS_YEAR=

REM Check for VS 2022 (most common)
if exist "C:\Program Files\Microsoft Visual Studio\2022" (
    set VS_VERSION=17
    set VS_YEAR=2022
    goto :found_vs
)

REM Check for VS 2019
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019" (
    set VS_VERSION=16
    set VS_YEAR=2019
    goto :found_vs
)

:found_vs
if "%VS_YEAR%"=="" (
    echo WARNING: Visual Studio not detected automatically
    echo Defaulting to Visual Studio 2022
    set VS_VERSION=17
    set VS_YEAR=2022
)

echo Detected/Using: Visual Studio %VS_YEAR%
echo.

REM Clean previous build directory (optional)
set CLEAN_BUILD=n
set /p CLEAN_BUILD="Clean previous build directory? (y/N): "
if /i "%CLEAN_BUILD%"=="y" (
    echo Cleaning build directory...
    if exist build (
        rmdir /s /q build
    )
)

REM Create build directory
if not exist build mkdir build

REM Generate Visual Studio solution
echo.
echo Generating Visual Studio %VS_YEAR% solution...
echo.

cmake -B build -G "Visual Studio %VS_VERSION% %VS_YEAR%" -A x64
if %errorlevel% neq 0 (
    echo.
    echo ERROR: CMake configuration failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Visual Studio solution generated
echo ========================================
echo.
echo Solution file: build\FlutterReflect.sln
echo.

REM Ask if user wants to open Visual Studio
set OPEN_VS=y
set /p OPEN_VS="Open Visual Studio now? (Y/n): "
if /i "%OPEN_VS%"=="n" goto :end

echo Opening Visual Studio...
start "" "build\FlutterReflect.sln"

:end
echo.
echo Done!
pause
