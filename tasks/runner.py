# File: tasks/runner.py

import logging
import threading
import time
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class TaskRunner:
    """
    Task Runner for managing background automation tasks.
    """
    
    def __init__(self, user_id=None):
        """
        Initialize the Task Runner.
        
        Args:
            user_id (str, optional): User ID for database operations
        """
        self.user_id = user_id
        self.tasks = {}
        self.selenium_handlers = {}
        self.running = False
    
    def add_task(self, task_name, task_class, *args, **kwargs):
        """
        Add a task to the runner.
        
        Args:
            task_name (str): Unique name for the task
            task_class: Task class to instantiate
            *args, **kwargs: Arguments to pass to the task constructor
            
        Returns:
            bool: True if task added successfully, False otherwise
        """
        if task_name in self.tasks:
            logger.warning(f"Task {task_name} already exists")
            return False
        
        try:
            # Create a new Selenium WebDriver for each task
            from utils.selenium_handler import SeleniumHandler
            
            # Reuse selenium handler if exists for this task type
            if task_name not in self.selenium_handlers:
                selenium_handler = SeleniumHandler()
                driver = selenium_handler.create_driver(user_id=self.user_id)
                self.selenium_handlers[task_name] = {
                    'handler': selenium_handler,
                    'driver': driver
                }
            
            # Initialize the task with the driver
            task_instance = task_class(
                self.selenium_handlers[task_name]['driver'],
                user_id=self.user_id,
                *args, **kwargs
            )
            
            # Store the task and its thread
            self.tasks[task_name] = {
                'instance': task_instance,
                'thread': None,
                'started_at': None,
                'status': 'idle'
            }
            
            logger.info(f"Task {task_name} added")
            return True
            
        except Exception as e:
            logger.error(f"Error adding task {task_name}: {e}")
            return False
    
    def start_task(self, task_name, *args, **kwargs):
        """
        Start a task in a separate thread.
        
        Args:
            task_name (str): Name of the task to start
            *args, **kwargs: Arguments to pass to the task's run method
            
        Returns:
            bool: True if task started successfully, False otherwise
        """
        if task_name not in self.tasks:
            logger.warning(f"Task {task_name} not found")
            return False
        
        task = self.tasks[task_name]
        
        if task['thread'] is not None and task['thread'].is_alive():
            logger.warning(f"Task {task_name} is already running")
            return False
        
        try:
            # Create a new thread for the task
            task_thread = threading.Thread(
                target=self._run_task,
                args=(task_name, args, kwargs),
                daemon=True
            )
            
            # Store the thread and start it
            task['thread'] = task_thread
            task['started_at'] = datetime.now()
            task['status'] = 'running'
            
            task_thread.start()
            
            logger.info(f"Task {task_name} started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting task {task_name}: {e}")
            task['status'] = 'error'
            return False
    
    def _run_task(self, task_name, args, kwargs):
        """
        Run a task and handle exceptions.
        
        Args:
            task_name (str): Name of the task to run
            args, kwargs: Arguments to pass to the task's run method
        """
        task = self.tasks[task_name]
        
        try:
            # Run the task
            logger.info(f"Running task {task_name}")
            result = task['instance'].run(*args, **kwargs)
            
            # Update task status
            if result:
                task['status'] = 'completed'
                logger.info(f"Task {task_name} completed successfully")
            else:
                task['status'] = 'failed'
                logger.warning(f"Task {task_name} failed")
            
        except Exception as e:
            logger.error(f"Error in task {task_name}: {e}")
            task['status'] = 'error'
            
            # Log activity if possible
            if self.user_id:
                try:
                    from database.models.activity_log import ActivityLog
                    
                    activity_model = ActivityLog()
                    activity_model.log_activity(
                        user_id=self.user_id,
                        activity_type=task_name.lower(),
                        details=f"Task error: {str(e)}",
                        status='error'
                    )
                except ImportError:
                    pass
                except Exception as log_error:
                    logger.error(f"Error logging activity: {log_error}")
    
    def stop_task(self, task_name):
        """
        Stop a running task.
        
        Args:
            task_name (str): Name of the task to stop
            
        Returns:
            bool: True if task stopped successfully, False otherwise
        """
        if task_name not in self.tasks:
            logger.warning(f"Task {task_name} not found")
            return False
        
        task = self.tasks[task_name]
        
        if task['thread'] is None or not task['thread'].is_alive():
            logger.info(f"Task {task_name} is not running")
            return True
        
        try:
            # Call the task's stop method if it exists
            if hasattr(task['instance'], 'stop'):
                task['instance'].stop()
            
            # Update task status
            task['status'] = 'stopped'
            
            logger.info(f"Task {task_name} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping task {task_name}: {e}")
            return False
    
    def stop_all_tasks(self):
        """
        Stop all running tasks.
        
        Returns:
            bool: True if all tasks stopped successfully, False otherwise
        """
        success = True
        
        for task_name in self.tasks:
            if not self.stop_task(task_name):
                success = False
        
        return success
    
    def cleanup(self):
        """
        Clean up resources used by tasks.
        
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            # Stop all tasks
            self.stop_all_tasks()
            
            # Quit all WebDrivers
            for task_name, handler_data in self.selenium_handlers.items():
                try:
                    handler_data['driver'].quit()
                    logger.info(f"WebDriver for task {task_name} closed")
                except Exception as e:
                    logger.warning(f"Error closing WebDriver for task {task_name}: {e}")
            
            # Clear tasks and handlers
            self.tasks.clear()
            self.selenium_handlers.clear()
            
            logger.info("Task Runner cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during Task Runner cleanup: {e}")
            return False