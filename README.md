# travian-whispers
Travian Text-Game AutoBot.
This project automates several tasks for Travian (e.g., auto-farming, troop training, village extraction, and tribe detection) using Selenium WebDriver. The suite is built in Python and uses a modular design so you can easily add new features in the future.

## Features

- **Auto-Farm**: Automatically triggers your farm list at random intervals.
- **Trainer**: Automates troop training based on your tribe’s available units.
- **Village Extraction**: Extracts your village list (name, coordinates, newdid) and saves it for later use.
- **Tribe Detection**: Automatically detects your account tribe from your profile, confirms it with you, and saves it to a file.
- **Task Scheduling**: Multiple tasks can be scheduled concurrently using threading.

## Requirements

- Python 3.8+
- [Selenium](https://www.selenium.dev/)
- [webdriver-manager](https://pypi.org/project/webdriver-manager/)

## Installation

1. **Clone the Repository**  
   Open your terminal and run:
   ```bash
   git clone https://github.com/yourusername/travian-automation-suite.git
   cd travian-automation-suite
Create and Activate a Virtual Environment (recommended)

bash
Copy
python3 -m venv venv
source venv/bin/activate
Install the Required Python Packages

bash
Copy
pip install -r requirements.txt
(If you don't have a requirements.txt, create one with the following contents:)

text
Copy
selenium
webdriver-manager
Setup
Credentials File (Optional):
You can store your Travian login credentials in a file named credentials.txt in the following format:

nginx
Copy
your_username
your_password
When you run the program, it will ask if you want to use these saved credentials.

Buildings File (For Trainer Module):
Create a buildings.txt file with the URLs for your building pages (barracks, stable, workshop). Example:

bash
Copy
barracks=https://ts1.x1.international.travian.com/build.php?gid=19
stable=https://ts1.x1.international.travian.com/build.php?gid=20
workshop=https://ts1.x1.international.travian.com/build.php?gid=21
Tribe File:
After successful tribe detection from your profile, the detected tribe will be saved to tribe.txt.

How to Run
Start the Automation Suite:
Run the main script:

bash
Copy
python3 main.py
Program Flow:

Login:
You will be prompted for your Travian credentials (or use the saved ones from credentials.txt).

Tribe Detection:
After login, the program will navigate to your profile edit page and click the Overview tab to detect your tribe. Confirm the detected tribe to save it in tribe.txt.

Village List Refresh:
You will be asked whether you want to refresh your villages list. If you choose yes, the script will extract village names, coordinates, and IDs, then save them to villages_list.txt.

Task Menu:
You will then see a menu with the following options:

Auto-Farm: Runs the auto-farming routine.
Trainer: Runs the troop training routine.
Both Auto-Farm and Trainer: Runs both tasks concurrently.
Exit: Closes the browser and terminates the program.
Project Structure
main.py
The central script that handles login, tribe detection, village extraction, and the main task menu.

auto_farm.py
Contains the automation code for triggering your farm list at random intervals.

trainer.py
Contains the automation code for troop training based on your tribe and selected options.

villages.py
Contains the code to extract and save the list of villages from the overview page.

credentials.txt (optional)
Stores your Travian username and password.

buildings.txt
Contains URLs for building pages required by the trainer module.

tribe.txt
Automatically generated file that stores your detected tribe.

requirements.txt
Contains the Python package dependencies.

Troubleshooting
Login Issues:
If the login fails, ensure that your credentials are correct. If you encounter CAPTCHA challenges, run the browser in non-headless mode to solve them manually.

Element Not Found Errors:
Travian’s website layout may change. If the script cannot find an element (e.g., the tribe row or village list), inspect the page and update the corresponding XPath or CSS selectors in the code.

License
MIT License