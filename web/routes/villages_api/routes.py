"""
Villages API endpoint for direct village management.
"""
import logging
import re
import time
from flask import Blueprint, request, jsonify, session
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from web.utils.decorators import login_required, api_error_handler
from database.models.user import User
from database.models.activity_log import ActivityLog

# Initialize logger
logger = logging.getLogger(__name__)

# Create blueprint
villages_api_bp = Blueprint('villages_api', __name__, url_prefix='/api/user/villages')

@villages_api_bp.route('/extract', methods=['POST'])
@api_error_handler
@login_required
def extract_villages():
    """
    API endpoint to extract villages directly from Travian.
    Uses a robust method that focuses on extracting the essential information.
    """
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Check if Travian credentials are set
    if not user['travianCredentials'].get('username') or not user['travianCredentials'].get('password'):
        return jsonify({
            'success': False,
            'message': 'Travian credentials not set. Please update your Travian settings first.'
        }), 400
    
    driver = None
    
    try:
        # Get Travian credentials
        travian_username = user['travianCredentials']['username']
        travian_password = user['travianCredentials']['password']
        travian_server = user['travianCredentials'].get('server', 'https://ts1.x1.international.travian.com')
        
        # Ensure server URL has protocol
        if not travian_server.startswith(('http://', 'https://')):
            travian_server = f"https://{travian_server}"
        
        logger.info(f"Starting village extraction for user {user['username']}")
        
        # Setup Selenium in headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Check if Selenium Grid URL is configured (for Docker)
        selenium_url = request.environ.get('SELENIUM_REMOTE_URL')
        
        if selenium_url:
            logger.info(f"Using Selenium Grid at {selenium_url}")
            driver = webdriver.Remote(
                command_executor=selenium_url,
                options=chrome_options
            )
        else:
            # Local Chrome WebDriver
            driver = webdriver.Chrome(options=chrome_options)
        
        # Extract villages using our improved method
        villages = improved_village_extraction(driver, travian_username, travian_password, travian_server)
        
        if not villages:
            logger.error("No villages were extracted.")
            return jsonify({
                'success': False,
                'message': 'No villages were extracted. Please try again.'
            }), 400
        
        logger.info(f"Successfully extracted {len(villages)} villages")
        
        # Update user's villages in database
        if user_model.update_user(session['user_id'], {'villages': villages}):
            # Log the activity
            try:
                activity_model = ActivityLog()
                activity_model.log_activity(
                    user_id=session['user_id'],
                    activity_type='village-extract',
                    details=f"Extracted {len(villages)} villages from Travian",
                    status='success'
                )
            except Exception as e:
                logger.error(f"Error logging activity: {e}")
            
            return jsonify({
                'success': True,
                'message': f'Successfully extracted {len(villages)} villages',
                'data': villages
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save extracted villages'
            }), 500
            
    except Exception as e:
        logger.error(f"Error extracting villages: {e}")
        return jsonify({
            'success': False,
            'message': f'Error extracting villages: {str(e)}'
        }), 500
    finally:
        if driver:
            driver.quit()

@villages_api_bp.route('/list', methods=['GET'])
@api_error_handler
@login_required
def list_villages():
    """API endpoint to list user's villages."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Return villages
    return jsonify({
        'success': True,
        'data': user.get('villages', [])
    })

@villages_api_bp.route('/update', methods=['POST'])
@api_error_handler
@login_required
def update_villages():
    """API endpoint to update villages."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Get request data
    data = request.get_json()
    villages = data.get('villages', [])
    
    if not villages:
        return jsonify({
            'success': False,
            'message': 'No villages provided'
        }), 400
    
    # Update user's villages in database
    if user_model.update_user(session['user_id'], {'villages': villages}):
        # Log the activity
        try:
            activity_model = ActivityLog()
            activity_model.log_activity(
                user_id=session['user_id'],
                activity_type='village-update',
                details=f"Updated {len(villages)} villages",
                status='success'
            )
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Villages updated successfully',
            'data': villages
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to update villages'
        }), 500

def improved_village_extraction(driver, username, password, server_url):
    """
    Improved village extraction method that's more robust against UI changes.
    
    Args:
        driver: Selenium WebDriver instance
        username: Travian username
        password: Travian password
        server_url: Travian server URL
        
    Returns:
        list: List of extracted villages
    """
    villages = []
    
    try:
        # Step 1: Navigate to login page and log in
        logger.info(f"Navigating to {server_url}")
        driver.get(server_url)
        time.sleep(2)
        
        # Check if we need to go to login page
        if "login" not in driver.current_url.lower() and "dorf1.php" not in driver.current_url.lower():
            # Try to find and click login button
            try:
                login_link = driver.find_element(By.XPATH, "//a[contains(@href, 'login.php')]")
                login_link.click()
                time.sleep(2)
            except NoSuchElementException:
                # If login link not found, navigate directly to login page
                driver.get(f"{server_url}/login.php")
                time.sleep(2)
        
        # Check if already logged in
        if "dorf1.php" in driver.current_url or "village" in driver.current_url:
            logger.info("Already logged in to Travian.")
        else:
            # Fill in login form
            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "name"))
                )
                password_field = driver.find_element(By.NAME, "password")
                
                # Enter credentials
                username_field.clear()
                username_field.send_keys(username)
                
                password_field.clear()
                password_field.send_keys(password)
                
                # Find and click login button
                login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                login_button.click()
                
                # Wait for successful login (redirect to village page)
                WebDriverWait(driver, 15).until(
                    lambda d: "dorf1.php" in d.current_url or 
                               "village" in d.current_url or 
                               "game.php" in d.current_url
                )
                
                logger.info("Successfully logged in to Travian.")
            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"Login failed: {str(e)}")
                return []
        
        # Step 2: Extract villages using multiple methods for reliability
        
        # Method 1: Try to find villages in the sidebar village list
        try:
            # Wait for the village list to load
            village_list = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "sidebarBoxVillagelist"))
            )
            
            village_elements = village_list.find_elements(By.CSS_SELECTOR, ".listEntry")
            
            if village_elements:
                logger.info(f"Found {len(village_elements)} villages in the sidebar")
                
                for elem in village_elements:
                    try:
                        # Extract village ID (newdid)
                        newdid = elem.get_attribute("data-did")
                        if not newdid:
                            href = elem.get_attribute("href")
                            if href and "newdid=" in href:
                                newdid = href.split("newdid=")[1].split("&")[0]
                        
                        # Get village name
                        name_elem = elem.find_element(By.CSS_SELECTOR, ".name")
                        village_name = name_elem.text.strip()
                        
                        # Get coordinates
                        coords_elem = elem.find_element(By.CSS_SELECTOR, ".coordinatesGrid")
                        x = coords_elem.get_attribute("data-x")
                        y = coords_elem.get_attribute("data-y")
                        
                        # Create village object
                        village = {
                            "name": village_name,
                            "newdid": newdid,
                            "x": int(x) if x and x.isdigit() else 0,
                            "y": int(y) if y and y.isdigit() else 0,
                            "population": 0,  # Will be updated separately
                            "status": "active",
                            "auto_farm_enabled": True,  # Default to enabled
                            "training_enabled": True,   # Default to enabled
                            "resources": {
                                "wood": 0,
                                "clay": 0,
                                "iron": 0,
                                "crop": 0
                            }
                        }
                        
                        villages.append(village)
                        logger.info(f"Extracted village: {village_name} ({x}|{y})")
                        
                    except Exception as e:
                        logger.warning(f"Error extracting village data: {e}")
            
        except (TimeoutException, NoSuchElementException):
            logger.warning("Could not find village list in sidebar")
        
        # If no villages found, try alternative method
        if not villages:
            # Method 2: Try to extract current village info
            try:
                # Get current village name
                village_name_elem = driver.find_element(By.ID, "villageNameField")
                village_name = village_name_elem.text.strip()
                
                # Try to get coordinates
                try:
                    coords_elem = driver.find_element(By.CSS_SELECTOR, ".coordinatesGrid")
                    x = coords_elem.get_attribute("data-x")
                    y = coords_elem.get_attribute("data-y")
                except NoSuchElementException:
                    # Alternative method to find coordinates
                    title_text = driver.title
                    coords_match = re.search(r'\((-?\d+)\|(-?\d+)\)', title_text)
                    if coords_match:
                        x, y = coords_match.groups()
                    else:
                        x, y = "0", "0"
                
                # Try to get newdid from URL or links
                current_url = driver.current_url
                newdid_match = re.search(r'newdid=(\d+)', current_url)
                if newdid_match:
                    newdid = newdid_match.group(1)
                else:
                    # Default ID for single village
                    newdid = "1"  
                
                # Create village object
                village = {
                    "name": village_name,
                    "newdid": newdid,
                    "x": int(x) if x and x.isdigit() else 0,
                    "y": int(y) if y and y.isdigit() else 0,
                    "population": 0,
                    "status": "active",
                    "auto_farm_enabled": True,
                    "training_enabled": True,
                    "resources": {
                        "wood": 0,
                        "clay": 0,
                        "iron": 0,
                        "crop": 0
                    }
                }
                
                villages.append(village)
                logger.info(f"Extracted current village: {village_name} ({x}|{y})")
                
            except Exception as e:
                logger.error(f"Error extracting current village: {e}")
        
        # Method 3: Try to navigate to profile and extract villages list
        if not villages or len(villages) < 2:  # If only one village found, check if there are more
            try:
                # Navigate to profile villages tab
                profile_url = f"{server_url}/profile/villages"
                driver.get(profile_url)
                time.sleep(2)
                
                # Find village table rows
                village_rows = driver.find_elements(By.CSS_SELECTOR, "table.villages tr")
                
                if len(village_rows) > 1:  # Skip header row
                    logger.info(f"Found {len(village_rows)-1} villages in profile")
                    
                    # Clear existing villages if any were found through other methods
                    if villages:
                        villages.clear()
                    
                    for row in village_rows[1:]:  # Skip header row
                        try:
                            # Extract cells
                            cells = row.find_elements(By.TAG_NAME, "td")
                            
                            if len(cells) >= 2:
                                # Extract village name and link
                                name_cell = cells[0]
                                name_link = name_cell.find_element(By.TAG_NAME, "a")
                                village_name = name_link.text.strip()
                                
                                # Extract newdid from link
                                href = name_link.get_attribute("href")
                                newdid_match = re.search(r'newdid=(\d+)', href)
                                newdid = newdid_match.group(1) if newdid_match else f"unknown_{len(villages)}"
                                
                                # Extract coordinates
                                coords_text = ""
                                for cell in cells:
                                    if '(' in cell.text and '|' in cell.text and ')' in cell.text:
                                        coords_text = cell.text
                                        break
                                
                                coords_match = re.search(r'\((-?\d+)\|(-?\d+)\)', coords_text)
                                if coords_match:
                                    x, y = coords_match.groups()
                                else:
                                    x, y = "0", "0"
                                
                                # Create village object
                                village = {
                                    "name": village_name,
                                    "newdid": newdid,
                                    "x": int(x) if x and x.isdigit() else 0,
                                    "y": int(y) if y and y.isdigit() else 0,
                                    "population": 0,
                                    "status": "active",
                                    "auto_farm_enabled": True,
                                    "training_enabled": True,
                                    "resources": {
                                        "wood": 0,
                                        "clay": 0,
                                        "iron": 0,
                                        "crop": 0
                                    }
                                }
                                
                                villages.append(village)
                                logger.info(f"Extracted village from profile: {village_name} ({x}|{y})")
                                
                        except Exception as e:
                            logger.warning(f"Error extracting village from profile row: {e}")
            
            except Exception as e:
                logger.warning(f"Error extracting villages from profile: {e}")
        
        # Step 3: Try to visit each village to get more data if time allows
        if villages and len(villages) < 10:  # Only do this for a reasonable number of villages
            logger.info(f"Gathering additional data for {len(villages)} villages")
            
            # Create a map of villages by newdid for easy updating
            villages_map = {v["newdid"]: v for v in villages}
            
            for newdid, village in villages_map.items():
                try:
                    # Skip placeholder IDs
                    if "unknown" in newdid:
                        continue
                        
                    # Visit the village
                    driver.get(f"{server_url}/dorf1.php?newdid={newdid}")
                    time.sleep(2)
                    
                    # Try to get population
                    try:
                        pop_elem = driver.find_element(By.ID, "population")
                        pop_text = pop_elem.text.strip()
                        if pop_text.isdigit():
                            village['population'] = int(pop_text)
                    except:
                        pass
                    
                    # Try to get resources
                    try:
                        resource_fields = {
                            "wood": (By.ID, "l1"),
                            "clay": (By.ID, "l2"),
                            "iron": (By.ID, "l3"),
                            "crop": (By.ID, "l4")
                        }
                        
                        for resource, locator in resource_fields.items():
                            try:
                                element = driver.find_element(*locator)
                                value_text = element.text.strip().replace(',', '')
                                if value_text.isdigit():
                                    village['resources'][resource] = int(value_text)
                            except:
                                pass
                    except:
                        pass
                    
                except Exception as e:
                    logger.warning(f"Error getting additional data for village {village['name']}: {e}")
            
            # Convert map back to list
            villages = list(villages_map.values())
        
        return villages
        
    except Exception as e:
        logger.error(f"Error in village extraction: {e}")
        return []

def register_routes(app):
    """Register Villages API routes with the application."""
    app.register_blueprint(villages_api_bp)