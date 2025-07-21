using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using ExileCore;
using ExileCore.PoEMemory.Elements;
using SharpDX;

namespace RadarMovement.Utils
{
    public class AdvancedMouse
    {
        private const int MOUSEEVENTF_MOVE = 0x0001;
        private const int MOUSEEVENTF_LEFTDOWN = 0x02;
        private const int MOUSEEVENTF_LEFTUP = 0x04;
        private const int MOUSEEVENTF_RIGHTDOWN = 0x0008;
        private const int MOUSEEVENTF_RIGHTUP = 0x0010;
        private const int MOUSEEVENTF_MIDDLEDOWN = 0x0020;
        private const int MOUSEEVENTF_MIDDLEUP = 0x0040;
        
        private static readonly Random Random = new Random();
        private static readonly Queue<DateTime> RecentActions = new Queue<DateTime>();
        private const int MAX_ACTIONS_PER_SECOND = 2; // Very conservative
        
        private static GameController _gameController;

        [DllImport("user32.dll")]
        public static extern bool SetCursorPos(int x, int y);

        [DllImport("user32.dll")]
        private static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo);

        [DllImport("user32.dll")]
        public static extern bool GetCursorPos(out Point lpPoint);

        [StructLayout(LayoutKind.Sequential)]
        public struct Point
        {
            public int X;
            public int Y;

            public static implicit operator Vector2(Point point)
            {
                return new Vector2(point.X, point.Y);
            }
        }

        public static void Initialize(GameController gameController)
        {
            _gameController = gameController;
        }

        /// <summary>
        /// Human-like cursor movement with smooth interpolation
        /// </summary>
        public static async Task SetCursorPosHuman(Vector2 targetPos, bool applyRandomness = true)
        {
            if (IsActionRateLimited())
            {
                await Task.Delay(GetRandomDelay(200, 500));
                return;
            }

            var currentPos = GetCursorPosition();
            var distance = Vector2.Distance(currentPos, targetPos);
            
            // Apply small random offset for more human-like behavior
            if (applyRandomness)
            {
                targetPos.X += Random.Next(-3, 4);
                targetPos.Y += Random.Next(-3, 4);
            }
            
            // Validate target position is safe (not on UI)
            targetPos = GetSafeScreenPosition(targetPos);
            
            // Use smooth movement for longer distances
            if (distance > 50f)
            {
                await MoveCursorSmoothly(currentPos, targetPos);
            }
            else
            {
                SetCursorPos((int)targetPos.X, (int)targetPos.Y);
                await Task.Delay(GetRandomDelay(5, 15));
            }
            
            RecordAction();
        }

        /// <summary>
        /// Human-like click with proper timing and randomness
        /// </summary>
        public static async Task LeftClickHuman(int extraDelay = 0)
        {
            if (IsActionRateLimited())
            {
                await Task.Delay(GetRandomDelay(200, 500));
                return;
            }

            var clickDelay = GetRandomDelay(25, 75) + extraDelay;
            
            mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0);
            await Task.Delay(GetRandomDelay(10, 25)); // Human-like click duration
            mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
            
            await Task.Delay(clickDelay);
            RecordAction();
        }

        /// <summary>
        /// Combined cursor movement and click operation
        /// </summary>
        public static async Task SetCursorPosAndLeftClickHuman(Vector2 targetPos, int extraDelay = 0)
        {
            await SetCursorPosHuman(targetPos);
            await Task.Delay(GetRandomDelay(50, 150)); // Pause between move and click
            await LeftClickHuman(extraDelay);
        }

        /// <summary>
        /// Right click with human-like timing
        /// </summary>
        public static async Task RightClickHuman(int extraDelay = 0)
        {
            if (IsActionRateLimited())
            {
                await Task.Delay(GetRandomDelay(200, 500));
                return;
            }

            var clickDelay = GetRandomDelay(25, 75) + extraDelay;
            
            mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0);
            await Task.Delay(GetRandomDelay(10, 25));
            mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0);
            
            await Task.Delay(clickDelay);
            RecordAction();
        }

        /// <summary>
        /// Smooth cursor movement using Bezier curves for natural motion
        /// </summary>
        private static async Task MoveCursorSmoothly(Vector2 start, Vector2 end)
        {
            var distance = Vector2.Distance(start, end);
            var steps = Math.Max(10, (int)(distance / 20)); // Adaptive step count
            
            // Create control points for Bezier curve
            var controlPoint1 = Vector2.Lerp(start, end, 0.25f);
            var controlPoint2 = Vector2.Lerp(start, end, 0.75f);
            
            // Add slight randomness to control points for more natural curves
            controlPoint1.X += Random.Next(-20, 21);
            controlPoint1.Y += Random.Next(-20, 21);
            controlPoint2.X += Random.Next(-20, 21);
            controlPoint2.Y += Random.Next(-20, 21);

            for (int i = 0; i <= steps; i++)
            {
                var t = (float)i / steps;
                var pos = CalculateBezierPoint(t, start, controlPoint1, controlPoint2, end);
                
                SetCursorPos((int)pos.X, (int)pos.Y);
                
                // Variable delay for more natural movement
                var delay = Math.Max(1, (int)(10 - (distance / 100)));
                await Task.Delay(delay);
            }
        }

        /// <summary>
        /// Calculate point on cubic Bezier curve
        /// </summary>
        private static Vector2 CalculateBezierPoint(float t, Vector2 p0, Vector2 p1, Vector2 p2, Vector2 p3)
        {
            var u = 1 - t;
            var tt = t * t;
            var uu = u * u;
            var uuu = uu * u;
            var ttt = tt * t;

            var p = uuu * p0;
            p += 3 * uu * t * p1;
            p += 3 * u * tt * p2;
            p += ttt * p3;

            return p;
        }

        /// <summary>
        /// Get current cursor position
        /// </summary>
        public static Vector2 GetCursorPosition()
        {
            GetCursorPos(out var point);
            return new Vector2(point.X, point.Y);
        }

        /// <summary>
        /// Check if we're being rate limited to prevent kicks
        /// </summary>
        private static bool IsActionRateLimited()
        {
            var now = DateTime.Now;
            var oneSecondAgo = now.AddSeconds(-1);
            
            // Remove actions older than 1 second
            while (RecentActions.Count > 0 && RecentActions.Peek() < oneSecondAgo)
            {
                RecentActions.Dequeue();
            }
            
            return RecentActions.Count >= MAX_ACTIONS_PER_SECOND;
        }

        /// <summary>
        /// Record that we performed an action
        /// </summary>
        private static void RecordAction()
        {
            RecentActions.Enqueue(DateTime.Now);
        }

        /// <summary>
        /// Get random delay with human-like variation
        /// </summary>
        private static int GetRandomDelay(int min, int max)
        {
            return Random.Next(min, max + 1);
        }

        /// <summary>
        /// Find a safe screen position that avoids UI elements
        /// </summary>
        private static Vector2 GetSafeScreenPosition(Vector2 originalPos)
        {
            if (_gameController == null)
                return originalPos;

            try
            {
                var windowRect = _gameController.Window.GetWindowRectangle();
                var safeMargin = 100;
                
                // Keep within window bounds with safe margins
                var result = new Vector2(
                    Math.Max(safeMargin, Math.Min(windowRect.Width - safeMargin, originalPos.X)),
                    Math.Max(safeMargin, Math.Min(windowRect.Height - safeMargin, originalPos.Y))
                );

                // Check if position conflicts with UI elements
                if (IsUIBlocking(result))
                {
                    return FindAlternativeSafePosition(result, windowRect);
                }

                return result;
            }
            catch
            {
                return originalPos; // Fallback to original if analysis fails
            }
        }

        /// <summary>
        /// Check if UI elements are blocking the target position
        /// </summary>
        private static bool IsUIBlocking(Vector2 screenPos)
        {
            try
            {
                var ingameUI = _gameController?.IngameState?.IngameUi;
                if (ingameUI == null) return false;

                var checkRect = new RectangleF(screenPos.X - 50, screenPos.Y - 50, 100, 100);

                // Check common UI panels that might block movement
                var uiElements = new[]
                {
                    ingameUI.InventoryPanel,
                    ingameUI.StashElement,
                    ingameUI.TreePanel,
                    ingameUI.Atlas,
                    ingameUI.OpenLeftPanel,
                    ingameUI.OpenRightPanel
                };

                return uiElements.Any(panel => 
                    panel?.IsVisible == true && 
                    panel.GetClientRect().Intersects(checkRect));
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Find an alternative safe position when UI is blocking
        /// </summary>
        private static Vector2 FindAlternativeSafePosition(Vector2 originalPos, RectangleF windowRect)
        {
            var attempts = new[]
            {
                new Vector2(originalPos.X - 100, originalPos.Y),
                new Vector2(originalPos.X + 100, originalPos.Y),
                new Vector2(originalPos.X, originalPos.Y - 100),
                new Vector2(originalPos.X, originalPos.Y + 100),
                new Vector2(windowRect.Width / 2, windowRect.Height / 2) // Center as last resort
            };

            foreach (var attempt in attempts)
            {
                if (attempt.X >= 100 && attempt.X <= windowRect.Width - 100 &&
                    attempt.Y >= 100 && attempt.Y <= windowRect.Height - 100 &&
                    !IsUIBlocking(attempt))
                {
                    return attempt;
                }
            }

            return new Vector2(windowRect.Width / 2, windowRect.Height / 2);
        }

        /// <summary>
        /// Convert world position to safe screen position
        /// </summary>
        public static Vector2 WorldToValidScreenPosition(SharpDX.Vector3 worldPos)
        {
            if (_gameController == null)
                return Vector2.Zero;

            try
            {
                var camera = _gameController.Game.IngameState.Camera;
                var screenPos = camera.WorldToScreen(worldPos);
                var windowRect = _gameController.Window.GetWindowRectangle();
                
                var result = new Vector2(
                    screenPos.X + windowRect.X,
                    screenPos.Y + windowRect.Y
                );

                return GetSafeScreenPosition(result);
            }
            catch
            {
                return Vector2.Zero;
            }
        }

        /// <summary>
        /// Get current action rate for monitoring
        /// </summary>
        public static string GetActionRateInfo()
        {
            var now = DateTime.Now;
            var oneSecondAgo = now.AddSeconds(-1);
            
            // Clean old actions
            while (RecentActions.Count > 0 && RecentActions.Peek() < oneSecondAgo)
            {
                RecentActions.Dequeue();
            }

            var rateInfo = $"{RecentActions.Count}/{MAX_ACTIONS_PER_SECOND} actions/sec";
            var isLimited = RecentActions.Count >= MAX_ACTIONS_PER_SECOND;
            
            return isLimited ? $"{rateInfo} (LIMITED)" : rateInfo;
        }

        /// <summary>
        /// Emergency stop all mouse actions (useful for debugging)
        /// </summary>
        public static void EmergencyStop()
        {
            try
            {
                mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
                mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0);
                mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0);
            }
            catch
            {
                // Silent fail for emergency stop
            }
        }
    }
} 