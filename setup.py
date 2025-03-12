#!/usr/bin/env python3
"""
Initial setup script for Travian Whispers.
This script creates the necessary directories and basic configuration files.
"""
import os
import sys
import shutil
import subprocess
import platform

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)

def print_step(message):
    """Print a step message."""
    print(f"\n➡️  {message}")

def print_success(message):
    """Print a success message."""
    print(f"✅  {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌  {message}")

def create_directories():
    """Create necessary directories."""
    print_step("Creating directory structure...")
    
    directories = [
        "database",
        "database/models",
        "auth",
        "email",
        "email/templates",
        "payment",
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
        "startup",
        "tasks",
        "tasks/trainer",
        "info",
        "info/maps",
        "info/profile",
        "backups"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  Created directory: {directory}")
    
    print_success("Directory structure created successfully")

def create_init_files():
    """Create __init__.py files in Python packages."""
    print_step("Creating __init__.py files...")
    
    # Find all directories
    all_dirs = []
    for root, dirs, files in os.walk("."):
        if root == "." or root.startswith("./.") or "/venv/" in root:
            continue
        
        for dir_name in dirs:
            if dir_name.startswith(".") or dir_name == "venv":
                continue
            
            dir_path = os.path.join(root, dir_name)
            if os.path.isdir(dir_path) and not dir_path.startswith("./."):
                all_dirs.append(dir_path)
    
    # Create __init__.py files
    count = 0
    for directory in all_dirs:
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write('"""Package initialization."""\n')
            print(f"  Created: {init_file}")
            count += 1
    
    print_success(f"Created {count} __init__.py files")

def check_venv():
    """Check if running in a virtual environment."""
    print_step("Checking virtual environment...")
    
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print_success("Running in a virtual environment")
        return True
    else:
        print_error("Not running in a virtual environment")
        print("  Please create and activate a virtual environment using:")
        print("  python3 -m venv venv")
        if platform.system() == "Windows":
            print("  .\\venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        return False

def install_requirements():
    """Install required packages."""
    print_step("Installing required packages...")
    
    try:
        # Create requirements.txt if it doesn't exist
        if not os.path.exists("requirements.txt"):
            with open("requirements.txt", "w") as f:
                f.write("""# Browser automation
selenium==4.16.0
webdriver-manager==4.0.1

# Web application
flask==2.3.3
flask-cors==4.0.0
gunicorn==21.2.0

# Database
pymongo==4.6.1
dnspython==2.4.2

# Authentication and security
bcrypt==4.1.2
pyjwt==2.8.0
email-validator==2.1.0.post1
cryptography==41.0.7

# Payment processing
requests==2.31.0

# Utilities
python-dotenv==1.0.0
schedule==1.2.1
""")
        
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print_success("Required packages installed successfully")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install packages: {e}")
        return False
    
    return True

def create_env_file():
    """Create .env file for environment variables."""
    print_step("Creating .env file...")
    
    if os.path.exists(".env"):
        print("  .env file already exists. Skipping...")
        return
    
    with open(".env", "w") as f:
        f.write("""# Application settings
SECRET_KEY=change-this-in-production
FLASK_ENV=development

# MongoDB settings
MONGODB_URI=mongodb+srv://whispers:eZAafCQTrjKKcZua@cluster0.9josw.mongodb.net/whispers

# Email settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=Travian Whispers <your-email@gmail.com>

# PayPal settings
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_SECRET=your-paypal-secret
PAYPAL_MODE=sandbox
""")
    
    print_success(".env file created successfully")

def main():
    """Main function."""
    print_header("Travian Whispers - Initial Setup")
    
    # Check if running in a virtual environment
    if not check_venv() and input("Continue anyway? (y/n): ").lower() != "y":
        print("Setup aborted.")
        return
    
    # Create directory structure
    create_directories()
    
    # Create __init__.py files
    create_init_files()
    
    # Install required packages
    if not install_requirements() and input("Continue anyway? (y/n): ").lower() != "y":
        print("Setup aborted.")
        return
    
    # Create .env file
    create_env_file()
    
    print_header("Setup completed successfully!")
    print("\nTo run the application, use one of the following commands:")
    print("  - Web mode: python main.py --web")
    print("  - Bot mode: python main.py --user-id <user_id>")
    print("\nAdditional configuration may be required. See README.md for details.")

if __name__ == "__main__":
    main()
