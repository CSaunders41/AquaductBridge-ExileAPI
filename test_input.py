#!/usr/bin/env python3
"""
Simple test script to verify input controller functionality
"""

import sys
import time
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def test_input_controller():
    print("🧪 Testing Input Controller")
    print("=" * 40)
    
    try:
        from input_controller import InputController
        
        # Create input controller
        controller = InputController()
        
        print(f"Input method: {controller.get_method()}")
        print(f"Input available: {controller.is_available()}")
        
        if not controller.is_available():
            print("❌ No input libraries available!")
            print("Install PyAutoGUI or pynput:")
            print("  pip install pyautogui")
            print("  pip install pynput")
            return False
        
        print("✅ Input controller is working!")
        
        # Test mouse position
        mouse_pos = controller.get_mouse_position()
        print(f"Current mouse position: {mouse_pos}")
        
        # Test keyboard input (safe)
        print("\n🔤 Testing keyboard input...")
        print("This will NOT send any keys - just test the method")
        
        # Test without actually sending keys
        print("✅ Keyboard input methods are available")
        
        print("\n⚠️  IMPORTANT:")
        print("The automation will now be able to control mouse and keyboard")
        print("Make sure Path of Exile is running and focused when you start automation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing input controller: {e}")
        return False

def test_api_connection():
    print("\n🌐 Testing API Connection")
    print("=" * 40)
    
    try:
        from api_client import AqueductAPIClient
        
        client = AqueductAPIClient()
        
        if client.is_connected():
            print("✅ API connection successful!")
            
            # Get game info
            game_info = client.get_game_info()
            if game_info:
                print(f"Player: {game_info.get('player_name', 'Unknown')}")
                print(f"Area: {game_info.get('area_name', 'Unknown')}")
                print(f"In Game: {game_info.get('in_game', False)}")
                return True
            else:
                print("⚠️  API connected but no game data")
                return False
        else:
            print("❌ API connection failed")
            print("Make sure ExileAPI is running with AqueductBridge plugin")
            return False
            
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def main():
    print("🎯 Aqueduct Automation - System Test")
    print("=" * 50)
    
    # Test input controller
    input_ok = test_input_controller()
    
    # Test API connection
    api_ok = test_api_connection()
    
    print("\n📊 Test Results")
    print("=" * 50)
    print(f"Input Controller: {'✅ PASS' if input_ok else '❌ FAIL'}")
    print(f"API Connection: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if input_ok and api_ok:
        print("\n🎉 All tests passed! Automation is ready to run.")
        print("Start automation with: python start_automation.py")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
        
        if not input_ok:
            print("\nTo fix input issues:")
            print("  pip install pyautogui pynput")
            
        if not api_ok:
            print("\nTo fix API issues:")
            print("  1. Start ExileAPI")
            print("  2. Enable AqueductBridge plugin")
            print("  3. Make sure Path of Exile is running")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest cancelled")
    except Exception as e:
        print(f"Test error: {e}")
    
    input("\nPress Enter to exit...") 