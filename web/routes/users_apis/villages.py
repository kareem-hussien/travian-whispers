"""
Villages management routes for Travian Whispers web application.
"""
import logging
import json
import os
import time
from flask import (
    render_template, flash, session, redirect, 
    url_for, request, jsonify, current_app
)
from bson import ObjectId

from web.utils.decorators import login_required, api_error_handler
from database.models.user import User
from database.models.activity_log import ActivityLog

# Initialize logger
logger = logging.getLogger(__name__)

# Define the extract_villages_internal function first, before it's referenced
def extract_villages_internal(user_id):
    """
    Extract villages internally (without HTTP request/response).
    This can be called from travian_settings when a user adds/updates their account.
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: Result dictionary with keys 'success', 'message', and optionally 'data'
    """
    from database.models.user import User
    from database.models.activity_log import ActivityLog
    
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        return {
            'success': False,
            'message': 'User not found'
        }
    
    # Check if Travian credentials are set
    if not user['travianCredentials'].get('username') or not user['travianCredentials'].get('password'):
        return {
            'success': False,
            'message': 'Travian credentials not set'
        }
    
    driver = None
    
    try:
        # Set up detailed logging
        logger.info(f"Starting internal village extraction for user {user['username']} (ID: {user_id})")
        
        # Get Travian credentials
        travian_username = user['travianCredentials']['username']
        travian_password = user['travianCredentials']['password']
        travian_server = user['travianCredentials'].get('server', 'https://ts1.x1.international.travian.com')
        
        logger.info(f"Using server URL: {travian_server}")
        
        # Import required modules for browser automation
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            logger.info("Successfully imported required Selenium modules")
        except ImportError as e:
            logger.error(f"Failed to import required Selenium modules: {str(e)}")
            return {
                'success': False,
                'message': f'Server configuration error: Unable to import Selenium modules'
            }
        
        # Setup browser
        try:
            logger.info("Setting up browser for internal village extraction")
            
            # Check for Selenium remote URL
            selenium_url = os.environ.get('SELENIUM_REMOTE_URL')
            logger.info(f"Selenium remote URL: {selenium_url if selenium_url else 'Not set - using local browser'}")
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Initialize the WebDriver
            if selenium_url:
                logger.info(f"Using Selenium Grid at {selenium_url} for village extraction")
                try:
                    driver = webdriver.Remote(
                        command_executor=selenium_url,
                        options=chrome_options
                    )
                    logger.info("Successfully connected to Selenium Grid")
                except Exception as e:
                    logger.warning(f"Failed to connect to Selenium Grid: {e}. Falling back to local Chrome.")
                    selenium_url = None  # Force fallback to local Chrome
            
            if not selenium_url:
                # If no Selenium Grid, use local Chrome
                logger.info("Using local Chrome for village extraction")
                # Check if we need to specify the service object
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("Using webdriver_manager to set up ChromeDriver")
                except ImportError:
                    logger.info("webdriver_manager not available, using default Chrome setup")
                    driver = webdriver.Chrome(options=chrome_options)
            
            logger.info("Browser setup successful")
        except Exception as e:
            logger.error(f"Error setting up browser: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to set up browser: {str(e)}'
            }
        
        # Login to Travian
        try:
            logger.info(f"Attempting to log in to Travian as {travian_username}")
            
            # Basic login implementation
            if not travian_server.startswith(('http://', 'https://')):
                travian_server = f"https://{travian_server}"
                
            driver.get(travian_server)
            time.sleep(2)
            
            # Check if we're already on a login page or need to navigate to it
            if "login" not in driver.current_url.lower():
                # Try to find and click a login link
                try:
                    login_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'login')]")
                    if login_links:
                        login_links[0].click()
                        time.sleep(2)
                    else:
                        # Directly navigate to login page
                        driver.get(f"{travian_server}/login.php")
                        time.sleep(2)
                except:
                    # Direct navigation as fallback
                    driver.get(f"{travian_server}/login.php")
                    time.sleep(2)
            
            # Find login form elements
            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "name"))
                )
                password_field = driver.find_element(By.NAME, "password")
                
                # Enter credentials
                username_field.clear()
                username_field.send_keys(travian_username)
                password_field.clear()
                password_field.send_keys(travian_password)
                
                # Find login button
                login_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                
                if login_buttons:
                    login_buttons[0].click()
                    time.sleep(3)  # Wait for login to process
                else:
                    # Try alternate button locators
                    login_buttons = driver.find_elements(By.XPATH, "//button[contains(.,'Login') or contains(.,'Sign in')]")
                    if login_buttons:
                        login_buttons[0].click()
                        time.sleep(3)
                    else:
                        # Last resort - try by form submission
                        form = driver.find_element(By.TAG_NAME, "form")
                        if form:
                            form.submit()
                            time.sleep(3)
                
                # Check if login was successful by looking for typical elements on the game page
                try:
                    # Wait for elements that indicate successful login
                    WebDriverWait(driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.ID, "navigation")),
                            EC.presence_of_element_located((By.ID, "resources")),
                            EC.presence_of_element_located((By.CLASS_NAME, "villageList")),
                            EC.presence_of_element_located((By.ID, "sidebarBoxVillagelist")),
                            EC.presence_of_element_located((By.ID, "village_map")),
                            EC.presence_of_element_located((By.ID, "villageNameField"))
                        )
                    )
                    logger.info("Login successful - found game elements")
                    login_successful = True
                except Exception as e:
                    # If we didn't find game elements, login probably failed
                    logger.warning(f"Login failed - couldn't find game elements: {e}")
                    login_successful = False
            except Exception as e:
                logger.error(f"Error finding or interacting with login elements: {str(e)}")
                login_successful = False
            
            if not login_successful:
                logger.error("Login failed - invalid credentials or Travian site changes")
                if driver:
                    driver.quit()
                return {
                    'success': False,
                    'message': 'Failed to log in to Travian. Please check your credentials or try again later.'
                }
            logger.info("Login successful")
        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            if driver:
                driver.quit()
            return {
                'success': False,
                'message': f'Error during login: {str(e)}'
            }
        
        # Extract villages
        try:
            logger.info("Running village extraction")
            from tasks.villages import run_villages
            
            extracted_villages = run_villages(driver)
            
            if not extracted_villages:
                logger.error("No villages were extracted")
                if driver:
                    driver.quit()
                return {
                    'success': False,
                    'message': 'No villages were extracted. Please try again.'
                }
            
            logger.info(f"Successfully extracted {len(extracted_villages)} villages")
            for idx, village in enumerate(extracted_villages):
                logger.info(f"Village {idx+1}: {village['name']} ({village['x']}|{village['y']})")
                
        except Exception as e:
            logger.error(f"Error extracting villages: {str(e)}", exc_info=True)
            if driver:
                driver.quit()
            return {
                'success': False,
                'message': f'Error extracting villages: {str(e)}'
            }
        
        # Close browser
        if driver:
            driver.quit()
            logger.info("Browser closed")
        
        # Preserve existing settings when updating villages
        current_villages = user.get('villages', [])
        village_settings = {}
        
        # Create a map of existing village settings by newdid
        for village in current_villages:
            newdid = village.get('newdid')
            if newdid:
                village_settings[newdid] = {
                    'auto_farm_enabled': village.get('auto_farm_enabled', False),
                    'training_enabled': village.get('training_enabled', False)
                }
        
        # Apply existing settings to extracted villages
        for village in extracted_villages:
            newdid = village.get('newdid')
            if newdid and newdid in village_settings:
                village['auto_farm_enabled'] = village_settings[newdid]['auto_farm_enabled']
                village['training_enabled'] = village_settings[newdid]['training_enabled']
            else:
                # Default settings for new villages - ENABLE auto-farm by default for better UX
                village['auto_farm_enabled'] = True  # Enable auto-farm by default
                village['training_enabled'] = False
        
        # Update user's villages in database
        logger.info("Updating user's villages in database")
        if user_model.update_user(user_id, {'villages': extracted_villages}):
            # Log the activity
            activity_model = ActivityLog()
            activity_model.log_activity(
                user_id=user_id,
                activity_type='village-extract',
                details=f"Automatically extracted {len(extracted_villages)} villages from Travian",
                status='success'
            )
            
            logger.info(f"User '{user['username']}' extracted {len(extracted_villages)} villages from Travian")
            return {
                'success': True,
                'message': f'Successfully extracted {len(extracted_villages)} villages',
                'data': extracted_villages
            }
        else:
            logger.warning(f"Failed to save extracted villages for user '{user['username']}'")
            return {
                'success': False,
                'message': 'Failed to save extracted villages'
            }
            
    except Exception as e:
        logger.error(f"Error extracting villages for user '{user['username']}': {str(e)}", exc_info=True)
        if driver:
            try:
                driver.quit()
            except:
                pass
        return {
            'success': False,
            'message': f'Error extracting villages: {str(e)}'
        }

def register_routes(user_bp):
    """Register villages routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/villages')(login_required(villages))
    
    # API routes for villages management
    user_bp.route('/api/user/villages/add', methods=['POST'])(api_error_handler(login_required(add_village)))
    user_bp.route('/api/user/villages/update', methods=['POST'])(api_error_handler(login_required(update_village)))
    user_bp.route('/api/user/villages/remove', methods=['POST'])(api_error_handler(login_required(remove_village)))
    user_bp.route('/api/user/villages/settings', methods=['POST'])(api_error_handler(login_required(update_village_settings)))
    user_bp.route('/api/user/villages/extract', methods=['POST'])(api_error_handler(login_required(extract_villages)))

@login_required
def villages():
    """Villages management route."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        # Flash error message
        flash('User not found', 'danger')
        
        # Clear session and redirect to login
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Check if villages array exists and has expected format
    if 'villages' not in user or not isinstance(user['villages'], list):
        # Initialize empty villages array if needed
        user['villages'] = []
        user_model.update_user(session['user_id'], {'villages': []})
        logger.warning(f"Initialized empty villages array for user {user['username']}")
    
    # Format each village to ensure it has all required properties
    formatted_villages = []
    for village in user.get('villages', []):
        # Get activity logs for this village
        activity_model = ActivityLog()
        
        # Get the last farm activity for this village
        farm_activity = activity_model.get_latest_user_activity(
            user_id=session['user_id'],
            activity_type='auto-farm',
            filter_query={'village': village.get('name')}
        )
        
        # Get the last training activity for this village
        training_activity = activity_model.get_latest_user_activity(
            user_id=session['user_id'],
            activity_type='troop-training',
            filter_query={'village': village.get('name')}
        )
        
        # Format village with consistent data structure
        formatted_village = {
            'name': village.get('name', 'Unknown Village'),
            'x': village.get('x', 0),
            'y': village.get('y', 0),
            'newdid': village.get('newdid', '0'),
            'population': village.get('population', 0),
            'status': village.get('status', 'active'),
            'auto_farm_enabled': village.get('auto_farm_enabled', False),
            'training_enabled': village.get('training_enabled', False),
            'resources': village.get('resources', {
                'wood': 0,
                'clay': 0,
                'iron': 0,
                'crop': 0
            }),
            'last_farmed': farm_activity['timestamp'].strftime('%Y-%m-%d %H:%M') if farm_activity and farm_activity.get('timestamp') else 'Never',
            'last_trained': training_activity['timestamp'].strftime('%Y-%m-%d %H:%M') if training_activity and training_activity.get('timestamp') else 'Never'
        }
        
        formatted_villages.append(formatted_village)
    
    # Render villages template with formatted data
    return render_template(
        'user/villages.html', 
        villages=formatted_villages,
        current_user=user, 
        title='Villages Management'
    )

@api_error_handler
@login_required
def add_village():
    """API endpoint to add a village manually."""
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
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # Validate required fields
    required_fields = ['village_name', 'village_x', 'village_y', 'village_newdid']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Create village data structure
    village = {
        'name': data['village_name'],
        'x': int(data['village_x']),
        'y': int(data['village_y']),
        'newdid': data['village_newdid'],
        'population': int(data.get('village_population', 0)),
        'auto_farm_enabled': data.get('auto_farm_enabled', True),  # Default to True for better UX
        'training_enabled': data.get('training_enabled', False),
        'status': 'active',
        'resources': {
            'wood': 0,
            'clay': 0,
            'iron': 0, 
            'crop': 0
        }
    }
    
    # Check if village with this newdid already exists
    current_villages = user.get('villages', [])
    for existing_village in current_villages:
        if existing_village.get('newdid') == village['newdid']:
            return jsonify({
                'success': False,
                'message': 'A village with this ID already exists'
            }), 400
    
    # Add village to user's villages
    current_villages.append(village)
    
    # Update user in database
    if user_model.update_user(session['user_id'], {'villages': current_villages}):
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='village-add',
            details=f"Manually added village: {village['name']} ({village['x']}|{village['y']})",
            status='success',
            village=village['name']
        )
        
        logger.info(f"User '{user['username']}' added village '{village['name']}'")
        return jsonify({
            'success': True,
            'message': 'Village added successfully',
            'data': village
        })
    else:
        logger.warning(f"Failed to add village for user '{user['username']}'")
        return jsonify({
            'success': False,
            'message': 'Failed to add village'
        }), 500

@api_error_handler
@login_required
def update_village():
    """API endpoint to update a village."""
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
    
    if not data or 'village_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Missing village ID'
        }), 400
    
    # Find the village to update
    current_villages = user.get('villages', [])
    village_idx = None
    
    for idx, village in enumerate(current_villages):
        if str(village.get('newdid')) == str(data['village_id']):
            village_idx = idx
            break
    
    if village_idx is None:
        return jsonify({
            'success': False,
            'message': 'Village not found'
        }), 404
    
    # Get the original village data before update (for logging)
    original_village = current_villages[village_idx].copy()
    
    # Update village data
    if 'village_name' in data:
        current_villages[village_idx]['name'] = data['village_name']
    
    if 'village_x' in data:
        current_villages[village_idx]['x'] = int(data['village_x'])
    
    if 'village_y' in data:
        current_villages[village_idx]['y'] = int(data['village_y'])
    
    if 'village_population' in data:
        current_villages[village_idx]['population'] = int(data['village_population'])
    
    if 'auto_farm_enabled' in data:
        current_villages[village_idx]['auto_farm_enabled'] = bool(data['auto_farm_enabled'])
    
    if 'training_enabled' in data:
        current_villages[village_idx]['training_enabled'] = bool(data['training_enabled'])
    
    # Update user in database
    if user_model.update_user(session['user_id'], {'villages': current_villages}):
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='village-update',
            details=f"Updated village: {current_villages[village_idx]['name']} ({current_villages[village_idx]['x']}|{current_villages[village_idx]['y']})",
            status='success',
            village=current_villages[village_idx]['name']
        )
        
        logger.info(f"User '{user['username']}' updated village '{original_village['name']}'")
        return jsonify({
            'success': True,
            'message': 'Village updated successfully',
            'data': current_villages[village_idx]
        })
    else:
        logger.warning(f"Failed to update village for user '{user['username']}'")
        return jsonify({
            'success': False,
            'message': 'Failed to update village'
        }), 500

@api_error_handler
@login_required
def remove_village():
    """API endpoint to remove a village."""
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
    
    if not data or 'village_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Missing village ID'
        }), 400
    
    # Find the village to remove
    current_villages = user.get('villages', [])
    village_to_remove = None
    
    for village in current_villages:
        if str(village.get('newdid')) == str(data['village_id']):
            village_to_remove = village
            break
    
    if village_to_remove is None:
        return jsonify({
            'success': False,
            'message': 'Village not found'
        }), 404
    
    # Remove the village from the list
    current_villages = [v for v in current_villages if str(v.get('newdid')) != str(data['village_id'])]
    
    # Update user in database
    if user_model.update_user(session['user_id'], {'villages': current_villages}):
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='village-remove',
            details=f"Removed village: {village_to_remove['name']} ({village_to_remove['x']}|{village_to_remove['y']})",
            status='success'
        )
        
        logger.info(f"User '{user['username']}' removed village '{village_to_remove['name']}'")
        return jsonify({
            'success': True,
            'message': 'Village removed successfully'
        })
    else:
        logger.warning(f"Failed to remove village for user '{user['username']}'")
        return jsonify({
            'success': False,
            'message': 'Failed to remove village'
        }), 500

@api_error_handler
@login_required
def update_village_settings():
    """API endpoint to update village automation settings."""
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
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # Get selected villages for auto farm
    auto_farm_villages = data.get('auto_farm_villages', [])
    
    # Get selected villages for troop training
    training_villages = data.get('training_villages', [])
    
    # Update villages settings
    current_villages = user.get('villages', [])
    
    for village in current_villages:
        village_id = str(village.get('newdid'))
        
        # Update auto farm setting
        village['auto_farm_enabled'] = village_id in auto_farm_villages
        
        # Update training setting
        village['training_enabled'] = village_id in training_villages
    
    # Update user in database
    if user_model.update_user(session['user_id'], {'villages': current_villages}):
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='village-settings',
            details=f"Updated automation settings for {len(auto_farm_villages)} auto-farm villages and {len(training_villages)} training villages",
            status='success'
        )
        
        logger.info(f"User '{user['username']}' updated village automation settings")
        return jsonify({
            'success': True,
            'message': 'Village settings updated successfully'
        })
    else:
        logger.warning(f"Failed to update village settings for user '{user['username']}'")
        return jsonify({
            'success': False,
            'message': 'Failed to update village settings'
        }), 500

@api_error_handler
@login_required
def extract_villages():
    """API endpoint to extract villages from Travian."""
    # Call the internal function, just passing the user ID from the session
    result = extract_villages_internal(session['user_id'])
    
    # Return JSON response based on the result
    if result.get('success'):
        return jsonify({
            'success': True,
            'message': result.get('message', f'Successfully extracted {len(result.get("data", []))} villages'),
            'data': result.get('data', [])
        })
    else:
        return jsonify({
            'success': False,
            'message': result.get('message', 'Unknown error occurred during extraction')
        }), 500
