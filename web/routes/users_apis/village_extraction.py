"""
Village extraction module for Travian Whispers.
This module provides functions for extracting villages from Travian.
"""
import logging
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize logger
logger = logging.getLogger(__name__)

def extract_villages_internal(user_id):
    """
    Extract villages internally (without HTTP request/response).
    This can be called from travian_settings when a user adds/updates their account.
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: Result dictionary with keys 'success', 'message', and optionally 'data'
    """
    from database.models.user import User
    from database.models.activity_log import ActivityLog
    
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        return {
            'success': False,
            'message': 'User not found'
        }
    
    # Check if Travian credentials are set
    if not user['travianCredentials'].get('username') or not user['travianCredentials'].get('password'):
        return {
            'success': False,
            'message': 'Travian credentials not set'
        }
    
    driver = None
    
    try:
        # Set up detailed logging
        logger.info(f"Starting internal village extraction for user {user['username']} (ID: {user_id})")
        
        # Get Travian credentials
        travian_username = user['travianCredentials']['username']
        travian_password = user['travianCredentials']['password']
        travian_server = user['travianCredentials'].get('server', 'https://ts1.x1.international.travian.com')
        
        logger.info(f"Using server URL: {travian_server}")
        
        # Setup browser
        try:
            logger.info("Setting up browser for internal village extraction")
            
            # Check for Selenium remote URL
            selenium_url = os.environ.get('SELENIUM_REMOTE_URL')
            logger.info(f"Selenium remote URL: {selenium_url if selenium_url else 'Not set - using local browser'}")
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Initialize the WebDriver
            if selenium_url:
                logger.info(f"Using Selenium Grid at {selenium_url} for village extraction")
                try:
                    driver = webdriver.Remote(
                        command_executor=selenium_url,
                        options=chrome_options
                    )
                    logger.info("Successfully connected to Selenium Grid")
                except Exception as e:
                    logger.warning(f"Failed to connect to Selenium Grid: {e}. Falling back to local Chrome.")
                    selenium_url = None  # Force fallback to local Chrome
            
            if not selenium_url:
                # If no Selenium Grid, use local Chrome
                logger.info("Using local Chrome for village extraction")
                # Check if we need to specify the service object
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("Using webdriver_manager to set up ChromeDriver")
                except ImportError:
                    logger.info("webdriver_manager not available, using default Chrome setup")
                    driver = webdriver.Chrome(options=chrome_options)
            
            logger.info("Browser setup successful")
        except Exception as e:
            logger.error(f"Error setting up browser: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to set up browser: {str(e)}'
            }
        
        # Login to Travian
        try:
            logger.info(f"Attempting to log in to Travian as {travian_username}")
            
            # Basic login implementation
            if not travian_server.startswith(('http://', 'https://')):
                travian_server = f"https://{travian_server}"
                
            driver.get(travian_server)
            time.sleep(2)
            
            # Check if we're already on a login page or need to navigate to it
            if "login" not in driver.current_url.lower():
                # Try to find and click a login link
                try:
                    login_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'login')]")
                    if login_links:
                        login_links[0].click()
                        time.sleep(2)
                    else:
                        # Directly navigate to login page
                        driver.get(f"{travian_server}/login.php")
                        time.sleep(2)
                except:
                    # Direct navigation as fallback
                    driver.get(f"{travian_server}/login.php")
                    time.sleep(2)
            
            # Find login form elements
            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "name"))
                )
                password_field = driver.find_element(By.NAME, "password")
                
                # Enter credentials
                username_field.clear()
                username_field.send_keys(travian_username)
                password_field.clear()
                password_field.send_keys(travian_password)
                
                # Find login button
                login_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                
                if login_buttons:
                    login_buttons[0].click()
                    time.sleep(3)  # Wait for login to process
                else:
                    # Try alternate button locators
                    login_buttons = driver.find_elements(By.XPATH, "//button[contains(.,'Login') or contains(.,'Sign in')]")
                    if login_buttons:
                        login_buttons[0].click()
                        time.sleep(3)
                    else:
                        # Last resort - try by form submission
                        form = driver.find_element(By.TAG_NAME, "form")
                        if form:
                            form.submit()
                            time.sleep(3)
                
                # Check if login was successful by looking for typical elements on the game page
                try:
                    # Wait for map or resources to appear, which indicates successful login
                    WebDriverWait(driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.ID, "village_map")),
                            EC.presence_of_element_located((By.ID, "navigation")),
                            EC.presence_of_element_located((By.ID, "resources"))
                        )
                    )
                    logger.info("Login successful - found game elements")
                    login_successful = True
                except Exception as e:
                    # If we didn't find game elements, login probably failed
                    logger.warning(f"Login failed - couldn't find game elements: {e}")
                    login_successful = False
            except Exception as e:
                logger.error(f"Error finding or interacting with login elements: {str(e)}")
                login_successful = False
            
            if not login_successful:
                logger.error("Login failed - invalid credentials or Travian site changes")
                if driver:
                    driver.quit()
                return {
                    'success': False,
                    'message': 'Failed to log in to Travian. Please check your credentials or try again later.'
                }
            logger.info("Login successful")
        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            if driver:
                driver.quit()
            return {
                'success': False,
                'message': f'Error during login: {str(e)}'
            }
        
        # Extract villages
        try:
            logger.info("Running village extraction")
            from tasks.villages import run_villages
            
            extracted_villages = run_villages(driver)
            
            if not extracted_villages:
                logger.error("No villages were extracted")
                if driver:
                    driver.quit()
                return {
                    'success': False,
                    'message': 'No villages were extracted. Please try again.'
                }
            
            logger.info(f"Successfully extracted {len(extracted_villages)} villages")
            for idx, village in enumerate(extracted_villages):
                logger.info(f"Village {idx+1}: {village['name']} ({village['x']}|{village['y']})")
                
        except Exception as e:
            logger.error(f"Error extracting villages: {str(e)}", exc_info=True)
            if driver:
                driver.quit()
            return {
                'success': False,
                'message': f'Error extracting villages: {str(e)}'
            }
        
        # Close browser
        if driver:
            driver.quit()
            logger.info("Browser closed")
        
        # Preserve existing settings when updating villages
        current_villages = user.get('villages', [])
        village_settings = {}
        
        # Create a map of existing village settings by newdid
        for village in current_villages:
            newdid = village.get('newdid')
            if newdid:
                village_settings[newdid] = {
                    'auto_farm_enabled': village.get('auto_farm_enabled', False),
                    'training_enabled': village.get('training_enabled', False)
                }
        
        # Apply existing settings to extracted villages
        for village in extracted_villages:
            newdid = village.get('newdid')
            if newdid and newdid in village_settings:
                village['auto_farm_enabled'] = village_settings[newdid]['auto_farm_enabled']
                village['training_enabled'] = village_settings[newdid]['training_enabled']
            else:
                # Default settings for new villages - ENABLE auto-farm by default for better UX
                village['auto_farm_enabled'] = True  # Enable auto-farm by default
                village['training_enabled'] = False
        
        # Update user's villages in database
        logger.info("Updating user's villages in database")
        if user_model.update_user(user_id, {'villages': extracted_villages}):
            # Log the activity
            activity_model = ActivityLog()
            activity_model.log_activity(
                user_id=user_id,
                activity_type='village-extract',
                details=f"Automatically extracted {len(extracted_villages)} villages from Travian",
                status='success'
            )
            
            logger.info(f"User '{user['username']}' extracted {len(extracted_villages)} villages from Travian")
            return {
                'success': True,
                'message': f'Successfully extracted {len(extracted_villages)} villages',
                'data': extracted_villages
            }
        else:
            logger.warning(f"Failed to save extracted villages for user '{user['username']}'")
            return {
                'success': False,
                'message': 'Failed to save extracted villages'
            }
            
    except Exception as e:
        logger.error(f"Error extracting villages for user '{user['username']}': {str(e)}", exc_info=True)
        if driver:
            try:
                driver.quit()
            except:
                pass
        return {
            'success': False,
            'message': f'Error extracting villages: {str(e)}'
        }
