"""
Configuration module for Travian Whispers.
Loads settings from environment variables with secure defaults.
"""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Application settings
APP_ENV = os.getenv("FLASK_ENV", "development")
DEBUG = APP_ENV == "development"
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

# Database settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/whispers")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "whispers")

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "24"))  # hours

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Travian Whispers <noreply@travianwhispers.com>")

# PayPal settings
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"