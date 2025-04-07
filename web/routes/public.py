"""
Public routes for Travian Whispers web application.
This module defines the blueprint for public-facing routes.
"""
import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database.models.subscription import SubscriptionPlan

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """Landing page route."""
    try:
        # Get subscription plans for pricing section
        plan_model = SubscriptionPlan()
        plans = plan_model.list_plans()
        
        # Check if base template exists
        base_template_exists = os.path.exists(os.path.join(current_app.template_folder, 'base.html'))
        
        # Render index template
        return render_template('index.html', 
                             plans=plans, 
                             title='Home', 
                             base_template_exists=base_template_exists)
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        # Render a simple fallback page if there's an error
        return render_template('errors/500.html')


@public_bp.route('/about')
def about():
    """About page route."""
    return render_template('about.html', title='About')


@public_bp.route('/features')
def features():
    """Features page route."""
    return render_template('features.html', title='Features')


@public_bp.route('/pricing')
def pricing():
    """Pricing page route."""
    # Get subscription plans
    plan_model = SubscriptionPlan()
    plans = plan_model.list_plans()
    
    # Render pricing template
    return render_template('pricing.html', plans=plans, title='Pricing')


@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page route."""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        subject = request.form.get('subject', '')
        message = request.form.get('message', '')
        
        # Validate form data
        if not name or not email or not subject or not message:
            flash('All fields are required', 'danger')
            return render_template(
                'contact.html',
                name=name, 
                email=email, 
                subject=subject, 
                message=message,
                title='Contact'
            )
        
        # Send email (implementation would go here)
        try:
            # Log contact form submission
            logger.info(f"Contact form submitted by {name} ({email}): {subject}")
            
            # In production, this would send an email
            # send_contact_email(name, email, subject, message)
            
            # Flash success message
            flash('Your message has been sent! We will get back to you soon.', 'success')
            
            # Redirect to contact page
            return redirect(url_for('public.contact'))
        except Exception as e:
            # Flash error message
            flash(f"Failed to send message: {str(e)}", 'danger')
            logger.error(f"Error sending contact email: {str(e)}")
    
    # Render contact template
    return render_template('contact.html', title='Contact')


@public_bp.route('/faq')
def faq():
    """FAQ page route."""
    return render_template('faq.html', title='FAQ')


@public_bp.route('/terms')
def terms():
    """Terms and Conditions page route."""
    return render_template('terms.html', title='Terms and Conditions')


@public_bp.route('/privacy')
def privacy():
    """Privacy Policy page route."""
    return render_template('privacy.html', title='Privacy Policy')

@public_bp.route('/goodbye')
def goodbye():
    """Goodbye page after account deletion."""
    return render_template('goodbye.html', title='Account Deleted')