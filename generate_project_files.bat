@echo off
echo Generating Visual Studio 2022 project files...
cmake -B build -S . -G "Visual Studio 17 2022"
echo Done. Open build\FlutterReflect.sln in Visual Studio.
