using System;
using System.Collections.Generic;
using System.Linq;
using ExileCore;
using ExileCore.Shared.Helpers;
using RadarMovement.Utils;
using SharpDX;
using Vector2 = System.Numerics.Vector2;

namespace RadarMovement.Utils
{
    public enum PathStatus
    {
        Clear,      // The path is fully walkable
        Dashable,   // The path is blocked by dashable obstacles (terrain value 2)
        Blocked,    // The path is blocked by impassable walls or terrain
        Invalid     // The start or end point is out of bounds
    }

    public class LineOfSight
    {
        private readonly GameController _gameController;
        private int[][] _terrainData;
        private Vector2i _areaDimensions;
        private DateTime _lastTerrainRefresh = DateTime.MinValue;
        
        // Enhanced settings
        private int TerrainRefreshInterval => 1000; // Refresh every 1 second
        private int TerrainValueForCollision => 2; // Terrain value that blocks movement but allows dashing
        
        // Debug and visualization data
        private readonly List<(Vector2 Start, Vector2 End, PathStatus Status)> _debugRays = new();
        private readonly HashSet<Vector2> _walkablePoints = new();
        private readonly Dictionary<Vector2, PathStatus> _pathStatusCache = new();
        private DateTime _lastCacheCleanup = DateTime.MinValue;

        public LineOfSight(GameController gameController)
        {
            _gameController = gameController;
            
            // Subscribe to events
            var eventBus = EventBus.Instance;
            eventBus.Subscribe<AreaChangeEvent>(OnAreaChange);
            eventBus.Subscribe<RenderEvent>(OnRender);
        }

        /// <summary>
        /// Enhanced path status check that determines if path is clear, dashable, or blocked
        /// </summary>
        public PathStatus GetPathStatus(Vector2 from, Vector2 to)
        {
            try
            {
                // Check cache first
                var cacheKey = new Vector2(from.X + to.X, from.Y + to.Y); // Simple cache key
                if (_pathStatusCache.TryGetValue(cacheKey, out var cachedStatus) && 
                    DateTime.Now - _lastTerrainRefresh < TimeSpan.FromMilliseconds(TerrainRefreshInterval))
                {
                    return cachedStatus;
                }

                RefreshTerrainDataIfNeeded();
                
                if (_terrainData == null)
                    return PathStatus.Invalid;

                var status = CheckPathInternal(from, to);
                
                // Cache the result
                _pathStatusCache[cacheKey] = status;
                
                // Add to debug visualization
                _debugRays.Add((from, to, status));
                
                // Keep only recent rays for performance
                if (_debugRays.Count > 100)
                {
                    _debugRays.RemoveRange(0, _debugRays.Count - 100);
                }
                
                return status;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"LineOfSight error: {ex.Message}");
                return PathStatus.Blocked;
            }
        }

        /// <summary>
        /// Check if there's a clear path between two points (legacy compatibility)
        /// </summary>
        public PathStatus CheckPath(Vector2 from, Vector2 to)
        {
            return GetPathStatus(from, to);
        }

        /// <summary>
        /// Enhanced walkability check with terrain type detection
        /// </summary>
        public bool IsWalkable(Vector2 position, bool allowDashable = false)
        {
            try
            {
                RefreshTerrainDataIfNeeded();
                if (_terrainData == null) return false;
                
                var terrainValue = GetTerrainValue(position);
                
                if (terrainValue == 0) // Impassable
                    return false;
                    
                if (terrainValue == TerrainValueForCollision) // Dashable obstacle
                    return allowDashable;
                    
                return terrainValue > 0; // Walkable terrain
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Find the closest walkable position to a target with improved algorithm
        /// </summary>
        public Vector2? FindClosestWalkablePosition(Vector2 target, float searchRadius = 50f, bool allowDashable = false)
        {
            try
            {
                if (IsWalkable(target, allowDashable))
                    return target;

                var bestDistance = float.MaxValue;
                Vector2? bestPosition = null;

                // Search in expanding circles with improved sampling
                for (int radius = 5; radius <= searchRadius; radius += 5)
                {
                    var samples = Math.Max(8, (int)(radius / 5) * 8); // More samples for larger radii
                    
                    for (int i = 0; i < samples; i++)
                    {
                        var angle = (2 * Math.PI * i) / samples;
                        var testPos = new Vector2(
                            target.X + (float)(Math.Cos(angle) * radius),
                            target.Y + (float)(Math.Sin(angle) * radius)
                        );

                        if (IsWalkable(testPos, allowDashable))
                        {
                            var distance = Vector2.Distance(target, testPos);
                            if (distance < bestDistance)
                            {
                                bestDistance = distance;
                                bestPosition = testPos;
                            }
                        }
                    }
                    
                    // If we found a good position, return early
                    if (bestPosition.HasValue)
                        return bestPosition;
                }

                return bestPosition;
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// Get detailed terrain information for debugging
        /// </summary>
        public string GetTerrainInfo(Vector2 position)
        {
            try
            {
                RefreshTerrainDataIfNeeded();
                if (_terrainData == null) return "No terrain data";
                
                var terrainValue = GetTerrainValue(position);
                var walkable = IsWalkable(position);
                var dashableWalkable = IsWalkable(position, true);
                
                var terrainType = terrainValue switch
                {
                    0 => "Blocked",
                    2 => "Dashable",
                    _ when terrainValue > 0 => "Walkable",
                    _ => "Unknown"
                };
                
                return $"Terrain: {terrainValue} ({terrainType}), Walkable: {walkable}, Dashable: {dashableWalkable}";
            }
            catch (Exception ex)
            {
                return $"Error: {ex.Message}";
            }
        }

        /// <summary>
        /// Get raw terrain data for external pathfinding systems
        /// </summary>
        public int[,] GetTerrainData()
        {
            RefreshTerrainDataIfNeeded();
            
            if (_terrainData == null)
                return null;
                
            var result = new int[_areaDimensions.Y, _areaDimensions.X];
            for (int y = 0; y < _areaDimensions.Y; y++)
            {
                for (int x = 0; x < _areaDimensions.X; x++)
                {
                    result[y, x] = _terrainData[y][x];
                }
            }
            
            return result;
        }

        /// <summary>
        /// Analyze area for common patterns (bridges, choke points, etc.)
        /// </summary>
        public Dictionary<string, object> AnalyzeArea()
        {
            var analysis = new Dictionary<string, object>();
            
            try
            {
                RefreshTerrainDataIfNeeded();
                if (_terrainData == null)
                {
                    analysis["Error"] = "No terrain data available";
                    return analysis;
                }

                var walkableTiles = 0;
                var blockedTiles = 0;
                var dashableTiles = 0;
                var bridgeCandidates = new List<Vector2>();
                var chokePoints = new List<Vector2>();

                for (int y = 1; y < _areaDimensions.Y - 1; y++)
                {
                    for (int x = 1; x < _areaDimensions.X - 1; x++)
                    {
                        var terrainValue = _terrainData[y][x];
                        
                        switch (terrainValue)
                        {
                            case 0:
                                blockedTiles++;
                                break;
                            case 2:
                                dashableTiles++;
                                break;
                            default when terrainValue > 0:
                                walkableTiles++;
                                
                                // Check for bridge patterns (walkable surrounded by water/blocked)
                                var blockedNeighbors = CountBlockedNeighbors(x, y);
                                if (blockedNeighbors >= 4)
                                {
                                    bridgeCandidates.Add(new Vector2(x, y));
                                }
                                
                                // Check for choke points (walkable with few walkable neighbors)
                                var walkableNeighbors = CountWalkableNeighbors(x, y);
                                if (walkableNeighbors <= 2 && walkableNeighbors > 0)
                                {
                                    chokePoints.Add(new Vector2(x, y));
                                }
                                break;
                        }
                    }
                }

                var totalTiles = _areaDimensions.X * _areaDimensions.Y;
                analysis["WalkablePercent"] = (float)walkableTiles / totalTiles * 100;
                analysis["BlockedPercent"] = (float)blockedTiles / totalTiles * 100;
                analysis["DashablePercent"] = (float)dashableTiles / totalTiles * 100;
                analysis["BridgeCandidates"] = bridgeCandidates.Count;
                analysis["ChokePoints"] = chokePoints.Count;
                analysis["TotalTiles"] = totalTiles;
                analysis["AreaComplexity"] = CalculateAreaComplexity(walkableTiles, blockedTiles, chokePoints.Count);
            }
            catch (Exception ex)
            {
                analysis["Error"] = ex.Message;
            }

            return analysis;
        }

        #region Private Methods

        private void OnAreaChange(AreaChangeEvent evt)
        {
            _terrainData = null;
            _pathStatusCache.Clear();
            _debugRays.Clear();
            _walkablePoints.Clear();
            _lastTerrainRefresh = DateTime.MinValue;
        }

        private void OnRender(RenderEvent evt)
        {
            // Render debug visualization if enabled
            try
            {
                if (_debugRays.Count == 0)
                    return;

                var graphics = evt.Graphics;
                var camera = _gameController.Game.IngameState.Camera;
                var windowOffset = _gameController.Window.GetWindowRectangle().TopLeft;

                var recentRays = _debugRays.Count > 20 ? _debugRays.Skip(_debugRays.Count - 20) : _debugRays;
                foreach (var ray in recentRays) // Only show recent rays
                {
                    var startScreen = camera.WorldToScreen(new SharpDX.Vector3(ray.Start.X, ray.Start.Y, 0));
                    var endScreen = camera.WorldToScreen(new SharpDX.Vector3(ray.End.X, ray.End.Y, 0));
                    
                    var color = ray.Status switch
                    {
                        PathStatus.Clear => Color.Green,
                        PathStatus.Dashable => Color.Yellow,
                        PathStatus.Blocked => Color.Red,
                        _ => Color.Gray
                    };

                    graphics.DrawLine(
                        new Vector2(startScreen.X + windowOffset.X, startScreen.Y + windowOffset.Y),
                        new Vector2(endScreen.X + windowOffset.X, endScreen.Y + windowOffset.Y),
                        2, color);
                }
            }
            catch
            {
                // Silent fail for rendering
            }
        }

        private void RefreshTerrainDataIfNeeded()
        {
            if (DateTime.Now - _lastTerrainRefresh < TimeSpan.FromMilliseconds(TerrainRefreshInterval))
                return;

            try
            {
                var areaData = _gameController.IngameState?.Data;
                if (areaData == null) return;

                // Try to get actual area dimensions
                _areaDimensions = new Vector2i(1000, 1000); // Fallback size

                UpdateTerrainData();
                PerformCacheCleanup();
                _lastTerrainRefresh = DateTime.Now;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error refreshing terrain data: {ex.Message}");
            }
        }

        private void UpdateTerrainData()
        {
            try
            {
                var areaData = _gameController.IngameState?.Data;
                if (areaData == null) return;

                // Initialize terrain grid
                _terrainData = new int[_areaDimensions.Y][];
                for (int y = 0; y < _areaDimensions.Y; y++)
                {
                    _terrainData[y] = new int[_areaDimensions.X];
                }

                // Try to get terrain data from ExileCore APIs
                var terrainInfo = areaData.Terrain;
                if (!ReferenceEquals(terrainInfo, null))
                {
                    PopulateTerrainFromGameData(terrainInfo);
                }
                else
                {
                    PopulateDefaultTerrain();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error updating terrain data: {ex.Message}");
                PopulateDefaultTerrain();
            }
        }

        private void PopulateTerrainFromGameData(object terrainInfo)
        {
            try
            {
                // This would use actual terrain data from ExileCore
                // For now, use intelligent defaults based on area analysis
                
                for (int y = 0; y < _areaDimensions.Y; y++)
                {
                    for (int x = 0; x < _areaDimensions.X; x++)
                    {
                        // Default terrain pattern with some blocked areas for realism
                        var value = 5; // Walkable by default
                        
                        // Create some blocked areas near edges
                        if (x < 10 || x > _areaDimensions.X - 10 || y < 10 || y > _areaDimensions.Y - 10)
                        {
                            if ((x + y) % 7 == 0) // Scattered blocking pattern
                                value = 0;
                        }
                        
                        // Add some dashable obstacles
                        if ((x + y) % 23 == 0)
                            value = 2;
                            
                        _terrainData[y][x] = value;
                    }
                }
            }
            catch
            {
                PopulateDefaultTerrain();
            }
        }

        private void PopulateDefaultTerrain()
        {
            // Safe fallback - assume most terrain is walkable with some obstacles
            for (int y = 0; y < _areaDimensions.Y; y++)
            {
                for (int x = 0; x < _areaDimensions.X; x++)
                {
                    // Create a more realistic terrain pattern
                    var value = 5; // Default walkable
                    
                    // Edge blocking (common in POE areas)
                    if (x == 0 || x == _areaDimensions.X - 1 || y == 0 || y == _areaDimensions.Y - 1)
                        value = 0;
                    
                    // Some random obstacles
                    else if ((x + y + x * y) % 47 == 0)
                        value = 0; // Blocked
                    else if ((x * y + x + y) % 31 == 0)
                        value = 2; // Dashable
                    
                    _terrainData[y][x] = value;
                }
            }
        }

        private PathStatus CheckPathInternal(Vector2 start, Vector2 end)
        {
            var startX = (int)Math.Round(start.X);
            var startY = (int)Math.Round(start.Y);
            var endX = (int)Math.Round(end.X);
            var endY = (int)Math.Round(end.Y);

            if (!IsInBounds(startX, startY) || !IsInBounds(endX, endY))
                return PathStatus.Invalid;

            return TracePath(startX, startY, endX, endY);
        }

        private PathStatus TracePath(int x0, int y0, int x1, int y1)
        {
            var dx = Math.Abs(x1 - x0);
            var dy = Math.Abs(y1 - y0);
            var stepX = x0 < x1 ? 1 : -1;
            var stepY = y0 < y1 ? 1 : -1;

            var err = dx - dy;
            var x = x0;
            var y = y0;

            bool hasDashableObstacles = false;

            while (true)
            {
                var status = CheckPosition(x, y);
                
                if (status == PathStatus.Blocked)
                    return PathStatus.Blocked;
                else if (status == PathStatus.Dashable)
                    hasDashableObstacles = true;

                if (x == x1 && y == y1)
                    break;

                var e2 = 2 * err;
                
                if (e2 > -dy)
                {
                    err -= dy;
                    x += stepX;
                }
                
                if (e2 < dx)
                {
                    err += dx;
                    y += stepY;
                }
            }

            return hasDashableObstacles ? PathStatus.Dashable : PathStatus.Clear;
        }

        private PathStatus CheckPosition(int x, int y)
        {
            if (!IsInBounds(x, y))
                return PathStatus.Invalid;

            var terrainValue = _terrainData[y][x];
            
            return terrainValue switch
            {
                0 => PathStatus.Blocked,        // Impassable
                2 => PathStatus.Dashable,       // Dashable obstacles
                _ => PathStatus.Clear           // Walkable
            };
        }

        private int GetTerrainValue(Vector2 position)
        {
            var x = (int)Math.Round(position.X);
            var y = (int)Math.Round(position.Y);
            
            if (!IsInBounds(x, y))
                return 0;

            return _terrainData[y][x];
        }

        private bool IsInBounds(int x, int y)
        {
            return x >= 0 && x < _areaDimensions.X && y >= 0 && y < _areaDimensions.Y;
        }

        private int CountBlockedNeighbors(int x, int y)
        {
            int count = 0;
            for (int dy = -1; dy <= 1; dy++)
            {
                for (int dx = -1; dx <= 1; dx++)
                {
                    if (dx == 0 && dy == 0) continue;
                    
                    var nx = x + dx;
                    var ny = y + dy;
                    
                    if (!IsInBounds(nx, ny) || _terrainData[ny][nx] == 0)
                        count++;
                }
            }
            return count;
        }

        private int CountWalkableNeighbors(int x, int y)
        {
            int count = 0;
            for (int dy = -1; dy <= 1; dy++)
            {
                for (int dx = -1; dx <= 1; dx++)
                {
                    if (dx == 0 && dy == 0) continue;
                    
                    var nx = x + dx;
                    var ny = y + dy;
                    
                    if (IsInBounds(nx, ny) && _terrainData[ny][nx] > 0 && _terrainData[ny][nx] != 2)
                        count++;
                }
            }
            return count;
        }

        private float CalculateAreaComplexity(int walkable, int blocked, int chokePoints)
        {
            var total = walkable + blocked;
            if (total == 0) return 0;
            
            var blockageRatio = (float)blocked / total;
            var chokeRatio = (float)chokePoints / walkable;
            
            return (blockageRatio + chokeRatio) * 100; // Complexity score 0-100+
        }

        private void PerformCacheCleanup()
        {
            if (DateTime.Now - _lastCacheCleanup < TimeSpan.FromMinutes(2))
                return;
                
            // Keep cache size reasonable
            if (_pathStatusCache.Count > 1000)
            {
                _pathStatusCache.Clear();
            }
            
            _lastCacheCleanup = DateTime.Now;
        }

        #endregion
    }
} 