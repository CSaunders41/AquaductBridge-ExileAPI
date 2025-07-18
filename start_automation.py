#!/usr/bin/env python3
"""
Simple start script for Aqueduct Automation
"""

import os
from pathlib import Path

# Import and run the automation
from aqueduct_automation.main import main

if __name__ == "__main__":
    print("🎯 Starting Aqueduct Automation System...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("✅ Automation stopped by user")
        print("Thanks for using Aqueduct Automation!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Check the logs for more details") 