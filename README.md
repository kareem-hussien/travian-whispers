Below is an updated README.md that includes all the latest features and project structure:

---

```markdown
# travian-whispers

Travian Text-Game AutoBot.

This project automates several tasks for Travian (e.g., auto-farming, troop training, village extraction, and tribe detection) using Selenium WebDriver. The suite is built in Python with a modular design, making it easy to add new features in the future.

## Features

- **Auto-Farm**: Automatically triggers your farm list at random intervals.
- **Trainer**: Automates troop training based on your tribe’s available units.
- **Village Extraction**: Extracts your village list (name, coordinates, newdid) and saves it for later use.
- **Tribe Detection**: Automatically detects your account tribe (and profile ID) from your profile, confirms it with you, and saves the information to a file.
- **Task Scheduling**: Multiple tasks can be scheduled concurrently using threading.
- **Startup Animation**: Displays welcome messages with a loading effect at startup.
- **Modular Design**: Code is split into multiple modules (including a `startup` folder) for improved maintainability.

## Requirements

- Python 3.8+
- [Selenium](https://www.selenium.dev/)
- [webdriver-manager](https://pypi.org/project/webdriver-manager/)

## Installation

1. **Clone the Repository**  
   Open your terminal and run:
   ```bash
   git clone https://github.com/yourusername/travian-whispers.git
   cd travian-whispers
   ```

2. **Create and Activate a Virtual Environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the Required Python Packages**
   ```bash
   pip install -r requirements.txt
   ```
   *(If you don't have a `requirements.txt`, create one with the following contents:)*
   ```
   selenium
   webdriver-manager
   ```

## Setup

### Credentials File (Optional)
You can store your Travian login credentials in a file named `credentials.txt` in the following format:
```
your_username
your_password
```
When you run the program, it will ask if you want to use these saved credentials.

### Buildings File (For Trainer Module)
Create a `buildings.txt` file with the URLs for your building pages (barracks, stable, workshop). Example:
```
barracks=https://ts1.x1.international.travian.com/build.php?gid=19
stable=https://ts1.x1.international.travian.com/build.php?gid=20
workshop=https://ts1.x1.international.travian.com/build.php?gid=21
```

### Tribe File
After successful tribe detection from your profile, the detected tribe and profile ID will be saved to `tribe.txt` in the format:  
```
Tribe,ProfileID
```

## How to Run

Start the Automation Suite by running the main script:
```bash
python3 main.py
```

### Program Flow

1. **Welcome Animation**  
   At startup, the program displays welcome messages with a loading effect.
2. **Login**  
   You will be prompted for your Travian credentials (or you can use the saved ones from `credentials.txt`).
3. **Browser & Profile Detection**  
   The program opens the browser, logs in, and automatically navigates to your profile edit page. It clicks the Overview tab to detect your tribe and extract your profile ID. You are asked to confirm the detected tribe. Once confirmed, the tribe and profile ID are saved to `tribe.txt`.
4. **Village List Refresh**  
   You will be asked whether to refresh your villages list. If you choose yes, the script extracts village names, coordinates, and IDs, then saves them to `villages_list.txt`.
5. **Task Menu**  
   Finally, a menu is displayed with the following options:
   - **Auto-Farm**: Runs the auto-farming routine.
   - **Trainer**: Runs the troop training routine.
   - **Both Auto-Farm and Trainer**: Runs both tasks concurrently.
   - **Exit**: Closes the browser and terminates the program.

## Project Structure

```
travian-whispers/
├── main.py
├── auto_farm.py
├── trainer.py
├── villages.py
├── requirements.txt
├── credentials.txt (optional)
├── buildings.txt
├── tribe.txt (generated after tribe detection)
└── startup/
    ├── welcome_messages.py
    ├── login_credentials.py
    └── browser_profile.py
```

- **main.py**  
  The central script that displays welcome messages, handles login, performs profile/tribe detection, village extraction, and shows the main task menu.
- **auto_farm.py**  
  Contains automation code for triggering your farm list at random intervals.
- **trainer.py**  
  Contains automation code for troop training based on your tribe and selected options.
- **villages.py**  
  Contains code to extract and save the list of villages from the overview page.
- **startup/**  
  Contains modules for startup tasks:
  - **welcome_messages.py**: Displays welcome messages with a loading effect.
  - **login_credentials.py**: Handles reading and saving Travian credentials.
  - **browser_profile.py**: Handles browser setup, login, and auto-detection of account tribe and profile ID.

## Troubleshooting

- **Login Issues**:  
  If login fails, verify that your credentials are correct. If you encounter CAPTCHA challenges, run the browser in non-headless mode to solve them manually.
  
- **Element Not Found Errors**:  
  Travian’s website layout may change. If the script cannot locate an element (e.g., the tribe row or village list), inspect the page and update the corresponding XPath or CSS selectors in the code.

## License

MIT License

Made with love by Eng. Kareem Hussien  
WhatsApp: [https://wa.me/002010993393](https://wa.me/002010993393)
```

---