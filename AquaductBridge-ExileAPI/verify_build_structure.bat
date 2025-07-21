@echo off
echo.
echo ===============================================
echo RadarMovement Hybrid v5.0 - Build Verification
echo ===============================================
echo.

echo Checking required files...
set MISSING_FILES=0

if not exist "RadarMovement.cs" (
    echo ERROR: RadarMovement.cs not found!
    set MISSING_FILES=1
)

if not exist "RadarTask.cs" (
    echo ERROR: RadarTask.cs not found!
    set MISSING_FILES=1
)

if not exist "Utils\EventBus.cs" (
    echo ERROR: Utils\EventBus.cs not found!
    set MISSING_FILES=1
)

if not exist "Utils\LineOfSight.cs" (
    echo ERROR: Utils\LineOfSight.cs not found!
    set MISSING_FILES=1
)

if not exist "Utils\AqueductPathfinder.cs" (
    echo ERROR: Utils\AqueductPathfinder.cs not found!
    set MISSING_FILES=1
)

if not exist "Utils\AdvancedMouse.cs" (
    echo ERROR: Utils\AdvancedMouse.cs not found!
    set MISSING_FILES=1
)

if not exist "Utils\BinaryHeap.cs" (
    echo ERROR: Utils\BinaryHeap.cs not found!
    set MISSING_FILES=1
)

if not exist "RadarMovement.csproj" (
    echo ERROR: RadarMovement.csproj not found!
    set MISSING_FILES=1
)

if %MISSING_FILES%==0 (
    echo SUCCESS: All required files found!
) else (
    echo.
    echo FAILURE: Some required files are missing.
    echo Please check the above errors and ensure all files are in place.
    pause
    exit /b 1
)

echo.
echo Checking for conflicting duplicate files...
set DUPLICATE_FILES=0

if exist "AqueductBridgePlugin.cs" (
    echo WARNING: Found duplicate AqueductBridgePlugin.cs in root directory
    echo This may cause build conflicts. The project excludes it, but consider moving it.
    set DUPLICATE_FILES=1
)

if exist "AqueductBridgeSettings.cs" (
    echo WARNING: Found duplicate AqueductBridgeSettings.cs in root directory
    echo This may cause build conflicts. The project excludes it, but consider moving it.
    set DUPLICATE_FILES=1
)

if exist "AqueductBridge_Deploy_20250720_201333\" (
    echo INFO: Found deployment directory (excluded from build)
    echo The .csproj file excludes this directory to prevent duplicates.
)

echo.
echo Checking .NET SDK...
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: .NET SDK not found. Please install .NET 8.0 SDK.
    echo Download from: https://dotnet.microsoft.com/download
    pause
    exit /b 1
) else (
    echo SUCCESS: .NET SDK found
    dotnet --version
)

echo.
echo Checking ExileCore references...
if not exist "..\..\..\..\ExileCore.dll" (
    echo WARNING: ExileCore.dll not found at expected path
    echo Expected: ..\..\..\..\ExileCore.dll
    echo Please ensure this plugin is in: ExileApi-Compiled\Plugins\Source\AqueductBridge-ExileAPI\
)

echo.
echo ===============================================
echo Build Structure Verification Complete
echo ===============================================

if %MISSING_FILES%==0 (
    echo.
    echo Ready to build! Run the following command:
    echo dotnet build RadarMovement.csproj --configuration Release
    echo.
    echo Or use the build.bat script if it exists.
    echo.
) else (
    echo.
    echo Please resolve the errors above before building.
    echo.
)

pause 