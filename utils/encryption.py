"""
Encryption utilities for sensitive data.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # Generate a key if not provided
    # In production, this should be set in environment variables
    key = Fernet.generate_key()
    ENCRYPTION_KEY = base64.urlsafe_b64encode(key).decode('utf-8')
    print(f"WARNING: Generated temporary encryption key: {ENCRYPTION_KEY}")
    print("Add this to your .env file as ENCRYPTION_KEY")
else:
    # Ensure the key is properly formatted
    try:
        key = base64.urlsafe_b64decode(ENCRYPTION_KEY)
    except Exception:
        # If the key is not base64 encoded, derive a key from it
        salt = os.getenv('ENCRYPTION_SALT', b'travian_whispers_salt').encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))

# Initialize Fernet cipher
cipher = Fernet(key)

def encrypt_data(data):
    """
    Encrypt sensitive data.
    
    Args:
        data (str): Data to encrypt
        
    Returns:
        str: Encrypted data in base64 format
    """
    if not data:
        return None
    
    encrypted_data = cipher.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

def decrypt_data(encrypted_data):
    """
    Decrypt encrypted data.
    
    Args:
        encrypted_data (str): Encrypted data in base64 format
        
    Returns:
        str: Decrypted data
    """
    if not encrypted_data:
        return None
    
    try:
        data = base64.urlsafe_b64decode(encrypted_data)
        decrypted_data = cipher.decrypt(data)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        print(f"Error decrypting data: {e}")
        return None