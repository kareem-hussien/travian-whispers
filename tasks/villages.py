import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logger
logger = logging.getLogger(__name__)

# Assuming the village list is available on the overview page.
VILLAGE_OVERVIEW_URL = "https://ts1.x1.international.travian.com/dorf1.php"

def run_villages(driver):
    """
    Navigates to the village overview page, extracts the list of villages,
    and returns them as a list of dictionaries.
    
    Args:
        driver (webdriver.Chrome): Chrome WebDriver instance
    
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
        
        # Try to find the village list
        try:
            # First, check if we're on the right page - look for dorf1 elements
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "village_map"))
            )
            logger.info("Village map found - we're on the village page")
            
            # Let's try two different ways to find villages
            # Method 1: Try to find villages in the list selector
            villages = []
            
            # First check if there are multiple villages by looking for the village list
            try:
                village_list = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "sidebarBoxVillagelist"))
                )
                logger.info("Found village list container")
                
                # Now look for the village entries
                village_elements = village_list.find_elements(By.CSS_SELECTOR, ".listEntry")
                
                if village_elements:
                    logger.info(f"Found {len(village_elements)} villages in the sidebar")
                    
                    for idx, elem in enumerate(village_elements):
                        try:
                            # Extract village ID (newdid)
                            newdid = elem.get_attribute("data-did")
                            if not newdid:
                                href = elem.get_attribute("href")
                                if href and "newdid=" in href:
                                    newdid = href.split("newdid=")[1].split("&")[0]
                            
                            # Get village name
                            try:
                                name_elem = elem.find_element(By.CSS_SELECTOR, ".name")
                                village_name = name_elem.text.strip()
                            except NoSuchElementException:
                                # Fallback - if can't find .name class, try getting text directly
                                village_name = elem.text.strip().split('(')[0].strip()
                            
                            # Get coordinates
                            try:
                                coords_elem = elem.find_element(By.CSS_SELECTOR, ".coordinatesGrid")
                                x = coords_elem.get_attribute("data-x")
                                y = coords_elem.get_attribute("data-y")
                            except NoSuchElementException:
                                # Fallback - try to parse coordinates from text content
                                coords_text = elem.text.strip()
                                if '(' in coords_text and ')' in coords_text:
                                    coords = coords_text.split('(')[1].split(')')[0]
                                    coords_parts = coords.split('|')
                                    if len(coords_parts) == 2:
                                        x = coords_parts[0].strip()
                                        y = coords_parts[1].strip()
                                    else:
                                        x, y = "0", "0"
                                else:
                                    x, y = "0", "0"
                            
                            # Get population (we'll need to visit the village to get this)
                            population = 0  # Default
                            
                            # Collect all data even if some parts might be missing
                            if newdid and village_name:
                                villages.append({
                                    "newdid": newdid,
                                    "name": village_name,
                                    "x": int(x) if x and x.isdigit() else 0,
                                    "y": int(y) if y and y.isdigit() else 0,
                                    "population": population,
                                    "status": "active",
                                    "auto_farm_enabled": False,
                                    "training_enabled": False,
                                    "resources": {
                                        "wood": 0,
                                        "clay": 0,
                                        "iron": 0,
                                        "crop": 0
                                    }
                                })
                                logger.info(f"Extracted village: {village_name} (newdid: {newdid}), Coordinates: ({x}, {y})")
                            else:
                                logger.warning(f"Missing required data for village {idx+1}")
                                
                        except Exception as e:
                            logger.exception(f"Error processing village element {idx+1}: {str(e)}")
                else:
                    logger.warning("No village elements found in the sidebar")
            except TimeoutException:
                logger.info("No village list found in sidebar - user might have only one village")
                
                # If we're here, the user might have only one village
                # Try to extract the current village information
                try:
                    # Get village name from the header
                    header_elem = driver.find_element(By.ID, "villageNameField")
                    village_name = header_elem.text.strip()
                    
                    # Try to get coordinates
                    try:
                        coords_elem = driver.find_element(By.CSS_SELECTOR, ".coordinatesGrid")
                        x = coords_elem.get_attribute("data-x")
                        y = coords_elem.get_attribute("data-y")
                    except NoSuchElementException:
                        # Fallback - try to find coordinates in the title
                        title_elem = driver.find_element(By.CSS_SELECTOR, ".villageName")
                        title_text = title_elem.text
                        if '(' in title_text and ')' in title_text:
                            coords = title_text.split('(')[1].split(')')[0]
                            coords_parts = coords.split('|')
                            if len(coords_parts) == 2:
                                x = coords_parts[0].strip()
                                y = coords_parts[1].strip()
                            else:
                                x, y = "0", "0"
                        else:
                            x, y = "0", "0"
                    
                    # Try to extract a village ID from the page
                    newdid = "1"  # Default for the single village
                    try:
                        # Look for links with newdid parameter
                        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='newdid=']")
                        if links:
                            for link in links:
                                href = link.get_attribute("href")
                                if href and "newdid=" in href:
                                    newdid = href.split("newdid=")[1].split("&")[0]
                                    break
                    except:
                        pass
                    
                    # Create village entry for single village
                    villages.append({
                        "newdid": newdid,
                        "name": village_name,
                        "x": int(x) if x and x.isdigit() else 0,
                        "y": int(y) if y and y.isdigit() else 0,
                        "population": 0,  # Default
                        "status": "active",
                        "auto_farm_enabled": False,
                        "training_enabled": False,
                        "resources": {
                            "wood": 0,
                            "clay": 0,
                            "iron": 0,
                            "crop": 0
                        }
                    })
                    logger.info(f"Extracted single village: {village_name} (newdid: {newdid}), Coordinates: ({x}, {y})")
                    
                except Exception as e:
                    logger.exception(f"Error extracting single village: {str(e)}")
            
            # If we still have no villages, try a different approach
            if not villages:
                logger.warning("No villages extracted using primary methods, trying alternative methods...")
                
                # Method 3: Try to find villages in the production overview
                try:
                    # Navigate to production overview 
                    driver.get("https://ts1.x1.international.travian.com/production.php")
                    time.sleep(3)
                    
                    # Look for village data in the production table
                    village_rows = driver.find_elements(By.CSS_SELECTOR, "table.villages tr")
                    
                    for idx, row in enumerate(village_rows[1:], start=1):  # Skip header row
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                # Get village name
                                name_elem = cells[0]
                                village_name = name_elem.text.strip()
                                
                                # Try to extract coordiates from name if they're in parentheses
                                x, y = "0", "0"
                                if '(' in village_name and ')' in village_name:
                                    coords_part = village_name.split('(')[1].split(')')[0]
                                    if '|' in coords_part:
                                        coords = coords_part.split('|')
                                        x = coords[0].strip()
                                        y = coords[1].strip()
                                        # Clean village name
                                        village_name = village_name.split('(')[0].strip()
                                
                                # Try to get newdid from links
                                newdid = f"alt_{idx}"  # Default fallback
                                links = name_elem.find_elements(By.TAG_NAME, "a")
                                for link in links:
                                    href = link.get_attribute("href")
                                    if href and "newdid=" in href:
                                        newdid = href.split("newdid=")[1].split("&")[0]
                                        break
                                
                                villages.append({
                                    "newdid": newdid,
                                    "name": village_name,
                                    "x": int(x) if x and x.isdigit() else 0,
                                    "y": int(y) if y and y.isdigit() else 0,
                                    "population": 0,  # Default
                                    "status": "active",
                                    "auto_farm_enabled": False,
                                    "training_enabled": False,
                                    "resources": {
                                        "wood": 0,
                                        "clay": 0,
                                        "iron": 0,
                                        "crop": 0
                                    }
                                })
                                logger.info(f"Extracted village from production page: {village_name}")
                        except Exception as e:
                            logger.exception(f"Error processing production village row {idx}: {str(e)}")
                except Exception as e:
                    logger.exception(f"Error accessing production page: {str(e)}")
            
            # Attempt to visit each village to get more data if time allows
            if villages and len(villages) < 10:  # Only do this for a reasonable number of villages
                logger.info(f"Attempting to gather additional data for {len(villages)} villages")
                for village in villages:
                    try:
                        # Visit the village to get population and resources
                        driver.get(f"{VILLAGE_OVERVIEW_URL}?newdid={village['newdid']}")
                        time.sleep(2)
                        
                        # Try to get population
                        try:
                            pop_elem = driver.find_element(By.ID, "population")
                            if pop_elem:
                                pop_text = pop_elem.text.strip()
                                if pop_text.isdigit():
                                    village['population'] = int(pop_text)
                        except:
                            pass
                            
                        # Try to get resources
                        try:
                            wood_elem = driver.find_element(By.ID, "l1")
                            clay_elem = driver.find_element(By.ID, "l2")
                            iron_elem = driver.find_element(By.ID, "l3")
                            crop_elem = driver.find_element(By.ID, "l4")
                            
                            if wood_elem and clay_elem and iron_elem and crop_elem:
                                wood = wood_elem.text.strip().replace(',', '')
                                clay = clay_elem.text.strip().replace(',', '')
                                iron = iron_elem.text.strip().replace(',', '')
                                crop = crop_elem.text.strip().replace(',', '')
                                
                                village['resources'] = {
                                    "wood": int(wood) if wood.isdigit() else 0,
                                    "clay": int(clay) if clay.isdigit() else 0,
                                    "iron": int(iron) if iron.isdigit() else 0,
                                    "crop": int(crop) if crop.isdigit() else 0
                                }
                        except:
                            pass
                        
                    except Exception as e:
                        logger.warning(f"Error getting additional data for village {village['name']}: {str(e)}")
            
            # Return the collected villages
            return villages if villages else []
            
        except TimeoutException:
            logger.error("Timeout waiting for village map - we might not be on the village page")
            
            # If not on village page, we might be on the login page or elsewhere
            # Try to check if we need to log in
            try:
                if driver.find_element(By.ID, "loginForm") or driver.find_element(By.CSS_SELECTOR, "form[name='login']"):
                    logger.error("Login form detected - we're not logged in")
                    return []  # Not logged in, can't extract villages
            except:
                pass
                
            return []  # Can't extract villages
            
    except Exception as e:
        logger.exception(f"Error in village extraction: {str(e)}")
        return []
