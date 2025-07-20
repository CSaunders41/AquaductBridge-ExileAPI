using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ExileCore;
using SharpDX;
using Vector2 = System.Numerics.Vector2;
using Vector3 = System.Numerics.Vector3;

namespace RadarMovement.Utils
{
    public struct Vector2i : IEquatable<Vector2i>
    {
        public int X { get; }
        public int Y { get; }
        
        public Vector2i(int x, int y)
        {
            X = x;
            Y = y;
        }
        
        public static Vector2i operator +(Vector2i a, Vector2i b) => new Vector2i(a.X + b.X, a.Y + b.Y);
        public static Vector2i operator -(Vector2i a, Vector2i b) => new Vector2i(a.X - b.X, a.Y - b.Y);
        public static bool operator ==(Vector2i a, Vector2i b) => a.X == b.X && a.Y == b.Y;
        public static bool operator !=(Vector2i a, Vector2i b) => !(a == b);
        
        public bool Equals(Vector2i other) => this == other;
        public override bool Equals(object obj) => obj is Vector2i other && Equals(other);
        public override int GetHashCode() => HashCode.Combine(X, Y);
        public override string ToString() => $"({X}, {Y})";
    }

    public enum TerrainType : byte
    {
        Blocked = 0,      // Water, walls, impassable
        Normal = 1,       // Normal walkable terrain
        Bridge = 2,       // Bridge tiles (special pathable over water)
        Waypoint = 3,     // Important navigation waypoints
        Exit = 4,         // Area exits and transitions
        Hazard = 5        // Dangerous but passable (for future use)
    }

    public class AqueductWaypoint
    {
        public Vector3 WorldPosition { get; set; }
        public Vector2i GridPosition { get; set; }
        public string Name { get; set; }
        public TerrainType Type { get; set; }
        public List<AqueductWaypoint> ConnectedWaypoints { get; set; } = new List<AqueductWaypoint>();
        public float Priority { get; set; } = 1.0f; // Higher priority = preferred route
        
        public AqueductWaypoint(Vector3 worldPos, string name, TerrainType type = TerrainType.Waypoint)
        {
            WorldPosition = worldPos;
            GridPosition = WorldToGrid(worldPos);
            Name = name;
            Type = type;
        }
    }

    public class PathfindingResult
    {
        public List<Vector3> WorldPath { get; set; } = new List<Vector3>();
        public List<Vector2i> GridPath { get; set; } = new List<Vector2i>();
        public List<AqueductWaypoint> WaypointPath { get; set; } = new List<AqueductWaypoint>();
        public float TotalCost { get; set; }
        public TimeSpan CalculationTime { get; set; }
        public bool Success { get; set; }
        public string FailureReason { get; set; } = "";
    }

    /// <summary>
    /// Advanced pathfinding system specifically designed for Path of Exile's Aqueduct area.
    /// Handles water channels, bridges, multi-level navigation, and waypoint-based routing.
    /// </summary>
    public class AqueductPathfinder
    {
        // Core pathfinding data
        private TerrainType[][] terrainGrid;
        private readonly GameController gameController;
        private readonly LineOfSight lineOfSight;
        
        // Grid dimensions and constants
        private int gridWidth = 0;
        private int gridHeight = 0;
        private const int TILE_SIZE = 23; // POE's tile size
        private const float DIAGONAL_COST = 1.414f;
        private const float STRAIGHT_COST = 1.0f;
        private const float BRIDGE_COST = 1.2f;        // Slightly prefer non-bridge routes
        private const float WAYPOINT_BONUS = 0.8f;     // Prefer routes through waypoints
        private const float EXIT_BONUS = 0.5f;         // Heavily prefer routes to exits

        // Caching for performance
        private readonly ConcurrentDictionary<Vector2i, byte[][]> directionFieldCache = new();
        private readonly Dictionary<string, AqueductWaypoint> namedWaypoints = new();
        private readonly List<AqueductWaypoint> allWaypoints = new();
        
        // Movement directions (8-directional)
        private static readonly Vector2i[] NeighborOffsets = {
            new Vector2i(0, 1),   // North
            new Vector2i(1, 1),   // Northeast  
            new Vector2i(1, 0),   // East
            new Vector2i(1, -1),  // Southeast
            new Vector2i(0, -1),  // South
            new Vector2i(-1, -1), // Southwest
            new Vector2i(-1, 0),  // West
            new Vector2i(-1, 1),  // Northwest
        };

        public AqueductPathfinder(GameController gameController, LineOfSight lineOfSight)
        {
            this.gameController = gameController;
            this.lineOfSight = lineOfSight;
            InitializeAqueductWaypoints();
        }

        private void InitializeAqueductWaypoints()
        {
            // Pre-defined waypoints for Aqueduct navigation
            // These represent key navigation points like bridge entrances, corridors, exits
            // Coordinates are approximate - will be refined based on actual terrain detection

            try
            {
                // Main bridge system waypoints
                AddWaypoint(new Vector3(100, 200, 0), "NorthBridgeEntrance", TerrainType.Bridge);
                AddWaypoint(new Vector3(150, 200, 0), "NorthBridgeCenter", TerrainType.Bridge);
                AddWaypoint(new Vector3(200, 200, 0), "NorthBridgeExit", TerrainType.Bridge);
                
                AddWaypoint(new Vector3(100, 100, 0), "SouthBridgeEntrance", TerrainType.Bridge);
                AddWaypoint(new Vector3(150, 100, 0), "SouthBridgeCenter", TerrainType.Bridge);
                AddWaypoint(new Vector3(200, 100, 0), "SouthBridgeExit", TerrainType.Bridge);
                
                // Corridor waypoints
                AddWaypoint(new Vector3(50, 150, 0), "WestCorridor", TerrainType.Waypoint);
                AddWaypoint(new Vector3(250, 150, 0), "EastCorridor", TerrainType.Waypoint);
                
                // Area exits (high priority destinations)
                AddWaypoint(new Vector3(0, 150, 0), "WestExit", TerrainType.Exit);
                AddWaypoint(new Vector3(300, 150, 0), "EastExit", TerrainType.Exit);
                
                // Connect waypoints to create preferred routes
                ConnectWaypoints("WestCorridor", "NorthBridgeEntrance");
                ConnectWaypoints("WestCorridor", "SouthBridgeEntrance");
                ConnectWaypoints("NorthBridgeEntrance", "NorthBridgeCenter");
                ConnectWaypoints("NorthBridgeCenter", "NorthBridgeExit");
                ConnectWaypoints("SouthBridgeEntrance", "SouthBridgeCenter");
                ConnectWaypoints("SouthBridgeCenter", "SouthBridgeExit");
                ConnectWaypoints("NorthBridgeExit", "EastCorridor");
                ConnectWaypoints("SouthBridgeExit", "EastCorridor");
                ConnectWaypoints("EastCorridor", "EastExit");
                ConnectWaypoints("WestCorridor", "WestExit");
            }
            catch (Exception ex)
            {
                // Log error but don't fail initialization
                Console.WriteLine($"Error initializing waypoints: {ex.Message}");
            }
        }

        private void AddWaypoint(Vector3 worldPos, string name, TerrainType type)
        {
            var waypoint = new AqueductWaypoint(worldPos, name, type);
            namedWaypoints[name] = waypoint;
            allWaypoints.Add(waypoint);
        }

        private void ConnectWaypoints(string from, string to)
        {
            if (namedWaypoints.TryGetValue(from, out var fromWaypoint) &&
                namedWaypoints.TryGetValue(to, out var toWaypoint))
            {
                fromWaypoint.ConnectedWaypoints.Add(toWaypoint);
                toWaypoint.ConnectedWaypoints.Add(fromWaypoint);
            }
        }

        public bool InitializeTerrain()
        {
            try
            {
                // Get terrain data from LineOfSight system
                var terrainData = lineOfSight.GetTerrainData();
                if (terrainData == null)
                {
                    return false;
                }

                gridHeight = terrainData.GetLength(0);
                gridWidth = terrainData.GetLength(1);
                
                // Initialize terrain grid
                terrainGrid = new TerrainType[gridHeight][];
                for (int y = 0; y < gridHeight; y++)
                {
                    terrainGrid[y] = new TerrainType[gridWidth];
                    for (int x = 0; x < gridWidth; x++)
                    {
                        terrainGrid[y][x] = ClassifyTerrain(terrainData[y, x], x, y);
                    }
                }

                // Update waypoint positions based on actual terrain
                RefineWaypointPositions();
                
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing terrain: {ex.Message}");
                return false;
            }
        }

        private TerrainType ClassifyTerrain(byte terrainValue, int x, int y)
        {
            // Classify terrain based on LineOfSight data
            // This is area-specific logic for the Aqueduct
            
            if (terrainValue == 0 || terrainValue > 200) // Blocked areas (water, walls)
                return TerrainType.Blocked;
                
            // Check if this might be a bridge (pathable terrain over water areas)
            if (IsPotentialBridge(x, y, terrainValue))
                return TerrainType.Bridge;
                
            // Check for area exits (near map boundaries with specific terrain values)
            if (IsAreaExit(x, y, terrainValue))
                return TerrainType.Exit;
                
            // Normal walkable terrain
            if (terrainValue >= 1 && terrainValue <= 100)
                return TerrainType.Normal;
                
            return TerrainType.Blocked;
        }

        private bool IsPotentialBridge(int x, int y, byte terrainValue)
        {
            // Heuristic: bridges are often pathable terrain surrounded by water/blocked areas
            // and tend to form linear patterns across water channels
            
            if (terrainValue < 10 || terrainValue > 50) return false;
            
            int blockedNeighbors = 0;
            int totalNeighbors = 0;
            
            for (int dy = -1; dy <= 1; dy++)
            {
                for (int dx = -1; dx <= 1; dx++)
                {
                    if (dx == 0 && dy == 0) continue;
                    
                    int nx = x + dx, ny = y + dy;
                    if (nx >= 0 && nx < gridWidth && ny >= 0 && ny < gridHeight)
                    {
                        if (terrainGrid?[ny]?[nx] == TerrainType.Blocked)
                            blockedNeighbors++;
                        totalNeighbors++;
                    }
                }
            }
            
            // Bridge if surrounded by significant water/blocked areas
            return totalNeighbors > 0 && (float)blockedNeighbors / totalNeighbors > 0.4f;
        }

        private bool IsAreaExit(int x, int y, byte terrainValue)
        {
            // Area exits are typically near map boundaries
            const int BOUNDARY_THRESHOLD = 10;
            
            return (x < BOUNDARY_THRESHOLD || x > gridWidth - BOUNDARY_THRESHOLD ||
                    y < BOUNDARY_THRESHOLD || y > gridHeight - BOUNDARY_THRESHOLD) &&
                   terrainValue >= 1 && terrainValue <= 50;
        }

        private void RefineWaypointPositions()
        {
            // Adjust waypoint positions to match actual terrain
            foreach (var waypoint in allWaypoints)
            {
                var gridPos = waypoint.GridPosition;
                
                // Find the nearest suitable terrain for this waypoint type
                var refinedPos = FindNearestSuitableTerrain(gridPos, waypoint.Type, 5);
                if (refinedPos.HasValue)
                {
                    waypoint.GridPosition = refinedPos.Value;
                    waypoint.WorldPosition = GridToWorld(refinedPos.Value);
                }
            }
        }

        private Vector2i? FindNearestSuitableTerrain(Vector2i center, TerrainType desiredType, int searchRadius)
        {
            for (int radius = 0; radius <= searchRadius; radius++)
            {
                for (int dx = -radius; dx <= radius; dx++)
                {
                    for (int dy = -radius; dy <= radius; dy++)
                    {
                        if (Math.Abs(dx) != radius && Math.Abs(dy) != radius) continue;
                        
                        var pos = new Vector2i(center.X + dx, center.Y + dy);
                        if (IsValidGridPosition(pos) && 
                            (terrainGrid[pos.Y][pos.X] == desiredType || 
                             (desiredType == TerrainType.Bridge && terrainGrid[pos.Y][pos.X] != TerrainType.Blocked)))
                        {
                            return pos;
                        }
                    }
                }
            }
            return null;
        }

        public async Task<PathfindingResult> FindPathAsync(Vector3 start, Vector3 target, CancellationToken cancellationToken = default)
        {
            return await Task.Run(() => FindPath(start, target), cancellationToken);
        }

        public PathfindingResult FindPath(Vector3 start, Vector3 target)
        {
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            var result = new PathfindingResult();

            try
            {
                if (terrainGrid == null && !InitializeTerrain())
                {
                    result.FailureReason = "Failed to initialize terrain data";
                    return result;
                }

                var startGrid = WorldToGrid(start);
                var targetGrid = WorldToGrid(target);

                // Validate positions
                if (!IsValidGridPosition(startGrid) || !IsValidGridPosition(targetGrid))
                {
                    result.FailureReason = "Start or target position is outside valid area";
                    return result;
                }

                if (!IsTerrainPathable(startGrid) || !IsTerrainPathable(targetGrid))
                {
                    result.FailureReason = "Start or target position is not pathable";
                    return result;
                }

                // Try waypoint-based pathfinding first for long distances
                if (Vector3.Distance(start, target) > 100f) // Long distance threshold
                {
                    var waypointPath = FindWaypointPath(start, target);
                    if (waypointPath.Success)
                    {
                        result = waypointPath;
                        result.CalculationTime = stopwatch.Elapsed;
                        return result;
                    }
                }

                // Fall back to direct A* pathfinding
                var gridPath = FindPathAStar(startGrid, targetGrid);
                if (gridPath != null && gridPath.Count > 0)
                {
                    result.GridPath = gridPath;
                    result.WorldPath = gridPath.Select(GridToWorld).ToList();
                    result.Success = true;
                    result.TotalCost = CalculatePathCost(gridPath);
                }
                else
                {
                    result.FailureReason = "No path found using A* algorithm";
                }
            }
            catch (Exception ex)
            {
                result.FailureReason = $"Pathfinding error: {ex.Message}";
            }

            result.CalculationTime = stopwatch.Elapsed;
            stopwatch.Stop();
            return result;
        }

        private PathfindingResult FindWaypointPath(Vector3 start, Vector3 target)
        {
            var result = new PathfindingResult();
            
            try
            {
                // Find nearest waypoints to start and target
                var startWaypoint = FindNearestWaypoint(start);
                var targetWaypoint = FindNearestWaypoint(target);
                
                if (startWaypoint == null || targetWaypoint == null)
                {
                    result.FailureReason = "Could not find suitable waypoints";
                    return result;
                }

                // Use A* on waypoint graph
                var waypointPath = FindWaypointPathAStar(startWaypoint, targetWaypoint);
                if (waypointPath == null || waypointPath.Count == 0)
                {
                    result.FailureReason = "No waypoint path found";
                    return result;
                }

                // Build complete path: start -> first waypoint -> ... -> last waypoint -> target
                var completePath = new List<Vector3>();
                
                // Path from start to first waypoint
                var firstPath = FindPathAStar(WorldToGrid(start), waypointPath[0].GridPosition);
                if (firstPath != null)
                    completePath.AddRange(firstPath.Select(GridToWorld));
                
                // Path through waypoints
                for (int i = 0; i < waypointPath.Count - 1; i++)
                {
                    var segmentPath = FindPathAStar(waypointPath[i].GridPosition, waypointPath[i + 1].GridPosition);
                    if (segmentPath != null)
                        completePath.AddRange(segmentPath.Skip(1).Select(GridToWorld)); // Skip first to avoid duplicates
                }
                
                // Path from last waypoint to target
                var lastPath = FindPathAStar(waypointPath.Last().GridPosition, WorldToGrid(target));
                if (lastPath != null)
                    completePath.AddRange(lastPath.Skip(1).Select(GridToWorld));

                if (completePath.Count > 0)
                {
                    result.WorldPath = completePath;
                    result.WaypointPath = waypointPath;
                    result.Success = true;
                    result.TotalCost = CalculateWorldPathCost(completePath);
                }
                else
                {
                    result.FailureReason = "Failed to build complete waypoint path";
                }
            }
            catch (Exception ex)
            {
                result.FailureReason = $"Waypoint pathfinding error: {ex.Message}";
            }

            return result;
        }

        private List<Vector2i> FindPathAStar(Vector2i start, Vector2i target)
        {
            if (start == target)
                return new List<Vector2i> { target };

            var openSet = new BinaryHeap<float, Vector2i>();
            var closedSet = new HashSet<Vector2i>();
            var gScore = new Dictionary<Vector2i, float>();
            var fScore = new Dictionary<Vector2i, float>();
            var cameFrom = new Dictionary<Vector2i, Vector2i>();

            gScore[start] = 0;
            fScore[start] = Heuristic(start, target);
            openSet.Add(fScore[start], start);

            while (openSet.TryRemoveTop(out var currentNode))
            {
                var current = currentNode.Value;

                if (current == target)
                {
                    return ReconstructPath(cameFrom, current);
                }

                closedSet.Add(current);

                foreach (var offset in NeighborOffsets)
                {
                    var neighbor = current + offset;
                    
                    if (!IsValidGridPosition(neighbor) || 
                        !IsTerrainPathable(neighbor) || 
                        closedSet.Contains(neighbor))
                        continue;

                    var movementCost = GetMovementCost(current, neighbor);
                    var tentativeGScore = gScore[current] + movementCost;

                    if (!gScore.ContainsKey(neighbor) || tentativeGScore < gScore[neighbor])
                    {
                        cameFrom[neighbor] = current;
                        gScore[neighbor] = tentativeGScore;
                        fScore[neighbor] = tentativeGScore + Heuristic(neighbor, target);
                        
                        openSet.Add(fScore[neighbor], neighbor);
                    }
                }
            }

            return null; // No path found
        }

        private List<AqueductWaypoint> FindWaypointPathAStar(AqueductWaypoint start, AqueductWaypoint target)
        {
            if (start == target)
                return new List<AqueductWaypoint> { target };

            var openSet = new BinaryHeap<float, AqueductWaypoint>();
            var closedSet = new HashSet<AqueductWaypoint>();
            var gScore = new Dictionary<AqueductWaypoint, float>();
            var fScore = new Dictionary<AqueductWaypoint, float>();
            var cameFrom = new Dictionary<AqueductWaypoint, AqueductWaypoint>();

            gScore[start] = 0;
            fScore[start] = Vector3.Distance(start.WorldPosition, target.WorldPosition);
            openSet.Add(fScore[start], start);

            while (openSet.TryRemoveTop(out var currentNode))
            {
                var current = currentNode.Value;

                if (current == target)
                {
                    return ReconstructWaypointPath(cameFrom, current);
                }

                closedSet.Add(current);

                foreach (var neighbor in current.ConnectedWaypoints)
                {
                    if (closedSet.Contains(neighbor))
                        continue;

                    var distance = Vector3.Distance(current.WorldPosition, neighbor.WorldPosition);
                    var cost = distance * neighbor.Priority; // Apply priority weighting
                    var tentativeGScore = gScore[current] + cost;

                    if (!gScore.ContainsKey(neighbor) || tentativeGScore < gScore[neighbor])
                    {
                        cameFrom[neighbor] = current;
                        gScore[neighbor] = tentativeGScore;
                        fScore[neighbor] = tentativeGScore + Vector3.Distance(neighbor.WorldPosition, target.WorldPosition);
                        
                        openSet.Add(fScore[neighbor], neighbor);
                    }
                }
            }

            return null;
        }

        private AqueductWaypoint FindNearestWaypoint(Vector3 position)
        {
            if (allWaypoints.Count == 0) return null;
            
            return allWaypoints
                .Where(w => IsTerrainPathable(w.GridPosition))
                .OrderBy(w => Vector3.Distance(position, w.WorldPosition))
                .FirstOrDefault();
        }

        private List<Vector2i> ReconstructPath(Dictionary<Vector2i, Vector2i> cameFrom, Vector2i current)
        {
            var path = new List<Vector2i>();
            
            while (cameFrom.ContainsKey(current))
            {
                path.Add(current);
                current = cameFrom[current];
            }
            
            path.Reverse();
            return path;
        }

        private List<AqueductWaypoint> ReconstructWaypointPath(Dictionary<AqueductWaypoint, AqueductWaypoint> cameFrom, AqueductWaypoint current)
        {
            var path = new List<AqueductWaypoint>();
            
            while (cameFrom.ContainsKey(current))
            {
                path.Add(current);
                current = cameFrom[current];
            }
            
            path.Reverse();
            return path;
        }

        private bool IsValidGridPosition(Vector2i pos)
        {
            return pos.X >= 0 && pos.X < gridWidth && pos.Y >= 0 && pos.Y < gridHeight;
        }

        private bool IsTerrainPathable(Vector2i pos)
        {
            if (!IsValidGridPosition(pos) || terrainGrid == null)
                return false;
                
            var terrain = terrainGrid[pos.Y][pos.X];
            return terrain != TerrainType.Blocked;
        }

        private float GetMovementCost(Vector2i from, Vector2i to)
        {
            var dx = Math.Abs(to.X - from.X);
            var dy = Math.Abs(to.Y - from.Y);
            
            float baseCost = (dx == 1 && dy == 1) ? DIAGONAL_COST : STRAIGHT_COST;
            
            // Apply terrain-specific costs
            var toTerrain = terrainGrid[to.Y][to.X];
            switch (toTerrain)
            {
                case TerrainType.Bridge:
                    return baseCost * BRIDGE_COST;
                case TerrainType.Waypoint:
                    return baseCost * WAYPOINT_BONUS;
                case TerrainType.Exit:
                    return baseCost * EXIT_BONUS;
                default:
                    return baseCost;
            }
        }

        private float CalculatePathCost(List<Vector2i> path)
        {
            float totalCost = 0;
            for (int i = 1; i < path.Count; i++)
            {
                totalCost += GetMovementCost(path[i - 1], path[i]);
            }
            return totalCost;
        }

        private float CalculateWorldPathCost(List<Vector3> path)
        {
            float totalCost = 0;
            for (int i = 1; i < path.Count; i++)
            {
                totalCost += Vector3.Distance(path[i - 1], path[i]);
            }
            return totalCost;
        }

        private static float Heuristic(Vector2i a, Vector2i b)
        {
            // Manhattan distance with diagonal movement consideration
            var dx = Math.Abs(a.X - b.X);
            var dy = Math.Abs(a.Y - b.Y);
            return Math.Max(dx, dy) + (DIAGONAL_COST - 1) * Math.Min(dx, dy);
        }

        public static Vector2i WorldToGrid(Vector3 worldPos)
        {
            return new Vector2i((int)(worldPos.X / TILE_SIZE), (int)(worldPos.Y / TILE_SIZE));
        }

        public static Vector3 GridToWorld(Vector2i gridPos)
        {
            return new Vector3(gridPos.X * TILE_SIZE, gridPos.Y * TILE_SIZE, 0);
        }

        public void ClearCache()
        {
            directionFieldCache.Clear();
        }

        public List<AqueductWaypoint> GetWaypoints() => allWaypoints.ToList();
        public Dictionary<string, AqueductWaypoint> GetNamedWaypoints() => namedWaypoints.ToDictionary(kv => kv.Key, kv => kv.Value);
    }
} 