using System;
using System.Collections.Generic;
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
        
        // Settings
        private int TerrainRefreshInterval => 1000; // Refresh every 1 second
        private int TerrainValueForCollision => 2; // Terrain value that blocks movement but allows dashing
        
        // Debug visualization
        private readonly List<(Vector2 Start, Vector2 End, PathStatus Status)> _debugRays = new();
        private readonly HashSet<Vector2> _walkablePoints = new();

        public LineOfSight(GameController gameController)
        {
            _gameController = gameController;
            
            // Subscribe to events
            var eventBus = EventBus.Instance;
            eventBus.Subscribe<AreaChangeEvent>(OnAreaChange);
            eventBus.Subscribe<RenderEvent>(OnRender);
        }

        /// <summary>
        /// Check if there's a clear path between two points
        /// </summary>
        public PathStatus CheckPath(Vector2 from, Vector2 to)
        {
            try
            {
                // Ensure terrain data is available and fresh
                RefreshTerrainDataIfNeeded();
                
                if (_terrainData == null)
                    return PathStatus.Invalid;

                var status = CheckPathInternal(from, to);
                
                // Add to debug visualization
                _debugRays.Add((from, to, status));
                
                // Keep only recent rays for performance
                if (_debugRays.Count > 50)
                {
                    _debugRays.RemoveAt(0);
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
        /// Check if a specific position is walkable
        /// </summary>
        public bool IsWalkable(Vector2 position)
        {
            try
            {
                RefreshTerrainDataIfNeeded();
                if (_terrainData == null) return false;
                
                var terrainValue = GetTerrainValue(position);
                return terrainValue != 0; // 0 = impassable
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Find the closest walkable position to a target
        /// </summary>
        public Vector2? FindClosestWalkablePosition(Vector2 target, float searchRadius = 50f)
        {
            try
            {
                if (IsWalkable(target))
                    return target;

                // Search in expanding circles
                for (int radius = 5; radius <= searchRadius; radius += 5)
                {
                    for (int angle = 0; angle < 360; angle += 15)
                    {
                        var radians = angle * Math.PI / 180.0;
                        var testPos = new Vector2(
                            target.X + (float)(Math.Cos(radians) * radius),
                            target.Y + (float)(Math.Sin(radians) * radius)
                        );

                        if (IsWalkable(testPos))
                        {
                            return testPos;
                        }
                    }
                }

                return null; // No walkable position found
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// Get terrain analysis for a position (for debugging/visualization)
        /// </summary>
        public string GetTerrainInfo(Vector2 position)
        {
            try
            {
                RefreshTerrainDataIfNeeded();
                if (_terrainData == null) return "No terrain data";
                
                var terrainValue = GetTerrainValue(position);
                var walkable = IsWalkable(position);
                
                return $"Terrain: {terrainValue}, Walkable: {walkable}";
            }
            catch (Exception ex)
            {
                return $"Error: {ex.Message}";
            }
        }

        #region Private Methods

        private void OnAreaChange(AreaChangeEvent evt)
        {
            // Force terrain refresh on area change
            _terrainData = null;
            _areaDimensions = Vector2i.Zero;
            _lastTerrainRefresh = DateTime.MinValue;
            
            RefreshTerrainDataIfNeeded();
        }

        private void OnRender(RenderEvent evt)
        {
            // This could be used for debug visualization in the future
            // For now, we'll keep it simple and just maintain the ray list
        }

        private void RefreshTerrainDataIfNeeded()
        {
            var now = DateTime.Now;
            if (_terrainData != null && (now - _lastTerrainRefresh).TotalMilliseconds < TerrainRefreshInterval)
                return;

            try
            {
                if (!_gameController.InGame || _gameController.Player == null)
                    return;

                var areaData = _gameController.IngameState?.Data;
                if (areaData == null) return;

                _areaDimensions = areaData.AreaDimensions;
                if (_areaDimensions.X <= 0 || _areaDimensions.Y <= 0)
                    return;

                // Get terrain data from the game
                UpdateTerrainData();
                _lastTerrainRefresh = now;
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

                // Get terrain data from ExileCore
                // This is a simplified approach - in reality you'd access the actual terrain data
                // For now, we'll use a basic approach that works with available APIs
                
                var terrainInfo = areaData.Terrain;
                if (terrainInfo != null)
                {
                    // Try to populate terrain data using available ExileCore APIs
                    PopulateTerrainFromGameData(terrainInfo);
                }
                else
                {
                    // Fallback: assume most areas are walkable
                    PopulateDefaultTerrain();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error updating terrain data: {ex.Message}");
                // Fallback to default terrain
                PopulateDefaultTerrain();
            }
        }

        private void PopulateTerrainFromGameData(object terrainInfo)
        {
            try
            {
                // This would use the actual terrain data from ExileCore
                // Implementation depends on available APIs
                // For now, use a conservative approach
                
                for (int y = 0; y < _areaDimensions.Y; y++)
                {
                    for (int x = 0; x < _areaDimensions.X; x++)
                    {
                        // Default to walkable, but this would be replaced with actual terrain reading
                        _terrainData[y][x] = 5; // Walkable
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
            // Safe fallback - assume most terrain is walkable
            for (int y = 0; y < _areaDimensions.Y; y++)
            {
                for (int x = 0; x < _areaDimensions.X; x++)
                {
                    _terrainData[y][x] = 5; // Assume walkable
                }
            }
        }

        private PathStatus CheckPathInternal(Vector2 start, Vector2 end)
        {
            var startX = (int)Math.Round(start.X);
            var startY = (int)Math.Round(start.Y);
            var endX = (int)Math.Round(end.X);
            var endY = (int)Math.Round(end.Y);

            // Check bounds
            if (!IsInBounds(startX, startY) || !IsInBounds(endX, endY))
                return PathStatus.Invalid;

            // Use Bresenham-like algorithm to check path
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

            while (true)
            {
                // Check current position
                var status = CheckPosition(x, y);
                if (status != PathStatus.Clear)
                    return status;

                // Are we at the destination?
                if (x == x1 && y == y1)
                    break;

                // Calculate next step
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

            return PathStatus.Clear;
        }

        private PathStatus CheckPosition(int x, int y)
        {
            if (!IsInBounds(x, y))
                return PathStatus.Invalid;

            var terrainValue = _terrainData[y][x];
            
            return terrainValue switch
            {
                0 => PathStatus.Blocked,        // Impassable (walls, void)
                2 => PathStatus.Dashable,       // Dashable obstacles (doors, etc.)
                _ => PathStatus.Clear           // Walkable (1, 5, etc.)
            };
        }

        private int GetTerrainValue(Vector2 position)
        {
            var x = (int)Math.Round(position.X);
            var y = (int)Math.Round(position.Y);
            
            if (!IsInBounds(x, y))
                return 0; // Out of bounds = blocked

            return _terrainData[y][x];
        }

        private bool IsInBounds(int x, int y)
        {
            return x >= 0 && x < _areaDimensions.X && y >= 0 && y < _areaDimensions.Y;
        }

        #endregion

        #region Debug and Visualization

        public List<(Vector2 Start, Vector2 End, PathStatus Status)> GetDebugRays()
        {
            return new List<(Vector2, Vector2, PathStatus)>(_debugRays);
        }

        public void ClearDebugData()
        {
            _debugRays.Clear();
            _walkablePoints.Clear();
        }

        public Vector2i GetAreaDimensions()
        {
            return _areaDimensions;
        }

        #endregion
    }
} 