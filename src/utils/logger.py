"""
Logging configuration for the Monday Uploader application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger():
    """
    Set up and configure the application logger.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Get logger
    logger = logging.getLogger("monday_uploader")
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create log file handler with rotation
    log_file = os.path.join(logs_dir, 'monday_uploader.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Attach formatters
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("Logger initialized")
    
    return logger

def get_logger(name=None):
    """
    Get a named logger.
    
    Args:
        name (str, optional): Logger name. Defaults to None.
        
    Returns:
        logging.Logger: Logger instance
    """
    if name:
        return logging.getLogger(f"monday_uploader.{name}")
    return logging.getLogger("monday_uploader") 