# File: utils/grid_health.py

import logging
import requests
import time
import os
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class GridHealthCheck:
    """
    Utility to check Selenium Grid health and status.
    """
    
    def __init__(self):
        """Initialize the health check utility."""
        self.grid_url = os.environ.get('SELENIUM_REMOTE_URL', 'http://selenium:4444/wd/hub')
        self.status_endpoint = self.grid_url.rstrip('/') + '/status'
        self.last_check = None
        self.status = None
    
    def check_status(self):
        """
        Check Selenium Grid status.
        
        Returns:
            dict: Grid status information
        """
        try:
            response = requests.get(self.status_endpoint, timeout=5)
            self.last_check = datetime.now()
            
            if response.status_code == 200:
                status_data = response.json()
                self.status = 'up'
                logger.info("Selenium Grid is up and running")
                return status_data
            else:
                self.status = 'error'
                logger.warning(f"Selenium Grid returned status code {response.status_code}")
                return {'value': {'ready': False, 'message': f"Status code: {response.status_code}"}}
                
        except requests.exceptions.RequestException as e:
            self.last_check = datetime.now()
            self.status = 'down'
            logger.error(f"Error connecting to Selenium Grid: {e}")
            return {'value': {'ready': False, 'message': str(e)}}
    
    def wait_for_grid(self, timeout=60, check_interval=5):
        """
        Wait for Selenium Grid to be ready.
        
        Args:
            timeout (int): Maximum time to wait in seconds
            check_interval (int): Interval between checks in seconds
            
        Returns:
            bool: True if grid is ready, False otherwise
        """
        start_time = time.time()
        end_time = start_time + timeout
        
        logger.info(f"Waiting for Selenium Grid to be ready (timeout: {timeout}s)")
        
        while time.time() < end_time:
            status = self.check_status()
            
            try:
                if status['value']['ready']:
                    logger.info("Selenium Grid is ready")
                    return True
                else:
                    logger.info(f"Selenium Grid not ready: {status['value'].get('message', 'Unknown reason')}")
            except (KeyError, TypeError):
                logger.warning("Unable to parse Selenium Grid status response")
            
            time.sleep(check_interval)
        
        logger.error(f"Selenium Grid not ready after {timeout} seconds")
        return False
    
    def get_active_sessions(self):
        """
        Get information about active sessions.
        
        Returns:
            list: List of active sessions
        """
        try:
            response = requests.get(self.grid_url.rstrip('/') + '/sessions', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('value', [])
            else:
                logger.warning(f"Error getting sessions: Status code {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting sessions: {e}")
            return []
    
    def get_node_info(self):
        """
        Get information about Grid nodes.
        
        Returns:
            list: List of nodes
        """
        try:
            # This might need adjustment based on the actual Grid API
            response = requests.get(self.grid_url.replace('/wd/hub', '/grid/console'), timeout=5)
            
            if response.status_code == 200:
                # This is typically HTML, but you could parse it if needed
                return {'html': response.text}
            else:
                logger.warning(f"Error getting node info: Status code {response.status_code}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting node info: {e}")
            return {}