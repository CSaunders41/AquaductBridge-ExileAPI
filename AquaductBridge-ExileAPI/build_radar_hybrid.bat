@echo off
echo.
echo ===============================================
echo Building RadarMovement Hybrid v5.0
echo ===============================================
echo.

REM Check if dotnet is installed
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: .NET SDK not found. Please install .NET 8.0 SDK.
    echo Download from: https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

echo Found .NET SDK version:
dotnet --version
echo.

REM Check if we're in the right directory structure
if not exist "..\..\..\..\ExileCore.dll" (
    echo WARNING: ExileCore.dll not found at expected location.
    echo.
    echo This plugin should be placed in:
    echo   ExileApi-Compiled\Plugins\Source\AqueductBridge-ExileAPI\
    echo.
    echo ExileCore.dll should be at:
    echo   ExileApi-Compiled\ExileCore.dll
    echo.
    echo Continuing build anyway...
    echo.
)

REM Clean any previous builds
if exist "bin\" (
    echo Cleaning previous build...
    rmdir /s /q "bin"
)

if exist "obj\" (
    rmdir /s /q "obj"
)

REM Build the specific RadarMovement project (avoids duplicate compilation)
echo Building RadarMovement Hybrid plugin...
echo Command: dotnet build RadarMovement.csproj --configuration Release --verbosity minimal
echo.

dotnet build RadarMovement.csproj --configuration Release --verbosity minimal

if errorlevel 1 (
    echo.
    echo ===============================================
    echo BUILD FAILED
    echo ===============================================
    echo.
    echo Common solutions:
    echo 1. Make sure all required files are present:
    echo    - RadarMovement.cs
    echo    - RadarTask.cs  
    echo    - Utils/AqueductPathfinder.cs
    echo    - Utils/AdvancedMouse.cs
    echo    - Utils/LineOfSight.cs
    echo    - Utils/EventBus.cs
    echo    - Utils/BinaryHeap.cs
    echo.
    echo 2. Ensure ExileCore.dll and dependencies are in the right location
    echo.
    echo 3. Check that no duplicate class files exist
    echo.
    echo Run verify_build_structure.bat for detailed diagnostics.
    echo.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo BUILD SUCCESSFUL!
echo ===============================================
echo.

REM Show build output location
if exist "bin\Release\net8.0\RadarMovement.dll" (
    echo Successfully built: bin\Release\net8.0\RadarMovement.dll
    echo File size: 
    dir "bin\Release\net8.0\RadarMovement.dll" | find "RadarMovement.dll"
) else (
    echo WARNING: Expected output file not found at bin\Release\net8.0\RadarMovement.dll
    echo Checking for alternative locations...
    if exist "bin\Release\" (
        dir /s "bin\Release\*.dll" | find "RadarMovement"
    )
)

echo.
echo ===============================================
echo INSTALLATION INSTRUCTIONS
echo ===============================================
echo.
echo 1. Copy RadarMovement.dll to your ExileCore plugins directory:
echo    ExileApi-Compiled\Plugins\Compiled\RadarMovement\
echo.
echo 2. Start ExileCore (ExileApi-Compiled.exe)
echo.
echo 3. In the ExileCore menu, go to Plugins and enable "RadarMovement"
echo.
echo 4. Configure the plugin settings as needed
echo.
echo 5. The hybrid system will now provide:
echo    - Radar-style direction field pathfinding
echo    - Follower-like human movement patterns  
echo    - AreWeThereYet terrain analysis
echo    - Advanced visualization and debugging
echo.
echo Your existing Python automation scripts will continue to work
echo but will now benefit from all the hybrid enhancements!
echo.

REM Optional: Copy to a common deployment location
if exist "..\..\..\Compiled\RadarMovement\" (
    echo.
    echo Copying to plugins directory...
    copy "bin\Release\net8.0\RadarMovement.dll" "..\..\..\Compiled\RadarMovement\" /Y
    if not errorlevel 1 (
        echo Successfully copied to ..\..\..\Compiled\RadarMovement\
    )
)

echo.
echo Build completed successfully!
echo.
pause 