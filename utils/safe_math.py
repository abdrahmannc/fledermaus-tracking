"""
Safe mathematical operations to prevent division by zero and other mathematical errors.
"""
import logging
from typing import Union, Optional

logger = logging.getLogger(__name__)


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], 
                default: Union[int, float] = 0.0, min_denominator: float = 1e-10) -> float:
    """
    Safely divide two numbers, avoiding division by zero.
    
    Args:
        numerator: The numerator value
        denominator: The denominator value
        default: Default value to return if division is unsafe
        min_denominator: Minimum allowed denominator value
        
    Returns:
        Result of division or default value if unsafe
    """
    if abs(denominator) < min_denominator:
        logger.warning(f"Division by zero avoided: {numerator}/{denominator}, returning {default}")
        return default
    
    try:
        return float(numerator) / float(denominator)
    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"Mathematical error in division: {e}, returning {default}")
        return default


def safe_fps_calculation(frame_idx: int, fps: float, fallback_fps: float = 30.0) -> float:
    """
    Safely calculate time from frame index and FPS.
    
    Args:
        frame_idx: Frame index
        fps: Frames per second
        fallback_fps: Fallback FPS if original is invalid
        
    Returns:
        Time in seconds
    """
    if fps <= 0:
        logger.warning(f"Invalid FPS {fps}, using fallback FPS {fallback_fps}")
        fps = fallback_fps
    
    return safe_divide(frame_idx, fps, default=0.0)


def safe_contour_center(moments: dict) -> tuple[float, float]:
    """
    Safely calculate contour center from moments, avoiding division by zero.
    
    Args:
        moments: OpenCV moments dictionary
        
    Returns:
        Tuple of (center_x, center_y) coordinates
    """
    m00 = moments.get("m00", 0)
    m10 = moments.get("m10", 0)
    m01 = moments.get("m01", 0)
    
    if abs(m00) < 1e-10:
        logger.warning("Contour has zero area (m00=0), returning default center (0, 0)")
        return (0.0, 0.0)
    
    center_x = safe_divide(m10, m00, default=0.0)
    center_y = safe_divide(m01, m00, default=0.0)
    
    return (center_x, center_y)


def validate_numeric_range(value: Union[int, float], min_val: float, max_val: float, 
                          default: float, name: str = "value") -> float:
    """
    Validate that a numeric value is within acceptable range.
    
    Args:
        value: Value to validate
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value
        default: Default value if validation fails
        name: Name of the value for logging
        
    Returns:
        Validated value or default
    """
    try:
        val = float(value)
        if min_val <= val <= max_val:
            return val
        else:
            logger.warning(f"{name} {val} is outside range [{min_val}, {max_val}], using default {default}")
            return default
    except (ValueError, TypeError):
        logger.error(f"Invalid {name} value: {value}, using default {default}")
        return default