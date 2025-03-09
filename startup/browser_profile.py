import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

LOGIN_URL = "https://ts1.x1.international.travian.com"

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

def login_and_detect_profile(driver, username, password):
    """
    Opens the browser, logs in with provided credentials, then auto-detects the account tribe
    and profile ID by navigating to the profile edit page and clicking the Overview tab.
    
    Returns a tuple (login_success, detected_info).
    detected_info is a tuple (detected_tribe, profile_id) if successful, else None.
    """
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
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False, None
    
    # Navigate to the profile edit page for tribe detection.
    profile_edit_url = "https://ts1.x1.international.travian.com/profile/edit"
    print("[INFO] Navigating to the profile edit page for tribe detection...")
    driver.get(profile_edit_url)
    try:
        overview_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-tab='1' and contains(.,'Overview')]"))
        )
        overview_tab.click()
    except Exception as e:
        print(f"[ERROR] Could not click Overview tab: {e}")
        return True, None

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
            return True, (detected_tribe, profile_id)
        else:
            print("[INFO] Tribe detection not confirmed.")
            return True, None
    except Exception as e:
        print(f"[ERROR] Could not detect tribe: {e}")
        return True, None
