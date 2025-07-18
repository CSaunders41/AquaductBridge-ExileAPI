"""
Debug Overlay System for Aqueduct Automation
Shows current task, target information, and debug data on screen
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class DebugLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

@dataclass
class DebugMessage:
    """A single debug message to display"""
    text: str
    level: DebugLevel
    timestamp: float
    duration: float = 5.0  # How long to show message (seconds)
    
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.duration

class DebugOverlay:
    """On-screen debug overlay system"""
    
    def __init__(self, api_client):
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.messages: List[DebugMessage] = []
        self.current_task = "Initializing..."
        self.target_info = {}
        self.path_info = {}
        self.last_update = 0
        
    def set_current_task(self, task: str):
        """Set the current task being performed"""
        self.current_task = task
        self.add_message(f"TASK: {task}", DebugLevel.INFO)
        self.logger.info(f"🎯 Current Task: {task}")
        
    def set_target_info(self, target_type: str, position: Dict[str, int], distance: float):
        """Set information about the current target"""
        self.target_info = {
            'type': target_type,
            'position': position,
            'distance': distance
        }
        self.add_message(f"TARGET: {target_type} at ({position.get('x', 0)}, {position.get('y', 0)}) - {distance:.1f} units", DebugLevel.INFO)
        self.logger.info(f"🎯 Target: {target_type} at distance {distance:.1f}")
        
    def set_path_info(self, waypoints: int, current_waypoint: int, waypoint_pos: Dict[str, int]):
        """Set information about the current path"""
        self.path_info = {
            'total_waypoints': waypoints,
            'current_waypoint': current_waypoint,
            'current_position': waypoint_pos
        }
        self.add_message(f"PATH: Waypoint {current_waypoint}/{waypoints} → ({waypoint_pos.get('x', 0)}, {waypoint_pos.get('y', 0)})", DebugLevel.INFO)
        self.logger.info(f"🗺️  Path: {current_waypoint}/{waypoints} waypoints")
        
    def report_pathfinding_method(self, method: str, success: bool):
        """Report which pathfinding method was used"""
        level = DebugLevel.SUCCESS if success else DebugLevel.WARNING
        self.add_message(f"PATHFINDING: {method} - {'SUCCESS' if success else 'FAILED'}", level)
        self.logger.info(f"🧭 Pathfinding: {method} - {'✅' if success else '❌'}")
        
    def report_movement_result(self, success: bool, distance: float, reason: str = ""):
        """Report movement attempt result"""
        if success:
            self.add_message(f"MOVEMENT: SUCCESS - Reached target", DebugLevel.SUCCESS)
            self.logger.info(f"✅ Movement: SUCCESS")
        else:
            self.add_message(f"MOVEMENT: FAILED - {reason} (distance: {distance:.1f})", DebugLevel.ERROR)
            self.logger.warning(f"❌ Movement: FAILED - {reason} (distance: {distance:.1f})")
    
    def report_obstacle_detected(self, obstacle_type: str, position: Dict[str, int]):
        """Report obstacle detection"""
        self.add_message(f"OBSTACLE: {obstacle_type} at ({position.get('x', 0)}, {position.get('y', 0)})", DebugLevel.WARNING)
        self.logger.warning(f"🚧 Obstacle: {obstacle_type}")
        
    def report_zone_exit_found(self, exit_type: str, position: Dict[str, int], count: int):
        """Report zone exit detection"""
        self.add_message(f"EXIT FOUND: {count} {exit_type}(s) detected", DebugLevel.SUCCESS)
        self.logger.info(f"🚪 Found {count} {exit_type}(s)")
        
    def add_message(self, text: str, level: DebugLevel, duration: float = 5.0):
        """Add a debug message to display"""
        message = DebugMessage(text, level, time.time(), duration)
        self.messages.append(message)
        
        # Keep only recent messages
        self.messages = self.messages[-10:]  # Keep last 10 messages
        
    def update_display(self):
        """Update the on-screen display"""
        try:
            # Remove expired messages
            self.messages = [msg for msg in self.messages if not msg.is_expired()]
            
            # Create display text
            display_lines = []
            
            # Current task (always shown)
            display_lines.append(f"🎯 TASK: {self.current_task}")
            
            # Target info
            if self.target_info:
                target = self.target_info
                display_lines.append(f"🎯 TARGET: {target['type']} at ({target['position'].get('x', 0)}, {target['position'].get('y', 0)}) - {target['distance']:.1f} units")
            
            # Path info
            if self.path_info:
                path = self.path_info
                display_lines.append(f"🗺️  PATH: Waypoint {path['current_waypoint']}/{path['total_waypoints']} → ({path['current_position'].get('x', 0)}, {path['current_position'].get('y', 0)})")
            
            # Recent messages
            for msg in self.messages[-5:]:  # Show last 5 messages
                icon = self._get_level_icon(msg.level)
                display_lines.append(f"{icon} {msg.text}")
            
            # Send to log (since we don't have on-screen display yet)
            if time.time() - self.last_update > 2.0:  # Update every 2 seconds
                self.logger.info("=" * 50)
                self.logger.info("🖥️  DEBUG OVERLAY")
                for line in display_lines:
                    self.logger.info(line)
                self.logger.info("=" * 50)
                self.last_update = time.time()
                
        except Exception as e:
            self.logger.error(f"Error updating debug display: {e}")
            
    def _get_level_icon(self, level: DebugLevel) -> str:
        """Get icon for debug level"""
        icons = {
            DebugLevel.INFO: "ℹ️",
            DebugLevel.WARNING: "⚠️",
            DebugLevel.ERROR: "❌",
            DebugLevel.SUCCESS: "✅"
        }
        return icons.get(level, "📝")
    
    def clear_messages(self):
        """Clear all debug messages"""
        self.messages.clear()
        
    def get_current_status(self) -> Dict[str, Any]:
        """Get current debug status"""
        return {
            'current_task': self.current_task,
            'target_info': self.target_info,
            'path_info': self.path_info,
            'message_count': len(self.messages)
        }

# Global debug overlay instance
_debug_overlay = None

def get_debug_overlay(api_client=None) -> DebugOverlay:
    """Get the global debug overlay instance"""
    global _debug_overlay
    if _debug_overlay is None and api_client:
        _debug_overlay = DebugOverlay(api_client)
    return _debug_overlay

def set_current_task(task: str):
    """Convenience function to set current task"""
    if _debug_overlay:
        _debug_overlay.set_current_task(task)

def set_target_info(target_type: str, position: Dict[str, int], distance: float):
    """Convenience function to set target info"""
    if _debug_overlay:
        _debug_overlay.set_target_info(target_type, position, distance)

def set_path_info(waypoints: int, current_waypoint: int, waypoint_pos: Dict[str, int]):
    """Convenience function to set path info"""
    if _debug_overlay:
        _debug_overlay.set_path_info(waypoints, current_waypoint, waypoint_pos)

def report_pathfinding_method(method: str, success: bool):
    """Convenience function to report pathfinding method"""
    if _debug_overlay:
        _debug_overlay.report_pathfinding_method(method, success)

def report_movement_result(success: bool, distance: float, reason: str = ""):
    """Convenience function to report movement result"""
    if _debug_overlay:
        _debug_overlay.report_movement_result(success, distance, reason)

def report_obstacle_detected(obstacle_type: str, position: Dict[str, int]):
    """Convenience function to report obstacle detection"""
    if _debug_overlay:
        _debug_overlay.report_obstacle_detected(obstacle_type, position)

def report_zone_exit_found(exit_type: str, position: Dict[str, int], count: int):
    """Convenience function to report zone exit detection"""
    if _debug_overlay:
        _debug_overlay.report_zone_exit_found(exit_type, position, count) 