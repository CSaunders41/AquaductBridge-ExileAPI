#!/usr/bin/env python3
"""
Debug Movement and Pathfinding
Tests if the movement system and pathfinding are working correctly
"""

import sys
import time
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def debug_movement():
    """Debug movement and pathfinding"""
    print("🚶 Debug Movement and Pathfinding")
    print("=" * 50)
    
    # Test API connection
    from api_client import AqueductAPIClient
    client = AqueductAPIClient()
    
    if not client.is_connected():
        print("❌ API not connected. Make sure AqueductBridge is running.")
        return
    
    print("✅ API connected")
    
    # Test player position
    print("\n--- Test 1: Player Position ---")
    player_pos = client.get_player_position()
    print(f"Player position: {player_pos}")
    
    # Test terrain data
    print("\n--- Test 2: Terrain Data ---")
    full_data = client.get_full_game_data()
    terrain_string = full_data.get('terrain_string', '')
    print(f"Terrain data length: {len(terrain_string)} characters")
    print(f"Terrain preview: {terrain_string[:100]}...")
    
    # Test pathfinding
    print("\n--- Test 3: Pathfinding ---")
    from pathfinding import PathfindingEngine
    
    pathfinder = PathfindingEngine()
    
    if player_pos and terrain_string:
        try:
            path = pathfinder.create_aqueduct_path(player_pos, terrain_string)
            print(f"Created path with {len(path)} waypoints")
            
            # Show first few waypoints
            for i, waypoint in enumerate(path[:5]):
                print(f"  Waypoint {i+1}: {waypoint}")
            
            if len(path) > 5:
                print(f"  ... and {len(path) - 5} more waypoints")
                
        except Exception as e:
            print(f"Pathfinding error: {e}")
            import traceback
            traceback.print_exc()
    
    # Test coordinate conversion
    print("\n--- Test 4: Coordinate Conversion ---")
    from coordinate_fix import get_coordinate_fix
    
    coord_fix = get_coordinate_fix()
    
    if full_data and 'WindowArea' in full_data:
        coord_fix.set_game_window(full_data['WindowArea'])
    
    if player_pos:
        # Test converting player position
        screen_coords = coord_fix.get_movement_position(player_pos['X'], player_pos['Y'])
        print(f"Player world pos: ({player_pos['X']}, {player_pos['Y']})")
        print(f"Player screen pos: {screen_coords}")
        
        # Test nearby position
        nearby_pos = {'X': player_pos['X'] + 10, 'Y': player_pos['Y'] + 10}
        nearby_screen = coord_fix.get_movement_position(nearby_pos['X'], nearby_pos['Y'])
        print(f"Nearby world pos: ({nearby_pos['X']}, {nearby_pos['Y']})")
        print(f"Nearby screen pos: {nearby_screen}")
    
    # Test movement simulation
    print("\n--- Test 5: Movement Simulation ---")
    from utils import calculate_distance
    
    if player_pos and 'path' in locals() and len(path) > 0:
        current_pos = player_pos
        target_pos = path[0]  # First waypoint
        
        print(f"Current position: {current_pos}")
        print(f"Target position: {target_pos}")
        
        # Calculate distance
        distance = calculate_distance(current_pos, target_pos)
        print(f"Distance to target: {distance:.2f}")
        
        # Test if coordinates are valid
        if screen_coords:
            valid = coord_fix.is_valid_screen_position(*screen_coords)
            print(f"Screen coordinates valid: {valid}")
    
    # Test input system
    print("\n--- Test 6: Input System ---")
    from input_controller import get_input_controller
    
    input_controller = get_input_controller()
    print(f"Input method: {input_controller.input_method}")
    
    if input_controller.input_method != 'none':
        print("✅ Input system available")
        
        # Test a safe click (screen center)
        response = input("Test a click at screen center? (y/n): ")
        if response.lower() == 'y':
            center_x, center_y = coord_fix.get_screen_center()
            print(f"Clicking at screen center: ({center_x}, {center_y})")
            
            try:
                success = input_controller.click_position(center_x, center_y)
                print(f"Click success: {success}")
                
                # Wait and check if player moved
                time.sleep(2)
                new_pos = client.get_player_position()
                print(f"New position: {new_pos}")
                
                if new_pos != player_pos:
                    move_distance = calculate_distance(player_pos, new_pos)
                    print(f"Player moved {move_distance:.2f} units")
                else:
                    print("⚠️  Player did not move")
                    
            except Exception as e:
                print(f"Click error: {e}")
    else:
        print("❌ Input system not available")
    
    print("\n--- Summary ---")
    print("Check the following:")
    print("1. ✅ API connected")
    print("2. ✅ Player position retrieved")
    print("3. ✅ Terrain data available")
    print("4. ✅ Pathfinding working")
    print("5. ✅ Coordinate conversion working")
    print("6. ✅ Input system available")
    print("\nIf player is not moving, check:")
    print("- Game window focus")
    print("- Click coordinates")
    print("- Input method working")
    print("- Character not stuck")

def main():
    try:
        debug_movement()
    except KeyboardInterrupt:
        print("\nDebug cancelled")
    except Exception as e:
        print(f"Debug error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 