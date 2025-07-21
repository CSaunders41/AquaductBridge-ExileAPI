@echo off
echo Building AqueductBridge plugin...
echo.

REM Check if dotnet is installed
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: .NET SDK not found. Please install .NET 8.0 SDK.
    pause
    exit /b 1
)

REM Check if required DLLs exist (should be in ExileApi-Compiled root)
if not exist "..\..\..\ExileCore.dll" (
    echo WARNING: ExileCore.dll not found. Please ensure this plugin is in the correct directory:
    echo Expected path: ExileApi-Compiled/Plugins/Source/AquaductBridge-ExileAPI/
    echo ExileCore.dll should be at: ExileApi-Compiled/ExileCore.dll
)

if not exist "..\..\..\GameOffsets.dll" (
    echo WARNING: GameOffsets.dll not found in ExileApi-Compiled root directory.
)

if not exist "..\..\..\ImGui.NET.dll" (
    echo WARNING: ImGui.NET.dll not found in ExileApi-Compiled root directory.
)

if not exist "..\..\..\ProcessMemoryUtilities.dll" (
    echo WARNING: ProcessMemoryUtilities.dll not found in ExileApi-Compiled root directory.
)

REM Build the project
echo Building project...
dotnet build --configuration Release

if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo SUCCESS: AqueductBridge.dll built successfully!
echo Built to: bin\Release\AqueductBridge.dll
echo.
echo Installation:
echo 1. The plugin should already be in the correct location if you placed the source in:
echo    ExileApi-Compiled/Plugins/Source/AquaductBridge-ExileAPI/
echo 2. Start ExileApi-Compiled.exe
echo 3. Enable the AqueductBridge plugin in the plugins menu
echo 4. The HTTP server will start automatically on port 50002
echo.
echo For aqueduct_runner:
echo 1. Ensure this plugin is running and HTTP server is started
echo 2. Run your aqueduct_runner Python script
echo 3. It should connect to http://127.0.0.1:50002 automatically
echo.
pause 