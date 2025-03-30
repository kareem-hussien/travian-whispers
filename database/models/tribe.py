"""
Tribe data model for Travian Whispers web application.
This module provides tribe-specific data and configurations.
"""
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class TribeData:
    """Tribe data model for accessing tribe-specific information."""
    
    def __init__(self):
        """Initialize tribe data model with predefined tribe information."""
        # Define troop types for each tribe
        self.tribe_troops = {
            'romans': [
                'legionnaire', 'praetorian', 'imperian', 
                'equites_legati', 'equites_imperatoris', 'equites_caesaris',
                'battering_ram', 'fire_catapult', 'senator'
            ],
            'gauls': [
                'phalanx', 'swordsman', 'pathfinder', 
                'theutates_thunder', 'druidrider', 'haeduan',
                'ram', 'trebuchet', 'chieftain'
            ],
            'teutons': [
                'clubswinger', 'spearman', 'axeman', 
                'scout', 'paladin', 'teutonic_knight',
                'ram', 'catapult', 'chief'
            ],
            'egyptians': [
                'slave_militia', 'ash_warden', 'khopesh_warrior',
                'sopdu_explorer', 'anhur_guard', 'resheph_chariot',
                'ram', 'stone_catapult', 'nomarch'
            ],
            'huns': [
                'mercenary', 'bowman', 'spotter',
                'steppe_rider', 'marksman', 'marauder',
                'ram', 'catapult', 'logades'
            ]
        }
        
        # Define troop costs for each tribe (food, clay, iron, crop, time in seconds)
        self.troop_costs = {
            'romans': {
                'legionnaire': [120, 100, 150, 30, 2000],
                'praetorian': [100, 130, 160, 70, 2200],
                'imperian': [150, 160, 210, 80, 2400],
                'equites_legati': [140, 160, 20, 40, 2200],
                'equites_imperatoris': [550, 440, 320, 100, 2800],
                'equites_caesaris': [550, 640, 800, 180, 3600],
                'battering_ram': [900, 360, 500, 70, 5000],
                'fire_catapult': [950, 1350, 600, 90, 9000],
                'senator': [30750, 27200, 45000, 37500, 90700]
            },
            # Add costs for other tribes similarly
        }
    
    def get_troop_types(self, tribe):
        """
        Get list of troop types for a tribe.
        
        Args:
            tribe (str): Tribe name ('romans', 'gauls', 'teutons', 'egyptians', 'huns')
        
        Returns:
            list: List of troop types or empty list if tribe not found
        """
        # Convert tribe to lowercase
        tribe = tribe.lower()
        
        # Return troop types for the tribe
        return self.tribe_troops.get(tribe, [])
    
    def get_troop_cost(self, tribe, troop_type):
        """
        Get cost and training time for a specific troop type.
        
        Args:
            tribe (str): Tribe name
            troop_type (str): Troop type identifier
        
        Returns:
            dict: Cost and training time information or None if not found
        """
        # Convert tribe to lowercase
        tribe = tribe.lower()
        
        # Get costs for the tribe and troop type
        costs = self.troop_costs.get(tribe, {}).get(troop_type)
        
        if costs:
            return {
                'resources': {
                    'wood': costs[0],
                    'clay': costs[1],
                    'iron': costs[2],
                    'crop': costs[3]
                },
                'time': costs[4]  # Training time in seconds
            }
        
        return None
    
    def get_tribe_names(self):
        """
        Get list of all tribe names.
        
        Returns:
            list: List of tribe names
        """
        return list(self.tribe_troops.keys())
    
    def get_all_troop_types(self):
        """
        Get all troop types from all tribes.
        
        Returns:
            dict: Dictionary mapping tribe name to list of troop types
        """
        return self.tribe_troops.copy()
