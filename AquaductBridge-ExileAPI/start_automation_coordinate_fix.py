#!/usr/bin/env python3
"""
Aqueduct Automation with Coordinate Fix
Uses the new coordinate fix system to bypass broken AqueductBridge API
"""

import sys
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def main():
    print("🚀 Aqueduct Automation - Coordinate Fix Version")
    print("=" * 60)
    print("This version uses the coordinate fix system to bypass")
    print("the broken AqueductBridge positionOnScreen API.")
    print("=" * 60)
    
    # Import and run automation
    from aqueduct_automation.main import AqueductAutomation
    from aqueduct_automation.config import AutomationConfig
    from aqueduct_automation.utils import setup_logging
    
    # Set up logging
    setup_logging(log_level="INFO")
    
    # Create config
    config = AutomationConfig()
    
    # Ask user for preferences
    print("\n⚙️  Configuration Options:")
    print("1. Number of runs (0 = unlimited):")
    try:
        max_runs = int(input("   Enter max runs (default: 0): ") or "0")
        if max_runs > 0:
            config.max_runs = max_runs
    except ValueError:
        print("   Using default (unlimited runs)")
    
    print("\n2. Safety settings:")
    safe_mode = input("   Enable safe mode? (y/n, default: n): ").lower().startswith('y')
    debug_mode = input("   Enable debug mode? (y/n, default: n): ").lower().startswith('y')
    
    print("\n3. Advanced settings:")
    disable_failsafe = input("   Disable PyAutoGUI failsafe? (y/n, default: n): ").lower().startswith('y')
    
    # Handle PyAutoGUI failsafe
    if disable_failsafe:
        print("⚠️  Disabling PyAutoGUI failsafe...")
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            print("✅ PyAutoGUI failsafe disabled")
        except ImportError:
            print("⚠️  PyAutoGUI not available")
    
    # Create automation with coordinate fix
    automation = AqueductAutomation(config, debug_mode=debug_mode, safe_mode=safe_mode)
    
    print("\n🎯 Starting automation with coordinate fix...")
    print("Features:")
    print("- ✅ Coordinate validation prevents invalid clicks")
    print("- ✅ Grid coordinate conversion bypasses broken API")
    print("- ✅ Safe fallback positions for failed conversions")
    print("- ✅ Enhanced debugging and error handling")
    print("- ✅ No more PyAutoGUI failsafe errors")
    
    if safe_mode:
        print("\n🛡️  SAFE MODE: No actual clicks will be performed")
    
    if debug_mode:
        print("\n🐛 DEBUG MODE: Detailed coordinate information will be logged")
    
    print("\nPress Ctrl+C to stop automation")
    print("=" * 60)
    
    try:
        automation.start_automation()
    except KeyboardInterrupt:
        print("\n✅ Automation stopped by user")
    except Exception as e:
        print(f"\n❌ Automation error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n🔧 Troubleshooting:")
        print("1. Make sure AqueductBridge plugin is running")
        print("2. Check that Path of Exile is running")
        print("3. Verify you're in the correct area")
        print("4. Run test_coordinate_fix.py for diagnosis")
    
    print("\n📊 Automation complete!")

if __name__ == "__main__":
    main() 