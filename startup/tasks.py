import threading
from tasks.auto_farm import run_auto_farm
from tasks.trainer import run_trainer


def start_tasks(driver, run_auto_farm_flag, run_trainer_flag):
    """
    Starts selected tasks in separate threads.
    """
    threads = []
    if run_auto_farm_flag:
        t_af = threading.Thread(target=run_auto_farm, args=(driver,), daemon=True)
        threads.append(t_af)
    if run_trainer_flag:
        t_tr = threading.Thread(target=run_trainer, args=(driver,), daemon=True)
        threads.append(t_tr)
    
    for t in threads:
        t.start()
    
    print("[INFO] Tasks have been saved and are running concurrently!")
    for t in threads:
        t.join()

def run_task_menu(driver):
    """
    Displays the main task menu (Auto-Farm, Trainer, Both, or Exit)
    and calls start_tasks() based on the user's choice.
    """
    while True:
        print("\n=== Travian Automation Suite ===")
        print("1. Start Auto-Farm")
        print("2. Start Trainer")
        print("3. Both Auto-Farm and Trainer")
        print("4. Exit")
        choice = input("Enter your option (1/2/3/4): ").strip()
        
        if choice == "1":
            start_tasks(driver, run_auto_farm_flag=True, run_trainer_flag=False)
        elif choice == "2":
            start_tasks(driver, run_auto_farm_flag=False, run_trainer_flag=True)
        elif choice == "3":
            start_tasks(driver, run_auto_farm_flag=True, run_trainer_flag=True)
        elif choice == "4":
            print("[INFO] Exiting... Closing browser.")
            driver.quit()
            break
        else:
            print("[ERROR] Invalid choice. Please enter a valid option.")
