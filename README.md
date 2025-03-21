# Travian Whispers - Advanced Travian Automation Suite

**Author:** Eng. Kareem Hussien  
**Contact:** [WhatsApp](https://wa.me/00201099339393)

## Overview
Travian Whispers is a comprehensive automation suite for the browser-based game Travian. Built with Python, Selenium, and MongoDB, it features both a powerful bot for game automation and a sleek web interface for user management, subscription plans, and secure payment processing.

![Travian Whispers Dashboard](web/static/img/dashboard-preview.png)

## Core Features

### Game Automation
✅ **Automated Login** - Securely log into Travian with stored credentials  
✅ **Village Management** - Extract and store village data  
✅ **Auto-Farming** - Send farm lists at regular intervals  
✅ **Troop Training** - Automate training based on your tribe  
✅ **Multi-Tasking** - Run multiple automation processes simultaneously  

### Web Platform
✅ **User Authentication** - Secure registration and login system  
✅ **Subscription Plans** - Tiered plans with different feature sets  
✅ **User Dashboard** - Monitor your automation tasks and villages  
✅ **Admin Controls** - Manage users, plans, and view analytics  
✅ **Payment Processing** - PayPal integration for subscriptions  

### System Features
✅ **Error Handling** - Comprehensive error detection and recovery  
✅ **Database Integration** - MongoDB for secure data storage  
✅ **Cron Jobs** - Scheduled tasks for maintenance  
✅ **Responsive Design** - Works on desktop and mobile devices  
✅ **API Endpoints** - For advanced integrations  
✅ **Docker Support** - Containerized deployment for easy setup  

---

## Getting Started

### Option 1: Docker Setup (Recommended)

The easiest way to run Travian Whispers is using Docker and Docker Compose.

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

#### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/travian-whispers.git
   cd travian-whispers
   ```

2. Create the required `http_utils.py` module:
   ```bash
   # Download the setup script
   curl -O https://raw.githubusercontent.com/yourusername/travian-whispers/main/fix-http-utils.sh
   
   # Make it executable and run it
   chmod +x fix-http-utils.sh
   ./fix-http-utils.sh
   ```

3. Start the application with Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the web interface at http://localhost:5000
   Access the MongoDB admin interface at http://localhost:8081

For more detailed Docker instructions, see [DOCKER.md](DOCKER.md).

### Option 2: Traditional Setup

#### Prerequisites
- Python 3.8+ (Python 3.10 recommended)
- Chrome/Chromium browser
- MongoDB database
- PayPal developer account (for payment processing)

#### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/travian-whispers.git
cd travian-whispers

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create the required http_utils module
./fix-http-utils.sh

# Set up configuration
cp .env.example .env
# Edit .env with your settings
```

#### Development Helpers
```bash
# Run setup procedure to create directories
python main.py --setup

# Check Python imports
python main.py --check-imports

# Enable debug logging
python main.py --debug
```

---

## Running the Application

The application can run in two modes:

### Web Application Mode
```bash
python main.py --web
```
This will start the Flask web server on http://localhost:5000

### Bot Mode (for a specific user)
```bash
python main.py --user-id <user_id>
```
This will run the automation bot for the specified user.

---

## Troubleshooting

### Common Issues

#### Docker Startup Issues
If you encounter "services.networks must be a mapping" or similar YAML errors:
```bash
# Create a backup of your current file
mv docker-compose.yml docker-compose.yml.bak

# Create a new clean file
nano docker-compose.yml
# Paste the example from DOCKER.md, save and exit

# Restart containers
docker-compose down
docker-compose up -d
```

#### MongoDB CPU Compatibility Issue
If MongoDB fails with an error about AVX support, modify your docker-compose.yml file to use MongoDB 4.4 instead of 5.0:
```yaml
mongodb:
  image: mongo:4.4
  # rest of configuration...
```

#### Missing HTTP Utils Module
If you see a "ModuleNotFoundError: No module named 'http_utils'" error:
```bash
# Run the fix script
./fix-http-utils.sh

# Restart the containers
docker-compose down
docker-compose up -d
```

#### Flask Template Errors
If you see errors related to templates like "jinja2.exceptions.UndefinedError" or "AttributeError: 'NoneType' object has no attribute 'split'":

```bash
# Connect to the web container
docker exec -it travian-tools-web bash

# Create base.html template if it doesn't exist
mkdir -p /app/web/templates
touch /app/web/templates/base.html
cat > /app/web/templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Travian Whispers{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block styles %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
EOF

# Fix context processor to ensure current_user is available
cat > /app/web/utils/context_processors.py << 'EOF'
"""
Context processors for Travian Whispers web application.
"""
import logging
from flask import session
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)

def inject_user():
    """Inject user data into templates."""
    user_data = {
        'is_authenticated': False,
        'is_admin': False,
        'username': None,
        'email': None
    }
    
    if 'user_id' in session:
        user_data['is_authenticated'] = True
        user_data['username'] = session.get('username')
        user_data['email'] = session.get('email')
        user_data['is_admin'] = session.get('role') == 'admin'
    
    return {
        'user_data': user_data,
        'current_user': user_data
    }

def inject_helpers():
    """Inject helper functions into templates."""
    return {
        'current_year': datetime.now().year
    }

def register_context_processors(app):
    app.context_processor(inject_user)
    app.context_processor(inject_helpers)
    logger.info("Context processors registered")
EOF

# Exit and restart the container
exit
docker-compose restart web
```

#### Bot Mode User ID Error
If the bot service fails with a "MongoDB user ID for bot mode" error, try temporarily configuring it to run in web mode:
```yaml
# In docker-compose.yml
bot:
  build: .
  command: python main.py --web  # Change this line
  # rest of configuration...
```

---

## Project Structure

```
travian-whispers/
├── main.py                  # Main entry point
├── signal_handler.py        # Graceful shutdown
├── cron_jobs.py             # Scheduled tasks
├── http_utils.py            # HTTP utilities
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Multi-container setup
│
├── database/                # Database integration
│   ├── mongodb.py           # MongoDB connection
│   ├── error_handler.py     # Error handling
│   └── models/              # Data models
│
├── auth/                    # Authentication
│   ├── registration.py      # User registration
│   ├── login.py             # Login & JWT
│   ├── verification.py      # Email verification
│   └── password_reset.py    # Password recovery
│
├── email_module/            # Email system
│   ├── sender.py            # Email sending
│   └── templates/           # Email templates
│
├── payment/                 # Payment processing
│   ├── paypal.py            # PayPal integration
│   └── http_utils.py        # HTTP utilities for payment
│
├── web/                     # Web application
│   ├── app.py               # Flask application
│   ├── static/              # Static assets
│   └── templates/           # HTML templates
│   └── routes/
│       ├── __init__.py
│       ├── auth.py
│       ├── user.py
│       ├── admin.py
|       ├── public.py
├── startup/                 # Bot initialization
│   ├── browser_profile.py   # Browser setup
│   └── tasks.py             # Task management
│
├── tasks/                   # Bot automation
│   ├── auto_farm.py         # Auto-farming
│   └── trainer/             # Troop training
│
├── info/                    # Game information
│   └── maps/                # Game data
│
├── logs/                    # Application logs
└── backups/                 # Database backups
```

---

## Special Considerations

### Database Models
When working with MongoDB models, always use explicit `is None` checks instead of implicit boolean tests:

```python
# CORRECT: Explicit None check
if self.db is not None:
    self.collection = self.db["collectionName"]
    
# INCORRECT: Will raise NotImplementedError
if self.db:  # Don't do this with PyMongo objects
    self.collection = self.db["collectionName"]
```

### Jinja Templates
All templates should follow proper template inheritance patterns:

```html
{% extends "base.html" %}

{% block content %}
   <!-- Your content here -->
{% endblock %}
```

Make sure the base.html template exists and defines all necessary blocks.

---

## Features in Detail

### Authentication System
The authentication system provides secure registration, login, and account management:
- **Registration** with email verification
- **Login** with session management using JWT tokens
- **Password Reset** functionality
- **Role-based access** (admin/user)

### User Dashboard
The user dashboard provides a comprehensive view of the automation status:
- **Overview** of subscription and village usage
- **Task management** for starting/stopping automation
- **Village management** for monitoring village status
- **Activity logs** for tracking automation history

### Admin Panel
The admin panel allows administrators to manage the entire system:
- **User management** for viewing and managing users
- **Subscription management** for creating and editing plans
- **Transaction history** for tracking payments
- **System statistics** for monitoring usage

### Subscription System
The subscription system offers tiered plans with different features:
- **Basic Plan** ($4.99/month) - Auto-Farm and 2 villages
- **Standard Plan** ($9.99/month) - Auto-Farm, Trainer, and 5 villages
- **Premium Plan** ($19.99/month) - All features and 15 villages

---

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is proprietary software. Unauthorized copying, distribution, or use is prohibited.

## Support
For assistance or feature requests, contact me via [WhatsApp](https://wa.me/00201099339393).

---

**© 2025 Eng. Kareem Hussien - Travian Whispers Automation Suite**
