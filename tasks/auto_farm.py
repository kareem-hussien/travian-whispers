# File: tasks/auto_farm.py

import logging
import time
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logger
logger = logging.getLogger(__name__)

class AutoFarm:
    """
    Auto Farm task for Travian.
    Automatically sends farm raids at regular intervals.
    """
    
    def __init__(self, driver, user_id=None):
        """
        Initialize the Auto Farm task.
        
        Args:
            driver: WebDriver instance
            user_id (str, optional): User ID for logging
        """
        self.driver = driver
        self.user_id = user_id
        self.running = False
        self.villages = []
        self.interval = 30  # Default: 30 minutes
        self.randomize = 5   # Default: ±5 minutes randomization
        
        # If user_id provided, load settings from database
        if user_id:
            self._load_settings()
    
    def _load_settings(self):
        """Load Auto Farm settings from database."""
        try:
            from database.models.auto_farm import AutoFarmConfiguration
            
            # Get configuration from database
            auto_farm_model = AutoFarmConfiguration()
            config = auto_farm_model.get_user_configuration(self.user_id)
            
            if config:
                self.interval = config.get('interval', 30)
                self.randomize = config.get('randomize', 5)
                logger.info(f"Loaded Auto Farm settings: interval={self.interval}m, randomize=±{self.randomize}m")
        except ImportError:
            logger.warning("AutoFarmConfiguration model not available. Using default settings.")
        except Exception as e:
            logger.error(f"Error loading Auto Farm settings: {e}")
    
    def _get_next_interval(self):
        """
        Get the next interval with randomization.
        
        Returns:
            int: Interval in minutes
        """
        if self.randomize > 0:
            # Add randomization within specified range
            return self.interval + random.randint(-self.randomize, self.randomize)
        return self.interval
    
    def _log_activity(self, village_name, farm_lists_sent, status='success'):
        """
        Log Auto Farm activity to database.
        
        Args:
            village_name (str): Village name
            farm_lists_sent (int): Number of farm lists sent
            status (str): Activity status
        """
        if not self.user_id:
            return
            
        try:
            from database.models.activity_log import ActivityLog
            
            # Create activity log
            activity_model = ActivityLog()
            activity_model.log_activity(
                user_id=self.user_id,
                activity_type='auto-farm',
                details=f"Sent {farm_lists_sent} farm lists from {village_name}",
                status=status,
                village=village_name,
                data={
                    'farm_lists_sent': farm_lists_sent,
                    'next_interval': self._get_next_interval()
                }
            )
        except ImportError:
            logger.warning("ActivityLog model not available. Activity not logged.")
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def _get_villages(self):
        """
        Get list of villages from database or directly from Travian.
        
        Returns:
            list: List of village data
        """
        if self.user_id:
            try:
                # Get villages from database
                from database.models.user import User
                
                user_model = User()
                user = user_model.get_user_by_id(self.user_id)
                
                if user and 'villages' in user:
                    # Filter for villages with auto farm enabled
                    villages = [v for v in user['villages'] if v.get('auto_farm_enabled', True)]
                    
                    if villages:
                        logger.info(f"Found {len(villages)} villages with Auto Farm enabled")
                        return villages
            except ImportError:
                logger.warning("User model not available. Will extract villages directly.")
            except Exception as e:
                logger.error(f"Error getting villages from database: {e}")
        
        # Fallback: Extract villages directly from Travian
        try:
            from startup.villages_list import extract_villages
            
            villages = extract_villages(self.driver)
            logger.info(f"Extracted {len(villages)} villages directly from Travian")
            return villages
        except ImportError:
            logger.error("villages_list module not available. Cannot extract villages.")
            return []
        except Exception as e:
            logger.error(f"Error extracting villages: {e}")
            return []
    
    def run_farm_lists(self, max_iterations=None):
        """
        Run the Auto Farm task.
        
        Args:
            max_iterations (int, optional): Maximum number of iterations
            
        Returns:
            bool: True if completed successfully, False otherwise
        """
        try:
            logger.info("Starting Auto Farm task")
            self.running = True
            iterations = 0
            
            # Get villages
            self.villages = self._get_villages()
            
            if not self.villages:
                logger.error("No villages found for Auto Farm")
                self.running = False
                return False
            
            # Main loop
            while self.running:
                # Check if max iterations reached
                if max_iterations is not None and iterations >= max_iterations:
                    logger.info(f"Reached maximum iterations ({max_iterations}). Stopping Auto Farm.")
                    self.running = False
                    break
                
                start_time = datetime.now()
                logger.info(f"Starting Auto Farm iteration {iterations + 1}")
                
                # Process each village
                for village in self.villages:
                    village_name = village.get('name', 'Unknown Village')
                    logger.info(f"Processing village: {village_name}")
                    
                    try:
                        # Switch to village
                        self._switch_to_village(village)
                        
                        # Send farm lists
                        farm_lists_sent = self._send_farm_lists(village)
                        
                        # Log activity
                        self._log_activity(village_name, farm_lists_sent)
                        
                    except Exception as e:
                        logger.error(f"Error processing village {village_name}: {e}")
                        self._log_activity(village_name, 0, 'error')
                
                # Calculate next run time
                iterations += 1
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds() / 60  # Convert to minutes
                
                next_interval = self._get_next_interval()
                wait_time = max(0, next_interval - elapsed_time)
                
                logger.info(f"Auto Farm iteration {iterations} completed in {elapsed_time:.1f} minutes")
                logger.info(f"Next iteration in {wait_time:.1f} minutes")
                
                # Wait until next iteration
                if self.running and wait_time > 0:
                    time.sleep(wait_time * 60)  # Convert to seconds
            
            logger.info("Auto Farm task stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error in Auto Farm task: {e}")
            self.running = False
            return False
    
    def _switch_to_village(self, village):
        """
        Switch to the specified village.
        
        Args:
            village (dict): Village data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            village_id = village.get('newdid')
            village_name = village.get('name', 'Unknown Village')
            
            if not village_id:
                logger.warning(f"Village {village_name} has no ID (newdid). Cannot switch.")
                return False
            
            # Navigate to village URL
            self.driver.get(f"https://ts1.x1.international.travian.com/dorf1.php?newdid={village_id}")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "village_map"))
            )
            
            logger.info(f"Switched to village: {village_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error switching to village: {e}")
            return False
    
    def _send_farm_lists(self, village):
        """
        Send farm lists for the current village.
        
        Args:
            village (dict): Village data
            
        Returns:
            int: Number of farm lists sent
        """
        try:
            # Navigate to rally point and farm lists
            self.driver.get(self.driver.current_url.split('?')[0] + "?t=3&tt=99")
            
            # Wait for farm lists to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "raidList"))
            )
            
            # Find farm list start buttons
            start_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.startButton")
            
            # Count how many were actually sent
            sent_count = 0
            
            # Click each start button
            for button in start_buttons:
                try:
                    button.click()
                    time.sleep(0.5)  # Short delay between clicks
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"Error clicking farm list button: {e}")
            
            logger.info(f"Sent {sent_count} farm lists from {village.get('name', 'Unknown Village')}")
            return sent_count
            
        except TimeoutException:
            logger.warning("Timeout waiting for farm lists to load")
            return 0
        except NoSuchElementException:
            logger.warning("Farm lists or buttons not found")
            return 0
        except Exception as e:
            logger.error(f"Error sending farm lists: {e}")
            return 0
    
    def stop(self):
        """Stop the Auto Farm task."""
        logger.info("Stopping Auto Farm task")
        self.running = False