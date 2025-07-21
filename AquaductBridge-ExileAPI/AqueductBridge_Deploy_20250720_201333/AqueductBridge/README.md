# AqueductBridge - ExileApi Plugin for aqueduct_runner

## Overview

AqueductBridge is an ExileApi-Compiled plugin that provides HTTP endpoints for compatibility with the `aqueduct_runner` Python bot. It replaces the abandoned "gamehelper" by providing the same HTTP REST API endpoints that aqueduct_runner expects.

## Features

- **HTTP Server**: Runs on `http://127.0.0.1:50002` (configurable)
- **3 Required Endpoints**:
  - `GET /gameInfo?type=full` - Complete game data
  - `GET /gameInfo` - Instance data only  
  - `GET /positionOnScreen?y={y}&x={x}` - Grid to screen coordinate conversion
- **Real-time Data Extraction**: Terrain, entities, player position, life stats
- **ExileApi Integration**: Uses ExileApi's robust game data access
- **Configurable Settings**: Port, logging, auto-start options

## Installation

### Prerequisites

1. **Path of Exile** - Running game in Windowed or Windowed Fullscreen mode
2. **ExileApi-Compiled** - Latest version from https://github.com/exApiTools/ExileApi-Compiled.git
3. **Visual Studio 2022** or **MSBuild** - For building the plugin
4. **.NET 8.0 SDK** - For compilation
5. **Microsoft Visual C++ 2015 Redistributable** - Required by ExileApi
6. **Windows Aero transparency effects** - Must be enabled
7. **Windows scaling** - Must be set to 100%

### Building the Plugin

1. **Download ExileApi-Compiled** from the official repository:
   ```bash
   git clone https://github.com/exApiTools/ExileApi-Compiled.git
   ```

2. **Place Plugin Source** in the correct directory structure:
   ```
   ExileApi-Compiled/
   ├── ExileCore.dll
   ├── GameOffsets.dll
   ├── ImGui.NET.dll
   ├── ProcessMemoryUtilities.dll
   ├── Plugins/
   │   └── AqueductBridge/
   │       ├── AqueductBridge.csproj
   │       ├── AqueductBridgePlugin.cs
   │       ├── AqueductBridgeSettings.cs
   │       ├── HttpServer.cs
   │       ├── DataExtractor.cs
   │       ├── build.bat
   │       └── README_AqueductBridge.md
   ```

3. **Build the Plugin**:
   ```bash
   cd ExileApi-Compiled/Plugins/AqueductBridge
   dotnet build --configuration Release
   ```
   Or simply double-click `build.bat`

4. **Start ExileApi**:
   - Run `ExileApi-Compiled.exe`
   - The plugin should be automatically detected

### Alternative: Pre-compiled Installation

If you have a pre-compiled version:

1. Create directory `ExileApi-Compiled/Plugins/AqueductBridge/`
2. Copy `AqueductBridge.dll` to that directory
3. Start `ExileApi-Compiled.exe`
4. The plugin should appear in the plugins list

## Configuration

### Plugin Settings

Access settings through the ExileApi interface:

- **Enable**: Toggle plugin on/off
- **HTTP Server Port**: Port for the HTTP server (default: 50002)
- **Enable Debug Logging**: Verbose logging for troubleshooting
- **Auto-Start Server**: Start HTTP server automatically when plugin loads

### ExileApi Setup

1. **Start ExileApi-Compiled.exe** before launching Path of Exile
2. **Load the Plugin** from the plugins menu
3. **Configure Settings** as needed
4. **Start the HTTP Server** (automatic if auto-start is enabled)

## Usage

### With aqueduct_runner

1. **Start Path of Exile** (in Windowed or Windowed Fullscreen mode)
2. **Start ExileApi-Compiled.exe** with AqueductBridge loaded
3. **Verify HTTP Server** is running on port 50002
4. **Run aqueduct_runner** - it should connect automatically

### Manual Testing

Test the endpoints manually:

```bash
# Get full game data
curl http://127.0.0.1:50002/gameInfo?type=full

# Get instance data only
curl http://127.0.0.1:50002/gameInfo

# Get screen coordinates for grid position (100, 100)
curl http://127.0.0.1:50002/positionOnScreen?y=100&x=100
```

### JSON Response Format

#### `/gameInfo?type=full` Response:
```json
{
  "WindowArea": {
    "X": 0,
    "Y": 0,
    "Width": 1920,
    "Height": 1080
  },
  "terrain_string": "51 51 49 51...\r\n51 49 51 51...\r\n",
  "player_pos": {
    "X": 150,
    "Y": 200,
    "Z": 0
  },
  "awake_entities": [
    {
      "GridPosition": { "X": 120, "Y": 180, "Z": 0 },
      "location_on_screen": { "X": 500, "Y": 300 },
      "EntityType": 14,
      "Path": "Metadata/Monsters/...",
      "life": {
        "Health": { "Current": 100, "Total": 100, "ReservedTotal": 0 },
        "Mana": { "Current": 50, "Total": 50, "ReservedTotal": 0 },
        "EnergyShield": { "Current": 0, "Total": 0, "ReservedTotal": 0 }
      },
      "Id": 12345,
      "IsAlive": true
    }
  ],
  "life": {
    "Health": { "Current": 500, "Total": 500, "ReservedTotal": 0 },
    "Mana": { "Current": 200, "Total": 200, "ReservedTotal": 0 },
    "EnergyShield": { "Current": 100, "Total": 100, "ReservedTotal": 0 }
  },
  "area_loading": false,
  "area_id": 12345
}
```

#### `/gameInfo` Response:
Same as above but without `WindowArea` and `terrain_string`.

#### `/positionOnScreen?y=100&x=100` Response:
```json
[450, 350]
```

## Technical Details

### Terrain Data Format

- **String Format**: `\r\n` line separators
- **Values**: Space-separated int8 values per line
- **Walkability**: 
  - `< 50` = Unwalkable
  - `≥ 50` = Walkable (with different weights)
- **Coordinate System**: Game uses inverted Y coordinates (handled by aqueduct_runner)

### Entity Filtering

aqueduct_runner looks for:
- **EntityType == 14**: Monsters
- **Path contains**:
  - `"Door"` - Doors
  - `"Waypoint"` - Waypoints  
  - `"Transition"` - Area transitions
  - `"Stash"` - Stash boxes

### Coordinate Conversion

- **Grid to Screen**: Uses ExileApi's `Camera.WorldToScreen()` method
- **Input**: Grid coordinates (y, x)
- **Output**: Screen coordinates [x, y]

## Troubleshooting

### Common Issues

1. **HTTP Server Not Starting**:
   - Check if port 50002 is available
   - Try changing the port in settings
   - Check Windows Firewall settings

2. **aqueduct_runner Can't Connect**:
   - Verify HTTP server is running
   - Test endpoints manually with curl
   - Check ExileApi-Compiled logs for errors

3. **Empty/Invalid Data**:
   - Ensure you're in-game (not in menus)
   - Check that ExileApi-Compiled is properly reading game data
   - Enable debug logging for detailed error messages

### Debug Logging

Enable debug logging in plugin settings to see detailed information:
- HTTP requests and responses
- Data extraction processes
- Error messages with stack traces

### Port Conflicts

If port 50002 is in use:
1. Change the port in plugin settings
2. Update aqueduct_runner to use the new port:
   ```python
   self.poe_hud_endpoint = "http://127.0.0.1:NEW_PORT"
   ```

## Development

### Architecture

```
AqueductBridgePlugin (Main)
├── HttpServer (HTTP endpoints)
├── DataExtractor (Game data extraction)
└── AqueductBridgeSettings (Configuration)
```

### Key Components

- **HttpServer**: Handles HTTP requests using `HttpListener`
- **DataExtractor**: Extracts game data from ExileApi
- **AqueductBridgePlugin**: Main plugin class managing lifecycle
- **AqueductBridgeSettings**: Configuration interface

### Extending the Plugin

To add new endpoints:

1. Add route handling in `HttpServer.ProcessRequestAsync()`
2. Implement data extraction method in `DataExtractor`
3. Update documentation

## Compatibility

- **ExileApi**: Compatible with latest ExileApi-Compiled
- **Path of Exile**: Current league supported
- **aqueduct_runner**: Full compatibility with existing Python bot
- **Operating System**: Windows (ExileApi requirement)

## License

[Specify your license here]

## Support

For issues and questions:
1. Check the troubleshooting section
2. Enable debug logging
3. Check ExileApi-Compiled logs
4. Create an issue with detailed error information

## Version History

- **v1.0.0**: Initial release
  - HTTP server implementation
  - All 3 required endpoints
  - Complete aqueduct_runner compatibility
  - Configuration interface
  - Debug logging support 