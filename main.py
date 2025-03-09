import warnings
warnings.filterwarnings(
    "ignore", 
    message="Unable to find acceptable character detection dependency", 
    module="requests"
)

import os
import time
import threading

from startup.welcome_messages import welcome
from startup.login_credentials import get_credentials
from startup.browser_profile import setup_browser, login_and_detect_profile
from startup.villages_list import run_villages

import auto_farm
import trainer
# Note: The task menu will be imported later from startup.tasks

def main():
    """
    Main flow:
      1. Display welcome messages.
      2. Ask for login credentials.
      3. Open the browser, log in, and auto-detect account tribe and profile ID.
      4. Ask if the villages list should be refreshed.
      5. Display the task menu (moved to startup/tasks.py).
    """
    welcome()
    username, password = get_credentials()
    driver = setup_browser()
    
    login_success, detected_info = login_and_detect_profile(driver, username, password)
    if not login_success:
        driver.quit()
        return
    
    if detected_info:
        detected_tribe, profile_id = detected_info
        print(f"[INFO] Tribe detected: {detected_tribe}, Profile ID: {profile_id}")
        with open("tribe.txt", "w") as file:
            file.write(f"{detected_tribe},{profile_id}")
        print("[SUCCESS] Tribe and profile id saved to tribe.txt")
    else:
        print("[INFO] Tribe detection was not confirmed or failed.")
    
    refresh = input("Do you want to refresh the villages list? (y/n): ").strip().lower()
    if refresh == "y":
        print("[INFO] Refreshing villages list...")
        run_villages(driver)
    else:
        print("[INFO] Skipping villages refresh. Using existing data.")
    
    # Import and run the task menu from startup/tasks.py
    from startup.tasks import run_task_menu
    run_task_menu(driver)

if __name__ == "__main__":
    main()
