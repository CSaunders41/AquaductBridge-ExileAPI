using System;
using System.Collections.Generic;

namespace RadarMovement.Utils
{
    public class EventBus
    {
        private static EventBus _instance;
        public static EventBus Instance => _instance ??= new EventBus();
        
        private readonly Dictionary<Type, List<Delegate>> _subscribers = new();

        public void Subscribe<T>(Action<T> handler)
        {
            var eventType = typeof(T);
            if (!_subscribers.ContainsKey(eventType))
                _subscribers[eventType] = new List<Delegate>();
            _subscribers[eventType].Add(handler);
        }

        public void Unsubscribe<T>(Action<T> handler)
        {
            if (_subscribers.TryGetValue(typeof(T), out var handlers))
            {
                handlers.Remove(handler);
            }
        }

        public void Publish<T>(T eventData)
        {
            if (_subscribers.TryGetValue(typeof(T), out var handlers))
            {
                foreach (var handler in handlers)
                {
                    try 
                    { 
                        ((Action<T>)handler)(eventData); 
                    }
                    catch (Exception ex)
                    {
                        // Log error but continue processing other handlers
                        System.Diagnostics.Debug.WriteLine($"EventBus error: {ex.Message}");
                    }
                }
            }
        }

        public void Clear()
        {
            _subscribers.Clear();
        }
    }

    // Event Types for RadarMovement
    public class AreaChangeEvent 
    { 
        public string NewArea { get; set; }
        public string PreviousArea { get; set; }
    }

    public class TargetFoundEvent 
    { 
        public ExileCore.PoEMemory.MemoryObjects.Entity Target { get; set; }
        public float Distance { get; set; }
        public RadarTaskType TaskType { get; set; }
    }

    public class TargetLostEvent 
    { 
        public ExileCore.PoEMemory.MemoryObjects.Entity Target { get; set; }
        public string Reason { get; set; }
    }

    public class MovementStartedEvent 
    { 
        public SharpDX.Vector2 Destination { get; set; }
        public RadarTaskType TaskType { get; set; }
    }

    public class MovementCompleteEvent 
    { 
        public SharpDX.Vector2 FinalPosition { get; set; }
        public bool Success { get; set; }
        public string Result { get; set; }
    }

    public class TaskQueuedEvent 
    { 
        public RadarTask Task { get; set; }
        public int QueueSize { get; set; }
    }

    public class TaskCompletedEvent 
    { 
        public RadarTask Task { get; set; }
        public bool Success { get; set; }
        public string Details { get; set; }
    }

    public class PlayerStuckEvent 
    { 
        public SharpDX.Vector2 Position { get; set; }
        public int StuckDuration { get; set; }
    }

    public class RenderEvent
    {
        public ExileCore.Graphics Graphics { get; set; }
        public RenderEvent(ExileCore.Graphics graphics) => Graphics = graphics;
    }
} 