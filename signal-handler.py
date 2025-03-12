"""
Signal handler for graceful shutdowns.
"""
import signal
import logging
import sys
import time
import threading
from database.mongodb import MongoDB

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('signal_handler')

# Global variables
shutdown_event = threading.Event()
handlers = []

def handle_signal(signum, frame):
    """
    Handle termination signals (SIGINT, SIGTERM).
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
    logger.info(f"Received {signal_name} signal. Starting graceful shutdown...")
    
    # Set shutdown event to notify all threads
    shutdown_event.set()
    
    # Execute registered handlers in reverse order
    for handler in reversed(handlers):
        try:
            handler()
        except Exception as e:
            logger.error(f"Error during shutdown handler execution: {e}")
    
    # Wait briefly to allow handlers to complete
    time.sleep(1)
    
    logger.info("Graceful shutdown completed. Exiting.")
    sys.exit(0)

def register_shutdown_handler(handler):
    """
    Register a function to be called during shutdown.
    Handlers will be called in reverse order of registration.
    
    Args:
        handler: Function to call during shutdown
    """
    handlers.append(handler)
    logger.debug(f"Registered shutdown handler: {handler.__name__}")

def initialize_signal_handlers():
    """
    Initialize signal handlers for graceful shutdown.
    """
    logger.info("Initializing signal handlers...")
    
    # Register default database shutdown
    def close_database_connections():
        logger.info("Closing database connections...")
        MongoDB().disconnect()
    
    register_shutdown_handler(close_database_connections)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    logger.info("Signal handlers initialized successfully.")

def is_shutting_down():
    """
    Check if application is in the process of shutting down.
    
    Returns:
        bool: True if shutting down, False otherwise
    """
    return shutdown_event.is_set()
