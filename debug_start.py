#!/usr/bin/env python3
"""
Debug Start Script for Aqueduct Automation
Runs in safe mode and debug mode to diagnose coordinate issues
"""

import sys
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def main():
    print("🐛 Aqueduct Automation - Debug Start")
    print("=" * 50)
    print("This will run in DEBUG + SAFE MODE")
    print("- DEBUG MODE: Shows detailed coordinate information")
    print("- SAFE MODE: No actual clicks will be performed")
    print("- This helps diagnose coordinate issues safely")
    print("=" * 50)
    
    # Import and run with debug flags
    from aqueduct_automation.main import AqueductAutomation
    from aqueduct_automation.config import AutomationConfig
    from aqueduct_automation.utils import setup_logging
    
    # Set up debug logging
    setup_logging(log_level="DEBUG")
    
    # Create config
    config = AutomationConfig()
    config.max_runs = 3  # Only 3 runs for debugging
    
    # Create automation with debug and safe mode
    automation = AqueductAutomation(config, debug_mode=True, safe_mode=True)
    
    print("\n🎯 Starting debug automation...")
    print("Watch for coordinate information in the logs!")
    print("Press Ctrl+C to stop\n")
    
    try:
        automation.start_automation()
    except KeyboardInterrupt:
        print("\n✅ Debug stopped by user")
    except Exception as e:
        print(f"\n❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n📊 Debug complete!")
    print("Look for these in the logs:")
    print("- 'Raw entity coordinates' - shows what API returns")
    print("- 'Converted coordinates' - shows coordinate conversion")
    print("- 'Invalid coordinates' - shows validation failures")
    print("- 'Refusing to click' - shows blocked clicks")

if __name__ == "__main__":
    main() 