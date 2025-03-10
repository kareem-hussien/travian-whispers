import os

# Sample troop map data is now provided via an external file,
# so this file may be used for any additional static data if needed.
# For now, we only need the function to read building URLs.
def read_building_urls(filename="info/maps/buildings.txt"):
    """
    Reads building URLs from the specified file and returns a dictionary.
    Expected file format (one per line):
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
                building_urls[key.strip().lower()] = url.strip()
    return building_urls
