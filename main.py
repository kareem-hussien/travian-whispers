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
import auto_farm
import trainer
import villages

def start_tasks(driver, run_auto_farm, run_trainer):
    """
    Starts selected tasks in separate threads.
    """
    threads = []
    if run_auto_farm:
        t_af = threading.Thread(target=auto_farm.run_auto_farm, args=(driver,), daemon=True)
        threads.append(t_af)
    if run_trainer:
        t_tr = threading.Thread(target=trainer.run_trainer, args=(driver,), daemon=True)
        threads.append(t_tr)
    
    for t in threads:
        t.start()
    
    print("[INFO] Tasks have been saved and are running concurrently!")
    for t in threads:
        t.join()

def main():
    """
    Main flow:
      1. Display welcome messages.
      2. Ask for login credentials.
      3. Open the browser, log in, and auto-detect account tribe and profile ID (merged in one step).
      4. Ask if the villages list should be refreshed.
      5. Display task menu (Auto-Farm, Trainer, Both, or Exit).
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
        villages.run_villages(driver)
    else:
        print("[INFO] Skipping villages refresh. Using existing data.")
    
    while True:
        print("\n=== Travian Automation Suite ===")
        print("1. Start Auto-Farm")
        print("2. Start Trainer")
        print("3. Both Auto-Farm and Trainer")
        print("4. Exit")
        choice = input("Enter your option (1/2/3/4): ").strip()
        
        if choice == "1":
            start_tasks(driver, run_auto_farm=True, run_trainer=False)
        elif choice == "2":
            start_tasks(driver, run_auto_farm=False, run_trainer=True)
        elif choice == "3":
            start_tasks(driver, run_auto_farm=True, run_trainer=True)
        elif choice == "4":
            print("[INFO] Exiting... Closing browser.")
            driver.quit()
            break
        else:
            print("[ERROR] Invalid choice. Please enter a valid option.")

if __name__ == "__main__":
    main()
