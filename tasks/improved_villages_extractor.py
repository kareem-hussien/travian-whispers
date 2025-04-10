"""
Improved village extraction module with robust error handling.
"""
import logging
import re
import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Configure logger
logger = logging.getLogger(__name__)

def extract_villages(driver: WebDriver, username: str, password: str, server_url: str) -> List[Dict[str, Any]]:
    """
    Extract villages from Travian using multiple methods for reliability.
    
    Args:
        driver: Selenium WebDriver instance
        username: Travian username
        password: Travian password
        server_url: Travian server URL
        
    Returns:
        list: List of village dictionaries
    """
    villages = []
    
    try:
        # Step 1: Login to Travian
        if not login_to_travian(driver, username, password, server_url):
            logger.error("Failed to log in to Travian")
            return []
            
        # Step 2: Try different methods to extract villages
        
        # Method A: Extract from sidebar village list
        sidebar_villages = extract_from_sidebar(driver)
        if sidebar_villages:
            villages = sidebar_villages
            logger.info(f"Successfully extracted {len(villages)} villages from sidebar")
        
        # Method B: If sidebar didn't work, try current village
        if not villages:
            current_village = extract_current_village(driver)
            if current_village:
                villages = [current_village]
                logger.info("Extracted current village only")
        
        # Method C: Try profile villages page
        if not villages or len(villages) == 1:
            profile_villages = extract_from_profile(driver, server_url)
            if profile_villages:
                # Replace with profile villages if found, as it's usually more complete
                villages = profile_villages
                logger.info(f"Extracted {len(villages)} villages from profile")
                
        # Method D: Try village overview page
        if not villages:
            overview_villages = extract_from_overview(driver, server_url)
            if overview_villages:
                villages = overview_villages
                logger.info(f"Extracted {len(villages)} villages from overview")
        
        # Step 3: Enrich village data if possible
        if villages and len(villages) < 10:  # Only for a reasonable number of villages
            villages = enrich_village_data(driver, villages, server_url)
        
        return villages
        
    except Exception as e:
        logger.error(f"Error in village extraction: {e}")
        return []
        
def login_to_travian(driver: WebDriver, username: str, password: str, server_url: str) -> bool:
    """
    Login to Travian account.
    
    Args:
        driver: Selenium WebDriver instance
        username: Travian username
        password: Travian password
        server_url: Travian server URL
        
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        # Navigate to server URL
        logger.info(f"Navigating to {server_url}")
        driver.get(server_url)
        time.sleep(2)
        
        # Check if already logged in
        if "dorf1.php" in driver.current_url or "village" in driver.current_url:
            logger.info("Already logged in to Travian")
            return True
            
        # Navigate to login page if needed
        if "login" not in driver.current_url.lower():
            try:
                # Try to find login link
                login_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'login.php')]")
                if login_links:
                    login_links[0].click()
                    time.sleep(2)
                else:
                    # Navigate directly to login
                    driver.get(f"{server_url}/login.php")
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Error navigating to login page: {e}")
                driver.get(f"{server_url}/login.php")
                time.sleep(2)
        
        # Find login form elements
        try:
            # Wait for username field
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "name"))
            )
            
            # Find password field
            password_field = driver.find_element(By.NAME, "password")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Find login button
            login_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            if not login_buttons:
                logger.error("Login button not found")
                return False
                
            # Click login button
            login_buttons[0].click()
            
            # Wait for redirect to village page
            WebDriverWait(driver, 15).until(
                lambda d: any(url_part in d.current_url for url_part in ["dorf1.php", "village", "game.php"])
            )
            
            logger.info("Login successful")
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Error during login: {e}")
            
            # Check for error messages
            try:
                error_elements = driver.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    logger.error(f"Login error: {error_elements[0].text}")
            except:
                pass
                
            return False
            
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return False

def extract_from_sidebar(driver: WebDriver) -> List[Dict[str, Any]]:
    """
    Extract villages from the sidebar village list.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        list: List of village dictionaries
    """
    villages = []
    
    try:
        # Wait for village list to load
        wait = WebDriverWait(driver, 5)
        village_list = None
        
        # Try different selectors for village list
        selectors = [
            (By.ID, "sidebarBoxVillagelist"),
            (By.CLASS_NAME, "villageList"),
            (By.CSS_SELECTOR, ".sidebarBoxInnerBox.villageList")
        ]
        
        for by, selector in selectors:
            try:
                village_list = wait.until(EC.presence_of_element_located((by, selector)))
                if village_list:
                    break
            except:
                continue
        
        if not village_list:
            return []
        
        # Find village elements
        # Try different selectors for village entries
        village_elements = []
        entry_selectors = [
            ".listEntry",
            ".listEntry.village",
            "div[data-did]",
            "a[href*='newdid=']"
        ]
        
        for selector in entry_selectors:
            village_elements = village_list.find_elements(By.CSS_SELECTOR, selector)
            if village_elements:
                break
        
        if not village_elements:
            return []
            
        logger.info(f"Found {len(village_elements)} villages in sidebar")
        
        for elem in village_elements:
            try:
                # Get village ID (newdid)
                newdid = elem.get_attribute("data-did")
                
                # Alternative: extract from href
                if not newdid:
                    try:
                        href = elem.get_attribute("href")
                        if href and "newdid=" in href:
                            newdid = href.split("newdid=")[1].split("&")[0]
                    except:
                        links = elem.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and "newdid=" in href:
                                newdid = href.split("newdid=")[1].split("&")[0]
                                break
                
                if not newdid:
                    # Skip if no ID found
                    continue
                
                # Get village name
                village_name = None
                
                try:
                    # Try class selectors first
                    name_selectors = [".name", ".villageName", ".villageNameField"]
                    for selector in name_selectors:
                        try:
                            name_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            village_name = name_elem.text.strip()
                            if village_name:
                                break
                        except:
                            continue
                    
                    # If no name found, try to extract from the element text
                    if not village_name:
                        text = elem.text.strip()
                        # Extract name part (before coordinates)
                        if '(' in text:
                            village_name = text.split('(')[0].strip()
                        else:
                            village_name = text
                except:
                    # Fallback: use placeholder name
                    village_name = f"Village {len(villages) + 1}"
                
                # Get coordinates
                x, y = 0, 0
                
                try:
                    # Try to find coordinates element
                    coords_selectors = [".coordinatesGrid", ".coordinates"]
                    for selector in coords_selectors:
                        try:
                            coords_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            x = coords_elem.get_attribute("data-x")
                            y = coords_elem.get_attribute("data-y")
                            if x and y:
                                break
                        except:
                            continue
                    
                    # Try to extract from element text
                    if not (x and y):
                        text = elem.text.strip()
                        coords_match = re.search(r'\((-?\d+)\|(-?\d+)\)', text)
                        if coords_match:
                            x, y = coords_match.groups()
                except:
                    pass
                
                # Create village dictionary
                village = {
                    "name": village_name,
                    "newdid": newdid,
                    "x": int(x) if x and str(x).isdigit() else 0,
                    "y": int(y) if y and str(y).isdigit() else 0,
                    "population": 0,
                    "status": "active",
                    "auto_farm_enabled": True,
                    "training_enabled": True,
                    "resources": {
                        "wood": 0,
                        "clay": 0,
                        "iron": 0,
                        "crop": 0
                    }
                }
                
                villages.append(village)
                logger.info(f"Extracted village: {village_name} ({x}|{y})")
                
            except Exception as e:
                logger.warning(f"Error extracting village from sidebar: {e}")
        
        return villages
        
    except Exception as e:
        logger.error(f"Error extracting villages from sidebar: {e}")
        return []

def extract_current_village(driver: WebDriver) -> Optional[Dict[str, Any]]:
    """
    Extract information about the current village from the page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        dict: Village dictionary or None if extraction failed
    """
    try:
        # Get village name
        village_name = None
        
        # Try different selectors for village name
        name_selectors = [
            (By.ID, "villageNameField"),
            (By.CLASS_NAME, "villageName"),
            (By.CSS_SELECTOR, ".villageName")
        ]
        
        for by, selector in name_selectors:
            try:
                element = driver.find_element(by, selector)
                village_name = element.text.strip()
                if village_name:
                    break
            except:
                continue
        
        if not village_name:
            # Try to get from page title
            title = driver.title
            if " - " in title:
                village_name = title.split(" - ")[0].strip()
        
        if not village_name:
            village_name = "Current Village"
        
        # Get coordinates
        x, y = 0, 0
        
        # Try different methods to get coordinates
        try:
            # Method 1: From coordinate elements
            coords_selectors = [
                (By.CSS_SELECTOR, ".coordinatesGrid"),
                (By.CSS_SELECTOR, ".coordinates"),
                (By.CSS_SELECTOR, "[data-x][data-y]")
            ]
            
            for by, selector in coords_selectors:
                try:
                    element = driver.find_element(by, selector)
                    x = element.get_attribute("data-x")
                    y = element.get_attribute("data-y")
                    if x and y:
                        break
                except:
                    continue
            
            # Method 2: From title or text content
            if not (x and y):
                # Try title or any visible text containing coordinates
                text_elements = [
                    driver.title,
                    driver.find_element(By.TAG_NAME, "body").text
                ]
                
                for text in text_elements:
                    coords_match = re.search(r'\((-?\d+)\|(-?\d+)\)', text)
                    if coords_match:
                        x, y = coords_match.groups()
                        break
        except:
            pass
        
        # Get village ID (newdid)
        newdid = None
        
        # Method 1: From URL
        try:
            current_url = driver.current_url
            newdid_match = re.search(r'newdid=(\d+)', current_url)
            if newdid_match:
                newdid = newdid_match.group(1)
        except:
            pass
        
        # Method 2: From links
        if not newdid:
            try:
                links = driver.find_elements(By.CSS_SELECTOR, "a[href*='newdid=']")
                for link in links:
                    href = link.get_attribute("href")
                    newdid_match = re.search(r'newdid=(\d+)', href)
                    if newdid_match:
                        newdid = newdid_match.group(1)
                        break
            except:
                pass
        
        # Default ID if nothing found
        if not newdid:
            newdid = "1"  # Default ID for single village
        
        # Create village dictionary
        village = {
            "name": village_name,
            "newdid": newdid,
            "x": int(x) if x and str(x).isdigit() else 0,
            "y": int(y) if y and str(y).isdigit() else 0,
            "population": 0,
            "status": "active",
            "auto_farm_enabled": True,
            "training_enabled": True,
            "resources": {
                "wood": 0,
                "clay": 0,
                "iron": 0,
                "crop": 0
            }
        }
        
        logger.info(f"Extracted current village: {village_name} ({x}|{y})")
        return village
        
    except Exception as e:
        logger.error(f"Error extracting current village: {e}")
        return None

def extract_from_profile(driver: WebDriver, server_url: str) -> List[Dict[str, Any]]:
    """
    Extract villages from the profile page.
    
    Args:
        driver: Selenium WebDriver instance
        server_url: Travian server URL
        
    Returns:
        list: List of village dictionaries
    """
    villages = []
    
    try:
        # Navigate to profile page
        profile_url = None
        
        # Try different profile URLs
        profile_urls = [
            f"{server_url}/profile",
            f"{server_url}/profile/villages",
            f"{server_url}/spieler.php",
            f"{server_url}/spieler.php?s=1"  # Village tab
        ]
        
        for url in profile_urls:
            driver.get(url)
            time.sleep(2)
            
            # Check if profile page loaded
            if "profile" in driver.current_url or "spieler.php" in driver.current_url:
                profile_url = url
                break
        
        if not profile_url:
            logger.warning("Could not navigate to profile page")
            return []
        
        # Try to find the villages tab if not already there
        if "s=1" not in driver.current_url and "villages" not in driver.current_url:
            try:
                # Look for village tab link
                tab_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='s=1'], a[href*='villages']")
                for link in tab_links:
                    if "villages" in link.text.lower() or "dörfer" in link.text.lower():
                        link.click()
                        time.sleep(2)
                        break
            except:
                # Try direct navigation
                driver.get(f"{server_url}/spieler.php?s=1")
                time.sleep(2)
        
        # Find village table
        village_table = None
        table_selectors = [
            (By.CSS_SELECTOR, "table.villages"),
            (By.CSS_SELECTOR, "table.row_table_data"),
            (By.XPATH, "//table[contains(@class, 'table') and .//th]")
        ]
        
        for by, selector in table_selectors:
            try:
                tables = driver.find_elements(by, selector)
                for table in tables:
                    # Check if this looks like a villages table
                    headers = table.find_elements(By.TAG_NAME, "th")
                    if headers and any("village" in h.text.lower() for h in headers):
                        village_table = table
                        break
                if village_table:
                    break
            except:
                continue
        
        if not village_table:
            logger.warning("Could not find villages table in profile")
            return []
        
        # Get table rows (skip header)
        rows = village_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
        
        if not rows:
            logger.warning("No village rows found in profile table")
            return []
            
        logger.info(f"Found {len(rows)} village rows in profile")
        
        for row in rows:
            try:
                # Get cells
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) < 2:
                    continue
                
                # Extract village name and link
                village_name = None
                newdid = None
                
                # First cell usually contains village name and link
                try:
                    name_cell = cells[0]
                    links = name_cell.find_elements(By.TAG_NAME, "a")
                    
                    if links:
                        link = links[0]
                        village_name = link.text.strip()
                        href = link.get_attribute("href")
                        
                        # Extract newdid from link
                        newdid_match = re.search(r'newdid=(\d+)', href)
                        if newdid_match:
                            newdid = newdid_match.group(1)
                    
                    # If no name from link, try cell text
                    if not village_name:
                        village_name = name_cell.text.strip()
                except:
                    pass
                
                if not village_name or not newdid:
                    continue
                
                # Extract coordinates
                x, y = 0, 0
                
                # Look for coordinates in all cells
                for cell in cells:
                    cell_text = cell.text.strip()
                    coords_match = re.search(r'\((-?\d+)\|(-?\d+)\)', cell_text)
                    if coords_match:
                        x, y = coords_match.groups()
                        break
                
                # Create village dictionary
                village = {
                    "name": village_name,
                    "newdid": newdid,
                    "x": int(x) if x and str(x).isdigit() else 0,
                    "y": int(y) if y and str(y).isdigit() else 0,
                    "population": 0,
                    "status": "active",
                    "auto_farm_enabled": True,
                    "training_enabled": True,
                    "resources": {
                        "wood": 0,
                        "clay": 0,
                        "iron": 0,
                        "crop": 0
                    }
                }
                
                villages.append(village)
                logger.info(f"Extracted village from profile: {village_name} ({x}|{y})")
                
            except Exception as e:
                logger.warning(f"Error extracting village from profile row: {e}")
        
        return villages
        
    except Exception as e:
        logger.error(f"Error extracting villages from profile: {e}")
        return []

def extract_from_overview(driver: WebDriver, server_url: str) -> List[Dict[str, Any]]:
    """
    Extract villages from the production overview page.
    
    Args:
        driver: Selenium WebDriver instance
        server_url: Travian server URL
        
    Returns:
        list: List of village dictionaries
    """
    villages = []
    
    try:
        # Navigate to production overview
        overview_urls = [
            f"{server_url}/production.php",
            f"{server_url}/dorf3.php"
        ]
        
        for url in overview_urls:
            driver.get(url)
            time.sleep(2)
            
            # Check if we're on the overview page
            if "production.php" in driver.current_url or "dorf3.php" in driver.current_url:
                break
        
        # Find village table
        village_table = None
        table_selectors = [
            (By.CSS_SELECTOR, "table.villages"),
            (By.CSS_SELECTOR, "table.row_table_data"),
            (By.XPATH, "//table[contains(@class, 'table') and .//th]")
        ]
        
        for by, selector in table_selectors:
            try:
                tables = driver.find_elements(by, selector)
                for table in tables:
                    # Check if this looks like a villages table
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) > 1:  # Has at least a header and one data row
                        village_table = table
                        break
                if village_table:
                    break
            except:
                continue
        
        if not village_table:
            logger.warning("Could not find villages table in overview")
            return []
        
        # Get table rows (skip header)
        rows = village_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
        
        if not rows:
            logger.warning("No village rows found in overview table")
            return []
            
        logger.info(f"Found {len(rows)} village rows in overview")
        
        for idx, row in enumerate(rows, start=1):
            try:
                # Get cells
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) < 1:
                    continue
                
                # Extract village name and link
                village_name = None
                newdid = None
                
                # First cell usually contains village name and link
                try:
                    name_cell = cells[0]
                    links = name_cell.find_elements(By.TAG_NAME, "a")
                    
                    if links:
                        link = links[0]
                        village_name = link.text.strip()
                        href = link.get_attribute("href")
                        
                        # Extract newdid from link
                        newdid_match = re.search(r'newdid=(\d+)', href)
                        if newdid_match:
                            newdid = newdid_match.group(1)
                    
                    # If no name from link, try cell text
                    if not village_name:
                        village_name = name_cell.text.strip()
                except:
                    pass
                
                # If still no name, use default
                if not village_name:
                    village_name = f"Village {idx}"
                    
                # If no newdid, use placeholder
                if not newdid:
                    newdid = f"unknown_{idx}"
                
                # Extract coordinates
                x, y = 0, 0
                
                # Extract from village name if it contains coordinates
                if village_name:
                    coords_match = re.search(r'\((-?\d+)\|(-?\d+)\)', village_name)
                    if coords_match:
                        x, y = coords_match.groups()
                        # Clean village name
                        village_name = village_name.split('(')[0].strip()
                
                # Create village dictionary
                village = {
                    "name": village_name,
                    "newdid": newdid,
                    "x": int(x) if x and str(x).isdigit() else 0,
                    "y": int(y) if y and str(y).isdigit() else 0,
                    "population": 0,
                    "status": "active",
                    "auto_farm_enabled": True,
                    "training_enabled": True,
                    "resources": {
                        "wood": 0,
                        "clay": 0,
                        "iron": 0,
                        "crop": 0
                    }
                }
                
                villages.append(village)
                logger.info(f"Extracted village from overview: {village_name} ({x}|{y})")
                
            except Exception as e:
                logger.warning(f"Error extracting village from overview row: {e}")
        
        return villages
        
    except Exception as e:
        logger.error(f"Error extracting villages from overview: {e}")
        return []

def enrich_village_data(driver: WebDriver, villages: List[Dict[str, Any]], server_url: str) -> List[Dict[str, Any]]:
    """
    Visit each village to enrich with additional data.
    
    Args:
        driver: Selenium WebDriver instance
        villages: List of village dictionaries
        server_url: Travian server URL
        
    Returns:
        list: Updated list of village dictionaries
    """
    if not villages:
        return []
        
    logger.info(f"Enriching data for {len(villages)} villages")
    
    # Create a map of villages by newdid for easy updating
    villages_map = {v["newdid"]: v for v in villages}
    
    for newdid, village in villages_map.items():
        try:
            # Skip placeholder IDs
            if "unknown" in newdid:
                continue
                
            # Visit the village
            village_url = f"{server_url}/dorf1.php?newdid={newdid}"
            logger.info(f"Visiting {village_url}")
            driver.get(village_url)
            time.sleep(2)
            
            # Get population
            try:
                pop_elem = None
                pop_selectors = [
                    (By.ID, "population"),
                    (By.CLASS_NAME, "inhabitants")
                ]
                
                for by, selector in pop_selectors:
                    try:
                        pop_elem = driver.find_element(by, selector)
                        if pop_elem:
                            break
                    except:
                        continue
                
                if pop_elem:
                    pop_text = pop_elem.text.strip().replace(',', '')
                    if pop_text.isdigit():
                        village['population'] = int(pop_text)
                        logger.info(f"Updated population for {village['name']}: {pop_text}")
            except Exception as e:
                logger.warning(f"Error getting population: {e}")
            
            # Get resources
            try:
                resource_fields = {
                    "wood": (By.ID, "l1"),
                    "clay": (By.ID, "l2"),
                    "iron": (By.ID, "l3"),
                    "crop": (By.ID, "l4")
                }
                
                for resource, locator in resource_fields.items():
                    try:
                        element = driver.find_element(*locator)
                        value_text = element.text.strip().replace(',', '')
                        if value_text.isdigit():
                            village['resources'][resource] = int(value_text)
                            logger.info(f"Updated {resource} for {village['name']}: {value_text}")
                    except Exception as e:
                        logger.warning(f"Error getting {resource}: {e}")
            except Exception as e:
                logger.warning(f"Error getting resources: {e}")
                
        except Exception as e:
            logger.warning(f"Error enriching data for village {village['name']}: {e}")
    
    # Convert villages map back to list
    return list(villages_map.values())