"""
Villages extraction module with MongoDB integration.
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('startup.villages')

VILLAGE_OVERVIEW_URL = "https://ts1.x1.international.travian.com/dorf1.php"

def run_villages(driver, return_villages=False):
    """
    Navigates to the village overview page, extracts the list of villages,
    prints them for confirmation, and returns them if requested.
    
    Args:
        driver: Selenium WebDriver instance
        return_villages: Whether to return the extracted villages
        
    Returns:
        list: List of villages if return_villages is True, None otherwise
    """
    logger.info("Navigating to the village overview page...")
    driver.get(VILLAGE_OVERVIEW_URL)
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "villageList"))
        )
    except Exception as e:
        logger.error(f"Village list not found: {e}")
        return None
    
    time.sleep(3)

    villages = []
    village_elements = driver.find_elements(By.CSS_SELECTOR, "div.villageList div.listEntry.village")
    if not village_elements:
        logger.error("No village entries found.")
        return None

    for elem in village_elements:
        try:
            newdid = elem.get_attribute("data-did")
            name_elem = elem.find_element(By.CSS_SELECTOR, "span.name")
            village_name = name_elem.text.strip()
            coord_elem = elem.find_element(By.CSS_SELECTOR, "span.coordinatesGrid")
            x = coord_elem.get_attribute("data-x")
            y = coord_elem.get_attribute("data-y")
            villages.append({
                "name": village_name,
                "newdid": newdid,
                "x": int(x),
                "y": int(y)
            })
        except Exception as e:
            logger.warning(f"Could not extract info for one village: {e}")

    if not villages:
        logger.error("No villages extracted.")
        return None

    print("\nExtracted Villages:")
    for idx, v in enumerate(villages, start=1):
        print(f"{idx}. {v['name']} (newdid: {v['newdid']}), Coordinates: ({v['x']}, {v['y']})")

    confirm = input("Are these villages correct? (y/n): ").strip().lower()
    if confirm != "y":
        logger.info("Village extraction not confirmed.")
        return None

    logger.info(f"Successfully extracted {len(villages)} villages.")
    
    if return_villages:
        return villages
    
    return None
