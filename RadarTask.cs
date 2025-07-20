using System;
using ExileCore.PoEMemory.MemoryObjects;
using SharpDX;

namespace RadarMovement
{
    public class RadarTask
    {
        /// <summary>
        /// The target position in world coordinates
        /// </summary>
        public Vector2 WorldPosition { get; set; }

        /// <summary>
        /// The target position on screen (updated dynamically)
        /// </summary>
        public Vector2 ScreenPosition { get; set; }

        /// <summary>
        /// Type of task we are performing - different tasks have different logic
        /// </summary>
        public RadarTaskType Type { get; set; }

        /// <summary>
        /// How close we must get to complete this task (in world units)
        /// </summary>
        public float CompletionDistance { get; set; }

        /// <summary>
        /// Priority score - higher priority tasks are executed first
        /// </summary>
        public int Priority { get; set; }

        /// <summary>
        /// How many times we've attempted this task (for failure detection)
        /// </summary>
        public int AttemptCount { get; set; }

        /// <summary>
        /// Maximum attempts before considering the task failed
        /// </summary>
        public int MaxAttempts { get; set; }

        /// <summary>
        /// When this task was created
        /// </summary>
        public DateTime CreatedTime { get; set; }

        /// <summary>
        /// When this task was last attempted
        /// </summary>
        public DateTime LastAttemptTime { get; set; }

        /// <summary>
        /// The target entity (if applicable)
        /// </summary>
        public Entity TargetEntity { get; set; }

        /// <summary>
        /// Expected destination area (for transitions)
        /// </summary>
        public string ExpectedDestination { get; set; }

        /// <summary>
        /// Additional metadata for the task
        /// </summary>
        public string Metadata { get; set; }

        /// <summary>
        /// Whether this task has been completed
        /// </summary>
        public bool IsCompleted { get; set; }

        /// <summary>
        /// Whether this task has failed permanently
        /// </summary>
        public bool IsFailed { get; set; }

        /// <summary>
        /// Whether this task is a pathfinding waypoint (part of an A* path)
        /// </summary>
        public bool IsPathfindingWaypoint { get; set; } = false;

        public RadarTask(Vector2 position, RadarTaskType type, float completionDistance = 30f)
        {
            WorldPosition = position;
            Type = type;
            CompletionDistance = completionDistance;
            Priority = GetDefaultPriority(type);
            MaxAttempts = GetDefaultMaxAttempts(type);
            CreatedTime = DateTime.Now;
            LastAttemptTime = DateTime.MinValue;
            AttemptCount = 0;
            IsCompleted = false;
            IsFailed = false;
        }

        public RadarTask(Entity entity, RadarTaskType type, float completionDistance = 30f)
            : this(entity.GridPos, type, completionDistance)
        {
            TargetEntity = entity;
            Metadata = entity.Path;
            
            // Set expected destination for transitions
            if (type == RadarTaskType.ClickTransition || type == RadarTaskType.ClickWaypoint)
            {
                ExpectedDestination = DetermineDestination(entity);
            }
        }

        /// <summary>
        /// Check if this task is still valid (entity exists, not expired, etc.)
        /// </summary>
        public bool IsValid()
        {
            // Check if task has been completed or failed
            if (IsCompleted || IsFailed)
                return false;

            // Check if too many attempts
            if (AttemptCount >= MaxAttempts)
            {
                IsFailed = true;
                return false;
            }

            // Check if task is too old (5 minutes max)
            if (DateTime.Now - CreatedTime > TimeSpan.FromMinutes(5))
            {
                IsFailed = true;
                return false;
            }

            // Check if entity-based task still has valid entity
            if (TargetEntity != null && (!TargetEntity.IsValid || TargetEntity.Address == 0))
            {
                IsFailed = true;
                return false;
            }

            return true;
        }

        /// <summary>
        /// Record an attempt to execute this task
        /// </summary>
        public void RecordAttempt()
        {
            AttemptCount++;
            LastAttemptTime = DateTime.Now;
        }

        /// <summary>
        /// Calculate distance from player to this task's position
        /// </summary>
        public float GetDistanceFrom(Vector2 playerPosition)
        {
            return Vector2.Distance(playerPosition, WorldPosition);
        }

        /// <summary>
        /// Check if player is close enough to complete this task
        /// </summary>
        public bool IsPlayerCloseEnough(Vector2 playerPosition)
        {
            return GetDistanceFrom(playerPosition) <= CompletionDistance;
        }

        /// <summary>
        /// Get a human-readable description of this task
        /// </summary>
        public override string ToString()
        {
            var entityInfo = TargetEntity != null ? $" ({TargetEntity.Path})" : "";
            return $"{Type} at ({WorldPosition.X:F0}, {WorldPosition.Y:F0}){entityInfo} - Priority: {Priority}, Attempts: {AttemptCount}/{MaxAttempts}";
        }

        private int GetDefaultPriority(RadarTaskType type)
        {
            return type switch
            {
                RadarTaskType.ClickTransition => 100,    // Highest priority - area exits
                RadarTaskType.ClickWaypoint => 90,       // High priority - waypoints
                RadarTaskType.ClickPortal => 80,         // Medium-high - portals
                RadarTaskType.ClickDoor => 70,           // Medium - doors
                RadarTaskType.MoveToPosition => 50,      // Medium-low - movement
                RadarTaskType.Investigate => 30,         // Low - exploration
                _ => 40
            };
        }

        private int GetDefaultMaxAttempts(RadarTaskType type)
        {
            return type switch
            {
                RadarTaskType.ClickTransition => 5,      // Few attempts for transitions
                RadarTaskType.ClickWaypoint => 5,        // Few attempts for waypoints  
                RadarTaskType.ClickPortal => 3,          // Few attempts for portals
                RadarTaskType.ClickDoor => 3,            // Few attempts for doors
                RadarTaskType.MoveToPosition => 10,      // More attempts for movement
                RadarTaskType.Investigate => 2,          // Few attempts for investigation
                _ => 3
            };
        }

        private string DetermineDestination(Entity entity)
        {
            var path = entity.Path?.ToLowerInvariant() ?? "";
            
            // Try to determine destination based on entity path/name
            if (path.Contains("aqueduct"))
                return "The Aqueduct";
            else if (path.Contains("dried") || path.Contains("lake"))
                return "The Dried Lake";
            else if (path.Contains("town") || path.Contains("hideout"))
                return "Town/Hideout";
            
            return "Unknown";
        }
    }

    public enum RadarTaskType
    {
        /// <summary>
        /// Move to a specific position (basic movement)
        /// </summary>
        MoveToPosition,

        /// <summary>
        /// Click on a waypoint to travel
        /// </summary>
        ClickWaypoint,

        /// <summary>
        /// Click on an area transition
        /// </summary>
        ClickTransition,

        /// <summary>
        /// Click on a portal
        /// </summary>
        ClickPortal,

        /// <summary>
        /// Click on a door to open it
        /// </summary>
        ClickDoor,

        /// <summary>
        /// Move to investigate an area or entity
        /// </summary>
        Investigate
    }
} 