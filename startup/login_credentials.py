import os

def get_credentials():
    """
    Reads credentials from 'credentials.txt' if available.
    If found, asks if you want to use them.
    Otherwise, prompts for credentials and offers to save them.
    """
    if os.path.exists("credentials.txt"):
        with open("credentials.txt", "r") as file:
            lines = file.read().splitlines()
            if len(lines) >= 2:
                saved_username = lines[0].strip()
                saved_password = lines[1].strip()
                use_file = input("Found saved credentials. Use them? (y/n): ").strip().lower()
                if use_file == 'y':
                    return saved_username, saved_password
    username = input("Enter your Travian username: ")
    password = input("Enter your Travian password: ")
    save = input("Save these credentials for future use? (y/n): ").strip().lower()
    if save == 'y':
        with open("credentials.txt", "w") as file:
            file.write(username + "\n")
            file.write(password + "\n")
    return username, password
