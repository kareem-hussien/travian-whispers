import time

def welcome():
    """Displays welcome messages with a loading effect."""
    messages = [
        "Travian Whispers",
        "made by Eng. Kareem Hussien",
        "WhatsApp : https://wa.me/00201099339393"
    ]
    for message in messages:
        print(message, end='', flush=True)
        for i in range(5):
            print(" .", end='', flush=True)
            time.sleep(0.6)  # 0.6 sec per dot gives ~3 seconds total per message.
        print()  # New line after each message.
