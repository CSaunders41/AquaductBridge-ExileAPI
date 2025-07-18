#!/usr/bin/env python3
"""
Quick Coordinate Test
Tests if the coordinate fix conversion is working correctly
"""

import sys
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def test_coordinate_conversion():
    """Test coordinate conversion"""
    print("🧪 Quick Coordinate Conversion Test")
    print("=" * 40)
    
    from coordinate_fix import get_coordinate_fix
    
    # Create coordinate fix instance
    coord_fix = get_coordinate_fix()
    
    # Set up fake window info
    window_info = {'X': 0.0, 'Y': 0.0, 'Width': 1920.0, 'Height': 1080.0}
    coord_fix.set_game_window(window_info)
    
    # Test grid coordinate conversion
    print("\n--- Testing Grid Coordinate Conversion ---")
    test_coords = [
        (500, 300),  # Center-ish
        (504, 271),  # From actual log
        (515, 259),  # From actual log
        (498, 251),  # From actual log
        (480, 280),  # Slight offset
        (520, 320),  # Different offset
    ]
    
    for grid_x, grid_y in test_coords:
        screen_x, screen_y = coord_fix.convert_grid_to_screen(grid_x, grid_y)
        valid = coord_fix.is_valid_screen_position(screen_x, screen_y)
        print(f"Grid ({grid_x:3}, {grid_y:3}) -> Screen ({screen_x:4}, {screen_y:4}) Valid: {valid}")
    
    # Test entity position conversion
    print("\n--- Testing Entity Position Conversion ---")
    test_entities = [
        {
            'GridPosition': {'X': 504, 'Y': 271, 'Z': 0},
            'location_on_screen': {'X': 5075, 'Y': -9539}  # This is the broken data
        },
        {
            'GridPosition': {'X': 515, 'Y': 259, 'Z': 0},
            'location_on_screen': {'X': 2930, 'Y': -8339}  # This is the broken data
        }
    ]
    
    for i, entity in enumerate(test_entities):
        grid_pos = entity['GridPosition']
        screen_pos = entity['location_on_screen']
        
        print(f"\nEntity {i+1}:")
        print(f"  Grid: ({grid_pos['X']}, {grid_pos['Y']})")
        print(f"  Broken Screen: ({screen_pos['X']}, {screen_pos['Y']})")
        
        # Test our coordinate fix
        fixed_coords = coord_fix.get_entity_click_position(entity)
        print(f"  Fixed Coords: {fixed_coords}")
        
        if fixed_coords:
            valid = coord_fix.is_valid_screen_position(*fixed_coords)
            print(f"  Fixed Valid: {valid}")
    
    # Test screen center
    center = coord_fix.get_screen_center()
    print(f"\nScreen Center: {center}")
    
    print("\n✅ Coordinate conversion test complete!")
    print("\nExpected results:")
    print("- All coordinates should be in range 100-1820 x 100-980")
    print("- All coordinates should be marked as valid")
    print("- Fixed coordinates should ignore broken screen data")

def main():
    try:
        test_coordinate_conversion()
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 