import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

LOGIN_URL = "https://ts1.x1.international.travian.com"

def setup_browser(headless=False, user_id=None):
    """
    Sets up and returns a new Chrome WebDriver instance.
    If user_id is provided, tries to load saved session.
    
    Args:
        headless (bool): Whether to run in headless mode
        user_id (str, optional): User ID to load saved session
        
    Returns:
        WebDriver: Selenium WebDriver instance
    """
    print("[INFO] Launching browser...")
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920x1080")
    
    if headless:
        chrome_options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Try to load saved session if user_id is provided
    if user_id:
        session_loaded = load_browser_session(driver, user_id)
        if session_loaded:
            return driver
    
    return driver

def save_browser_session(driver, user_id):
    """
    Save browser cookies for future sessions.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        user_id (str): User ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from utils.encryption import encrypt_data
        from database.models.user import User
        
        # Get cookies from the browser
        cookies = driver.get_cookies()
        
        # Serialize cookies to JSON
        serialized_cookies = json.dumps(cookies)
        
        # Encrypt the serialized cookies
        encrypted_cookies = encrypt_data(serialized_cookies)
        
        # Update user document
        user_model = User()
        update_data = {
            "browserSession.cookies": encrypted_cookies,
            "browserSession.lastSaved": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        result = user_model.update_user(user_id, update_data)
        
        if result:
            print("[INFO] Browser session saved successfully")
            return True
        else:
            print("[ERROR] Failed to save browser session")
            return False
    except Exception as e:
        print(f"[ERROR] Error saving browser session: {e}")
        return False

def load_browser_session(driver, user_id):
    """
    Load saved browser cookies into the driver.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        user_id (str): User ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from utils.encryption import decrypt_data
        from database.models.user import User
        
        # Get user document
        user_model = User()
        user = user_model.get_user_by_id(user_id)
        
        # Check if browser session exists
        if not user or "browserSession" not in user or not user["browserSession"].get("cookies"):
            print("[INFO] No saved browser session found")
            return False
        
        # Decrypt cookies
        encrypted_cookies = user["browserSession"]["cookies"]
        serialized_cookies = decrypt_data(encrypted_cookies)
        
        if not serialized_cookies:
            print("[ERROR] Failed to decrypt browser session")
            return False
        
        # Deserialize cookies
        cookies = json.loads(serialized_cookies)
        
        # Navigate to the domain first (required to set cookies)
        driver.get(LOGIN_URL)
        
        # Add cookies to the browser
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"[WARNING] Failed to add cookie: {e}")
        
        # Refresh the page to apply cookies
        driver.refresh()
        
        # Check if still logged in
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "topBar")))
            print("[INFO] Browser session restored successfully")
            return True
        except:
            print("[INFO] Browser session expired or invalid")
            return False
    except Exception as e:
        print(f"[ERROR] Error loading browser session: {e}")
        return False
    
def login_only(driver, username, password, user_id=None):
    """
    Logs in with the provided credentials and returns True if successful.
    If user_id is provided, saves the session after login.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        username (str): Travian username
        password (str): Travian password
        user_id (str, optional): User ID to save session
        
    Returns:
        bool: True if login successful, False otherwise
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
        except:
            print("[INFO] No CAPTCHA detected.")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "topBar")))
        print("[SUCCESS] Logged in successfully!")
        
        # Save browser session if user_id is provided
        if user_id:
            save_browser_session(driver, user_id)
        
        return True
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False

def update_profile(driver, profile_path="info/profile/tribe.txt"):
    """
    Navigates to the profile edit page, clicks the Overview tab,
    waits for the URL to update (e.g. .../profile/4662), and extracts the tribe.
    Saves tribe & profile ID to 'info/profile/tribe.txt' if confirmed.
    Returns (detected_tribe, profile_id) if successful, else None.
    """
    profile_edit_url = "https://ts1.x1.international.travian.com/profile/edit"
    print("[INFO] Navigating to the profile edit page for profile update...")
    driver.get(profile_edit_url)

    # Click the "Overview" tab
    try:
        overview_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-tab='1' and contains(.,'Overview')]"))
        )
        overview_tab.click()
    except Exception as e:
        print(f"[ERROR] Could not click Overview tab: {e}")
        return None

    # Wait until the URL changes to .../profile/xxxx
    try:
        WebDriverWait(driver, 10).until(lambda d: "/profile/" in d.current_url and d.current_url != profile_edit_url)
        current_url = driver.current_url
        print(f"[INFO] Redirected URL: {current_url}")
        profile_id = current_url.rstrip("/").split("/")[-1]
    except Exception as e:
        print(f"[ERROR] Could not retrieve profile id from URL: {e}")
        profile_id = None

    # Detect tribe from the table
    try:
        tribe_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//tr[th[text()='Tribe']]/td"))
        )
        detected_tribe = tribe_element.text.strip()
        print(f"[INFO] Detected tribe: {detected_tribe}")
        confirm = input("Is this your correct tribe? (y/n): ").strip().lower()
        if confirm == "y":
            with open(profile_path, "w") as file:
                file.write(f"{detected_tribe},{profile_id}")
            print("[SUCCESS] Tribe and profile ID saved.")
            return (detected_tribe, profile_id)
        else:
            print("[INFO] Tribe detection not confirmed.")
            return None
    except Exception as e:
        print(f"[ERROR] Could not detect tribe: {e}")
        return None
