# Quick Installation Guide for AqueductBridge

## Prerequisites

1. **Download ExileApi-Compiled** from the official repository:
   ```bash
   git clone https://github.com/exApiTools/ExileApi-Compiled.git
   ```

2. **Install .NET 8.0 SDK** if not already installed

## Installation Steps

### Step 1: Create Plugin Directory
```bash
cd ExileApi-Compiled
mkdir Plugins\AqueductBridge
```

### Step 2: Copy Plugin Files
Copy all the AqueductBridge plugin files to the `Plugins\AqueductBridge\` directory:
- `AqueductBridge.csproj`
- `AqueductBridgePlugin.cs`
- `AqueductBridgeSettings.cs`
- `HttpServer.cs`
- `DataExtractor.cs`
- `build.bat`
- `README_AqueductBridge.md`

### Step 3: Build the Plugin
```bash
cd Plugins\AqueductBridge
dotnet build --configuration Release
```

Or simply double-click `build.bat`

### Step 4: Verify Installation
The directory structure should look like:
```
ExileApi-Compiled/
├── ExileCore.dll
├── GameOffsets.dll
├── ImGui.NET.dll
├── ProcessMemoryUtilities.dll
├── ExileApi-Compiled.exe
├── Plugins/
│   └── AqueductBridge/
│       ├── AqueductBridge.csproj
│       ├── AqueductBridgePlugin.cs
│       ├── AqueductBridgeSettings.cs
│       ├── HttpServer.cs
│       ├── DataExtractor.cs
│       ├── build.bat
│       └── bin/
│           └── Release/
│               └── AqueductBridge.dll
```

### Step 5: Start ExileApi
1. Run `ExileApi-Compiled.exe`
2. Go to the plugins menu
3. Enable "AqueductBridge" plugin
4. The HTTP server will start automatically on port 50002

## Using with aqueduct_runner

1. **Start Path of Exile** in Windowed or Windowed Fullscreen mode
2. **Start ExileApi-Compiled.exe** 
3. **Enable AqueductBridge** plugin
4. **Run aqueduct_runner** - it should connect to `http://127.0.0.1:50002` automatically

## Quick Test

Test the endpoints manually:
```bash
# Test if server is running
curl http://127.0.0.1:50002/gameInfo

# Test position conversion
curl http://127.0.0.1:50002/positionOnScreen?y=100&x=100
```

## Troubleshooting

- **Build fails**: Ensure you're in the correct directory structure
- **Plugin not detected**: Check that the DLL is in `Plugins/AqueductBridge/bin/Release/`
- **HTTP server not starting**: Check port 50002 is not in use, check Windows Firewall
- **aqueduct_runner can't connect**: Verify plugin is enabled and HTTP server is running

## Requirements Reminder

- **Path of Exile**: Must be in Windowed or Windowed Fullscreen mode
- **Windows Scaling**: Must be set to 100%
- **Windows Aero**: Transparency effects must be enabled
- **Visual C++ 2015 Redistributable**: Must be installed 