"""
Travian API connection module for Travian Whispers.
This module provides functionality to connect and verify Travian accounts.
"""
import logging
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Initialize logger
logger = logging.getLogger(__name__)

def test_connection(username, password, server_url, timeout=30):
    """
    Test connection to Travian server with the provided credentials.
    
    Args:
        username (str): Travian username
        password (str): Travian password
        server_url (str): Travian server URL
        timeout (int, optional): Connection timeout in seconds
        
    Returns:
        dict: Connection result with keys 'success' and 'message'
    """
    if not server_url:
        server_url = "https://ts1.x1.international.travian.com"
    
    # Ensure server URL has protocol
    if not server_url.startswith(('http://', 'https://')):
        server_url = f"https://{server_url}"
    
    try:
        # First try a simple request to check if the server is reachable
        response = requests.head(server_url, timeout=5)
        if response.status_code >= 400:
            return {
                'success': False,
                'message': f"Travian server returned error status: {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f"Could not reach Travian server: {str(e)}"
        }
    
    # If basic connection works, try logging in with Selenium
    try:
        return _selenium_login_test(username, password, server_url, timeout)
    except Exception as e:
        logger.error(f"Error during Selenium login test: {str(e)}")
        # Fall back to simpler login check if Selenium fails
        return _simple_login_test(username, password, server_url)

def _selenium_login_test(username, password, server_url, timeout=30):
    """
    Test login using Selenium WebDriver.
    
    Args:
        username (str): Travian username
        password (str): Travian password
        server_url (str): Travian server URL
        timeout (int): Connection timeout in seconds
        
    Returns:
        dict: Connection result with keys 'success' and 'message'
    """
    driver = None
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize Chrome WebDriver
        from selenium.webdriver.chrome.service import Service
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set page load timeout
        driver.set_page_load_timeout(timeout)
        
        # Navigate to login page
        driver.get(server_url)
        time.sleep(2)  # Allow page to load
        
        # Check if we're redirected to a login page
        if "login" not in driver.current_url.lower() and "dorf1.php" not in driver.current_url.lower():
            # Navigate to the login page
            try:
                login_link = driver.find_element(By.XPATH, "//a[contains(@href, 'login.php')]")
                login_link.click()
                time.sleep(2)
            except NoSuchElementException:
                # If we can't find a login link, try direct login URL
                driver.get(f"{server_url}/login.php")
                time.sleep(2)
        
        # Locate username and password fields
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "name"))
            )
            password_field = driver.find_element(By.NAME, "password")
            
            # Enter credentials
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Find and click the login button
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(driver, 10).until(
                lambda d: "dorf1.php" in d.current_url or "village" in d.current_url or "game.php" in d.current_url
            )
            
            # Check if login was successful
            if "dorf1.php" in driver.current_url or "village" in driver.current_url or "game.php" in driver.current_url:
                # Successfully logged in
                logger.info(f"Successfully connected to Travian account for {username}")
                return {
                    'success': True,
                    'message': "Successfully connected to Travian account",
                    'villages_count': _count_villages(driver)
                }
            else:
                # Check for error messages
                error_elements = driver.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_message = error_elements[0].text
                    logger.warning(f"Travian login failed with error: {error_message}")
                    return {
                        'success': False,
                        'message': f"Login failed: {error_message}"
                    }
                else:
                    logger.warning("Travian login failed without specific error")
                    return {
                        'success': False,
                        'message': "Login failed for unknown reason"
                    }
        except TimeoutException:
            logger.warning("Timeout waiting for login form or redirect")
            return {
                'success': False,
                'message': "Timeout during login process"
            }
        except NoSuchElementException as e:
            logger.warning(f"Element not found during login: {e}")
            return {
                'success': False,
                'message': f"Login form not found: {str(e)}"
            }
    finally:
        # Clean up: close the browser
        if driver:
            driver.quit()

def _simple_login_test(username, password, server_url):
    """
    Simple login test using direct requests (fallback method).
    
    Args:
        username (str): Travian username
        password (str): Travian password
        server_url (str): Travian server URL
        
    Returns:
        dict: Connection result with keys 'success' and 'message'
    """
    try:
        # Create a session to handle cookies
        session = requests.Session()
        
        # Get the login page to obtain any CSRF tokens
        login_page = session.get(f"{server_url}/login.php")
        
        # Simple check if the login page loaded
        if login_page.status_code != 200:
            return {
                'success': False,
                'message': f"Failed to load login page, status code: {login_page.status_code}"
            }
        
        # Prepare login data
        login_data = {
            'name': username,
            'password': password,
            's1': 'Login',
            'w': '1920:1080'
        }
        
        # Submit login form
        login_response = session.post(f"{server_url}/dorf1.php", data=login_data, allow_redirects=True)
        
        # Check if login was successful
        if "dorf1.php" in login_response.url or "village" in login_response.url:
            return {
                'success': True,
                'message': "Successfully connected to Travian account"
            }
        else:
            return {
                'success': False,
                'message': "Login failed, please check your credentials"
            }
    except Exception as e:
        logger.error(f"Error in simple login test: {str(e)}")
        return {
            'success': False,
            'message': f"Connection error: {str(e)}"
        }

def _count_villages(driver):
    """
    Count the number of villages the account has.
    
    Args:
        driver: Selenium WebDriver instance with active Travian session
        
    Returns:
        int: Number of villages found
    """
    try:
        # Try to find the village list
        village_list = driver.find_elements(By.CSS_SELECTOR, "#sidebarBoxVillagelist .listEntry")
        if village_list:
            return len(village_list)
        
        # If no village list found, check if we have village navigation elements
        village_nav = driver.find_elements(By.CSS_SELECTOR, ".villageList")
        if village_nav:
            villages = village_nav[0].find_elements(By.TAG_NAME, "a")
            return len(villages)
        
        # If no village elements found, assume there's just one village
        return 1
    except Exception as e:
        logger.warning(f"Error counting villages: {e}")
        return 0
