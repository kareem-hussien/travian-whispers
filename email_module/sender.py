# email_module/sender.py
"""
Simplified email sender module that only logs messages (no actual sending).
"""
import logging

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email_sender')

def send_email(to_email, subject, html_content, text_content=None):
    """
    Mock function that logs email details instead of sending.
    """
    logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
    return True

def send_verification_email(to_email, username, verification_url):
    """
    Mock function for verification email.
    """
    logger.info(f"[MOCK VERIFICATION] To: {to_email}, Username: {username}, URL: {verification_url}")
    return True

def send_password_reset_email(to_email, username, reset_url):
    """
    Mock function for password reset email.
    """
    logger.info(f"[MOCK PASSWORD RESET] To: {to_email}, Username: {username}, URL: {reset_url}")
    return True

def send_subscription_confirmation_email(to_email, username, plan_name, end_date, amount, payment_id):
    """
    Mock function for subscription confirmation email.
    """
    logger.info(f"[MOCK SUBSCRIPTION] To: {to_email}, Username: {username}, Plan: {plan_name}")
    return True

def send_welcome_email(to_email, username):
    """
    Mock function for welcome email.
    """
    logger.info(f"[MOCK WELCOME] To: {to_email}, Username: {username}")
    return True