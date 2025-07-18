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

                var responseData = GetGameData(request.Url.AbsolutePath);
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

        private object GetGameData(string path)
        {
            try
            {
                switch (path)
                {
                    case "/gameInfo":
                        return GetGameInfo();
                    case "/player":
                        return GetPlayerData();
                    case "/area":
                        return GetAreaData();
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

        public override void OnClose()
        {
            StopHttpServer();
        }
    }
} 