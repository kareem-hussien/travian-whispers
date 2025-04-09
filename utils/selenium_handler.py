# File: utils/selenium_handler.py

import os
import logging
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configure logger
logger = logging.getLogger(__name__)

class SeleniumHandler:
    """
    Utility class to handle Selenium WebDriver creation and management.
    Provides a consistent interface for both local and remote (Grid) WebDrivers.
    """
    
    def __init__(self):
        """Initialize the handler"""
        self.remote_url = os.environ.get('SELENIUM_REMOTE_URL')
        
    def create_driver(self, user_id=None, headless=True, timeout=60):
        """
        Create and configure a WebDriver instance.
        
        Args:
            user_id (str, optional): User ID for session management
            headless (bool): Whether to run browser in headless mode
            timeout (int): Page load timeout in seconds
            
        Returns:
            webdriver.WebDriver: Configured WebDriver instance
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
        
        # Initialize the WebDriver
        if self.remote_url:
            logger.info(f"Using Selenium Grid at {self.remote_url}")
            
            # Wait for Selenium Grid to be ready
            if not self._wait_for_grid():
                logger.warning("Selenium Grid not ready, but attempting to connect anyway")
            
            # Create remote WebDriver
            try:
                # Add retries for more resilience
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        driver = webdriver.Remote(
                            command_executor=self.remote_url,
                            options=chrome_options
                        )
                        logger.info("Successfully connected to Selenium Grid")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise
                        logger.warning(f"Retry {retry_count}/{max_retries} connecting to Selenium Grid: {e}")
                        time.sleep(5)
                        
            except Exception as e:
                logger.error(f"Error connecting to Selenium Grid: {e}")
                raise
        else:
            logger.warning("SELENIUM_REMOTE_URL not set. Using local Chrome WebDriver which may cause compatibility issues.")
            
            # Fallback to local WebDriver
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                logger.error(f"Failed to create local WebDriver: {e}")
                raise
        
        # Configure browser
        driver.set_page_load_timeout(timeout)
        driver.implicitly_wait(10)
        
        return driver
    
    def _wait_for_grid(self, timeout=60, interval=5):
        """
        Wait for Selenium Grid to be ready.
        
        Args:
            timeout (int): Maximum wait time in seconds
            interval (int): Check interval in seconds
            
        Returns:
            bool: True if grid is ready, False otherwise
        """
        if not self.remote_url:
            return False
            
        status_url = f"{self.remote_url}/status"
        end_time = time.time() + timeout
        
        logger.info(f"Waiting for Selenium Grid at {status_url}")
        
        while time.time() < end_time:
            try:
                response = requests.get(status_url, timeout=5)
                if response.status_code == 200:
                    logger.info("Selenium Grid is ready")
                    return True
            except Exception as e:
                logger.warning(f"Selenium Grid status check error: {e}")
            
            logger.info(f"Waiting for Selenium Grid to be ready... (timeout in {int(end_time - time.time())} seconds)")
            time.sleep(interval)
        
        logger.warning(f"Selenium Grid not ready after {timeout} seconds")
        return False
    
    def is_grid_available(self):
        """
        Check if Selenium Grid is available.
        
        Returns:
            bool: True if Selenium Grid is available, False otherwise
        """
        if not self.remote_url:
            return False
            
        try:
            response = requests.get(f"{self.remote_url}/status", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Selenium Grid status check failed: {e}")
            return False
    
    def close_driver(self, driver):
        """
        Safely close the WebDriver.
        
        Args:
            driver: WebDriver instance to close
        """
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")