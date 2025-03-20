"""
Support routes for user dashboard.
This module defines the routes for help and support.
"""
import logging
from flask import render_template, redirect, url_for, flash, session, current_app
from web.utils.decorators import login_required
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/support')
    @login_required
    def support():
        """Help and support route."""
        # Get user data
        user_model = User()
        user = user_model.get_user_by_id(session['user_id'])
        
        if not user:
            # Flash error message
            flash('User not found', 'danger')
            
            # Clear session and redirect to login
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Get support articles from config (if available)
        support_articles = current_app.config.get('SUPPORT_ARTICLES', [])
        
        # Get FAQ entries from database (if available)
        try:
            from database.models.faq import FAQ
            faq_model = FAQ()
            faq_entries = faq_model.list_faq_entries()
        except (ImportError, AttributeError):
            # Fall back to empty list if model doesn't exist
            faq_entries = []
        
        # Render support template
        return render_template(
            'user/support.html', 
            current_user=user,
            support_articles=support_articles,
            faq_entries=faq_entries,
            title='Help & Support'
        )