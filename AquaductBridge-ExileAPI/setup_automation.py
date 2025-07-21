#!/usr/bin/env python3
"""
Setup script for Aqueduct Automation
Helps users configure their automation settings
"""

import sys
import os
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def main():
    print("🎯 Aqueduct Automation Setup")
    print("=" * 50)
    
    # Check if API is accessible
    print("1. Checking API connection...")
    try:
        from api_client import AqueductAPIClient
        
        client = AqueductAPIClient()
        if client.is_connected():
            print("✅ API connection successful!")
            
            # Get basic game info
            game_info = client.get_game_info()
            if game_info:
                print(f"   Player: {game_info.get('player_name', 'Unknown')}")
                print(f"   Area: {game_info.get('area_name', 'Unknown')}")
                print(f"   In Game: {game_info.get('in_game', False)}")
        else:
            print("❌ API connection failed!")
            print("   Make sure ExileAPI is running with AqueductBridge plugin enabled")
            return False
            
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False
    
    print("\n2. Configuration Options:")
    print("   1. Speed Farming (fast, less safe)")
    print("   2. Safe Farming (slower, safer)")
    print("   3. Currency Farming (currency focus)")
    print("   4. Custom Configuration")
    
    while True:
        try:
            choice = input("\nSelect configuration (1-4): ").strip()
            if choice in ["1", "2", "3", "4"]:
                break
            print("Please enter 1, 2, 3, or 4")
        except KeyboardInterrupt:
            print("\nSetup cancelled")
            return False
    
    # Create configuration
    try:
        from config import ConfigTemplates, ConfigManager
        
        config_manager = ConfigManager()
        
        if choice == "1":
            config = ConfigTemplates.create_speed_farming_config()
            config_name = "speed_farming"
        elif choice == "2":
            config = ConfigTemplates.create_safe_farming_config()
            config_name = "safe_farming"
        elif choice == "3":
            config = ConfigTemplates.create_currency_farming_config()
            config_name = "currency_farming"
        else:
            from config import create_config_from_user_input
            config = create_config_from_user_input()
            config_name = "custom"
        
        # Save configuration
        config_manager.save_config(config, config_name)
        print(f"\n✅ Configuration saved as '{config_name}'")
        
        # Ask about flask keys
        print("\n3. Flask Configuration:")
        print("   Current settings:")
        print(f"   Life Flask: {config.resource_config.life_flask_key}")
        print(f"   Mana Flask: {config.resource_config.mana_flask_key}")
        print(f"   Utility Flasks: {', '.join(config.resource_config.utility_flask_keys)}")
        
        modify_flasks = input("\nModify flask keys? (y/n): ").strip().lower()
        if modify_flasks in ["y", "yes"]:
            config.resource_config.life_flask_key = input("Life flask key (current: {}): ".format(config.resource_config.life_flask_key)) or config.resource_config.life_flask_key
            config.resource_config.mana_flask_key = input("Mana flask key (current: {}): ".format(config.resource_config.mana_flask_key)) or config.resource_config.mana_flask_key
            
            # Save updated configuration
            config_manager.save_config(config, config_name)
            print("✅ Flask configuration updated")
        
        print("\n4. Setup Complete!")
        print("=" * 50)
        print("To start automation:")
        print("   Windows: Double-click start_automation.bat")
        print("   Mac/Linux: ./start_automation.py")
        print("   Manual: python aqueduct_automation/main.py")
        print("\nTo stop automation:")
        print("   Press Ctrl+C in the terminal")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup cancelled")
    except Exception as e:
        print(f"Setup error: {e}")
    
    input("\nPress Enter to exit...") 