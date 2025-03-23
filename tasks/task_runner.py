"""
Task Runner module for Travian Whispers application.
This module provides a centralized system for running automated tasks with
proper session isolation and IP management.
"""
import time
import logging
import threading
from datetime import datetime, timedelta
from queue import Queue, Empty

from startup.browser_profile import setup_browser, login
from startup.session_isolation import BrowserIsolationManager
from startup.ip_manager import IPManager
from tasks.auto_farm import run_auto_farm
from tasks.trainer.trainer_main import run_trainer

# Configure logger
logger = logging.getLogger(__name__)

class TaskRunner:
    """
    Task runner for automated Travian operations with session isolation.
    """
    
    def __init__(self):
        """Initialize TaskRunner."""
        self.ip_manager = IPManager()
        self.browser_manager = BrowserIsolationManager()
        self.task_queue = Queue()
        self.active_tasks = {}
        self.stop_event = threading.Event()
        self.worker_thread = None
    
    def start(self):
        """Start the task runner."""
        if self.worker_thread and self.worker_thread.is_alive():
            logger.warning("Task runner is already running")
            return False
        
        # Clear stop event
        self.stop_event.clear()
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        logger.info("Task runner started")
        return True
    
    def stop(self):
        """Stop the task runner."""
        if not self.worker_thread or not self.worker_thread.is_alive():
            logger.warning("Task runner is not running")
            return False
        
        # Set stop event
        self.stop_event.set()
        
        # Wait for worker thread to finish
        self.worker_thread.join(timeout=60)
        
        if self.worker_thread.is_alive():
            logger.warning("Worker thread did not stop gracefully")
        
        logger.info("Task runner stopped")
        return True
    
    def schedule_task(self, task_type, user_id, params=None, delay=0):
        """
        Schedule a task for execution.
        
        Args:
            task_type (str): Type of task ('auto_farm', 'trainer', etc.)
            user_id (str): User ID
            params (dict, optional): Task parameters
            delay (int, optional): Delay before execution (seconds)
            
        Returns:
            str: Task ID or None if error
        """
        from uuid import uuid4
        task_id = str(uuid4())
        
        # Create task
        task = {
            "id": task_id,
            "type": task_type,
            "user_id": user_id,
            "params": params or {},
            "status": "scheduled",
            "scheduled_at": datetime.utcnow(),
            "execute_at": datetime.utcnow() + timedelta(seconds=delay),
            "completed_at": None,
            "result": None
        }
        
        # Add to active tasks
        self.active_tasks[task_id] = task
        
        # Add to queue
        self.task_queue.put(task)
        
        logger.info(f"Scheduled {task_type} task for user {user_id} with ID {task_id}")
        
        return task_id
    
    def get_task_status(self, task_id):
        """
        Get the status of a task.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            dict: Task status or None if not found
        """
        return self.active_tasks.get(task_id)
    
    def cancel_task(self, task_id):
        """
        Cancel a scheduled task.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            bool: True if task was cancelled, False otherwise
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found")
            return False
        
        task = self.active_tasks[task_id]
        
        if task["status"] != "scheduled":
            logger.warning(f"Task {task_id} cannot be cancelled (status: {task['status']})")
            return False
        
        # Update task status
        task["status"] = "cancelled"
        task["completed_at"] = datetime.utcnow()
        
        logger.info(f"Cancelled task {task_id}")
        
        return True
    
    def _worker_loop(self):
        """
        Main worker loop.
        This runs in a separate thread and processes tasks from the queue.
        """
        logger.info("Worker loop started")
        
        while not self.stop_event.is_set():
            try:
                # Get the next task (block for 1 second)
                try:
                    task = self.task_queue.get(timeout=1)
                except Empty:
                    # No tasks in queue, continue
                    continue
                
                # Check if task should be executed now
                if task["execute_at"] > datetime.utcnow():
                    # Not time yet, put it back in the queue
                    self.task_queue.put(task)
                    time.sleep(1)
                    continue
                
                # Check if task was cancelled
                if task["status"] == "cancelled":
                    logger.info(f"Skipping cancelled task {task['id']}")
                    self.task_queue.task_done()
                    continue
                
                # Update task status
                task["status"] = "running"
                
                # Execute task
                logger.info(f"Executing task {task['id']} ({task['type']}) for user {task['user_id']}")
                
                try:
                    # Execute task by type
                    if task["type"] == "auto_farm":
                        result = self._execute_auto_farm(task)
                    elif task["type"] == "trainer":
                        result = self._execute_trainer(task)
                    else:
                        logger.error(f"Unknown task type: {task['type']}")
                        result = {"status": "error", "message": f"Unknown task type: {task['type']}"}
                    
                    # Update task result
                    task["result"] = result
                    
                    # Check if task should be rescheduled (continuous tasks)
                    if task["params"].get("continuous", False) and result.get("status") != "error":
                        # Calculate next execution time
                        delay = task["params"].get("interval", 3600)  # Default 1 hour
                        next_time = datetime.utcnow() + timedelta(seconds=delay)
                        
                        # Create new task
                        new_task = task.copy()
                        new_task["id"] = str(uuid4())
                        new_task["status"] = "scheduled"
                        new_task["scheduled_at"] = datetime.utcnow()
                        new_task["execute_at"] = next_time
                        new_task["completed_at"] = None
                        new_task["result"] = None
                        
                        # Add to active tasks
                        self.active_tasks[new_task["id"]] = new_task
                        
                        # Add to queue
                        self.task_queue.put(new_task)
                        
                        logger.info(f"Rescheduled {task['type']} task for user {task['user_id']} with ID {new_task['id']}")
                    
                except Exception as e:
                    logger.error(f"Error executing task {task['id']}: {e}")
                    task["result"] = {"status": "error", "message": str(e)}
                
                # Update task status
                task["status"] = "completed"
                task["completed_at"] = datetime.utcnow()
                
                # Mark task as done in queue
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)
        
        logger.info("Worker loop stopped")
    
    def _execute_auto_farm(self, task):
        """
        Execute an auto_farm task.
        
        Args:
            task (dict): Task data
            
        Returns:
            dict: Task result
        """
        user_id = task["user_id"]
        
        # Get parameters
        max_runtime = task["params"].get("max_runtime", 3600)  # Default 1 hour
        interval_min = task["params"].get("interval_min", 1800)  # Default 30 minutes
        interval_max = task["params"].get("interval_max", 2700)  # Default 45 minutes
        
        # Get user credentials
        from database.models.user import User
        user_model = User()
        user = user_model.get_user_by_id(user_id)
        
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Get Travian credentials
        username = user["travianCredentials"].get("username")
        password = user["travianCredentials"].get("password")
        server = user["travianCredentials"].get("server", "https://ts1.x1.international.travian.com")
        
        if not username or not password:
            return {"status": "error", "message": "Travian credentials not set"}
        
        # Setup browser with isolation
        driver = None
        try:
            driver = setup_browser(user_id)
            
            # Login to Travian
            if not login(driver, username, password, server):
                return {"status": "error", "message": "Login failed"}
            
            # Run auto farm
            result = run_auto_farm(driver, user_id, max_runtime, (interval_min, interval_max))
            
            # Check if rotation is required
            if result.get("status") == "rotation_required":
                # A rotation has already been performed, but we need to restart the browser
                return {
                    "status": "rotation_performed",
                    "message": "IP or session rotation performed, browser restart required",
                    "rotation_info": result.get("rotation_info"),
                    "original_result": result
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in auto_farm task: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            # Close browser
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _execute_trainer(self, task):
        """
        Execute a trainer task.
        
        Args:
            task (dict): Task data
            
        Returns:
            dict: Task result
        """
        user_id = task["user_id"]
        
        # Get parameters
        max_runtime = task["params"].get("max_runtime", 3600)  # Default 1 hour
        interval_min = task["params"].get("interval_min", 1800)  # Default 30 minutes
        interval_max = task["params"].get("interval_max", 3600)  # Default 60 minutes
        
        # Get user credentials
        from database.models.user import User
        user_model = User()
        user = user_model.get_user_by_id(user_id)
        
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Get Travian credentials
        username = user["travianCredentials"].get("username")
        password = user["travianCredentials"].get("password")
        server = user["travianCredentials"].get("server", "https://ts1.x1.international.travian.com")
        
        if not username or not password:
            return {"status": "error", "message": "Travian credentials not set"}
        
        # Setup browser with isolation
        driver = None
        try:
            driver = setup_browser(user_id)
            
            # Login to Travian
            if not login(driver, username, password, server):
                return {"status": "error", "message": "Login failed"}
            
            # Run trainer
            result = run_trainer(driver, user_id, max_runtime, (interval_min, interval_max))
            
            # Check if rotation is required
            if result.get("status") == "rotation_required":
                # A rotation has already been performed, but we need to restart the browser
                return {
                    "status": "rotation_performed",
                    "message": "IP or session rotation performed, browser restart required",
                    "rotation_info": result.get("rotation_info"),
                    "original_result": result
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in trainer task: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            # Close browser
            if driver:
                try:
                    driver.quit()
                except:
                    pass

# Create a singleton instance
task_runner = TaskRunner()
