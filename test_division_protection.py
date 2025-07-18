#!/usr/bin/env python3
"""
Test script to verify division by zero protections.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.safe_math import safe_divide, safe_fps_calculation, safe_contour_center, validate_numeric_range

def test_safe_divide():
    """Test safe_divide function."""
    print("Testing safe_divide function...")
    
    # Test normal division
    result = safe_divide(10, 2)
    assert result == 5.0, f"Expected 5.0, got {result}"
    print("  ✓ Normal division works")
    
    # Test division by zero
    result = safe_divide(10, 0, default=99.0)
    assert result == 99.0, f"Expected 99.0, got {result}"
    print("  ✓ Division by zero protection works")
    
    # Test very small denominator
    result = safe_divide(10, 1e-15, default=50.0)
    assert result == 50.0, f"Expected 50.0, got {result}"
    print("  ✓ Small denominator protection works")


def test_safe_fps_calculation():
    """Test safe_fps_calculation function."""
    print("Testing safe_fps_calculation function...")
    
    # Test normal FPS
    result = safe_fps_calculation(30, 30.0)
    assert result == 1.0, f"Expected 1.0, got {result}"
    print("  ✓ Normal FPS calculation works")
    
    # Test zero FPS (should use fallback)
    result = safe_fps_calculation(30, 0.0, fallback_fps=15.0)
    assert result == 2.0, f"Expected 2.0, got {result}"  # 30 frames / 15 fps = 2 seconds
    print("  ✓ Zero FPS fallback works")
    
    # Test negative FPS (should use fallback)
    result = safe_fps_calculation(60, -10.0, fallback_fps=30.0)
    assert result == 2.0, f"Expected 2.0, got {result}"  # 60 frames / 30 fps = 2 seconds
    print("  ✓ Negative FPS fallback works")


def test_safe_contour_center():
    """Test safe_contour_center function."""
    print("Testing safe_contour_center function...")
    
    # Test normal moments
    moments = {"m00": 100, "m10": 500, "m01": 300}
    result = safe_contour_center(moments)
    assert result == (5.0, 3.0), f"Expected (5.0, 3.0), got {result}"
    print("  ✓ Normal contour center calculation works")
    
    # Test zero area moment
    moments = {"m00": 0, "m10": 500, "m01": 300}
    result = safe_contour_center(moments)
    assert result == (0.0, 0.0), f"Expected (0.0, 0.0), got {result}"
    print("  ✓ Zero area moment protection works")
    
    # Test missing moments
    moments = {}
    result = safe_contour_center(moments)
    assert result == (0.0, 0.0), f"Expected (0.0, 0.0), got {result}"
    print("  ✓ Missing moments protection works")


def test_validate_numeric_range():
    """Test validate_numeric_range function."""
    print("Testing validate_numeric_range function...")
    
    # Test valid value
    result = validate_numeric_range(5.0, 1.0, 10.0, 0.0, "test")
    assert result == 5.0, f"Expected 5.0, got {result}"
    print("  ✓ Valid range validation works")
    
    # Test value below range
    result = validate_numeric_range(0.5, 1.0, 10.0, 5.0, "test")
    assert result == 5.0, f"Expected 5.0, got {result}"
    print("  ✓ Below range validation works")
    
    # Test value above range
    result = validate_numeric_range(15.0, 1.0, 10.0, 5.0, "test")
    assert result == 5.0, f"Expected 5.0, got {result}"
    print("  ✓ Above range validation works")
    
    # Test invalid value (string)
    result = validate_numeric_range("invalid", 1.0, 10.0, 5.0, "test")
    assert result == 5.0, f"Expected 5.0, got {result}"
    print("  ✓ Invalid value validation works")


def main():
    """Run all tests."""
    print("Running division by zero protection tests...\n")
    
    try:
        test_safe_divide()
        print()
        
        test_safe_fps_calculation()
        print()
        
        test_safe_contour_center()
        print()
        
        test_validate_numeric_range()
        print()
        
        print("🎉 All tests passed! Division by zero protections are working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)