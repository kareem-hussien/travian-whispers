"""
Email sender module for Travian Whispers.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email_sender')

def send_email(to_email, subject, html_content, text_content=None):
    """
    Send an email using configured SMTP server.
    If SMTP credentials are not configured, logs the email instead.
    
    Args:
        to_email (str): Recipient email
        subject (str): Email subject
        html_content (str): HTML content
        text_content (str, optional): Plain text content
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    # If SMTP not configured, log instead of sending
    if not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
        logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
        return True
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config.EMAIL_FROM
        msg['To'] = to_email
        
        # Add plain text version if provided, otherwise create from HTML
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        
        # Add HTML version
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

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