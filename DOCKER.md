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

2. Run the setup script:
   ```bash
   chmod +x setup-docker.sh
   ./setup-docker.sh
   ```

3. Edit the `.env` file in your home directory with your configuration:
   ```bash
   nano ~/travian-whispers-env/.env
   ```

4. Start the application:
   ```bash
   docker-compose up -d
   ```

5. Access the web interface at http://localhost:5000

## Docker Components

The Docker setup consists of the following services:

- **web**: The Flask web application
- **bot**: The Travian automation bot
- **mongodb**: MongoDB database
- **mongo-express**: Web interface for MongoDB (optional)

## Configuration

### Environment Variables

Edit the `.env` file in your home directory (`~/travian-whispers-env/.env`) to configure the application:

- `SECRET_KEY`: Flask secret key
- `JWT_SECRET`: JWT token secret key
- `MONGODB_URI`: MongoDB connection string
- `PAYPAL_CLIENT_ID` and `PAYPAL_SECRET`: PayPal API credentials
- `USER_ID`: MongoDB user ID for bot mode

Note: The `.env` file is stored in your home directory instead of the project directory to avoid permission issues with NTFS drives.

### Volumes

The Docker setup uses the following volumes:

- **mongodb_data**: Persists MongoDB data
- **logs**: Stores application logs
- **backups**: Stores database backups

## Running Different Modes

### Web Application Only

```bash
docker-compose up -d web mongodb
```

### Bot Mode Only

```bash
# Make sure to set USER_ID in .env file first
docker-compose up -d bot mongodb
```

### Full Stack

```bash
docker-compose up -d
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

## Database Management

### Access MongoDB Shell

```bash
docker-compose exec mongodb mongo
```

### MongoDB Web Interface

Access MongoDB Express at http://localhost:8081

## Backups

Database backups are stored in the `backups` volume. You can access them from the host system.

To create a manual backup:

```bash
docker-compose exec web python -c "from database.backup import create_backup; create_backup()"
```

## Troubleshooting

### NTFS Filesystem Considerations

If your project is located on an NTFS drive (common when working with external drives or Windows partitions), you might encounter permission issues. This setup addresses this by:

1. Storing the `.env` file in your Linux home directory (`~/travian-whispers-env/.env`)
2. Using Docker volumes for persistent data (logs, backups)

If you encounter permission issues with other files, you might need to:

```bash
# Check your drive mount settings
mount | grep ntfs

# Create directories with proper permissions before Docker tries to access them
mkdir -p info/maps info/profile
chmod 777 info info/maps info/profile
```

### Selenium/Chrome Issues

If the bot has issues with Chrome, you may need to update the Chrome configuration:

```bash
docker-compose exec bot google-chrome --version
```

Check that the ChromeDriver version matches Chrome's version:

```bash
docker-compose exec bot chromedriver --version
```

### Connection Issues

If services can't connect to each other:

1. Ensure all containers are on the same network:
   ```bash
   docker network inspect travian-whispers_travian-network
   ```

2. Check if MongoDB is accessible:
   ```bash
   docker-compose exec web ping mongodb
   ```

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

## Security Considerations

1. **Never** expose MongoDB directly to the internet (port 27017)
2. Change default credentials in the `.env` file
3. Use a reverse proxy like Nginx with SSL for production deployments
4. Consider using Docker Secrets for sensitive information in production
