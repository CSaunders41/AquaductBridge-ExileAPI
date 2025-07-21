#!/usr/bin/env python3
"""
Coordinate Fix Diagnostic Tool
Tests different coordinate conversion fixes to solve backwards movement
"""

import sys
import time
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def test_coordinate_fixes():
    """Test different coordinate conversion fixes"""
    print("🔧 Coordinate Fix Diagnostic Tool")
    print("=" * 50)
    print("This tool helps diagnose backwards movement issues")
    print("=" * 50)
    
    from api_client import AqueductAPIClient
    from coordinate_fix import get_coordinate_fix
    from input_controller import InputController
    
    client = AqueductAPIClient()
    coord_fix = get_coordinate_fix()
    input_controller = InputController()
    
    if not client.is_connected():
        print("❌ API not connected. Make sure:")
        print("   1. Path of Exile is running")
        print("   2. ExileAPI is loaded")
        print("   3. AqueductBridge plugin is enabled")
        print("   4. You are IN-GAME (not in menus)")
        return
    
    print("✅ API connected")
    
    # Get current player position
    try:
        game_data = client.get_game_info()
        if not game_data or 'player_pos' not in game_data:
            print("❌ Could not get player position from API")
            return
        
        player_pos = game_data['player_pos']
        player_x = player_pos.get('X', 0)
        player_y = player_pos.get('Y', 0)
        
        print(f"📍 Current player position: ({player_x}, {player_y})")
        
        # Test different coordinate fix combinations
        print("\n🧪 Testing coordinate fix combinations:")
        print("-" * 40)
        
        fix_results = coord_fix.test_coordinate_conversion(player_x, player_y)
        
        for name, (screen_x, screen_y) in fix_results.items():
            print(f"{name:15}: Screen({screen_x:4}, {screen_y:4})")
        
        print("\n" + "=" * 50)
        print("INTERACTIVE TESTING:")
        print("Each test will move your mouse to a position.")
        print("Watch where it goes relative to your character!")
        print("=" * 50)
        
        while True:
            print("\nSelect a coordinate fix to test:")
            print("1. normal        - No fixes applied")
            print("2. invert_y      - Invert Y axis (DEFAULT - usually fixes backwards)")
            print("3. invert_x      - Invert X axis")
            print("4. invert_both   - Invert both X and Y")
            print("5. swap_xy       - Swap X and Y coordinates")
            print("6. swap_invert_y - Swap XY and invert Y")
            print("7. Run movement test")
            print("0. Exit")
            
            choice = input("\nEnter choice (1-7, 0 to exit): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                test_coordinate_fix(coord_fix, input_controller, player_x, player_y, False, False, False, "normal")
            elif choice == "2":
                test_coordinate_fix(coord_fix, input_controller, player_x, player_y, False, True, False, "invert_y")
            elif choice == "3":
                test_coordinate_fix(coord_fix, input_controller, player_x, player_y, True, False, False, "invert_x")
            elif choice == "4":
                test_coordinate_fix(coord_fix, input_controller, player_x, player_y, True, True, False, "invert_both")
            elif choice == "5":
                test_coordinate_fix(coord_fix, input_controller, player_x, player_y, False, False, True, "swap_xy")
            elif choice == "6":
                test_coordinate_fix(coord_fix, input_controller, player_x, player_y, False, True, True, "swap_invert_y")
            elif choice == "7":
                run_movement_test(client, coord_fix, input_controller)
            else:
                print("Invalid choice!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_coordinate_fix(coord_fix, input_controller, player_x, player_y, invert_x, invert_y, swap_xy, name):
    """Test a specific coordinate fix configuration"""
    print(f"\n🎯 Testing {name} configuration...")
    print(f"   invert_x={invert_x}, invert_y={invert_y}, swap_xy={swap_xy}")
    
    # Apply the fix
    coord_fix.set_coordinate_fixes(invert_x, invert_y, swap_xy)
    
    # Calculate test positions around the player
    test_positions = [
        (player_x + 50, player_y, "50 units RIGHT of player"),
        (player_x - 50, player_y, "50 units LEFT of player"),  
        (player_x, player_y + 50, "50 units DOWN from player"),
        (player_x, player_y - 50, "50 units UP from player"),
    ]
    
    for test_x, test_y, description in test_positions:
        screen_x, screen_y = coord_fix.convert_grid_to_screen(test_x, test_y)
        print(f"   {description}: Grid({test_x}, {test_y}) -> Screen({screen_x}, {screen_y})")
        
        # Move mouse to the position (but don't click)
        try:
            if hasattr(input_controller, 'mouse_controller'):
                input_controller.mouse_controller.position = (screen_x, screen_y)
                time.sleep(1)  # Give time to observe
            print(f"   ✅ Mouse moved to screen position")
        except Exception as e:
            print(f"   ❌ Could not move mouse: {e}")
    
    input("Press Enter to continue to next test...")

def run_movement_test(client, coord_fix, input_controller):
    """Run a full movement test"""
    print(f"\n🚶 Running Movement Test")
    print("=" * 30)
    print("This will attempt actual clicks to test movement")
    print("Make sure you're in a safe area!")
    
    confirm = input("Type 'TEST' to proceed: ")
    if confirm != "TEST":
        print("Test cancelled")
        return
    
    try:
        # Get current position
        game_data = client.get_game_info()
        player_pos = game_data['player_pos']
        start_x = player_pos.get('X', 0)
        start_y = player_pos.get('Y', 0)
        
        print(f"Starting position: ({start_x}, {start_y})")
        
        # Test small movement to the right
        target_x = start_x + 30
        target_y = start_y
        
        screen_x, screen_y = coord_fix.convert_grid_to_screen(target_x, target_y)
        print(f"Clicking at screen position: ({screen_x}, {screen_y})")
        print("This should move you RIGHT...")
        
        # Perform the click
        success = input_controller.click_position(screen_x, screen_y)
        if success:
            print("✅ Click sent")
            time.sleep(2)  # Wait for movement
            
            # Check if we moved correctly
            new_game_data = client.get_game_info()
            new_pos = new_game_data['player_pos']
            new_x = new_pos.get('X', 0)
            new_y = new_pos.get('Y', 0)
            
            print(f"New position: ({new_x}, {new_y})")
            
            # Analyze movement
            actual_dx = new_x - start_x
            actual_dy = new_y - start_y
            expected_dx = target_x - start_x
            expected_dy = target_y - start_y
            
            print(f"Expected movement: ({expected_dx}, {expected_dy})")
            print(f"Actual movement: ({actual_dx}, {actual_dy})")
            
            if abs(actual_dx - expected_dx) < 10 and abs(actual_dy - expected_dy) < 10:
                print("✅ Movement direction is CORRECT!")
            elif actual_dx < 0 and expected_dx > 0:
                print("❌ Moving LEFT when should move RIGHT - try invert_x=True")
            elif actual_dy < 0 and expected_dy > 0:
                print("❌ Moving UP when should move DOWN - try invert_y=True")
            else:
                print("⚠️ Movement doesn't match expected direction")
                
        else:
            print("❌ Click failed")
            
    except Exception as e:
        print(f"❌ Movement test error: {e}")

if __name__ == "__main__":
    try:
        test_coordinate_fixes()
    except KeyboardInterrupt:
        print("\n👋 Diagnostic tool stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc() 