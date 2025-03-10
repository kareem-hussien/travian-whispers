import time
import random
from tasks.trainer.trainer_data import read_building_urls
from tasks.trainer.trainer_actions import train_troops

def get_account_tribe(filepath="info/profile/tribe.txt"):
    """
    Reads the account tribe from the specified file.
    Expected format: "Tribe,ProfileID"
    Returns the tribe as a string, or None if not found.
    """
    try:
        with open(filepath, "r") as f:
            data = f.read().strip()
            if not data:
                print("[ERROR] Tribe file is empty! Please update your profile first.")
                return None
            parts = data.split(",")
            if len(parts) < 1 or not parts[0].strip():
                print("[ERROR] Tribe data is missing in the file!")
                return None
            return parts[0].strip()
    except Exception as e:
        print(f"[ERROR] Unable to read tribe file: {e}")
        return None

def run_trainer(driver):
    """
    Main function to run the troop training automation.
    Automatically reads the account tribe from 'info/profile/tribe.txt' and loads the available troops
    from the 'info/maps/troops-maps.txt' file. The mapping file should have lines in the format:
       Tribe-Building-[icon]-Troop Type
    For example:
       Romans-barracks-[tid1]-Legionnaire
       Romans-barracks-[tid2]-Praetorian
       Romans-barracks-[tid3]-Imperian

    The script then:
      1. Displays available troops for the account's tribe.
      2. Lets the user select which troops to train (by number).
      3. Asks for a training option (which determines random time and troop count).
      4. For each selected troop, looks up the building from the troops map and then finds the building URL from 'info/maps/buildings.txt'.
      5. Calls the training action to set the troop count.
    """
    # Step 1: Get account tribe automatically
    account_tribe = get_account_tribe("info/profile/tribe.txt")
    if not account_tribe:
        print("[ERROR] Unable to determine account tribe. Exiting trainer.")
        return

    print(f"[INFO] Account tribe: {account_tribe}")

    # Step 2: Load available troops for this tribe from troops-maps.txt
    troops = []
    troops_map_file = "info/maps/troops-maps.txt"
    try:
        with open(troops_map_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Expected format: Tribe-Building-[icon]-Troop Type
                parts = line.split("-")
                if len(parts) < 4:
                    continue
                line_tribe = parts[0].strip()
                building = parts[1].strip()
                icon = parts[2].strip()
                troop_type = "-".join(parts[3:]).strip()
                if line_tribe.lower() == account_tribe.lower():
                    troops.append((troop_type, building, icon))
    except Exception as e:
        print(f"[ERROR] Could not read troops map: {e}")
        return

    if not troops:
        print(f"[ERROR] No troop data found for tribe: {account_tribe}.")
        return

    # Step 3: Display available troops and let user select
    print("Available Troops:")
    for idx, (troop_type, building, icon) in enumerate(troops, start=1):
        print(f"{idx}. {troop_type} (Trained in {building})")
    
    selection = input("Enter the numbers of the troops to train (comma separated): ").strip()
    selected_indices = []
    try:
        for part in selection.split(","):
            index = int(part.strip())
            if 1 <= index <= len(troops):
                selected_indices.append(index - 1)
            else:
                print(f"[WARNING] Invalid option: {part}")
    except Exception as e:
        print(f"[ERROR] Invalid input: {e}")
        return

    if not selected_indices:
        print("[ERROR] No valid troops selected. Exiting trainer.")
        return

    selected_troops = [troops[i] for i in selected_indices]

    # Step 4: Choose training option and timing
    print("Select training option:")
    print("1. Small amounts (30-45 minutes / 20-50 troops)")
    print("2. Medium amounts (90-120 minutes / 100-250 troops)")
    print("3. Large amounts")
    training_option = input("Enter your option (1/2/3): ").strip()

    min_time = max_time = 0
    min_troops = max_troops = 0
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
            # In this design, we don't ask for extra building selection
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

    # Step 5: Read building URLs from info/maps/buildings.txt
    from tasks.trainer.trainer_data import read_building_urls
    building_urls = read_building_urls("info/maps/buildings.txt")
    if not building_urls:
        print("[ERROR] Building URLs not loaded. Exiting.")
        return

    # Step 6: For each selected troop, determine the building URL and train the troops
    for troop_type, building, icon in selected_troops:
        url = building_urls.get(building)
        if url:
            train_troops(driver, url, troop_type, troop_count)
        else:
            print(f"[ERROR] URL for building '{building}' not found.")

    print(f"[INFO] Waiting {training_time} minutes until next training cycle...")
    time.sleep(training_time * 60)
    print("[INFO] Training cycle completed. Exiting trainer.")
