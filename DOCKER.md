# Docker Setup for Travian Whispers

This document provides instructions for setting up and running Travian Whispers using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/travian-whispers.git
   cd travian-whispers
   ```

2. Create the required HTTP utils module:
   ```bash
   # Download and run the fix script
   chmod +x fix-http-utils.sh
   ./fix-http-utils.sh
   ```

3. Create a clean docker-compose.yml file:
   ```bash
   nano docker-compose.yml
   ```
   
   Paste the following content:
   ```yaml
   services:
     mongodb:
       image: mongo:4.4
       volumes:
         - mongodb_data:/data/db
       ports:
         - "27017:27017"
       environment:
         - MONGO_INITDB_DATABASE=whispers
       networks:
         - travian-network
       restart: always
   
     mongo-express:
       image: mongo-express
       ports:
         - "8081:8081"
       environment:
         - ME_CONFIG_MONGODB_SERVER=mongodb
       depends_on:
         - mongodb
       networks:
         - travian-network
       restart: always
   
     web:
       build: .
       command: gunicorn --bind 0.0.0.0:5000 "web.app:create_app()"
       volumes:
         - ./:/app
         - logs:/app/logs
         - backups:/app/backups
       ports:
         - "5000:5000"
       environment:
         - FLASK_ENV=production
         - MONGODB_URI=mongodb://mongodb:27017/whispers
         - MONGODB_DB_NAME=whispers
         - SECRET_KEY=defaultsecretkey
         - JWT_SECRET=defaultjwtsecret
       depends_on:
         - mongodb
       networks:
         - travian-network
       restart: always
   
     # Bot service (optional, can enable after web service is working)
     bot:
       build: .
       command: python main.py --web
       volumes:
         - ./:/app
         - logs:/app/logs
         - backups:/app/backups
         - ./info:/app/info
       environment:
         - MONGODB_URI=mongodb://mongodb:27017/whispers
         - MONGODB_DB_NAME=whispers
         - HEADLESS=true
         - SECRET_KEY=defaultsecretkey
         - JWT_SECRET=defaultjwtsecret
       depends_on:
         - mongodb
       networks:
         - travian-network
       restart: always
   
   volumes:
     mongodb_data:
     logs:
     backups:
   
   networks:
     travian-network:
       driver: bridge
   ```

4. Create essential template files before starting:
   ```bash
   # Create directories if they don't exist
   mkdir -p web/templates
   
   # Create a base template file
   cat > web/templates/base.html << 'EOF'
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
   ```

5. Start the application:
   ```bash
   docker-compose up -d
   ```

6. Access the web interface at http://localhost:5000

## Docker Components

The Docker setup consists of the following services:

- **mongodb**: MongoDB 4.4 database (compatible with older CPUs without AVX support)
- **mongo-express**: Web interface for MongoDB administration
- **web**: The Flask web application
- **bot**: The Travian automation bot (can be enabled or disabled as needed)

## Common Issues and Fixes

### 1. Template Errors (500 Internal Server Error)

If you see errors related to Jinja templates:

```bash
# Connect to the web container
docker exec -it travian-whispers-web-1 bash

# Create a proper base.html template
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

# Fix context processor to provide current_user variable
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

# Exit the container
exit

# Restart the web container
docker-compose restart web
```

### 2. MongoDB 'truth value' Error

If you encounter a NotImplementedError with a message about "Database objects do not implement truth value testing":

```bash
# Connect to the web container
docker exec -it travian-whispers-web-1 bash

# Navigate to the models directory
cd /app/database/models/

# Fix subscription.py by adding explicit None checks
sed -i 's/self.collection = self.db\["subscriptionPlans"\] if self.db else None/self.collection = None\n        if self.db is not None:\n            self.collection = self.db\["subscriptionPlans"\]/' subscription.py

# Repeat for other model files that might have similar issues
sed -i 's/self.collection = self.db\["users"\] if self.db else None/self.collection = None\n        if self.db is not None:\n            self.collection = self.db\["users"\]/' user.py
sed -i 's/self.collection = self.db\["transactions"\] if self.db else None/self.collection = None\n        if self.db is not None:\n            self.collection = self.db\["transactions"\]/' transaction.py

# Exit the container
exit

# Restart the web container
docker-compose restart web
```

### 3. 404 Error with URL for 'index'

If you see errors about being unable to build a URL for endpoint 'index':

```bash
# Connect to the web container
docker exec -it travian-whispers-web-1 bash

# Navigate to the templates directory
cd /app/web/templates/errors/

# Fix 404.html
sed -i 's|url_for("index")|url_for("public.index")|g' 404.html

# Fix 500.html
sed -i 's|url_for("index")|url_for("public.index")|g' 500.html

# Exit the container
exit

# Restart the web container
docker-compose restart web
```

### 4. YAML Parsing Errors

If you encounter errors like "services.networks must be a mapping" or "services.volumes must be a mapping":

- Use the exact format shown in the Quick Start section
- Avoid copying from PDF or websites that might add invisible characters
- Type the configuration manually if needed

### 5. Container Permission Issues

If you encounter permission errors when trying to stop containers:

```bash
# First try to stop the Docker service
sudo systemctl stop docker

# If that doesn't work, try a more aggressive approach
sudo killall -9 docker
sudo killall -9 containerd

# Then restart Docker
sudo systemctl start docker

# And start the containers again
docker-compose up -d
```

### 6. Missing HTTP Utils Module

The `http_utils.py` module is required for the payment system. If it's missing, run:

```bash
./fix-http-utils.sh
```

## Managing Containers

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
```

### Stop Containers

```bash
docker-compose down
```

### Restart Containers

```bash
docker-compose restart
```

### Check Container Status

```bash
docker ps -a
```

### Access Container Shell

```bash
docker exec -it travian-whispers-web-1 bash
```

## Database Management

### Access MongoDB Shell

```bash
docker exec -it travian-whispers-mongodb-1 mongo
```

### MongoDB Web Interface

Access MongoDB Express at http://localhost:8081

## Updating the Application

To update the application:

1. Pull the latest changes:
   ```bash
   git pull
   ```

2. Rebuild and restart the containers:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

## Custom Configuration

### Using Environment Variables

For better security, use environment variables instead of hardcoded values:

1. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Edit the file with your settings:
   ```bash
   nano .env
   ```

3. Modify docker-compose.yml to use these variables:
   ```yaml
   environment:
     - SECRET_KEY=${SECRET_KEY:-defaultsecretkey}
     - JWT_SECRET=${JWT_SECRET:-defaultjwtsecret}
     # more environment variables...
   ```

## Best Practices for Development

### 1. MongoDB Models

When working with MongoDB models, always use explicit None checks:

```python
# CORRECT: Use explicit None checks
self.collection = None
if self.db is not None:
    self.collection = self.db["collectionName"]

# INCORRECT: PyMongo objects don't support boolean evaluation
self.collection = self.db["collectionName"] if self.db else None
```

### 2. Template Structure

Always use proper template inheritance:

```html
{% extends "base.html" %}

{% block content %}
   <!-- Your content here -->
{% endblock %}
```

### 3. Context Processing

Ensure templates have all required variables:

```python
def inject_user():
    """Inject user data into templates."""
    user_data = {
        'is_authenticated': False,
        'is_admin': False,
        'username': None,
        'email': None
    }
    
    # Always return both user_data and current_user
    return {
        'user_data': user_data,
        'current_user': user_data
    }
```

## Security Considerations

1. **Never** expose MongoDB directly to the internet (port 27017)
2. Change default credentials in the `.env` file
3. Use a reverse proxy like Nginx with SSL for production deployments
4. Consider using Docker Secrets for sensitive information in production
