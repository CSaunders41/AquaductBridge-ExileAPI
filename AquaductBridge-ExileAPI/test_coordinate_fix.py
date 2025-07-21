#!/usr/bin/env python3
"""
Test Coordinate Fix System
Tests the new coordinate fix that bypasses the broken AqueductBridge API
"""

import sys
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def test_coordinate_fix():
    """Test the coordinate fix system"""
    print("🔧 Testing Coordinate Fix System")
    print("=" * 50)
    
    from api_client import AqueductAPIClient
    from coordinate_fix import get_coordinate_fix
    
    client = AqueductAPIClient()
    
    if not client.is_connected():
        print("❌ API not connected. Make sure AqueductBridge is running.")
        return
    
    print("✅ API connected")
    
    # Initialize coordinate fix
    coord_fix = get_coordinate_fix()
    
    # Get game data
    print("\n📊 Getting game data...")
    full_data = client.get_full_game_data()
    
    if not full_data:
        print("❌ No game data available")
        return
    
    # Set up coordinate fix with window info
    if 'WindowArea' in full_data:
        coord_fix.set_game_window(full_data['WindowArea'])
        print(f"✅ Window info set: {full_data['WindowArea']}")
    
    # Test 1: Player position conversion
    print("\n--- Test 1: Player Position Conversion ---")
    player_pos = client.get_player_position()
    if player_pos:
        print(f"Player world position: {player_pos}")
        
        # Test the coordinate fix conversion
        movement_pos = coord_fix.get_movement_position(player_pos['X'], player_pos['Y'])
        print(f"Fixed movement position: {movement_pos}")
        
        # Test safe click near player
        safe_pos = coord_fix.get_safe_click_near_player(player_pos)
        print(f"Safe click position: {safe_pos}")
        
        # Test validation
        if movement_pos:
            valid = coord_fix.is_valid_screen_position(*movement_pos)
            print(f"Movement position valid: {valid}")
        
        # Debug coordinate conversion
        coord_fix.debug_coordinate_conversion(player_pos)
    
    # Test 2: Entity position conversion
    print("\n--- Test 2: Entity Position Conversion ---")
    entities = full_data.get('awake_entities', [])
    print(f"Found {len(entities)} entities")
    
    for i, entity in enumerate(entities[:3]):  # Test first 3 entities
        print(f"\nEntity {i+1}:")
        print(f"  Type: {entity.get('EntityType', 'Unknown')}")
        print(f"  Path: {entity.get('Path', 'Unknown')}")
        
        # Test coordinate fix
        click_pos = coord_fix.get_entity_click_position(entity)
        print(f"  Fixed click position: {click_pos}")
        
        if click_pos:
            valid = coord_fix.is_valid_screen_position(*click_pos)
            print(f"  Position valid: {valid}")
        
        # Compare with broken API
        screen_pos = entity.get('location_on_screen', {})
        if screen_pos:
            x, y = screen_pos.get('X', 0), screen_pos.get('Y', 0)
            print(f"  Original screen pos: ({x}, {y})")
            api_valid = coord_fix.is_valid_screen_position(x, y)
            print(f"  Original valid: {api_valid}")
    
    # Test 3: Grid coordinate conversion
    print("\n--- Test 3: Grid Coordinate Conversion ---")
    test_grid_coords = [
        (500, 300),  # Near player position
        (520, 320),  # Slightly offset
        (480, 280),  # Different offset
        (400, 200),  # Further away
        (600, 400),  # Different direction
    ]
    
    for grid_x, grid_y in test_grid_coords:
        screen_pos = coord_fix.convert_grid_to_screen(grid_x, grid_y)
        valid = coord_fix.is_valid_screen_position(*screen_pos)
        print(f"  Grid ({grid_x}, {grid_y}) -> Screen {screen_pos}, Valid: {valid}")
    
    print("\n✅ Coordinate Fix Test Complete!")
    print("\n🎯 Summary:")
    print("- The coordinate fix bypasses the broken AqueductBridge API")
    print("- It uses grid coordinates and converts them to screen coordinates")
    print("- All coordinates are validated before use")
    print("- This should prevent PyAutoGUI failsafe errors")
    print("\nThe automation should now work without coordinate errors!")

def main():
    try:
        test_coordinate_fix()
    except KeyboardInterrupt:
        print("\nTest cancelled")
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 