using System;
using System.Threading.Tasks;
using ExileCore;
using ExileCore.Shared.Interfaces;
using ExileCore.Shared.Nodes;
using ImGuiNET;
using System.Net;
using System.IO;
using System.Text;
using Newtonsoft.Json;
using System.Threading;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using ExileCore.PoEMemory.Components;
using ExileCore.PoEMemory.MemoryObjects;
using ExileCore.Shared.Enums;
using SharpDX;
using ExileCore.PoEMemory;
using GameOffsets.Native;
using System.Reflection;

namespace AqueductBridge
{
    public class AqueductBridgePlugin : BaseSettingsPlugin<AqueductBridgeSettings>
    {
        private HttpListener _httpListener;
        private bool _isServerRunning = false;
        private Task _serverTask;
        private CancellationTokenSource _cancellationTokenSource;

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

            if (ImGui.Begin("AqueductBridge"))
            {
                ImGui.Text($"Server Status: {(_isServerRunning ? "Running" : "Stopped")}");
                ImGui.Text($"Port: {Settings.HttpServerPort.Value}");
                
                if (_isServerRunning)
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
        }

        private void StartHttpServer()
        {
            if (_isServerRunning) return;

            try
            {
                _cancellationTokenSource = new CancellationTokenSource();
                _serverTask = Task.Run(() => RunHttpServer(_cancellationTokenSource.Token));
                _isServerRunning = true;
                DebugWindow.LogMsg($"HTTP Server started on port {Settings.HttpServerPort.Value}");
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Failed to start HTTP server: {ex.Message}");
            }
        }

        private void StopHttpServer()
        {
            if (!_isServerRunning) return;

            try
            {
                _cancellationTokenSource?.Cancel();
                _httpListener?.Stop();
                _httpListener?.Close();
                _isServerRunning = false;
                DebugWindow.LogMsg("HTTP Server stopped");
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"Error stopping HTTP server: {ex.Message}");
            }
        }

        private async Task RunHttpServer(CancellationToken cancellationToken)
        {
            _httpListener = new HttpListener();
            _httpListener.Prefixes.Add($"http://127.0.0.1:{Settings.HttpServerPort.Value}/");
            
            try
            {
                _httpListener.Start();
                
                while (!cancellationToken.IsCancellationRequested)
                {
                    try
                    {
                        var context = await _httpListener.GetContextAsync();
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
                _httpListener?.Close();
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

                var responseData = GetGameData(request.Url);
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

        private object GetGameData(Uri url)
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
                
                // Try to get real terrain data first
                var terrain = GameController?.IngameState?.Data?.Terrain;
                if (terrain != null)
                {
                    try
                    {
                        // Try to access terrain data
                        var terrainSize = terrain.LayerMelee.Size;
                        if (terrainSize > 0)
                        {
                            var terrainBytes = GameController.Memory.ReadBytes(terrain.LayerMelee.First, terrainSize);
                            var width = (int)(terrain.NumCols - 1) * 23;
                            var height = (int)(terrain.NumRows - 1) * 23;

                            var sb = new StringBuilder();
                            if ((width & 1) > 0) width++;
                            
                            for (int y = 0; y < height; y++)
                            {
                                var dataIndex = y * terrain.BytesPerRow;
                                for (int x = 0; x < width; x += 2)
                                {
                                    if (dataIndex + (x >> 1) < terrainBytes.Length)
                                    {
                                        var b = terrainBytes[dataIndex + (x >> 1)];
                                        var terrainValue1 = b & 15;
                                        var terrainValue2 = (b >> 4) & 15;
                                        
                                        // Convert terrain value to aqueduct_runner format
                                        // ExileApi: 0 = passable, 1+ = not passable
                                        // aqueduct_runner: 51 = passable, 49 = not passable
                                        var convertedValue1 = terrainValue1 == 0 ? 51 : 49;
                                        sb.Append(convertedValue1);
                                        
                                        if (x + 1 < width)
                                        {
                                            var convertedValue2 = terrainValue2 == 0 ? 51 : 49;
                                            sb.Append(" ");
                                            sb.Append(convertedValue2);
                                        }
                                    }
                                    else
                                    {
                                        sb.Append("49"); // Default to not passable
                                        if (x + 1 < width)
                                        {
                                            sb.Append(" 49");
                                        }
                                    }

                                    if (x < width - 2)
                                    {
                                        sb.Append(" ");
                                    }
                                }
                                if (y < height - 1)
                                {
                                    sb.Append("\r\n");
                                }
                            }
                            
                            DebugWindow.LogMsg($"GetTerrainString: Generated real terrain data {width}x{height}");
                            return sb.ToString();
                        }
                    }
                    catch (Exception ex)
                    {
                        DebugWindow.LogError($"Error accessing real terrain data: {ex.Message}");
                    }
                }
                
                // Fallback to simple terrain if real data fails
                DebugWindow.LogMsg("GetTerrainString: Using fallback terrain data");
                
                // Return a larger grid for better pathfinding
                var sb2 = new StringBuilder();
                for (int y = 0; y < 50; y++)
                {
                    for (int x = 0; x < 50; x++)
                    {
                        sb2.Append("51"); // All passable for now
                        if (x < 49)
                        {
                            sb2.Append(" ");
                        }
                    }
                    if (y < 49)
                    {
                        sb2.Append("\r\n");
                    }
                }
                
                return sb2.ToString();
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
                // Map ExileApi entity types to aqueduct_runner expected values
                if (entity.Type == EntityType.Monster)
                {
                    return 14; // aqueduct_runner expects 14 for monsters
                }

                // Check for important entities by path
                var path = entity.Path?.ToLower() ?? "";
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

        public override void OnClose()
        {
            StopHttpServer();
        }
    }
} 