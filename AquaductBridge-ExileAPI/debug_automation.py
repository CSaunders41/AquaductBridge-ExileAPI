#!/usr/bin/env python3
"""
Debug version of Aqueduct Automation
Shows coordinate information without actually clicking
"""

import sys
import time
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

from api_client import AqueductAPIClient
from coordinate_helper import get_coordinate_helper
from utils import setup_logging

def debug_coordinates():
    """Debug coordinate information"""
    setup_logging(log_level="DEBUG")
    
    print("🐛 Aqueduct Automation - Coordinate Debug Mode")
    print("=" * 60)
    
    # Initialize API client
    client = AqueductAPIClient()
    
    if not client.is_connected():
        print("❌ API not connected. Make sure AqueductBridge is running.")
        return
    
    # Initialize coordinate helper
    coord_helper = get_coordinate_helper()
    
    # Get game data
    print("\n📊 Getting game data...")
    full_data = client.get_full_game_data()
    
    if not full_data:
        print("❌ No game data available")
        return
    
    # Set up coordinate helper
    if 'WindowArea' in full_data:
        coord_helper.set_game_window(full_data['WindowArea'])
        print(f"Game window: {full_data['WindowArea']}")
    
    # Get entities
    entities = full_data.get('awake_entities', [])
    print(f"\n👾 Found {len(entities)} entities")
    
    if not entities:
        print("No entities to debug")
        return
    
    # Debug first few entities
    for i, entity in enumerate(entities[:5]):  # Only debug first 5
        print(f"\n--- Entity {i+1} ---")
        print(f"Type: {entity.get('EntityType', 'Unknown')}")
        print(f"Path: {entity.get('Path', 'Unknown')}")
        
        # Screen position
        screen_pos = entity.get('location_on_screen', {})
        if screen_pos:
            x, y = screen_pos.get('X', 0), screen_pos.get('Y', 0)
            print(f"Raw screen pos: ({x}, {y})")
            
            # Test coordinate conversion
            converted = coord_helper.convert_game_to_screen(x, y)
            print(f"Converted pos: {converted}")
            
            # Validate
            valid = coord_helper.validate_screen_coordinates(*converted)
            print(f"Valid: {valid}")
            
            # Check if on screen
            on_screen = coord_helper.is_position_on_screen(*converted)
            print(f"On screen: {on_screen}")
            
            # Get safe coordinates
            safe_coords = coord_helper.get_safe_click_coordinates(entity)
            print(f"Safe coords: {safe_coords}")
        
        # Grid position
        grid_pos = entity.get('GridPosition', {})
        if grid_pos:
            print(f"Grid pos: {grid_pos}")
    
    # Test screen center
    center = coord_helper.get_screen_center()
    print(f"\n🎯 Screen center: {center}")
    
    # Test player position
    player_pos = client.get_player_position()
    print(f"Player position: {player_pos}")
    
    # Test coordinate conversion for player
    if player_pos:
        try:
            screen_coords = client.get_screen_position(player_pos['X'], player_pos['Y'])
            print(f"Player screen coords: {screen_coords}")
        except Exception as e:
            print(f"Error converting player coords: {e}")
    
    print("\n✅ Debug complete!")
    print("\nKey findings:")
    print("- Check if coordinates are reasonable (should be 0-3000 range)")
    print("- Look for patterns in invalid coordinates")
    print("- Note any coordinate conversion issues")

def main():
    try:
        debug_coordinates()
    except KeyboardInterrupt:
        print("\nDebug cancelled")
    except Exception as e:
        print(f"Debug error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 