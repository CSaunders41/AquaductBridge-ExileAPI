using ExileCore.Shared.Interfaces;
using ExileCore.Shared.Nodes;
using ExileCore.Shared.Attributes;
using SharpDX;

namespace AqueductBridge
{
    public class AqueductBridgeSettings : ISettings
    {
        public ToggleNode Enable { get; set; } = new ToggleNode(true);

        [Menu("HTTP Server Port")]
        public RangeNode<int> HttpServerPort { get; set; } = new RangeNode<int>(50002, 1024, 65535);

        [Menu("Enable Debug Logging")]
        public ToggleNode EnableDebugLogging { get; set; } = new ToggleNode(false);

        [Menu("Auto-Start Server")]
        public ToggleNode AutoStartServer { get; set; } = new ToggleNode(true);
        
        [Menu("Show Visual Path")]
        public ToggleNode ShowVisualPath { get; set; } = new ToggleNode(true);
        
        [Menu("Path Line Color")]
        public ColorNode PathLineColor { get; set; } = new ColorNode(Color.Yellow);
        
        [Menu("Path Line Width")]
        public RangeNode<int> PathLineWidth { get; set; } = new RangeNode<int>(3, 1, 10);
        
        [Menu("Show Target Marker")]
        public ToggleNode ShowTargetMarker { get; set; } = new ToggleNode(true);
        
        [Menu("Target Marker Color")]
        public ColorNode TargetMarkerColor { get; set; } = new ColorNode(Color.Red);
    }
} 