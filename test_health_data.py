#!/usr/bin/env python3
"""
Test Health Data Retrieval
Tests if the resource manager can correctly get health/mana data from the API
"""

import sys
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def test_health_data():
    """Test health data retrieval"""
    print("💊 Testing Health Data Retrieval")
    print("=" * 40)
    
    # Test API client directly
    print("\n--- Test 1: Direct API Client ---")
    from api_client import AqueductAPIClient
    
    client = AqueductAPIClient()
    
    if not client.is_connected():
        print("❌ API not connected. Make sure AqueductBridge is running.")
        return
    
    print("✅ API connected")
    
    # Test life data from API
    life_data = client.get_life_data()
    print(f"Life data from API: {life_data}")
    
    # Test direct health percentage
    health_pct = client.get_health_percentage()
    mana_pct = client.get_mana_percentage()
    print(f"Health percentage: {health_pct:.1f}%")
    print(f"Mana percentage: {mana_pct:.1f}%")
    
    # Test resource manager
    print("\n--- Test 2: Resource Manager ---")
    from resource_manager import ResourceManager, create_resource_config
    
    # Create with safe mode configuration
    config = create_resource_config("safe_mode")
    resource_manager = ResourceManager(config)
    
    print(f"Resource config thresholds:")
    print(f"  Health flask: {config.health_flask_threshold}%")
    print(f"  Critical health: {config.critical_health_threshold}%")
    print(f"  Retreat health: {config.retreat_health_threshold}%")
    print(f"  Panic mode: {config.panic_mode_threshold}%")
    
    # Update resource status
    resource_manager.update_resource_status()
    
    # Check current status
    status = resource_manager.current_status
    print(f"\nCurrent resource status:")
    print(f"  Health: {status.health_percentage:.1f}% ({status.health_current}/{status.health_max})")
    print(f"  Mana: {status.mana_percentage:.1f}% ({status.mana_current}/{status.mana_max})")
    print(f"  ES: {status.es_percentage:.1f}% ({status.es_current}/{status.es_max})")
    
    # Test status checks
    print(f"\nStatus checks:")
    print(f"  Is critical: {status.is_critical(config)}")
    print(f"  Should retreat: {status.should_retreat(config)}")
    print(f"  Is panic mode: {status.is_panic_mode(config)}")
    print(f"  Is healthy: {resource_manager.is_healthy()}")
    
    # Test flask usage decisions
    print(f"\nFlask usage decisions:")
    print(f"  Should use health flask: {resource_manager._should_use_health_flask()}")
    print(f"  Should use mana flask: {resource_manager._should_use_mana_flask()}")
    print(f"  Should use hybrid flask: {resource_manager._should_use_hybrid_flask()}")
    print(f"  Should use utility flask: {resource_manager._should_use_utility_flasks()}")
    
    # Test with default config
    print("\n--- Test 3: Default Config ---")
    default_config = create_resource_config("default")
    print(f"Default config thresholds:")
    print(f"  Health flask: {default_config.health_flask_threshold}%")
    print(f"  Critical health: {default_config.critical_health_threshold}%")
    print(f"  Retreat health: {default_config.retreat_health_threshold}%")
    print(f"  Panic mode: {default_config.panic_mode_threshold}%")
    
    # Test with default config
    default_status = status  # Same status, different config
    print(f"\nWith default config:")
    print(f"  Is critical: {default_status.is_critical(default_config)}")
    print(f"  Should retreat: {default_status.should_retreat(default_config)}")
    print(f"  Is panic mode: {default_status.is_panic_mode(default_config)}")
    
    print("\n✅ Health data test complete!")
    print("\nKey findings:")
    print("- Check if health data is being retrieved correctly")
    print("- Look for reasonable health/mana values")
    print("- Verify that status checks make sense")
    print("- Test different configurations")

def main():
    try:
        test_health_data()
    except KeyboardInterrupt:
        print("\nTest cancelled")
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 