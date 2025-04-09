#!/bin/bash
# File: check_grid.sh

# Ensure Selenium Grid is running before starting the application
echo "Checking Selenium Grid status..."

MAX_RETRIES=30
RETRY_INTERVAL=2
RETRY_COUNT=0
GRID_URL=${SELENIUM_REMOTE_URL:-http://selenium:4444/wd/hub}
STATUS_URL="${GRID_URL}/status"

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Attempt $((RETRY_COUNT+1))/$MAX_RETRIES: Checking Selenium Grid at $STATUS_URL"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $STATUS_URL)
    
    if [ $HTTP_CODE -eq 200 ]; then
        echo "Selenium Grid is up and running!"
        exec "$@"  # Execute the command passed to this script
        exit 0
    else
        echo "Selenium Grid not ready yet (status code: $HTTP_CODE). Retrying in $RETRY_INTERVAL seconds..."
        sleep $RETRY_INTERVAL
        RETRY_COUNT=$((RETRY_COUNT+1))
    fi
done

echo "Selenium Grid not available after $MAX_RETRIES attempts. Starting anyway, but automation may fail."
exec "$@"  # Execute the command passed to this script anyway
exit 0