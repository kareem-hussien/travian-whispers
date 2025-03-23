import time
import random
import logging
import os
from datetime import datetime, timedelta
from tasks.trainer.trainer_data import read_building_urls, read_troop_mappings
from tasks.trainer.trainer_actions import train_troops
from startup.browser_profile import check_for_captcha, check_for_ban, handle_detection_event

# Configure logger
logger = logging.getLogger(__name__)

def get_account_tribe(filepath="info/profile/tribe.txt"):
    """
    Reads the account tribe from the specified file.
    Expected format: "Tribe,ProfileID"
    
    Args:
        filepath (str): Path to the tribe file
        
    Returns:
        str: The tribe as a string or None if not found
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Check if file exists
        if not os.path.exists(filepath):
            logger.error(f"Tribe file does not exist: {filepath}")
            return None
            
        with open(filepath, "r") as f:
            data = f.read().strip()
            if not data:
                logger.error("Tribe file is empty! Please update your profile first.")
                return None
                
            parts = data.split(",")
            return parts[0].strip() if parts else None
            
    except Exception as e:
        logger.error(f"Unable to read tribe file: {e}")
        return None

def train_troop_with_detection(driver, url, troop_number, troop_type, count, user_id=None):
    """
    Train troops with detection handling.
    
    Args:
        driver (webdriver.Chrome): Chrome WebDriver instance
        url (str): URL of the building
        troop_number (str): Troop identifier
        troop_type (str): Type of troop for logging
        count (int): Number of troops to train
        user_id (str, optional): User ID for detection handling
        
    Returns:
        bool: True if troops were trained successfully
    """
    try:
        # Navigate to building
        logger.info(f"Training {count} {troop_type}")
        driver.get(url)
        time.sleep(2)
        
        # Check for CAPTCHA or bans before proceeding
        if check_for_captcha(driver):
            logger.warning("CAPTCHA detected during troop training")
            if user_id:
                handle_detection_event(driver, user_id, "captcha")
            return False
        
        banned, reason = check_for_ban(driver)
        if banned:
            logger.critical(f"Ban detected during troop training: {reason}")
            if user_id:
                handle_detection_event(driver, user_id, "ban", {"reason": reason})
            return False
            
        # Train troops
        success = train_troops(driver, url, troop_number, troop_type, count)
        
        if not success and user_id:
            # Report suspicious activity
            handle_detection_event(driver, user_id, "suspicious", 
                                {"operation": "troop_training", "troop_type": troop_type})
        
        return success
    
    except Exception as e:
        logger.error(f"Error training troops: {e}")
        return False

def run_trainer(driver, user_id=None, max_runtime=None, interval_range=(1800, 3600)):
    """
    Main function to run the troop training automation.
    
    Args:
        driver (webdriver.Chrome): Chrome WebDriver instance
        user_id (str, optional): User ID for detection handling
        max_runtime (int, optional): Maximum runtime in seconds
        interval_range (tuple, optional): Range of wait times between training (min, max) in seconds
        
    Returns:
        dict: Summary of trainer session
    """
    start_time = datetime.now()
    end_time = None if max_runtime is None else start_time + timedelta(seconds=max_runtime)
    
    train_count = 0
    success_count = 0
    failure_count = 0
    
    logger.info(f"Starting troop trainer for user {user_id if user_id else 'Anonymous'}")
    
    # Step 1: Get the user's tribe
    account_tribe = get_account_tribe("info/profile/tribe.txt")
    if not account_tribe:
        logger.error("Unable to determine account tribe. Exiting trainer.")
        return {
            "status": "error",
            "message": "Unable to determine account tribe"
        }

    logger.info(f"Account tribe: {account_tribe}")

    # Step 2: Load troop mappings & filter based on tribe
    troops_map = read_troop_mappings("info/maps/troops-maps.txt")
    filtered_troops = [(troop_type, building, troop_number) for troop_type, building, troop_number, tribe in troops_map if tribe.lower() == account_tribe.lower()]

    if not filtered_troops:
        logger.error(f"No troop data found for tribe: {account_tribe}. Exiting trainer.")
        return {
            "status": "error",
            "message": f"No troop data found for tribe: {account_tribe}"
        }
    
    # Step 3: Display filtered troops for selection if interactive mode
    # For automated mode, we'll use a predefined selection or all available troops
    selected_troops = filtered_troops  # Use all available troops for now
    
    # Step 4: Load building URLs
    building_urls = read_building_urls("info/maps/buildings.txt")
    if not building_urls:
        logger.error("Building URLs not loaded. Exiting trainer.")
        return {
            "status": "error",
            "message": "Building URLs not loaded"
        }
    
    try:
        while True:
            # Check if we've exceeded max runtime
            if end_time and datetime.now() >= end_time:
                logger.info(f"Maximum runtime reached ({max_runtime} seconds)")
                break
            
            # Training parameters
            troop_count = random.randint(20, 100)
            
            # Train each selected troop type
            for troop_type, building, troop_number in selected_troops:
                url = building_urls.get(building)
                if url:
                    train_count += 1
                    success = train_troop_with_detection(driver, url, troop_number, troop_type, troop_count, user_id)
                    
                    if success:
                        success_count += 1
                        logger.info(f"Successfully trained {troop_count} {troop_type}")
                    else:
                        failure_count += 1
                        logger.warning(f"Failed to train {troop_type}")
                        
                        # Check if we need to rotate IP or session
                        if failure_count >= 3:
                            logger.warning("Multiple training failures detected, considering rotation")
                            if user_id:
                                result = handle_detection_event(driver, user_id, "suspicious", 
                                                             {"operation": "troop_training", "failures": failure_count})
                                
                                # If rotation requires restart, return with status
                                if result.get("requires_restart", False):
                                    logger.info("Browser restart required after rotation")
                                    return {
                                        "status": "rotation_required",
                                        "train_count": train_count,
                                        "success_count": success_count,
                                        "failure_count": failure_count,
                                        "runtime": (datetime.now() - start_time).total_seconds(),
                                        "rotation_info": result
                                    }
                    
                    # Small delay between training different troops
                    time.sleep(random.randint(5, 15))
                else:
                    logger.error(f"URL for building '{building}' not found.")
            
            # Calculate wait time for next cycle
            wait_time = random.randint(interval_range[0], interval_range[1])
            next_run = datetime.now() + timedelta(seconds=wait_time)
            
            logger.info(f"Waiting {wait_time/60:.2f} minutes until next training cycle. Next run at {next_run.strftime('%H:%M:%S')}")
            
            # If max_runtime is set, check if the next run would exceed it
            if end_time and next_run >= end_time:
                logger.info("Next run would exceed maximum runtime, ending troop trainer")
                break
                
            # Wait until next cycle
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        logger.info("Troop trainer interrupted by user")
    except Exception as e:
        logger.error(f"Troop trainer error: {e}")
        failure_count += 1
    
    # Return summary
    total_runtime = (datetime.now() - start_time).total_seconds()
    return {
        "status": "completed",
        "train_count": train_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "runtime": total_runtime
    }
