import time
import random
from tasks.trainer.trainer_data import read_building_urls, read_troop_mappings
from tasks.trainer.trainer_actions import train_troops

def get_account_tribe(filepath="info/profile/tribe.txt"):
    """
    Reads the account tribe from the specified file.
    Expected format: "Tribe,ProfileID"
    Returns the tribe as a string.
    """
    try:
        with open(filepath, "r") as f:
            data = f.read().strip()
            if not data:
                print("[ERROR] Tribe file is empty! Please update your profile first.")
                return None
            parts = data.split(",")
            return parts[0].strip() if parts else None
    except Exception as e:
        print(f"[ERROR] Unable to read tribe file: {e}")
        return None

def run_trainer(driver):
    """
    Main function to run the troop training automation.
    - Reads the user's tribe from `tribe.txt`.
    - Filters the troop list based on the user's tribe.
    """
    # Step 1: Get the user's tribe
    account_tribe = get_account_tribe("info/profile/tribe.txt")
    if not account_tribe:
        print("[ERROR] Unable to determine account tribe. Exiting trainer.")
        return

    print(f"[INFO] Account tribe: {account_tribe}")

    # Step 2: Load troop mappings & filter based on tribe
    troops_map = read_troop_mappings("info/maps/troops-maps.txt")
    filtered_troops = [(troop_type, building, troop_number) for troop_type, building, troop_number, tribe in troops_map if tribe.lower() == account_tribe.lower()]

    if not filtered_troops:
        print(f"[ERROR] No troop data found for tribe: {account_tribe}. Exiting trainer.")
        return

    # Step 3: Display filtered troops for selection
    print("\nAvailable Troops:")
    for idx, (troop_type, building, troop_number) in enumerate(filtered_troops, start=1):
        print(f"{idx}. {troop_type} (Trained in {building}, Input name: {troop_number})")

    selection = input("Enter the numbers of the troops to train (comma separated): ").strip()
    selected_indices = [int(idx.strip()) - 1 for idx in selection.split(",") if idx.strip().isdigit()]

    if not selected_indices:
        print("[ERROR] No valid troops selected. Exiting trainer.")
        return

    selected_troops = [filtered_troops[i] for i in selected_indices]

    # Step 4: Training parameters
    min_time, max_time = 30, 60
    min_troops, max_troops = 20, 100
    training_time = random.randint(min_time, max_time)
    troop_count = random.randint(min_troops, max_troops)

    print(f"[INFO] Training will occur every {training_time} minutes, training {troop_count} troops each cycle.")

    # Step 5: Load building URLs & train selected troops
    building_urls = read_building_urls("info/maps/buildings.txt")
    if not building_urls:
        print("[ERROR] Building URLs not loaded. Exiting trainer.")
        return

    for troop_type, building, troop_number in selected_troops:
        url = building_urls.get(building)
        if url:
            train_troops(driver, url, troop_number, troop_type, troop_count)
        else:
            print(f"[ERROR] URL for building '{building}' not found.")

    print(f"[INFO] Waiting {training_time} minutes until next training cycle...")
    time.sleep(training_time * 60)
