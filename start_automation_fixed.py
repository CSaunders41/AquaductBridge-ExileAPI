#!/usr/bin/env python3
"""
Temporary Fix for PyAutoGUI Failsafe Issues
⚠️  THIS IS A TEMPORARY WORKAROUND - NOT RECOMMENDED FOR PRODUCTION ⚠️
"""

import sys
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def main():
    print("⚠️  Aqueduct Automation - Failsafe Disabled Version")
    print("=" * 60)
    print("WARNING: This version disables PyAutoGUI failsafe!")
    print("This is NOT RECOMMENDED for production use!")
    print("Only use this for testing the coordinate fix!")
    print("=" * 60)
    
    response = input("\nType 'I UNDERSTAND' to proceed: ")
    if response != "I UNDERSTAND":
        print("Aborted.")
        return
    
    print("\n🛠️  Disabling PyAutoGUI failsafe...")
    
    # Disable PyAutoGUI failsafe
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        print("✅ PyAutoGUI failsafe disabled")
    except ImportError:
        print("⚠️  PyAutoGUI not available")
    
    # Import and run automation
    from aqueduct_automation.main import AqueductAutomation
    from aqueduct_automation.config import AutomationConfig
    from aqueduct_automation.utils import setup_logging
    
    # Set up logging
    setup_logging(log_level="INFO")
    
    # Create config with limited runs for safety
    config = AutomationConfig()
    config.max_runs = 10  # Limit to 10 runs for safety
    
    # Create automation with coordinate validation
    automation = AqueductAutomation(config, debug_mode=False, safe_mode=False)
    
    print("\n🎯 Starting automation with coordinate validation...")
    print("The system will now validate coordinates before clicking.")
    print("Invalid coordinates will be rejected automatically.")
    print("Press Ctrl+C to stop\n")
    
    try:
        automation.start_automation()
    except KeyboardInterrupt:
        print("\n✅ Automation stopped by user")
    except Exception as e:
        print(f"\n❌ Automation error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n📊 Automation complete!")
    print("If you still see coordinate issues, please run debug_start.py")

if __name__ == "__main__":
    main() 