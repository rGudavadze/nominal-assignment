import logging
import sys
from logging.handlers import RotatingFileHandler
import os

os.makedirs('logs', exist_ok=True)

# Configure the root logger
def setup_logger(name='app', level=logging.INFO):
    """
    Set up and return a logger with the specified name and level.
    
    Args:
        name (str): The name of the logger
        level (int): The logging level (default: logging.INFO)
        
    Returns:
        logging.Logger: The configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    
    file_handler = RotatingFileHandler(
        f'logs/{name}.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


logger = setup_logger()

# Export the logger
__all__ = ['logger', 'setup_logger']
