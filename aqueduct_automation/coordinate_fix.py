"""
Coordinate Fix for AqueductBridge API
Bypasses the broken positionOnScreen conversion and uses grid coordinates
"""

import logging
from typing import Tuple, Dict, Any, Optional

class CoordinateFix:
    """Fixed coordinate system that bypasses broken API conversion"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.game_window = None
        self.grid_to_screen_scale = 1.0
        self.screen_offset = (0, 0)
        self.calibrated = False
        
    def set_game_window(self, window_info: Dict[str, Any]):
        """Set the game window information"""
        self.game_window = window_info
        self.logger.info(f"Game window set: {window_info}")
        
        # Calculate basic scaling
        if window_info:
            width = window_info.get('Width', 1920)
            height = window_info.get('Height', 1080)
            # Basic scale estimate - adjust this based on testing
            self.grid_to_screen_scale = min(width / 1000, height / 1000)
            self.screen_offset = (width // 2, height // 2)
            self.logger.info(f"Calculated scale: {self.grid_to_screen_scale}, offset: {self.screen_offset}")
    
    def convert_grid_to_screen(self, grid_x: int, grid_y: int) -> Tuple[int, int]:
        """Convert grid coordinates to screen coordinates"""
        try:
            if not self.game_window:
                # Default fallback
                screen_x = grid_x + 500  # Rough offset
                screen_y = grid_y + 300
                return (screen_x, screen_y)
            
            # Get window center
            window_width = self.game_window.get('Width', 1920)
            window_height = self.game_window.get('Height', 1080)
            center_x = window_width // 2
            center_y = window_height // 2
            
            # Convert grid to screen relative to center
            # This is a rough approximation - may need tweaking
            screen_x = center_x + (grid_x - 500) * 2  # Assuming 500 is roughly center
            screen_y = center_y + (grid_y - 300) * 2  # Assuming 300 is roughly center
            
            # Ensure coordinates are within window bounds
            screen_x = max(50, min(screen_x, window_width - 50))
            screen_y = max(50, min(screen_y, window_height - 50))
            
            return (screen_x, screen_y)
            
        except Exception as e:
            self.logger.error(f"Error converting grid coordinates ({grid_x}, {grid_y}): {e}")
            # Return safe fallback
            return (960, 540)  # Screen center
    
    def get_entity_click_position(self, entity: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Get safe click position for an entity using grid coordinates"""
        try:
            # Try grid position first (this seems to work)
            grid_pos = entity.get('GridPosition', {})
            if grid_pos:
                grid_x = grid_pos.get('X', 0)
                grid_y = grid_pos.get('Y', 0)
                
                self.logger.debug(f"Entity grid position: ({grid_x}, {grid_y})")
                
                # Convert to screen coordinates
                screen_x, screen_y = self.convert_grid_to_screen(grid_x, grid_y)
                
                # Validate
                if self.is_valid_screen_position(screen_x, screen_y):
                    return (screen_x, screen_y)
                else:
                    self.logger.warning(f"Invalid converted screen position: ({screen_x}, {screen_y})")
                    return None
            
            # If no grid position, try screen position but validate heavily
            screen_pos = entity.get('location_on_screen', {})
            if screen_pos:
                x = screen_pos.get('X', 0)
                y = screen_pos.get('Y', 0)
                
                # Only use if coordinates are reasonable
                if self.is_valid_screen_position(x, y):
                    return (x, y)
                else:
                    self.logger.warning(f"Invalid entity screen position: ({x}, {y})")
                    return None
            
            self.logger.warning("No valid position data found in entity")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting entity click position: {e}")
            return None
    
    def get_movement_position(self, world_x: int, world_y: int) -> Optional[Tuple[int, int]]:
        """Get movement position using grid coordinates instead of broken API"""
        try:
            # Use grid coordinates directly as they seem reasonable
            screen_x, screen_y = self.convert_grid_to_screen(world_x, world_y)
            
            if self.is_valid_screen_position(screen_x, screen_y):
                return (screen_x, screen_y)
            else:
                self.logger.warning(f"Invalid movement position: ({screen_x}, {screen_y})")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting movement position: {e}")
            return None
    
    def is_valid_screen_position(self, x: int, y: int) -> bool:
        """Check if screen position is valid"""
        # Basic bounds check
        if x < 10 or y < 10:
            return False
        
        if not self.game_window:
            # Default screen bounds
            return x <= 1920 and y <= 1080
        
        # Window bounds
        width = self.game_window.get('Width', 1920)
        height = self.game_window.get('Height', 1080)
        
        return x <= width - 10 and y <= height - 10
    
    def get_safe_click_near_player(self, player_pos: Dict[str, Any]) -> Tuple[int, int]:
        """Get a safe click position near the player"""
        try:
            player_x = player_pos.get('X', 500)
            player_y = player_pos.get('Y', 300)
            
            # Convert player position to screen
            screen_x, screen_y = self.convert_grid_to_screen(player_x, player_y)
            
            # Add small offset for movement
            screen_x += 50
            screen_y += 30
            
            # Ensure it's valid
            if self.is_valid_screen_position(screen_x, screen_y):
                return (screen_x, screen_y)
            else:
                # Return screen center as fallback
                if self.game_window:
                    center_x = self.game_window.get('Width', 1920) // 2
                    center_y = self.game_window.get('Height', 1080) // 2
                    return (center_x, center_y)
                else:
                    return (960, 540)
                    
        except Exception as e:
            self.logger.error(f"Error getting safe click position: {e}")
            return (960, 540)
    
    def debug_coordinate_conversion(self, world_pos: Dict[str, Any]):
        """Debug coordinate conversion"""
        self.logger.info("=== Coordinate Conversion Debug ===")
        world_x = world_pos.get('X', 0)
        world_y = world_pos.get('Y', 0)
        
        self.logger.info(f"World position: ({world_x}, {world_y})")
        
        # Test grid conversion
        screen_pos = self.convert_grid_to_screen(world_x, world_y)
        self.logger.info(f"Grid->Screen conversion: {screen_pos}")
        
        # Test validation
        valid = self.is_valid_screen_position(*screen_pos)
        self.logger.info(f"Position valid: {valid}")
        
        self.logger.info("=== End Debug ===")

# Global instance
_coordinate_fix = None

def get_coordinate_fix() -> CoordinateFix:
    """Get the global coordinate fix instance"""
    global _coordinate_fix
    if _coordinate_fix is None:
        _coordinate_fix = CoordinateFix()
    return _coordinate_fix 