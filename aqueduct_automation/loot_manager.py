"""
Loot Management System for Aqueduct Automation
Handles item detection, filtering, pickup, and stash management
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re

class ItemType(Enum):
    """Item types for filtering"""
    CURRENCY = "currency"
    DIVINATION_CARD = "divination_card"
    UNIQUE = "unique"
    RARE = "rare"
    MAGIC = "magic"
    NORMAL = "normal"
    GEM = "gem"
    MAP = "map"
    FLASK = "flask"
    UNKNOWN = "unknown"

class ItemRarity(Enum):
    """Item rarity levels"""
    NORMAL = 0
    MAGIC = 1
    RARE = 2
    UNIQUE = 3

@dataclass
class LootConfig:
    """Configuration for loot management"""
    # Pickup settings
    pickup_currency: bool = True
    pickup_divination_cards: bool = True
    pickup_uniques: bool = True
    pickup_rares: bool = False
    pickup_magic: bool = False
    pickup_normal: bool = False
    pickup_gems: bool = True
    pickup_maps: bool = True
    pickup_flasks: bool = False
    
    # Currency filters
    valuable_currency: Set[str] = None
    ignore_currency: Set[str] = None
    
    # Item filters
    valuable_uniques: Set[str] = None
    valuable_div_cards: Set[str] = None
    min_item_level: int = 60
    
    # Pickup behavior
    pickup_radius: float = 50.0
    max_inventory_slots: int = 60
    inventory_full_threshold: float = 0.9  # 90% full
    
    # Stash settings
    stash_currency: bool = True
    stash_divination_cards: bool = True
    stash_uniques: bool = True
    stash_maps: bool = True
    stash_gems: bool = True
    
    def __post_init__(self):
        if self.valuable_currency is None:
            self.valuable_currency = {
                "Ancient Orb", "Orb of Alchemy", "Chaos Orb", "Chromatic Orb",
                "Divine Orb", "Exalted Orb", "Orb of Fusing", "Gemcutter's Prism",
                "Jeweller's Orb", "Orb of Regret", "Regal Orb", "Vaal Orb",
                "Blessed Orb", "Cartographer's Chisel", "Glassblower's Bauble",
                "Mirror of Kalandra", "Annulment Orb", "Harbinger's Orb",
                "Engineer's Orb", "Infused Engineer's Orb", "Tempering Orb",
                "Tailoring Orb", "Orb of Horizons", "Orb of Binding"
            }
        
        if self.ignore_currency is None:
            self.ignore_currency = {
                "Armourer's Scrap", "Blacksmith's Whetstone", "Portal Scroll",
                "Scroll of Wisdom", "Orb of Transmutation", "Orb of Augmentation",
                "Orb of Alteration"
            }
        
        if self.valuable_uniques is None:
            self.valuable_uniques = set()  # Would be populated with valuable unique names
        
        if self.valuable_div_cards is None:
            self.valuable_div_cards = set()  # Would be populated with valuable div card names

@dataclass
class Item:
    """Represents an item entity"""
    id: int
    position: Dict[str, int]
    screen_position: Dict[str, int]
    path: str
    name: str
    rarity: ItemRarity
    item_type: ItemType
    item_level: int = 0
    distance: float = 0.0
    is_valuable: bool = False
    
    def get_display_name(self) -> str:
        """Get display name for logging"""
        return self.name if self.name else self.path.split('/')[-1]

class LootManager:
    """Main loot management system"""
    
    def __init__(self, config: LootConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Stats tracking
        self.items_collected = 0
        self.currency_collected = 0
        self.uniques_collected = 0
        self.div_cards_collected = 0
        self.total_pickup_time = 0.0
        
        # State tracking
        self.current_inventory_slots = 0
        self.last_pickup_time = 0.0
        
    def collect_nearby_loot(self) -> int:
        """Collect all valuable loot within pickup radius"""
        try:
            start_time = time.time()
            
            # Get nearby items
            nearby_items = self._get_nearby_items()
            
            if not nearby_items:
                return 0
            
            # Filter valuable items
            valuable_items = self._filter_valuable_items(nearby_items)
            
            if not valuable_items:
                return 0
            
            # Sort by priority and distance
            valuable_items.sort(key=self._calculate_pickup_priority)
            
            # Collect items
            collected = 0
            for item in valuable_items:
                if self.is_inventory_full():
                    self.logger.info("Inventory full, stopping pickup")
                    break
                
                if self._pickup_item(item):
                    collected += 1
                    self.items_collected += 1
                    self._update_collection_stats(item)
                    
                    # Small delay between pickups
                    time.sleep(0.1)
            
            pickup_time = time.time() - start_time
            self.total_pickup_time += pickup_time
            
            if collected > 0:
                self.logger.info(f"Collected {collected} items in {pickup_time:.1f}s")
            
            return collected
            
        except Exception as e:
            self.logger.error(f"Error collecting loot: {e}")
            return 0
    
    def _get_nearby_items(self) -> List[Item]:
        """Get items within pickup radius"""
        try:
            # This would be implemented with actual API calls to get entities
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting nearby items: {e}")
            return []
    
    def _filter_valuable_items(self, items: List[Item]) -> List[Item]:
        """Filter items based on loot configuration"""
        valuable_items = []
        
        for item in items:
            if self._is_item_valuable(item):
                item.is_valuable = True
                valuable_items.append(item)
        
        return valuable_items
    
    def _is_item_valuable(self, item: Item) -> bool:
        """Check if an item is valuable and should be picked up"""
        try:
            # Check by item type
            if item.item_type == ItemType.CURRENCY:
                return self._is_currency_valuable(item)
            elif item.item_type == ItemType.DIVINATION_CARD:
                return self._is_divination_card_valuable(item)
            elif item.item_type == ItemType.UNIQUE:
                return self._is_unique_valuable(item)
            elif item.item_type == ItemType.RARE:
                return self.config.pickup_rares and item.item_level >= self.config.min_item_level
            elif item.item_type == ItemType.MAGIC:
                return self.config.pickup_magic and item.item_level >= self.config.min_item_level
            elif item.item_type == ItemType.NORMAL:
                return self.config.pickup_normal and item.item_level >= self.config.min_item_level
            elif item.item_type == ItemType.GEM:
                return self.config.pickup_gems
            elif item.item_type == ItemType.MAP:
                return self.config.pickup_maps
            elif item.item_type == ItemType.FLASK:
                return self.config.pickup_flasks
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking item value: {e}")
            return False
    
    def _is_currency_valuable(self, item: Item) -> bool:
        """Check if currency item is valuable"""
        if not self.config.pickup_currency:
            return False
        
        item_name = item.get_display_name()
        
        # Check if it's in the ignore list
        if item_name in self.config.ignore_currency:
            return False
        
        # Check if it's in the valuable list
        if item_name in self.config.valuable_currency:
            return True
        
        # Default to picking up currency not in ignore list
        return True
    
    def _is_divination_card_valuable(self, item: Item) -> bool:
        """Check if divination card is valuable"""
        if not self.config.pickup_divination_cards:
            return False
        
        item_name = item.get_display_name()
        
        # If we have a valuable list, check it
        if self.config.valuable_div_cards:
            return item_name in self.config.valuable_div_cards
        
        # Default to picking up all divination cards
        return True
    
    def _is_unique_valuable(self, item: Item) -> bool:
        """Check if unique item is valuable"""
        if not self.config.pickup_uniques:
            return False
        
        item_name = item.get_display_name()
        
        # If we have a valuable list, check it
        if self.config.valuable_uniques:
            return item_name in self.config.valuable_uniques
        
        # Default to picking up all uniques
        return True
    
    def _calculate_pickup_priority(self, item: Item) -> float:
        """Calculate pickup priority (lower = higher priority)"""
        priority = item.distance
        
        # Boost priority for valuable item types
        if item.item_type == ItemType.CURRENCY:
            priority *= 0.5
        elif item.item_type == ItemType.UNIQUE:
            priority *= 0.7
        elif item.item_type == ItemType.DIVINATION_CARD:
            priority *= 0.6
        elif item.item_type == ItemType.MAP:
            priority *= 0.8
        
        return priority
    
    def _pickup_item(self, item: Item) -> bool:
        """Pick up a specific item"""
        try:
            self.logger.debug(f"Picking up {item.get_display_name()}")
            
            # Move close to item if needed
            if item.distance > 15:  # Too far for pickup
                self._move_to_item(item)
                time.sleep(0.2)  # Wait for movement
            
            # Use coordinate fix to get safe click position
            from coordinate_fix import get_coordinate_fix
            coord_fix = get_coordinate_fix()
            
            # Convert item to entity dict for coordinate fix
            entity_dict = {
                'GridPosition': item.position,
                'location_on_screen': item.screen_position
            }
            
            screen_coords = coord_fix.get_entity_click_position(entity_dict)
            if screen_coords:
                self._click_position(screen_coords[0], screen_coords[1])
            else:
                self.logger.warning("Could not get valid screen coordinates for item")
                return False
            
            # Wait for pickup
            time.sleep(0.1)
            
            # Update inventory count
            self.current_inventory_slots += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error picking up item: {e}")
            return False
    
    def _move_to_item(self, item: Item):
        """Move closer to an item for pickup"""
        try:
            # Calculate position near the item
            player_pos = self._get_player_position()
            item_pos = item.position
            
            # Calculate direction vector
            dx = item_pos['X'] - player_pos['X']
            dy = item_pos['Y'] - player_pos['Y']
            distance = (dx*dx + dy*dy)**0.5
            
            if distance > 0:
                # Move to within pickup range
                move_distance = distance - 10  # Get within 10 units
                dx = dx / distance * move_distance
                dy = dy / distance * move_distance
                
                target_pos = {
                    'X': player_pos['X'] + dx,
                    'Y': player_pos['Y'] + dy
                }
                
                self._move_to_position(target_pos)
                
        except Exception as e:
            self.logger.error(f"Error moving to item: {e}")
    
    def _update_collection_stats(self, item: Item):
        """Update collection statistics"""
        if item.item_type == ItemType.CURRENCY:
            self.currency_collected += 1
        elif item.item_type == ItemType.UNIQUE:
            self.uniques_collected += 1
        elif item.item_type == ItemType.DIVINATION_CARD:
            self.div_cards_collected += 1
    
    def is_inventory_full(self) -> bool:
        """Check if inventory is full or nearly full"""
        return self.current_inventory_slots >= self.config.max_inventory_slots * self.config.inventory_full_threshold
    
    def has_valuable_items(self) -> bool:
        """Check if player has valuable items to stash"""
        # This would check actual inventory contents
        # For now, assume we have valuable items if we've collected any
        return self.items_collected > 0
    
    def stash_items(self) -> bool:
        """Stash valuable items"""
        try:
            self.logger.info("Stashing valuable items")
            
            # Find stash
            stash_entities = self._get_stash_entities()
            if not stash_entities:
                self.logger.error("No stash found")
                return False
            
            # Use the first stash found
            stash = stash_entities[0]
            
            # Move to stash if needed
            stash_distance = self._calculate_distance_to_entity(stash)
            if stash_distance > 20:
                self._move_to_stash(stash)
                time.sleep(1)  # Wait for movement
            
            # Open stash
            self._interact_with_stash(stash)
            time.sleep(0.5)  # Wait for stash to open
            
            # Transfer items
            transferred = self._transfer_items_to_stash()
            
            # Close stash
            self._send_key("Escape")
            time.sleep(0.2)
            
            # Update inventory count
            self.current_inventory_slots = max(0, self.current_inventory_slots - transferred)
            
            self.logger.info(f"Stashed {transferred} items")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stashing items: {e}")
            return False
    
    def _get_stash_entities(self) -> List[Dict[str, Any]]:
        """Get stash entities"""
        try:
            # This would be implemented with actual API calls
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting stash entities: {e}")
            return []
    
    def _move_to_stash(self, stash: Dict[str, Any]):
        """Move to stash entity"""
        try:
            stash_pos = stash['GridPosition']
            self._move_to_position(stash_pos)
            
        except Exception as e:
            self.logger.error(f"Error moving to stash: {e}")
    
    def _interact_with_stash(self, stash: Dict[str, Any]):
        """Interact with stash entity"""
        try:
            # Use coordinate fix to get safe click position
            from coordinate_fix import get_coordinate_fix
            coord_fix = get_coordinate_fix()
            
            screen_coords = coord_fix.get_entity_click_position(stash)
            if screen_coords:
                self._click_position(screen_coords[0], screen_coords[1])
            else:
                self.logger.warning("Could not get valid screen coordinates for stash")
            
        except Exception as e:
            self.logger.error(f"Error interacting with stash: {e}")
    
    def _transfer_items_to_stash(self) -> int:
        """Transfer items from inventory to stash"""
        try:
            # This would implement actual inventory management
            # For now, simulate transferring items
            transferred = min(self.current_inventory_slots, 20)  # Transfer up to 20 items
            
            # Simulate the transfer process
            time.sleep(transferred * 0.1)  # 0.1s per item
            
            return transferred
            
        except Exception as e:
            self.logger.error(f"Error transferring items: {e}")
            return 0
    
    def _calculate_distance_to_entity(self, entity: Dict[str, Any]) -> float:
        """Calculate distance to an entity"""
        try:
            player_pos = self._get_player_position()
            entity_pos = entity['GridPosition']
            
            dx = entity_pos['X'] - player_pos['X']
            dy = entity_pos['Y'] - player_pos['Y']
            
            return (dx*dx + dy*dy)**0.5
            
        except Exception as e:
            self.logger.error(f"Error calculating distance: {e}")
            return 0.0
    
    def _get_player_position(self) -> Dict[str, int]:
        """Get current player position"""
        # Placeholder - would be implemented with API call
        return {'X': 0, 'Y': 0, 'Z': 0}
    
    def _move_to_position(self, position: Dict[str, int]):
        """Move to a specific position"""
        # Placeholder - would be implemented with API call
        pass
    
    def _click_position(self, x: int, y: int):
        """Click at screen position"""
        try:
            from input_controller import click_position
            return click_position(x, y)
        except ImportError:
            self.logger.error("Input controller not available")
            return False
    
    def _send_key(self, key: str):
        """Send key press"""
        try:
            from input_controller import send_key
            return send_key(key)
        except ImportError:
            self.logger.error("Input controller not available")
            return False
    
    def get_loot_stats(self) -> Dict[str, Any]:
        """Get loot collection statistics"""
        return {
            'items_collected': self.items_collected,
            'currency_collected': self.currency_collected,
            'uniques_collected': self.uniques_collected,
            'div_cards_collected': self.div_cards_collected,
            'total_pickup_time': self.total_pickup_time,
            'current_inventory_slots': self.current_inventory_slots,
            'inventory_full': self.is_inventory_full()
        }
    
    def reset_stats(self):
        """Reset loot statistics"""
        self.items_collected = 0
        self.currency_collected = 0
        self.uniques_collected = 0
        self.div_cards_collected = 0
        self.total_pickup_time = 0.0
        self.current_inventory_slots = 0
    
    def update_inventory_count(self, count: int):
        """Update current inventory slot count"""
        self.current_inventory_slots = max(0, count)
    
    def clear_inventory(self):
        """Clear inventory count (after stashing)"""
        self.current_inventory_slots = 0

# Helper functions for item type detection
def detect_item_type(path: str, name: str = "") -> ItemType:
    """Detect item type from path or name"""
    path_lower = path.lower()
    name_lower = name.lower()
    
    # Currency detection
    if 'currency' in path_lower or any(curr in name_lower for curr in ['orb', 'shard', 'essence', 'fossil']):
        return ItemType.CURRENCY
    
    # Divination card detection
    if 'divinationcards' in path_lower or 'divination' in name_lower:
        return ItemType.DIVINATION_CARD
    
    # Map detection
    if 'maps' in path_lower or 'map' in name_lower:
        return ItemType.MAP
    
    # Gem detection
    if 'gems' in path_lower or 'gem' in name_lower:
        return ItemType.GEM
    
    # Flask detection
    if 'flasks' in path_lower or 'flask' in name_lower:
        return ItemType.FLASK
    
    # Default to unknown
    return ItemType.UNKNOWN

def create_loot_config(farming_type: str = "default") -> LootConfig:
    """Create loot configuration based on farming type"""
    
    configs = {
        "currency_farming": LootConfig(
            pickup_currency=True,
            pickup_divination_cards=True,
            pickup_uniques=False,
            pickup_rares=False,
            pickup_magic=False,
            pickup_normal=False,
            pickup_gems=False,
            pickup_maps=True,
            pickup_flasks=False
        ),
        "general_farming": LootConfig(
            pickup_currency=True,
            pickup_divination_cards=True,
            pickup_uniques=True,
            pickup_rares=True,
            pickup_magic=False,
            pickup_normal=False,
            pickup_gems=True,
            pickup_maps=True,
            pickup_flasks=False,
            min_item_level=75
        ),
        "speed_farming": LootConfig(
            pickup_currency=True,
            pickup_divination_cards=True,
            pickup_uniques=True,
            pickup_rares=False,
            pickup_magic=False,
            pickup_normal=False,
            pickup_gems=False,
            pickup_maps=True,
            pickup_flasks=False,
            pickup_radius=30.0  # Smaller radius for speed
        )
    }
    
    return configs.get(farming_type, LootConfig()) 