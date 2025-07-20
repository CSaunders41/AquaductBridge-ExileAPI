@echo off
echo.
echo 📦 Building AqueductBridge for Deployment
echo ========================================

REM Check if .NET SDK is installed
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo ❌ .NET SDK not found. Please install .NET 8.0 SDK
    pause
    exit /b 1
)

echo ✅ .NET SDK found

REM Build the plugin
echo.
echo 🔨 Building AqueductBridge plugin...
dotnet build --configuration Release --verbosity minimal

if errorlevel 1 (
    echo ❌ Build failed
    pause
    exit /b 1
)

echo ✅ Build successful

REM Check if output exists
if exist "bin\Release\AqueductBridge.dll" (
    echo ✅ Plugin DLL created: bin\Release\AqueductBridge.dll
) else (
    echo ❌ Plugin DLL not found in expected location
    pause
    exit /b 1
)

REM Create deployment package
echo.
echo 📦 Creating deployment package...
python create_deployment_package.py

if errorlevel 1 (
    echo ❌ Failed to create deployment package
    pause
    exit /b 1
)

echo.
echo ✅ Deployment package created successfully!
echo 📁 Ready for deployment to ExileApi-Compiled
echo.
pause 