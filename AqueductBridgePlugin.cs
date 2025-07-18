using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Web;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.IO;
using ExileCore;
using ExileCore.PoEMemory.Components;
using ExileCore.PoEMemory.MemoryObjects;
using ExileCore.Shared.Attributes;
using ExileCore.Shared.Interfaces;
using ExileCore.Shared.Nodes;
using Newtonsoft.Json;
using SharpDX;
using ImGuiNET;

namespace AqueductBridge
{
    public class AqueductBridgePlugin : BaseSettingsPlugin<AqueductBridgeSettings>
    {
        private HttpListener httpListener;
        private bool isRunning = false;
        private Task serverTask;
        private CancellationTokenSource cancellationTokenSource;
        private string lastError = "";
        
        // Visual path data
        private List<SharpDX.Vector2> currentPath = new List<SharpDX.Vector2>();
        private SharpDX.Vector2? targetPosition = null;
        private DateTime lastPathUpdate = DateTime.MinValue;
        private readonly object pathLock = new object();

        public override bool Initialise()
        {
            try
            {
                DebugWindow.LogMsg("AqueductBridge plugin initializing...");
                
                if (Settings.AutoStartServer.Value)
                {
                    StartHttpServer();
                }

                DebugWindow.LogMsg("AqueductBridge plugin initialized successfully");
                return true;
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Failed to initialize AqueductBridge: {ex.Message}");
                return false;
            }
        }

        public override void Render()
        {
            if (!Settings.Enable.Value) return;

            try
            {
                if (ImGui.Begin("AqueductBridge"))
                {
                    ImGui.Text($"Server Status: {(isRunning ? "Running" : "Stopped")}");
                    ImGui.Text($"Port: {Settings.HttpServerPort.Value}");
                    
                    if (isRunning)
                    {
                        ImGui.Text("Available Endpoints:");
                        ImGui.BulletText("/gameInfo - Basic game info");
                        ImGui.BulletText("/gameInfo?type=full - Full automation data");
                        ImGui.BulletText("/player - Player data");
                        ImGui.BulletText("/area - Area data");
                        ImGui.BulletText("/positionOnScreen?y={y}&x={x} - Coordinate conversion");
                        
                        if (ImGui.Button("Stop Server"))
                        {
                            StopHttpServer();
                        }
                    }
                    else
                    {
                        if (ImGui.Button("Start Server"))
                        {
                            StartHttpServer();
                        }
                    }

                    ImGui.End();
                }

                // Render visual path if enabled
                if (Settings.ShowVisualPath.Value)
                {
                    RenderVisualPath();
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error in Render: {ex.Message}");
            }
        }

        private void StartHttpServer()
        {
            if (isRunning) return;

            try
            {
                cancellationTokenSource = new CancellationTokenSource();
                serverTask = Task.Run(() => RunHttpServer(cancellationTokenSource.Token));
                isRunning = true;
                DebugWindow.LogMsg($"HTTP Server started on port {Settings.HttpServerPort.Value}");
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Failed to start HTTP server: {ex.Message}");
            }
        }

        private void StopHttpServer()
        {
            if (!isRunning) return;

            try
            {
                cancellationTokenSource?.Cancel();
                httpListener?.Stop();
                httpListener?.Close();
                isRunning = false;
                DebugWindow.LogMsg("HTTP Server stopped");
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error stopping HTTP server: {ex.Message}");
            }
        }

        private async Task RunHttpServer(CancellationToken cancellationToken)
        {
            httpListener = new HttpListener();
            httpListener.Prefixes.Add($"http://127.0.0.1:{Settings.HttpServerPort.Value}/");
            
            try
            {
                httpListener.Start();
                
                while (!cancellationToken.IsCancellationRequested)
                {
                    try
                    {
                        var context = await httpListener.GetContextAsync();
                        _ = Task.Run(() => ProcessRequest(context), cancellationToken);
                    }
                    catch (ObjectDisposedException)
                    {
                        break; // Server was stopped
                    }
                    catch (Exception ex)
                    {
                        DebugWindow.LogError($"Error accepting HTTP request: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"HTTP server error: {ex.Message}");
            }
            finally
            {
                httpListener?.Close();
            }
        }

        private void ProcessRequest(HttpListenerContext context)
        {
            try
            {
                var request = context.Request;
                var response = context.Response;
                
                // Set CORS headers
                response.Headers.Add("Access-Control-Allow-Origin", "*");
                response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
                response.Headers.Add("Access-Control-Allow-Headers", "Content-Type");
                
                if (request.HttpMethod == "OPTIONS")
                {
                    response.StatusCode = 200;
                    response.Close();
                    return;
                }

                var responseData = GetGameData(request.Url, context);
                var responseString = JsonConvert.SerializeObject(responseData);
                var responseBytes = Encoding.UTF8.GetBytes(responseString);
                
                response.ContentType = "application/json";
                response.ContentLength64 = responseBytes.Length;
                response.StatusCode = 200;
                
                using (var output = response.OutputStream)
                {
                    output.Write(responseBytes, 0, responseBytes.Length);
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error processing request: {ex.Message}");
                try
                {
                    context.Response.StatusCode = 500;
                    context.Response.Close();
                }
                catch { }
            }
        }

        private object GetGameData(Uri url, HttpListenerContext context)
        {
            try
            {
                var path = url.AbsolutePath;
                var query = HttpUtility.ParseQueryString(url.Query);
                
                switch (path)
                {
                    case "/gameInfo":
                        var type = query["type"];
                        if (string.Equals(type, "full", StringComparison.OrdinalIgnoreCase))
                        {
                            return GetFullGameData();
                        }
                        return GetGameInfo();
                    case "/player":
                        return GetPlayerData();
                    case "/area":
                        return GetAreaData();
                    case "/positionOnScreen":
                        return GetPositionOnScreen(query["x"], query["y"]);
                    case "/updatePath":
                        return HandleUpdatePath(context);
                    case "/clearPath":
                        return HandleClearPath();
                    default:
                        return new { error = "Unknown endpoint" };
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error getting game data: {ex.Message}");
                return new { error = ex.Message };
            }
        }

        private object GetGameInfo()
        {
            if (GameController?.Player == null)
                return new { error = "Game not loaded" };

            return new
            {
                player_name = GameController.Player.GetComponent<ExileCore.PoEMemory.Components.Player>()?.PlayerName ?? "Unknown",
                area_name = GameController.Area?.CurrentArea?.Name ?? "Unknown",
                in_game = GameController.InGame,
                window_focused = GameController.Window.IsForeground()
            };
        }

        private object GetFullGameData()
        {
            if (GameController?.Player == null)
                return new { error = "Game not loaded" };

            return new
            {
                WindowArea = GetWindowArea(),
                terrain_string = GetTerrainString(),
                player_pos = GetPlayerPosition(),
                awake_entities = GetAwakeEntities(),
                life = GetLifeData(),
                area_loading = GameController.IsLoading,
                area_id = GameController.Game?.IngameState?.Data?.CurrentAreaHash ?? 0
            };
        }

        private object GetPlayerData()
        {
            if (GameController?.Player == null)
                return new { error = "Player not found" };

            var player = GameController.Player;
            var life = player.GetComponent<ExileCore.PoEMemory.Components.Life>();
            var pos = player.GetComponent<ExileCore.PoEMemory.Components.Render>();

            return new
            {
                position = new { x = pos?.Pos.X ?? 0, y = pos?.Pos.Y ?? 0 },
                health = new 
                { 
                    current = life?.CurHP ?? 0, 
                    max = life?.MaxHP ?? 0, 
                    percentage = life?.HPPercentage ?? 0 
                },
                mana = new 
                { 
                    current = life?.CurMana ?? 0, 
                    max = life?.MaxMana ?? 0, 
                    percentage = (life?.MaxMana ?? 0) > 0 ? (life?.CurMana ?? 0) * 100 / (life?.MaxMana ?? 0) : 0 
                }
            };
        }

        private object GetAreaData()
        {
            if (GameController?.Area == null)
                return new { error = "Area not loaded" };

            return new
            {
                area_name = GameController.Area.CurrentArea?.Name ?? "Unknown",
                area_id = GameController.Game?.IngameState?.Data?.CurrentAreaHash.ToString() ?? "Unknown",
                is_loading = GameController.IsLoading
            };
        }

        private object GetPositionOnScreen(string xStr, string yStr)
        {
            try
            {
                if (!int.TryParse(xStr, out int x) || !int.TryParse(yStr, out int y))
                {
                    return new { error = "Invalid coordinates" };
                }

                var camera = GameController?.IngameState?.Camera;
                if (camera == null)
                {
                    return new { error = "Camera not available" };
                }

                var worldPos = new Vector3(x, y, 0);
                var screenPos = camera.WorldToScreen(worldPos);
                
                return new int[] { (int)screenPos.X, (int)screenPos.Y };
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error converting position to screen: {ex.Message}");
                return new { error = ex.Message };
            }
        }

        private object GetWindowArea()
        {
            try
            {
                var windowRect = GameController.Window.GetWindowRectangle();
                return new
                {
                    X = windowRect.X,
                    Y = windowRect.Y,
                    Width = windowRect.Width,
                    Height = windowRect.Height
                };
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error getting window area: {ex.Message}");
                return new { X = 0, Y = 0, Width = 1920, Height = 1080 };
            }
        }

        private string GetTerrainString()
        {
            try
            {
                // Debug: Let's see what TerrainData properties are available
                var terrain = GameController?.IngameState?.Data?.Terrain;
                if (terrain != null)
                {
                    DebugWindow.LogMsg("TerrainData object found, investigating properties...");
                    var terrainType = terrain.GetType();
                    var properties = terrainType.GetProperties();
                    DebugWindow.LogMsg($"TerrainData properties ({properties.Length} total):");
                    foreach (var prop in properties)
                    {
                        DebugWindow.LogMsg($"  - {prop.Name}: {prop.PropertyType.Name}");
                    }
                }
                else
                {
                    DebugWindow.LogMsg("TerrainData is null");
                }
                
                // Use fallback terrain data - real terrain access needs more research
                DebugWindow.LogMsg("GetTerrainString: Using improved fallback terrain data");
                
                // Return a larger grid for better pathfinding (50x50 instead of 10x10)
                var sb = new StringBuilder();
                for (int y = 0; y < 50; y++)
                {
                    for (int x = 0; x < 50; x++)
                    {
                        sb.Append("51"); // All passable for now
                        if (x < 49)
                        {
                            sb.Append(" ");
                        }
                    }
                    if (y < 49)
                    {
                        sb.Append("\r\n");
                    }
                }
                
                return sb.ToString();
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error getting terrain string: {ex.Message}");
                return "";
            }
        }

        private object GetPlayerPosition()
        {
            try
            {
                var player = GameController.Player;
                if (player == null)
                {
                    return new { X = 0, Y = 0, Z = 0 };
                }

                var gridPos = player.GridPos;
                return new
                {
                    X = (int)gridPos.X,
                    Y = (int)gridPos.Y,
                    Z = 0
                };
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error getting player position: {ex.Message}");
                return new { X = 0, Y = 0, Z = 0 };
            }
        }

        private object[] GetAwakeEntities()
        {
            try
            {
                var entities = new List<object>();
                var entityList = GameController?.EntityListWrapper?.ValidEntitiesByType;
                
                if (entityList == null)
                {
                    return entities.ToArray();
                }

                var camera = GameController?.IngameState?.Camera;
                if (camera == null)
                {
                    return entities.ToArray();
                }

                foreach (var entityGroup in entityList.Values)
                {
                    foreach (var entity in entityGroup)
                    {
                        try
                        {
                            if (entity?.IsValid != true || entity.Address == 0)
                                continue;

                            var gridPos = entity.GridPos;
                            var worldPos = new Vector3(gridPos.X, gridPos.Y, 0);
                            var screenPos = camera.WorldToScreen(worldPos);

                            // Get entity type for aqueduct_runner
                            var entityType = GetEntityTypeForRunner(entity);
                            if (entityType == 0) continue; // Skip if not relevant

                            var life = entity.GetComponent<Life>();
                            var lifeData = new
                            {
                                Health = new
                                {
                                    Current = life?.CurHP ?? 0,
                                    Total = life?.MaxHP ?? 0,
                                    ReservedTotal = 0
                                },
                                Mana = new
                                {
                                    Current = life?.CurMana ?? 0,
                                    Total = life?.MaxMana ?? 0,
                                    ReservedTotal = 0
                                },
                                EnergyShield = new
                                {
                                    Current = life?.CurES ?? 0,
                                    Total = life?.MaxES ?? 0,
                                    ReservedTotal = 0
                                }
                            };

                            entities.Add(new
                            {
                                GridPosition = new { X = (int)gridPos.X, Y = (int)gridPos.Y, Z = 0 },
                                location_on_screen = new { X = (int)screenPos.X, Y = (int)screenPos.Y },
                                EntityType = entityType,
                                Path = entity.Path ?? "",
                                life = lifeData,
                                Id = entity.Id,
                                IsAlive = entity.IsAlive
                            });
                        }
                        catch (Exception ex)
                        {
                            // Skip individual entity errors
                            continue;
                        }
                    }
                }

                return entities.ToArray();
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error getting awake entities: {ex.Message}");
                return new object[0];
            }
        }

        private int GetEntityTypeForRunner(Entity entity)
        {
            try
            {
                // Check for important entities by path
                var path = entity.Path?.ToLower() ?? "";
                
                // Check for monsters first
                if (path.Contains("monster") || path.Contains("enemy") || 
                    entity.HasComponent<Monster>())
                {
                    return 14; // aqueduct_runner expects 14 for monsters
                }
                
                if (path.Contains("door") || path.Contains("waypoint") || 
                    path.Contains("transition") || path.Contains("stash"))
                {
                    return 1; // Generic interactable
                }

                return 0; // Skip other entities
            }
            catch
            {
                return 0;
            }
        }

        private object GetLifeData()
        {
            try
            {
                var player = GameController.Player;
                if (player == null)
                {
                    return new { error = "Player not found" };
                }

                var life = player.GetComponent<Life>();
                if (life == null)
                {
                    return new { error = "Life component not found" };
                }

                return new
                {
                    Health = new
                    {
                        Current = life.CurHP,
                        Total = life.MaxHP,
                        ReservedTotal = 0
                    },
                    Mana = new
                    {
                        Current = life.CurMana,
                        Total = life.MaxMana,
                        ReservedTotal = 0
                    },
                    EnergyShield = new
                    {
                        Current = life.CurES,
                        Total = life.MaxES,
                        ReservedTotal = 0
                    }
                };
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error getting life data: {ex.Message}");
                return new { error = ex.Message };
            }
        }

        private void RenderVisualPath()
        {
            try
            {
                if (!GameController.InGame || GameController.Player == null)
                    return;

                lock (pathLock)
                {
                    // Draw path lines
                    if (currentPath.Count > 1)
                    {
                        var camera = GameController.IngameState.Camera;
                        var playerPos = GameController.Player.GridPos;
                        var playerScreenPos = camera.WorldToScreen(new Vector3(playerPos.X, playerPos.Y, 0));

                        // Draw line from player to first waypoint
                        if (currentPath.Count > 0)
                        {
                            var firstWaypoint = currentPath[0];
                            var firstScreenPos = camera.WorldToScreen(new SharpDX.Vector3(firstWaypoint.X, firstWaypoint.Y, 0f));
                            
                            if (IsValidScreenPosition(playerScreenPos) && IsValidScreenPosition(firstScreenPos))
                            {
                                Graphics.DrawLine(
                                    new SharpDX.Vector2(playerScreenPos.X, playerScreenPos.Y),
                                    new SharpDX.Vector2(firstScreenPos.X, firstScreenPos.Y),
                                    Settings.PathLineWidth.Value,
                                    Settings.PathLineColor.Value
                                );
                            }
                        }

                        // Draw lines between waypoints
                        for (int i = 0; i < currentPath.Count - 1; i++)
                        {
                            var fromPos = currentPath[i];
                            var toPos = currentPath[i + 1];
                            
                            var fromScreenPos = camera.WorldToScreen(new SharpDX.Vector3(fromPos.X, fromPos.Y, 0f));
                            var toScreenPos = camera.WorldToScreen(new SharpDX.Vector3(toPos.X, toPos.Y, 0f));
                            
                            if (IsValidScreenPosition(fromScreenPos) && IsValidScreenPosition(toScreenPos))
                            {
                                Graphics.DrawLine(
                                    new SharpDX.Vector2(fromScreenPos.X, fromScreenPos.Y),
                                    new SharpDX.Vector2(toScreenPos.X, toScreenPos.Y),
                                    Settings.PathLineWidth.Value,
                                    Settings.PathLineColor.Value
                                );
                            }
                        }
                    }

                    // Draw target marker
                    if (Settings.ShowTargetMarker.Value && targetPosition.HasValue)
                    {
                        var camera = GameController.IngameState.Camera;
                        var targetScreenPos = camera.WorldToScreen(new SharpDX.Vector3(targetPosition.Value.X, targetPosition.Value.Y, 0f));
                        
                        if (IsValidScreenPosition(targetScreenPos))
                        {
                            var screenPos = new System.Numerics.Vector2(targetScreenPos.X, targetScreenPos.Y);
                            var radius = 10f;
                            
                            // Draw target circle
                            Graphics.DrawEllipse(screenPos, new System.Numerics.Vector2(radius * 2, radius * 2), Settings.TargetMarkerColor.Value, Settings.PathLineWidth.Value);
                            
                            // Draw target cross
                            Graphics.DrawLine(
                                new SharpDX.Vector2(screenPos.X - radius, screenPos.Y),
                                new SharpDX.Vector2(screenPos.X + radius, screenPos.Y),
                                Settings.PathLineWidth.Value,
                                Settings.TargetMarkerColor.Value
                            );
                            Graphics.DrawLine(
                                new SharpDX.Vector2(screenPos.X, screenPos.Y - radius),
                                new SharpDX.Vector2(screenPos.X, screenPos.Y + radius),
                                Settings.PathLineWidth.Value,
                                Settings.TargetMarkerColor.Value
                            );
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error rendering visual path: {ex.Message}");
            }
        }

        private bool IsValidScreenPosition(Vector3 screenPos)
        {
            var windowRect = GameController.Window.GetWindowRectangle();
            return screenPos.X >= 0 && screenPos.X <= windowRect.Width &&
                   screenPos.Y >= 0 && screenPos.Y <= windowRect.Height;
        }

        public void UpdateVisualPath(List<Dictionary<string, object>> waypoints, Dictionary<string, object> target = null)
        {
            try
            {
                lock (pathLock)
                {
                    currentPath.Clear();
                    
                    if (waypoints != null)
                    {
                        foreach (var waypoint in waypoints)
                        {
                            if (waypoint.ContainsKey("x") && waypoint.ContainsKey("y"))
                            {
                                var x = Convert.ToSingle(waypoint["x"]);
                                var y = Convert.ToSingle(waypoint["y"]);
                                currentPath.Add(new Vector2(x, y));
                            }
                        }
                    }
                    
                    if (target != null && target.ContainsKey("x") && target.ContainsKey("y"))
                    {
                        var x = Convert.ToSingle(target["x"]);
                        var y = Convert.ToSingle(target["y"]);
                        targetPosition = new Vector2(x, y);
                    }
                    else
                    {
                        targetPosition = null;
                    }
                    
                    lastPathUpdate = DateTime.Now;
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error updating visual path: {ex.Message}");
            }
        }

        public void ClearVisualPath()
        {
            lock (pathLock)
            {
                currentPath.Clear();
                targetPosition = null;
            }
        }

        private object HandleUpdatePath(HttpListenerContext context)
        {
            try
            {
                if (context.Request.HttpMethod != "POST")
                {
                    return new { error = "Method not allowed" };
                }

                using (var reader = new StreamReader(context.Request.InputStream))
                {
                    var json = reader.ReadToEnd();
                    var pathData = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
                    
                    if (pathData.ContainsKey("waypoints"))
                    {
                        var waypoints = JsonConvert.DeserializeObject<List<Dictionary<string, object>>>(pathData["waypoints"].ToString());
                        var target = pathData.ContainsKey("target") ? 
                                   JsonConvert.DeserializeObject<Dictionary<string, object>>(pathData["target"].ToString()) : null;
                        
                        UpdateVisualPath(waypoints, target);
                        
                        return new { success = true, message = "Path updated successfully" };
                    }
                    else
                    {
                        return new { error = "Invalid path data" };
                    }
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error handling update path: {ex.Message}");
                return new { error = ex.Message };
            }
        }

        private object HandleClearPath()
        {
            try
            {
                ClearVisualPath();
                return new { success = true, message = "Path cleared successfully" };
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error handling clear path: {ex.Message}");
                return new { error = ex.Message };
            }
        }

        public override void OnClose()
        {
            StopHttpServer();
        }
    }
} 