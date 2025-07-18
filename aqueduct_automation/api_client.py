"""
API Client for AqueductBridge Plugin
Handles all communication with the Path of Exile ExileApi plugin
"""

import requests
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
import json
from urllib.parse import urlencode

class AqueductAPIClient:
    """Client for communicating with AqueductBridge ExileApi plugin"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 50002):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Set timeout and connection settings
        self.session.timeout = 5.0
        self.session.headers.update({
            'User-Agent': 'AqueductAutomation/1.0',
            'Accept': 'application/json'
        })
    
    def is_connected(self) -> bool:
        """Check if connection to AqueductBridge is active"""
        try:
            response = self.session.get(f"{self.base_url}/gameInfo", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_game_info(self) -> Dict[str, Any]:
        """Get basic game information"""
        try:
            response = self.session.get(f"{self.base_url}/gameInfo")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get game info: {e}")
            return {}
    
    def get_full_game_data(self) -> Dict[str, Any]:
        """Get comprehensive game data for automation"""
        try:
            response = self.session.get(f"{self.base_url}/gameInfo?type=full")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get full game data: {e}")
            return {}
    
    def get_player_data(self) -> Dict[str, Any]:
        """Get player-specific data"""
        try:
            response = self.session.get(f"{self.base_url}/player")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get player data: {e}")
            return {}
    
    def get_area_data(self) -> Dict[str, Any]:
        """Get current area information"""
        try:
            response = self.session.get(f"{self.base_url}/area")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get area data: {e}")
            return {}
    
    def get_player_position(self) -> Dict[str, int]:
        """Get current player position"""
        try:
            full_data = self.get_full_game_data()
            return full_data.get('player_pos', {'X': 0, 'Y': 0, 'Z': 0})
        except Exception as e:
            self.logger.error(f"Failed to get player position: {e}")
            return {'X': 0, 'Y': 0, 'Z': 0}
    
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get all awake entities"""
        try:
            full_data = self.get_full_game_data()
            return full_data.get('awake_entities', [])
        except Exception as e:
            self.logger.error(f"Failed to get entities: {e}")
            return []
    
    def get_terrain_data(self) -> str:
        """Get terrain string for pathfinding"""
        try:
            full_data = self.get_full_game_data()
            return full_data.get('terrain_string', '')
        except Exception as e:
            self.logger.error(f"Failed to get terrain data: {e}")
            return ''
    
    def get_life_data(self) -> Dict[str, Any]:
        """Get player life/mana/ES data"""
        try:
            full_data = self.get_full_game_data()
            return full_data.get('life', {})
        except Exception as e:
            self.logger.error(f"Failed to get life data: {e}")
            return {}
    
    def get_screen_position(self, x: int, y: int) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        try:
            params = {'x': x, 'y': y}
            response = self.session.get(f"{self.base_url}/positionOnScreen", params=params)
            response.raise_for_status()
            coords = response.json()
            if isinstance(coords, list) and len(coords) >= 2:
                screen_x, screen_y = int(coords[0]), int(coords[1])
                
                # Validate screen coordinates
                if self._validate_screen_coordinates(screen_x, screen_y):
                    return (screen_x, screen_y)
                else:
                    self.logger.warning(f"Invalid screen coordinates from API: ({screen_x}, {screen_y}) for world ({x}, {y})")
                    return (0, 0)
            return (0, 0)
        except Exception as e:
            self.logger.error(f"Failed to get screen position: {e}")
            return (0, 0)
    
    def _validate_screen_coordinates(self, x: int, y: int) -> bool:
        """Validate screen coordinates are reasonable"""
        # Check for obviously invalid coordinates
        if x < -100 or x > 5000 or y < -100 or y > 5000:
            return False
        
        # Check for coordinates that would trigger PyAutoGUI fail-safe
        if x < 5 and y < 5:
            return False
        
        return True
    
    def get_window_area(self) -> Dict[str, int]:
        """Get game window area"""
        try:
            full_data = self.get_full_game_data()
            return full_data.get('WindowArea', {'X': 0, 'Y': 0, 'Width': 1920, 'Height': 1080})
        except Exception as e:
            self.logger.error(f"Failed to get window area: {e}")
            return {'X': 0, 'Y': 0, 'Width': 1920, 'Height': 1080}
    
    def is_loading(self) -> bool:
        """Check if area is loading"""
        try:
            full_data = self.get_full_game_data()
            return full_data.get('area_loading', False)
        except Exception as e:
            self.logger.error(f"Failed to check loading status: {e}")
            return False
    
    def get_monsters(self) -> List[Dict[str, Any]]:
        """Get all monster entities"""
        try:
            entities = self.get_entities()
            return [e for e in entities if e.get('EntityType') == 14]
        except Exception as e:
            self.logger.error(f"Failed to get monsters: {e}")
            return []
    
    def get_interactables(self) -> List[Dict[str, Any]]:
        """Get all interactable entities (chests, waypoints, etc.)"""
        try:
            entities = self.get_entities()
            return [e for e in entities if e.get('EntityType') == 1]
        except Exception as e:
            self.logger.error(f"Failed to get interactables: {e}")
            return []
    
    def get_stash_entities(self) -> List[Dict[str, Any]]:
        """Get stash entities"""
        try:
            entities = self.get_interactables()
            return [e for e in entities if 'stash' in e.get('Path', '').lower()]
        except Exception as e:
            self.logger.error(f"Failed to get stash entities: {e}")
            return []
    
    def get_waypoint_entities(self) -> List[Dict[str, Any]]:
        """Get waypoint entities"""
        try:
            entities = self.get_interactables()
            return [e for e in entities if 'waypoint' in e.get('Path', '').lower()]
        except Exception as e:
            self.logger.error(f"Failed to get waypoint entities: {e}")
            return []
    
    def click_position(self, x: int, y: int):
        """Click at screen position"""
        try:
            from input_controller import click_position
            
            # Validate coordinates first
            if not self._validate_screen_coordinates(x, y):
                self.logger.warning(f"Refusing to click at invalid coordinates ({x}, {y})")
                return False
            
            return click_position(x, y)
        except ImportError:
            self.logger.error("Input controller not available")
            return False
    
    def send_key(self, key: str):
        """Send key press to game"""
        try:
            from input_controller import send_key
            return send_key(key)
        except ImportError:
            self.logger.error("Input controller not available")
            return False
    
    def wait_for_area_load(self, timeout: float = 30.0) -> bool:
        """Wait for area to finish loading"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.is_loading():
                return True
            time.sleep(0.5)
        
        self.logger.warning("Area loading timeout")
        return False
    
    def wait_for_movement_complete(self, start_pos: Dict[str, int], timeout: float = 5.0) -> bool:
        """Wait for player movement to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_pos = self.get_player_position()
            
            # Check if player has moved significantly
            distance_moved = self._calculate_distance(start_pos, current_pos)
            if distance_moved > 10:  # Moved at least 10 units
                return True
                
            time.sleep(0.1)
        
        return False
    
    def _calculate_distance(self, pos1: Dict[str, int], pos2: Dict[str, int]) -> float:
        """Calculate distance between two positions"""
        dx = pos1.get('X', 0) - pos2.get('X', 0)
        dy = pos1.get('Y', 0) - pos2.get('Y', 0)
        return (dx * dx + dy * dy) ** 0.5
    
    def get_health_percentage(self) -> float:
        """Get current health percentage"""
        try:
            life_data = self.get_life_data()
            health = life_data.get('Health', {})
            current = health.get('Current', 0)
            total = health.get('Total', 1)
            return (current / total) * 100 if total > 0 else 0
        except Exception as e:
            self.logger.error(f"Failed to get health percentage: {e}")
            return 100  # Assume full health on error
    
    def get_mana_percentage(self) -> float:
        """Get current mana percentage"""
        try:
            life_data = self.get_life_data()
            mana = life_data.get('Mana', {})
            current = mana.get('Current', 0)
            total = mana.get('Total', 1)
            return (current / total) * 100 if total > 0 else 0
        except Exception as e:
            self.logger.error(f"Failed to get mana percentage: {e}")
            return 100  # Assume full mana on error
    
    def get_energy_shield_percentage(self) -> float:
        """Get current energy shield percentage"""
        try:
            life_data = self.get_life_data()
            es = life_data.get('EnergyShield', {})
            current = es.get('Current', 0)
            total = es.get('Total', 1)
            return (current / total) * 100 if total > 0 else 0
        except Exception as e:
            self.logger.error(f"Failed to get energy shield percentage: {e}")
            return 100  # Assume full ES on error
    
    def is_in_area(self, area_name: str) -> bool:
        """Check if player is in specified area"""
        try:
            area_data = self.get_area_data()
            current_area = area_data.get('area_name', '').lower()
            return area_name.lower() in current_area
        except Exception as e:
            self.logger.error(f"Failed to check area: {e}")
            return False
    
    def is_in_game(self) -> bool:
        """Check if player is in game"""
        try:
            game_info = self.get_game_info()
            return game_info.get('in_game', False)
        except Exception as e:
            self.logger.error(f"Failed to check in-game status: {e}")
            return False
    
    def is_window_focused(self) -> bool:
        """Check if game window is focused"""
        try:
            game_info = self.get_game_info()
            return game_info.get('window_focused', False)
        except Exception as e:
            self.logger.error(f"Failed to check window focus: {e}")
            return False
    
    def log_api_stats(self):
        """Log API connection statistics"""
        try:
            if self.is_connected():
                game_info = self.get_game_info()
                self.logger.info(f"API Connected - Player: {game_info.get('player_name', 'Unknown')}")
                self.logger.info(f"Area: {game_info.get('area_name', 'Unknown')}")
                self.logger.info(f"In Game: {game_info.get('in_game', False)}")
            else:
                self.logger.warning("API not connected")
        except Exception as e:
            self.logger.error(f"Failed to log API stats: {e}") 