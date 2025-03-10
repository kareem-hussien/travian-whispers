import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def train_troops(driver, building_url, troop_type, count):
    """
    Trains troops by:
      1. Navigating to the building URL.
      2. Clicking the troop’s anchor to open its training dialog.
      3. Waiting for the input field to appear.
      4. Entering the desired troop count.
      5. Clicking the Train button.
      
    Adjust the XPaths below if your Travian version differs.
    """
    print(f"[INFO] Navigating to {building_url} to train {count} {troop_type}.")
    driver.get(building_url)
    time.sleep(3)  # Wait for the building page to load

    try:
        # Step 2: Find and click the anchor for the troop type
        troop_anchor = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(),'{troop_type}')]"))
        )
        troop_anchor.click()
        print(f"[INFO] Clicked on {troop_type} link to open training dialog.")
    except Exception as e:
        print(f"[ERROR] Could not click troop link for {troop_type}: {e}")
        return

    try:
        # Step 3: Wait for the training dialog to appear and locate the input field.
        # The input field for troop count is assumed to be within the dialog.
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='text' and contains(@name, 't')]"))
        )
        input_field.clear()
        input_field.send_keys(str(count))
        print(f"[INFO] Entered {count} for {troop_type}.")
    except Exception as e:
        print(f"[ERROR] Could not find or fill the input field for {troop_type}: {e}")
        return

    try:
        # Step 4: Find and click the Train button.
        train_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='s1' and contains(@class, 'startTraining')]"))
        )
        train_button.click()
        print(f"[INFO] Clicked Train button for {troop_type}.")
    except Exception as e:
        print(f"[ERROR] Could not click the Train button for {troop_type}: {e}")
        return

    # Wait a little to ensure the training order is processed.
    time.sleep(2)
