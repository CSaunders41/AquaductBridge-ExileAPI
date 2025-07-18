using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Drawing;
using ExileCore;
using ExileCore.PoEMemory.Components;
using ExileCore.PoEMemory.MemoryObjects;
using ExileCore.Shared.Enums;
using GameOffsets;
using System.Numerics;

namespace AqueductBridge
{
    public class DataExtractor
    {
        private readonly GameController _gameController;
        private readonly AqueductBridgeSettings _settings;

        public DataExtractor(GameController gameController, AqueductBridgeSettings settings)
        {
            _gameController = gameController;
            _settings = settings;
        }

        public async Task<object> GetFullGameDataAsync()
        {
            return await Task.Run(() =>
            {
                try
                {
                    var windowArea = GetWindowArea();
                    var terrainString = GetTerrainString();
                    var playerPos = GetPlayerPosition();
                    var entities = GetAwakeEntities();
                    var life = GetPlayerLife();
                    var areaLoading = GetAreaLoading();
                    var areaId = GetAreaId();

                    return new
                    {
                        WindowArea = windowArea,
                        terrain_string = terrainString,
                        player_pos = playerPos,
                        awake_entities = entities,
                        life = life,
                        area_loading = areaLoading,
                        area_id = areaId
                    };
                }
                catch (Exception ex)
                {
                    if (_settings.EnableDebugLogging.Value)
                    {
                        DebugWindow.LogError($"DataExtractor GetFullGameData error: {ex.Message}");
                    }
                    throw;
                }
            });
        }

        public async Task<object> GetInstanceDataAsync()
        {
            return await Task.Run(() =>
            {
                try
                {
                    var playerPos = GetPlayerPosition();
                    var entities = GetAwakeEntities();
                    var life = GetPlayerLife();
                    var areaLoading = GetAreaLoading();
                    var areaId = GetAreaId();

                    return new
                    {
                        player_pos = playerPos,
                        awake_entities = entities,
                        life = life,
                        area_loading = areaLoading,
                        area_id = areaId
                    };
                }
                catch (Exception ex)
                {
                    if (_settings.EnableDebugLogging.Value)
                    {
                        DebugWindow.LogError($"DataExtractor GetInstanceData error: {ex.Message}");
                    }
                    throw;
                }
            });
        }

        public async Task<object> GetPositionOnScreenAsync(int y, int x)
        {
            return await Task.Run(() =>
            {
                try
                {
                    var screenPos = GridToScreen(new Vector2(x, y));
                    return new int[] { (int)screenPos.X, (int)screenPos.Y };
                }
                catch (Exception ex)
                {
                    if (_settings.EnableDebugLogging.Value)
                    {
                        DebugWindow.LogError($"DataExtractor GetPositionOnScreen error: {ex.Message}");
                    }
                    throw;
                }
            });
        }

        private object GetWindowArea()
        {
            try
            {
                var windowRect = _gameController.Window.GetWindowRectangle();
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
                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogError($"GetWindowArea error: {ex.Message}");
                }
                return new { X = 0, Y = 0, Width = 1920, Height = 1080 };
            }
        }

        private string GetTerrainString()
        {
            try
            {
                var terrainData = _gameController.IngameState.Data.Terrain;
                if (terrainData == null || !terrainData.IsValid)
                {
                    return "";
                }

                var terrainBytes = terrainData.LayerMelee;
                if (terrainBytes == null || terrainBytes.Length == 0)
                {
                    return "";
                }

                var width = terrainData.NumCols;
                var height = terrainData.NumRows;
                
                if (width == 0 || height == 0)
                {
                    return "";
                }

                var sb = new StringBuilder();
                
                for (int y = 0; y < height; y++)
                {
                    for (int x = 0; x < width; x++)
                    {
                        var index = y * width + x;
                        if (index < terrainBytes.Length)
                        {
                            var terrainValue = terrainBytes[index];
                            
                            // Convert terrain value to aqueduct_runner format
                            // ExileApi terrain: 0 = passable, 1 = not passable
                            // aqueduct_runner: <50 = unwalkable, 50+ = walkable
                            byte convertedValue = (byte)(terrainValue == 0 ? 51 : 49);
                            
                            sb.Append(convertedValue.ToString());
                            if (x < width - 1) sb.Append(" ");
                        }
                    }
                    sb.Append("\r\n");
                }

                return sb.ToString();
            }
            catch (Exception ex)
            {
                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogError($"GetTerrainString error: {ex.Message}");
                }
                return "";
            }
        }

        private object GetPlayerPosition()
        {
            try
            {
                var player = _gameController.Player;
                if (player == null || !player.IsValid)
                {
                    return new { X = 0, Y = 0, Z = 0 };
                }

                var gridPos = player.GridPos;
                return new
                {
                    X = (int)gridPos.X,
                    Y = (int)gridPos.Y,
                    Z = (int)gridPos.Z
                };
            }
            catch (Exception ex)
            {
                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogError($"GetPlayerPosition error: {ex.Message}");
                }
                return new { X = 0, Y = 0, Z = 0 };
            }
        }

        private List<object> GetAwakeEntities()
        {
            try
            {
                var entities = new List<object>();
                
                if (_gameController.EntityListWrapper?.ValidEntitiesByType == null)
                {
                    return entities;
                }

                foreach (var entity in _gameController.EntityListWrapper.ValidEntitiesByType.Values.SelectMany(x => x))
                {
                    if (entity == null || !entity.IsValid) continue;

                    try
                    {
                        var gridPos = entity.GridPos;
                        var screenPos = GridToScreen(new Vector2(gridPos.X, gridPos.Y));
                        
                        // Get entity type
                        var entityType = GetEntityType(entity);
                        
                        // Get entity path
                        var path = entity.Path ?? "";
                        
                        // Get life component
                        var lifeComponent = entity.GetComponent<Life>();
                        var life = new
                        {
                            Health = new
                            {
                                Current = lifeComponent?.CurHP ?? 0,
                                Total = lifeComponent?.MaxHP ?? 0,
                                ReservedTotal = lifeComponent?.ReservedHP ?? 0
                            },
                            Mana = new
                            {
                                Current = lifeComponent?.CurMana ?? 0,
                                Total = lifeComponent?.MaxMana ?? 0,
                                ReservedTotal = lifeComponent?.ReservedMana ?? 0
                            },
                            EnergyShield = new
                            {
                                Current = lifeComponent?.CurES ?? 0,
                                Total = lifeComponent?.MaxES ?? 0,
                                ReservedTotal = lifeComponent?.ReservedES ?? 0
                            }
                        };

                        var entityData = new
                        {
                            GridPosition = new
                            {
                                X = (int)gridPos.X,
                                Y = (int)gridPos.Y,
                                Z = (int)gridPos.Z
                            },
                            location_on_screen = new
                            {
                                X = (int)screenPos.X,
                                Y = (int)screenPos.Y
                            },
                            EntityType = entityType,
                            Path = path,
                            life = life,
                            Id = entity.Id,
                            IsAlive = entity.IsAlive
                        };

                        entities.Add(entityData);
                    }
                    catch (Exception entityEx)
                    {
                        if (_settings.EnableDebugLogging.Value)
                        {
                            DebugWindow.LogError($"GetAwakeEntities entity error: {entityEx.Message}");
                        }
                        continue;
                    }
                }

                return entities;
            }
            catch (Exception ex)
            {
                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogError($"GetAwakeEntities error: {ex.Message}");
                }
                return new List<object>();
            }
        }

        private int GetEntityType(Entity entity)
        {
            try
            {
                // aqueduct_runner expects EntityType == 14 for monsters
                // We need to map ExileApi entity types to the expected values
                
                if (entity.Type == EntityType.Monster)
                {
                    return 14;
                }
                
                // Map other entity types as needed
                return (int)entity.Type;
            }
            catch
            {
                return 0;
            }
        }

        private object GetPlayerLife()
        {
            try
            {
                var player = _gameController.Player;
                if (player == null || !player.IsValid)
                {
                    return new
                    {
                        Health = new { Current = 0, Total = 0, ReservedTotal = 0 },
                        Mana = new { Current = 0, Total = 0, ReservedTotal = 0 },
                        EnergyShield = new { Current = 0, Total = 0, ReservedTotal = 0 }
                    };
                }

                var lifeComponent = player.GetComponent<Life>();
                if (lifeComponent == null)
                {
                    return new
                    {
                        Health = new { Current = 0, Total = 0, ReservedTotal = 0 },
                        Mana = new { Current = 0, Total = 0, ReservedTotal = 0 },
                        EnergyShield = new { Current = 0, Total = 0, ReservedTotal = 0 }
                    };
                }

                return new
                {
                    Health = new
                    {
                        Current = lifeComponent.CurHP,
                        Total = lifeComponent.MaxHP,
                        ReservedTotal = lifeComponent.ReservedHP
                    },
                    Mana = new
                    {
                        Current = lifeComponent.CurMana,
                        Total = lifeComponent.MaxMana,
                        ReservedTotal = lifeComponent.ReservedMana
                    },
                    EnergyShield = new
                    {
                        Current = lifeComponent.CurES,
                        Total = lifeComponent.MaxES,
                        ReservedTotal = lifeComponent.ReservedES
                    }
                };
            }
            catch (Exception ex)
            {
                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogError($"GetPlayerLife error: {ex.Message}");
                }
                return new
                {
                    Health = new { Current = 0, Total = 0, ReservedTotal = 0 },
                    Mana = new { Current = 0, Total = 0, ReservedTotal = 0 },
                    EnergyShield = new { Current = 0, Total = 0, ReservedTotal = 0 }
                };
            }
        }

        private bool GetAreaLoading()
        {
            try
            {
                return _gameController.IngameState.InGameStateObject.IsLoading;
            }
            catch
            {
                return false;
            }
        }

        private uint GetAreaId()
        {
            try
            {
                return _gameController.Area.CurrentArea?.Id ?? 0;
            }
            catch
            {
                return 0;
            }
        }

        private Vector2 GridToScreen(Vector2 gridPos)
        {
            try
            {
                var camera = _gameController.IngameState.Camera;
                var worldPos = new Vector3(gridPos.X, gridPos.Y, 0);
                var screenPos = camera.WorldToScreen(worldPos);
                return new Vector2(screenPos.X, screenPos.Y);
            }
            catch (Exception ex)
            {
                if (_settings.EnableDebugLogging.Value)
                {
                    DebugWindow.LogError($"GridToScreen error: {ex.Message}");
                }
                return new Vector2(0, 0);
            }
        }
    }
} 