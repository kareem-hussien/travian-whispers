import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def train_troops(driver, building_url, troop_number, troop_type, count):
    """
    Trains troops by:
      1. Navigating to the building URL.
      2. Clicking the correct troop’s input field (using troop_number as 'tX').
      3. Entering the desired troop count correctly.
      4. Clicking the Train button.
    """
    print(f"[INFO] Navigating to {building_url} to train {count} {troop_type}.")
    driver.get(building_url)
    time.sleep(3)  # Wait for the building page to load

    try:
        # Locate the correct input field using troop_number (e.g., name="t3")
        input_xpath = f"//input[@type='text' and @name='{troop_number}']"
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, input_xpath))
        )
        input_field.clear()
        input_field.send_keys(str(count))
        print(f"[INFO] Entered {count} for {troop_type}.")
    except Exception as e:
        print(f"[ERROR] Could not find or fill the input field for {troop_type}: {e}")
        return

    try:
        # Click the correct Train button
        train_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='s1' and contains(@class, 'startTraining')]"))
        )
        train_button.click()
        print(f"[INFO] Clicked Train button for {troop_type}.")
    except Exception as e:
        print(f"[ERROR] Could not click the Train button for {troop_type}: {e}")
        return

    # Ensure the training order is processed
    time.sleep(2)
