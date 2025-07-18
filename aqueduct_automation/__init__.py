"""
Aqueduct Automation Package
Advanced Path of Exile Aqueduct farming automation system
"""

__version__ = "1.0.0"
__author__ = "Aqueduct Automation Team"
__description__ = "Advanced Path of Exile Aqueduct farming automation system"

# Core modules
from .main import AqueductAutomation
from .config import AutomationConfig, ConfigTemplates
from .api_client import AqueductAPIClient

# Component modules
from .pathfinding import PathfindingEngine
from .combat import CombatSystem, CombatConfig
from .loot_manager import LootManager, LootConfig
from .resource_manager import ResourceManager, ResourceConfig

# Utilities
from .utils import setup_logging, calculate_distance, Timer

__all__ = [
    # Core classes
    'AqueductAutomation',
    'AutomationConfig',
    'ConfigTemplates',
    'AqueductAPIClient',
    
    # Component classes
    'PathfindingEngine',
    'CombatSystem',
    'CombatConfig',
    'LootManager',
    'LootConfig',
    'ResourceManager',
    'ResourceConfig',
    
    # Utilities
    'setup_logging',
    'calculate_distance',
    'Timer'
] 