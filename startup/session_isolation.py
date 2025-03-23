"""
Session Isolation module for Travian Whispers application.
This module provides utilities for isolating user browser sessions.
"""
import logging
import os
import random
import string
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from flask import current_app
from startup.ip_manager import IPManager

# Initialize logger
logger = logging.getLogger(__name__)


class SessionManager:
    """Manager for isolated browser sessions."""
    
    def __init__(self):
        """Initialize SessionManager."""
        self.ip_manager = IPManager()
        self.session_dir = os.path.join(os.getcwd(), 'browser_sessions')
        self.active_sessions = {}
        
        # Create session directory if it doesn't exist
        os.makedirs(self.session_dir, exist_ok=True)
    
    def get_session_for_user(self, user_id, create=True):
        """
        Get or create a browser session for a user.
        
        Args:
            user_id (str): The user ID
            create (bool, optional): Create a new session if one doesn't exist
            
        Returns:
            str: Path to the session directory
        """
        # Check if user has an active session
        if user_id in self.active_sessions:
            session_path = self.active_sessions[user_id]['path']
            
            # Verify the session directory exists
            if os.path.exists(session_path):
                return session_path
            else:
                # Session directory doesn't exist, remove from active sessions
                self.active_sessions.pop(user_id, None)
        
        # Create a new session if requested
        if create:
            return self._create_user_session(user_id)
        else:
            return None
    
    def _create_user_session(self, user_id):
        """
        Create a new browser session for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            str: Path to the session directory
        """
        # Generate a unique session ID
        session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        session_path = os.path.join(self.session_dir, f"user_{user_id}_{session_id}")
        
        # Create the session directory
        os.makedirs(session_path, exist_ok=True)
        
        # Record the session
        self.active_sessions[user_id] = {
            'id': session_id,
            'path': session_path,
            'created_at': datetime.utcnow()
        }
        
        logger.info(f"Created browser session for user {user_id}: {session_path}")
        return session_path
    
    def clear_user_session(self, user_id):
        """
        Clear a user's browser session.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            bool: True if session was cleared, False otherwise
        """
        if user_id not in self.active_sessions:
            logger.warning(f"No active session found for user {user_id}")
            return False
        
        session_path = self.active_sessions[user_id]['path']
        
        try:
            # Remove the session directory
            if os.path.exists(session_path):
                shutil.rmtree(session_path)
                
            # Remove from active sessions
            self.active_sessions.pop(user_id, None)
            
            logger.info(f"Cleared browser session for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing session for user {user_id}: {e}")
            return False
    
    def rotate_user_session(self, user_id):
        """
        Rotate a user's browser session.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            str: Path to the new session directory
        """
        # Clear existing session
        self.clear_user_session(user_id)
        
        # Create a new session
        return self._create_user_session(user_id)
    
    def clean_old_sessions(self, max_age_hours=24):
        """
        Clean up old browser sessions.
        
        Args:
            max_age_hours (int, optional): Maximum age in hours
            
        Returns:
            int: Number of sessions cleaned
        """
        cleaned_count = 0
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Check active sessions
        sessions_to_remove = []
        
        for user_id, session in self.active_sessions.items():
            if session['created_at'] < cutoff_time:
                sessions_to_remove.append(user_id)
        
        # Clean up old sessions
        for user_id in sessions_to_remove:
            if self.clear_user_session(user_id):
                cleaned_count += 1
        
        # Also check for orphaned session directories
        for item in os.listdir(self.session_dir):
            item_path = os.path.join(self.session_dir, item)
            
            if os.path.isdir(item_path):
                # Check the directory modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                
                if mtime < cutoff_time:
                    try:
                        shutil.rmtree(item_path)
                        cleaned_count += 1
                        logger.info(f"Cleaned orphaned session directory: {item}")
                    except Exception as e:
                        logger.error(f"Error cleaning orphaned session: {e}")
        
        logger.info(f"Cleaned {cleaned_count} old browser sessions")
        return cleaned_count


class BrowserIsolationManager:
    """Manager for browser isolation and IP assignment."""
    
    def __init__(self):
        """Initialize BrowserIsolationManager."""
        self.session_manager = SessionManager()
        self.ip_manager = IPManager()
    
    def get_isolated_browser_config(self, user_id):
        """
        Get an isolated browser configuration for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            dict: Browser configuration including proxy and session
        """
        # Get session path
        session_path = self.session_manager.get_session_for_user(user_id)
        
        # Get IP for the user
        ip_data = self.ip_manager.get_ip_for_user(user_id)
        
        if not ip_data:
            logger.error(f"Failed to get IP for user {user_id}")
            proxy_url = None
        else:
            proxy_url = self.ip_manager.get_proxy_url(ip_data)
        
        # Create browser configuration
        browser_config = {
            'session_path': session_path,
            'proxy': proxy_url,
            'user_agent': self._get_random_user_agent(),
            'headers': self._get_headers_for_user(user_id),
            'ip_data': ip_data
        }
        
        return browser_config
    
    def _get_random_user_agent(self):
        """
        Get a random user agent.
        
        Returns:
            str: Random user agent string
        """
        # Common user agents
        user_agents = [
            # Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            # Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
            # Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
        ]
        
        return random.choice(user_agents)
    
    def _get_headers_for_user(self, user_id):
        """
        Get custom headers for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            dict: Headers dictionary
        """
        # Standard headers
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Add user agent
        headers['User-Agent'] = self._get_random_user_agent()
        
        return headers
    
    def cleanup_user_resources(self, user_id):
        """
        Clean up all resources for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            bool: True if cleanup was successful
        """
        # Release IPs
        ip_success = self.ip_manager.release_ip_for_user(user_id)
        
        # Clear browser session
        session_success = self.session_manager.clear_user_session(user_id)
        
        logger.info(f"Cleaned up resources for user {user_id}: IP={ip_success}, Session={session_success}")
        
        return ip_success and session_success
    
    def rotate_user_identity(self, user_id):
        """
        Rotate a user's entire digital identity (IP and browser session).
        
        Args:
            user_id (str): The user ID
            
        Returns:
            dict: New browser configuration
        """
        # Rotate IP
        self.ip_manager.rotate_ip_for_user(user_id)
        
        # Rotate browser session
        self.session_manager.rotate_user_session(user_id)
        
        # Get new configuration
        return self.get_isolated_browser_config(user_id)
    
    def handle_detection_risk(self, user_id, risk_level, context=None):
        """
        Handle a detection risk for a user.
        
        Args:
            user_id (str): The user ID
            risk_level (str): Risk level (low, medium, high)
            context (dict, optional): Risk context information
            
        Returns:
            dict: Action taken and new configuration if applicable
        """
        # Get IP from context if available
        ip_id = None
        if context and 'ip_id' in context:
            ip_id = context['ip_id']
        elif context and 'ip_data' in context and '_id' in context['ip_data']:
            ip_id = str(context['ip_data']['_id'])
        
        # Handle based on risk level
        if risk_level == 'low':
            # For low risk, just log the incident
            logger.warning(f"Low detection risk for user {user_id}: {context}")
            
            return {
                'action': 'none',
                'message': 'Logged risk incident'
            }
            
        elif risk_level == 'medium':
            # For medium risk, rotate the browser session but keep the IP
            logger.warning(f"Medium detection risk for user {user_id}: {context}")
            
            # Rotate browser session
            new_session = self.session_manager.rotate_user_session(user_id)
            
            # Report IP issue if available
            if ip_id:
                self.ip_manager.report_ip_failure(ip_id, 'detection_risk', 
                                               f"Medium detection risk: {context}")
            
            return {
                'action': 'session_rotation',
                'message': 'Rotated browser session',
                'new_session': new_session
            }
            
        elif risk_level == 'high':
            # For high risk, rotate everything
            logger.error(f"High detection risk for user {user_id}: {context}")
            
            # If we have IP info, report it as potentially banned
            if ip_id:
                self.ip_manager.report_ip_ban(ip_id, f"High detection risk: {context}")
            
            # Rotate identity
            new_config = self.rotate_user_identity(user_id)
            
            return {
                'action': 'full_rotation',
                'message': 'Rotated entire digital identity',
                'new_config': new_config
            }
        
        # Unknown risk level
        logger.error(f"Unknown detection risk level '{risk_level}' for user {user_id}")
        
        return {
            'action': 'error',
            'message': f"Unknown risk level: {risk_level}"
        }