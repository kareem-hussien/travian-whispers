import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

VILLAGE_OVERVIEW_URL = "https://ts1.x1.international.travian.com/dorf1.php"

def run_villages(driver):
    """
    Navigates to the village overview page, extracts the list of villages,
    prints them for confirmation, and if confirmed, saves them to villages_list.txt.
    Extracted details include village name, coordinates, and newdid.
    """
    print("[INFO] Navigating to the village overview page...")
    driver.get(VILLAGE_OVERVIEW_URL)
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "villageList"))
        )
    except Exception as e:
        print(f"[ERROR] Village list not found: {e}")
        return
    
    time.sleep(3)

    villages = []
    village_elements = driver.find_elements(By.CSS_SELECTOR, "div.villageList div.listEntry.village")
    if not village_elements:
        print("[ERROR] No village entries found.")
        return

    for elem in village_elements:
        try:
            newdid = elem.get_attribute("data-did")
            name_elem = elem.find_element(By.CSS_SELECTOR, "span.name")
            village_name = name_elem.text.strip()
            coord_elem = elem.find_element(By.CSS_SELECTOR, "span.coordinatesGrid")
            x = coord_elem.get_attribute("data-x")
            y = coord_elem.get_attribute("data-y")
            villages.append({
                "newdid": newdid,
                "name": village_name,
                "x": x,
                "y": y
            })
        except Exception as e:
            print(f"[WARNING] Could not extract info for one village: {e}")

    if not villages:
        print("[ERROR] No villages extracted.")
        return

    print("\nExtracted Villages:")
    for idx, v in enumerate(villages, start=1):
        print(f"{idx}. {v['name']} (newdid: {v['newdid']}), Coordinates: ({v['x']}, {v['y']})")

    confirm = input("Are these villages correct? (y/n): ").strip().lower()
    if confirm != "y":
        print("[INFO] Aborting village extraction. No file will be saved.")
        return

    try:
        with open("villages_list.txt", "w") as file:
            for v in villages:
                file.write(f"{v['name']},{v['newdid']},{v['x']},{v['y']}\n")
        print("[SUCCESS] Villages list saved to villages_list.txt")
    except Exception as e:
        print(f"[ERROR] Could not write to file: {e}")
