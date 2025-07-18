"""
Resource Management System for Aqueduct Automation
Handles health, mana, energy shield monitoring and flask automation
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class FlaskType(Enum):
    """Flask types"""
    LIFE = "life"
    MANA = "mana"
    HYBRID = "hybrid"
    UTILITY = "utility"
    UNIQUE = "unique"

@dataclass
class ResourceConfig:
    """Configuration for resource management"""
    # Health management
    health_flask_threshold: float = 75.0     # Use health flask below this %
    critical_health_threshold: float = 30.0  # Emergency threshold
    
    # Mana management
    mana_flask_threshold: float = 50.0       # Use mana flask below this %
    critical_mana_threshold: float = 20.0    # Emergency threshold
    
    # Energy shield management
    es_flask_threshold: float = 50.0         # Use ES flask below this %
    
    # Flask settings
    flask_cooldown: float = 1.0              # Min time between flask uses
    emergency_flask_cooldown: float = 0.5    # Cooldown for emergency situations
    
    # Flask keys (customizable per build)
    life_flask_key: str = "1"
    mana_flask_key: str = "2"
    hybrid_flask_key: str = "3"
    utility_flask_keys: List[str] = None
    
    # Retreat settings
    retreat_health_threshold: float = 25.0   # Retreat if health below this %
    retreat_es_threshold: float = 20.0       # Retreat if ES below this %
    panic_mode_threshold: float = 15.0       # Panic mode threshold
    
    # Monitoring settings
    check_frequency: float = 0.5             # How often to check resources (seconds)
    
    def __post_init__(self):
        if self.utility_flask_keys is None:
            self.utility_flask_keys = ["4", "5"]

@dataclass
class ResourceStatus:
    """Current resource status"""
    health_current: int = 0
    health_max: int = 0
    health_percentage: float = 0.0
    
    mana_current: int = 0
    mana_max: int = 0
    mana_percentage: float = 0.0
    
    es_current: int = 0
    es_max: int = 0
    es_percentage: float = 0.0
    
    last_updated: float = 0.0
    
    def is_critical(self, config: ResourceConfig) -> bool:
        """Check if in critical state"""
        return (self.health_percentage < config.critical_health_threshold or
                self.mana_percentage < config.critical_mana_threshold)
    
    def should_retreat(self, config: ResourceConfig) -> bool:
        """Check if should retreat"""
        return (self.health_percentage < config.retreat_health_threshold or
                self.es_percentage < config.retreat_es_threshold)
    
    def is_panic_mode(self, config: ResourceConfig) -> bool:
        """Check if in panic mode"""
        return (self.health_percentage < config.panic_mode_threshold)

class ResourceManager:
    """Main resource management system"""
    
    def __init__(self, config: ResourceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Flask usage tracking
        self.last_flask_use = {}
        self.flask_uses_per_run = 0
        self.total_flask_uses = 0
        
        # Resource monitoring
        self.current_status = ResourceStatus()
        self.last_resource_check = 0.0
        
        # Emergency state
        self.in_panic_mode = False
        self.retreat_requested = False
        
        # Stats tracking
        self.total_monitoring_time = 0.0
        self.emergency_activations = 0
        
    def check_and_use_flasks(self) -> bool:
        """Check resources and use flasks if needed"""
        try:
            # Update resource status
            self.update_resource_status()
            
            # Check if we need to use flasks
            flasks_used = False
            
            # Health flask
            if self._should_use_health_flask():
                if self._use_flask(self.config.life_flask_key, FlaskType.LIFE):
                    flasks_used = True
            
            # Mana flask
            if self._should_use_mana_flask():
                if self._use_flask(self.config.mana_flask_key, FlaskType.MANA):
                    flasks_used = True
            
            # Hybrid flask (if available and beneficial)
            if self._should_use_hybrid_flask():
                if self._use_flask(self.config.hybrid_flask_key, FlaskType.HYBRID):
                    flasks_used = True
            
            # Utility flasks (less frequent)
            if self._should_use_utility_flasks():
                for key in self.config.utility_flask_keys:
                    if self._use_flask(key, FlaskType.UTILITY):
                        flasks_used = True
                        break  # Only use one utility flask per check
            
            # Check for panic mode
            if self.current_status.is_panic_mode(self.config):
                self._handle_panic_mode()
            
            # Check for retreat
            if self.current_status.should_retreat(self.config):
                self.retreat_requested = True
                self.logger.warning("Retreat requested due to low resources")
            
            return flasks_used
            
        except Exception as e:
            self.logger.error(f"Error checking resources: {e}")
            return False
    
    def update_resource_status(self):
        """Update current resource status from API"""
        try:
            # Get life data from API
            life_data = self._get_life_data()
            
            if life_data:
                # Update health
                health = life_data.get('Health', {})
                self.current_status.health_current = health.get('Current', 0)
                self.current_status.health_max = health.get('Total', 1)
                self.current_status.health_percentage = (
                    self.current_status.health_current / self.current_status.health_max * 100
                    if self.current_status.health_max > 0 else 0
                )
                
                # Update mana
                mana = life_data.get('Mana', {})
                self.current_status.mana_current = mana.get('Current', 0)
                self.current_status.mana_max = mana.get('Total', 1)
                self.current_status.mana_percentage = (
                    self.current_status.mana_current / self.current_status.mana_max * 100
                    if self.current_status.mana_max > 0 else 0
                )
                
                # Update energy shield
                es = life_data.get('EnergyShield', {})
                self.current_status.es_current = es.get('Current', 0)
                self.current_status.es_max = es.get('Total', 1)
                self.current_status.es_percentage = (
                    self.current_status.es_current / self.current_status.es_max * 100
                    if self.current_status.es_max > 0 else 0
                )
                
                self.current_status.last_updated = time.time()
                
        except Exception as e:
            self.logger.error(f"Error updating resource status: {e}")
    
    def _should_use_health_flask(self) -> bool:
        """Check if health flask should be used"""
        if self.current_status.health_percentage >= self.config.health_flask_threshold:
            return False
        
        # Check cooldown
        if not self._is_flask_ready(self.config.life_flask_key):
            return False
        
        # Don't use if at full health
        if self.current_status.health_current >= self.current_status.health_max:
            return False
        
        return True
    
    def _should_use_mana_flask(self) -> bool:
        """Check if mana flask should be used"""
        if self.current_status.mana_percentage >= self.config.mana_flask_threshold:
            return False
        
        # Check cooldown
        if not self._is_flask_ready(self.config.mana_flask_key):
            return False
        
        # Don't use if at full mana
        if self.current_status.mana_current >= self.current_status.mana_max:
            return False
        
        return True
    
    def _should_use_hybrid_flask(self) -> bool:
        """Check if hybrid flask should be used"""
        # Use hybrid flask if both health and mana are below threshold
        health_low = self.current_status.health_percentage < self.config.health_flask_threshold
        mana_low = self.current_status.mana_percentage < self.config.mana_flask_threshold
        
        if not (health_low and mana_low):
            return False
        
        # Check cooldown
        if not self._is_flask_ready(self.config.hybrid_flask_key):
            return False
        
        return True
    
    def _should_use_utility_flasks(self) -> bool:
        """Check if utility flasks should be used"""
        # Use utility flasks less frequently
        # Only use if in combat or health is below 50%
        if self.current_status.health_percentage < 50:
            return True
        
        # Use periodically for buffs (every 30 seconds)
        if self.config.utility_flask_keys:
            last_utility_use = min(self.last_flask_use.get(key, 0) for key in self.config.utility_flask_keys)
            if time.time() - last_utility_use > 30:
                return True
        
        return False
    
    def _use_flask(self, flask_key: str, flask_type: FlaskType) -> bool:
        """Use a specific flask"""
        try:
            # Check if flask is ready
            if not self._is_flask_ready(flask_key):
                return False
            
            # Send key press
            self._send_key(flask_key)
            
            # Record usage
            self.last_flask_use[flask_key] = time.time()
            self.flask_uses_per_run += 1
            self.total_flask_uses += 1
            
            self.logger.debug(f"Used {flask_type.value} flask (key: {flask_key})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error using flask {flask_key}: {e}")
            return False
    
    def _is_flask_ready(self, flask_key: str) -> bool:
        """Check if flask is ready (not on cooldown)"""
        last_use = self.last_flask_use.get(flask_key, 0)
        cooldown = self.config.flask_cooldown
        
        # Use shorter cooldown in emergencies
        if self.current_status.is_critical(self.config):
            cooldown = self.config.emergency_flask_cooldown
        
        return time.time() - last_use >= cooldown
    
    def _handle_panic_mode(self):
        """Handle panic mode - use all available flasks"""
        try:
            if not self.in_panic_mode:
                self.in_panic_mode = True
                self.emergency_activations += 1
                self.logger.warning("PANIC MODE ACTIVATED - Critical health/mana")
            
            # Use all available flasks
            emergency_flasks = [
                self.config.life_flask_key,
                self.config.mana_flask_key,
                self.config.hybrid_flask_key
            ]
            
            for flask_key in emergency_flasks:
                if self._is_flask_ready(flask_key):
                    self._use_flask(flask_key, FlaskType.LIFE)
                    time.sleep(0.1)  # Small delay between flasks
            
            # Also use utility flasks for defensive buffs
            for flask_key in self.config.utility_flask_keys:
                if self._is_flask_ready(flask_key):
                    self._use_flask(flask_key, FlaskType.UTILITY)
                    time.sleep(0.1)
            
        except Exception as e:
            self.logger.error(f"Error in panic mode: {e}")
    
    def should_retreat(self) -> bool:
        """Check if should retreat due to low resources"""
        return self.retreat_requested or self.current_status.should_retreat(self.config)
    
    def clear_retreat_request(self):
        """Clear retreat request"""
        self.retreat_requested = False
        self.in_panic_mode = False
    
    def get_resource_status(self) -> ResourceStatus:
        """Get current resource status"""
        return self.current_status
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get resource management statistics"""
        return {
            'flask_uses_per_run': self.flask_uses_per_run,
            'total_flask_uses': self.total_flask_uses,
            'emergency_activations': self.emergency_activations,
            'current_health_percentage': self.current_status.health_percentage,
            'current_mana_percentage': self.current_status.mana_percentage,
            'current_es_percentage': self.current_status.es_percentage,
            'in_panic_mode': self.in_panic_mode,
            'retreat_requested': self.retreat_requested
        }
    
    def reset_run_stats(self):
        """Reset per-run statistics"""
        self.flask_uses_per_run = 0
        self.retreat_requested = False
        self.in_panic_mode = False
    
    def reset_all_stats(self):
        """Reset all statistics"""
        self.flask_uses_per_run = 0
        self.total_flask_uses = 0
        self.emergency_activations = 0
        self.retreat_requested = False
        self.in_panic_mode = False
        self.last_flask_use = {}
    
    def force_flask_use(self, flask_key: str) -> bool:
        """Force use of a specific flask (ignores cooldown)"""
        try:
            self._send_key(flask_key)
            self.last_flask_use[flask_key] = time.time()
            self.flask_uses_per_run += 1
            self.total_flask_uses += 1
            
            self.logger.info(f"Force used flask (key: {flask_key})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error force using flask {flask_key}: {e}")
            return False
    
    def is_healthy(self) -> bool:
        """Check if character is in good health"""
        return (self.current_status.health_percentage > 75 and
                self.current_status.mana_percentage > 50 and
                not self.in_panic_mode)
    
    def get_effective_health_percentage(self) -> float:
        """Get effective health percentage (health + ES)"""
        if self.current_status.es_max > 0:
            total_effective_health = self.current_status.health_current + self.current_status.es_current
            total_effective_max = self.current_status.health_max + self.current_status.es_max
            return (total_effective_health / total_effective_max * 100) if total_effective_max > 0 else 0
        else:
            return self.current_status.health_percentage
    
    def log_resource_status(self):
        """Log current resource status"""
        self.logger.info(f"Health: {self.current_status.health_percentage:.1f}% "
                        f"({self.current_status.health_current}/{self.current_status.health_max})")
        self.logger.info(f"Mana: {self.current_status.mana_percentage:.1f}% "
                        f"({self.current_status.mana_current}/{self.current_status.mana_max})")
        if self.current_status.es_max > 0:
            self.logger.info(f"ES: {self.current_status.es_percentage:.1f}% "
                            f"({self.current_status.es_current}/{self.current_status.es_max})")
    
    def _get_life_data(self) -> Dict[str, Any]:
        """Get life data from API"""
        # Placeholder - would be implemented with actual API call
        return {}
    
    def _send_key(self, key: str):
        """Send key press"""
        # Placeholder - would be implemented with actual input system
        pass

# Factory function for creating resource configurations
def create_resource_config(build_type: str = "default") -> ResourceConfig:
    """Create resource configuration based on build type"""
    
    configs = {
        "life_based": ResourceConfig(
            health_flask_threshold=75.0,
            mana_flask_threshold=50.0,
            critical_health_threshold=30.0,
            life_flask_key="1",
            mana_flask_key="2",
            utility_flask_keys=["3", "4", "5"]
        ),
        "energy_shield": ResourceConfig(
            health_flask_threshold=50.0,  # Lower priority for life
            mana_flask_threshold=60.0,
            es_flask_threshold=70.0,      # Higher priority for ES
            critical_health_threshold=20.0,
            life_flask_key="1",
            mana_flask_key="2",
            utility_flask_keys=["3", "4", "5"]
        ),
        "hybrid": ResourceConfig(
            health_flask_threshold=70.0,
            mana_flask_threshold=55.0,
            es_flask_threshold=60.0,
            critical_health_threshold=25.0,
            life_flask_key="1",
            mana_flask_key="2",
            hybrid_flask_key="3",
            utility_flask_keys=["4", "5"]
        ),
        "low_life": ResourceConfig(
            health_flask_threshold=35.0,  # Keep health low intentionally
            mana_flask_threshold=70.0,
            es_flask_threshold=80.0,
            critical_health_threshold=15.0,
            retreat_health_threshold=10.0,  # Very low retreat threshold
            life_flask_key="1",
            mana_flask_key="2",
            utility_flask_keys=["3", "4", "5"]
        )
    }
    
    return configs.get(build_type, ResourceConfig()) 