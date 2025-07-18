using ExileCore.Shared.Interfaces;
using ExileCore.Shared.Nodes;
using ExileCore.Shared.Attributes;

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
    }
} 