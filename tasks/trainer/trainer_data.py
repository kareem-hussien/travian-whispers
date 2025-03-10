import os

def read_building_urls(filename="info/maps/buildings.txt"):
    """
    Reads building URLs from the specified file.
    """
    building_urls = {}
    if not os.path.exists(filename):
        print(f"[ERROR] {filename} not found!")
        return building_urls
    with open(filename, "r") as f:
        for line in f.read().splitlines():
            if "=" in line:
                key, url = line.split("=", 1)
                building_urls[key.strip().lower()] = url.strip()
    return building_urls

def read_troop_mappings(filename="info/maps/troops-maps.txt"):
    """
    Reads the troop mappings and extracts the correct troop input names.
    Expected format: Tribe-Building-[troop_number]-Troop Type
    Returns a list of tuples (troop_type, building, troop_number, tribe).
    """
    troop_mappings = []
    if not os.path.exists(filename):
        print(f"[ERROR] {filename} not found!")
        return troop_mappings
    with open(filename, "r") as f:
        for line in f.read().splitlines():
            parts = line.split("-")
            if len(parts) < 4:
                continue
            tribe = parts[0].strip()
            building = parts[1].strip()
            troop_number = parts[2].strip().replace("[", "").replace("]", "")  # Extract "tX"
            troop_type = parts[3].strip()
            troop_mappings.append((troop_type, building, troop_number, tribe))
    return troop_mappings
