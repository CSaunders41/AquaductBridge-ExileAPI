#!/usr/bin/env python3
"""
Test Coordinate Conversion from AqueductBridge API
"""

import sys
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def test_coordinates():
    """Test coordinate conversion from API"""
    print("🎯 Testing Coordinate Conversion")
    print("=" * 40)
    
    from api_client import AqueductAPIClient
    
    client = AqueductAPIClient()
    
    if not client.is_connected():
        print("❌ API not connected. Make sure AqueductBridge is running.")
        return
    
    print("✅ API connected")
    
    # Test 1: Get player position
    print("\n--- Test 1: Player Position ---")
    try:
        player_pos = client.get_player_position()
        print(f"Player position: {player_pos}")
        
        if player_pos:
            world_x = player_pos.get('X', 0)
            world_y = player_pos.get('Y', 0)
            print(f"World coordinates: ({world_x}, {world_y})")
            
            # Test coordinate conversion
            screen_coords = client.get_screen_position(world_x, world_y)
            print(f"Screen coordinates: {screen_coords}")
            
            # Test validation
            from coordinate_helper import get_coordinate_helper
            coord_helper = get_coordinate_helper()
            valid = coord_helper.validate_screen_coordinates(*screen_coords)
            print(f"Coordinates valid: {valid}")
            
    except Exception as e:
        print(f"Error testing player position: {e}")
    
    # Test 2: Test some known coordinates
    print("\n--- Test 2: Known Coordinates ---")
    test_coords = [
        (100, 100),      # Near screen origin
        (500, 500),      # Mid-screen
        (1000, 1000),    # Larger coordinates
        (0, 0),          # Origin
        (-100, -100),    # Negative coordinates
        (5000, 5000)     # Very large coordinates
    ]
    
    for world_x, world_y in test_coords:
        try:
            screen_coords = client.get_screen_position(world_x, world_y)
            print(f"({world_x}, {world_y}) -> {screen_coords}")
        except Exception as e:
            print(f"Error converting ({world_x}, {world_y}): {e}")
    
    # Test 3: Get entities and check their coordinates
    print("\n--- Test 3: Entity Coordinates ---")
    try:
        full_data = client.get_full_game_data()
        entities = full_data.get('awake_entities', [])
        print(f"Found {len(entities)} entities")
        
        for i, entity in enumerate(entities[:5]):  # Test first 5
            print(f"\nEntity {i+1}:")
            print(f"  Type: {entity.get('EntityType', 'Unknown')}")
            print(f"  Path: {entity.get('Path', 'Unknown')}")
            
            # Check screen position
            screen_pos = entity.get('location_on_screen', {})
            if screen_pos:
                x, y = screen_pos.get('X', 0), screen_pos.get('Y', 0)
                print(f"  Screen pos: ({x}, {y})")
                
                # Test if valid
                from coordinate_helper import get_coordinate_helper
                coord_helper = get_coordinate_helper()
                valid = coord_helper.validate_screen_coordinates(x, y)
                print(f"  Valid: {valid}")
                
                # Test conversion
                converted = coord_helper.convert_game_to_screen(x, y)
                print(f"  Converted: {converted}")
            
            # Check grid position
            grid_pos = entity.get('GridPosition', {})
            if grid_pos:
                print(f"  Grid pos: {grid_pos}")
                
    except Exception as e:
        print(f"Error testing entity coordinates: {e}")
    
    # Test 4: Window area info
    print("\n--- Test 4: Window Information ---")
    try:
        window_area = client.get_window_area()
        print(f"Window area: {window_area}")
        
        # Check if window coordinates make sense
        if window_area:
            width = window_area.get('Width', 0)
            height = window_area.get('Height', 0)
            print(f"Window size: {width}x{height}")
            
            if width > 0 and height > 0:
                print("✅ Window size looks reasonable")
            else:
                print("❌ Window size looks invalid")
                
    except Exception as e:
        print(f"Error getting window info: {e}")
    
    print("\n📊 Coordinate test complete!")
    print("\nWhat to look for:")
    print("- Player coordinates should be reasonable world coordinates")
    print("- Screen coordinates should be 0-2000 range typically")
    print("- Entity screen positions should be valid screen coordinates")
    print("- Window size should match your actual game window")

def main():
    try:
        test_coordinates()
    except KeyboardInterrupt:
        print("\nTest cancelled")
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 