"""
Combat System for Aqueduct Automation
Handles monster detection, targeting, and combat engagement
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class CombatState(Enum):
    """Combat states"""
    IDLE = "idle"
    SCANNING = "scanning"
    ENGAGING = "engaging"
    RETREATING = "retreating"
    DEAD = "dead"

@dataclass
class CombatConfig:
    """Configuration for combat system"""
    # Engagement settings
    max_engagement_range: float = 100.0  # Max distance to engage enemies
    min_engagement_range: float = 30.0   # Min distance to maintain from enemies
    retreat_health_threshold: float = 25.0  # Health % to retreat at
    
    # Targeting settings
    priority_targets: List[str] = None  # Priority monster types
    ignore_targets: List[str] = None    # Monsters to ignore
    
    # Combat timing
    skill_cooldown: float = 0.5        # Cooldown between skill usage
    movement_delay: float = 0.3        # Delay between movement commands
    combat_timeout: float = 30.0       # Max time to spend fighting one group
    
    # Skills (placeholder - would be customized per build)
    primary_skill_key: str = "Q"       # Primary attack skill
    secondary_skill_key: str = "W"     # Secondary skill  
    movement_skill_key: str = "E"      # Movement skill
    defensive_skill_key: str = "R"     # Defensive skill
    
    def __post_init__(self):
        if self.priority_targets is None:
            self.priority_targets = []
        if self.ignore_targets is None:
            self.ignore_targets = ["MercenaryScion", "MercenaryRanger", "MercenaryShadow"]  # Allied NPCs

@dataclass
class Monster:
    """Represents a monster entity"""
    id: int
    position: Dict[str, int]
    screen_position: Dict[str, int]
    path: str
    health: Dict[str, Any]
    is_alive: bool
    distance: float = 0.0
    threat_level: int = 1
    
    @property
    def health_percentage(self) -> float:
        """Get monster health percentage"""
        current = self.health.get('Health', {}).get('Current', 0)
        total = self.health.get('Health', {}).get('Total', 1)
        return (current / total) * 100 if total > 0 else 0
    
    @property
    def is_low_health(self) -> bool:
        """Check if monster is low on health"""
        return self.health_percentage < 30
    
    def get_monster_type(self) -> str:
        """Extract monster type from path"""
        if not self.path:
            return "unknown"
        
        # Extract the last part of the path
        parts = self.path.split('/')
        if parts:
            return parts[-1].split('@')[0]  # Remove @id suffix
        return "unknown"

class CombatSystem:
    """Main combat system for handling monster engagement"""
    
    def __init__(self, config: CombatConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.state = CombatState.IDLE
        self.last_skill_use = 0.0
        self.combat_start_time = 0.0
        self.current_targets: List[Monster] = []
        self.primary_target: Optional[Monster] = None
        
        # Stats tracking
        self.monsters_killed = 0
        self.total_combat_time = 0.0
        
    def scan_for_enemies(self) -> bool:
        """Scan for nearby enemies and return if any found"""
        try:
            from api_client import AqueductAPIClient
            
            # This would be passed in from the main automation system
            # For now, we'll simulate the API call
            # In practice, this would be injected as a dependency
            
            # Placeholder - in real implementation, this would get entities from API
            monsters = self._get_nearby_monsters()
            
            if not monsters:
                self.state = CombatState.IDLE
                return False
            
            self.current_targets = monsters
            self.state = CombatState.SCANNING
            
            # Select primary target
            self.primary_target = self._select_primary_target(monsters)
            
            self.logger.debug(f"Found {len(monsters)} monsters, primary target: {self.primary_target.get_monster_type() if self.primary_target else 'None'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error scanning for enemies: {e}")
            return False
    
    def engage_combat(self) -> int:
        """Engage in combat with detected enemies"""
        try:
            if not self.current_targets:
                return 0
            
            self.state = CombatState.ENGAGING
            self.combat_start_time = time.time()
            kills = 0
            
            self.logger.info(f"Engaging {len(self.current_targets)} monsters")
            
            while self.current_targets and self._should_continue_combat():
                # Update monster positions and status
                self._update_monster_status()
                
                # Check if we should retreat
                if self._should_retreat():
                    self.logger.warning("Retreating from combat")
                    self.state = CombatState.RETREATING
                    break
                
                # Select target
                target = self._select_primary_target(self.current_targets)
                if not target:
                    break
                
                # Engage target
                if self._engage_target(target):
                    kills += 1
                    self.monsters_killed += 1
                
                # Remove dead/invalid targets
                self.current_targets = [m for m in self.current_targets if m.is_alive and m.health_percentage > 0]
                
                # Small delay between targets
                time.sleep(0.1)
            
            # Combat finished
            combat_duration = time.time() - self.combat_start_time
            self.total_combat_time += combat_duration
            
            self.state = CombatState.IDLE
            self.logger.info(f"Combat finished. Killed {kills} monsters in {combat_duration:.1f}s")
            
            return kills
            
        except Exception as e:
            self.logger.error(f"Error in combat engagement: {e}")
            self.state = CombatState.IDLE
            return 0
    
    def _get_nearby_monsters(self) -> List[Monster]:
        """Get monsters within engagement range"""
        try:
            # This would be implemented with actual API calls
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting nearby monsters: {e}")
            return []
    
    def _select_primary_target(self, monsters: List[Monster]) -> Optional[Monster]:
        """Select the primary target based on priority and distance"""
        if not monsters:
            return None
        
        # Filter out ignored monsters
        valid_targets = []
        for monster in monsters:
            monster_type = monster.get_monster_type()
            if not any(ignored in monster_type for ignored in self.config.ignore_targets):
                valid_targets.append(monster)
        
        if not valid_targets:
            return None
        
        # Priority targeting
        priority_targets = []
        for monster in valid_targets:
            monster_type = monster.get_monster_type()
            if any(priority in monster_type for priority in self.config.priority_targets):
                priority_targets.append(monster)
        
        if priority_targets:
            valid_targets = priority_targets
        
        # Sort by distance and threat level
        def target_score(monster: Monster) -> float:
            # Lower score = higher priority
            score = monster.distance
            
            # Boost priority for low health monsters (easy kills)
            if monster.is_low_health:
                score *= 0.5
            
            # Boost priority for high threat monsters
            score /= monster.threat_level
            
            return score
        
        valid_targets.sort(key=target_score)
        return valid_targets[0] if valid_targets else None
    
    def _engage_target(self, target: Monster) -> bool:
        """Engage a specific target"""
        try:
            self.logger.debug(f"Engaging {target.get_monster_type()} at distance {target.distance:.1f}")
            
            # Move to optimal range if needed
            if target.distance > self.config.max_engagement_range:
                self._move_towards_target(target)
                return False
            
            if target.distance < self.config.min_engagement_range:
                self._move_away_from_target(target)
                return False
            
            # Use combat skills
            if self._can_use_skill():
                self._use_primary_skill(target)
                self.last_skill_use = time.time()
            
            # Check if target is dead
            if target.health_percentage <= 0:
                self.logger.debug(f"Killed {target.get_monster_type()}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error engaging target: {e}")
            return False
    
    def _move_towards_target(self, target: Monster):
        """Move towards a target"""
        try:
            # Calculate direction vector
            dx = target.position['X'] - self._get_player_position()['X']
            dy = target.position['Y'] - self._get_player_position()['Y']
            
            # Normalize and scale
            distance = (dx*dx + dy*dy)**0.5
            if distance > 0:
                move_distance = min(20, target.distance - self.config.max_engagement_range)
                dx = dx / distance * move_distance
                dy = dy / distance * move_distance
                
                # Move towards target
                target_pos = {
                    'X': self._get_player_position()['X'] + dx,
                    'Y': self._get_player_position()['Y'] + dy
                }
                
                self._move_to_position(target_pos)
                
        except Exception as e:
            self.logger.error(f"Error moving towards target: {e}")
    
    def _move_away_from_target(self, target: Monster):
        """Move away from a target"""
        try:
            # Calculate direction vector (opposite)
            dx = self._get_player_position()['X'] - target.position['X']
            dy = self._get_player_position()['Y'] - target.position['Y']
            
            # Normalize and scale
            distance = (dx*dx + dy*dy)**0.5
            if distance > 0:
                move_distance = self.config.min_engagement_range - target.distance + 10
                dx = dx / distance * move_distance
                dy = dy / distance * move_distance
                
                # Move away from target
                target_pos = {
                    'X': self._get_player_position()['X'] + dx,
                    'Y': self._get_player_position()['Y'] + dy
                }
                
                self._move_to_position(target_pos)
                
        except Exception as e:
            self.logger.error(f"Error moving away from target: {e}")
    
    def _can_use_skill(self) -> bool:
        """Check if we can use a skill (not on cooldown)"""
        return time.time() - self.last_skill_use >= self.config.skill_cooldown
    
    def _use_primary_skill(self, target: Monster):
        """Use primary combat skill on target"""
        try:
            # Click on target position
            screen_pos = target.screen_position
            self._click_position(screen_pos['X'], screen_pos['Y'])
            
            # Use primary skill
            self._send_key(self.config.primary_skill_key)
            
        except Exception as e:
            self.logger.error(f"Error using primary skill: {e}")
    
    def _should_continue_combat(self) -> bool:
        """Check if combat should continue"""
        # Check timeout
        if time.time() - self.combat_start_time > self.config.combat_timeout:
            self.logger.warning("Combat timeout reached")
            return False
        
        # Check if we have valid targets
        if not self.current_targets:
            return False
        
        # Check if we should retreat
        if self._should_retreat():
            return False
        
        return True
    
    def _should_retreat(self) -> bool:
        """Check if we should retreat from combat"""
        # Check health threshold
        health_percentage = self._get_player_health_percentage()
        if health_percentage < self.config.retreat_health_threshold:
            return True
        
        # Check for overwhelming odds (too many monsters)
        if len(self.current_targets) > 10:
            return True
        
        return False
    
    def _update_monster_status(self):
        """Update status of current monsters"""
        try:
            # This would re-query the API for updated monster data
            # For now, simulate by checking if monsters are still alive
            pass
            
        except Exception as e:
            self.logger.error(f"Error updating monster status: {e}")
    
    def _get_player_position(self) -> Dict[str, int]:
        """Get current player position"""
        # Placeholder - would be implemented with API call
        return {'X': 0, 'Y': 0, 'Z': 0}
    
    def _get_player_health_percentage(self) -> float:
        """Get current player health percentage"""
        # Placeholder - would be implemented with API call
        return 100.0
    
    def _move_to_position(self, position: Dict[str, int]):
        """Move to a specific position"""
        # Placeholder - would be implemented with API call
        pass
    
    def _click_position(self, x: int, y: int):
        """Click at screen position"""
        # Placeholder - would be implemented with API call
        pass
    
    def _send_key(self, key: str):
        """Send key press"""
        # Placeholder - would be implemented with API call
        pass
    
    def get_combat_stats(self) -> Dict[str, Any]:
        """Get combat statistics"""
        return {
            'monsters_killed': self.monsters_killed,
            'total_combat_time': self.total_combat_time,
            'average_kill_time': self.total_combat_time / max(1, self.monsters_killed),
            'current_state': self.state.value
        }
    
    def reset_stats(self):
        """Reset combat statistics"""
        self.monsters_killed = 0
        self.total_combat_time = 0.0
    
    def is_in_combat(self) -> bool:
        """Check if currently in combat"""
        return self.state in [CombatState.ENGAGING, CombatState.RETREATING]
    
    def force_retreat(self):
        """Force retreat from combat"""
        self.state = CombatState.RETREATING
        self.current_targets = []
        self.primary_target = None
        self.logger.info("Forced retreat from combat")
    
    def emergency_stop(self):
        """Emergency stop all combat"""
        self.state = CombatState.IDLE
        self.current_targets = []
        self.primary_target = None
        self.logger.warning("Emergency combat stop")

# Factory function for creating combat configurations
def create_combat_config(build_type: str = "default") -> CombatConfig:
    """Create combat configuration based on build type"""
    
    configs = {
        "melee": CombatConfig(
            max_engagement_range=40.0,
            min_engagement_range=10.0,
            primary_skill_key="Q",
            secondary_skill_key="W",
            movement_skill_key="E",
            defensive_skill_key="R"
        ),
        "ranged": CombatConfig(
            max_engagement_range=120.0,
            min_engagement_range=60.0,
            primary_skill_key="Q",
            secondary_skill_key="W",
            movement_skill_key="E",
            defensive_skill_key="R"
        ),
        "caster": CombatConfig(
            max_engagement_range=100.0,
            min_engagement_range=50.0,
            primary_skill_key="Q",
            secondary_skill_key="W",
            movement_skill_key="E",
            defensive_skill_key="R"
        )
    }
    
    return configs.get(build_type, CombatConfig()) 