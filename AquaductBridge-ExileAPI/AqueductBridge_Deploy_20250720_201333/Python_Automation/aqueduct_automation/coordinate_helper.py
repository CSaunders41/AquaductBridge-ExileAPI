"""
Coordinate Helper for Aqueduct Automation
Handles coordinate conversion and validation
"""

import logging
from typing import Tuple, Dict, Any, Optional

class CoordinateHelper:
    """Helper class for handling coordinate conversions and validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.game_window = None
        self.coordinate_offset = (0, 0)
        self.coordinate_scale = 1.0
        
    def set_game_window(self, window_info: Dict[str, Any]):
        """Set the game window information"""
        self.game_window = window_info
        self.logger.info(f"Game window set: {window_info}")
    
    def validate_screen_coordinates(self, x: int, y: int) -> bool:
        """Validate that screen coordinates are reasonable"""
        # Basic range check - much more restrictive
        if x < -100 or x > 3000 or y < -100 or y > 3000:
            self.logger.warning(f"Coordinates ({x}, {y}) outside reasonable range (-100 to 3000)")
            return False
        
        # Check for fail-safe trigger coordinates (top-left corner)
        if x < 5 and y < 5:
            self.logger.warning(f"Coordinates ({x}, {y}) would trigger fail-safe")
            return False
        
        # Check for obviously invalid coordinates (negative or very large)
        if x < 0 or y < 0:
            self.logger.warning(f"Negative coordinates ({x}, {y}) are invalid")
            return False
        
        # Check for coordinates that are way too large for any reasonable screen
        if x > 2560 or y > 1440:  # Larger than 1440p
            self.logger.warning(f"Coordinates ({x}, {y}) are too large for normal screen")
            return False
        
        return True
    
    def convert_game_to_screen(self, game_x: int, game_y: int) -> Tuple[int, int]:
        """Convert game coordinates to screen coordinates"""
        try:
            # If we have window information, use it to validate
            if self.game_window:
                window_x = self.game_window.get('X', 0)
                window_y = self.game_window.get('Y', 0)
                window_width = self.game_window.get('Width', 1920)
                window_height = self.game_window.get('Height', 1080)
                
                # Check if coordinates are within reasonable bounds relative to window
                if game_x > window_width * 3 or game_y > window_height * 3:
                    self.logger.warning(f"Game coordinates ({game_x}, {game_y}) seem too large for window {window_width}x{window_height}")
                    return self._fallback_coordinate_conversion(game_x, game_y)
            
            # For now, assume coordinates are already in screen space but may need adjustment
            screen_x = game_x
            screen_y = game_y
            
            # Apply any offset correction
            screen_x += self.coordinate_offset[0]
            screen_y += self.coordinate_offset[1]
            
            # Apply scaling if needed
            screen_x = int(screen_x * self.coordinate_scale)
            screen_y = int(screen_y * self.coordinate_scale)
            
            return (screen_x, screen_y)
            
        except Exception as e:
            self.logger.error(f"Error converting coordinates ({game_x}, {game_y}): {e}")
            return (0, 0)
    
    def _fallback_coordinate_conversion(self, game_x: int, game_y: int) -> Tuple[int, int]:
        """Fallback coordinate conversion when normal conversion fails"""
        # If coordinates are way too large, try to scale them down
        if self.game_window:
            window_width = self.game_window.get('Width', 1920)
            window_height = self.game_window.get('Height', 1080)
            
            # If coordinates are much larger than window, try scaling
            if game_x > window_width * 2:
                scale_factor = window_width / max(game_x, 1)
                screen_x = int(game_x * scale_factor)
                screen_y = int(game_y * scale_factor)
                
                self.logger.info(f"Applied scaling factor {scale_factor:.3f} to coordinates ({game_x}, {game_y}) -> ({screen_x}, {screen_y})")
                return (screen_x, screen_y)
        
        # If all else fails, return center of screen
        center_x = 960 if not self.game_window else self.game_window.get('Width', 1920) // 2
        center_y = 540 if not self.game_window else self.game_window.get('Height', 1080) // 2
        
        self.logger.warning(f"Using screen center ({center_x}, {center_y}) as fallback for ({game_x}, {game_y})")
        return (center_x, center_y)
    
    def get_safe_click_coordinates(self, entity: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Get safe click coordinates for an entity"""
        try:
            # Try to get screen position from entity
            screen_pos = entity.get('location_on_screen', {})
            if screen_pos:
                x = screen_pos.get('X', 0)
                y = screen_pos.get('Y', 0)
                
                self.logger.debug(f"Raw entity coordinates: ({x}, {y})")
                
                # Convert and validate
                converted_x, converted_y = self.convert_game_to_screen(x, y)
                
                if self.validate_screen_coordinates(converted_x, converted_y):
                    return (converted_x, converted_y)
                else:
                    self.logger.warning(f"Invalid converted coordinates: ({converted_x}, {converted_y})")
                    return None
            
            # Try to get grid position and convert
            grid_pos = entity.get('GridPosition', {})
            if grid_pos:
                grid_x = grid_pos.get('X', 0)
                grid_y = grid_pos.get('Y', 0)
                
                self.logger.debug(f"Using grid position: ({grid_x}, {grid_y})")
                
                # For grid position, we need to use the API conversion
                # This would require an API call, so for now return None
                # and let the caller handle the conversion
                return None
            
            self.logger.warning("No valid position data found in entity")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting safe coordinates for entity: {e}")
            return None
    
    def is_position_on_screen(self, x: int, y: int) -> bool:
        """Check if position is visible on screen"""
        if not self.game_window:
            # Without window info, use reasonable defaults
            return 0 <= x <= 1920 and 0 <= y <= 1080
        
        window_x = self.game_window.get('X', 0)
        window_y = self.game_window.get('Y', 0)
        window_width = self.game_window.get('Width', 1920)
        window_height = self.game_window.get('Height', 1080)
        
        return (window_x <= x <= window_x + window_width and
                window_y <= y <= window_y + window_height)
    
    def get_screen_center(self) -> Tuple[int, int]:
        """Get center of screen/game window"""
        if not self.game_window:
            return (960, 540)
        
        window_x = self.game_window.get('X', 0)
        window_y = self.game_window.get('Y', 0)
        window_width = self.game_window.get('Width', 1920)
        window_height = self.game_window.get('Height', 1080)
        
        center_x = window_x + window_width // 2
        center_y = window_y + window_height // 2
        
        return (center_x, center_y)
    
    def debug_coordinates(self, entity: Dict[str, Any]):
        """Debug coordinate information for an entity"""
        self.logger.info(f"=== Entity Coordinate Debug ===")
        
        # Grid position (the good data)
        grid_pos = entity.get('GridPosition', {})
        if grid_pos:
            self.logger.info(f"Grid position: {grid_pos}")
        
        # Screen position (the broken data - for comparison)
        screen_pos = entity.get('location_on_screen', {})
        if screen_pos:
            self.logger.info(f"Screen position (BROKEN): {screen_pos}")
        
        # Entity type and path
        self.logger.info(f"Entity type: {entity.get('EntityType', 'Unknown')}")
        self.logger.info(f"Entity path: {entity.get('Path', 'Unknown')}")
        
        # Try coordinate fix conversion using grid coordinates
        if grid_pos:
            from coordinate_fix import get_coordinate_fix
            coord_fix = get_coordinate_fix()
            fixed_coords = coord_fix.get_entity_click_position(entity)
            self.logger.info(f"Fixed coordinates: {fixed_coords}")
            if fixed_coords:
                self.logger.info(f"Fixed coordinates valid: {self.validate_screen_coordinates(*fixed_coords)}")
                self.logger.info(f"Fixed position on screen: {self.is_position_on_screen(*fixed_coords)}")
        
        self.logger.info(f"=== End Debug ===")

# Global coordinate helper instance
_coordinate_helper = None

def get_coordinate_helper() -> CoordinateHelper:
    """Get the global coordinate helper instance"""
    global _coordinate_helper
    if _coordinate_helper is None:
        _coordinate_helper = CoordinateHelper()
    return _coordinate_helper 