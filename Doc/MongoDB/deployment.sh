#!/bin/bash
# MongoDB Production Deployment Script for Travian Whispers
# This script helps set up MongoDB in a production environment

set -e  # Exit on any error

# Log colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# MongoDB configuration
MONGO_VERSION="5.0"
DB_NAME="whispers"
BACKUP_DIR="./backups"
ADMIN_USER="admin"
APP_USER="travian_app"

# Configuration file
CONFIG_FILE="./.env"

# Function to log messages
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
  exit 1
}

# Check if MongoDB is installed
check_mongodb() {
  log "Checking MongoDB installation..."
  if command -v mongod &> /dev/null; then
    MONGO_VERSION=$(mongod --version | grep "db version" | sed 's/db version v//')
    log "MongoDB $MONGO_VERSION is installed"
  else
    error "MongoDB is not installed. Please install MongoDB $MONGO_VERSION or later"
  fi
}

# Check if MongoDB is running
check_mongodb_running() {
  log "Checking if MongoDB is running..."
  if pgrep -x mongod &> /dev/null; then
    log "MongoDB is running"
  else
    warn "MongoDB is not running. Attempting to start..."
    if systemctl start mongod &> /dev/null; then
      log "MongoDB started successfully"
    else
      error "Failed to start MongoDB. Please check MongoDB service"
    fi
  fi
}

# Create MongoDB users
create_mongo_users() {
  log "Setting up MongoDB users..."
  
  # Prompt for passwords if not already set
  if [ -z "$ADMIN_PASSWORD" ]; then
    read -sp "Enter MongoDB admin password: " ADMIN_PASSWORD
    echo
  fi
  
  if [ -z "$APP_PASSWORD" ]; then
    read -sp "Enter MongoDB application user password: " APP_PASSWORD
    echo
  fi
  
  # Create admin user
  mongo admin --eval "db.createUser({user: '$ADMIN_USER', pwd: '$ADMIN_PASSWORD', roles: [ { role: 'userAdminAnyDatabase', db: 'admin' } ]})" || warn "Admin user may already exist"
  
  # Create application user
  mongo admin -u "$ADMIN_USER" -p "$ADMIN_PASSWORD" --authenticationDatabase "admin" --eval "use $DB_NAME; db.createUser({user: '$APP_USER', pwd: '$APP_PASSWORD', roles: [ { role: 'readWrite', db: '$DB_NAME' } ]})" || warn "Application user may already exist"
  
  log "MongoDB users created successfully"
}

# Enable MongoDB authentication
enable_authentication() {
  log "Enabling MongoDB authentication..."
  
  MONGO_CONF="/etc/mongod.conf"
  if [ ! -f "$MONGO_CONF" ]; then
    warn "MongoDB configuration file not found at $MONGO_CONF"
    return
  fi
  
  # Check if authentication is already enabled
  if grep -q "authorization: enabled" "$MONGO_CONF"; then
    log "Authentication is already enabled"
  else
    # Backup the original config
    cp "$MONGO_CONF" "${MONGO_CONF}.bak"
    
    # Add authentication setting
    if grep -q "security:" "$MONGO_CONF"; then
      # Security section exists, add authorization
      sed -i '/security:/a\  authorization: enabled' "$MONGO_CONF"
    else
      # Add security section with authorization
      echo -e "\nsecurity:\n  authorization: enabled" >> "$MONGO_CONF"
    fi
    
    log "Authentication enabled in MongoDB configuration"
    log "Restarting MongoDB..."
    systemctl restart mongod
  fi
}

# Create necessary directories
create_directories() {
  log "Creating necessary directories..."
  
  # Create backup directory
  mkdir -p "$BACKUP_DIR"
  chmod 750 "$BACKUP_DIR"
  log "Created backup directory: $BACKUP_DIR"
}

# Create configuration file
create_config_file() {
  log "Creating configuration file..."
  
  if [ -f "$CONFIG_FILE" ]; then
    warn "Configuration file already exists at $CONFIG_FILE"
    read -p "Do you want to overwrite it? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ]; then
      log "Keeping existing configuration file"
      return
    fi
  fi
  
  # Create connection string
  MONGO_URI="mongodb://$APP_USER:$APP_PASSWORD@localhost:27017/$DB_NAME?authSource=admin"
  
  # Generate a random secret key
  SECRET_KEY=$(openssl rand -hex 32)
  
  # Write configuration to file
  cat > "$CONFIG_FILE" << EOF
# MongoDB Configuration
MONGODB_URI=$MONGO_URI
MONGODB_DB_NAME=$DB_NAME

# Application Configuration
SECRET_KEY=$SECRET_KEY
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@travianwhispers.com
ADMIN_PASSWORD=change-this-password

# Backup Configuration
BACKUP_DIR=$BACKUP_DIR
BACKUP_RETENTION_DAYS=30

# Email Configuration
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM=Travian Whispers <noreply@example.com>

# Payment Gateway Configuration
PAYPAL_CLIENT_ID=
PAYPAL_SECRET=
PAYPAL_MODE=sandbox
EOF

  chmod 600 "$CONFIG_FILE"
  log "Configuration file created at $CONFIG_FILE"
  log "Please update the configuration with your actual settings"
}

# Setup initial database
setup_database() {
  log "Setting up initial database..."
  
  # Run the database migration script
  if [ -f "./scripts/database_migration.py" ]; then
    log "Running database migration script..."
    python3 ./scripts/database_migration.py --all || error "Database migration failed"
    log "Database initialized successfully"
  else
    warn "Database migration script not found at ./scripts/database_migration.py"
    warn "Please run the script manually after setup"
  fi
}

# Configure automatic backups
setup_backups() {
  log "Setting up automatic backups..."
  
  # Create backup script
  BACKUP_SCRIPT="./scripts/backup.sh"
  
  cat > "$BACKUP_SCRIPT" << EOF
#!/bin/bash
# Automatic MongoDB backup script

# Load environment variables
source ./.env

# Set the backup filename
TIMESTAMP=\$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="\$BACKUP_DIR/mongodb_backup_\$TIMESTAMP.gz"

# Perform backup
mongodump --uri="\$MONGODB_URI" --gzip --archive="\$BACKUP_FILE" || exit 1

# Delete old backups
find "\$BACKUP_DIR" -name "mongodb_backup_*.gz" -type f -mtime +\$BACKUP_RETENTION_DAYS -delete

echo "Backup completed: \$BACKUP_FILE"
EOF

  chmod +x "$BACKUP_SCRIPT"
  log "Backup script created at $BACKUP_SCRIPT"
  
  # Add cron job for daily backups at 2 AM
  CRON_JOB="0 2 * * * $(pwd)/$BACKUP_SCRIPT >> $(pwd)/logs/backup.log 2>&1"
  
  # Check if cron job already exists
  if (crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"); then
    log "Backup cron job already exists"
  else
    # Create logs directory
    mkdir -p ./logs
    
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    log "Added daily backup cron job at 2 AM"
  fi
}

# Display setup summary
show_summary() {
  log "MongoDB Production Setup Summary:"
  echo "-----------------------------"
  echo "MongoDB Version: $MONGO_VERSION"
  echo "Database Name: $DB_NAME"
  echo "Admin User: $ADMIN_USER"
  echo "Application User: $APP_USER"
  echo "Backup Directory: $BACKUP_DIR"
  echo "Configuration File: $CONFIG_FILE"
  echo "-----------------------------"
  echo ""
  log "Setup completed successfully!"
  log "Next steps:"
  echo "1. Update the configuration file with your actual settings"
  echo "2. Run the database migration script if not already done"
  echo "3. Start your application"
}

# Main function
main() {
  log "Starting MongoDB Production Setup for Travian Whispers..."
  
  # Check prerequisites
  check_mongodb
  check_mongodb_running
  
  # Create directories
  create_directories
  
  # Setup MongoDB
  create_mongo_users
  enable_authentication
  
  # Setup application
  create_config_file
  setup_database
  setup_backups
  
  # Show summary
  show_summary
}

# Run main function
main
