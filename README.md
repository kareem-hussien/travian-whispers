# Travian Whispers - Automated Travian Bot

**Author:** Eng. Kareem Hussien  
**Contact:** [WhatsApp](https://wa.me/00201099339393)

## Overview
Travian Whispers is an advanced **automation bot** for the browser-based game **Travian**, built using **Python** and **Selenium**. It supports **multi-tasking**, allowing users to run multiple automation processes simultaneously.

### Features
✅ **Automated Login** - Securely logs into Travian with stored credentials.  
✅ **Village Management** - Extracts and stores village data.  
✅ **Auto-Farming** - Sends farm lists at regular intervals.  
✅ **Troop Training** - Automates training based on the user’s tribe.  
✅ **Multi-Tasking** - Supports running multiple tasks simultaneously.  
✅ **Task Memory** - Saves running tasks and allows adding more without restarting.  

---

## Installation

### 1️⃣ **Setup Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ **Run the Bot**
```bash
python3 main.py
```

---

## Project Structure
```plaintext
travian-whispers/
├── main.py
├── info/
│   ├── maps/
│   │   ├── buildings.txt
│   │   └── troops-maps.txt
│   └── profile/
│       ├── credentials.txt
│       ├── tribe.txt
│       └── villages_list.txt
├── startup/
│   ├── welcome_messages.py
│   ├── login_credentials.py
│   ├── browser_profile.py
│   ├── villages_list.py
│   └── tasks.py
├── tasks/
│   ├── auto_farm.py
│   ├── trainer/
│   │   ├── trainer_data.py
│   │   ├── trainer_actions.py
│   │   ├── trainer_main.py
│   │   └── __init__.py
│   └── villages.py
└── requirements.txt
```

---

## **Step-by-Step Flow**

### 1️⃣ **Startup and Login**
- Displays **welcome messages** (`startup/welcome_messages.py`).
- Loads **saved credentials** (`info/profile/credentials.txt`).
- Logs into **Travian** (`startup/browser_profile.py`).
- Extracts **villages list** (`startup/villages_list.py`).
- Detects **user tribe** (`info/profile/tribe.txt`).

### 2️⃣ **Task Selection & Multi-Tasking**
- **Auto-Farm** (`tasks/auto_farm.py`).
- **Troop Trainer** (`tasks/trainer/trainer_main.py`).
- **Both Farming & Training**.
- **View running tasks**.
- **Stop a task without exiting the bot**.
- **Keep tasks in memory and return to the menu**.

### 3️⃣ **Automation Execution**
✅ **Auto-Farm** sends farm lists at random intervals.  
✅ **Trainer** only shows **troops available for the user's tribe**.  
✅ **Task Manager** prevents duplicate tasks from running.  

---

## **Multi-Tasking System**
- When a task is started, it is **saved in memory**.
- The bot **returns to the task menu** instead of exiting.
- Users can **start/stop tasks dynamically**.
- **Active tasks run in the background**.

---

## **Troubleshooting**
**Common Issues:**
- **ChromeDriver issues:** Ensure **Chrome & WebDriver** are up to date.
- **Credential issues:** Verify `info/profile/credentials.txt` has the correct format.
- **Tribe not detected:** Run **profile update** (`tasks/trainer/trainer_main.py`).
- **Bot not responding:** Restart the **browser session** (`startup/browser_profile.py`).

---

## **Planned Features**
🚀 **MongoDB Authentication** - Multi-user accounts with subscriptions. *(Planned)*  
🚀 **Admin Panel** - Manage bot settings remotely. *(Planned)*  
🚀 **Web Dashboard** - Start/Stop tasks via a web interface. *(Planned)*  

---

## **Contact & Support**
For assistance, contact me on [WhatsApp](https://wa.me/00201099339393).  

---
**© Eng. Kareem Hussien - Travian Whispers Automation Suite**