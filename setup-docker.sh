#!/bin/bash
# Docker setup script for Travian Whispers

set -e

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Travian Whispers Docker Setup${NC}"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Create .env file in home directory to avoid NTFS permission issues
ENV_DIR=~/travian-whispers-env
ENV_FILE=${ENV_DIR}/.env

if [ ! -d "${ENV_DIR}" ]; then
    echo -e "${YELLOW}Creating directory for .env file...${NC}"
    mkdir -p ${ENV_DIR}
fi

if [ ! -f "${ENV_FILE}" ]; then
    echo -e "${YELLOW}Creating .env file at ${ENV_FILE}...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example ${ENV_FILE} || {
            cat .env.example > ${ENV_FILE} || {
                echo -e "${RED}Failed to create .env file.${NC}"
                exit 1
            }
        }
    else
        # If .env.example doesn't exist, create a basic .env file
        cat > ${ENV_FILE} << EOF
# Application settings
SECRET_KEY=replace_with_strong_random_string
JWT_SECRET=replace_with_different_strong_random_string
FLASK_ENV=production
SERVER_NAME=localhost:5000

# Database settings
MONGODB_URI=mongodb://mongodb:27017/whispers
MONGODB_DB_NAME=whispers

# PayPal settings
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=
PAYPAL_SECRET=

# Bot settings
HEADLESS=true
USER_ID=
EOF
    fi
    echo -e "${GREEN}.env file created at ${ENV_FILE}. Please edit it with your configuration.${NC}"
    echo -e "${YELLOW}Remember to set strong secret keys in the .env file!${NC}"
fi

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p logs backups info/maps info/profile

# Build Docker images
echo -e "${GREEN}Building Docker images...${NC}"
docker-compose build

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}To start the application, run:${NC} docker-compose up -d"
echo -e "${YELLOW}To view logs, run:${NC} docker-compose logs -f"
echo -e "${YELLOW}To stop the application, run:${NC} docker-compose down"
echo -e "${YELLOW}MongoDB data is persisted in a Docker volume.${NC}"
echo -e "${YELLOW}MongoDB admin interface is available at:${NC} http://localhost:8081"
