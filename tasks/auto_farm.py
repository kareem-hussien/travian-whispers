import time
import random
import logging
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from startup.browser_profile import check_for_captcha, check_for_ban, handle_detection_event

# Configure logger
logger = logging.getLogger(__name__)

# Travian farm list URL
FARM_LIST_URL = "https://ts1.x1.international.travian.com/build.php?id=39&gid=16&tt=99"

def send_farm_list(driver, user_id=None):
    """
    Clicks the 'Start all farm lists' button.
    
    Args:
        driver (webdriver.Chrome): Chrome WebDriver instance
        user_id (str, optional): User ID for detection handling
        
    Returns:
        bool: True if farm lists were sent successfully, False otherwise
    """
    try:
        logger.info("Navigating to farm list page")
        driver.get(FARM_LIST_URL)
        time.sleep(3)
        
        # Check for CAPTCHA or bans before proceeding
        if check_for_captcha(driver):
            logger.warning("CAPTCHA detected during farm list operation")
            if user_id:
                handle_detection_event(driver, user_id, "captcha")
            return False
        
        banned, reason = check_for_ban(driver)
        if banned:
            logger.critical(f"Ban detected during farm list operation: {reason}")
            if user_id:
                handle_detection_event(driver, user_id, "ban", {"reason": reason})
            return False
        
        # Look for the start all button
        try:
            start_all_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'startAllFarmLists')]"))
            )
            
            # Click the button
            start_all_button.click()
            logger.info("Clicked 'Start all farm lists' button!")
            
            # Verify success (optional - you might look for a confirmation message)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"'Start all farm lists' button not found: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Could not send farm list: {e}")
        return False

def run_auto_farm(driver, user_id=None, max_runtime=None, interval_range=(1800, 2700)):
    """
    Runs the farm list automation in a loop.
    
    Args:
        driver (webdriver.Chrome): Chrome WebDriver instance
        user_id (str, optional): User ID for detection handling
        max_runtime (int, optional): Maximum runtime in seconds
        interval_range (tuple, optional): Range of wait times between farms (min, max) in seconds
        
    Returns:
        dict: Summary of auto farm session
    """
    start_time = datetime.now()
    end_time = None if max_runtime is None else start_time + timedelta(seconds=max_runtime)
    
    farm_count = 0
    success_count = 0
    failure_count = 0
    
    logger.info(f"Starting auto farm for user {user_id if user_id else 'Anonymous'}")
    
    try:
        while True:
            # Check if we've exceeded max runtime
            if end_time and datetime.now() >= end_time:
                logger.info(f"Maximum runtime reached ({max_runtime} seconds)")
                break
            
            # Send farm lists
            farm_count += 1
            success = send_farm_list(driver, user_id)
            
            if success:
                success_count += 1
            else:
                failure_count += 1
                
                # Check if we need to rotate IP or session
                if failure_count >= 3:
                    logger.warning("Multiple farm list failures detected, considering rotation")
                    if user_id:
                        result = handle_detection_event(driver, user_id, "suspicious", 
                                                     {"operation": "auto_farm", "failures": failure_count})
                        
                        # If rotation requires restart, return with status
                        if result.get("requires_restart", False):
                            logger.info("Browser restart required after rotation")
                            return {
                                "status": "rotation_required",
                                "farm_count": farm_count,
                                "success_count": success_count,
                                "failure_count": failure_count,
                                "runtime": (datetime.now() - start_time).total_seconds(),
                                "rotation_info": result
                            }
            
            # Calculate wait time for next cycle
            wait_time = random.randint(interval_range[0], interval_range[1])
            next_run = datetime.now() + timedelta(seconds=wait_time)
            
            logger.info(f"Waiting {wait_time/60:.2f} minutes before next farm list send. Next run at {next_run.strftime('%H:%M:%S')}")
            
            # If max_runtime is set, check if the next run would exceed it
            if end_time and next_run >= end_time:
                logger.info("Next run would exceed maximum runtime, ending auto farm")
                break
                
            # Wait until next cycle
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        logger.info("Auto farm interrupted by user")
    except Exception as e:
        logger.error(f"Auto farm error: {e}")
        failure_count += 1
    
    # Return summary
    total_runtime = (datetime.now() - start_time).total_seconds()
    return {
        "status": "completed",
        "farm_count": farm_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "runtime": total_runtime
    }