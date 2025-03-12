"""
Task management module with MongoDB integration.
"""
import threading
import logging
from tasks.auto_farm import run_auto_farm
from tasks.trainer import run_trainer
from database.models.user import User

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('startup.tasks')

# Dictionary to keep track of running tasks
running_tasks = {}

def start_tasks(driver, task_name, user_id, max_tasks, run_auto_farm_flag=False, run_trainer_flag=False):
    """
    Starts selected tasks and keeps them in memory.
    If a task is already running, it won't start again.
    
    Args:
        driver: Selenium WebDriver instance
        task_name: Name of the task ("Auto-Farm", "Trainer", or "Both")
        user_id: MongoDB user ID
        max_tasks: Maximum number of tasks allowed by subscription
        run_auto_farm_flag: Whether to run auto farm
        run_trainer_flag: Whether to run trainer
    """
    global running_tasks
    
    # Initialize user's running tasks if not exist
    if user_id not in running_tasks:
        running_tasks[user_id] = {}
    
    # Check if task is already running
    if task_name in running_tasks[user_id]:
        logger.warning(f"Task '{task_name}' is already running!")
        return
    
    # Check maximum tasks limit
    if len(running_tasks[user_id]) >= max_tasks:
        logger.warning(f"Maximum number of tasks ({max_tasks}) already running. Please upgrade your subscription for more tasks.")
        return
    
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        logger.error(f"User not found: {user_id}")
        return
    
    # Check user villages (needed for both tasks)
    if not user['villages'] or len(user['villages']) == 0:
        logger.error("No villages found. Please update your profile first.")
        return
    
    threads = []
    
    if run_auto_farm_flag and "Auto-Farm" not in running_tasks[user_id]:
        t_af = threading.Thread(
            target=run_auto_farm, 
            args=(driver, user['villages']), 
            daemon=True
        )
        threads.append(t_af)
        running_tasks[user_id]["Auto-Farm"] = t_af
    
    if run_trainer_flag and "Trainer" not in running_tasks[user_id]:
        t_tr = threading.Thread(
            target=run_trainer, 
            args=(
                driver, 
                user['villages'], 
                user['travianCredentials']['tribe']
            ), 
            daemon=True
        )
        threads.append(t_tr)
        running_tasks[user_id]["Trainer"] = t_tr
    
    for t in threads:
        t.start()
    
    logger.info(f"Task '{task_name}' started successfully!")

def stop_task(user_id, task_name):
    """
    Stops a running task.
    
    Args:
        user_id: MongoDB user ID
        task_name: Name of the task to stop
    """
    global running_tasks
    
    if user_id not in running_tasks:
        logger.error(f"No tasks running for user: {user_id}")
        return
    
    if task_name in running_tasks[user_id]:
        logger.info(f"Stopping task: {task_name}")
        # We can't actually stop the thread, but we can remove it from our tracking
        del running_tasks[user_id][task_name]
        
        # Remove user from tracking if no tasks running
        if len(running_tasks[user_id]) == 0:
            del running_tasks[user_id]
    else:
        logger.error(f"Task '{task_name}' is not running.")

def list_tasks(user_id):
    """
    Lists currently running tasks for a user.
    
    Args:
        user_id: MongoDB user ID
    """
    if user_id not in running_tasks or len(running_tasks[user_id]) == 0:
        logger.info("No tasks running.")
        return []
    
    logger.info("\nCurrently Running Tasks:")
    for task in running_tasks[user_id].keys():
        logger.info(f"- {task}")
    
    return list(running_tasks[user_id].keys())

def run_task_menu(driver, user_id, max_tasks, available_features):
    """
    Displays the main task menu and allows users to start multiple tasks.
    
    Args:
        driver: Selenium WebDriver instance
        user_id: MongoDB user ID
        max_tasks: Maximum number of tasks allowed by subscription
        available_features: List of available features based on subscription
    """
    while True:
        print("\n=== Travian Whispers Automation Suite ===")
        
        # Show available options based on subscription
        options = []
        can_run_auto_farm = "Auto-Farm" in available_features
        can_run_trainer = "Trainer" in available_features
        
        if can_run_auto_farm:
            print("1. Start Auto-Farm")
            options.append("1")
        
        if can_run_trainer:
            print("2. Start Trainer")
            options.append("2")
        
        if can_run_auto_farm and can_run_trainer:
            print("3. Start Both Auto-Farm and Trainer")
            options.append("3")
        
        print("4. List Running Tasks")
        print("5. Stop a Task")
        print("6. Exit")
        
        choice = input(f"Enter your option ({'/'.join(options + ['4', '5', '6'])}): ").strip()
        
        if choice == "1" and can_run_auto_farm:
            start_tasks(
                driver, 
                "Auto-Farm", 
                user_id, 
                max_tasks, 
                run_auto_farm_flag=True, 
                run_trainer_flag=False
            )
        elif choice == "2" and can_run_trainer:
            start_tasks(
                driver, 
                "Trainer", 
                user_id, 
                max_tasks, 
                run_auto_farm_flag=False, 
                run_trainer_flag=True
            )
        elif choice == "3" and can_run_auto_farm and can_run_trainer:
            start_tasks(
                driver, 
                "Both", 
                user_id, 
                max_tasks, 
                run_auto_farm_flag=True, 
                run_trainer_flag=True
            )
        elif choice == "4":
            list_tasks(user_id)
        elif choice == "5":
            # List tasks for user to choose
            running = list_tasks(user_id)
            
            if running:
                task_name = input("Enter the task name to stop (Auto-Farm / Trainer): ").strip()
                stop_task(user_id, task_name)
            else:
                print("No tasks running to stop.")
        elif choice == "6":
            print("Exiting... Closing browser.")
            driver.quit()
            break
        else:
            print("Invalid choice. Please enter a valid option.")
