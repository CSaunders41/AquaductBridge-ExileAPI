using System;
using System.Collections.Generic;
using System.Linq;
using ExileCore;
using ExileCore.PoEMemory.Components;
using ExileCore.PoEMemory.MemoryObjects;
using ExileCore.Shared;
using ExileCore.Shared.Attributes;
using ExileCore.Shared.Interfaces;
using ExileCore.Shared.Nodes;
using SharpDX;
using Vector2 = System.Numerics.Vector2;
using Vector3 = System.Numerics.Vector3;

namespace RadarMovement
{
    public class RadarMovementSettings : ISettings
    {
        public ToggleNode Enable { get; set; } = new ToggleNode(true);
        
        [Menu("Show Path Line")]
        public ToggleNode ShowPathLine { get; set; } = new ToggleNode(true);
        
        [Menu("Path Line Color")]
        public ColorNode PathLineColor { get; set; } = new ColorNode(Color.Yellow);
        
        [Menu("Path Line Width")]
        public RangeNode<int> PathLineWidth { get; set; } = new RangeNode<int>(3, 1, 10);
        
        [Menu("Auto Move to Target")]
        public ToggleNode AutoMove { get; set; } = new ToggleNode(true);
        
        [Menu("Movement Speed (ms)")]
        public RangeNode<int> MovementDelay { get; set; } = new RangeNode<int>(100, 50, 500);
    }

    public class RadarMovement : BaseSettingsPlugin<RadarMovementSettings>
    {
        private Entity currentTarget = null;
        private List<Entity> availableTargets = new List<Entity>();
        private DateTime lastTargetScan = DateTime.MinValue;
        private DateTime lastMovement = DateTime.MinValue;

        public override bool Initialise()
        {
            return true;
        }

        public override void Render()
        {
            if (!Settings.Enable.Value) return;

            try
            {
                UpdateTargets();
                
                if (currentTarget != null && Settings.ShowPathLine.Value)
                {
                    DrawPathLine();
                }
                
                if (currentTarget != null && Settings.AutoMove.Value)
                {
                    MoveToTarget();
                }
            }
            catch (Exception ex)
            {
                DebugWindow.LogError($"RadarMovement error: {ex.Message}");
            }
        }

        private void UpdateTargets()
        {
            // Only scan for targets every 500ms to avoid performance issues
            if (DateTime.Now - lastTargetScan < TimeSpan.FromMilliseconds(500))
                return;

            lastTargetScan = DateTime.Now;
            availableTargets.Clear();

            if (!GameController.InGame || GameController.Player == null)
                return;

            var entities = GameController.Entities;
            var playerPos = GameController.Player.GridPos;

            foreach (var entity in entities)
            {
                if (entity?.IsValid != true || entity.Address == 0)
                    continue;

                // Look for waypoints, doors, and teleports (like Radar does)
                if (IsTargetEntity(entity))
                {
                    var distance = Vector2.Distance(
                        new Vector2(playerPos.X, playerPos.Y),
                        new Vector2(entity.GridPos.X, entity.GridPos.Y)
                    );
                    
                    // Only consider targets within reasonable range
                    if (distance < 200)
                    {
                        availableTargets.Add(entity);
                    }
                }
            }

            // Select the closest target
            if (availableTargets.Count > 0)
            {
                var playerPos2D = new Vector2(playerPos.X, playerPos.Y);
                currentTarget = availableTargets.OrderBy(t => 
                    Vector2.Distance(playerPos2D, new Vector2(t.GridPos.X, t.GridPos.Y))
                ).FirstOrDefault();
            }
            else
            {
                currentTarget = null;
            }
        }

        private bool IsTargetEntity(Entity entity)
        {
            var path = entity.Path?.ToLowerInvariant() ?? "";
            
            // Waypoints
            if (path.Contains("waypoint"))
                return true;
            
            // Doors and transitions
            if (path.Contains("door") || path.Contains("transition"))
                return true;
            
            // Teleports and portals
            if (path.Contains("teleport") || path.Contains("portal"))
                return true;
            
            // Area transitions
            if (path.Contains("areatransition"))
                return true;
            
            return false;
        }

        private void DrawPathLine()
        {
            if (!GameController.InGame || GameController.Player == null || currentTarget == null)
                return;

            var camera = GameController.IngameState.Camera;
            var playerPos = GameController.Player.GridPos;
            var targetPos = currentTarget.GridPos;

            // Convert Vector2 grid positions to Vector3 for WorldToScreen
            var playerPos3D = new Vector3(playerPos.X, playerPos.Y, 0);
            var targetPos3D = new Vector3(targetPos.X, targetPos.Y, 0);

            // Convert world positions to screen positions
            var playerScreen = camera.WorldToScreen(playerPos3D);
            var targetScreen = camera.WorldToScreen(targetPos3D);

            // Draw the line (like Radar does)
            if (IsValidScreenPosition(playerScreen) && IsValidScreenPosition(targetScreen))
            {
                Graphics.DrawLine(
                    playerScreen,
                    targetScreen,
                    Settings.PathLineWidth.Value,
                    Settings.PathLineColor.Value
                );
                
                // Draw a small circle at the target
                Graphics.DrawEllipse(targetScreen, new Vector2(10, 10), Settings.PathLineColor.Value, 2);
            }
        }

        private void MoveToTarget()
        {
            if (!GameController.InGame || GameController.Player == null || currentTarget == null)
                return;

            // Rate limit movement to avoid spam
            if (DateTime.Now - lastMovement < TimeSpan.FromMilliseconds(Settings.MovementDelay.Value))
                return;

            lastMovement = DateTime.Now;

            var playerPos = GameController.Player.GridPos;
            var targetPos = currentTarget.GridPos;
            
            // Check if we're close enough to the target
            var distance = Vector2.Distance(
                new Vector2(playerPos.X, playerPos.Y),
                new Vector2(targetPos.X, targetPos.Y)
            );

            if (distance < 30) // Close enough, find a new target
            {
                currentTarget = null;
                return;
            }

            // Convert target position to screen coordinates
            var camera = GameController.IngameState.Camera;
            var targetPos3D = new Vector3(targetPos.X, targetPos.Y, 0);
            var targetScreen = camera.WorldToScreen(targetPos3D);

            if (IsValidScreenPosition(targetScreen))
            {
                // Click to move (simple approach like Radar)
                Input.SetCursorPos(targetScreen);
                Mouse.LeftDown();
                System.Threading.Thread.Sleep(10);
                Mouse.LeftUp();
                DebugWindow.LogMsg($"Moving to target at distance {distance:F1}");
            }
        }

        private bool IsValidScreenPosition(Vector2 screenPos)
        {
            var windowRect = GameController.Window.GetWindowRectangle();
            return screenPos.X >= 0 && screenPos.X <= windowRect.Width &&
                   screenPos.Y >= 0 && screenPos.Y <= windowRect.Height;
        }
    }
} 