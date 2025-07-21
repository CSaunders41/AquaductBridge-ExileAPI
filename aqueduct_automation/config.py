"""
Configuration System for Aqueduct Automation
Centralized configuration management for all automation components
"""

import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from .combat import CombatConfig, create_combat_config
from .loot_manager import LootConfig, create_loot_config
from .resource_manager import ResourceConfig, create_resource_config

@dataclass
class AutomationConfig:
    """Main configuration for the automation system"""
    
    # API Settings
    api_host: str = "127.0.0.1"
    api_port: int = 50002
    
    # Automation Behavior
    auto_start_server: bool = True
    max_runs: int = 0              # 0 = unlimited
    max_runtime: float = 0         # 0 = unlimited (seconds)
    run_delay: float = 2.0         # Delay between runs (seconds)
    
    # Safety Settings
    enable_safety_checks: bool = True
    max_deaths_per_run: int = 1
    disconnect_on_death: bool = False
    pause_on_player_detected: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "automation.log"
    
    # Build Configuration
    build_type: str = "default"    # Used for combat/resource configs
    character_class: str = "unknown"
    
    # Component Configs
    combat_config: CombatConfig = None
    loot_config: LootConfig = None
    resource_config: ResourceConfig = None
    
    def __post_init__(self):
        """Initialize sub-configurations if not provided"""
        if self.combat_config is None:
            self.combat_config = create_combat_config(self.build_type)
        
        if self.loot_config is None:
            self.loot_config = create_loot_config("general_farming")
        
        if self.resource_config is None:
            self.resource_config = create_resource_config(self.build_type)
    
    def save_to_file(self, file_path: str):
        """Save configuration to JSON file"""
        try:
            config_dict = asdict(self)
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            logging.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'AutomationConfig':
        """Load configuration from JSON file"""
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            
            # Create configs from dictionaries
            combat_config = CombatConfig(**config_dict.get('combat_config', {}))
            loot_config = LootConfig(**config_dict.get('loot_config', {}))
            resource_config = ResourceConfig(**config_dict.get('resource_config', {}))
            
            # Remove sub-configs from main dict
            config_dict.pop('combat_config', None)
            config_dict.pop('loot_config', None)
            config_dict.pop('resource_config', None)
            
            # Create main config
            config = cls(**config_dict)
            config.combat_config = combat_config
            config.loot_config = loot_config
            config.resource_config = resource_config
            
            logging.info(f"Configuration loaded from {file_path}")
            return config
            
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            return cls()  # Return default config
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        try:
            # Validate API settings
            if not (1 <= self.api_port <= 65535):
                logging.error(f"Invalid API port: {self.api_port}")
                return False
            
            # Validate timing settings
            if self.run_delay < 0:
                logging.error(f"Invalid run delay: {self.run_delay}")
                return False
            
            # Validate safety settings
            if self.max_deaths_per_run < 0:
                logging.error(f"Invalid max deaths per run: {self.max_deaths_per_run}")
                return False
            
            # Validate log level
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if self.log_level not in valid_log_levels:
                logging.error(f"Invalid log level: {self.log_level}")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Configuration validation error: {e}")
            return False

# Predefined configuration templates
class ConfigTemplates:
    """Predefined configuration templates for common setups"""
    
    @staticmethod
    def create_speed_farming_config() -> AutomationConfig:
        """Configuration optimized for speed farming"""
        return AutomationConfig(
            build_type="ranged",
            run_delay=1.0,
            combat_config=create_combat_config("ranged"),
            loot_config=create_loot_config("speed_farming"),
            resource_config=create_resource_config("life_based")
        )
    
    @staticmethod
    def create_safe_farming_config() -> AutomationConfig:
        """Configuration optimized for safe farming"""
        return AutomationConfig(
            build_type="default",
            run_delay=3.0,
            enable_safety_checks=True,
            max_deaths_per_run=0,
            combat_config=CombatConfig(
                retreat_health_threshold=40.0,
                max_engagement_range=80.0,
                combat_timeout=20.0
            ),
            loot_config=create_loot_config("general_farming"),
            resource_config=ResourceConfig(
                health_flask_threshold=80.0,
                retreat_health_threshold=35.0
            )
        )
    
    @staticmethod
    def create_currency_farming_config() -> AutomationConfig:
        """Configuration optimized for currency farming"""
        return AutomationConfig(
            build_type="default",
            run_delay=1.5,
            combat_config=create_combat_config("default"),
            loot_config=create_loot_config("currency_farming"),
            resource_config=create_resource_config("default")
        )
    
    @staticmethod
    def create_energy_shield_config() -> AutomationConfig:
        """Configuration for energy shield based builds"""
        return AutomationConfig(
            build_type="caster",
            combat_config=create_combat_config("caster"),
            loot_config=create_loot_config("general_farming"),
            resource_config=create_resource_config("energy_shield")
        )
    
    @staticmethod
    def create_melee_config() -> AutomationConfig:
        """Configuration for melee builds"""
        return AutomationConfig(
            build_type="melee",
            combat_config=create_combat_config("melee"),
            loot_config=create_loot_config("general_farming"),
            resource_config=create_resource_config("life_based")
        )

class ConfigManager:
    """Configuration management utility"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def save_config(self, config: AutomationConfig, name: str):
        """Save a configuration with a given name"""
        try:
            file_path = self.config_dir / f"{name}.json"
            config.save_to_file(str(file_path))
            self.logger.info(f"Configuration '{name}' saved")
        except Exception as e:
            self.logger.error(f"Failed to save configuration '{name}': {e}")
    
    def load_config(self, name: str) -> Optional[AutomationConfig]:
        """Load a configuration by name"""
        try:
            file_path = self.config_dir / f"{name}.json"
            if file_path.exists():
                return AutomationConfig.load_from_file(str(file_path))
            else:
                self.logger.warning(f"Configuration '{name}' not found")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load configuration '{name}': {e}")
            return None
    
    def list_configs(self) -> list:
        """List all available configurations"""
        try:
            config_files = list(self.config_dir.glob("*.json"))
            return [f.stem for f in config_files]
        except Exception as e:
            self.logger.error(f"Failed to list configurations: {e}")
            return []
    
    def delete_config(self, name: str) -> bool:
        """Delete a configuration by name"""
        try:
            file_path = self.config_dir / f"{name}.json"
            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"Configuration '{name}' deleted")
                return True
            else:
                self.logger.warning(f"Configuration '{name}' not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete configuration '{name}': {e}")
            return False
    
    def create_default_configs(self):
        """Create default configuration templates"""
        templates = {
            "speed_farming": ConfigTemplates.create_speed_farming_config(),
            "safe_farming": ConfigTemplates.create_safe_farming_config(),
            "currency_farming": ConfigTemplates.create_currency_farming_config(),
            "energy_shield": ConfigTemplates.create_energy_shield_config(),
            "melee": ConfigTemplates.create_melee_config()
        }
        
        for name, config in templates.items():
            self.save_config(config, name)
        
        self.logger.info("Default configurations created")

# Configuration validation functions
def validate_flask_keys(config: AutomationConfig) -> bool:
    """Validate flask key configuration"""
    resource_config = config.resource_config
    
    # Check for duplicate keys
    all_keys = [
        resource_config.life_flask_key,
        resource_config.mana_flask_key,
        resource_config.hybrid_flask_key
    ] + resource_config.utility_flask_keys
    
    if len(all_keys) != len(set(all_keys)):
        logging.error("Duplicate flask keys detected")
        return False
    
    # Check for valid key format
    valid_keys = set("12345qwertyuiopasdfghjklzxcvbnm")
    for key in all_keys:
        if key and key.lower() not in valid_keys:
            logging.error(f"Invalid flask key: {key}")
            return False
    
    return True

def validate_combat_config(config: AutomationConfig) -> bool:
    """Validate combat configuration"""
    combat_config = config.combat_config
    
    # Check range settings
    if combat_config.max_engagement_range <= combat_config.min_engagement_range:
        logging.error("Max engagement range must be greater than min engagement range")
        return False
    
    # Check threshold settings
    if combat_config.retreat_health_threshold <= 0 or combat_config.retreat_health_threshold > 100:
        logging.error("Invalid retreat health threshold")
        return False
    
    return True

def validate_full_config(config: AutomationConfig) -> bool:
    """Perform full configuration validation"""
    return (config.validate() and
            validate_flask_keys(config) and
            validate_combat_config(config))

# Configuration CLI helper
def create_config_from_user_input() -> AutomationConfig:
    """Create configuration from user input (interactive)"""
    print("=== Aqueduct Automation Configuration ===")
    
    # Build type selection
    print("\nSelect build type:")
    print("1. Melee")
    print("2. Ranged")
    print("3. Caster")
    print("4. Default")
    
    build_choice = input("Enter choice (1-4): ").strip()
    build_map = {"1": "melee", "2": "ranged", "3": "caster", "4": "default"}
    build_type = build_map.get(build_choice, "default")
    
    # Farming style selection
    print("\nSelect farming style:")
    print("1. Speed farming (fast, less safe)")
    print("2. Safe farming (slower, safer)")
    print("3. Currency farming (currency focus)")
    print("4. General farming (balanced)")
    
    farming_choice = input("Enter choice (1-4): ").strip()
    farming_map = {"1": "speed_farming", "2": "safe_farming", "3": "currency_farming", "4": "general_farming"}
    farming_style = farming_map.get(farming_choice, "general_farming")
    
    # Resource management
    print("\nSelect resource management:")
    print("1. Life-based")
    print("2. Energy shield")
    print("3. Hybrid")
    print("4. Low life")
    
    resource_choice = input("Enter choice (1-4): ").strip()
    resource_map = {"1": "life_based", "2": "energy_shield", "3": "hybrid", "4": "low_life"}
    resource_type = resource_map.get(resource_choice, "life_based")
    
    # Create configuration
    config = AutomationConfig(
        build_type=build_type,
        combat_config=create_combat_config(build_type),
        loot_config=create_loot_config(farming_style),
        resource_config=create_resource_config(resource_type)
    )
    
    # Optional: Ask for flask keys
    print("\nConfigure flask keys (press Enter to use defaults):")
    life_key = input(f"Life flask key (default: {config.resource_config.life_flask_key}): ").strip()
    if life_key:
        config.resource_config.life_flask_key = life_key
    
    mana_key = input(f"Mana flask key (default: {config.resource_config.mana_flask_key}): ").strip()
    if mana_key:
        config.resource_config.mana_flask_key = mana_key
    
    print("\nConfiguration created successfully!")
    return config

# Default configuration getter
def get_default_config() -> AutomationConfig:
    """Get the default configuration"""
    return AutomationConfig() 