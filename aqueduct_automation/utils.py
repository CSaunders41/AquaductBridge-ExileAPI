"""
Utility Functions for Aqueduct Automation
Helper functions, logging setup, and common utilities
"""

import logging
import time
import random
import math
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import sys
import os

def setup_logging(log_level: str = "INFO", log_to_file: bool = True, log_file: str = "automation.log"):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        file_handler = logging.FileHandler(log_dir / log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # Log startup message
    logging.info("Logging initialized")
    logging.info(f"Log level: {log_level}")
    logging.info(f"Log to file: {log_to_file}")

def calculate_distance(pos1: Dict[str, Any], pos2: Dict[str, Any]) -> float:
    """Calculate Euclidean distance between two positions"""
    try:
        x1, y1 = pos1.get('X', 0), pos1.get('Y', 0)
        x2, y2 = pos2.get('X', 0), pos2.get('Y', 0)
        
        dx = x2 - x1
        dy = y2 - y1
        
        return math.sqrt(dx * dx + dy * dy)
        
    except Exception as e:
        logging.error(f"Error calculating distance: {e}")
        return 0.0

def calculate_angle(pos1: Dict[str, Any], pos2: Dict[str, Any]) -> float:
    """Calculate angle between two positions in degrees"""
    try:
        x1, y1 = pos1.get('X', 0), pos1.get('Y', 0)
        x2, y2 = pos2.get('X', 0), pos2.get('Y', 0)
        
        dx = x2 - x1
        dy = y2 - y1
        
        angle = math.atan2(dy, dx)
        return math.degrees(angle)
        
    except Exception as e:
        logging.error(f"Error calculating angle: {e}")
        return 0.0

def is_position_within_circle(center: Dict[str, Any], point: Dict[str, Any], radius: float) -> bool:
    """Check if a point is within a circular area"""
    distance = calculate_distance(center, point)
    return distance <= radius

def is_position_within_rectangle(top_left: Dict[str, Any], bottom_right: Dict[str, Any], 
                                point: Dict[str, Any]) -> bool:
    """Check if a point is within a rectangular area"""
    try:
        x, y = point.get('X', 0), point.get('Y', 0)
        x1, y1 = top_left.get('X', 0), top_left.get('Y', 0)
        x2, y2 = bottom_right.get('X', 0), bottom_right.get('Y', 0)
        
        return x1 <= x <= x2 and y1 <= y <= y2
        
    except Exception as e:
        logging.error(f"Error checking rectangle bounds: {e}")
        return False

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max"""
    return max(min_val, min(max_val, value))

def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation between start and end"""
    return start + t * (end - start)

def normalize_angle(angle: float) -> float:
    """Normalize angle to 0-360 degrees"""
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle

def safe_sleep(duration: float, variance: float = 0.1):
    """Sleep with random variance for anti-detection"""
    try:
        # Add random variance to avoid predictable timing
        actual_duration = duration + random.uniform(-variance, variance)
        actual_duration = max(0.01, actual_duration)  # Minimum 10ms
        
        time.sleep(actual_duration)
        
    except Exception as e:
        logging.error(f"Error in safe_sleep: {e}")
        time.sleep(duration)  # Fallback to regular sleep

def random_delay(min_delay: float = 0.1, max_delay: float = 0.5):
    """Random delay for anti-detection"""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def format_time(seconds: float) -> str:
    """Format seconds into human readable time"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def format_number(num: int) -> str:
    """Format large numbers with commas"""
    return f"{num:,}"

def calculate_efficiency(items_collected: int, time_elapsed: float) -> float:
    """Calculate items per hour efficiency"""
    if time_elapsed <= 0:
        return 0.0
    return (items_collected / time_elapsed) * 3600

def percentage_to_float(percentage: float) -> float:
    """Convert percentage (0-100) to float (0.0-1.0)"""
    return clamp(percentage / 100.0, 0.0, 1.0)

def float_to_percentage(value: float) -> float:
    """Convert float (0.0-1.0) to percentage (0-100)"""
    return clamp(value * 100.0, 0.0, 100.0)

def get_screen_center(window_info: Dict[str, Any]) -> Tuple[int, int]:
    """Get center coordinates of game window"""
    try:
        x = window_info.get('X', 0)
        y = window_info.get('Y', 0)
        width = window_info.get('Width', 1920)
        height = window_info.get('Height', 1080)
        
        center_x = x + width // 2
        center_y = y + height // 2
        
        return (center_x, center_y)
        
    except Exception as e:
        logging.error(f"Error getting screen center: {e}")
        return (960, 540)  # Default center

def is_within_screen_bounds(pos: Tuple[int, int], window_info: Dict[str, Any]) -> bool:
    """Check if position is within screen bounds"""
    try:
        x, y = pos
        window_x = window_info.get('X', 0)
        window_y = window_info.get('Y', 0)
        width = window_info.get('Width', 1920)
        height = window_info.get('Height', 1080)
        
        return (window_x <= x <= window_x + width and
                window_y <= y <= window_y + height)
        
    except Exception as e:
        logging.error(f"Error checking screen bounds: {e}")
        return False

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        time.sleep(delay)
                    else:
                        logging.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator

def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """Create a text progress bar"""
    if total <= 0:
        return "[" + "?" * width + "]"
    
    progress = current / total
    filled = int(width * progress)
    bar = "=" * filled + "-" * (width - filled)
    percentage = int(progress * 100)
    
    return f"[{bar}] {percentage}% ({current}/{total})"

def validate_position(pos: Dict[str, Any]) -> bool:
    """Validate position dictionary has required keys"""
    required_keys = ['X', 'Y']
    return all(key in pos for key in required_keys)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    filename = filename[:200]
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    return filename

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0

def ensure_directory_exists(directory: str):
    """Ensure directory exists, create if it doesn't"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def get_timestamp() -> str:
    """Get current timestamp as string"""
    return time.strftime("%Y%m%d_%H%M%S")

def get_human_readable_timestamp() -> str:
    """Get human readable timestamp"""
    return time.strftime("%Y-%m-%d %H:%M:%S")

class Timer:
    """Simple timer utility"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer"""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self):
        """Stop the timer"""
        if self.start_time is not None:
            self.end_time = time.time()
    
    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time
    
    def elapsed_str(self) -> str:
        """Get elapsed time as formatted string"""
        return format_time(self.elapsed())

class RateLimiter:
    """Rate limiter utility"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_call(self) -> bool:
        """Check if a call can be made"""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a call"""
        self.calls.append(time.time())
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        if not self.can_call():
            # Wait until the oldest call expires
            if self.calls:
                oldest_call = min(self.calls)
                wait_time = self.time_window - (time.time() - oldest_call) + 0.1
                if wait_time > 0:
                    time.sleep(wait_time)

class MovingAverage:
    """Moving average calculator"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.values = []
    
    def add_value(self, value: float):
        """Add a value to the average"""
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
    
    def get_average(self) -> float:
        """Get the current average"""
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)
    
    def reset(self):
        """Reset the average"""
        self.values.clear()

def calculate_eta(current: int, total: int, elapsed_time: float) -> str:
    """Calculate estimated time to completion"""
    if current <= 0 or elapsed_time <= 0:
        return "Unknown"
    
    rate = current / elapsed_time
    remaining = total - current
    
    if rate <= 0:
        return "Unknown"
    
    eta_seconds = remaining / rate
    return format_time(eta_seconds)

def create_summary_stats(stats: Dict[str, Any]) -> str:
    """Create a formatted summary of statistics"""
    lines = []
    lines.append("=== Automation Summary ===")
    
    for key, value in stats.items():
        if isinstance(value, float):
            if 'time' in key.lower():
                lines.append(f"{key}: {format_time(value)}")
            elif 'percentage' in key.lower():
                lines.append(f"{key}: {value:.1f}%")
            else:
                lines.append(f"{key}: {value:.2f}")
        elif isinstance(value, int):
            lines.append(f"{key}: {format_number(value)}")
        else:
            lines.append(f"{key}: {value}")
    
    return '\n'.join(lines)

# Constants
EPSILON = 1e-10  # Small value for floating point comparisons
DEFAULT_TIMEOUT = 30.0  # Default timeout in seconds
MAX_RETRIES = 3  # Default maximum retries 