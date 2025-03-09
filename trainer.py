import time
import random
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Sample data: For each tribe, map troop number to a tuple: (troop name, building type)
tribes_data = {
    "Romans": {
       "1": ("Legionnaire", "barracks"),
       "2": ("Imperian", "barracks"),
       "3": ("Praetorian", "barracks"),
       "4": ("Equites Imperatoris", "stable")
    },
    "Teutons": {
       "1": ("Clubswinger", "barracks"),
       "2": ("Spearman", "barracks"),
       "3": ("Axeman", "barracks"),
       "4": ("Scout", "stable")
    },
    "Gauls": {
       "1": ("Phalanx", "barracks"),
       "2": ("Swordsman", "barracks"),
       "3": ("Theutates Thunder", "barracks"),
       "4": ("Haeduan", "stable")
    }
}

def read_building_urls(filename="buildings.txt"):
    """
    Reads building URLs from a text file and returns a dictionary.
    Expected file content (one per line):
      barracks=https://ts1.x1.international.travian.com/build.php?gid=19
      stable=https://ts1.x1.international.travian.com/build.php?gid=20
      workshop=https://ts1.x1.international.travian.com/build.php?gid=21
    """
    building_urls = {}
    if not os.path.exists(filename):
        print(f"[ERROR] {filename} not found!")
        return building_urls
    with open(filename, "r") as f:
        lines = f.read().splitlines()
        for line in lines:
            if "=" in line:
                key, url = line.split("=", 1)
                key = key.strip().lower()
                url = url.strip()
                building_urls[key] = url
    return building_urls

def train_troops(driver, building_url, troop_name, count):
    """
    Simulates training troops.
    In a real script, this function would interact with the page elements.
    Here we navigate to the building URL and print an action message.
    """
    print(f"[INFO] Navigating to {building_url} to train {count} {troop_name}.")
    driver.get(building_url)
    time.sleep(3)  # Wait for page to load
    print(f"[INFO] Training {count} {troop_name} ...")
    time.sleep(2)  # Simulate action delay

def run_trainer(driver):
    """Main function to run the troop training automation."""
    
    # === Step 1: Choose tribe ===
    print("Available Tribes:")
    for idx, tribe in enumerate(tribes_data.keys(), start=1):
        print(f"{idx}. {tribe}")
    tribe_choice = input("Select your tribe (enter number): ").strip()
    try:
        tribe_choice = int(tribe_choice)
    except ValueError:
        print("[ERROR] Invalid input. Exiting.")
        return
    tribe_list = list(tribes_data.keys())
    if tribe_choice < 1 or tribe_choice > len(tribe_list):
        print("[ERROR] Invalid tribe selection. Exiting.")
        return
    selected_tribe = tribe_list[tribe_choice - 1]
    print(f"[INFO] You selected: {selected_tribe}")
    
    # === Step 2: List available troops and choose which ones to train ===
    troop_options = tribes_data[selected_tribe]
    print("Available Troops:")
    for num, (troop_name, building) in troop_options.items():
        print(f"{num}. {troop_name} (Trained in {building})")
    troop_selection = input("Enter troop numbers to train (comma separated): ").strip()
    selected_troops = []
    for part in troop_selection.split(","):
        part = part.strip()
        if part in troop_options:
            selected_troops.append(troop_options[part])
        else:
            print(f"[WARNING] Invalid troop number: {part}")
    if not selected_troops:
        print("[ERROR] No valid troop selected. Exiting.")
        return
    
    # === Step 3: Choose building(s) to use for training ===
    print("Select building(s) to use for training:")
    print("1. Barracks")
    print("2. Stable")
    print("3. Workshop")
    print("4. All")
    building_choice = input("Enter your choice (1/2/3/4): ").strip()
    valid_buildings = []
    if building_choice == "1":
        valid_buildings = ["barracks"]
    elif building_choice == "2":
        valid_buildings = ["stable"]
    elif building_choice == "3":
        valid_buildings = ["workshop"]
    elif building_choice == "4":
        valid_buildings = ["barracks", "stable", "workshop"]
    else:
        print("[ERROR] Invalid building choice. Exiting.")
        return
    
    # === Step 4: Choose training option and timing ===
    print("Select training option:")
    print("1. Small amounts (30-45 minutes / 20-50 troops)")
    print("2. Medium amounts (90-120 minutes / 100-250 troops)")
    print("3. Large amounts")
    training_option = input("Enter your option (1/2/3): ").strip()
    
    min_time = max_time = 0
    min_troops = max_troops = 0
    use_great_building = False
    great_building_choice = []
    
    if training_option == "1":
        min_time, max_time = 30, 45
        min_troops, max_troops = 20, 50
    elif training_option == "2":
        min_time, max_time = 90, 120
        min_troops, max_troops = 100, 250
    elif training_option == "3":
        print("Large amounts training options:")
        print("A. Enter troop amounts manually")
        print("B. Use Great Building training (Great Barracks/Great Stable)")
        sub_option = input("Select sub-option (A/B): ").strip().upper()
        if sub_option == "A":
            try:
                min_troops = int(input("Enter minimum troop count: ").strip())
                max_troops = int(input("Enter maximum troop count: ").strip())
                min_time, max_time = 180, 360
            except ValueError:
                print("[ERROR] Invalid input for troop counts. Exiting.")
                return
        elif sub_option == "B":
            use_great_building = True
            print("Select Great Building to use for training:")
            print("1. Great Barracks")
            print("2. Great Stable")
            print("3. Both")
            gb_choice = input("Enter your choice (1/2/3): ").strip()
            if gb_choice == "1":
                great_building_choice = ["barracks"]
            elif gb_choice == "2":
                great_building_choice = ["stable"]
            elif gb_choice == "3":
                great_building_choice = ["barracks", "stable"]
            else:
                print("[ERROR] Invalid great building choice. Exiting.")
                return
            try:
                min_time = int(input("Enter minimum training time in minutes: ").strip())
                max_time = int(input("Enter maximum training time in minutes: ").strip())
            except ValueError:
                print("[ERROR] Invalid input for training time. Exiting.")
                return
            min_troops, max_troops = 500, 2000
        else:
            print("[ERROR] Invalid sub-option. Exiting.")
            return
    else:
        print("[ERROR] Invalid training option. Exiting.")
        return

    training_time = random.randint(min_time, max_time)
    troop_count = random.randint(min_troops, max_troops)
    
    print(f"[INFO] Training will occur every {training_time} minutes, training {troop_count} troops each cycle.")
    
    building_urls = read_building_urls()
    if not building_urls:
        print("[ERROR] Building URLs not loaded. Exiting.")
        return

    # Training cycle (a single cycle for demonstration; you can wrap this in a loop if desired).
    for troop_name, troop_building in selected_troops:
        if use_great_building:
            if troop_building in great_building_choice:
                url = building_urls.get(troop_building)
                if url:
                    train_troops(driver, url, troop_name, troop_count)
                else:
                    print(f"[ERROR] URL for {troop_building} not found.")
            else:
                print(f"[INFO] Skipping {troop_name} (trained in {troop_building}) due to great building selection.")
        else:
            if troop_building in valid_buildings:
                url = building_urls.get(troop_building)
                if url:
                    train_troops(driver, url, troop_name, troop_count)
                else:
                    print(f"[ERROR] URL for {troop_building} not found.")
            else:
                print(f"[INFO] Skipping {troop_name} (trained in {troop_building}) as it is not in the selected buildings.")
    
    print(f"[INFO] Waiting {training_time} minutes until next training cycle...")
    time.sleep(training_time * 60)
    print("[INFO] Training cycle completed. Exiting trainer.")

if __name__ == "__main__":
    # For standalone testing.
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920x1080")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    run_trainer(driver)
