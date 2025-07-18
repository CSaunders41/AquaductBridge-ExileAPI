# RadarMovement Plugin

A simple ExileAPI plugin that focuses **only** on movement using the proven [Radar plugin](https://github.com/exApiTools/Radar.git) methodology.

## Purpose

This plugin does exactly what Radar does:
1. **Detects waypoints, doors, and teleports** in the current area  
2. **Draws a line from player to the closest target** (visual feedback)
3. **Automatically moves the player to the target** using simple clicking

## Features

- ✅ **Visual Path Line**: Shows yellow line from player to target (like Radar)
- ✅ **Auto Movement**: Automatically clicks to move to waypoints/doors/teleports
- ✅ **Target Detection**: Finds waypoints, doors, transitions, portals, teleports
- ✅ **Distance-based targeting**: Always goes to the closest available target
- ✅ **Rate limiting**: Prevents spam clicking
- ✅ **Simple and reliable**: Based on proven Radar methodology

## Settings

- **Enable**: Turn the plugin on/off
- **Show Path Line**: Draw visual line to target
- **Path Line Color**: Color of the path line (default: Yellow)
- **Path Line Width**: Width of the path line (1-10)
- **Auto Move to Target**: Automatically move to targets
- **Movement Speed**: Delay between movements (50-500ms)

## How It Works

1. **Target Scanning**: Every 500ms, scans for entities within 200 units
2. **Target Selection**: Chooses the closest waypoint/door/teleport
3. **Visual Feedback**: Draws a line from player to target
4. **Movement**: Clicks on the target to move there
5. **Completion**: When close enough (<30 units), finds next target

## Installation

1. Build the plugin using .NET 8.0
2. Copy `RadarMovement.dll` to your ExileAPI `Plugins/Compiled` folder
3. Enable the plugin in ExileAPI

## Usage

1. **Load into any POE area** (Aqueduct, maps, etc.)
2. **Enable the plugin** in ExileAPI settings
3. **Watch the yellow line** appear pointing to the nearest waypoint/door
4. **Player will automatically move** to the target
5. **Process repeats** until all targets are reached

## Target Types

The plugin detects the same entities as Radar:
- **Waypoints**: All waypoint types
- **Doors**: Area transitions, doors
- **Teleports**: Teleport pads, portals
- **Area Transitions**: Zone exits and entrances

## Comparison to Complex Systems

This plugin is intentionally **simple and focused**:
- ❌ No complex pathfinding algorithms
- ❌ No terrain analysis
- ❌ No HTTP APIs
- ❌ No external Python scripts
- ✅ Just pure movement using Radar's proven approach

## Benefits

- **Reliability**: Based on Radar's proven methodology
- **Simplicity**: Easy to understand and modify
- **Performance**: Minimal overhead
- **Focus**: Does one thing well - movement
- **Proven**: Uses the same approach as the successful Radar plugin

## Perfect for Aqueduct

This plugin is ideal for Aqueduct farming because:
- Detects waypoints at both ends of the area
- Automatically moves between them
- No complex pathfinding needed
- Simple, reliable movement

## Next Steps

Once basic movement is working perfectly, we can add:
- Combat integration
- Loot pickup
- Area-specific optimizations
- But **movement first** - the foundation of everything else 