@echo off
echo.
echo  🎯 Starting Aqueduct Automation System...
echo  Press Ctrl+C to stop
echo  ===================================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Start the automation
python start_automation.py

echo.
echo ✅ Automation finished
pause 