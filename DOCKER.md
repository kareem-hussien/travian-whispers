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

4. Start the application:
   ```bash
   docker-compose up -d
   ```

5. Access the web interface at http://localhost:5000

## Docker Components

The Docker setup consists of the following services:

- **mongodb**: MongoDB 4.4 database (compatible with older CPUs without AVX support)
- **mongo-express**: Web interface for MongoDB administration
- **web**: The Flask web application
- **bot**: The Travian automation bot (can be enabled or disabled as needed)

## Troubleshooting Docker Issues

### 1. YAML Parsing Errors

If you encounter errors like "services.networks must be a mapping" or "services.volumes must be a mapping":

- Use the exact format shown above, with proper indentation
- Avoid copying from PDF or websites that might add invisible characters
- Type the configuration manually if needed

### 2. Container Permission Issues

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

### 3. MongoDB CPU Compatibility

If MongoDB 5.0+ fails with errors about AVX support, the provided configuration uses MongoDB 4.4 which is compatible with older CPUs.

### 4. Missing HTTP Utils Module

The `http_utils.py` module is required for the payment system. If it's missing, run:

```bash
./fix-http-utils.sh
```

### 5. Bot Service Issues

The bot service may continuously restart if not properly configured. The provided configuration runs it in web mode for testing. To run in bot mode with a specific user:

```yaml
bot:
  build: .
  command: python main.py --user-id <YOUR_USER_ID_HERE>
  # rest of configuration...
```

Replace `<YOUR_USER_ID_HERE>` with an actual MongoDB user ID.

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

## Special Notes for Z400 Workstations

If running on an HP Z400 workstation or similar older hardware:

1. Use MongoDB 4.4 instead of newer versions that require AVX support
2. Avoid running the Selenium bot in headless mode if experiencing issues
3. Consider limiting Docker memory usage if the system becomes unresponsive

## Security Considerations

1. **Never** expose MongoDB directly to the internet (port 27017)
2. Change default credentials in the `.env` file
3. Use a reverse proxy like Nginx with SSL for production deployments
4. Consider using Docker Secrets for sensitive information in production

## Advanced Configuration

For advanced setups like multi-node deployments, load balancing, or high availability, refer to the Docker Swarm and Docker Compose documentation.
