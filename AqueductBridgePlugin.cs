using System;
using System.Threading.Tasks;
using ExileCore;
using ExileCore.Shared.Attributes;
using ExileCore.Shared.Interfaces;
using ExileCore.Shared.Nodes;
using ImGuiNET;

namespace AqueductBridge
{
    [PluginName("AqueductBridge")]
    [PluginDescription("HTTP Bridge for aqueduct_runner compatibility")]
    [PluginVersion("1.0.0")]
    [PluginAuthor("AqueductBridge")]
    public class AqueductBridgePlugin : BaseSettingsPlugin<AqueductBridgeSettings>
    {
        private HttpServer _httpServer;
        private DataExtractor _dataExtractor;
        private bool _isInitialized = false;
        private Exception _lastError;

        public override bool Initialise()
        {
            try
            {
                _dataExtractor = new DataExtractor(GameController, Settings);
                _httpServer = new HttpServer(GameController, _dataExtractor, Settings);
                
                _isInitialized = true;

                if (Settings.AutoStartServer.Value)
                {
                    Task.Run(async () =>
                    {
                        try
                        {
                            await _httpServer.StartAsync();
                        }
                        catch (Exception ex)
                        {
                            _lastError = ex;
                            DebugWindow.LogError($"AqueductBridge auto-start failed: {ex.Message}");
                        }
                    });
                }

                DebugWindow.LogMsg("AqueductBridge plugin initialized successfully");
                return true;
            }
            catch (Exception ex)
            {
                _lastError = ex;
                DebugWindow.LogError($"AqueductBridge initialization failed: {ex.Message}");
                return false;
            }
        }

        public override void Render()
        {
            if (!_isInitialized) return;

            try
            {
                if (ImGui.CollapsingHeader("AqueductBridge Status"))
                {
                    // Server status
                    var serverStatus = _httpServer?.IsRunning == true ? "Running" : "Stopped";
                    var statusColor = _httpServer?.IsRunning == true ? 
                        new System.Numerics.Vector4(0, 1, 0, 1) : // Green
                        new System.Numerics.Vector4(1, 0, 0, 1);  // Red

                    ImGui.TextColored(statusColor, $"HTTP Server: {serverStatus}");
                    
                    if (_httpServer?.IsRunning == true)
                    {
                        ImGui.Text($"Listening on: http://127.0.0.1:{Settings.HttpServerPort.Value}");
                    }

                    ImGui.Separator();

                    // Control buttons
                    if (_httpServer?.IsRunning == true)
                    {
                        if (ImGui.Button("Stop Server"))
                        {
                            Task.Run(() =>
                            {
                                try
                                {
                                    _httpServer.Stop();
                                    DebugWindow.LogMsg("AqueductBridge HTTP Server stopped manually");
                                }
                                catch (Exception ex)
                                {
                                    _lastError = ex;
                                    DebugWindow.LogError($"AqueductBridge stop error: {ex.Message}");
                                }
                            });
                        }
                    }
                    else
                    {
                        if (ImGui.Button("Start Server"))
                        {
                            Task.Run(async () =>
                            {
                                try
                                {
                                    await _httpServer.StartAsync();
                                    DebugWindow.LogMsg("AqueductBridge HTTP Server started manually");
                                }
                                catch (Exception ex)
                                {
                                    _lastError = ex;
                                    DebugWindow.LogError($"AqueductBridge start error: {ex.Message}");
                                }
                            });
                        }
                    }

                    ImGui.Separator();

                    // Endpoint information
                    if (ImGui.CollapsingHeader("Endpoint Information"))
                    {
                        ImGui.Text("Available Endpoints:");
                        ImGui.BulletText($"GET /gameInfo?type=full - Complete game data");
                        ImGui.BulletText($"GET /gameInfo - Instance data only");
                        ImGui.BulletText($"GET /positionOnScreen?y={{y}}&x={{x}} - Grid to screen conversion");
                        
                        if (_httpServer?.IsRunning == true)
                        {
                            ImGui.Separator();
                            ImGui.Text("Test URLs:");
                            ImGui.Text($"http://127.0.0.1:{Settings.HttpServerPort.Value}/gameInfo?type=full");
                            ImGui.Text($"http://127.0.0.1:{Settings.HttpServerPort.Value}/gameInfo");
                            ImGui.Text($"http://127.0.0.1:{Settings.HttpServerPort.Value}/positionOnScreen?y=100&x=100");
                        }
                    }

                    // Error information
                    if (_lastError != null)
                    {
                        ImGui.Separator();
                        ImGui.TextColored(new System.Numerics.Vector4(1, 0, 0, 1), "Last Error:");
                        ImGui.TextWrapped(_lastError.Message);
                        
                        if (ImGui.Button("Clear Error"))
                        {
                            _lastError = null;
                        }
                    }

                    // Game state information
                    if (ImGui.CollapsingHeader("Game State"))
                    {
                        var player = GameController.Player;
                        if (player != null && player.IsValid)
                        {
                            var gridPos = player.GridPos;
                            ImGui.Text($"Player Position: ({gridPos.X:F0}, {gridPos.Y:F0}, {gridPos.Z:F0})");
                            
                            var windowRect = GameController.Window.GetWindowRectangle();
                            ImGui.Text($"Window: ({windowRect.X}, {windowRect.Y}) {windowRect.Width}x{windowRect.Height}");
                            
                            var entityCount = GameController.EntityListWrapper?.ValidEntitiesByType?.Values?.Count ?? 0;
                            ImGui.Text($"Valid Entities: {entityCount}");
                            
                            var areaName = GameController.Area?.CurrentArea?.Name ?? "Unknown";
                            ImGui.Text($"Current Area: {areaName}");
                        }
                        else
                        {
                            ImGui.Text("Player not available");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _lastError = ex;
                ImGui.TextColored(new System.Numerics.Vector4(1, 0, 0, 1), $"Render Error: {ex.Message}");
            }
        }

        public override void OnClose()
        {
            try
            {
                _httpServer?.Stop();
                DebugWindow.LogMsg("AqueductBridge plugin closed");
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"AqueductBridge close error: {ex.Message}");
            }
        }

        public override void AreaChange(AreaInstance area)
        {
            if (Settings.EnableDebugLogging.Value)
            {
                DebugWindow.LogMsg($"AqueductBridge area changed to: {area.Name}");
            }
        }

        public override void EntityAdded(Entity entity)
        {
            // We could log entity additions here if needed for debugging
            if (Settings.EnableDebugLogging.Value && entity?.Path != null)
            {
                if (entity.Path.Contains("Door") || entity.Path.Contains("Waypoint") || 
                    entity.Path.Contains("Transition") || entity.Path.Contains("Stash"))
                {
                    DebugWindow.LogMsg($"AqueductBridge important entity added: {entity.Path}");
                }
            }
        }

        public override void EntityRemoved(Entity entity)
        {
            // We could log entity removals here if needed for debugging
        }
    }
} 