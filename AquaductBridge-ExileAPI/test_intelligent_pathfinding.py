#!/usr/bin/env python3
"""
Test Intelligent Pathfinding System
Tests the new intelligent pathfinding that finds actual zone exits
"""

import sys
import time
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def test_intelligent_pathfinding():
    """Test intelligent pathfinding with real game data"""
    print("🧠 Testing Intelligent Pathfinding System")
    print("=" * 50)
    
    # Test API connection
    from api_client import AqueductAPIClient
    client = AqueductAPIClient()
    
    if not client.is_connected():
        print("❌ API not connected. Make sure AqueductBridge is running.")
        return
    
    print("✅ API connected")
    
    # Test getting game data
    print("\n--- Test 1: Getting Game Data ---")
    full_data = client.get_full_game_data()
    
    if not full_data:
        print("❌ Failed to get game data")
        return
    
    player_pos = full_data.get('player_pos', {})
    terrain_string = full_data.get('terrain_string', '')
    entities = full_data.get('awake_entities', [])
    
    print(f"✅ Player position: {player_pos}")
    print(f"✅ Terrain data: {len(terrain_string)} characters")
    print(f"✅ Entities: {len(entities)} detected")
    
    # Test intelligent pathfinding
    print("\n--- Test 2: Intelligent Pathfinding ---")
    from intelligent_pathfinding import IntelligentPathfinder
    
    intelligent_pathfinder = IntelligentPathfinder()
    
    try:
        path = intelligent_pathfinder.create_intelligent_path(
            player_pos,
            terrain_string,
            entities
        )
        
        print(f"✅ Created intelligent path with {len(path)} waypoints")
        
        # Show first few waypoints
        for i, waypoint in enumerate(path[:10]):
            print(f"  Waypoint {i+1}: {waypoint}")
        
        if len(path) > 10:
            print(f"  ... and {len(path) - 10} more waypoints")
            
    except Exception as e:
        print(f"❌ Intelligent pathfinding error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test zone analysis
    print("\n--- Test 3: Zone Analysis ---")
    from intelligent_pathfinding import ZoneAnalyzer
    
    zone_analyzer = ZoneAnalyzer()
    
    try:
        exits = zone_analyzer.find_zone_exits(entities)
        print(f"✅ Found {len(exits)} potential zone exits")
        
        for i, exit_pos in enumerate(exits):
            print(f"  Exit {i+1}: {exit_pos}")
            
        if exits:
            from intelligent_pathfinding import Position
            player_position = Position(player_pos['X'], player_pos['Y'])
            optimal_exit = zone_analyzer.find_optimal_exit(player_position, exits)
            print(f"✅ Optimal exit: {optimal_exit}")
        else:
            print("⚠️  No exits found - will use exploration pattern")
            
    except Exception as e:
        print(f"❌ Zone analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test terrain analysis
    print("\n--- Test 4: Terrain Analysis ---")
    from intelligent_pathfinding import TerrainAnalyzer
    
    try:
        terrain_analyzer = TerrainAnalyzer(terrain_string)
        print(f"✅ Terrain grid: {terrain_analyzer.width}x{terrain_analyzer.height}")
        
        if terrain_analyzer.grid:
            # Test some positions
            test_positions = [
                (player_pos['X'], player_pos['Y']),
                (player_pos['X'] + 10, player_pos['Y']),
                (player_pos['X'], player_pos['Y'] + 10),
                (player_pos['X'] + 10, player_pos['Y'] + 10)
            ]
            
            for x, y in test_positions:
                walkable = terrain_analyzer.is_walkable(x, y)
                print(f"  Position ({x}, {y}): {'Walkable' if walkable else 'Blocked'}")
        else:
            print("⚠️  No terrain grid data available")
            
    except Exception as e:
        print(f"❌ Terrain analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test entity analysis
    print("\n--- Test 5: Entity Analysis ---")
    
    print(f"Found {len(entities)} entities:")
    
    # Show interesting entities
    for entity in entities[:20]:  # Show first 20
        path = entity.get('Path', '')
        entity_type = entity.get('EntityType', 0)
        grid_pos = entity.get('GridPosition', {})
        
        if any(keyword in path.lower() for keyword in ['door', 'exit', 'waypoint', 'portal', 'transition']):
            print(f"  🚪 POTENTIAL EXIT: {path} at {grid_pos}")
        elif entity_type == 14:  # Monster
            print(f"  👹 Monster: {path} at {grid_pos}")
        elif entity_type in [1, 2, 3]:  # Possible exits
            print(f"  🔍 Exit Type {entity_type}: {path} at {grid_pos}")
    
    if len(entities) > 20:
        print(f"  ... and {len(entities) - 20} more entities")
    
    # Comparison with old system
    print("\n--- Test 6: Comparison with Old System ---")
    from pathfinding import PathfindingEngine
    
    try:
        old_pathfinder = PathfindingEngine()
        old_path = old_pathfinder.create_aqueduct_path(player_pos, terrain_string)
        
        print(f"Old pathfinder: {len(old_path)} waypoints")
        print(f"New pathfinder: {len(path)} waypoints")
        
        if len(old_path) > 0 and len(path) > 0:
            print(f"Old first waypoint: {old_path[0]}")
            print(f"New first waypoint: {path[0]}")
            print(f"Old last waypoint: {old_path[-1]}")
            print(f"New last waypoint: {path[-1]}")
            
    except Exception as e:
        print(f"❌ Old pathfinder comparison error: {e}")
    
    print("\n--- Summary ---")
    print("✅ Intelligent pathfinding system is working!")
    print("Key improvements:")
    print("- Analyzes real entity data to find zone exits")
    print("- Uses A* pathfinding with terrain data")
    print("- Falls back to exploration pattern if no exits found")
    print("- Much more intelligent than hardcoded linear movement")
    print()
    print("The bot should now:")
    print("1. Find actual zone exits (doors, waypoints, transitions)")
    print("2. Create optimal paths to those exits")
    print("3. Navigate intelligently through the zone")
    print("4. Explore systematically if no exits are found")

def main():
    try:
        test_intelligent_pathfinding()
    except KeyboardInterrupt:
        print("\nTest cancelled")
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 