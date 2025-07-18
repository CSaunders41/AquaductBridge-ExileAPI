"""
Pathfinding Engine for Aqueduct Navigation
Handles terrain parsing and A* pathfinding through the Aqueduct
"""

import logging
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from heapq import heappush, heappop
import re

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
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def manhattan_distance_to(self, other: 'Position') -> int:
        """Calculate Manhattan distance to another position"""
        return abs(self.x - other.x) + abs(self.y - other.y)

@dataclass
class PathNode:
    """Node for A* pathfinding algorithm"""
    position: Position
    g_cost: float = 0.0  # Cost from start
    h_cost: float = 0.0  # Heuristic cost to end
    parent: Optional['PathNode'] = None
    
    @property
    def f_cost(self) -> float:
        """Total cost (g + h)"""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost

class TerrainGrid:
    """Represents the game terrain as a navigable grid"""
    
    def __init__(self, terrain_string: str):
        self.logger = logging.getLogger(__name__)
        self.grid = self._parse_terrain_string(terrain_string)
        self.width = len(self.grid[0]) if self.grid else 0
        self.height = len(self.grid)
        
    def _parse_terrain_string(self, terrain_string: str) -> List[List[int]]:
        """Parse terrain string into 2D grid"""
        try:
            if not terrain_string:
                # Return empty grid if no terrain data
                return []
            
            lines = terrain_string.strip().split('\n')
            grid = []
            
            for line in lines:
                # Split by spaces and convert to integers
                values = [int(x) for x in line.split()]
                grid.append(values)
            
            self.logger.debug(f"Parsed terrain grid: {len(grid)}x{len(grid[0]) if grid else 0}")
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
            return terrain_value == 51
            
        except Exception:
            return False
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within grid bounds"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_neighbors(self, pos: Position) -> List[Position]:
        """Get walkable neighbors of a position"""
        neighbors = []
        
        # 8-directional movement (including diagonals)
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
    
    def get_movement_cost(self, from_pos: Position, to_pos: Position) -> float:
        """Calculate movement cost between two positions"""
        # Diagonal movement costs more
        dx = abs(to_pos.x - from_pos.x)
        dy = abs(to_pos.y - from_pos.y)
        
        if dx == 1 and dy == 1:
            return 1.414  # Diagonal movement (sqrt(2))
        else:
            return 1.0    # Straight movement

class PathfindingEngine:
    """Main pathfinding engine for Aqueduct navigation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_terrain: Optional[TerrainGrid] = None
        
    def create_aqueduct_path(self, start_pos: Dict[str, int], terrain_string: str) -> List[Dict[str, int]]:
        """Create a path through the Aqueduct from start to end"""
        try:
            self.logger.info(f"Creating Aqueduct path from {start_pos}")
            
            # Parse terrain data
            self.current_terrain = TerrainGrid(terrain_string)
            
            if not self.current_terrain.grid:
                self.logger.warning("No terrain data available, using fallback path")
                fallback_path = self._create_fallback_path(start_pos)
                self.logger.info(f"Created fallback path with {len(fallback_path)} waypoints")
                return fallback_path
            
            # Convert start position
            start = Position(start_pos['X'], start_pos['Y'])
            
            # Try the complex pathfinding first
            path = self._create_linear_aqueduct_path(start)
            
            # If we got a valid path with multiple waypoints, use it
            if len(path) > 1:
                result_path = [{'x': pos.x, 'y': pos.y} for pos in path]
                self.logger.info(f"Created linear path with {len(result_path)} waypoints")
                return result_path
            
            # If complex pathfinding failed, use simple method
            self.logger.warning("Complex pathfinding failed, using simple path")
            simple_path = self._create_simple_aqueduct_path(start_pos)
            self.logger.info(f"Created simple path with {len(simple_path)} waypoints")
            return simple_path
            
        except Exception as e:
            self.logger.error(f"Failed to create Aqueduct path: {e}")
            import traceback
            traceback.print_exc()
            fallback_path = self._create_fallback_path(start_pos)
            self.logger.info(f"Using fallback path with {len(fallback_path)} waypoints")
            return fallback_path
    
    def _create_linear_aqueduct_path(self, start: Position) -> List[Position]:
        """Create a linear path through the Aqueduct"""
        path = []
        
        # Aqueduct is typically a linear area going from one end to the other
        # We'll create waypoints that cover the main path
        
        # Start from current position
        current = start
        path.append(current)
        
        # Create waypoints moving forward through the area
        # This is a simplified version - in practice, you'd want to:
        # 1. Identify the main path through the Aqueduct
        # 2. Create waypoints along that path
        # 3. Use A* to navigate between waypoints if needed
        
        # For now, create a simple forward path
        terrain = self.current_terrain
        
        # Try to move in the general direction of the Aqueduct
        # Aqueduct typically runs horizontally or vertically
        target_direction = self._detect_aqueduct_direction(start)
        self.logger.debug(f"Detected Aqueduct direction: {target_direction}")
        
        waypoints = self._generate_waypoints_along_direction(start, target_direction, 20)
        self.logger.debug(f"Generated {len(waypoints)} waypoints")
        
        # Use A* pathfinding between waypoints
        for i, waypoint in enumerate(waypoints):
            self.logger.debug(f"Processing waypoint {i+1}: {waypoint}")
            segment_path = self.find_path(current, waypoint)
            if segment_path:
                self.logger.debug(f"Found segment path with {len(segment_path)} positions")
                path.extend(segment_path[1:])  # Skip first position (current)
                current = waypoint
            else:
                self.logger.debug(f"No segment path found to waypoint {waypoint}")
        
        self.logger.debug(f"Final path has {len(path)} positions")
        return path
    
    def _detect_aqueduct_direction(self, start: Position) -> Tuple[int, int]:
        """Detect the main direction of the Aqueduct"""
        # Simplified detection - in practice, you'd analyze the terrain
        # to find the main corridor direction
        
        # For now, assume Aqueduct runs horizontally (most common)
        return (1, 0)  # Move right
    
    def _generate_waypoints_along_direction(self, start: Position, direction: Tuple[int, int], spacing: int) -> List[Position]:
        """Generate waypoints along a direction"""
        waypoints = []
        current = start
        
        for i in range(1, 10):  # Create up to 9 waypoints
            next_pos = Position(
                current.x + direction[0] * spacing * i,
                current.y + direction[1] * spacing * i
            )
            
            # Check if position is valid and walkable
            if self.current_terrain and self.current_terrain.is_valid_position(next_pos.x, next_pos.y):
                waypoints.append(next_pos)
                self.logger.debug(f"Added waypoint {i}: {next_pos}")
            else:
                self.logger.debug(f"Waypoint {i} at {next_pos} is not valid, stopping")
                break  # Reached the end of the area
        
        return waypoints
    
    def find_path(self, start: Position, end: Position) -> List[Position]:
        """Find path between two positions using A* algorithm"""
        try:
            if not self.current_terrain:
                return []
            
            # Check if start and end are walkable
            if not self.current_terrain.is_walkable(start.x, start.y):
                self.logger.warning(f"Start position {start} is not walkable")
                return []
            
            if not self.current_terrain.is_walkable(end.x, end.y):
                self.logger.warning(f"End position {end} is not walkable")
                return []
            
            # A* pathfinding
            open_set = []
            closed_set: Set[Position] = set()
            
            start_node = PathNode(start, 0, start.distance_to(end))
            heappush(open_set, start_node)
            
            nodes_map = {start: start_node}
            
            while open_set:
                current_node = heappop(open_set)
                current_pos = current_node.position
                
                if current_pos == end:
                    # Path found, reconstruct it
                    return self._reconstruct_path(current_node)
                
                closed_set.add(current_pos)
                
                # Check all neighbors
                for neighbor_pos in self.current_terrain.get_neighbors(current_pos):
                    if neighbor_pos in closed_set:
                        continue
                    
                    # Calculate costs
                    movement_cost = self.current_terrain.get_movement_cost(current_pos, neighbor_pos)
                    tentative_g_cost = current_node.g_cost + movement_cost
                    
                    neighbor_node = nodes_map.get(neighbor_pos)
                    
                    if neighbor_node is None:
                        # New node
                        neighbor_node = PathNode(
                            neighbor_pos,
                            tentative_g_cost,
                            neighbor_pos.distance_to(end),
                            current_node
                        )
                        nodes_map[neighbor_pos] = neighbor_node
                        heappush(open_set, neighbor_node)
                    elif tentative_g_cost < neighbor_node.g_cost:
                        # Better path found
                        neighbor_node.g_cost = tentative_g_cost
                        neighbor_node.parent = current_node
            
            # No path found
            self.logger.warning(f"No path found from {start} to {end}")
            return []
            
        except Exception as e:
            self.logger.error(f"Error in pathfinding: {e}")
            return []
    
    def _reconstruct_path(self, end_node: PathNode) -> List[Position]:
        """Reconstruct path from end node to start"""
        path = []
        current = end_node
        
        while current:
            path.append(current.position)
            current = current.parent
        
        path.reverse()
        return path
    
    def _create_fallback_path(self, start_pos: Dict[str, int]) -> List[Dict[str, int]]:
        """Create a fallback path when terrain data is not available"""
        self.logger.info("Creating fallback path for Aqueduct")
        
        # Create a simple linear path moving forward
        path = []
        current_x = start_pos['X']
        current_y = start_pos['Y']
        
        # Create waypoints moving in a typical Aqueduct direction
        for i in range(10):
            path.append({
                'x': current_x + i * 20,
                'y': current_y
            })
        
        return path
    
    def find_nearest_walkable_position(self, target: Position, search_radius: int = 5) -> Optional[Position]:
        """Find the nearest walkable position to a target"""
        if not self.current_terrain:
            return None
        
        if self.current_terrain.is_walkable(target.x, target.y):
            return target
        
        # Search in expanding squares
        for radius in range(1, search_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Only check perimeter
                        check_pos = Position(target.x + dx, target.y + dy)
                        if self.current_terrain.is_walkable(check_pos.x, check_pos.y):
                            return check_pos
        
        return None
    
    def smooth_path(self, path: List[Position]) -> List[Position]:
        """Smooth a path by removing unnecessary waypoints"""
        if len(path) <= 2:
            return path
        
        smoothed = [path[0]]
        
        i = 0
        while i < len(path) - 1:
            # Try to find the furthest point we can reach directly
            furthest = i + 1
            
            for j in range(i + 2, len(path)):
                if self._has_clear_line_of_sight(path[i], path[j]):
                    furthest = j
                else:
                    break
            
            smoothed.append(path[furthest])
            i = furthest
        
        return smoothed
    
    def _has_clear_line_of_sight(self, start: Position, end: Position) -> bool:
        """Check if there's a clear line of sight between two positions"""
        if not self.current_terrain:
            return False
        
        # Use Bresenham's line algorithm to check all points along the line
        dx = abs(end.x - start.x)
        dy = abs(end.y - start.y)
        
        x_step = 1 if start.x < end.x else -1
        y_step = 1 if start.y < end.y else -1
        
        error = dx - dy
        x, y = start.x, start.y
        
        while True:
            if not self.current_terrain.is_walkable(x, y):
                return False
            
            if x == end.x and y == end.y:
                break
            
            double_error = 2 * error
            
            if double_error > -dy:
                error -= dy
                x += x_step
            
            if double_error < dx:
                error += dx
                y += y_step
        
        return True
    
    def get_path_length(self, path: List[Position]) -> float:
        """Calculate total path length"""
        if len(path) <= 1:
            return 0.0
        
        total_length = 0.0
        for i in range(len(path) - 1):
            total_length += path[i].distance_to(path[i + 1])
        
        return total_length 

    def _create_simple_aqueduct_path(self, start_pos: Dict[str, int]) -> List[Dict[str, int]]:
        """Create a simple path through the Aqueduct (guaranteed to work)"""
        path = []
        current_x = start_pos['X']
        current_y = start_pos['Y']
        
        self.logger.info(f"Creating simple Aqueduct path from ({current_x}, {current_y})")
        
        # Create a comprehensive path that covers the typical Aqueduct route
        # The Aqueduct is usually a linear area, so we'll create waypoints
        # that move through the main path
        
        waypoints = [
            # Start position
            {'x': current_x, 'y': current_y},
            
            # Move right (typical Aqueduct direction)
            {'x': current_x + 15, 'y': current_y},
            {'x': current_x + 30, 'y': current_y},
            {'x': current_x + 45, 'y': current_y},
            
            # Move slightly up/down to explore branches
            {'x': current_x + 60, 'y': current_y - 10},
            {'x': current_x + 75, 'y': current_y - 10},
            {'x': current_x + 90, 'y': current_y},
            
            # Move further right
            {'x': current_x + 105, 'y': current_y},
            {'x': current_x + 120, 'y': current_y},
            {'x': current_x + 135, 'y': current_y},
            
            # Explore other branch
            {'x': current_x + 150, 'y': current_y + 10},
            {'x': current_x + 165, 'y': current_y + 10},
            {'x': current_x + 180, 'y': current_y},
            
            # Continue to the end
            {'x': current_x + 195, 'y': current_y},
            {'x': current_x + 210, 'y': current_y},
        ]
        
        # Filter out the start position since we don't need to move there
        waypoints = waypoints[1:]  # Remove first waypoint (current position)
        
        self.logger.info(f"Created {len(waypoints)} waypoints for simple path")
        
        return waypoints 