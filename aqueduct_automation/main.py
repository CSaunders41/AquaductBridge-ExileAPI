#!/usr/bin/env python3
"""
Aqueduct Automation - Main Script
Advanced Path of Exile Aqueduct farming automation system
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .api_client import AqueductAPIClient
from .pathfinding import PathfindingEngine
from .intelligent_pathfinding import IntelligentPathfinder
from .combat import CombatSystem
from .loot_manager import LootManager
from .resource_manager import ResourceManager
from .config import AutomationConfig
from .utils import setup_logging, calculate_distance, safe_sleep

@dataclass
class FarmingStats:
    """Track farming statistics"""
    runs_completed: int = 0
    monsters_killed: int = 0
    items_collected: int = 0
    start_time: float = 0
    total_runtime: float = 0
    
    def get_efficiency_stats(self) -> Dict[str, float]:
        """Calculate efficiency metrics"""
        if self.total_runtime == 0:
            return {}
        
        return {
            'runs_per_hour': self.runs_completed / (self.total_runtime / 3600),
            'monsters_per_hour': self.monsters_killed / (self.total_runtime / 3600),
            'items_per_hour': self.items_collected / (self.total_runtime / 3600),
            'avg_run_time': self.total_runtime / max(1, self.runs_completed)
        }

class AqueductAutomation:
    """Main automation controller for Aqueduct farming"""
    
    def __init__(self, config: AutomationConfig, debug_mode: bool = False, safe_mode: bool = False):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.debug_mode = debug_mode
        self.safe_mode = safe_mode
        
        # Initialize components
        self.api_client = AqueductAPIClient(config.api_host, config.api_port)
        self.pathfinder = PathfindingEngine()
        self.intelligent_pathfinder = IntelligentPathfinder()
        self.combat_system = CombatSystem(config.combat_config)
        self.loot_manager = LootManager(config.loot_config)
        self.resource_manager = ResourceManager(config.resource_config)
        
        # Initialize coordinate helper
        from coordinate_helper import get_coordinate_helper
        self.coordinate_helper = get_coordinate_helper()
        
        # Initialize coordinate fix (bypasses broken API)
        from coordinate_fix import get_coordinate_fix
        self.coordinate_fix = get_coordinate_fix()
        
        # Stats tracking
        self.stats = FarmingStats()
        self.current_state = "initializing"
        self.running = False
        
        # Debug/safe mode settings
        if debug_mode:
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("Debug mode enabled")
        
        if safe_mode:
            self.logger.info("Safe mode enabled - no actual clicks will be performed")
            
        # Coordinate validation stats
        self.invalid_coordinates_count = 0
        self.coordinate_warnings = []
        
    def start_automation(self):
        """Start the main automation loop"""
        self.logger.info("Starting Aqueduct Automation System")
        self.running = True
        self.stats.start_time = time.time()
        
        # Clear any existing path visualization
        self.api_client.clear_path_visualization()
        
        try:
            while self.running:
                self.run_aqueduct_cycle()
                self.stats.runs_completed += 1
                
                # Check if we should stop
                if self.should_stop():
                    break
                    
                # Rest between runs
                safe_sleep(self.config.run_delay)
                
        except KeyboardInterrupt:
            self.logger.info("Automation stopped by user")
        except Exception as e:
            self.logger.error(f"Automation error: {e}")
            raise
        finally:
            self.cleanup()
    
    def run_aqueduct_cycle(self):
        """Execute one complete Aqueduct farming cycle"""
        self.logger.info(f"Starting Aqueduct run #{self.stats.runs_completed + 1}")
        
        try:
            # 1. Verify we're in the right state
            if not self.verify_game_state():
                self.handle_invalid_state()
                return
            
            # 2. Enter Aqueduct (if not already there)
            if not self.enter_aqueduct():
                self.logger.error("Failed to enter Aqueduct")
                return
            
            # 3. Navigate and farm the area
            self.farm_aqueduct()
            
            # 4. Return to hideout
            self.return_to_hideout()
            
            # 5. Manage inventory/stash
            self.manage_inventory()
            
        except Exception as e:
            self.logger.error(f"Error in Aqueduct cycle: {e}")
            self.handle_error_recovery()
    
    def verify_game_state(self) -> bool:
        """Verify game is in correct state for automation"""
        try:
            game_info = self.api_client.get_game_info()
            
            if not game_info.get('in_game', False):
                self.logger.warning("Not in game")
                return False
                
            if not game_info.get('window_focused', False):
                self.logger.warning("Game window not focused")
                # Could auto-focus here if needed
            
            # Set up coordinate helper with window info
            try:
                full_data = self.api_client.get_full_game_data()
                if full_data and 'WindowArea' in full_data:
                    self.coordinate_helper.set_game_window(full_data['WindowArea'])
                    self.coordinate_fix.set_game_window(full_data['WindowArea'])
            except Exception as e:
                self.logger.warning(f"Could not get window info: {e}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to verify game state: {e}")
            return False
    
    def enter_aqueduct(self) -> bool:
        """Enter Aqueduct area"""
        try:
            area_info = self.api_client.get_area_data()
            current_area = area_info.get('area_name', '').lower()
            
            if 'aqueduct' in current_area:
                self.logger.info("Already in Aqueduct")
                return True
            
            # If in hideout, look for waypoint
            if 'hideout' in current_area:
                return self.use_waypoint_to_aqueduct()
            
            # If in town, navigate to waypoint
            if 'town' in current_area:
                return self.navigate_to_waypoint()
                
            self.logger.warning(f"Unknown area: {current_area}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to enter Aqueduct: {e}")
            return False
    
    def farm_aqueduct(self):
        """Main farming logic for Aqueduct"""
        self.logger.info("Starting Aqueduct farming")
        
        try:
            # Get initial position and terrain
            game_data = self.api_client.get_full_game_data()
            
            # Debug coordinate information if in debug mode
            if self.debug_mode:
                self._debug_entity_coordinates(game_data)
            
            # Create intelligent navigation path through Aqueduct
            path = self.intelligent_pathfinder.create_intelligent_path(
                game_data['player_pos'],
                game_data['terrain_string'],
                game_data['awake_entities']
            )
            
            self.logger.info(f"Created intelligent path with {len(path)} waypoints")
            
            # Send path data to plugin for visualization
            if len(path) > 0:
                target = path[-1] if path else None  # Last waypoint is the target
                self.api_client.send_path_data(path, target)
            
            # Follow the path, fighting and looting
            successful_moves = 0
            for i, waypoint in enumerate(path):
                self.logger.info(f"Moving to waypoint {i+1}/{len(path)}: {waypoint}")
                
                # Move to waypoint
                movement_successful = self.move_to_position(waypoint)
                
                if movement_successful:
                    successful_moves += 1
                    
                    # Check for and handle combat
                    if self.combat_system.scan_for_enemies():
                        killed = self.combat_system.engage_combat()
                        self.stats.monsters_killed += killed
                    
                    # Check for loot
                    loot_collected = self.loot_manager.collect_nearby_loot()
                    self.stats.items_collected += loot_collected
                    
                    # Monitor resources
                    self.resource_manager.check_and_use_flasks()
                    
                    # Check if inventory is full
                    if self.loot_manager.is_inventory_full():
                        self.logger.info("Inventory full, returning to stash")
                        break
                        
                    # Safety check - if health too low, retreat
                    if self.resource_manager.should_retreat():
                        self.logger.warning("Health critical, retreating")
                        break
                else:
                    self.logger.warning(f"Failed to move to waypoint {i+1}, continuing to next")
                    
            self.logger.info(f"Completed path traversal: {successful_moves}/{len(path)} waypoints reached")
                    
        except Exception as e:
            self.logger.error(f"Error during farming: {e}")
            raise
    
    def _debug_entity_coordinates(self, game_data: Dict[str, Any]):
        """Debug entity coordinate information"""
        entities = game_data.get('awake_entities', [])
        self.logger.debug(f"Debugging {len(entities)} entities")
        
        for i, entity in enumerate(entities[:3]):  # Only debug first 3
            self.logger.debug(f"Entity {i+1}: {entity.get('Path', 'Unknown')}")
            self.coordinate_helper.debug_coordinates(entity)
    
    def move_to_position(self, target_pos: Dict[str, int]):
        """Move player to target position"""
        try:
            # Get current position
            current_pos = self.api_client.get_player_position()
            
            if self.debug_mode:
                self.logger.info(f"=== Movement Debug ===")
                self.logger.info(f"Current position: {current_pos}")
                self.logger.info(f"Target position: {target_pos}")
            
            # Use coordinate fix instead of broken API
            screen_coords = self.coordinate_fix.get_movement_position(
                target_pos['x'], target_pos['y']
            )
            
            if not screen_coords:
                self.logger.warning(f"Could not get valid screen coordinates for target {target_pos}")
                # Try safe click near player as fallback
                screen_coords = self.coordinate_fix.get_safe_click_near_player(current_pos)
                self.logger.info(f"Using safe click position: {screen_coords}")
                
                if not screen_coords:
                    self.logger.error("Failed to get any valid screen coordinates")
                    return False
            
            # Debug coordinate information
            self.logger.info(f"Moving to world pos {target_pos} -> screen pos {screen_coords}")
            
            # In safe mode, don't actually click
            if self.safe_mode:
                self.logger.info(f"SAFE MODE: Would click at {screen_coords}")
                return True  # Assume success in safe mode
            
            # Click to move
            success = self.api_client.click_position(screen_coords[0], screen_coords[1])
            if not success:
                self.logger.warning(f"Failed to click at {screen_coords}")
                return False
            
            # Wait for movement
            movement_successful = self.wait_for_movement(current_pos, target_pos)
            return movement_successful
            
        except Exception as e:
            self.logger.error(f"Failed to move to position: {e}")
            return False
    
    def wait_for_movement(self, start_pos: Dict, target_pos: Dict, timeout: float = 5.0):
        """Wait for player to reach target position"""
        start_time = time.time()
        last_pos = start_pos
        
        self.logger.debug(f"Waiting for movement from {start_pos} to {target_pos}")
        
        while time.time() - start_time < timeout:
            current_pos = self.api_client.get_player_position()
            distance_to_target = calculate_distance(current_pos, target_pos)
            distance_from_start = calculate_distance(current_pos, start_pos)
            
            self.logger.debug(f"Current pos: {current_pos}, Distance to target: {distance_to_target:.2f}, Distance from start: {distance_from_start:.2f}")
            
            if distance_to_target < 35:  # More forgiving tolerance for Aqueduct
                self.logger.debug("Reached target position")
                break
                
            # Check if stuck (haven't moved from start position)
            if distance_from_start < 8:
                if time.time() - start_time > 2.0:  # Been stuck for 2 seconds
                    self.logger.warning("Player appears stuck, trying alternate route")
                    break
            else:
                # Player is moving, extend timeout slightly
                if distance_from_start > 8:
                    self.logger.debug("Player is moving...")
                    
            time.sleep(0.1)
        
        # Log final result
        final_pos = self.api_client.get_player_position()
        final_distance = calculate_distance(final_pos, target_pos)
        elapsed = time.time() - start_time
        
        if final_distance < 35:
            self.logger.info(f"Successfully reached target in {elapsed:.2f}s")
            return True
        else:
            self.logger.warning(f"Did not reach target after {elapsed:.2f}s. Final distance: {final_distance:.2f}")
            return False
    
    def return_to_hideout(self):
        """Return to hideout via portal or waypoint"""
        try:
            # Try to use portal scroll
            if self.use_portal_scroll():
                return True
                
            # Try to find waypoint
            if self.use_waypoint_to_hideout():
                return True
                
            self.logger.error("Failed to return to hideout")
            return False
            
        except Exception as e:
            self.logger.error(f"Error returning to hideout: {e}")
            return False
    
    def manage_inventory(self):
        """Manage inventory and stash items"""
        try:
            if self.loot_manager.has_valuable_items():
                self.loot_manager.stash_items()
                
        except Exception as e:
            self.logger.error(f"Error managing inventory: {e}")
    
    def use_waypoint_to_aqueduct(self) -> bool:
        """Use waypoint to travel to Aqueduct"""
        try:
            # Find waypoint entity
            entities = self.api_client.get_entities()
            waypoint = next((e for e in entities if 'waypoint' in e.get('Path', '').lower()), None)
            
            if not waypoint:
                self.logger.error("No waypoint found")
                return False
                
            # Use coordinate fix to get safe click position
            screen_coords = self.coordinate_fix.get_entity_click_position(waypoint)
            if not screen_coords:
                self.logger.warning("Could not get valid screen coordinates for waypoint")
                return False
                
            # Click waypoint
            self.api_client.click_position(screen_coords[0], screen_coords[1])
            
            # Wait for waypoint UI and select Aqueduct
            time.sleep(2)
            # TODO: Implement waypoint UI interaction
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to use waypoint: {e}")
            return False
    
    def use_waypoint_to_hideout(self) -> bool:
        """Use waypoint to travel to hideout"""
        try:
            # Find waypoint entity
            entities = self.api_client.get_entities()
            waypoint = next((e for e in entities if 'waypoint' in e.get('Path', '').lower()), None)
            
            if not waypoint:
                self.logger.error("No waypoint found")
                return False
                
            # Use coordinate fix to get safe click position
            screen_coords = self.coordinate_fix.get_entity_click_position(waypoint)
            if not screen_coords:
                self.logger.warning("Could not get valid screen coordinates for waypoint")
                return False
                
            # Click waypoint
            self.api_client.click_position(screen_coords[0], screen_coords[1])
            
            # Wait for waypoint UI and select hideout
            time.sleep(2)
            # TODO: Implement waypoint UI interaction for hideout
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to use waypoint to hideout: {e}")
            return False
    
    def navigate_to_waypoint(self) -> bool:
        """Navigate to waypoint in town"""
        try:
            # For now, assume waypoint is accessible
            # In a real implementation, this would navigate through town
            self.logger.info("Navigating to waypoint in town")
            return self.use_waypoint_to_aqueduct()
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to waypoint: {e}")
            return False
    
    def use_portal_scroll(self) -> bool:
        """Use portal scroll to return to hideout"""
        try:
            # TODO: Implement portal scroll usage
            # This would involve:
            # 1. Finding portal scroll in inventory
            # 2. Right-clicking it
            # 3. Clicking the ground
            # 4. Entering the portal
            
            return False  # Not implemented yet
            
        except Exception as e:
            self.logger.error(f"Failed to use portal scroll: {e}")
            return False
    
    def should_stop(self) -> bool:
        """Check if automation should stop"""
        # Check max runs
        if self.config.max_runs > 0 and self.stats.runs_completed >= self.config.max_runs:
            self.logger.info(f"Reached max runs ({self.config.max_runs})")
            return True
            
        # Check max runtime
        current_runtime = time.time() - self.stats.start_time
        if self.config.max_runtime > 0 and current_runtime >= self.config.max_runtime:
            self.logger.info(f"Reached max runtime ({self.config.max_runtime}s)")
            return True
            
        return False
    
    def handle_invalid_state(self):
        """Handle when game is in invalid state"""
        self.logger.warning("Game in invalid state, attempting recovery")
        time.sleep(5)  # Wait and try again
    
    def handle_error_recovery(self):
        """Handle error recovery"""
        self.logger.info("Attempting error recovery")
        time.sleep(10)  # Wait before trying again
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.stats.total_runtime = time.time() - self.stats.start_time
        
        # Clear path visualization
        self.api_client.clear_path_visualization()
        
        # Log final stats
        efficiency = self.stats.get_efficiency_stats()
        self.logger.info("=== Automation Complete ===")
        self.logger.info(f"Total runs: {self.stats.runs_completed}")
        self.logger.info(f"Monsters killed: {self.stats.monsters_killed}")
        self.logger.info(f"Items collected: {self.stats.items_collected}")
        self.logger.info(f"Total runtime: {self.stats.total_runtime:.2f}s")
        
        if efficiency:
            self.logger.info(f"Runs per hour: {efficiency['runs_per_hour']:.2f}")
            self.logger.info(f"Average run time: {efficiency['avg_run_time']:.2f}s")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Aqueduct Automation System')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--safe-mode', action='store_true', help='Enable safe mode (no actual clicks)')
    parser.add_argument('--log-level', default='INFO', help='Set log level (DEBUG, INFO, WARNING, ERROR)')
    parser.add_argument('--max-runs', type=int, default=0, help='Maximum number of runs (0 = unlimited)')
    parser.add_argument('--disable-failsafe', action='store_true', help='Disable PyAutoGUI failsafe (NOT RECOMMENDED)')
    
    args = parser.parse_args()
    
    setup_logging(log_level=args.log_level)
    
    try:
        # Handle PyAutoGUI failsafe
        if args.disable_failsafe:
            logging.warning("⚠️  DISABLING PYAUTOGUI FAILSAFE - THIS IS NOT RECOMMENDED")
            try:
                import pyautogui
                pyautogui.FAILSAFE = False
            except ImportError:
                pass
        
        config = AutomationConfig()
        
        # Override config with command line args
        if args.max_runs > 0:
            config.max_runs = args.max_runs
        
        automation = AqueductAutomation(config, debug_mode=args.debug, safe_mode=args.safe_mode)
        automation.start_automation()
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main() 