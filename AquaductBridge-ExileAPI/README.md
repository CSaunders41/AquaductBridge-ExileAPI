# Aqueduct Automation System

A comprehensive automation system for Path of Exile's Aqueduct farming using the AqueductBridge ExileAPI plugin.

## 🎯 Features

### Core Automation
- **Intelligent Pathfinding**: Advanced A* pathfinding with terrain analysis
- **Combat System**: Automated monster targeting and engagement
- **Loot Management**: Smart item pickup with extensive filtering
- **Resource Management**: Automated flask usage and health monitoring
- **Area Navigation**: Seamless waypoint and instance management

### Advanced Features
- **Multi-Build Support**: Configurations for melee, ranged, and caster builds
- **Safety Systems**: Health monitoring, retreat mechanisms, and death prevention
- **Efficiency Optimization**: Speed vs safety balance customization
- **Anti-Detection**: Random delays and human-like behavior patterns
- **Comprehensive Logging**: Detailed statistics and performance tracking

## 🔧 Installation

### Prerequisites
- Path of Exile
- ExileAPI (ExileCore) installed
- AqueductBridge plugin (included in this repository)
- Python 3.8 or higher

### Setup Steps

1. **Install AqueductBridge Plugin**
   ```bash
   # Copy the AqueductBridge plugin to your ExileAPI plugins directory
   cp -r AquaductBridge-ExileAPI /path/to/ExileAPI/Plugins/AqueductBridge
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Plugin**
   - Start ExileAPI
   - Enable the AqueductBridge plugin
   - Ensure HTTP server starts on port 50002

4. **Run the Automation**
   ```bash
   cd aqueduct_automation
   python main.py
   ```

## ⚙️ Configuration

### Quick Start Configurations

The system includes several pre-configured templates:

- **Speed Farming**: Fast runs with minimal safety checks
- **Safe Farming**: Slower, safer runs with health monitoring
- **Currency Farming**: Optimized for currency collection
- **Melee Build**: Configuration for melee characters
- **Energy Shield**: Specialized for ES-based builds

### Custom Configuration

Create your own configuration:

```python
from config import AutomationConfig, ConfigTemplates

# Use a template
config = ConfigTemplates.create_speed_farming_config()

# Or create custom
config = AutomationConfig(
    build_type="ranged",
    max_runs=50,
    run_delay=2.0,
    enable_safety_checks=True
)
```

### Flask Configuration

Configure flask keys for your build:

```python
config.resource_config.life_flask_key = "1"
config.resource_config.mana_flask_key = "2"
config.resource_config.utility_flask_keys = ["3", "4", "5"]
```

## 🎮 Build Support

### Melee Builds
- Close-range combat optimization
- Aggressive positioning
- Life-based resource management

### Ranged Builds
- Long-range engagement
- Kiting mechanics
- Positioning optimization

### Caster Builds
- Mana management focus
- Area damage optimization
- Energy shield support

## 🛡️ Safety Features

### Health Monitoring
- Automatic flask usage
- Emergency retreat mechanisms
- Death prevention systems

### Anti-Detection
- Random timing variations
- Human-like movement patterns
- Configurable behavior randomization

### Error Recovery
- Automatic retry on failures
- Graceful error handling
- State recovery mechanisms

## 📊 Statistics & Monitoring

### Real-time Metrics
- Runs per hour
- Items collected
- Currency gained
- Combat efficiency
- Health/mana usage

### Logging
- Comprehensive event logging
- Performance metrics
- Error tracking
- Debug information

## 🔄 Workflow

1. **Initialization**: Load configuration and connect to game
2. **State Verification**: Check game state and player status
3. **Area Entry**: Navigate to Aqueduct via waypoint
4. **Farming Loop**: 
   - Navigate through area using pathfinding
   - Engage monsters with combat system
   - Collect valuable loot
   - Monitor health/mana and use flasks
5. **Return**: Portal back to hideout
6. **Stash Management**: Store valuable items
7. **Repeat**: Continue for configured number of runs

## 📋 API Endpoints

The AqueductBridge plugin provides these endpoints:

- `GET /gameInfo` - Basic game information
- `GET /gameInfo?type=full` - Comprehensive automation data
- `GET /player` - Player-specific data
- `GET /area` - Current area information
- `GET /positionOnScreen?x={x}&y={y}` - Coordinate conversion

## 🔧 Advanced Usage

### Custom Pathfinding
```python
from pathfinding import PathfindingEngine

pathfinder = PathfindingEngine()
path = pathfinder.create_aqueduct_path(start_pos, terrain_data)
```

### Custom Combat Logic
```python
from combat import CombatSystem, CombatConfig

combat_config = CombatConfig(
    max_engagement_range=120.0,
    retreat_health_threshold=30.0
)
combat = CombatSystem(combat_config)
```

### Loot Filtering
```python
from loot_manager import LootConfig

loot_config = LootConfig(
    pickup_currency=True,
    pickup_uniques=True,
    valuable_currency={"Chaos Orb", "Exalted Orb"}
)
```

## 🐛 Troubleshooting

### Common Issues

1. **Plugin not connecting**
   - Verify AqueductBridge plugin is enabled
   - Check port 50002 is not blocked
   - Ensure Path of Exile is running

2. **Pathfinding issues**
   - Verify terrain data is being received
   - Check player position updates
   - Review pathfinding logs

3. **Combat not working**
   - Verify monster detection
   - Check combat skill configuration
   - Review entity data

### Debug Mode
```bash
python main.py --log-level DEBUG
```

## ⚠️ Disclaimer

This automation system is for educational purposes. Use at your own risk and in accordance with Path of Exile's Terms of Service. The developers are not responsible for any account actions taken by Grinding Gear Games.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- ExileAPI team for the excellent reverse engineering work
- Path of Exile community for guidance and support
- Contributors to the pathfinding and automation algorithms

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting guide
- Review the logs for error details

---

**Happy Farming!** 🎯 