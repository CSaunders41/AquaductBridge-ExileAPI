using System;
using System.Collections;
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
using RadarMovement.Utils;

namespace RadarMovement
{
    public class RadarMovementSettings : ISettings
    {
        public ToggleNode Enable { get; set; } = new ToggleNode(true);
        
        [Menu("Movement Settings")]
        public MovementSettingsNode Movement { get; set; } = new MovementSettingsNode();
        
        [Menu("Visual Settings")]
        public VisualSettingsNode Visual { get; set; } = new VisualSettingsNode();
        
        [Menu("Debug Settings")]
        public DebugSettingsNode Debug { get; set; } = new DebugSettingsNode();
        
        [Menu("Pathfinding")]
        public PathfindingSettings Pathfinding { get; set; } = new PathfindingSettings();
    }

    public class MovementSettingsNode
    {
        [Menu("Auto Move to Target")]
        public ToggleNode AutoMove { get; set; } = new ToggleNode(true);
        
        [Menu("Movement Speed (ms)")]
        public RangeNode<int> MovementDelay { get; set; } = new RangeNode<int>(100, 50, 500);
        
        [Menu("Task Scan Interval (ms)")]
        public RangeNode<int> ScanInterval { get; set; } = new RangeNode<int>(500, 100, 2000);
        
        [Menu("Max Detection Range")]
        public RangeNode<int> MaxRange { get; set; } = new RangeNode<int>(200, 50, 500);
        
        [Menu("Completion Distance")]
        public RangeNode<float> CompletionDistance { get; set; } = new RangeNode<float>(30f, 10f, 100f);
    }

    public class VisualSettingsNode
    {
        [Menu("Show Path Line")]
        public ToggleNode ShowPathLine { get; set; } = new ToggleNode(true);
        
        [Menu("Path Line Color")]
        public ColorNode PathLineColor { get; set; } = new ColorNode(Color.Yellow);
        
        [Menu("Path Line Width")]
        public RangeNode<int> PathLineWidth { get; set; } = new RangeNode<int>(3, 1, 10);
        
        [Menu("Show Target Marker")]
        public ToggleNode ShowTargetMarker { get; set; } = new ToggleNode(true);
        
        [Menu("Show Task Queue")]
        public ToggleNode ShowTaskQueue { get; set; } = new ToggleNode(false);
    }

    public class DebugSettingsNode
    {
        [Menu("Show Debug Info")]
        public ToggleNode ShowDebug { get; set; } = new ToggleNode(false);
        
        [Menu("Show Detailed Logs")]
        public ToggleNode DetailedLogs { get; set; } = new ToggleNode(false);
        
        [Menu("Show Performance Stats")]
        public ToggleNode ShowPerformance { get; set; } = new ToggleNode(false);
        
        [Menu("Show Terrain Analysis")]
        public ToggleNode ShowTerrain { get; set; } = new ToggleNode(false);
        
        [Menu("Show Path Rays")]
        public ToggleNode ShowPathRays { get; set; } = new ToggleNode(false);
        
        [Menu("Terrain Check Range")]
        public RangeNode<float> TerrainCheckRange { get; set; } = new RangeNode<float>(100f, 50f, 300f);
        
        [Menu("Show Coroutine Status")]
        public ToggleNode ShowCoroutineStatus { get; set; } = new ToggleNode(false);
        
        [Menu("Area Transition Timeout (ms)")]
        public RangeNode<int> TransitionTimeout { get; set; } = new RangeNode<int>(10000, 5000, 30000);
    }

    [Submenu]
    public class PathfindingSettings
    {
        [Menu("Enable Advanced Pathfinding")]
        public ToggleNode EnableAdvancedPathfinding { get; set; } = new ToggleNode(true);
        
        [Menu("Use Waypoint-Based Navigation")]
        public ToggleNode UseWaypointNavigation { get; set; } = new ToggleNode(true);
        
        [Menu("Pathfinding Timeout (ms)")]
        public RangeNode<int> PathfindingTimeout { get; set; } = new RangeNode<int>(500, 100, 2000);
        
        [Menu("Min Distance for Pathfinding")]
        public RangeNode<float> MinPathfindingDistance { get; set; } = new RangeNode<float>(50f, 20f, 200f);
        
        [Menu("Max Waypoints Per Path")]
        public RangeNode<int> MaxWaypointsPerPath { get; set; } = new RangeNode<int>(10, 3, 20);
        
        [Menu("Prefer Bridge Routes")]
        public ToggleNode PreferBridgeRoutes { get; set; } = new ToggleNode(true);
        
        [Menu("Show Path Lines")]
        public ToggleNode ShowPathLines { get; set; } = new ToggleNode(true);
        
        [Menu("Show Waypoints")]
        public ToggleNode ShowWaypoints { get; set; } = new ToggleNode(true);
        
        [Menu("Path Line Color")]
        public ColorNode PathLineColor { get; set; } = new ColorNode(Color.Cyan);
        
        [Menu("Waypoint Color")]
        public ColorNode WaypointColor { get; set; } = new ColorNode(Color.Yellow);
    }

    public class RadarMovement : BaseSettingsPlugin<RadarMovementSettings>
    {
        // Task-based system
        private readonly Queue<RadarTask> taskQueue = new Queue<RadarTask>();
        private RadarTask currentTask = null;
        
        // Terrain analysis system
        private LineOfSight lineOfSight = null;
        
        // Advanced pathfinding system
        private AqueductPathfinder pathfinder = null;
        private bool pathfinderInitialized = false;
        private DateTime lastPathfindingUpdate = DateTime.MinValue;
        
        // Coroutine system
        private Coroutine mainProcessingCoroutine = null;
        private Coroutine areaTransitionCoroutine = null;
        private bool processingPaused = false;
        
        // Timing and state management
        private DateTime lastTaskScan = DateTime.MinValue;
        private DateTime lastMovement = DateTime.MinValue;
        private DateTime lastAreaChange = DateTime.MinValue;
        private string currentArea = "";
        private string expectedDestinationArea = "";
        
        // Debug and performance tracking
        private List<string> debugMessages = new List<string>();
        private DateTime lastPerformanceCheck = DateTime.MinValue;
        private int tasksCompletedThisSession = 0;
        private int tasksFailedThisSession = 0;
        private int targetsFilteredByTerrain = 0;
        private int areaTransitionsThisSession = 0;
        
        // State tracking
        private bool isTransitioning = false;
        private Vector2 lastPlayerPosition = Vector2.Zero;
        private DateTime lastPositionUpdate = DateTime.MinValue;
        
        public override bool Initialise()
        {
            try
            {
                // Initialize LineOfSight system
                lineOfSight = new LineOfSight(GameController);
                
                // Initialize pathfinding system
                pathfinder = new AqueductPathfinder(GameController, lineOfSight);
                InitializePathfinder();
                
                // Subscribe to EventBus events
                var eventBus = EventBus.Instance;
                eventBus.Subscribe<AreaChangeEvent>(OnAreaChange);
                eventBus.Subscribe<TargetFoundEvent>(OnTargetFound);
                eventBus.Subscribe<MovementCompleteEvent>(OnMovementComplete);
                eventBus.Subscribe<TaskCompletedEvent>(OnTaskCompleted);
                eventBus.Subscribe<PlayerStuckEvent>(OnPlayerStuck);

                // Start main processing coroutine
                StartMainProcessingCoroutine();

                AddDebugMessage("RadarMovement initialized with EventBus integration, LineOfSight, Pathfinding, and Coroutine processing");
                LogMessage("RadarMovement v4.0 - Advanced pathfinding system with A* navigation for Aqueducts initialized");
                
                return true;
            }
            catch (Exception ex)
            {
                LogError($"Failed to initialize RadarMovement: {ex.Message}");
                return false;
            }
        }

        public override void AreaChange()
        {
            try
            {
                var newArea = GameController.Area?.CurrentArea?.DisplayName ?? "Unknown";
                var previousArea = currentArea;
                currentArea = newArea;
                lastAreaChange = DateTime.Now;

                // Handle area transition with coroutine
                if (isTransitioning)
                {
                    AddDebugMessage($"Expected area transition: {previousArea} -> {newArea}");
                    
                    // Reinitialize pathfinder for new area
                    InitializePathfinder();
                    
                    // Start grace period coroutine to handle post-transition cleanup
                    StartAreaTransitionGracePeriod();
                    
                    // Publish area change event
                    EventBus.Instance.Publish(new AreaChangeEvent { 
                        NewArea = newArea, 
                        PreviousArea = previousArea 
                    });
                }
                else
                {
                    // Unexpected area change - pause processing and reset state
                    AddDebugMessage($"Unexpected area change: {previousArea} -> {newArea}");
                    PauseProcessing("Unexpected area change");
                    ResetState("Unexpected area change");
                    
                    // Resume processing after a brief pause
                    System.Threading.Tasks.Task.Delay(2000).ContinueWith(_ => 
                        ResumeProcessing("Recovery from unexpected area change"));
                }

                base.AreaChange();
            }
            catch (Exception ex)
            {
                LogError($"Error in AreaChange: {ex.Message}");
            }
        }

        private void StartAreaTransitionGracePeriod()
        {
            try
            {
                // Stop any existing area transition coroutine
                if (areaTransitionCoroutine != null)
                {
                    Core.ParallelRunner.FindByName("RadarMovement_AreaTransition")?.Done = true;
                }

                // Start new grace period coroutine
                areaTransitionCoroutine = new Coroutine(PostAreaTransitionGracePeriod(), this, "RadarMovement_AreaTransition");
                Core.ParallelRunner.Run(areaTransitionCoroutine);
            }
            catch (Exception ex)
            {
                LogError($"Error starting area transition grace period: {ex.Message}");
                // Fallback - just clear the transition flag
                isTransitioning = false;
                processingPaused = false;
            }
        }

        public override void Render()
        {
            if (!Settings.Enable.Value) return;

            try
            {
                // Only handle visualization in Render - main processing is now in coroutines
                if (Settings.Visual.ShowPathLine.Value || Settings.Visual.ShowTaskQueue.Value)
                {
                    RenderVisuals();
                }
                
                if (Settings.Debug.ShowDebug.Value)
                {
                    RenderDebugInfo();
                }
                
                // Publish render event for other components
                EventBus.Instance.Publish(new RenderEvent(Graphics));
            }
            catch (Exception ex)
            {
                LogError($"RadarMovement render error: {ex.Message}");
                AddDebugMessage($"Render error: {ex.Message}");
            }
        }

        #region Pathfinding System

        private void InitializePathfinder()
        {
            try
            {
                if (pathfinder != null && pathfinder.InitializeTerrain())
                {
                    pathfinderInitialized = true;
                    lastPathfindingUpdate = DateTime.Now;
                    AddDebugMessage("Pathfinder initialized with Aqueduct terrain data");
                }
                else
                {
                    pathfinderInitialized = false;
                    AddDebugMessage("Pathfinder initialization failed - terrain data unavailable");
                }
            }
            catch (Exception ex)
            {
                LogError($"Error initializing pathfinder: {ex.Message}");
                pathfinderInitialized = false;
            }
        }

        private bool ShouldUsePathfinding(Vector3 start, Vector3 target)
        {
            if (!Settings.Pathfinding.EnableAdvancedPathfinding.Value || !pathfinderInitialized)
                return false;
                
            var distance = Vector3.Distance(start, target);
            return distance >= Settings.Pathfinding.MinPathfindingDistance.Value;
        }

        private async Task<PathfindingResult> FindPathToTargetAsync(Vector3 target)
        {
            try
            {
                if (!pathfinderInitialized || GameController.Player == null)
                    return new PathfindingResult { Success = false, FailureReason = "Pathfinder not ready" };

                var playerPos = new Vector3(
                    GameController.Player.Pos.X,
                    GameController.Player.Pos.Y,
                    GameController.Player.Pos.Z
                );

                var cancellationToken = new CancellationTokenSource(Settings.Pathfinding.PathfindingTimeout.Value).Token;
                return await pathfinder.FindPathAsync(playerPos, target, cancellationToken);
            }
            catch (Exception ex)
            {
                return new PathfindingResult { Success = false, FailureReason = $"Pathfinding error: {ex.Message}" };
            }
        }

        private void AddPathfindingTasks(PathfindingResult pathResult)
        {
            if (!pathResult.Success || pathResult.WorldPath.Count == 0)
                return;

            try
            {
                // Add movement tasks for each waypoint in the path
                var waypointsToAdd = Math.Min(pathResult.WorldPath.Count, Settings.Pathfinding.MaxWaypointsPerPath.Value);
                
                for (int i = 0; i < waypointsToAdd; i++)
                {
                    var waypoint = pathResult.WorldPath[i];
                    var screenPos = Camera.WorldToScreen(waypoint);
                    
                    if (screenPos != Vector2.Zero)
                    {
                        var taskType = (i == waypointsToAdd - 1) ? RadarTaskType.ClickTarget : RadarTaskType.ClickWaypoint;
                        var priority = 10 - i; // Earlier waypoints get higher priority
                        
                        var task = new RadarTask(
                            worldPosition: waypoint,
                            screenPosition: screenPos,
                            type: taskType,
                            priority: priority
                        )
                        {
                            Description = $"Pathfinding waypoint {i + 1}/{waypointsToAdd}",
                            IsPathfindingWaypoint = true
                        };
                        
                        taskQueue.Enqueue(task);
                    }
                }
                
                AddDebugMessage($"Added {waypointsToAdd} pathfinding waypoints to task queue");
            }
            catch (Exception ex)
            {
                LogError($"Error adding pathfinding tasks: {ex.Message}");
            }
        }

        #endregion

        #region Coroutine System

        private void StartMainProcessingCoroutine()
        {
            try
            {
                if (mainProcessingCoroutine != null)
                {
                    // Stop existing coroutine
                    Core.ParallelRunner.FindByName("RadarMovement_MainProcessing")?.Done = true;
                }

                mainProcessingCoroutine = new Coroutine(MainProcessingCoroutine(), this, "RadarMovement_MainProcessing");
                Core.ParallelRunner.Run(mainProcessingCoroutine);
                
                AddDebugMessage("Main processing coroutine started");
            }
            catch (Exception ex)
            {
                LogError($"Error starting main processing coroutine: {ex.Message}");
            }
        }

        private IEnumerator MainProcessingCoroutine()
        {
            while (true)
            {
                try
                {
                    // ========================================
                    // SECTION 1: SAFETY CHECKS
                    // ========================================
                    if (!Settings.Enable.Value || 
                        !GameController.InGame || 
                        GameController.Player == null || 
                        !GameController.Player.IsAlive ||
                        GameController.IsLoading ||
                        processingPaused)
                    {
                        yield return new WaitTime(100);
                        continue;
                    }

                    // ========================================
                    // SECTION 2: PERFORMANCE STATS UPDATE
                    // ========================================
                    UpdatePerformanceStats();

                    // ========================================
                    // SECTION 3: TASK QUEUE PROCESSING
                    // ========================================
                    if (!isTransitioning) // Don't process tasks during area transitions
                    {
                        ProcessTaskQueue();
                    }
                    else
                    {
                        // During transitions, just clean up invalid tasks
                        CleanupTaskQueue();
                    }

                    // ========================================
                    // SECTION 4: WAIT FOR NEXT CYCLE
                    // ========================================
                    var waitTime = isTransitioning ? 200 : Settings.Movement.MovementDelay.Value;
                    yield return new WaitTime(waitTime);
                }
                catch (Exception ex)
                {
                    LogError($"Error in main processing coroutine: {ex.Message}");
                    AddDebugMessage($"Main coroutine error: {ex.Message}");
                    yield return new WaitTime(1000); // Wait longer on errors
                }
            }
        }

        private IEnumerator PostAreaTransitionGracePeriod()
        {
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            var timeoutMs = Settings.Debug.TransitionTimeout.Value; // Configurable timeout
            const int CHECK_INTERVAL_MS = 200;

            AddDebugMessage($"Starting post-transition grace period for area: {expectedDestinationArea}");

            while (stopwatch.ElapsedMilliseconds < timeoutMs)
            {
                try
                {
                    // Check if we're in the expected area
                    var currentAreaName = GameController.Area?.CurrentArea?.DisplayName ?? "Unknown";
                    
                    if (!string.IsNullOrEmpty(expectedDestinationArea) && 
                        currentAreaName.Contains(expectedDestinationArea.Split('/')[0]) || // Handle area variations
                        currentAreaName == expectedDestinationArea)
                    {
                        // Successfully reached expected destination
                        AddDebugMessage($"Transition successful: Now in {currentAreaName}");
                        areaTransitionsThisSession++;
                        break;
                    }

                    // Check if game is stable (not loading, player exists)
                    if (GameController.InGame && 
                        GameController.Player != null && 
                        !GameController.IsLoading)
                    {
                        // Game is stable but might be unexpected area - continue anyway
                        AddDebugMessage($"Game stable in area: {currentAreaName}");
                        break;
                    }

                    yield return new WaitTime(CHECK_INTERVAL_MS);
                }
                catch (Exception ex)
                {
                    LogError($"Error in grace period: {ex.Message}");
                    yield return new WaitTime(CHECK_INTERVAL_MS);
                }
            }

            // Grace period complete - resume normal processing
            isTransitioning = false;
            processingPaused = false;
            expectedDestinationArea = "";
            
            AddDebugMessage($"Grace period complete. Resuming normal processing.");
            
            // Clear old tasks that might be invalid in the new area
            ClearInvalidTasks("Area transition complete");

            stopwatch.Stop();
        }

        private void PauseProcessing(string reason)
        {
            processingPaused = true;
            AddDebugMessage($"Processing paused: {reason}");
        }

        private void ResumeProcessing(string reason)
        {
            processingPaused = false;
            AddDebugMessage($"Processing resumed: {reason}");
        }

        #endregion

        #region Event Handlers

        private void OnAreaChange(AreaChangeEvent evt)
        {
            AddDebugMessage($"EventBus: Area changed to {evt.NewArea}");
        }

        private void OnTargetFound(TargetFoundEvent evt)
        {
            AddDebugMessage($"EventBus: Target found - {evt.TaskType} at distance {evt.Distance:F1}");
        }

        private void OnMovementComplete(MovementCompleteEvent evt)
        {
            AddDebugMessage($"EventBus: Movement complete - {evt.Result}");
            
            if (currentTask != null && evt.Success)
            {
                CompleteCurrentTask("Movement successful");
            }
        }

        private void OnTaskCompleted(TaskCompletedEvent evt)
        {
            if (evt.Success)
            {
                tasksCompletedThisSession++;
                AddDebugMessage($"Task completed: {evt.Task.Type}");
            }
            else
            {
                tasksFailedThisSession++;
                AddDebugMessage($"Task failed: {evt.Task.Type} - {evt.Details}");
            }
        }

        private void OnPlayerStuck(PlayerStuckEvent evt)
        {
            AddDebugMessage($"Player stuck at ({evt.Position.X:F0}, {evt.Position.Y:F0}) for {evt.StuckDuration}s");
            ResetState("Player stuck");
        }

        #endregion

        #region Task Management

        private void ProcessTaskQueue()
        {
            // Check if we should scan for new tasks
            if (ShouldScanForTasks())
            {
                ScanForNewTasks();
            }

            // Process current task or get next one
            if (currentTask == null || !currentTask.IsValid())
            {
                GetNextTask();
            }

            // Execute current task
            if (currentTask != null && Settings.Movement.AutoMove.Value)
            {
                ExecuteCurrentTask();
            }

            // Clean up completed/failed tasks periodically
            CleanupTaskQueue();
        }

        private bool ShouldScanForTasks()
        {
            var scanInterval = TimeSpan.FromMilliseconds(Settings.Movement.ScanInterval.Value);
            return DateTime.Now - lastTaskScan >= scanInterval;
        }

        private void ScanForNewTasks()
        {
            if (!GameController.InGame || GameController.Player == null)
                return;

            lastTaskScan = DateTime.Now;
            var playerPos = GameController.Player.GridPos;
            var playerPos2D = new Vector2(playerPos.X, playerPos.Y);
            var maxRange = Settings.Movement.MaxRange.Value;
            
            var entities = GameController.Entities;
            var newTasks = new List<RadarTask>();

            foreach (var entity in entities)
            {
                if (entity?.IsValid != true || entity.Address == 0)
                    continue;

                // Check if this entity is a valid target
                var taskType = GetTaskTypeForEntity(entity);
                if (taskType == null)
                    continue;

                var distance = Vector2.Distance(playerPos2D, new Vector2(entity.GridPos.X, entity.GridPos.Y));
                
                // Only consider targets within range
                if (distance > maxRange)
                    continue;

                // Check if we already have a task for this entity
                if (HasTaskForEntity(entity))
                    continue;

                // Check terrain accessibility (critical for Aqueduct navigation)
                var targetPos = new Vector2(entity.GridPos.X, entity.GridPos.Y);
                var targetWorld = new Vector3(entity.GridPos.X, entity.GridPos.Y, entity.GridPos.Z);
                var pathStatus = lineOfSight?.CheckPath(playerPos2D, targetPos) ?? PathStatus.Clear;
                
                // Advanced pathfinding for blocked or complex routes
                if (pathStatus == PathStatus.Blocked && pathfinderInitialized && 
                    ShouldUsePathfinding(new Vector3(playerPos.X, playerPos.Y, playerPos.Z), targetWorld))
                {
                    // Try pathfinding for blocked targets
                    var pathResult = FindPathToTargetAsync(targetWorld).Result;
                    
                    if (pathResult.Success && pathResult.WorldPath.Count > 0)
                    {
                        // Target is reachable via pathfinding - add pathfinding tasks
                        AddPathfindingTasks(pathResult);
                        AddDebugMessage($"Added pathfinding route to {taskType}: {pathResult.WorldPath.Count} waypoints");
                        continue; // Don't add the direct task since we're using pathfinding
                    }
                    else
                    {
                        // Even pathfinding failed - filter this target
                        targetsFilteredByTerrain++;
                        if (Settings.Debug.DetailedLogs.Value)
                        {
                            AddDebugMessage($"Filtered unreachable target: {taskType} - {pathResult.FailureReason}");
                        }
                        continue;
                    }
                }
                else if (pathStatus == PathStatus.Blocked)
                {
                    // No pathfinding available, filter blocked targets
                    targetsFilteredByTerrain++;
                    if (Settings.Debug.DetailedLogs.Value)
                    {
                        AddDebugMessage($"Filtered blocked target: {taskType} at {targetPos}");
                    }
                    continue;
                }

                // For accessible targets or when pathfinding is disabled
                var priorityModifier = pathStatus == PathStatus.Dashable ? -10 : 0;

                // Check if we should use pathfinding even for clear paths (long distance optimization)
                if (pathStatus == PathStatus.Clear && pathfinderInitialized && 
                    ShouldUsePathfinding(new Vector3(playerPos.X, playerPos.Y, playerPos.Z), targetWorld) &&
                    Settings.Pathfinding.UseWaypointNavigation.Value)
                {
                    var pathResult = FindPathToTargetAsync(targetWorld).Result;
                    if (pathResult.Success && pathResult.WorldPath.Count > 1) // Only use if it provides a better route
                    {
                        AddPathfindingTasks(pathResult);
                        AddDebugMessage($"Added optimized pathfinding route to {taskType}: {pathResult.WorldPath.Count} waypoints");
                        continue;
                    }
                }

                // Create standard direct movement task
                var task = new RadarTask(entity, taskType.Value, Settings.Movement.CompletionDistance.Value);
                task.Priority += priorityModifier; // Reduce priority for dashable targets
                
                // Add terrain analysis metadata
                task.Metadata += $" | Terrain: {pathStatus}";
                
                newTasks.Add(task);

                // Publish target found event
                EventBus.Instance.Publish(new TargetFoundEvent
                {
                    Target = entity,
                    Distance = distance,
                    TaskType = taskType.Value
                });
            }

            // Add new tasks to queue, sorted by priority
            foreach (var task in newTasks.OrderByDescending(t => t.Priority))
            {
                taskQueue.Enqueue(task);
                
                EventBus.Instance.Publish(new TaskQueuedEvent
                {
                    Task = task,
                    QueueSize = taskQueue.Count
                });
            }

            if (newTasks.Count > 0)
            {
                AddDebugMessage($"Added {newTasks.Count} new tasks to queue");
            }
        }

        private RadarTaskType? GetTaskTypeForEntity(Entity entity)
        {
            var path = entity.Path?.ToLowerInvariant() ?? "";

            // Waypoints - highest priority for Aqueduct farming
            if (path.Contains("waypoint"))
                return RadarTaskType.ClickWaypoint;

            // Area transitions - critical for zone navigation
            if (path.Contains("areatransition") || path.Contains("transition"))
                return RadarTaskType.ClickTransition;

            // Portals - for returning to town/hideout
            if (path.Contains("portal"))
                return RadarTaskType.ClickPortal;

            // Doors - for opening passages
            if (path.Contains("door"))
                return RadarTaskType.ClickDoor;

            // Teleports - various teleport mechanics
            if (path.Contains("teleport"))
                return RadarTaskType.ClickTransition;

            return null; // Not a target entity
        }

        private bool HasTaskForEntity(Entity entity)
        {
            // Check current task
            if (currentTask?.TargetEntity?.Address == entity.Address)
                return true;

            // Check queued tasks
            foreach (var task in taskQueue)
            {
                if (task.TargetEntity?.Address == entity.Address)
                    return true;
            }

            return false;
        }

        private void GetNextTask()
        {
            // Complete current task if it exists
            if (currentTask != null)
            {
                CompleteCurrentTask("Getting next task");
            }

            // Get next valid task from queue
            while (taskQueue.Count > 0)
            {
                var nextTask = taskQueue.Dequeue();
                
                if (nextTask.IsValid())
                {
                    currentTask = nextTask;
                    AddDebugMessage($"Started new task: {nextTask}");
                    return;
                }
                else
                {
                    // Task is invalid, publish failure event
                    EventBus.Instance.Publish(new TaskCompletedEvent
                    {
                        Task = nextTask,
                        Success = false,
                        Details = "Task invalid when dequeued"
                    });
                }
            }

            // No valid tasks available
            currentTask = null;
        }

        private void ExecuteCurrentTask()
        {
            if (currentTask == null || !GameController.InGame || GameController.Player == null)
                return;

            // Check movement delay
            if (DateTime.Now - lastMovement < TimeSpan.FromMilliseconds(Settings.Movement.MovementDelay.Value))
                return;

            var playerPos = GameController.Player.GridPos;
            var playerPos2D = new Vector2(playerPos.X, playerPos.Y);

            // Check if we're close enough to complete the task
            if (currentTask.IsPlayerCloseEnough(playerPos2D))
            {
                PerformTaskAction(currentTask);
                return;
            }

            // Move towards the task
            MoveTowardsTask(currentTask, playerPos2D);
        }

        private void PerformTaskAction(RadarTask task)
        {
            try
            {
                var camera = GameController.IngameState.Camera;
                var targetPos3D = new Vector3(task.WorldPosition.X, task.WorldPosition.Y, 0);
                var screenPos = camera.WorldToScreen(targetPos3D);

                if (IsValidScreenPosition(screenPos))
                {
                    // Record the attempt
                    task.RecordAttempt();
                    
                    // Perform the click
                    Input.SetCursorPos(screenPos);
                    Mouse.LeftDown();
                    // Note: In coroutine context, we don't use Thread.Sleep - timing is handled by coroutine delays
                    Mouse.LeftUp();

                    lastMovement = DateTime.Now;

                    // Set transition flag for transition tasks
                    if (task.Type == RadarTaskType.ClickTransition || task.Type == RadarTaskType.ClickWaypoint)
                    {
                        isTransitioning = true;
                        expectedDestinationArea = task.ExpectedDestination ?? "Unknown";
                        PauseProcessing($"Initiating area transition to {expectedDestinationArea}");
                        AddDebugMessage($"Initiated transition to: {expectedDestinationArea}");
                    }

                    AddDebugMessage($"Performed action for task: {task.Type}");
                    
                    // Publish movement started event
                    EventBus.Instance.Publish(new MovementStartedEvent
                    {
                        Destination = task.WorldPosition,
                        TaskType = task.Type
                    });

                    // Complete the task
                    CompleteCurrentTask("Action performed successfully");
                }
                else
                {
                    AddDebugMessage($"Invalid screen position for task: {task}");
                    task.RecordAttempt();
                }
            }
            catch (Exception ex)
            {
                LogError($"Error performing task action: {ex.Message}");
                task.RecordAttempt();
            }
        }

        private void MoveTowardsTask(RadarTask task, Vector2 playerPos)
        {
            try
            {
                var targetWorldPos = task.WorldPosition;
                
                // Check if we need to find an alternate route
                var pathStatus = lineOfSight?.CheckPath(playerPos, targetWorldPos) ?? PathStatus.Clear;
                Vector2 actualTarget = targetWorldPos;

                if (pathStatus == PathStatus.Blocked)
                {
                    // Try to find a walkable position closer to the target
                    var alternatePos = lineOfSight?.FindClosestWalkablePosition(targetWorldPos, Settings.Debug.TerrainCheckRange.Value);
                    if (alternatePos.HasValue)
                    {
                        actualTarget = alternatePos.Value;
                        AddDebugMessage($"Using alternate route: blocked -> walkable at {actualTarget}");
                    }
                    else
                    {
                        AddDebugMessage($"No alternate route found for blocked target");
                        task.RecordAttempt(); // Count this as an attempt since we couldn't find a route
                        return;
                    }
                }

                var camera = GameController.IngameState.Camera;
                var targetPos3D = new Vector3(actualTarget.X, actualTarget.Y, 0);
                var screenPos = camera.WorldToScreen(targetPos3D);

                if (IsValidScreenPosition(screenPos))
                {
                    Input.SetCursorPos(screenPos);
                    Mouse.LeftDown();
                    // Note: In coroutine context, we don't use Thread.Sleep - timing is handled by coroutine delays
                    Mouse.LeftUp();

                    lastMovement = DateTime.Now;
                    lastPlayerPosition = playerPos;
                    lastPositionUpdate = DateTime.Now;

                    var statusInfo = pathStatus != PathStatus.Clear ? $" ({pathStatus})" : "";
                    AddDebugMessage($"Moving towards: {task.Type} at distance {task.GetDistanceFrom(playerPos):F1}{statusInfo}");
                }
            }
            catch (Exception ex)
            {
                LogError($"Error moving towards task: {ex.Message}");
                task.RecordAttempt();
            }
        }

        private void CompleteCurrentTask(string reason)
        {
            if (currentTask == null)
                return;

            currentTask.IsCompleted = true;
            
            EventBus.Instance.Publish(new TaskCompletedEvent
            {
                Task = currentTask,
                Success = true,
                Details = reason
            });

            AddDebugMessage($"Completed task: {currentTask.Type} - {reason}");
            currentTask = null;
        }

        private void CleanupTaskQueue()
        {
            // Remove invalid tasks from queue periodically
            var cleanupInterval = TimeSpan.FromSeconds(30);
            if (DateTime.Now - lastPerformanceCheck < cleanupInterval)
                return;

            var originalCount = taskQueue.Count;
            var validTasks = new Queue<RadarTask>();

            while (taskQueue.Count > 0)
            {
                var task = taskQueue.Dequeue();
                if (task.IsValid())
                {
                    validTasks.Enqueue(task);
                }
            }

            // Replace queue with valid tasks
            while (validTasks.Count > 0)
            {
                taskQueue.Enqueue(validTasks.Dequeue());
            }

            if (originalCount != taskQueue.Count)
            {
                AddDebugMessage($"Cleaned up {originalCount - taskQueue.Count} invalid tasks");
            }
        }

        private void ClearInvalidTasks(string reason)
        {
            var clearedCount = taskQueue.Count;
            taskQueue.Clear();
            currentTask = null;
            
            if (clearedCount > 0)
            {
                AddDebugMessage($"Cleared {clearedCount} tasks: {reason}");
            }
        }

        #endregion

        #region Utility Methods

        private void ResetState(string reason)
        {
            try
            {
                ClearInvalidTasks(reason);
                isTransitioning = false;
                lastPlayerPosition = Vector2.Zero;
                lastPositionUpdate = DateTime.MinValue;
                
                AddDebugMessage($"State reset: {reason}");
                LogMessage($"RadarMovement state reset: {reason}");
            }
            catch (Exception ex)
            {
                LogError($"Error resetting state: {ex.Message}");
            }
        }

        private void UpdatePerformanceStats()
        {
            var now = DateTime.Now;
            if (now - lastPerformanceCheck < TimeSpan.FromSeconds(5))
                return;

            lastPerformanceCheck = now;

            if (Settings.Debug.ShowPerformance.Value)
            {
                var totalTasks = tasksCompletedThisSession + tasksFailedThisSession;
                var successRate = totalTasks > 0 ? (float)tasksCompletedThisSession / totalTasks * 100f : 0f;
                
                var coroutineStatus = mainProcessingCoroutine?.IsDone == false ? "Running" : "Stopped";
                var processingStatus = processingPaused ? "Paused" : "Active";
                var transitionStatus = isTransitioning ? $"Transitioning to {expectedDestinationArea}" : "Stable";
                
                AddDebugMessage($"Performance: {tasksCompletedThisSession}/{totalTasks} tasks ({successRate:F1}% success), {areaTransitionsThisSession} transitions");
                AddDebugMessage($"Status: Coroutine {coroutineStatus}, Processing {processingStatus}, {transitionStatus}");
                AddDebugMessage($"Filtered: {targetsFilteredByTerrain} by terrain, Queue: {taskQueue.Count} tasks");
            }
        }

        private void AddDebugMessage(string message)
        {
            if (!Settings.Debug.ShowDebug.Value && !Settings.Debug.DetailedLogs.Value)
                return;

            var timestampedMessage = $"{DateTime.Now:HH:mm:ss} - {message}";
            debugMessages.Add(timestampedMessage);
            
            // Keep only recent messages
            if (debugMessages.Count > 15)
            {
                debugMessages.RemoveAt(0);
            }

            if (Settings.Debug.DetailedLogs.Value)
            {
                LogMessage(message);
            }
        }

        #endregion

        #region Rendering

        private void RenderVisuals()
        {
            if (!GameController.InGame || GameController.Player == null)
                return;

            try
            {
                if (Settings.Visual.ShowPathLine.Value && currentTask != null)
                {
                    DrawTaskLine(currentTask);
                }

                if (Settings.Visual.ShowTaskQueue.Value)
                {
                    DrawTaskQueue();
                }

                if (Settings.Visual.ShowTargetMarker.Value && currentTask != null)
                {
                    DrawTargetMarker(currentTask);
                }

                // Terrain analysis visualization
                if (Settings.Debug.ShowPathRays.Value && lineOfSight != null)
                {
                    DrawLineOfSightRays();
                }

                if (Settings.Debug.ShowTerrain.Value && GameController.Player != null)
                {
                    DrawTerrainAnalysis();
                }

                // Pathfinding visualization
                if (Settings.Pathfinding.ShowPathLines.Value && pathfinderInitialized)
                {
                    DrawPathfindingVisualization();
                }

                if (Settings.Pathfinding.ShowWaypoints.Value && pathfinderInitialized)
                {
                    DrawWaypoints();
                }
            }
            catch (Exception ex)
            {
                LogError($"Error in RenderVisuals: {ex.Message}");
            }
        }

        private void DrawTaskLine(RadarTask task)
        {
            var camera = GameController.IngameState.Camera;
            var playerPos = GameController.Player.GridPos;
            var playerPos3D = new Vector3(playerPos.X, playerPos.Y, 0);
            var targetPos3D = new Vector3(task.WorldPosition.X, task.WorldPosition.Y, 0);

            var playerScreen = camera.WorldToScreen(playerPos3D);
            var targetScreen = camera.WorldToScreen(targetPos3D);

            if (IsValidScreenPosition(playerScreen) && IsValidScreenPosition(targetScreen))
            {
                // Choose color based on task type
                var lineColor = GetTaskColor(task.Type);
                
                Graphics.DrawLine(
                    playerScreen,
                    targetScreen,
                    Settings.Visual.PathLineWidth.Value,
                    lineColor
                );
            }
        }

        private void DrawTargetMarker(RadarTask task)
        {
            var camera = GameController.IngameState.Camera;
            var targetPos3D = new Vector3(task.WorldPosition.X, task.WorldPosition.Y, 0);
            var targetScreen = camera.WorldToScreen(targetPos3D);

            if (IsValidScreenPosition(targetScreen))
            {
                var color = GetTaskColor(task.Type);
                var radius = 12f;
                
                // Draw circle
                Graphics.DrawEllipse(targetScreen, new Vector2(radius * 2, radius * 2), color, 2);
                
                // Draw cross
                Graphics.DrawLine(
                    new SharpDX.Vector2(targetScreen.X - radius, targetScreen.Y),
                    new SharpDX.Vector2(targetScreen.X + radius, targetScreen.Y),
                    2, color
                );
                Graphics.DrawLine(
                    new SharpDX.Vector2(targetScreen.X, targetScreen.Y - radius),
                    new SharpDX.Vector2(targetScreen.X, targetScreen.Y + radius),
                    2, color
                );
            }
        }

        private void DrawTaskQueue()
        {
            var startY = 200;
            var lineHeight = 18;
            var x = 10;

            Graphics.DrawText($"Task Queue ({taskQueue.Count}):", new Vector2(x, startY), Color.White);
            startY += lineHeight;

            if (currentTask != null)
            {
                var currentColor = Color.Yellow;
                Graphics.DrawText($"CURRENT: {currentTask}", new Vector2(x, startY), currentColor);
                startY += lineHeight;
            }

            var displayCount = Math.Min(5, taskQueue.Count);
            var taskArray = taskQueue.ToArray();
            
            for (int i = 0; i < displayCount; i++)
            {
                var task = taskArray[i];
                var taskColor = GetTaskColor(task.Type);
                Graphics.DrawText($"{i + 1}: {task}", new Vector2(x, startY), taskColor);
                startY += lineHeight;
            }

            if (taskQueue.Count > displayCount)
            {
                Graphics.DrawText($"... and {taskQueue.Count - displayCount} more", new Vector2(x, startY), Color.Gray);
            }
        }

        private void RenderDebugInfo()
        {
            if (!Settings.Debug.ShowDebug.Value || debugMessages.Count == 0)
                return;

            try
            {
                var startY = 50;
                var lineHeight = 16;
                var x = 10;

                Graphics.DrawText("RadarMovement Debug:", new Vector2(x, startY), Color.Cyan);
                startY += lineHeight + 5;

                // Show recent debug messages
                for (int i = Math.Max(0, debugMessages.Count - 10); i < debugMessages.Count; i++)
                {
                    var message = debugMessages[i];
                    var color = GetDebugMessageColor(message);
                    Graphics.DrawText(message, new Vector2(x, startY), color);
                    startY += lineHeight;
                }

                // Show performance stats if enabled
                if (Settings.Debug.ShowPerformance.Value)
                {
                    startY += 10;
                    var stats = $"Tasks: {tasksCompletedThisSession} completed, {tasksFailedThisSession} failed";
                    Graphics.DrawText(stats, new Vector2(x, startY), Color.LightGreen);
                }
            }
            catch (Exception ex)
            {
                LogError($"Error in RenderDebugInfo: {ex.Message}");
            }
        }

        private Color GetTaskColor(RadarTaskType taskType)
        {
            return taskType switch
            {
                RadarTaskType.ClickWaypoint => Color.Red,        // High priority - red
                RadarTaskType.ClickTransition => Color.Orange,   // High priority - orange
                RadarTaskType.ClickPortal => Color.Purple,       // Medium - purple
                RadarTaskType.ClickDoor => Color.Blue,           // Medium - blue
                RadarTaskType.MoveToPosition => Color.Green,     // Low - green
                RadarTaskType.Investigate => Color.Gray,         // Low - gray
                _ => Settings.Visual.PathLineColor.Value
            };
        }

        private Color GetDebugMessageColor(string message)
        {
            if (message.Contains("error") || message.Contains("failed") || message.Contains("Error"))
                return Color.Red;
            if (message.Contains("warning") || message.Contains("stuck") || message.Contains("Warning"))
                return Color.Orange;
            if (message.Contains("completed") || message.Contains("success") || message.Contains("Success"))
                return Color.LightGreen;
            if (message.Contains("EventBus"))
                return Color.Cyan;
            if (message.Contains("Terrain") || message.Contains("alternate"))
                return Color.Yellow;
            
            return Color.White;
        }

        private void DrawLineOfSightRays()
        {
            try
            {
                var debugRays = lineOfSight?.GetDebugRays();
                if (debugRays == null || debugRays.Count == 0)
                    return;

                var camera = GameController.IngameState.Camera;

                foreach (var (start, end, status) in debugRays)
                {
                    var startPos3D = new Vector3(start.X, start.Y, 0);
                    var endPos3D = new Vector3(end.X, end.Y, 0);
                    
                    var startScreen = camera.WorldToScreen(startPos3D);
                    var endScreen = camera.WorldToScreen(endPos3D);

                    if (IsValidScreenPosition(startScreen) && IsValidScreenPosition(endScreen))
                    {
                        var rayColor = status switch
                        {
                            PathStatus.Clear => Color.Green,
                            PathStatus.Dashable => Color.Yellow,
                            PathStatus.Blocked => Color.Red,
                            PathStatus.Invalid => Color.Gray,
                            _ => Color.White
                        };

                        Graphics.DrawLine(startScreen, endScreen, 1, rayColor);
                    }
                }
            }
            catch (Exception ex)
            {
                LogError($"Error drawing LineOfSight rays: {ex.Message}");
            }
        }

        private void DrawTerrainAnalysis()
        {
            try
            {
                var playerPos = GameController.Player.GridPos;
                var playerPos2D = new Vector2(playerPos.X, playerPos.Y);
                
                // Show terrain info at player position and nearby area
                var startY = 350;
                var lineHeight = 16;
                var x = 10;

                Graphics.DrawText("Terrain Analysis:", new Vector2(x, startY), Color.Cyan);
                startY += lineHeight + 5;

                if (lineOfSight != null)
                {
                    var playerTerrainInfo = lineOfSight.GetTerrainInfo(playerPos2D);
                    Graphics.DrawText($"Player: {playerTerrainInfo}", new Vector2(x, startY), Color.White);
                    startY += lineHeight;

                    var areaDimensions = lineOfSight.GetAreaDimensions();
                    Graphics.DrawText($"Area: {areaDimensions.X} x {areaDimensions.Y}", new Vector2(x, startY), Color.Gray);
                    startY += lineHeight;

                    // Show terrain analysis for current task
                    if (currentTask != null)
                    {
                        var taskTerrainInfo = lineOfSight.GetTerrainInfo(currentTask.WorldPosition);
                        Graphics.DrawText($"Target: {taskTerrainInfo}", new Vector2(x, startY), Color.Yellow);
                        startY += lineHeight;

                        var pathStatus = lineOfSight.CheckPath(playerPos2D, currentTask.WorldPosition);
                        Graphics.DrawText($"Path: {pathStatus}", new Vector2(x, startY), GetPathStatusColor(pathStatus));
                        startY += lineHeight;
                    }

                    // Show filtered targets count
                    Graphics.DrawText($"Filtered by terrain: {targetsFilteredByTerrain}", new Vector2(x, startY), Color.Orange);
                    startY += lineHeight;

                    // Show coroutine status if enabled
                    if (Settings.Debug.ShowCoroutineStatus.Value)
                    {
                        var mainStatus = mainProcessingCoroutine?.IsDone == false ? "Running" : "Stopped";
                        var transitionStatus = areaTransitionCoroutine?.IsDone == false ? "Running" : "Stopped";
                        var pausedStatus = processingPaused ? " (PAUSED)" : "";
                        
                        Graphics.DrawText($"Main Coroutine: {mainStatus}{pausedStatus}", new Vector2(x, startY), 
                            mainProcessingCoroutine?.IsDone == false ? Color.Green : Color.Red);
                        startY += lineHeight;
                        
                        if (isTransitioning)
                        {
                            Graphics.DrawText($"Transition Coroutine: {transitionStatus}", new Vector2(x, startY), 
                                areaTransitionCoroutine?.IsDone == false ? Color.Yellow : Color.Red);
                            startY += lineHeight;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                LogError($"Error drawing terrain analysis: {ex.Message}");
            }
        }

        private Color GetPathStatusColor(PathStatus status)
        {
            return status switch
            {
                PathStatus.Clear => Color.Green,
                PathStatus.Dashable => Color.Yellow,
                PathStatus.Blocked => Color.Red,
                PathStatus.Invalid => Color.Gray,
                _ => Color.White
            };
        }

        private void DrawPathfindingVisualization()
        {
            try
            {
                if (GameController.Player == null) return;

                // Draw pathfinding routes for current pathfinding waypoint tasks
                var pathfindingTasks = taskQueue.Where(t => t.IsPathfindingWaypoint).ToList();
                if (pathfindingTasks.Count == 0) return;

                var playerScreenPos = Camera.WorldToScreen(GameController.Player.Pos);
                var pathColor = Settings.Pathfinding.PathLineColor.Value;

                // Group pathfinding tasks by their path sequence
                for (int i = 0; i < pathfindingTasks.Count - 1; i++)
                {
                    var currentTask = pathfindingTasks[i];
                    var nextTask = pathfindingTasks[i + 1];

                    var currentScreenPos = Camera.WorldToScreen(currentTask.WorldPosition);
                    var nextScreenPos = Camera.WorldToScreen(nextTask.WorldPosition);

                    if (currentScreenPos != Vector2.Zero && nextScreenPos != Vector2.Zero)
                    {
                        // Draw path segment with varying thickness based on priority
                        var thickness = Math.Max(1, currentTask.Priority / 2);
                        Graphics.DrawLine(currentScreenPos, nextScreenPos, thickness, pathColor);

                        // Draw direction arrow
                        DrawArrow(currentScreenPos, nextScreenPos, pathColor, 8f);

                        // Draw waypoint numbers
                        Graphics.DrawText($"{i + 1}", currentScreenPos + new Vector2(-5, -20), 
                            pathColor, FontAlign.Center);
                    }
                }

                // Draw line from player to first pathfinding waypoint
                if (pathfindingTasks.Count > 0 && playerScreenPos != Vector2.Zero)
                {
                    var firstTaskPos = Camera.WorldToScreen(pathfindingTasks[0].WorldPosition);
                    if (firstTaskPos != Vector2.Zero)
                    {
                        Graphics.DrawLine(playerScreenPos, firstTaskPos, 2, Color.White);
                    }
                }
            }
            catch (Exception ex)
            {
                LogError($"Error drawing pathfinding visualization: {ex.Message}");
            }
        }

        private void DrawWaypoints()
        {
            try
            {
                if (pathfinder == null) return;

                var waypoints = pathfinder.GetWaypoints();
                var waypointColor = Settings.Pathfinding.WaypointColor.Value;

                foreach (var waypoint in waypoints)
                {
                    var screenPos = Camera.WorldToScreen(waypoint.WorldPosition);
                    if (screenPos == Vector2.Zero) continue;

                    // Draw waypoint circle with color based on type
                    var color = GetWaypointColor(waypoint.Type);
                    var radius = GetWaypointRadius(waypoint.Type);

                    Graphics.DrawFrame(new RectangleF(screenPos.X - radius, screenPos.Y - radius, 
                        radius * 2, radius * 2), color, 2);

                    // Draw waypoint name
                    if (!string.IsNullOrEmpty(waypoint.Name))
                    {
                        Graphics.DrawText(waypoint.Name, screenPos + new Vector2(0, -radius - 15), 
                            color, FontAlign.Center);
                    }

                    // Draw connections to other waypoints
                    foreach (var connected in waypoint.ConnectedWaypoints)
                    {
                        var connectedScreenPos = Camera.WorldToScreen(connected.WorldPosition);
                        if (connectedScreenPos != Vector2.Zero)
                        {
                            Graphics.DrawLine(screenPos, connectedScreenPos, 1, 
                                Color.Gray.ToArgb() | 0x80000000); // Semi-transparent
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                LogError($"Error drawing waypoints: {ex.Message}");
            }
        }

        private Color GetWaypointColor(TerrainType type)
        {
            return type switch
            {
                TerrainType.Bridge => Color.Orange,
                TerrainType.Exit => Color.Red,
                TerrainType.Waypoint => Color.Yellow,
                TerrainType.Normal => Color.Green,
                TerrainType.Hazard => Color.Purple,
                _ => Color.Gray
            };
        }

        private float GetWaypointRadius(TerrainType type)
        {
            return type switch
            {
                TerrainType.Exit => 12f,
                TerrainType.Bridge => 8f,
                TerrainType.Waypoint => 6f,
                _ => 4f
            };
        }

        private void DrawArrow(Vector2 from, Vector2 to, Color color, float size)
        {
            var direction = Vector2.Normalize(to - from);
            var perpendicular = new Vector2(-direction.Y, direction.X);
            
            var arrowTip = to - direction * size;
            var arrowLeft = arrowTip - direction * size * 0.5f + perpendicular * size * 0.3f;
            var arrowRight = arrowTip - direction * size * 0.5f - perpendicular * size * 0.3f;
            
            Graphics.DrawLine(arrowTip, arrowLeft, 2, color);
            Graphics.DrawLine(arrowTip, arrowRight, 2, color);
        }

        #endregion

        private bool IsValidScreenPosition(Vector2 screenPos)
        {
            try
            {
                var windowRect = GameController.Window.GetWindowRectangle();
                return screenPos.X >= 0 && screenPos.X <= windowRect.Width &&
                       screenPos.Y >= 0 && screenPos.Y <= windowRect.Height &&
                       !float.IsNaN(screenPos.X) && !float.IsNaN(screenPos.Y);
            }
            catch
            {
                return false;
            }
        }

        public override void OnClose()
        {
            try
            {
                // Stop all coroutines
                StopAllCoroutines();
                
                // Clean up LineOfSight system
                lineOfSight?.ClearDebugData();
                lineOfSight = null;
                
                // Clean up pathfinder system
                pathfinder?.ClearCache();
                pathfinder = null;
                pathfinderInitialized = false;
                
                // Unsubscribe from events to prevent memory leaks
                EventBus.Instance?.Clear();
                
                // Clear any remaining tasks
                taskQueue?.Clear();
                currentTask = null;
                
                AddDebugMessage("RadarMovement plugin closed with coroutine cleanup");
                base.OnClose();
            }
            catch (Exception ex)
            {
                LogError($"Error during plugin shutdown: {ex.Message}");
            }
        }

        private void StopAllCoroutines()
        {
            try
            {
                // Stop main processing coroutine
                if (mainProcessingCoroutine != null)
                {
                    var mainCoroutine = Core.ParallelRunner.FindByName("RadarMovement_MainProcessing");
                    if (mainCoroutine != null)
                    {
                        mainCoroutine.Done = true;
                    }
                    mainProcessingCoroutine = null;
                }

                // Stop area transition coroutine
                if (areaTransitionCoroutine != null)
                {
                    var transitionCoroutine = Core.ParallelRunner.FindByName("RadarMovement_AreaTransition");
                    if (transitionCoroutine != null)
                    {
                        transitionCoroutine.Done = true;
                    }
                    areaTransitionCoroutine = null;
                }

                AddDebugMessage("All coroutines stopped");
            }
            catch (Exception ex)
            {
                LogError($"Error stopping coroutines: {ex.Message}");
            }
        }
    }
} 