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

---

## Getting Started

### Prerequisites
- Python 3.8+ (Python 3.10 recommended)
- Chrome/Chromium browser
- MongoDB database
- PayPal developer account (for payment processing)

### Installation

```bash
# Clone the repository
git clone https://github.com/username/travian-whispers.git
cd travian-whispers

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp .env.example .env
# Edit .env with your settings
```

### Configuration
The application uses environment variables for configuration. Copy the `.env.example` file to `.env` and update the values:

```
# Application settings
SECRET_KEY=your-secret-key
FLASK_ENV=development

# MongoDB settings
MONGODB_URI=mongodb+srv://whispers:eZAafCQTrjKKcZua@cluster0.9josw.mongodb.net/whispers

# Email settings (optional during development)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# PayPal settings (optional during development)
PAYPAL_CLIENT_ID=your-client-id
PAYPAL_SECRET=your-secret
```

### Running the Application

The application can run in two modes:

#### Web Application Mode
```bash
python main.py --web
```
This will start the Flask web server on http://localhost:5000

#### Bot Mode (for a specific user)
```bash
python main.py --user-id <user_id>
```
This will run the automation bot for the specified user.

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

## Project Structure

```
travian-whispers/
├── main.py                  # Main entry point
├── signal_handler.py        # Graceful shutdown
├── cron_jobs.py             # Scheduled tasks
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
│   └── paypal.py            # PayPal integration
│
├── web/                     # Web application
│   ├── app.py               # Flask application
│   ├── static/              # Static assets
│   │   ├── css/             # Stylesheets
│   │   ├── js/              # JavaScript
│   │   └── img/             # Images
│   └── templates/           # HTML templates
│       ├── auth/            # Authentication
│       ├── admin/           # Admin panel
│       ├── user/            # User dashboard
│       └── errors/          # Error pages
│
├── startup/                 # Bot initialization
│   ├── welcome_messages.py  # Welcome screen
│   ├── browser_profile.py   # Browser setup
│   ├── villages_list.py     # Village data
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

## Features in Detail

### Authentication System
The authentication system provides secure registration, login, and account management:
- **Registration** with email verification (optional during development)
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

### Bot Automation
The automation bot provides powerful features for Travian gameplay:
- **Auto-Farming** for resource collection
- **Troop Training** for army building
- **Multi-tasking** for running multiple automations
- **Error recovery** for handling game interruptions

---

## Development Notes

### Current Status
The project is currently in active development with the following components completed:
- ✅ Core bot functionality
- ✅ Database integration
- ✅ Authentication system
- ✅ User dashboard UI
- ✅ Error handling system
- ⏳ Payment processing (partially implemented)
- ⏳ Email notifications (temporarily disabled)

### Known Issues
- The email system is currently disabled for development
- Some links in the dashboard are placeholders
- The PayPal integration needs proper configuration

### Next Steps
1. Complete the payment processing integration
2. Finalize the admin dashboard functionality
3. Implement email notifications
4. Add more robust error handling for the bot

---

## Running in Production

For production deployment, the following additional steps are recommended:

1. **Use HTTPS** with a proper SSL certificate
2. **Set up a reverse proxy** (Nginx, Apache) in front of the Flask app
3. **Use Gunicorn** as the WSGI server
4. **Configure proper logging** to a file or log management service
5. **Set up monitoring** for the application and database

Example Gunicorn command:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 "web.app:app"
```

Example Nginx configuration snippet:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is proprietary software. Unauthorized copying, distribution, or use is prohibited.

## Support
For assistance or feature requests, contact me via [WhatsApp](https://wa.me/00201099339393).

---

**© 2025 Eng. Kareem Hussien - Travian Whispers Automation Suite**
