# File: startup/browser_profile.py

import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logger
logger = logging.getLogger(__name__)

def setup_browser(user_id=None, headless=True):
    """
    Setup Chrome browser using Selenium Grid if available.
    
    Args:
        user_id (str, optional): User ID for session management
        headless (bool): Whether to run browser in headless mode
        
    Returns:
        webdriver.Chrome: Configured WebDriver instance
    """
    # Configure Chrome options
    chrome_options = Options()
    
    # Set headless mode based on environment variable or parameter
    env_headless = os.environ.get('HEADLESS', 'true').lower() == 'true'
    if headless or env_headless:
        chrome_options.add_argument("--headless")
    
    # Set common arguments
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add user agent to avoid detection
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Set profile parameters if user_id is provided
    if user_id:
        # Add a custom profile path based on user_id
        profile_dir = os.path.join(os.getcwd(), 'info', 'profile', str(user_id))
        
        # Create directory if it doesn't exist
        os.makedirs(profile_dir, exist_ok=True)
        
        # Set user data directory
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        logger.info(f"Using Chrome profile directory: {profile_dir}")
    
    # Check if Selenium Grid URL is configured
    selenium_url = os.environ.get('SELENIUM_REMOTE_URL')
    
    # Initialize the WebDriver
    if selenium_url:
        logger.info(f"Using Selenium Grid at {selenium_url}")
        
        # Create remote WebDriver
        try:
            driver = webdriver.Remote(
                command_executor=selenium_url,
                options=chrome_options
            )
            logger.info("Successfully connected to Selenium Grid")
        except Exception as e:
            logger.error(f"Error connecting to Selenium Grid: {e}")
            raise
    else:
        logger.info("Selenium Grid URL not found. Using local Chrome WebDriver.")
        
        # Fallback to local WebDriver
        driver = webdriver.Chrome(options=chrome_options)
    
    # Configure browser
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
    
    return driver

def login_only(driver, username, password, server_url=None):
    """
    Login to Travian with the provided credentials.
    
    Args:
        driver: WebDriver instance
        username (str): Travian username
        password (str): Travian password
        server_url (str, optional): Travian server URL
        
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        # Default server URL if none provided
        if not server_url:
            server_url = "https://ts1.x1.international.travian.com"
        
        # Ensure server URL starts with protocol
        if not server_url.startswith(('http://', 'https://')):
            server_url = f"https://{server_url}"
        
        logger.info(f"Logging in to Travian at {server_url}")
        
        # Navigate to server URL
        driver.get(server_url)
        time.sleep(2)  # Allow page to load
        
        # Check if we need to navigate to login page
        if "login" not in driver.current_url.lower() and "dorf1.php" not in driver.current_url.lower():
            # Try to find and click login button
            try:
                login_link = driver.find_element(By.XPATH, "//a[contains(@href, 'login.php')]")
                login_link.click()
                time.sleep(2)
            except NoSuchElementException:
                # If login link not found, navigate directly to login page
                driver.get(f"{server_url}/login.php")
                time.sleep(2)
        
        # Check if already logged in
        if "dorf1.php" in driver.current_url or "village" in driver.current_url:
            logger.info("Already logged in to Travian.")
            return True
        
        # Fill in login form
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "name"))
            )
            password_field = driver.find_element(By.NAME, "password")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Find and click login button
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_button.click()
            
            # Wait for successful login (redirect to village page)
            WebDriverWait(driver, 15).until(
                lambda d: "dorf1.php" in d.current_url or 
                           "village" in d.current_url or 
                           "game.php" in d.current_url
            )
            
            logger.info("Successfully logged in to Travian.")
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Login failed: {str(e)}")
            
            # Check for error messages
            try:
                error_elements = driver.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_message = error_elements[0].text
                    logger.error(f"Login error: {error_message}")
            except:
                pass
                
            return False
            
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return False

def update_profile(driver):
    """
    Extract profile information from Travian account.
    
    Args:
        driver: WebDriver instance with active Travian session
        
    Returns:
        tuple: (tribe, profile_id) if successful, None otherwise
    """
    try:
        # Navigate to profile page
        driver.get(driver.current_url.split('?')[0] + "?profile")
        time.sleep(2)
        
        # Extract tribe information
        tribe_element = None
        tribe = "unknown"
        
        try:
            # Try to find tribe information in profile
            tribe_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Tribe')]/following-sibling::td")
            if tribe_element:
                tribe_text = tribe_element.text.strip().lower()
                
                # Map tribe text to internal representation
                if "roman" in tribe_text:
                    tribe = "romans"
                elif "gaul" in tribe_text:
                    tribe = "gauls"
                elif "teuton" in tribe_text:
                    tribe = "teutons"
                elif "egyptian" in tribe_text:
                    tribe = "egyptians"
                elif "hun" in tribe_text:
                    tribe = "huns"
        except NoSuchElementException:
            # Try alternative method to detect tribe
            try:
                # Check the icons or images that might indicate tribe
                race_icon = driver.find_element(By.CSS_SELECTOR, ".playerRace img")
                race_src = race_icon.get_attribute("src")
                
                if "roman" in race_src:
                    tribe = "romans"
                elif "gaul" in race_src:
                    tribe = "gauls"
                elif "teuton" in race_src:
                    tribe = "teutons"
                elif "egyptian" in race_src:
                    tribe = "egyptians"
                elif "hun" in race_src:
                    tribe = "huns"
            except NoSuchElementException:
                logger.warning("Could not determine tribe from profile")
        
        # Extract profile ID
        profile_id = None
        try:
            # Check URL for profile ID
            if "profile" in driver.current_url:
                url_parts = driver.current_url.split('?')
                if len(url_parts) > 1:
                    query_params = url_parts[1].split('&')
                    for param in query_params:
                        if "uid=" in param:
                            profile_id = param.split('=')[1]
                            break
            
            # If not found in URL, try to find it on the page
            if not profile_id:
                # Look for elements that might contain the profile ID
                profile_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'uid=')]")
                if profile_elements:
                    href = profile_elements[0].get_attribute("href")
                    if "uid=" in href:
                        profile_id = href.split("uid=")[1].split("&")[0]
        except Exception as e:
            logger.warning(f"Error extracting profile ID: {e}")
        
        if tribe != "unknown" or profile_id:
            logger.info(f"Profile updated - Tribe: {tribe}, Profile ID: {profile_id}")
            return (tribe, profile_id)
        else:
            logger.warning("Failed to extract profile information")
            return None
            
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return None