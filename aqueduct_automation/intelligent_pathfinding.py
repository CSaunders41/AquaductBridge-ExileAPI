#!/usr/bin/env python3
"""
Intelligent Pathfinding System
Uses real terrain data and zone analysis to find optimal paths to zone exits
"""

import logging
import math
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import deque
import heapq

@dataclass
class Position:
    """Represents a position in the game world"""
    x: int
    y: int
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def manhattan_distance_to(self, other: 'Position') -> int:
        """Calculate Manhattan distance to another position"""
        return abs(self.x - other.x) + abs(self.y - other.y)

@dataclass
class PathNode:
    """Node for A* pathfinding"""
    position: Position
    g_cost: float  # Cost from start
    h_cost: float  # Heuristic cost to goal
    parent: Optional['PathNode'] = None
    
    @property
    def f_cost(self) -> float:
        """Total cost (f = g + h)"""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost

class ZoneAnalyzer:
    """Analyzes zone layout to find exits, waypoints, and optimal routes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def find_zone_exits(self, entities: List[Dict[str, Any]]) -> List[Position]:
        """Find all possible zone exits from entity data"""
        exits = []
        
        for entity in entities:
            try:
                # Look for entities that might be zone exits
                path = entity.get('Path', '').lower()
                entity_type = entity.get('EntityType', 0)
                
                # Common exit/door/waypoint patterns
                if any(keyword in path for keyword in [
                    'door', 'exit', 'waypoint', 'portal', 'transition',
                    'areatransition', 'zoneexit', 'staircase', 'ladder'
                ]):
                    grid_pos = entity.get('GridPosition', {})
                    if grid_pos:
                        exit_pos = Position(grid_pos.get('X', 0), grid_pos.get('Y', 0))
                        exits.append(exit_pos)
                        self.logger.info(f"Found potential exit at {exit_pos}: {path}")
                
                # Also look for specific entity types that might be exits
                if entity_type in [1, 2, 3]:  # Common exit entity types
                    grid_pos = entity.get('GridPosition', {})
                    if grid_pos:
                        exit_pos = Position(grid_pos.get('X', 0), grid_pos.get('Y', 0))
                        exits.append(exit_pos)
                        self.logger.info(f"Found exit by entity type {entity_type} at {exit_pos}")
                        
            except Exception as e:
                self.logger.error(f"Error analyzing entity for exits: {e}")
        
        # Remove duplicates (same position)
        unique_exits = []
        for exit in exits:
            if not any(e.distance_to(exit) < 10 for e in unique_exits):
                unique_exits.append(exit)
        
        self.logger.info(f"Found {len(unique_exits)} unique zone exits")
        return unique_exits
    
    def find_optimal_exit(self, player_pos: Position, exits: List[Position]) -> Optional[Position]:
        """Find the optimal exit to target based on distance and accessibility"""
        if not exits:
            return None
        
        # For now, just return the closest exit
        # In a more advanced system, we'd consider factors like:
        # - Path difficulty
        # - Monster density
        # - Zone progression (which exit leads to next area)
        
        closest_exit = min(exits, key=lambda e: e.distance_to(player_pos))
        self.logger.info(f"Selected optimal exit at {closest_exit} (distance: {closest_exit.distance_to(player_pos):.2f})")
        return closest_exit

class TerrainAnalyzer:
    """Analyzes terrain data for pathfinding"""
    
    def __init__(self, terrain_string: str):
        self.logger = logging.getLogger(__name__)
        self.grid = self._parse_terrain_string(terrain_string)
        self.width = len(self.grid[0]) if self.grid else 0
        self.height = len(self.grid)
        
    def _parse_terrain_string(self, terrain_string: str) -> List[List[int]]:
        """Parse terrain string into 2D grid"""
        try:
            if not terrain_string or len(terrain_string.strip()) == 0:
                self.logger.warning("Empty terrain string, creating fallback grid")
                return []
            
            lines = terrain_string.strip().split('\n')
            grid = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Split by spaces and convert to integers
                values = [int(x) for x in line.split()]
                grid.append(values)
            
            self.logger.info(f"Parsed terrain grid: {len(grid)}x{len(grid[0]) if grid else 0}")
            return grid
            
        except Exception as e:
            self.logger.error(f"Failed to parse terrain string: {e}")
            return []
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if position is walkable"""
        try:
            if not self.is_valid_position(x, y):
                return False
            
            terrain_value = self.grid[y][x]
            # 51 = walkable, 49 = blocked (from aqueduct_runner format)
            return terrain_value >= 50
            
        except Exception:
            return False
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within grid bounds"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_neighbors(self, pos: Position) -> List[Position]:
        """Get walkable neighbors of a position"""
        neighbors = []
        
        # 8-directional movement
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for dx, dy in directions:
            new_x, new_y = pos.x + dx, pos.y + dy
            if self.is_walkable(new_x, new_y):
                neighbors.append(Position(new_x, new_y))
        
        return neighbors

class IntelligentPathfinder:
    """Advanced pathfinding system using real terrain data and zone analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.zone_analyzer = ZoneAnalyzer()
        self.terrain_analyzer: Optional[TerrainAnalyzer] = None
        
    def create_intelligent_path(self, start_pos: Dict[str, int], terrain_string: str, 
                              entities: List[Dict[str, Any]]) -> List[Dict[str, int]]:
        """Create an intelligent path to the zone exit using terrain analysis"""
        try:
            self.logger.info(f"Creating intelligent path from {start_pos}")
            
            # Parse terrain data
            self.terrain_analyzer = TerrainAnalyzer(terrain_string)
            
            # Convert start position
            start = Position(start_pos['X'], start_pos['Y'])
            
            # Find zone exits
            exits = self.zone_analyzer.find_zone_exits(entities)
            
            # Report exit detection
            from debug_overlay import get_debug_overlay
            debug_overlay = get_debug_overlay()
            
            if not exits:
                self.logger.warning("No zone exits found, trying extended search range")
                # Try searching with a larger range by getting all exits without distance filtering
                all_exits = []
                for entity in entities:
                    path = entity.get('Path', '').lower()
                    if any(keyword in path for keyword in ['waypoint', 'teleport', 'portal', 'transition']):
                        grid_pos = entity.get('GridPosition', {})
                        if grid_pos:
                            exit_pos = Position(grid_pos.get('X', 0), grid_pos.get('Y', 0))
                            all_exits.append(exit_pos)
                            self.logger.info(f"Found distant exit at {exit_pos}")
                
                if all_exits:
                    self.logger.info(f"Found {len(all_exits)} exits with extended search")
                    exits = all_exits
                else:
                    self.logger.warning("No zone exits found even with extended search, falling back to exploration pattern")
                    if debug_overlay:
                        debug_overlay.report_zone_exit_found("exit", {}, 0)
                        debug_overlay.report_pathfinding_method("Exploration Pattern", False)
                    return self._create_exploration_path(start_pos)
            
            # Find optimal exit
            target_exit = self.zone_analyzer.find_optimal_exit(start, exits)
            
            if not target_exit:
                self.logger.warning("No optimal exit found, falling back to exploration pattern")
                if debug_overlay:
                    debug_overlay.report_pathfinding_method("Optimal Exit Selection", False)
                return self._create_exploration_path(start_pos)
            
            # Report exit found
            if debug_overlay:
                debug_overlay.report_zone_exit_found("exit", {'x': target_exit.x, 'y': target_exit.y}, len(exits))
            
            # Use A* pathfinding if we have terrain data
            if self.terrain_analyzer.grid:
                self.logger.info(f"Using A* pathfinding to exit at {target_exit}")
                path = self._find_path_astar(start, target_exit)
                
                if path:
                    # Convert to dictionary format
                    result_path = [{'x': pos.x, 'y': pos.y} for pos in path]
                    self.logger.info(f"Created A* path with {len(result_path)} waypoints")
                    if debug_overlay:
                        debug_overlay.report_pathfinding_method("A* Pathfinding", True)
                    return result_path
                else:
                    self.logger.warning("A* pathfinding failed, trying direct path")
                    if debug_overlay:
                        debug_overlay.report_pathfinding_method("A* Pathfinding", False)
                        debug_overlay.report_pathfinding_method("Direct Path", True)
                    return self._create_direct_path(start, target_exit)
            else:
                self.logger.warning("No terrain data available, creating direct path to exit")
                if debug_overlay:
                    debug_overlay.report_pathfinding_method("Direct Path (No Terrain)", True)
                return self._create_direct_path(start, target_exit)
                
        except Exception as e:
            self.logger.error(f"Error creating intelligent path: {e}")
            import traceback
            traceback.print_exc()
            return self._create_exploration_path(start_pos)
    
    def _find_path_astar(self, start: Position, goal: Position) -> Optional[List[Position]]:
        """Find path using A* algorithm"""
        try:
            open_set = []
            closed_set: Set[Position] = set()
            
            start_node = PathNode(start, 0, start.distance_to(goal))
            heapq.heappush(open_set, start_node)
            
            nodes_dict = {start: start_node}
            
            while open_set:
                current_node = heapq.heappop(open_set)
                current_pos = current_node.position
                
                if current_pos.distance_to(goal) < 5:  # Close enough to goal
                    return self._reconstruct_path(current_node)
                
                closed_set.add(current_pos)
                
                # Get neighbors
                neighbors = self.terrain_analyzer.get_neighbors(current_pos)
                
                for neighbor_pos in neighbors:
                    if neighbor_pos in closed_set:
                        continue
                    
                    # Calculate costs
                    g_cost = current_node.g_cost + current_pos.distance_to(neighbor_pos)
                    h_cost = neighbor_pos.distance_to(goal)
                    
                    if neighbor_pos not in nodes_dict:
                        neighbor_node = PathNode(neighbor_pos, g_cost, h_cost, current_node)
                        nodes_dict[neighbor_pos] = neighbor_node
                        heapq.heappush(open_set, neighbor_node)
                    else:
                        existing_node = nodes_dict[neighbor_pos]
                        if g_cost < existing_node.g_cost:
                            existing_node.g_cost = g_cost
                            existing_node.parent = current_node
                            # Re-add to open set with updated cost
                            heapq.heappush(open_set, existing_node)
            
            self.logger.warning("A* pathfinding failed - no path found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in A* pathfinding: {e}")
            return None
    
    def _reconstruct_path(self, end_node: PathNode) -> List[Position]:
        """Reconstruct path from end node to start"""
        path = []
        current = end_node
        
        while current:
            path.append(current.position)
            current = current.parent
        
        path.reverse()
        return path
    
    def _create_direct_path(self, start: Position, goal: Position) -> List[Dict[str, int]]:
        """Create a direct path with waypoints between start and goal"""
        path = []
        
        # Calculate distance and create waypoints
        distance = start.distance_to(goal)
        
        # Create waypoints with larger spacing for better movement
        if distance < 20:
            # For short distances, just go directly
            path.append({'x': goal.x, 'y': goal.y})
        else:
            # For longer distances, create waypoints every 15 units (instead of smaller spacing)
            num_waypoints = max(2, int(distance / 15))
            
            for i in range(1, num_waypoints + 1):
                progress = i / num_waypoints
                waypoint_x = int(start.x + (goal.x - start.x) * progress)
                waypoint_y = int(start.y + (goal.y - start.y) * progress)
                path.append({'x': waypoint_x, 'y': waypoint_y})
        
        self.logger.info(f"Created direct path with {len(path)} waypoints to exit (distance: {distance:.1f})")
        return path
    
    def _create_exploration_path(self, start_pos: Dict[str, int]) -> List[Dict[str, int]]:
        """Create an exploration path when no exits are found"""
        path = []
        current_x = start_pos['X']
        current_y = start_pos['Y']
        
        self.logger.info(f"Creating exploration path from ({current_x}, {current_y})")
        
        # Create a more intelligent exploration pattern
        # This moves in expanding directions to explore the area
        waypoints = [
            # Initial forward movement - larger steps
            {'x': current_x + 60, 'y': current_y},
            {'x': current_x + 120, 'y': current_y},
            {'x': current_x + 180, 'y': current_y},
            
            # Explore up and down branches - larger steps
            {'x': current_x + 180, 'y': current_y + 60},
            {'x': current_x + 120, 'y': current_y + 60},
            {'x': current_x + 60, 'y': current_y + 60},
            
            # Explore down branch
            {'x': current_x + 60, 'y': current_y - 60},
            {'x': current_x + 120, 'y': current_y - 60},
            {'x': current_x + 180, 'y': current_y - 60},
            
            # Extend further out
            {'x': current_x + 240, 'y': current_y},
            {'x': current_x + 300, 'y': current_y},
            {'x': current_x + 360, 'y': current_y},
        ]
        
        self.logger.info(f"Created exploration path with {len(waypoints)} waypoints")
        return waypoints 