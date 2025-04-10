"""
Enhanced villages management route handlers for Travian Whispers.
This implementation replaces the existing extraction method with the improved version.
"""
import logging
from flask import (
    render_template, flash, session, redirect, 
    url_for, request, jsonify, current_app
)
from bson import ObjectId

from web.utils.decorators import login_required, api_error_handler
from database.models.user import User
from database.models.activity_log import ActivityLog
from improved_villages_extractor import get_villages_for_user, save_villages_to_database

# Initialize logger
logger = logging.getLogger(__name__)

@api_error_handler
@login_required
def extract_villages():
    """API endpoint to extract villages from Travian."""
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
        # Set up logging for detailed troubleshooting
        logger.info(f"Starting enhanced village extraction for user {user['username']}")
        
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
            from startup.browser_profile import setup_browser, login
            
            logger.info("Successfully imported required modules")
        except ImportError as e:
            logger.error(f"Failed to import required modules: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Failed to import required modules: {str(e)}'
            }), 500
        
        # Setup browser
        try:
            logger.info("Setting up browser")
            driver = setup_browser(session['user_id'])
            if not driver:
                logger.error("Failed to set up browser")
                return jsonify({
                    'success': False,
                    'message': 'Failed to set up browser'
                }), 500
            logger.info("Browser setup successful")
        except Exception as e:
            logger.error(f"Error setting up browser: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error setting up browser: {str(e)}'
            }), 500
        
        # Login to Travian
        try:
            logger.info(f"Attempting to log in to Travian as {travian_username}")
            login_successful = login(
                driver, 
                travian_username, 
                travian_password, 
                travian_server
            )
            
            if not login_successful:
                logger.error("Login failed")
                if driver:
                    driver.quit()
                return jsonify({
                    'success': False,
                    'message': 'Failed to log in to Travian. Please check your credentials.'
                }), 400
            logger.info("Login successful")
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            if driver:
                driver.quit()
            return jsonify({
                'success': False,
                'message': f'Error during login: {str(e)}'
            }), 500
        
        # Extract villages using the improved method
        try:
            logger.info("Running enhanced village extraction")
            extracted_villages = get_villages_for_user(
                driver,
                user_id=session['user_id'],
                compare_with_db=True,
                server_url=travian_server
            )
            
            if not extracted_villages:
                logger.error("No villages were extracted")
                if driver:
                    driver.quit()
                return jsonify({
                    'success': False,
                    'message': 'No villages were extracted. Please try again.'
                }), 400
            
            logger.info(f"Successfully extracted {len(extracted_villages)} villages")
            
            # Save villages to database
            save_result = save_villages_to_database(session['user_id'], extracted_villages)
            
            if not save_result:
                logger.warning("Failed to save villages to database")
                
        except Exception as e:
            logger.error(f"Error extracting villages: {str(e)}")
            if driver:
                driver.quit()
            return jsonify({
                'success': False,
                'message': f'Error extracting villages: {str(e)}'
            }), 500
        
        # Close browser
        if driver:
            driver.quit()
            logger.info("Browser closed")
        
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='village-extract',
            details=f"Extracted {len(extracted_villages)} villages from Travian",
            status='success'
        )
        
        logger.info(f"User '{user['username']}' extracted {len(extracted_villages)} villages from Travian")
        return jsonify({
            'success': True,
            'message': f'Successfully extracted {len(extracted_villages)} villages',
            'data': extracted_villages
        })
            
    except Exception as e:
        logger.error(f"Error extracting villages for user '{user['username']}': {str(e)}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return jsonify({
            'success': False,
            'message': f'Error extracting villages: {str(e)}'
        }), 500

def register_enhanced_routes(user_bp):
    """
    Register enhanced villages routes with the user blueprint.
    
    Args:
        user_bp: Flask Blueprint for user routes
    """
    # API routes for enhanced villages management
    user_bp.route('/api/user/villages/extract-enhanced', methods=['POST'])(api_error_handler(login_required(extract_villages)))
