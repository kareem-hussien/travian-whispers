"""
Villages extraction module with MongoDB integration.
Specific implementation for Travian Whispers application.
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logger
logger = logging.getLogger(__name__)

# Village overview URL (can be customized per user's server)
VILLAGE_OVERVIEW_URL = "https://ts1.x1.international.travian.com/dorf1.php"

def run_villages(driver, return_villages=False):
    """
    Navigates to the village overview page, extracts the list of villages,
    and returns them.
    
    Args:
        driver: Selenium WebDriver instance
        return_villages: Whether to return the extracted villages
        
    Returns:
        list: List of extracted villages or empty list if failed
    """
    logger.info("Starting village extraction process")
    
    try:
        # Navigate to the village overview page
        logger.info("Navigating to the village overview page")
        driver.get(VILLAGE_OVERVIEW_URL)
        
        # Wait for the page to load completely
        time.sleep(5)  # Give additional time for all elements to load
        
        # Try to find the village list using the exact structure from the HTML
        try:
            logger.info("Looking for the village list with class 'villageList'")
            
            # First check if the villageList div exists
            village_list = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "villageList"))
            )
            logger.info("Found villageList container")
            
            # Get all village entries
            village_elements = village_list.find_elements(By.CSS_SELECTOR, ".listEntry.village")
            
            if not village_elements:
                logger.warning("No elements found with .listEntry.village selector")
                # Try alternative selector
                village_elements = village_list.find_elements(By.CSS_SELECTOR, "div.listEntry")
                if not village_elements:
                    logger.warning("No elements found with alternative div.listEntry selector")
            
            logger.info(f"Found {len(village_elements)} village elements")
            
            villages = []
            for idx, elem in enumerate(village_elements):
                try:
                    # Extract newdid from the element
                    newdid = elem.get_attribute("data-did")
                    logger.info(f"Found village with data-did: {newdid}")
                    
                    # If data-did attribute is not present, try to extract from the link
                    if not newdid:
                        link = elem.find_element(By.TAG_NAME, "a")
                        href = link.get_attribute("href")
                        if "newdid=" in href:
                            newdid = href.split("newdid=")[1].split("&")[0]
                            logger.info(f"Extracted newdid from link: {newdid}")
                    
                    # Extract village name
                    try:
                        name_elem = elem.find_element(By.CSS_SELECTOR, ".name")
                        village_name = name_elem.text.strip()
                        logger.info(f"Found village name: {village_name}")
                    except NoSuchElementException:
                        # If .name element doesn't exist, try other methods
                        village_name = f"Village {idx+1}"
                        link_text = elem.text.strip()
                        if link_text:
                            # Try to extract name from text
                            if "(" in link_text:
                                village_name = link_text.split("(")[0].strip()
                            else:
                                village_name = link_text
                        logger.warning(f"Used fallback for village name: {village_name}")
                    
                    # Extract coordinates
                    try:
                        coords_elem = elem.find_element(By.CSS_SELECTOR, ".coordinatesGrid")
                        x = coords_elem.get_attribute("data-x")
                        y = coords_elem.get_attribute("data-y")
                        logger.info(f"Found coordinates: ({x}, {y})")
                    except NoSuchElementException:
                        # Try to find coordinates in the text
                        coord_text = elem.text
                        if "(" in coord_text and ")" in coord_text:
                            coords = coord_text.split("(")[1].split(")")[0]
                            if "|" in coords:
                                parts = coords.split("|")
                                x = parts[0].strip().replace("−", "-")  # Handle special minus sign
                                y = parts[1].strip().replace("−", "-")  # Handle special minus sign
                                logger.info(f"Extracted coordinates from text: ({x}, {y})")
                            else:
                                x, y = "0", "0"
                        else:
                            x, y = "0", "0"
                            logger.warning("Could not extract coordinates, using defaults")
                    
                    # Create village object
                    village = {
                        "name": village_name,
                        "newdid": newdid,
                        "x": int(x) if x and x.replace("-", "").isdigit() else 0,
                        "y": int(y) if y and y.replace("-", "").isdigit() else 0,
                        "population": 0,  # Default
                        "status": "active",
                        "auto_farm_enabled": True,  # Enable by default
                        "training_enabled": False,
                        "resources": {
                            "wood": 0,
                            "clay": 0,
                            "iron": 0,
                            "crop": 0
                        }
                    }
                    villages.append(village)
                    logger.info(f"Added village: {village_name} (newdid: {newdid}), Coordinates: ({x}, {y})")
                    
                except Exception as e:
                    logger.warning(f"Error processing village element {idx+1}: {str(e)}")
            
            if villages:
                logger.info(f"Successfully extracted {len(villages)} villages")
                return villages
            else:
                logger.warning("No villages extracted from found elements")
                
        except TimeoutException:
            logger.warning("Timeout while waiting for villageList element")
        except Exception as e:
            logger.warning(f"Error finding village list: {str(e)}")
        
        # Fallback strategy - look for village name in the UI
        try:
            logger.info("Trying fallback strategy - look for village name")
            
            # Try to find the village name field
            village_name_elem = driver.find_element(By.ID, "villageNameField")
            if village_name_elem:
                village_name = village_name_elem.text.strip()
                logger.info(f"Found current village name: {village_name}")
                
                # Look for coordinates
                x, y = "0", "0"
                try:
                    # Try to find coordinates in the header or title
                    header_elem = driver.find_element(By.CLASS_NAME, "villageName")
                    header_text = header_elem.text.strip()
                    
                    if "(" in header_text and ")" in header_text:
                        coords = header_text.split("(")[1].split(")")[0]
                        if "|" in coords:
                            parts = coords.split("|")
                            x = parts[0].strip().replace("−", "-")  # Handle special minus sign
                            y = parts[1].strip().replace("−", "-")  # Handle special minus sign
                            logger.info(f"Extracted coordinates from header: ({x}, {y})")
                except:
                    logger.warning("Could not extract coordinates from header")
                
                # Try to find village ID from URL or links
                newdid = "1"  # Default
                try:
                    current_url = driver.current_url
                    if "newdid=" in current_url:
                        newdid = current_url.split("newdid=")[1].split("&")[0]
                        logger.info(f"Extracted newdid from URL: {newdid}")
                    else:
                        # Look for links with newdid
                        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='newdid=']")
                        if links:
                            href = links[0].get_attribute("href")
                            newdid = href.split("newdid=")[1].split("&")[0]
                            logger.info(f"Extracted newdid from link: {newdid}")
                except:
                    logger.warning("Could not extract newdid, using default")
                
                # Create village object for single village
                village = {
                    "name": village_name,
                    "newdid": newdid,
                    "x": int(x) if x and x.replace("-", "").isdigit() else 0,
                    "y": int(y) if y and y.replace("-", "").isdigit() else 0,
                    "population": 0,  # Default
                    "status": "active",
                    "auto_farm_enabled": True,  # Enable by default
                    "training_enabled": False,
                    "resources": {
                        "wood": 0,
                        "clay": 0,
                        "iron": 0,
                        "crop": 0
                    }
                }
                
                logger.info(f"Created single village object: {village_name} (newdid: {newdid}), Coordinates: ({x}, {y})")
                return [village]
            
        except NoSuchElementException:
            logger.warning("Could not find village name element")
        except Exception as e:
            logger.warning(f"Error in fallback strategy: {str(e)}")
        
        # If all strategies failed, try one more thing - look for resources to confirm we're logged in
        try:
            resources = driver.find_element(By.ID, "resources")
            if resources:
                logger.warning("Resources found but no villages could be extracted - strange state")
                
                # Create a default village as last resort
                village = {
                    "name": "Unknown Village",
                    "newdid": "1",
                    "x": 0,
                    "y": 0,
                    "population": 0,
                    "status": "active",
                    "auto_farm_enabled": True,
                    "training_enabled": False,
                    "resources": {
                        "wood": 0,
                        "clay": 0,
                        "iron": 0,
                        "crop": 0
                    }
                }
                
                logger.info("Created default village as last resort")
                return [village]
        except:
            pass
        
        # Check if we're on the login page
        try:
            if (driver.find_element(By.ID, "loginForm") or 
                driver.find_element(By.CSS_SELECTOR, "form[name='login']")):
                logger.error("Login form detected - user is not logged in")
                return []
        except:
            pass
        
        logger.error("All extraction strategies failed. No villages found.")
        return []
            
    except Exception as e:
        logger.error(f"Error in village extraction: {str(e)}")
        return []
