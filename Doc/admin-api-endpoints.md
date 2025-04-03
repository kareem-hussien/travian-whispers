# Travian Whispers Admin API Documentation

This document outlines all admin API endpoints available in the Travian Whispers application. These endpoints provide administrative functionality for managing users, subscriptions, transactions, and system maintenance.

## Authentication

All admin API endpoints require authentication and admin privileges. Requests will be rejected if the user is not authenticated or lacks admin role.

## Dashboard

### Refresh Dashboard Statistics
- **Endpoint**: `/api/admin/refresh-stats`
- **Method**: `GET`
- **Description**: Refreshes all dashboard statistics
- **Response**:
  ```json
  {
    "success": true,
    "message": "Stats refreshed successfully"
  }
  ```

## User Management

### Get User Details
- **Endpoint**: `/api/admin/user/{user_id}`
- **Method**: `GET`
- **Description**: Retrieves detailed information about a specific user
- **Parameters**:
  - `user_id`: ID of the user to retrieve
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "id": "string",
      "username": "string",
      "email": "string",
      "role": "string",
      "status": "string",
      "createdAt": "string",
      "subscription": {
        "status": "string",
        "planId": "string",
        "planName": "string",
        "startDate": "string",
        "endDate": "string"
      },
      "villages": [],
      "settings": {}
    }
  }
  ```

### Create User
- **Endpoint**: `/admin/users/create`
- **Method**: `POST`
- **Description**: Creates a new user account
- **Form Data**:
  - `username`: Username for new user
  - `email`: Email address for new user
  - `password`: Password for new user
  - `role`: Role (user or admin)
  - `isVerified`: Whether the email is pre-verified
  - `subscription_status`: Subscription status (active or inactive)
  - `subscription_plan`: ID of subscription plan
  - `billing_period`: Billing period (monthly or yearly)

### Update User
- **Endpoint**: `/admin/users/edit/{user_id}`
- **Method**: `POST`
- **Description**: Updates an existing user's information
- **Parameters**:
  - `user_id`: ID of the user to update
- **Form Data**:
  - `email`: Email address
  - `role`: User role
  - `status`: Account status
  - `new_password`: New password (optional)
  - `subscription_status`: Subscription status
  - `subscription_plan`: ID of subscription plan
  - `billing_period`: Billing period

### Delete User
- **Endpoint**: `/admin/users/delete/{user_id}`
- **Method**: `POST`
- **Description**: Deletes a user account
- **Parameters**:
  - `user_id`: ID of the user to delete

## Subscription Plans

### Create Subscription Plan
- **Endpoint**: `/admin/subscriptions/create`
- **Method**: `POST`
- **Description**: Creates a new subscription plan
- **Form Data**:
  - `planName`: Name of the plan
  - `planPrice`: Monthly price of the plan
  - `yearlyPrice`: Yearly price of the plan
  - `planDescription`: Description of the plan
  - `featureAutoFarm`: Whether auto-farm feature is included
  - `featureTrainer`: Whether troop trainer feature is included
  - `featureNotification`: Whether notifications are included
  - `featureAdvanced`: Whether advanced features are included
  - `maxVillages`: Maximum number of villages allowed
  - `maxTasks`: Maximum number of concurrent tasks allowed

### Update Subscription Plan
- **Endpoint**: `/admin/subscriptions/edit/{plan_id}`
- **Method**: `POST`
- **Description**: Updates an existing subscription plan
- **Parameters**:
  - `plan_id`: ID of the plan to update
- **Form Data**: Same as create subscription plan

### Delete Subscription Plan
- **Endpoint**: `/admin/subscriptions/delete/{plan_id}`
- **Method**: `POST`
- **Description**: Deletes a subscription plan
- **Parameters**:
  - `plan_id`: ID of the plan to delete

## Transactions

### Get Transaction Details
- **Endpoint**: `/admin/transactions/{transaction_id}`
- **Method**: `GET`
- **Description**: Retrieves detailed information about a specific transaction
- **Parameters**:
  - `transaction_id`: ID of the transaction to retrieve

### Update Transaction Status
- **Endpoint**: `/admin/transactions/update-status/{transaction_id}`
- **Method**: `POST`
- **Description**: Updates the status of a transaction
- **Parameters**:
  - `transaction_id`: ID of the transaction to update
- **Form Data**:
  - `status`: New status (completed, pending, failed, refunded)
  - `notes`: Optional notes about the status change

### Send Transaction Receipt
- **Endpoint**: `/admin/transactions/send-receipt/{transaction_id}`
- **Method**: `POST`
- **Description**: Sends a receipt for a transaction via email
- **Parameters**:
  - `transaction_id`: ID of the transaction
- **Form Data**:
  - `email`: Email address to send receipt to
  - `subject`: Email subject (optional)
  - `message`: Custom message (optional)

## System Maintenance

### Update Maintenance Mode
- **Endpoint**: `/admin/update-maintenance`
- **Method**: `POST`
- **Description**: Toggles system maintenance mode
- **JSON/Form Data**:
  - `enabled`: Whether maintenance mode is enabled
  - `message`: Message to display to users during maintenance
  - `duration`: Expected duration of maintenance

### Create Backup
- **Endpoint**: `/admin/create-backup`
- **Method**: `POST`
- **Description**: Creates a database backup
- **JSON/Form Data**:
  - `backup_type`: Type of backup (full, users, transactions, subscriptions)
  - `compress_backup`: Whether to compress the backup

### Restore Backup
- **Endpoint**: `/admin/restore-backup`
- **Method**: `POST`
- **Description**: Restores a database from a backup
- **Form Data**:
  - `filename`: Name of the backup file to restore

### Delete Backup
- **Endpoint**: `/admin/delete-backup`
- **Method**: `POST`
- **Description**: Deletes a backup file
- **JSON/Form Data**:
  - `filename`: Name of the backup file to delete

### Download Backup
- **Endpoint**: `/admin/download-backup/{filename}`
- **Method**: `GET`
- **Description**: Downloads a backup file
- **Parameters**:
  - `filename`: Name of the backup file to download

## System Logs

### Get Log Details
- **Endpoint**: `/admin/api/logs/{log_id}`
- **Method**: `GET`
- **Description**: Retrieves detailed information about a specific log entry
- **Parameters**:
  - `log_id`: ID of the log entry to retrieve
- **Response**:
  ```json
  {
    "success": true,
    "log": {
      "id": "string",
      "timestamp": "string",
      "level": "string",
      "user": "string",
      "message": "string",
      "details": "string",
      "ip_address": "string",
      "category": "string",
      "stack_trace": "string"
    }
  }
  ```

### Download Logs
- **Endpoint**: `/admin/download-logs`
- **Method**: `POST`
- **Description**: Downloads logs based on filter criteria
- **Form Data**:
  - `level`: Log level filter (all, info, warning, error, debug)
  - `date_range`: Date range (today, yesterday, last7days, etc.)
  - `format`: Download format (csv, json, txt)
  - `date_from`: Custom start date (if date_range is custom)
  - `date_to`: Custom end date (if date_range is custom)

### Clear Old Logs
- **Endpoint**: `/admin/clear-logs`
- **Method**: `POST`
- **Description**: Clears logs older than a specified retention period
- **Form Data**:
  - `retention_days`: Number of days to retain logs

## Reports

### Generate Report
- **Endpoint**: `/admin/generate-report`
- **Method**: `POST`
- **Description**: Generates various administrative reports
- **Form Data**:
  - `report_type`: Type of report (users, transactions, subscriptions, system)
  - `date_range`: Date range for the report
  - `report_format`: Format of the report (pdf, csv, excel)
  - `start_date`: Custom start date (if date_range is custom)
  - `end_date`: Custom end date (if date_range is custom)

## Settings

### Update General Settings
- **Endpoint**: `/admin/settings`
- **Method**: `POST`
- **Description**: Updates general system settings
- **Form Data**:
  - `form_type`: "general"
  - `siteName`: Site name
  - `siteDescription`: Site description
  - `timezone`: Default timezone
  - `maintenanceMode`: Whether maintenance mode is enabled
  - `maintenanceMessage`: Maintenance message

### Update Email Settings
- **Endpoint**: `/admin/settings`
- **Method**: `POST`
- **Description**: Updates email settings
- **Form Data**:
  - `form_type`: "email"
  - `smtpServer`: SMTP server hostname
  - `smtpPort`: SMTP port
  - `smtpSecurity`: SMTP security type
  - `smtpUsername`: SMTP username
  - `smtpPassword`: SMTP password
  - `senderEmail`: Sender email address
  - `senderName`: Sender name

### Update Payment Settings
- **Endpoint**: `/admin/settings`
- **Method**: `POST`
- **Description**: Updates payment gateway settings
- **Form Data**:
  - `form_type`: "payment"
  - `paypalEnabled`: Whether PayPal is enabled
  - `paypalMode`: PayPal mode (sandbox or live)
  - `paypalClientId`: PayPal client ID
  - `paypalSecret`: PayPal secret
  - `stripeEnabled`: Whether Stripe is enabled
  - `stripeMode`: Stripe mode
  - `stripePublishableKey`: Stripe publishable key
  - `stripeSecretKey`: Stripe secret key
  - `currency`: Default currency
  - `currencyPosition`: Currency symbol position

### Update Security Settings
- **Endpoint**: `/admin/settings`
- **Method**: `POST`
- **Description**: Updates security settings
- **Form Data**:
  - `form_type`: "security"
  - `emailVerification`: Whether email verification is required
  - `sessionTimeout`: Session timeout in minutes
  - `maxLoginAttempts`: Maximum login attempts
  - `accountLockDuration`: Account lock duration in minutes
  - `passwordPolicy`: Password policy type
  - `passwordExpiry`: Password expiry in days
  - `forceHttps`: Whether to force HTTPS
  - `enableHSTS`: Whether to enable HSTS
  - `enableCSP`: Whether to enable content security policy
  - `xFrameOptions`: X-Frame-Options header value

### Update Backup Settings
- **Endpoint**: `/admin/settings`
- **Method**: `POST`
- **Description**: Updates backup settings
- **Form Data**:
  - `form_type`: "backup"
  - `autoBackup`: Whether automatic backups are enabled
  - `backupFrequency`: Backup frequency
  - `backupTime`: Time for automatic backups
  - `backupType`: Default backup type
  - `compressBackups`: Whether to compress backups
  - `retentionPeriod`: Backup retention period in days
  - `maxBackups`: Maximum number of backups to keep
  - `backupLocation`: Backup storage location
  - `externalStorage`: Whether to use external storage
  - `externalStorageType`: Type of external storage

### Test Email Configuration
- **Endpoint**: `/admin/test-email`
- **Method**: `POST`
- **Description**: Sends a test email to verify email configuration
- **Form Data**:
  - `form_type`: "test_email"
  - `testEmailAddress`: Email address to send test to

## PayPal Webhook

### Process PayPal Webhook
- **Endpoint**: `/api/webhooks/paypal`
- **Method**: `POST`
- **Description**: Handles PayPal webhook notifications
- **Headers**:
  - Required PayPal signature headers for verification
- **Body**: PayPal webhook event data
