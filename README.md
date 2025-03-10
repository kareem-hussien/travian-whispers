# Travian Whispers - Automated Travian Bot

**Author:** Eng. Kareem Hussien  
**Contact:** [WhatsApp](https://wa.me/00201099339393)

## Project Overview

This project provides automation scripts for the browser-based game **Travian**. It supports automatic farming, troop training, and account profile management with Selenium.

## Project Structure

```plaintext
travian-whispers/
├── main.py
├── info/
│   ├── maps/
│   │   ├── buildings.txt
│   │   └── troops-maps.txt
│
│   └── profile/
│       ├── credentials.txt
│       ├── tribe.txt
│       └── villages_list.txt
│
├── startup/
│   ├── welcome_messages.py
│   ├── login_credentials.py
│   ├── browser_profile.py
│   ├── villages_list.py
│   └── tasks.py
│
└── tasks/
    ├── auto_farm.py
    ├── villages.py
    └── trainer/
        ├── __init__.py
        ├── trainer_data.py
        ├── trainer_actions.py
        └── trainer_main.py


## Detailed File Descriptions

### Main Entry (`main.py`)
This file starts the bot, initializes the environment, and triggers task menus.

### Startup Scripts (`startup/`)
- **welcome_messages.py** - Display welcome/loading messages.
- **login_credentials.py** - Handle credential retrieval and storage.
- **tasks.py** - Provides a menu to choose tasks to run concurrently.
- **villages_list.py** extracts all account villages.

### Task Automation Scripts (`tasks/`)
- **auto_farm.py** - Automatically starts farm lists.
- **villages.py** - Extracts and manages village data.
- **trainer/** - Automates troop training:
    - **trainer_data.py** - Loads troop types and buildings from maps.
    - **trainer_actions.py** - Performs the actual Selenium actions.
    - **trainer_main.py** - User interaction and task scheduling.

### Info Data (`info/`)
- **maps/**:
  - **buildings.txt**: URLs for barracks, stable, and workshop.
  ```
  barracks=https://ts1.x1.international.travian.com/build.php?gid=19
  stable=https://ts1.x1.international.travian.com/build.php?gid=20
  workshop=https://ts1.x1.international.travian.com/build.php?gid=21
  ```
  - **troops-maps.txt** - Troops mapping per tribe.
  ```
  Romans-barracks-[tid1]-Legionnaire
  Romans-barracks-[tid2]-Praetorian
  Romans-barracks-[tid3]-Imperian
  ```

## Python Dependencies
- `selenium`
- `webdriver_manager`

---

# Installation

Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install selenium webdriver_manager
```

# Usage

Run the bot:

```bash
python3 main.py
```

---

# Step-by-Step Flow

1. **Startup and Login**:
    - Display welcome messages (`startup/welcome_messages.py`).
    - Load saved credentials or prompt to input them (`startup/login_credentials.py`).

2. **Browser Initialization**
   - Opens ChromeDriver instance.

3. **Account Profile Check**
   - Detects and confirms account tribe and profile ID (`tasks/villages.py`).

4. **Villages List Management**
   - Extract villages and their coordinates, saving data to `villages_list.txt`.

5. **Task Selection Menu (`startup/tasks.py`)**
   - Select tasks to run concurrently:
     - Auto-Farm
     - Trainer
     - Both
     - Exit

---

# Usage

1. Ensure your Travian login credentials are saved in:
```
info/profile/credentials.txt
```
or input them manually on the first run.

2. Run the bot:
```bash
python3 main.py
```

3. Select tasks to run from the presented menu.

---

# Troubleshooting

**Common Issues:**

- **ChromeDriver issues:**
  Ensure you have the latest version of Chrome and compatible ChromeDriver.
- **Credential issues:** Verify `credentials.txt` has the correct format.

---

# Project Structure Overview

This project follows a modular structure, allowing for easy maintenance and updates. Data files are separated from scripts, ensuring flexibility.

---

# Contact & Support

For further assistance, contact me on [WhatsApp](https://wa.me/00201099339393).

---

**© Eng. Kareem Hussien - Travian Whispers Automation Suite**
```

