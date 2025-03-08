import warnings
warnings.filterwarnings(
    "ignore", 
    message="Unable to find acceptable character detection dependency", 
    module="requests"
)

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

def welcome():
    """Displays welcome messages with a loading effect."""
    messages = [
        "Travian Whispers",
        "made by Eng. Kareem Hussien",
        "WhatsApp : https://wa.me/00201099339393"
    ]
    # For each message, print it, then show 5 dots (with a space before each) over 3 seconds.
    for message in messages:
        print(message, end='', flush=True)
        for i in range(5):
            print(" .", end='', flush=True)
            time.sleep(0.6)  # 0.6 sec per dot gives 3 seconds total per message.
        print()  # New line after each message.

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
    waits for the page to fully load (so that the URL becomes like .../profile/4662),
    extracts the profile ID and tribe type from the table,
    and then confirms with the user.
    If confirmed, saves both values to 'tribe.txt' in the format: tribe,profileID.
    """
    profile_edit_url = "https://ts1.x1.international.travian.com/profile/edit"
    print("[INFO] Navigating to the profile edit page for tribe detection...")
    driver.get(profile_edit_url)

    # Click the Overview tab.
    try:
        overview_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-tab='1' and contains(.,'Overview')]"))
        )
        overview_tab.click()
    except Exception as e:
        print(f"[ERROR] Could not click Overview tab: {e}")
        return None

    # Wait until the URL changes to one containing /profile/ (e.g., .../profile/4662).
    try:
        WebDriverWait(driver, 10).until(lambda d: "/profile/" in d.current_url and d.current_url != profile_edit_url)
        current_url = driver.current_url
        print(f"[INFO] Redirected URL: {current_url}")
        profile_id = current_url.rstrip("/").split("/")[-1]
    except Exception as e:
        print(f"[ERROR] Could not retrieve profile id from URL: {e}")
        profile_id = None

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
                file.write(f"{detected_tribe},{profile_id}")
            print(f"[SUCCESS] Tribe and profile id saved to tribe.txt: {detected_tribe}, {profile_id}")
            return (detected_tribe, profile_id)
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
      1. Display welcome messages.
      2. Ask for login credentials.
      3. Open the browser and log in.
      4. Auto-detect account tribe (and extract profile id) from the profile edit page.
      5. Ask if the villages list should be refreshed.
      6. Display task menu (Auto-Farm, Trainer, Both, or Exit).
    """
    welcome()
    username, password = get_credentials()
    driver = setup_browser()
    
    if not login(driver, username, password):
        driver.quit()
        return

    # Auto-detect tribe and profile id.
    detected_info = detect_tribe(driver)
    if not detected_info:
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
