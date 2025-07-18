using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using ExileCore;
using Newtonsoft.Json;

namespace AqueductBridge
{
    public class HttpServer
    {
        private readonly GameController _gameController;
        private readonly DataExtractor _dataExtractor;
        private readonly AqueductBridgeSettings _settings;
        private HttpListener _listener;
        private CancellationTokenSource _cancellationTokenSource;
        private bool _isRunning;

        public HttpServer(GameController gameController, DataExtractor dataExtractor, AqueductBridgeSettings settings)
        {
            _gameController = gameController;
            _dataExtractor = dataExtractor;
            _settings = settings;
        }

        public async Task StartAsync()
        {
            if (_isRunning) return;

            try
            {
                _listener = new HttpListener();
                _listener.Prefixes.Add($"http://127.0.0.1:{_settings.HttpServerPort.Value}/");
                _listener.Start();
                _isRunning = true;

                _cancellationTokenSource = new CancellationTokenSource();

                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogMsg($"AqueductBridge HTTP Server started on port {_settings.HttpServerPort.Value}");
                }

                await Task.Run(() => HandleRequestsAsync(_cancellationTokenSource.Token));
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"AqueductBridge HTTP Server failed to start: {ex.Message}");
                _isRunning = false;
            }
        }

        public void Stop()
        {
            if (!_isRunning) return;

            try
            {
                _cancellationTokenSource?.Cancel();
                _listener?.Stop();
                _listener?.Close();
                _isRunning = false;

                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogMsg("AqueductBridge HTTP Server stopped");
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"AqueductBridge HTTP Server stop error: {ex.Message}");
            }
        }

        private async Task HandleRequestsAsync(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested && _listener.IsListening)
            {
                try
                {
                    var contextTask = _listener.GetContextAsync();
                    var context = await contextTask;
                    _ = Task.Run(() => ProcessRequestAsync(context), cancellationToken);
                }
                catch (ObjectDisposedException)
                {
                    // Server is shutting down
                    break;
                }
                catch (Exception ex)
                {
                    if (_settings.EnableDebugLogging.Value)
                    {
                        DebugWindow.LogError($"AqueductBridge HTTP Server error: {ex.Message}");
                    }
                }
            }
        }

        private async Task ProcessRequestAsync(HttpListenerContext context)
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

                var responseJson = "";
                
                switch (request.Url.AbsolutePath.ToLower())
                {
                    case "/gameinfo":
                        if (request.QueryString["type"] == "full")
                        {
                            responseJson = await GetFullGameInfoAsync();
                        }
                        else
                        {
                            responseJson = await GetInstanceDataAsync();
                        }
                        break;
                    
                    case "/positiononscreen":
                        var y = request.QueryString["y"];
                        var x = request.QueryString["x"];
                        if (y != null && x != null && int.TryParse(y, out var yInt) && int.TryParse(x, out var xInt))
                        {
                            responseJson = await GetPositionOnScreenAsync(yInt, xInt);
                        }
                        else
                        {
                            response.StatusCode = 400;
                            responseJson = JsonConvert.SerializeObject(new { error = "Invalid coordinates" });
                        }
                        break;
                    
                    default:
                        response.StatusCode = 404;
                        responseJson = JsonConvert.SerializeObject(new { error = "Endpoint not found" });
                        break;
                }

                var buffer = Encoding.UTF8.GetBytes(responseJson);
                response.ContentType = "application/json";
                response.ContentLength64 = buffer.Length;
                await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
                response.Close();

                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogMsg($"AqueductBridge served: {request.Url.AbsolutePath}");
                }
            }
            catch (Exception ex)
            {
                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogError($"AqueductBridge request processing error: {ex.Message}");
                }
            }
        }

        private async Task<string> GetFullGameInfoAsync()
        {
            try
            {
                var gameData = await _dataExtractor.GetFullGameDataAsync();
                return JsonConvert.SerializeObject(gameData);
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"AqueductBridge GetFullGameInfo error: {ex.Message}");
                return JsonConvert.SerializeObject(new { error = ex.Message });
            }
        }

        private async Task<string> GetInstanceDataAsync()
        {
            try
            {
                var instanceData = await _dataExtractor.GetInstanceDataAsync();
                return JsonConvert.SerializeObject(instanceData);
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"AqueductBridge GetInstanceData error: {ex.Message}");
                return JsonConvert.SerializeObject(new { error = ex.Message });
            }
        }

        private async Task<string> GetPositionOnScreenAsync(int y, int x)
        {
            try
            {
                var screenPos = await _dataExtractor.GetPositionOnScreenAsync(y, x);
                return JsonConvert.SerializeObject(screenPos);
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"AqueductBridge GetPositionOnScreen error: {ex.Message}");
                return JsonConvert.SerializeObject(new { error = ex.Message });
            }
        }

        public bool IsRunning => _isRunning;
    }
} 