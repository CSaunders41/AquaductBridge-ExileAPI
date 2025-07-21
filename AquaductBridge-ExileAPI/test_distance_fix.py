#!/usr/bin/env python3
"""
Test Distance Calculation Fix
Tests if the distance calculation is working correctly with mixed case keys
"""

import sys
from pathlib import Path

# Add the aqueduct_automation directory to the Python path
automation_dir = Path(__file__).parent / "aqueduct_automation"
sys.path.insert(0, str(automation_dir))

def test_distance_calculation():
    """Test distance calculation with mixed case keys"""
    print("📏 Testing Distance Calculation Fix")
    print("=" * 50)
    
    from utils import calculate_distance
    
    # Test data from the logs
    current_pos = {'X': 524, 'Y': 229, 'Z': 0}  # Player position (uppercase)
    target_pos = {'x': 522, 'y': 235}  # Target waypoint (lowercase)
    
    print(f"Current position: {current_pos}")
    print(f"Target position: {target_pos}")
    
    # Calculate distance
    distance = calculate_distance(current_pos, target_pos)
    print(f"Calculated distance: {distance:.2f}")
    
    # Expected distance should be sqrt((522-524)² + (235-229)²) = sqrt(4 + 36) = sqrt(40) ≈ 6.32
    expected_distance = ((522 - 524) ** 2 + (235 - 229) ** 2) ** 0.5
    print(f"Expected distance: {expected_distance:.2f}")
    
    if abs(distance - expected_distance) < 0.1:
        print("✅ Distance calculation is correct!")
    else:
        print("❌ Distance calculation is still wrong!")
        print(f"Difference: {abs(distance - expected_distance):.2f}")
    
    # Test more cases
    print("\n--- Additional Test Cases ---")
    
    test_cases = [
        # Same case (uppercase)
        ({'X': 100, 'Y': 100}, {'X': 103, 'Y': 104}, 5.0),
        # Same case (lowercase)
        ({'x': 100, 'y': 100}, {'x': 103, 'y': 104}, 5.0),
        # Mixed case
        ({'X': 100, 'Y': 100}, {'x': 103, 'y': 104}, 5.0),
        # Reverse mixed case
        ({'x': 100, 'y': 100}, {'X': 103, 'Y': 104}, 5.0),
        # Real example from logs
        ({'X': 524, 'Y': 229}, {'x': 515, 'y': 259}, 31.32),
    ]
    
    for i, (pos1, pos2, expected) in enumerate(test_cases):
        distance = calculate_distance(pos1, pos2)
        print(f"Test {i+1}: {distance:.2f} (expected: {expected:.2f}) - {'✅' if abs(distance - expected) < 0.1 else '❌'}")
    
    print("\n--- Summary ---")
    print("If all tests pass, the distance calculation should work correctly")
    print("and the 'Final distance: 571.85' error should be resolved.")

def main():
    try:
        test_distance_calculation()
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 