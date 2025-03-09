import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

FARM_LIST_URL = "https://ts1.x1.international.travian.com/build.php?id=39&gid=16&tt=99"

def send_farm_list(driver):
    """Clicks the 'Start all farm lists' button."""
    try:
        driver.get(FARM_LIST_URL)
        time.sleep(3)
        try:
            start_all_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'startAllFarmLists')]"))
            )
            start_all_button.click()
            print("[SUCCESS] Clicked 'Start all farm lists' button!")
        except:
            print("[ERROR] 'Start all farm lists' button not found!")
    except Exception as e:
        print(f"[ERROR] Could not send farm list: {e}")

def run_auto_farm(driver):
    """Runs the farm list automation in a loop."""
    while True:
        send_farm_list(driver)
        wait_time = random.randint(1800, 2700)  # 30 to 45 minutes
        print(f"[INFO] Waiting for {wait_time / 60:.2f} minutes before next farm list send.")
        time.sleep(wait_time)
