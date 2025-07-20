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
        
        # Coordinate inversion flags - THESE FIX THE BACKWARDS MOVEMENT
        self.invert_x = False  # Set to True if moving left when should move right
        self.invert_y = True   # Set to True if moving up when should move down
        self.swap_xy = False   # Set to True if X and Y are swapped
        
        self.logger.info("CoordinateFix initialized with inversion fixes")
        
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
        """Convert grid coordinates to screen coordinates with inversion fixes"""
        try:
            if not self.game_window:
                # Default fallback - use screen center with meaningful offset
                center_x, center_y = 960, 540
                
                # Apply coordinate transformations to fix backwards movement
                raw_offset_x = (grid_x - 500) * 1.5
                raw_offset_y = (grid_y - 300) * 1.5
                
                # Apply inversion fixes
                if self.invert_x:
                    raw_offset_x = -raw_offset_x
                    self.logger.debug(f"Inverting X: {(grid_x - 500) * 1.5} -> {raw_offset_x}")
                    
                if self.invert_y:
                    raw_offset_y = -raw_offset_y
                    self.logger.debug(f"Inverting Y: {(grid_y - 300) * 1.5} -> {raw_offset_y}")
                
                # Swap XY if needed
                if self.swap_xy:
                    raw_offset_x, raw_offset_y = raw_offset_y, raw_offset_x
                    self.logger.debug(f"Swapping XY coordinates")
                
                screen_x = int(center_x + raw_offset_x)
                screen_y = int(center_y + raw_offset_y)
                
                # Ensure within bounds
                screen_x = max(100, min(screen_x, 1820))
                screen_y = max(100, min(screen_y, 980))
                
                self.logger.debug(f"Grid ({grid_x}, {grid_y}) -> Screen ({screen_x}, {screen_y})")
                return (screen_x, screen_y)
            
            # Get window center
            window_width = self.game_window.get('Width', 1920)
            window_height = self.game_window.get('Height', 1080)
            center_x = window_width // 2
            center_y = window_height // 2
            
            # Convert with scaling and apply fixes
            raw_x = grid_x * self.grid_to_screen_scale
            raw_y = grid_y * self.grid_to_screen_scale
            
            # Apply coordinate transformations
            if self.invert_x:
                raw_x = -raw_x
            if self.invert_y:
                raw_y = -raw_y
            if self.swap_xy:
                raw_x, raw_y = raw_y, raw_x
            
            screen_x = int(center_x + raw_x)
            screen_y = int(center_y + raw_y)
            
            # Clamp to screen bounds with margin
            screen_x = max(50, min(screen_x, window_width - 50))
            screen_y = max(50, min(screen_y, window_height - 50))
            
            self.logger.debug(f"Fixed conversion: Grid({grid_x}, {grid_y}) -> Screen({screen_x}, {screen_y})")
            return (screen_x, screen_y)
            
        except Exception as e:
            self.logger.error(f"Error converting coordinates: {e}")
            # Safe fallback to screen center
            return (960, 540)
    
    def set_coordinate_fixes(self, invert_x: bool = False, invert_y: bool = True, swap_xy: bool = False):
        """Set coordinate inversion flags to fix backwards movement"""
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.swap_xy = swap_xy
        self.logger.info(f"Coordinate fixes set: invert_x={invert_x}, invert_y={invert_y}, swap_xy={swap_xy}")
        
    def test_coordinate_conversion(self, player_x: int, player_y: int) -> Dict[str, Any]:
        """Test coordinate conversion with different fix combinations"""
        results = {}
        
        # Test different combinations
        fix_combinations = [
            ("normal", False, False, False),
            ("invert_y", False, True, False),
            ("invert_x", True, False, False),
            ("invert_both", True, True, False),
            ("swap_xy", False, False, True),
            ("swap_invert_y", False, True, True)
        ]
        
        original_x, original_y, original_swap = self.invert_x, self.invert_y, self.swap_xy
        
        for name, inv_x, inv_y, swap in fix_combinations:
            self.invert_x, self.invert_y, self.swap_xy = inv_x, inv_y, swap
            screen_x, screen_y = self.convert_grid_to_screen(player_x, player_y)
            results[name] = (screen_x, screen_y)
        
        # Restore original settings
        self.invert_x, self.invert_y, self.swap_xy = original_x, original_y, original_swap
        
        return results
    
    def get_entity_click_position(self, entity: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Get safe click position for an entity using grid coordinates"""
        try:
            # ALWAYS use grid position first - ignore broken screen coordinates
            grid_pos = entity.get('GridPosition', {})
            if grid_pos:
                grid_x = grid_pos.get('X', 0)
                grid_y = grid_pos.get('Y', 0)
                
                self.logger.debug(f"Entity grid position: ({grid_x}, {grid_y})")
                
                # Convert to screen coordinates using our fixed conversion
                screen_x, screen_y = self.convert_grid_to_screen(grid_x, grid_y)
                
                # Validate
                if self.is_valid_screen_position(screen_x, screen_y):
                    self.logger.debug(f"Converted grid ({grid_x}, {grid_y}) -> screen ({screen_x}, {screen_y})")
                    return (screen_x, screen_y)
                else:
                    self.logger.warning(f"Invalid converted screen position: ({screen_x}, {screen_y})")
                    # Return screen center as fallback
                    return self.get_screen_center()
            
            # If no grid position, DO NOT use screen position - it's broken
            # Instead, return screen center as safe fallback
            self.logger.warning("No grid position found in entity, using screen center")
            return self.get_screen_center()
            
        except Exception as e:
            self.logger.error(f"Error getting entity click position: {e}")
            return self.get_screen_center()
    
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
    
    def get_screen_center(self) -> Tuple[int, int]:
        """Get center of screen/game window"""
        if not self.game_window:
            return (960, 540)
        
        window_width = self.game_window.get('Width', 1920)
        window_height = self.game_window.get('Height', 1080)
        
        center_x = int(window_width // 2)
        center_y = int(window_height // 2)
        
        return (center_x, center_y)
    
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
_coordinate_fix_instance = None

def get_coordinate_fix() -> CoordinateFix:
    """Get the global coordinate fix instance"""
    global _coordinate_fix_instance
    if _coordinate_fix_instance is None:
        _coordinate_fix_instance = CoordinateFix()
    return _coordinate_fix_instance 