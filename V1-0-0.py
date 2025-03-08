import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Travian URLs
LOGIN_URL = "https://ts1.x1.international.travian.com"
FARM_LIST_URL = "https://ts1.x1.international.travian.com/build.php?id=39&gid=16&tt=99"

# Ask for credentials
username = input("Enter your Travian username: ")
password = input("Enter your Travian password: ")

# Setup Chrome WebDriver
chrome_options = Options()
# Remove headless mode to check visually if login works
# chrome_options.add_argument("--headless")  # Comment this out to see browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920x1080")

# Start WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def login():
    """Logs into Travian account, waits for post-login confirmation"""
    driver.get(LOGIN_URL)
    time.sleep(3)

    try:
        print("[INFO] Loading login page...")

        # Wait for username field
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "name")))

        username_input = driver.find_element(By.NAME, "name")
        username_input.send_keys(username)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)

        # Click the login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        time.sleep(5)  # Give time for login process

        # Debug: Print the current URL after login attempt
        print(f"[DEBUG] Current Page URL After Login: {driver.current_url}")

        # Check for CAPTCHA
        try:
            captcha_element = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox")
            print("[WARNING] CAPTCHA detected! Please solve it manually.")
            input("[ACTION REQUIRED] Press Enter after solving CAPTCHA...")
        except:
            print("[INFO] No CAPTCHA detected.")

        # Wait for a post-login element that confirms successful login
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "topBar")))
            print("[SUCCESS] Logged in successfully!")
            return True
        except:
            print("[ERROR] Login failed! Could not detect post-login elements.")
            return False

    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False

def send_farm_list():
    """Clicks the 'Start all farm lists' button"""
    try:
        driver.get(FARM_LIST_URL)
        time.sleep(3)

        # Look for "Start all farm lists" button
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

if login():
    while True:
        send_farm_list()
        wait_time = random.randint(1800, 2700)  # 30 to 45 minutes
        print(f"[INFO] Waiting for {wait_time / 60:.2f} minutes before next farm list send.")
        time.sleep(wait_time)
