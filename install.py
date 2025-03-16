#!/usr/bin/env python3
"""
Complete installation script for Travian Whispers.
This script:
1. Creates all necessary directories
2. Creates __init__.py files
3. Downloads all required Python modules
4. Sets up configuration files
5. Checks for dependencies
"""
import os
import sys
import shutil
import platform
import subprocess
import tempfile
import zipfile
import io
import argparse
from pathlib import Path
from urllib import request

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80)

def print_step(message):
    """Print a step message."""
    print(f"\n➡️  {message}")

def print_success(message):
    """Print a success message."""
    print(f"✅  {message}")

def print_warning(message):
    """Print a warning message."""
    print(f"⚠️  {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌  {message}")

def is_venv():
    """Check if running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def create_virtual_environment():
    """Create a virtual environment if not already in one."""
    if is_venv():
        print_success("Already running in a virtual environment.")
        return True
    
    print_step("Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        
        # Determine activate script path
        if platform.system() == "Windows":
            activate_script = os.path.join("venv", "Scripts", "activate")
            activate_cmd = f"{activate_script}.bat"
        else:
            activate_script = os.path.join("venv", "bin", "activate")
            activate_cmd = f"source {activate_script}"
        
        print_success(f"Virtual environment created successfully.")
        print_warning(f"You need to activate it with: {activate_cmd}")
        print_warning("Please restart the installation script after activating the virtual environment.")
        return False
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def create_directory_structure():
    """Create all necessary directories."""
    print_step("Creating directory structure...")
    
    directories = [
        # Database
        "database",
        "database/models",
        
        # Authentication
        "auth",
        
        # Email
        "email",
        "email/templates",
        
        # Payment
        "payment",
        
        # Web application
        "web",
        "web/routes",
        "web/static",
        "web/static/css",
        "web/static/js",
        "web/static/img",
        "web/templates",
        "web/templates/auth",
        "web/templates/admin",
        "web/templates/user",
        "web/templates/payment",
        "web/templates/errors",
        
        # Bot functionality
        "startup",
        "tasks",
        "tasks/trainer",
        
        # Game information
        "info",
        "info/maps",
        "info/profile",
        
        # Backup and logs
        "backups",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  Created directory: {directory}")
    
    print_success("Directory structure created successfully")

def create_init_files():
    """Create __init__.py files in all directories."""
    print_step("Creating __init__.py files...")
    
    # Find all directories
    dirs_with_init = []
    for root, dirs, files in os.walk('.'):
        if '/venv/' in root or './.git' in root or './backups' in root or './logs' in root:
            continue
            
        for d in dirs:
            if d.startswith('.') or d == 'venv' or d == '__pycache__':
                continue
                
            dir_path = os.path.join(root, d)
            if os.path.isdir(dir_path):
                init_file = os.path.join(dir_path, '__init__.py')
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        f.write('"""Package initialization."""\n')
                    dirs_with_init.append(dir_path)
    
    print_success(f"Created {len(dirs_with_init)} __init__.py files")

def install_requirements():
    """Install required Python packages."""
    print_step("Installing required packages...")
    
    requirements = [
        # Browser automation
        "selenium==4.16.0",
        "webdriver-manager==4.0.1",
        
        # Web application
        "flask==2.3.3",
        "flask-cors==4.0.0",
        "gunicorn==21.2.0",
        
        # Database
        "pymongo==4.6.1",
        "dnspython==2.4.2",
        
        # Authentication and security
        "bcrypt==4.1.2",
        "pyjwt==2.8.0",
        "email-validator==2.1.0.post1",
        "cryptography==41.0.7",
        
        # Payment processing
        "requests==2.31.0",
        
        # Utilities
        "python-dotenv==1.0.0",
        "schedule==1.2.1",
    ]
    
    # Write requirements.txt
    with open("requirements.txt", "w") as f:
        for req in requirements:
            f.write(f"{req}\n")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print_success("Required packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install packages: {e}")
        return False

def create_env_file():
    """Create .env file with configuration."""
    print_step("Creating .env configuration file...")
    
    if os.path.exists(".env"):
        print_warning(".env file already exists. Skipping.")
        return True
    
    env_content = """# Application settings
SECRET_KEY=inweb
FLASK_ENV=development

# MongoDB settings
MONGODB_URI=mongodb+srv://whispers:eZAafCQTrjKKcZua@cluster0.9josw.mongodb.net/whispers

# Email settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=traviahub.com@gmail.com
SMTP_PASSWORD=Ka19835251!@#$%
EMAIL_FROM=Travian Hub <traviahub.com@gmail.com>

# PayPal settings
PAYPAL_CLIENT_ID=AXHCLWcZ_sDcEI2dmoiznLOkosiMpGrAFezn4jR2jr7Hx89vzXgAJBOvVVr6z3yMk_7agGMk9nHvA-C9
PAYPAL_SECRET=EFobbN4yuKjRuuENC6O9nRD2MGnwBs2LJfKCMIoMIQNRTQQANji6gGvoO_twZ-TAMDeDZbZAO4a4r20n
PAYPAL_MODE=sandbox
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print_success(".env configuration file created successfully")
    return True

def download_required_files():
    """Download required files from the repository."""
    print_step("Downloading required files...")
    
    # Define GitHub raw URLs for each file
    files_to_download = {
        # Setup scripts
        "setup.py": "https://raw.githubusercontent.com/your-repo/travian-whispers/main/setup.py",
        "check_imports.py": "https://raw.githubusercontent.com/your-repo/travian-whispers/main/check_imports.py",
        
        # Core files
        "main.py": "https://raw.githubusercontent.com/your-repo/travian-whispers/main/main.py",
        "signal_handler.py": "https://raw.githubusercontent.com/your-repo/travian-whispers/main/signal_handler.py",
        "cron_jobs.py": "https://raw.githubusercontent.com/your-repo/travian-whispers/main/cron_jobs.py",
        
        # Database files 
        "database/mongodb.py": "https://raw.githubusercontent.com/your-repo/travian-whispers/main/database/mongodb.py",
        "database/error_handler.py": "https://raw.githubusercontent.com/your-repo/travian-whispers/main/database/error_handler.py",
    }
    
    # Since we don't have actual URLs, we'll just create placeholder files instead
    print_warning("GitHub repository URLs not available. Creating placeholder files instead.")
    
    for file_path, _ in files_to_download.items():
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        
        # Skip if file already exists
        if os.path.exists(file_path):
            print(f"  File already exists: {file_path}")
            continue
        
        # Create a placeholder
        with open(file_path, "w") as f:
            f.write(f'"""\nPlaceholder for {file_path}\nReplace with actual implementation.\n"""\n')
        
        print(f"  Created placeholder: {file_path}")
    
    print_success("Created placeholder files for all required components")
    return True

def init_database_models():
    """Initialize database models if not present."""
    print_step("Initializing database models...")
    
    model_files = [
        ("database/models/user.py", "User model for MongoDB integration"),
        ("database/models/subscription.py", "Subscription plan model for MongoDB integration"),
        ("database/models/transaction.py", "Transaction model for MongoDB integration"),
    ]
    
    for file_path, description in model_files:
        if os.path.exists(file_path):
            print(f"  File already exists: {file_path}")
            continue
        
        with open(file_path, "w") as f:
            f.write(f'"""\n{description}.\nReplace with actual implementation.\n"""\n\n')
            f.write('class ModelNotImplementedError(Exception):\n