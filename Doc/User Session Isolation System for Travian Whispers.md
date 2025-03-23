# User Session Isolation System for Travian Whispers

## Overview

This documentation covers the implementation of GitHub Issue #3: Develop User Session Isolation System for Travian Whispers.

The session isolation system enables multiple users to access the Travian game through our automation suite without sharing IP addresses, which violates Travian's rules and can result in account bans.

## Components

The implementation consists of the following key components:

1. **IP Manager**: Manages a pool of proxy IPs and assigns them to users
2. **Session Manager**: Creates isolated browser sessions for each user
3. **Browser Isolation Manager**: Coordinates both IP and session management
4. **Modified Task Handling**: Updates auto-farm and trainer tasks to use isolated sessions
5. **Detection Handler**: Identifies potential detection risks and rotates IPs/sessions
6. **Scheduled Jobs**: Automates IP rotation and session cleanup
7. **Web Routes**: Provides user interface for monitoring and managing IPs

## Architecture

```
                                                 ┌─────────────────┐
                                                 │                 │
                                                 │  IP Manager     │
                                                 │                 │
                                                 └────────┬────────┘
                                                          │
                                                          │ manages
                                                          │
┌─────────────────┐                               ┌──────▼────────┐
│                 │                               │               │
│  Task Runner    │◄──────── uses ───────────────►│  Browser      │
│                 │                               │  Isolation    │
└───────┬─────────┘                               │  Manager      │
        │                                         │               │
        │ runs                                    └──────┬────────┘
        │                                                │
┌───────▼─────────┐                                      │ manages
│                 │                                      │
│  Auto Farm &    │                               ┌──────▼────────┐
│  Trainer Tasks  │                               │               │
│                 │                               │  Session      │
└───────┬─────────┘                               │  Manager      │
        │                                         │               │
        │ uses                                    └───────────────┘
        │
┌───────▼─────────┐
│                 │
│  Browser Profile│
│                 │
└─────────────────┘
```

## Implementation Details

### 1. IP Manager (`startup/ip_manager.py`)

- Maintains a MongoDB collection of proxy IPs
- Tracks IP status (available, in use, banned, etc.)
- Assigns IPs to users and handles rotation
- Detects and reports IP failures and bans

Key functions:
- `get_ip_for_user(user_id)`: Assigns or retrieves an IP for a user
- `rotate_ip_for_user(user_id)`: Rotates a user's IP assignment
- `report_ip_ban(ip_id, reason)`: Marks an IP as banned and releases assignments

### 2. Session Manager (`startup/session_isolation.py`)

- Creates isolated Chrome user data directories for each session
- Manages session creation, rotation, and cleanup
- Prevents session conflicts between users

Key functions:
- `get_session_for_user(user_id)`: Creates or retrieves a session directory
- `rotate_user_session(user_id)`: Creates a fresh session for a user
- `clean_old_sessions(max_age_hours)`: Removes sessions older than specified time

### 3. Browser Isolation Manager (`startup/session_isolation.py`)

- Coordinates both IP and session management
- Handles browser configuration (proxy, user-agent, headers)
- Manages detection risks and rotates identities

Key functions:
- `get_isolated_browser_config(user_id)`: Returns complete browser configuration
- `rotate_user_identity(user_id)`: Rotates both IP and browser session
- `handle_detection_risk(user_id, risk_level, context)`: Responds to detection risks

### 4. Browser Profile (`startup/browser_profile.py`)

- Setup browser with proper isolation configuration
- Handles login and common Travian operations
- Detects CAPTCHA and ban situations

Key functions:
- `setup_browser(user_id)`: Creates WebDriver with proper isolation
- `check_for_captcha(driver)`: Detects CAPTCHA presence
- `check_for_ban(driver)`: Detects account/IP bans
- `handle_detection_event(driver, user_id, event_type, context)`: Manages detection events

### 5. Task Components (`tasks/auto_farm.py` and `tasks/trainer/trainer_main.py`)

- Modified to use isolated browser profiles
- Enhanced with detection handling
- Support IP and session rotation when needed

Key features:
- Detection of CAPTCHAs and bans
- Automatic rotation when suspicious activity detected
- Proper cleanup of resources

### 6. Task Runner (`tasks/task_runner.py`)

- Centralized system for running automated tasks
- Manages task scheduling and execution
- Handles browser setup and cleanup
- Responds to rotation requirements

Key functions:
- `schedule_task(task_type, user_id, params, delay)`: Schedules a task for execution
- `_execute_auto_farm(task)`: Executes auto farm task with proper isolation
- `_execute_trainer(task)`: Executes trainer task with proper isolation

### 7. Scheduled Jobs (`startup/scheduled_jobs.py`)

- Runs periodic maintenance tasks
- Rotates IPs that have been used for too long
- Cleans up old browser sessions
- Monitors IP health

Key jobs:
- IP rotation (every 12 hours)
- Session cleanup (every 24 hours)
- IP health check (every 6 hours)

### 8. IP Management Routes (`web/routes/ip_routes.py`)

- Allows users to view their current IP
- Provides manual IP and session rotation
- Admin interface for managing the IP pool

Key routes:
- `/dashboard/ip/status`: Shows current IP status
- `/dashboard/ip/rotate`: Rotates IP address
- `/dashboard/ip/rotate_identity`: Rotates entire identity
- `/dashboard/ip/session_info`: Shows browser session info

## Testing

The implementation includes a comprehensive testing tool (`tools/test_isolation.py`) that verifies:

1. IP assignment
2. Browser session isolation
3. Rotation functionality
4. Concurrent session handling
5. Detection handling simulation

Run the tests with:
```bash
python tools/test_isolation.py --test all
```

## Integration

The session isolation system is initialized during application startup in `startup/init.py`. It:

1. Creates necessary directories
2. Initializes the database
3. Sets up the IP pool
4. Starts the task runner
5. Launches scheduled jobs

## Usage

### For Developers

To use the session isolation system in a new task:

```python
from startup.browser_profile import setup_browser, login

# Setup browser with isolation
driver = setup_browser(user_id)

# Login to Travian
login(driver, username, password, server)

# Perform operations...

# Handle detection
from startup.browser_profile import check_for_captcha, handle_detection_event
if check_for_captcha(driver):
    handle_detection_event(driver, user_id, "captcha")
```

### For Users

Users can manage their IP and session through the web interface:

1. View current IP status
2. Request IP rotation if experiencing issues
3. Rotate entire digital identity if needed
4. View logs of IP usage and rotation

## Security Considerations

1. IP credentials are stored securely in the database
2. Session directories contain sensitive data and should be properly secured
3. Detection handling is crucial to avoid account bans
4. IP rotation is essential to maintain account security

## Future Improvements

1. Expand the proxy IP pool with reliable providers
2. Implement IP quality scoring based on performance
3. Add more sophisticated detection algorithms
4. Develop automated testing of proxies before use

## Conclusion

The user session isolation system provides robust protection against Travian's detection mechanisms by ensuring each user has a unique IP address and browser fingerprint. The system automatically handles detection risks and rotates IPs and sessions as needed.
