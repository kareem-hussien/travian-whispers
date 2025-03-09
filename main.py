import warnings
warnings.filterwarnings(
    "ignore", 
    message="Unable to find acceptable character detection dependency", 
    module="requests"
)

import os
import time

from startup.welcome_messages import welcome
from startup.login_credentials import get_credentials
from startup.browser_profile import setup_browser, login_only, update_profile
from startup.villages_list import run_villages
from startup.tasks import run_task_menu

def main():
    """
    Main flow:
      1. Display welcome messages.
      2. Ask for login credentials.
      3. Open the browser and log in.
      4. Ask if the user wants to update their profile (check account tribe and refresh villages).
         - If yes, update profile (detect tribe) and optionally refresh villages.
      5. Display the task menu (Auto-Farm, Trainer, Both, or Exit).
    """
    welcome()
    username, password = get_credentials()
    driver = setup_browser()
    
    if not login_only(driver, username, password):
        driver.quit()
        return

    update_choice = input("Do you want to update your profile (check account tribe and refresh villages)? (y/n): ").strip().lower()
    if update_choice == "y":
        profile_info = update_profile(driver)
        if profile_info:
            detected_tribe, profile_id = profile_info
            print(f"[INFO] Tribe detected: {detected_tribe}, Profile ID: {profile_id}")
            with open("tribe.txt", "w") as file:
                file.write(f"{detected_tribe},{profile_id}")
            print("[SUCCESS] Tribe and profile id saved to tribe.txt")
        else:
            print("[INFO] Profile update failed or not confirmed.")
        refresh = input("Do you want to refresh the villages list? (y/n): ").strip().lower()
        if refresh == "y":
            print("[INFO] Refreshing villages list...")
            run_villages(driver)
        else:
            print("[INFO] Skipping villages refresh. Using existing data.")
    else:
        print("[INFO] Skipping profile update.")

    run_task_menu(driver)

if __name__ == "__main__":
    main()
