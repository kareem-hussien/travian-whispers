import threading
from tasks.auto_farm import run_auto_farm
from tasks.trainer import run_trainer

# Dictionary to keep track of running tasks
running_tasks = {}

def start_tasks(driver, task_name, run_auto_farm_flag=False, run_trainer_flag=False):
    """
    Starts selected tasks and keeps them in memory.
    If a task is already running, it won't start again.
    """
    global running_tasks

    if task_name in running_tasks:
        print(f"[WARNING] Task '{task_name}' is already running!")
        return

    threads = []
    if run_auto_farm_flag and "Auto-Farm" not in running_tasks:
        t_af = threading.Thread(target=run_auto_farm, args=(driver,), daemon=True)
        threads.append(t_af)
        running_tasks["Auto-Farm"] = t_af
    if run_trainer_flag and "Trainer" not in running_tasks:
        t_tr = threading.Thread(target=run_trainer, args=(driver,), daemon=True)
        threads.append(t_tr)
        running_tasks["Trainer"] = t_tr
    
    for t in threads:
        t.start()

    print(f"[INFO] Task '{task_name}' started successfully!")

def stop_task(task_name):
    """
    Stops a running task.
    """
    global running_tasks
    if task_name in running_tasks:
        print(f"[INFO] Stopping task: {task_name}")
        del running_tasks[task_name]
    else:
        print(f"[ERROR] Task '{task_name}' is not running.")

def list_tasks():
    """
    Lists currently running tasks.
    """
    if not running_tasks:
        print("[INFO] No tasks running.")
    else:
        print("\n[INFO] Currently Running Tasks:")
        for task in running_tasks.keys():
            print(f"- {task}")

def run_task_menu(driver):
    """
    Displays the main task menu and allows users to start multiple tasks.
    """
    while True:
        print("\n=== Travian Automation Suite ===")
        print("1. Start Auto-Farm")
        print("2. Start Trainer")
        print("3. Start Both Auto-Farm and Trainer")
        print("4. List Running Tasks")
        print("5. Stop a Task")
        print("6. Exit")
        choice = input("Enter your option (1/2/3/4/5/6): ").strip()
        
        if choice == "1":
            start_tasks(driver, "Auto-Farm", run_auto_farm_flag=True, run_trainer_flag=False)
        elif choice == "2":
            start_tasks(driver, "Trainer", run_auto_farm_flag=False, run_trainer_flag=True)
        elif choice == "3":
            start_tasks(driver, "Both", run_auto_farm_flag=True, run_trainer_flag=True)
        elif choice == "4":
            list_tasks()
        elif choice == "5":
            task_name = input("Enter the task name to stop (Auto-Farm / Trainer): ").strip()
            stop_task(task_name)
        elif choice == "6":
            print("[INFO] Exiting... Closing browser.")
            driver.quit()
            break
        else:
            print("[ERROR] Invalid choice. Please enter a valid option.")
