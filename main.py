import os
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import auto_farm
import trainer
import villages  # Module for village list extraction

LOGIN_URL = "https://ts1.x1.international.travian.com"

def get_credentials():
    """
    Reads credentials from 'credentials.txt' if available.
    If found, asks if you want to use them.
    Otherwise, prompts for credentials and offers to save them.
    """
    if os.path.exists("credentials.txt"):
        with open("credentials.txt", "r") as file:
            lines = file.read().splitlines()
            if len(lines) >= 2:
                saved_username = lines[0].strip()
                saved_password = lines[1].strip()
                use_file = input("Found saved credentials. Use them? (y/n): ").strip().lower()
                if use_file == 'y':
                    return saved_username, saved_password

    username = input("Enter your Travian username: ")
    password = input("Enter your Travian password: ")
    save = input("Save these credentials for future use? (y/n): ").strip().lower()
    if save == 'y':
        with open("credentials.txt", "w") as file:
            file.write(username + "\n")
            file.write(password + "\n")
    return username, password

def setup_browser():
    """Sets up and returns a new Chrome WebDriver instance."""
    print("[INFO] Launching browser...")
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920x1080")
    # Uncomment the next line to run headless:
    # chrome_options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(driver, username, password):
    """Logs into Travian using the provided credentials."""
    driver.get(LOGIN_URL)
    time.sleep(3)

    try:
        print("[INFO] Loading login page...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        driver.find_element(By.NAME, "name").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        
        print(f"[DEBUG] Current Page URL After Login: {driver.current_url}")
        try:
            driver.find_element(By.CLASS_NAME, "recaptcha-checkbox")
            print("[WARNING] CAPTCHA detected! Please solve it manually.")
            input("[ACTION REQUIRED] Press Enter after solving CAPTCHA...")
        except Exception:
            print("[INFO] No CAPTCHA detected.")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "topBar")))
        print("[SUCCESS] Logged in successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False

def detect_tribe(driver):
    """
    Navigates to the profile edit page, clicks the Overview tab,
    waits for the tribe information to load, extracts the tribe from the table,
    confirms with the user, and saves it to 'tribe.txt' if confirmed.
    """
    profile_url = "https://ts1.x1.international.travian.com/profile/edit"
    print("[INFO] Navigating to the profile edit page for tribe detection...")
    driver.get(profile_url)

    # Wait for the tab container to load and click on the Overview tab.
    try:
        overview_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-tab='1' and contains(.,'Overview')]"))
        )
        overview_tab.click()
    except Exception as e:
        print(f"[ERROR] Could not click Overview tab: {e}")
        return None

    # Wait for the tribe row in the table to appear.
    try:
        tribe_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//tr[th[text()='Tribe']]/td"))
        )
        detected_tribe = tribe_element.text.strip()
        print(f"[INFO] Detected tribe: {detected_tribe}")
        confirm = input("Is this your correct tribe? (y/n): ").strip().lower()
        if confirm == "y":
            with open("tribe.txt", "w") as file:
                file.write(detected_tribe)
            print("[SUCCESS] Tribe saved to tribe.txt")
            return detected_tribe
        else:
            print("[INFO] Tribe detection not confirmed. You can update it manually later if needed.")
            return None
    except Exception as e:
        print(f"[ERROR] Could not detect tribe: {e}")
        return None

def start_tasks(driver, run_auto_farm, run_trainer):
    """
    Starts selected tasks in separate threads.
    run_auto_farm and run_trainer are boolean flags.
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
      1. Ask for login credentials.
      2. Open the browser and log in.
      3. Auto-detect account tribe and confirm/save it.
      4. Ask if the villages list should be refreshed.
      5. Display task menu (Auto-Farm, Trainer, Both, or Exit).
    """
    username, password = get_credentials()
    driver = setup_browser()
    
    if not login(driver, username, password):
        driver.quit()
        return

    # Auto-detect tribe from the profile edit page.
    detected_tribe = detect_tribe(driver)
    if not detected_tribe:
        print("[INFO] Tribe detection was not confirmed or failed.")
    
    # Ask if the user wants to refresh the villages list.
    refresh = input("Do you want to refresh the villages list? (y/n): ").strip().lower()
    if refresh == "y":
        print("[INFO] Refreshing villages list...")
        villages.run_villages(driver)
    else:
        print("[INFO] Skipping villages refresh. Using existing data.")

    # Main task menu.
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
